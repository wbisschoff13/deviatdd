# {{title}}

> {{verdict_story}}

## TL;DR

Two or three sentences a skim-reader absorbs: the change, the why, and
the result. Lead with the dominant phase from `{{phase_summary}}` or
the most concrete fact in `{{verdict_story}}`. If neither lands a
result, name the invariant from `{{invariant_protected}}` and stop.

## Context

Who hit this problem; what was expensive or wrong about the status
quo; why this work matters now. One short paragraph. Assume the reader
knows the domain — do not introduce the project. Borrow a concrete
fact from `{{verdict_story}}` only if it sets stakes.

## Approach

Walk through what we tried, what survived, what we threw away. Anchor
the arc to `{{phase_summary}}`. If the trace is thin, infer the steps
from the verbs in `{{invariant_protected}}`. Name the choices, not the
files — readers skim for judgment, not diffs.

## What Changed

The concrete delta, in one or two short paragraphs. Name the invariant
from `{{invariant_protected}}`, the change that broke or restored it,
and why the change is durable. Avoid listing every file touched; name
the seams.

## Takeaway

What we learned; what ships next; what we deliberately did NOT do and
why. One paragraph, honest voice. This is the paragraph the reader
remembers — do not bury it under approach recap. If the work raises a
new question, end on the question, not the result.

<!--
  blog.md — FLOW-12 blog format template (engineering-blog voice).

  Style reference: Increment, Stripe, Cloudflare engineering blogs.
  Sections are ordered for skim-then-deep reading: Hook → TL;DR →
  Context → Approach → What Changed → Takeaway.

  Placeholders (substituted by synthesis.build_context() in
  src/deviate/core/synthesis.py):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace (e.g. "red → green → judge → refactor")
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Delete this comment block before posting.
-->