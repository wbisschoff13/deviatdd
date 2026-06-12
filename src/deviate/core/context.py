from __future__ import annotations

from pathlib import Path


class ContextContract:
    pass


def resolve_workspace_context(repo_root: Path) -> ContextContract:
    raise NotImplementedError


def enforce_agents_symlink(claude_path: Path, agents_path: Path) -> None:
    raise NotImplementedError


def remove_stale_references(content: str, patterns: list[str]) -> str:
    raise NotImplementedError
