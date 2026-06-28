"""Pure synthesis helpers for FLOW-12 content drafts.

The synthesis layer turns a chronological window of ``HandoverRecord``s
into a single rendered Markdown draft by loading the relevant format
template from ``src/deviate/prompts/content/<format>.md`` and replacing
its ``{{ placeholder }}`` markers. The X / Twitter format is a special
case: the template's ``{{ post_N }}`` markers are documentation only;
the synthesis layer slices the anchor pool into ``count`` posts of at
most 280 characters each, where ``count`` defaults to
``X_THREAD_COUNT`` (6) and is overridable via the CLI's ``--posts`` flag.

All helpers in this module are pure functions of the records + slug.
They are kept free of filesystem or CLI surface so the public ``deviate
content`` sub-app can compose them.
"""

from __future__ import annotations

import importlib.resources
import re
from typing import Iterable

from deviate.core.handover import HandoverRecord

X_THREAD_LIMIT = 280
X_THREAD_COUNT = 6

_PHASE_ORDER = ("red", "green", "yellow", "judge", "refactor", "execute", "e2e")


def load_template(format: str) -> str:
    """Load the format template from the package resources."""
    resource = importlib.resources.files("deviate.prompts.content").joinpath(
        f"{format}.md"
    )
    return resource.read_text(encoding="utf-8")


def render_template(
    template: str,
    context: dict[str, str],
    *,
    format: str,
    posts: int = X_THREAD_COUNT,
) -> str:
    """Substitute ``{{ placeholder }}`` markers; delegate x-thread to its slicer.

    ``posts`` only affects the ``x-thread`` format; other formats ignore it.
    """
    if format == "x-thread":
        return render_x_thread(context, count=posts)
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def build_context(records: list[HandoverRecord], *, slug: str) -> dict[str, str]:
    """Assemble template placeholder values from handover records."""
    title = slug.replace("-", " ").title() if slug else "Untitled"
    verdict_story = collect_anchor_field(records, "verdict_story") or collect_stories(
        records
    )
    phase_summary = summarise_phases(records)
    invariant_protected = (
        collect_anchor_field(records, "invariant_protected") or phase_summary
    )
    return {
        "title": title,
        "verdict_story": verdict_story or "No verdict anchor available.",
        "phase_summary": phase_summary,
        "invariant_protected": invariant_protected,
    }


def collect_anchor_field(records: Iterable[HandoverRecord], field: str) -> str:
    """Newline-joined concatenation of every record's ``field`` anchor, deduped."""
    pieces: list[str] = []
    seen: set[str] = set()
    for record in records:
        value = _anchor_value(record, field)
        if value and value not in seen:
            pieces.append(value)
            seen.add(value)
    return "\n".join(pieces)


def collect_stories(records: Iterable[HandoverRecord]) -> str:
    """Newline-joined concatenation of every record's ``story`` / ``intent`` anchor."""
    pieces: list[str] = []
    seen: set[str] = set()
    for record in records:
        value = _anchor_value(record, "story") or _anchor_value(record, "intent")
        if value and value not in seen:
            pieces.append(value)
            seen.add(value)
    return "\n".join(pieces)


def _anchor_value(record: HandoverRecord, field: str) -> str:
    if not record.narrative_anchor:
        return ""
    raw = record.narrative_anchor.get(field)
    return str(raw) if raw else ""


def summarise_phases(records: list[HandoverRecord]) -> str:
    """Return ``red → green → judge → refactor`` for the active phases."""
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


def render_x_thread(context: dict[str, str], *, count: int = X_THREAD_COUNT) -> str:
    """Build exactly ``count`` posts, each ≤ 280 chars, sliced from the anchor pool."""
    return "\n\n---\n\n".join(slice_x_thread_posts(context, count=count)) + "\n"


def slice_x_thread_posts(
    context: dict[str, str],
    *,
    count: int = X_THREAD_COUNT,
) -> list[str]:
    """Produce exactly ``count`` ≤280-char posts derived from the anchor pool.

    The standard pool has six entries (verdict_story, phase trace, invariant,
    title, two static lines). For ``count > 6`` the pool is augmented with
    per-record story lines split from the ``verdict_story`` concatenation so
    longer threads draw from the underlying handover narrative rather than
    collapsing into pure filler.
    """
    raw_pool: list[str] = [
        context.get("verdict_story", ""),
        f"Phase trace: {context.get('phase_summary', '')}",
        f"Invariant protected: {context.get('invariant_protected', '')}",
        f"Title: {context.get('title', '')}",
        "Each step verified by the DeviaTDD micro-cycle.",
        "Drafts only — review, edit, publish manually.",
    ]
    if count > len(raw_pool):
        for line in context.get("verdict_story", "").split("\n"):
            stripped = line.strip()
            if stripped and stripped not in raw_pool:
                raw_pool.append(stripped)
    posts: list[str] = []
    for entry in raw_pool:
        if len(posts) >= count:
            break
        if not entry:
            continue
        truncated = truncate_post(entry)
        if truncated and truncated not in posts:
            posts.append(truncated)
    filler_index = 0
    while len(posts) < count:
        posts.append(truncate_post(f"Continued thread update {filler_index + 1}."))
        filler_index += 1
    return posts[:count]


def truncate_post(text: str) -> str:
    """Trim whitespace and hard-truncate to the X / Twitter limit."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= X_THREAD_LIMIT:
        return cleaned
    return cleaned[: X_THREAD_LIMIT - 1].rstrip() + "…"


__all__ = [
    "X_THREAD_COUNT",
    "X_THREAD_LIMIT",
    "build_context",
    "collect_anchor_field",
    "collect_stories",
    "load_template",
    "render_template",
    "render_x_thread",
    "slice_x_thread_posts",
    "summarise_phases",
    "truncate_post",
]
