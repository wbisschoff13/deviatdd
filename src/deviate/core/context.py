from __future__ import annotations

import os
from datetime import datetime, timezone
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
    timestamp: str = ""


def resolve_workspace_context(repo_root: Path) -> ContextContract:
    deviate_dir = repo_root / ".deviate"
    if not deviate_dir.is_dir():
        return ContextContract(
            status="FAILURE",
            repo_root="",
            diagnostic="Missing .deviate directory — run 'deviate init' first",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    deviate_path = ".deviate"
    specs_path: str | None = None
    specs_issues: list[str] = []
    specs_active_issue: str | None = None

    specs_dir = repo_root / "specs"
    if specs_dir.is_dir():
        specs_path = "specs"
        for child in sorted(specs_dir.iterdir()):
            issues_dir = child / "issues"
            if issues_dir.is_dir():
                for f in sorted(issues_dir.iterdir()):
                    if f.suffix == ".md":
                        specs_issues.append(str(f.relative_to(repo_root)))

    return ContextContract(
        status="READY",
        repo_root="",
        deviate_path=deviate_path,
        specs_path=specs_path,
        specs_issues=specs_issues,
        specs_active_issue=specs_active_issue,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def enforce_agents_symlink(claude_path: Path, agents_path: Path) -> None:
    if os.name == "nt":
        if agents_path.exists():
            if agents_path.read_text() == claude_path.read_text():
                agents_path.write_text(claude_path.read_text())
        else:
            agents_path.write_text(claude_path.read_text())
        return

    if agents_path.is_symlink():
        return

    if agents_path.exists():
        if agents_path.read_text() != claude_path.read_text():
            return
        agents_path.unlink()

    agents_path.symlink_to(claude_path)


def remove_stale_references(content: str, patterns: list[str]) -> str:
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if any(stripped == pattern for pattern in patterns):
            continue
        result.append(line)
    return "".join(result)
