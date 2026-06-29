"""Content Capture CLI sub-app (FLOW-11 / FLOW-12).

Implements the ``deviate content`` Typer sub-app with the ``pre|post``
dual pattern established by ``deviate.cli.macro``. The sub-app exposes:

* ``--format <fmt>`` (repeatable; defaults to the build-in-public bundle)
* ``--window EPIC-X`` (epic-scoped record filtering)
* ``--slug S`` (draft filename stem)
* ``--archive EPIC-X`` (tarball ``specs/_archives/<epic>-narrative.tar.gz``)

**Default bundle**: ``--format`` is pre-populated with
``("blog", "x-thread", "threads")`` so a bare
``deviate content --slug S --window EPIC-X`` produces a blog draft, an
X-thread, and a Meta Threads post from the same handover window in one
call. Explicit ``--format <fmt>`` values REPLACE the default set — they
do not extend it. See ``src/deviate/prompts/commands/deviate-content.md``
§ Default Bundle.

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
    X_THREAD_COUNT,
    build_context,
    load_template,
    render_template,
)


VALID_FORMATS: tuple[str, ...] = (
    # Original 5 formats (FLOW-12 v1).
    "blog",
    "x-thread",
    "release-notes",
    "commit-story",
    "resume-bullet",
    # Slice B — research-backed templates per the build-in-public playbook.
    # Each format ships as its own template file at
    # src/deviate/prompts/content/<format>.md. The synthesis layer loads the
    # template by format name; no Jinja2 / no per-format renderer needed.
    # Consolidates 4 blog variants down to 2 specialized blog voices:
    # `blog-devrel` (tutorial) and `blog-reflective` (merged Saha +
    # narrative reflective essay) — see the "Choosing a blog variant"
    # decision tree in src/deviate/prompts/commands/deviate-content.md.
    "blog-devrel",  # 4-section DevRel Bridge 2024 tutorial template (Stripe / Cloudflare voice)
    "blog-reflective",  # 6-section reflective essay (Saha retrospective + narrative decision essay merged)
    "threads",  # Meta Threads long-form narrative (distinct from X; per research)
    "linkedin",  # LinkedIn resume-discoverability cross-post
)

# Build-in-public default bundle applied when ``--format`` is omitted.
# ``/deviate-content`` is invoked by the developer after a phase or epic
# closes; the default bundle gives them a blog draft, an X-thread, and a
# Meta Threads post in one call without having to remember which
# ``--format`` value triggers which template. Power users override
# per-invocation by passing ``--format <fmt>`` (repeatable) — explicit
# values REPLACE the default set, they do not extend it. See
# ``src/deviate/prompts/commands/deviate-content.md`` § Default Bundle.
DEFAULT_FORMATS: tuple[str, ...] = (
    "blog",
    "x-thread",
    "threads",
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
    format: list[str] = typer.Option(
        list(DEFAULT_FORMATS),
        "--format",
        help=(
            "Synthesis format. Repeatable. One of: "
            f"{', '.join(VALID_FORMATS)}. Pass multiple times to render "
            "more than one format from the same window (e.g. "
            "'--format blog --format x-thread'). Omit entirely to render "
            "the default build-in-public bundle: "
            f"{', '.join(DEFAULT_FORMATS)}."
        ),
    ),
    posts: int = typer.Option(
        X_THREAD_COUNT,
        "--posts",
        help=(
            f"Number of posts for x-thread format (default {X_THREAD_COUNT}, "
            "valid range 1-50). Ignored by other formats."
        ),
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
    # ``--format`` has a non-empty default (DEFAULT_FORMATS), so the
    # bare-invocation help path is handled by Typer's
    # ``no_args_is_help=True`` on the sub-app above — no in-body check
    # needed. The validation below still fires when a user passes
    # ``--format`` with an unknown value.
    bad = [f for f in format if f not in VALID_FORMATS]
    if bad:
        console.print(
            f"[red]CONTENT_HALTED[/] unknown --format {bad!r}; "
            f"valid: {', '.join(VALID_FORMATS)}"
        )
        raise typer.Exit(code=2)
    if not (1 <= posts <= 50):
        console.print(f"[red]CONTENT_HALTED[/] --posts must be in 1..50, got {posts}")
        raise typer.Exit(code=2)
    if not slug:
        console.print("[red]CONTENT_HALTED[/] --slug is required for synthesis")
        raise typer.Exit(code=2)
    for fmt in format:
        try:
            target = _run_synthesis(format=fmt, window=window, slug=slug, posts=posts)
        except ContentCaptureError as exc:
            console.print(f"[red]CONTENT_HALTED[/] {exc}")
            raise typer.Exit(code=2) from exc
        console.print(f"[green]CONTENT_DRAFT_WRITTEN[/] {target}")


def _run_synthesis(
    *,
    format: str,
    window: str | None,
    slug: str,
    posts: int = X_THREAD_COUNT,
) -> Path:
    records = load_handover_records(window=window)
    if not records:
        raise ContentCaptureError(f"no handover records found for window={window!r}")
    context = build_context(records, slug=slug)
    rendered = render_template(
        load_template(format), context, format=format, posts=posts
    )
    draft_dir = Path(".deviate") / "content" / "drafts" / format
    draft_dir.mkdir(parents=True, exist_ok=True)
    target = draft_dir / f"{slug}.md"
    target.write_text(rendered, encoding="utf-8")
    return target


def _run_archive(epic: str) -> Path:
    base = Path.cwd() / ".deviate" / "content" / "handovers" / epic
    if not base.exists() or not any(base.rglob("*.yaml")):
        raise ContentCaptureError(f"no handover YAMLs under {base}; nothing to archive")
    archive_dir = Path("specs") / "_archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{epic}-narrative.tar.gz"
    with tarfile.open(archive_path, mode="w:gz") as tar:
        for yaml_path in sorted(base.rglob("*.yaml")):
            tar.add(yaml_path, arcname=yaml_path.relative_to(Path.cwd()))
    return archive_path


__all__ = ["content_app", "VALID_FORMATS", "DEFAULT_FORMATS"]
