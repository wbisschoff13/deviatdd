# {{title}}

> {{verdict_story}}

## TL;DR

Two or three sentences a skim-reader absorbs: the change, the why, the
result. Lead with the dominant phase from `{{phase_summary}}` or the most
concrete fact in `{{verdict_story}}`. If neither lands a result, name
the invariant from `{{invariant_protected}}` and stop.

## What I tried

Walk through the approach. Anchor the arc to `{{phase_summary}}`. Name
the choices, not the files. Two or three sentences — Threads posts are
long-form but each section must earn its scroll. Inline screenshots from
the AST parser output land well here (call-graph screenshots, KCH
detection samples, indexing-speed benchmarks).

## Result

Numbers mandatory. What improved, by how much. Latency, error rate,
test count, line count — any specific number. The `{{invariant_protected}}`
anchor frames the durability of the result. If the result is qualitative
(\"the agent now reasons about X\"), convert it to a proxy number
(\"added 12 anchored fields across 4 phases\").

## Insight

One lesson, generalized. The thing the reader can repeat back to their
team. One or two sentences. Resist the urge to recap the timeline — the
Insight is what the reader came for, not the story.

## Open question

End on a question, not a result. Invite replies. Threads's reply-driven
engagement rewards posts that hand the conversation back to the reader.
A post that ends with a result is a closed loop; a post that ends with a
question is an open thread.

<!--
  threads.md — FLOW-12 Threads format template (Meta Threads-native voice).

  Threads posts are longer-form than X (paragraphs of 200-500 chars are
  fine), narrative-tolerant, and visually support code-snippet screenshots
  from the AST parser output. Cadence: 1 Threads post per week (lower than
  X because each post takes more craft). Visual format supports inline
  screenshots — leverage the AST parser demo machine here.

  Why Threads is distinct from X (per the build-in-public research):
    - Higher tolerance for long-form narrative (Meta's text-first positioning).
    - Lower saturation for technical content = higher differentiation per post.
    - Visual format supports code-snippet screenshots from AST parser output.
    - Linked to Instagram ecosystem (potential downstream cross-post to IG
      carousels).

  Voice rules:
    - Lowercase acceptable. Em dashes for emphasis.
    - Long paragraphs OK (this is NOT X — paragraphs of 200-500 chars work).
    - End on a question, not a result (drives reply engagement).
    - One idea per section. If a section tries to land two, split it.
    - No corporate filler. "We're excited to announce" is a tell.

  Placeholders (substituted by synthesis.build_context()):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Add a specific number or measurement in the Result section.
    4. Add a screenshot path from the AST parser output if applicable.
    5. Delete this comment block before posting.
-->