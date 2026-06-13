from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer
from typer.models import Context as TyperContext

from deviate.cli._common import (
    _load_manifest,
    console,
    with_json_quiet,
)
from deviate.core._shared import git_env as _git_env
from deviate.core.context import (
    ContextContract,
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


def _build_governance_block(contract: ContextContract) -> str:
    parts: list[str] = []
    for key in ("status", "repo_root", "deviate_path", "specs_path", "timestamp"):
        value = getattr(contract, key, None)
        if value is not None:
            parts.append(f"{key}: {value}")
    return "Tasks=" + ", ".join(parts)


def _update_claude_governance(
    claude_path: Path,
    contract: ContextContract,
    repo_root: Path,
    files_to_commit: list[Path],
) -> None:
    claude_content = claude_path.read_text(encoding="utf-8")
    fresh_block = _build_governance_block(contract)
    updated = upsert_governance_block(
        content=claude_content,
        block_header="## Technical Execution Context",
        fresh_block=fresh_block,
        repo=repo_root,
    )
    claude_path.write_text(updated, encoding="utf-8")
    files_to_commit.append(claude_path)
    console.print("[green]CONTEXT[/] governance block updated in CLAUDE.md")


def _clean_agents_stale_refs(agents_path: Path) -> None:
    agents_content = agents_path.read_text(encoding="utf-8")
    cleaned = remove_stale_references(agents_content, STALE_PATTERNS)
    agents_path.write_text(cleaned, encoding="utf-8")
    console.print("[green]CONTEXT[/] stale references removed from AGENTS.md")


def _apply_context(contract: ContextContract, repo_root: Path) -> None:
    """Apply governance sync, symlink, stale refs, and stage changes.

    Stages CLAUDE.md and AGENTS.md changes for the caller to commit.
    This avoids creating noisy separate commits when auto-triggered
    from macro/meso post commands (those commits include context changes).
    """
    claude_path = repo_root / "CLAUDE.md"
    agents_path = repo_root / "AGENTS.md"
    files_to_stage: list[Path] = []

    if claude_path.exists():
        _update_claude_governance(claude_path, contract, repo_root, files_to_stage)
    else:
        console.print(
            "[yellow]CONTEXT_WARN[/] CLAUDE.md not found "
            "\u2014 skipping governance update"
        )

    if agents_path.exists() and not agents_path.is_symlink():
        _clean_agents_stale_refs(agents_path)

    enforce_agents_symlink(claude_path, agents_path)

    if agents_path.exists() and agents_path not in files_to_stage:
        files_to_stage.append(agents_path)

    if files_to_stage:
        try:
            subprocess.run(
                ["git", "add", "--"] + [str(f) for f in files_to_stage],
                cwd=repo_root,
                env=_git_env(),
                check=True,
                capture_output=True,
            )
            console.print(f"[green]CONTEXT[/] staged {len(files_to_stage)} file(s)")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]CONTEXT_WARN[/] git add failed \u2014 {e}")
    else:
        console.print("[yellow]CONTEXT_WARN[/] no files to stage")


context_app = typer.Typer(no_args_is_help=False, help="Context sync commands")


@context_app.callback(invoke_without_command=True)
def context_main(ctx: TyperContext) -> None:
    """Sync workspace context \u2014 discover and apply in one step.

    Use `deviate context pre` to only scan and emit a JSON contract,
    or `deviate context post <manifest>` to apply from a saved manifest.
    """
    if ctx.invoked_subcommand is not None:
        return

    contract = resolve_workspace_context(Path.cwd())
    if contract.status == "FAILURE" and contract.diagnostic:
        console.print(f"[red]CONTEXT_FAILURE[/] {contract.diagnostic}")
        raise typer.Exit(code=1)
    console.print(f"[green]CONTEXT[/] workspace scan \u2014 {contract.status}")
    _apply_context(contract, Path.cwd())


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
    manifest_data = _load_manifest(manifest, "CONTEXT")
    contract = ContextContract.model_validate(manifest_data)
    _apply_context(contract, Path.cwd())
