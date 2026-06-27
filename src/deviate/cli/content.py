"""Content Capture CLI sub-app (FLOW-11 / FLOW-12).

Implements the ``deviate content`` Typer sub-app with the ``pre|post``
dual pattern established by ``deviate.cli.macro``. The sub-app exposes:

* ``--format <blog|x-thread|release-notes|commit-story|resume-bullet>``
* ``--window EPIC-X`` (epic-scoped record filtering)
* ``--slug S`` (draft filename stem)
* ``--archive EPIC-X`` (tarball ``specs/_archives/<epic>-narrative.tar.gz``)

All synthesis logic lives in ``deviate.core.synthesis``; this module is
the thin Typer shell that wires CLI flags to the helpers.
"""

from __future__ import annotations

import tarfile
from pathlib import Path

import typer

from deviate.cli._common import console
from deviate.core.handover import load_handover_records
from deviate.core.synthesis import (
    build_context,
    load_template,
    render_template,
)


VALID_FORMATS: tuple[str, ...] = (
    "blog",
    "x-thread",
    "release-notes",
    "commit-story",
    "resume-bullet",
)

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
    context = build_context(records, slug=slug)
    rendered = render_template(load_template(format), context, format=format)
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


__all__ = ["content_app", "VALID_FORMATS"]
