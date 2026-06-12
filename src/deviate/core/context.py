from __future__ import annotations

import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel


class ContextContract(BaseModel):
    status: Literal["READY", "FAILURE"]
    repo_root: str
    deviate_path: Optional[str] = None
    specs_path: Optional[str] = None
    specs_issues: list[str] = []
    specs_active_issue: Optional[str] = None
    diagnostic: Optional[str] = None
    timestamp: str


def resolve_workspace_context(repo_root: Path) -> ContextContract:
    deviate_dir = repo_root / ".deviate"
    specs_dir = repo_root / "specs"

    if not deviate_dir.exists():
        return ContextContract(
            status="FAILURE",
            repo_root="",
            diagnostic="Missing .deviate/ directory",
            timestamp=datetime.now().isoformat(),
        )

    specs_exists = specs_dir.exists()
    specs_issues: list[str] = []

    if specs_exists:
        for child in sorted(specs_dir.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                issues_dir = child / "issues"
                if issues_dir.exists():
                    for f in sorted(issues_dir.iterdir()):
                        if f.is_file() and f.suffix == ".md":
                            specs_issues.append(str(f.relative_to(repo_root)))

    return ContextContract(
        status="READY",
        repo_root="",
        deviate_path=str(deviate_dir.relative_to(repo_root)),
        specs_path=str(specs_dir.relative_to(repo_root)) if specs_exists else None,
        specs_issues=specs_issues,
        diagnostic=None,
        timestamp=datetime.now().isoformat(),
    )


def enforce_agents_symlink(claude_path: Path, agents_path: Path) -> None:
    if agents_path.is_symlink():
        return

    if os.name == "posix":
        if not agents_path.exists():
            agents_path.symlink_to(claude_path)
            return

        claude_content = claude_path.read_bytes() if claude_path.exists() else b""
        agents_content = agents_path.read_bytes()

        if claude_content == agents_content:
            agents_path.unlink()
            agents_path.symlink_to(claude_path)
        else:
            warnings.warn(
                "AGENTS.md content diverges from CLAUDE.md "
                "\u2014 manual alignment may be needed"
            )

    elif os.name == "nt":
        if not agents_path.exists():
            agents_path.write_bytes(claude_path.read_bytes())
            return

        claude_content = claude_path.read_bytes() if claude_path.exists() else b""
        agents_content = agents_path.read_bytes()

        if claude_content == agents_content:
            return

        warnings.warn(
            "AGENTS.md content diverges from CLAUDE.md "
            "\u2014 manual alignment may be needed"
        )


def remove_stale_references(content: str, patterns: list[str]) -> str:
    lines = content.splitlines()
    result = [line for line in lines if line.strip() not in patterns]
    joined = "\n".join(result)
    if content.endswith("\n"):
        joined += "\n"
    return joined
