"""Content Capture runtime helpers (FLOW-11, FLOW-12).

Per ``specs/_product/architecture.md`` §3.5-§3.7 and
``specs/plans/deviate-content.md``: durable phase-output persistence
under ``.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml`` plus a
read-side ``HandoverRecord`` model used by the synthesis layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from deviate.core.yaml_repair import safe_load_yaml


class PathTraversalError(ValueError):
    """Raised when a handover path escapes ``.deviate/content/handovers/``."""


class HandoverRecord(BaseModel):
    """Read-side model for handover YAMLs (FLOW-11, FLOW-12).

    ``extra="allow"`` keeps the schema forward-compatible with the
    optional ``narrative_anchor:`` block and any future per-phase fields.
    """

    model_config = ConfigDict(extra="allow")

    epic_slug: str
    issue_id: str
    phase: str
    status: str = ""
    task_id: str | None = None
    files: list[str] = []
    narrative_anchor: dict[str, Any] | None = None
    timestamp: str | None = None


_HANDOVER_ROOT = Path(".deviate") / "content" / "handovers"
_YAML_SUFFIX = ".yaml"


def _validate_segment(label: str, value: str) -> str:
    """Reject segments that could escape ``.deviate/content/handovers/``."""
    if not value or value != value.strip():
        raise PathTraversalError(f"{label} must be a non-empty trimmed string")
    if "/" in value or "\\" in value:
        raise PathTraversalError(f"{label} must not contain path separators: {value!r}")
    if value in {"..", "."} or value.startswith(".."):
        raise PathTraversalError(f"{label} must not traverse parents: {value!r}")
    if Path(value).is_absolute():
        raise PathTraversalError(f"{label} must be relative: {value!r}")
    return value


def handover_path(
    epic_slug: str,
    issue_id: str,
    phase: str,
    task_id: str | None = None,
    repo: Path | None = None,
) -> Path:
    """Return the canonical handover YAML path (FLOW-11).

    Macro:         .deviate/content/handovers/<epic_slug>/<issue_id>/<phase>.yaml
    Micro:         .deviate/content/handovers/<epic_slug>/<issue_id>/<task_id>/<phase>.yaml
    Product-layer: .deviate/content/handovers/_product/<skill>/<skill>.yaml (sentinel)

    The Product-layer path is invoked via the underscore-prefixed sentinel
    epic_slug "_product" (per AC-ADHOC-013-04). The sentinel matches the
    specs/_product/ directory name for one-to-one traceability and is
    accepted by _validate_segment() because it is non-empty, stripped, and
    free of path separators or ".." sequences. The .deviate/content/handovers/
    root remains the single top-level root (FLOW-02 governance); the
    underscore prefix distinguishes the sentinel from real epic slugs.
    """
    base = repo or Path.cwd()
    epic = _validate_segment("epic_slug", epic_slug)
    issue = _validate_segment("issue_id", issue_id)
    phase_name = _validate_segment("phase", phase)
    parts: list[str] = [str(base), str(_HANDOVER_ROOT), epic, issue]
    if task_id is not None:
        parts.append(_validate_segment("task_id", task_id))
    parts.append(f"{phase_name}{_YAML_SUFFIX}")
    target = Path(*parts)
    # Defense in depth: resolve any pre-existing ``..``/symlinks inside base
    # and confirm the resolved target stays under ``base/.deviate/content/handovers/``.
    resolved_target = target.resolve()
    resolved_root = (base / _HANDOVER_ROOT).resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise PathTraversalError(
            f"resolved path {resolved_target!s} escapes {resolved_root!s}"
        ) from exc
    return target


def persist_handover(
    epic_slug: str,
    issue_id: str,
    phase: str,
    manifest: str,
    task_id: str | None = None,
    repo: Path | None = None,
) -> Path:
    """Persist a YAML handover manifest (idempotent overwrite-or-skip).

    Identical content is a no-op; divergent content writes through
    (last-writer-wins; divergence is surfaced by archive tarball diff).
    """
    target = handover_path(epic_slug, issue_id, phase, task_id, repo)
    payload = manifest if manifest.endswith("\n") else manifest + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_text(encoding="utf-8") == payload:
            return target
    target.write_text(payload, encoding="utf-8")
    return target


def _iter_handover_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.yaml"))


def _parts_from_path(path: Path, root: Path) -> tuple[str, str, str | None, str]:
    """Derive (epic, issue, task_or_None, phase) from a handover YAML path."""
    rel = path.relative_to(root).parts
    phase_token = rel[-1]
    phase = (
        Path(phase_token).stem if phase_token.endswith(_YAML_SUFFIX) else phase_token
    )
    task = rel[2] if len(rel) >= 4 else None
    return rel[0], rel[1], task, phase


def load_handover_records(
    window: str | None = None,
    repo: Path | None = None,
) -> list[HandoverRecord]:
    """Load handover YAMLs from ``.deviate/content/handovers/`` in chronological order.

    ``window`` filters by epic_slug. Handovers whose narrative anchors
    contain ``: `` are repaired heuristically (unquoted scalar wrapped in
    double quotes) before parsing; YAMLs that remain unparseable are
    skipped with a stderr warning (per AC-ADHOC-012-12).
    """
    base = repo or Path.cwd()
    root = base / _HANDOVER_ROOT
    if window is not None:
        root = root / _validate_segment("window", window)
    stamped: list[tuple[float, HandoverRecord]] = []
    for path in _iter_handover_files(root):
        loaded = safe_load_yaml(path)
        if loaded is None:
            continue
        epic, issue, task, phase = _parts_from_path(path, base / _HANDOVER_ROOT)
        data: dict[str, Any] = {
            "epic_slug": loaded.get("epic_slug", epic),
            "issue_id": loaded.get("issue_id", issue),
            "task_id": loaded.get("task_id", task),
            "phase": loaded.get("phase", phase),
            "status": loaded.get("status", ""),
            "files": loaded.get("files") or [],
            "narrative_anchor": loaded.get("narrative_anchor"),
            "timestamp": loaded.get("timestamp"),
        }
        stamped.append((path.stat().st_mtime, HandoverRecord(**data)))
    stamped.sort(key=lambda pair: pair[0])
    return [record for _, record in stamped]


__all__ = [
    "HandoverRecord",
    "PathTraversalError",
    "handover_path",
    "load_handover_records",
    "persist_handover",
]
