# {{title}}

> {{verdict_story}}

## Problem

What we tried to solve; why it mattered now. Anchor to `{{invariant_protected}}`
only if it sets stakes. One paragraph. Do not bury the lede — this is the
section a reader skims to decide whether to keep reading.

## Attempt

Our first approach. Name the choice, not the files. Anchor to
`{{phase_summary}}` for the trace. Two or three sentences. Be specific
about WHY we chose this approach over the alternatives — vague attempts
signal shallow work.

## Failure

What broke. Concrete, not vague. Cite the test, the symptom, the commit,
the error message — anything the reader can verify. The Failure section
is what gives the post credibility; vague failures signal vague work.
Two or three sentences.

## Pivot

What we changed. The decision rationale. The moment we realized the
first approach wouldn't work and the second one would. Anchor to
`{{invariant_protected}}` — the durable claim is what was preserved or
restored. Two or three sentences.

## Insight

The generalizable lesson. The thing the reader can repeat back to their
team without re-reading the post. One paragraph. Resist the urge to
recap the timeline — the Insight is what the reader came for, not the
story.

## CTA

Invite: a reply, a follow, a repo link, a question, or a bridge to the
next post. Posts without a CTA lose engagement at the final scroll.

<!--
  blog-narrative.md — FLOW-12 blog format template (Problem → Attempt →
  Failure → Pivot → Insight → CTA narrative arc).

  Style reference: DevRel Bridge 2024 — narrative essay template for
  framework essays ("Why I added a human-in-the-loop gate", "What I learned
  shipping X for 6 months"). Dramatic arc beats the linear engineering-blog
  structure for posts whose primary purpose is sharing a personal lesson.

  Use this variant for: framework essays, decision-rationale posts,
  lessons-learned retrospectives where the structural lesson matters more
  than the technical walkthrough.

  The Failure section is load-bearing — it is what gives the post
  credibility. Vague failures signal vague work.

  Placeholders (substituted by synthesis.build_context()):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Verify the Failure section names a concrete, verifiable symptom.
    4. Delete this comment block before posting.
-->