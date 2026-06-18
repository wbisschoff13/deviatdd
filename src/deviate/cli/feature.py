from __future__ import annotations

import re
import subprocess
from pathlib import Path

import typer
from deviate.core._shared import git_env
from deviate.state.config import SessionState, resolve_graphite_config

feature_app = typer.Typer(no_args_is_help=True)


def _derive_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def _create_feature_directory(slug: str, repo_path: Path) -> Path:
    spec_dir = repo_path / "specs" / slug
    spec_dir.mkdir(parents=True, exist_ok=True)
    return spec_dir


def _create_feature_branch(slug: str, repo_path: Path) -> None:
    branch_name = f"feat/{slug}"

    def _run(*args, **kwargs):
        return subprocess.run(*args, cwd=repo_path, env=git_env(), **kwargs)

    if resolve_graphite_config(repo_path):
        _run(["gt", "create", "-am", branch_name], check=True)
        return

    result = _run(
        ["git", "rev-parse", "--verify", "--quiet", branch_name], capture_output=True
    )
    if result.returncode == 0:
        return

    _run(["git", "branch", branch_name], check=True)


@feature_app.command()
def create(
    title: str = typer.Argument(..., help="Feature title"),
    slug: str | None = typer.Option(None, "--slug", help="Override derived slug"),
) -> None:
    repo_path = Path.cwd()
    final_slug = slug or _derive_slug(title)

    _create_feature_directory(final_slug, repo_path)
    _create_feature_branch(final_slug, repo_path)

    session_dir = repo_path / ".deviate"
    session_dir.mkdir(parents=True, exist_ok=True)
    session = SessionState()
    session_path = session_dir / "session.json"
    session.save(session_path)
