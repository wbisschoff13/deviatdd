"""Content Capture runtime helpers (FLOW-11).

Stub module — RED phase. Full implementation lands in the GREEN phase.
See ``specs/_product/architecture.md`` §3.5-§3.7 and
``specs/plans/deviate-content.md`` for the full contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PathTraversalError(ValueError):
    """Raised when a handover path escapes ``.deviate/feat/``."""


def handover_path(
    epic_slug: str,
    issue_id: str,
    phase: str,
    task_id: str | None = None,
    repo: Path | None = None,
) -> Path:
    """Return the canonical handover YAML path for the given coordinates.

    Full implementation lands in the GREEN phase. Stub raises
    ``NotImplementedError`` so RED tests fail cleanly.
    """
    raise NotImplementedError("handover_path() lands in the GREEN phase of TSK-012-01")


def persist_handover(
    epic_slug: str,
    issue_id: str,
    phase: str,
    manifest: str,
    task_id: str | None = None,
    repo: Path | None = None,
) -> Path:
    """Persist a YAML handover manifest to the canonical path (idempotent).

    Full implementation lands in the GREEN phase. Stub raises
    ``NotImplementedError`` so RED tests fail cleanly.
    """
    raise NotImplementedError(
        "persist_handover() lands in the GREEN phase of TSK-012-01"
    )


def load_handover_records(
    window: str | None = None,
    repo: Path | None = None,
) -> list["HandoverRecord"]:
    """Load handover YAMLs from ``.deviate/feat/`` in chronological order.

    Full implementation lands in a later phase. Stub raises
    ``NotImplementedError`` so RED tests fail cleanly.
    """
    raise NotImplementedError("load_handover_records() lands in a later phase")


class HandoverRecord:
    """Read-side Pydantic model (stub during RED phase).

    Real Pydantic model lands in the GREEN phase.
    """

    def __init__(
        self,
        *,
        epic_slug: str,
        issue_id: str,
        phase: str,
        status: str,
        task_id: str | None = None,
        files: list[str] | None = None,
        narrative_anchor: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> None:
        self.epic_slug = epic_slug
        self.issue_id = issue_id
        self.task_id = task_id
        self.phase = phase
        self.status = status
        self.files = files or []
        self.narrative_anchor = narrative_anchor
        self.timestamp = timestamp
