from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from deviate.cli._common import (
    _load_manifest,
    _run_pre_commit_hooks,
    console,
    with_json_quiet,
)
from deviate.core._shared import git_env as _git_env
from deviate.core.commit import stage_and_commit
from deviate.core.context import (
    enforce_agents_symlink,
    remove_stale_references,
    resolve_workspace_context,
)
from deviate.core.worktree import upsert_governance_block

STALE_PATTERNS = [
    "rgr run",
    "manage-tasks.sh",
    "sdd-parse-ast.sh",
    "get-test-config.sh",
    ".rgr/",
]


def _get_git_branch(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo,
            env=_git_env(),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "detached"


def _build_governance_block(contract_data: dict) -> str:
    items: list[str] = []
    for key in ("status", "repo_root", "deviate_path", "specs_path", "timestamp"):
        value = contract_data.get(key)
        if value is not None:
            items.append(f"{key}: {value}")
    return "Tasks=" + ", ".join(items)


context_app = typer.Typer(no_args_is_help=True, help="Context sync commands")


@context_app.command("pre")
@with_json_quiet
def context_pre() -> dict[str, object]:
    """Crawl workspace and emit ContextContract JSON."""
    contract = resolve_workspace_context(Path.cwd())
    data = contract.model_dump()
    typer.echo(json.dumps(data))
    return data


@context_app.command("post")
def context_post(
    manifest: Path = typer.Argument(..., help="Path to ContextContract JSON file"),
) -> None:
    """Read manifest, sync governance, enforce symlink, remove stale refs, commit."""
    repo_root = Path.cwd()
    manifest_data = _load_manifest(manifest, "CONTEXT")
    branch = _get_git_branch(repo_root)

    claude_path = repo_root / "CLAUDE.md"
    agents_path = repo_root / "AGENTS.md"
    files_to_commit: list[Path] = []

    if claude_path.exists():
        claude_content = claude_path.read_text(encoding="utf-8")
        fresh_block = _build_governance_block(manifest_data)
        updated = upsert_governance_block(
            content=claude_content,
            block_header="## Technical Execution Context",
            fresh_block=fresh_block,
            repo=repo_root,
        )
        claude_path.write_text(updated, encoding="utf-8")
        files_to_commit.append(claude_path)
        console.print("[green]CONTEXT[/] governance block updated in CLAUDE.md")
    else:
        console.print(
            "[yellow]CONTEXT_WARN[/] CLAUDE.md not found "
            "\u2014 skipping governance update"
        )

    if agents_path.exists() and not agents_path.is_symlink():
        agents_content = agents_path.read_text(encoding="utf-8")
        cleaned = remove_stale_references(agents_content, STALE_PATTERNS)
        agents_path.write_text(cleaned, encoding="utf-8")
        console.print("[green]CONTEXT[/] stale references removed from AGENTS.md")

    enforce_agents_symlink(claude_path, agents_path)

    if agents_path.exists():
        files_to_commit.append(agents_path)

    if files_to_commit:
        message = f"chore(context): sync governance for {branch}"
        try:
            _run_pre_commit_hooks()
            sha = stage_and_commit(
                message=message,
                files=files_to_commit,
                repo=repo_root,
            )
            console.print(f"[green]CONTEXT[/] committed at {sha[:8]}")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]CONTEXT_WARN[/] commit failed \u2014 {e}")
    else:
        console.print("[yellow]CONTEXT_WARN[/] no files to commit")
