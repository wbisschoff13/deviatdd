"""Content Capture CLI sub-app (FLOW-11 / FLOW-12).

Implements the ``deviate content`` Typer sub-app with the ``pre|post``
dual pattern established by ``deviate.cli.macro``. The sub-app exposes:

* ``--format <blog|x-thread|release-notes|commit-story|resume-bullet>``
* ``--window EPIC-X`` (epic-scoped record filtering)
* ``--slug S`` (draft filename stem)
* ``--archive EPIC-X`` (tarball ``specs/_archives/<epic>-narrative.tar.gz``)

Synthesis is template-driven — the 5 format templates under
``src/deviate/prompts/content/`` are loaded with ``importlib.resources``
and rendered via plain ``str.replace`` (no Jinja2 dependency per
``specs/plans/deviate-content.md:201``).
"""

from __future__ import annotations

import importlib.resources
import re
import tarfile
from pathlib import Path
from typing import Iterable

import typer

from deviate.cli._common import console
from deviate.core.handover import HandoverRecord, load_handover_records


VALID_FORMATS: tuple[str, ...] = (
    "blog",
    "x-thread",
    "release-notes",
    "commit-story",
    "resume-bullet",
)

_PHASE_ORDER = ("red", "green", "yellow", "judge", "refactor", "execute", "e2e")
_X_THREAD_LIMIT = 280
_X_THREAD_COUNT = 6

content_app = typer.Typer(
    no_args_is_help=True,
    help="Content Capture commands (FLOW-11 / FLOW-12)",
)


class ContentCaptureError(RuntimeError):
    """Raised when synthesis cannot proceed (empty window, IO failure, ...)."""


@content_app.command("pre")
def content_pre() -> None:
    """Prepare the Content Capture working state (no-op stub)."""
    console.print("[dim]CONTENT_PRE[/] no preparation needed; capture is actor-driven")


@content_app.command("post")
def content_post() -> None:
    """Close the Content Capture working state (no-op stub)."""
    console.print("[dim]CONTENT_POST[/] no teardown needed; capture is actor-driven")


@content_app.callback(invoke_without_command=True)
def _content_main(
    ctx: typer.Context,
    format: str | None = typer.Option(
        None,
        "--format",
        help=f"Synthesis format. One of: {', '.join(VALID_FORMATS)}.",
    ),
    window: str | None = typer.Option(
        None,
        "--window",
        help="Filter records to a single epic slug (e.g. EPIC-X).",
    ),
    slug: str | None = typer.Option(
        None,
        "--slug",
        help="Draft filename stem (e.g. 'my-post' → blog/my-post.md).",
    ),
    archive: str | None = typer.Option(
        None,
        "--archive",
        help="Produce specs/_archives/<epic>-narrative.tar.gz for the named epic.",
    ),
) -> None:
    """Content Capture top-level dispatch (FLOW-12)."""
    if ctx.invoked_subcommand is not None:
        return
    if archive is not None:
        try:
            target = _run_archive(archive)
        except ContentCaptureError as exc:
            console.print(f"[red]CONTENT_HALTED[/] {exc}")
            raise typer.Exit(code=2) from exc
        console.print(f"[green]CONTENT_ARCHIVE_WRITTEN[/] {target}")
        return
    if format is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)
    if format not in VALID_FORMATS:
        console.print(
            f"[red]CONTENT_HALTED[/] unknown --format {format!r}; "
            f"valid: {', '.join(VALID_FORMATS)}"
        )
        raise typer.Exit(code=2)
    if not slug:
        console.print("[red]CONTENT_HALTED[/] --slug is required for synthesis")
        raise typer.Exit(code=2)
    try:
        target = _run_synthesis(format=format, window=window, slug=slug)
    except ContentCaptureError as exc:
        console.print(f"[red]CONTENT_HALTED[/] {exc}")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]CONTENT_DRAFT_WRITTEN[/] {target}")


def _run_synthesis(*, format: str, window: str | None, slug: str) -> Path:
    records = load_handover_records(window=window)
    if not records:
        raise ContentCaptureError(f"no handover records found for window={window!r}")
    template = _load_template(format)
    rendered = _render_template(
        template, _build_context(records, slug=slug), format=format
    )
    draft_dir = Path(".deviate") / "content-drafts" / format
    draft_dir.mkdir(parents=True, exist_ok=True)
    target = draft_dir / f"{slug}.md"
    target.write_text(rendered, encoding="utf-8")
    return target


def _run_archive(epic: str) -> Path:
    base = Path.cwd() / ".deviate" / "feat" / epic
    if not base.exists() or not any(base.rglob("*.yaml")):
        raise ContentCaptureError(f"no handover YAMLs under {base}; nothing to archive")
    archive_dir = Path("specs") / "_archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{epic}-narrative.tar.gz"
    with tarfile.open(archive_path, mode="w:gz") as tar:
        for yaml_path in sorted(base.rglob("*.yaml")):
            tar.add(yaml_path, arcname=yaml_path.relative_to(Path.cwd()))
    return archive_path


def _build_context(records: list[HandoverRecord], *, slug: str) -> dict[str, str]:
    """Assemble template placeholder values from handover records."""
    title = slug.replace("-", " ").title() if slug else "Untitled"
    verdict_story = _collect_anchors(
        records, "verdict_story"
    ) or _collect_phase_stories(records)
    phase_summary = _summarise_phases(records)
    invariant_protected = (
        _collect_anchors(records, "invariant_protected") or phase_summary
    )
    return {
        "title": title,
        "verdict_story": verdict_story or "No verdict anchor available.",
        "phase_summary": phase_summary,
        "invariant_protected": invariant_protected,
    }


def _collect_anchors(records: Iterable[HandoverRecord], field: str) -> str:
    """Newline-joined concatenation of every record's ``field`` anchor."""
    pieces: list[str] = []
    seen: set[str] = set()
    for record in records:
        if not record.narrative_anchor:
            continue
        value = record.narrative_anchor.get(field)
        if value is None:
            continue
        text = str(value)
        if text and text not in seen:
            pieces.append(text)
            seen.add(text)
    return "\n".join(pieces)


def _collect_phase_stories(records: Iterable[HandoverRecord]) -> str:
    """Newline-joined concatenation of every record's story/intent anchor."""
    pieces: list[str] = []
    seen: set[str] = set()
    for record in records:
        if not record.narrative_anchor:
            continue
        story = record.narrative_anchor.get("story") or record.narrative_anchor.get(
            "intent"
        )
        if not story:
            continue
        text = str(story)
        if text and text not in seen:
            pieces.append(text)
            seen.add(text)
    return "\n".join(pieces)


def _summarise_phases(records: list[HandoverRecord]) -> str:
    seen: list[str] = []
    for record in records:
        if record.phase and record.phase not in seen:
            seen.append(record.phase)
    if not seen:
        return "Phase trace unavailable."
    seen_sorted = sorted(
        seen,
        key=lambda phase: (
            _PHASE_ORDER.index(phase) if phase in _PHASE_ORDER else len(_PHASE_ORDER)
        ),
    )
    return " → ".join(seen_sorted)


def _load_template(format: str) -> str:
    resource = importlib.resources.files("deviate.prompts.content").joinpath(
        f"{format}.md"
    )
    return resource.read_text(encoding="utf-8")


def _render_template(template: str, context: dict[str, str], *, format: str) -> str:
    if format == "x-thread":
        return _render_x_thread(context)
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def _render_x_thread(context: dict[str, str]) -> str:
    """Build exactly 6 posts, each ≤ 280 chars, sliced from the anchor pool."""
    return "\n\n---\n\n".join(_slice_x_thread_posts(context)) + "\n"


def _slice_x_thread_posts(context: dict[str, str]) -> list[str]:
    """Produce 6 ≤280-char posts derived from the anchor pool."""
    raw_pool = [
        context.get("verdict_story", ""),
        f"Phase trace: {context.get('phase_summary', '')}",
        f"Invariant protected: {context.get('invariant_protected', '')}",
        f"Title: {context.get('title', '')}",
        "Each step verified by the DeviaTDD micro-cycle.",
        "Drafts only — review, edit, publish manually.",
    ]
    posts: list[str] = []
    for entry in raw_pool:
        if not entry:
            continue
        truncated = _truncate_post(entry)
        if truncated and truncated not in posts:
            posts.append(truncated)
        if len(posts) == _X_THREAD_COUNT:
            break
    filler_index = 0
    while len(posts) < _X_THREAD_COUNT:
        posts.append(_truncate_post(f"Continued thread update {filler_index + 1}."))
        filler_index += 1
    return posts


def _truncate_post(text: str) -> str:
    """Trim whitespace and hard-truncate to the X / Twitter limit."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= _X_THREAD_LIMIT:
        return cleaned
    return cleaned[: _X_THREAD_LIMIT - 1].rstrip() + "…"


__all__ = ["content_app", "VALID_FORMATS"]
