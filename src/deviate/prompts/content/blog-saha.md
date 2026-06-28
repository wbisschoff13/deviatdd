# {{title}}

> {{verdict_story}}

## About the project

Who hits this problem; what the project is; the code snippet that grounds
the post. Anchor to `{{invariant_protected}}` only if it sets stakes. One
short paragraph. Assume the reader knows the domain — do not introduce
the project from scratch. If a tag, commit, or repo URL belongs here,
include it.

## The issue

What you addressed; why now; the supporting artifact (failing test, ADR,
spec, incident). Anchor to `{{phase_summary}}` for the trace. One short
paragraph. Be specific — vague problems get vague engagement.

## Codebase overview

The tech stack, the system shape, the workflow the reader needs to follow
the rest of the post. A short ASCII diagram or a single sentence per
component is enough. Cite `src/` paths verbatim. Skip the architecture
essay — name the seams, not the philosophy.

## Challenges

The specific technical challenge; at least three self-directed attempts
(one of which is the one that worked); who you reached out to (or why
you didn't). This is the paragraph that does the heavy lifting for resume
credibility. Be honest about what failed — vague challenges signal vague
work.

## Solution

The final approach; the test that proves it; the PR or commit that landed
it. Anchor to `{{invariant_protected}}` — the durable claim is what the
reader can repeat back to their team. One paragraph. End with a link.

## Takeaway

What you learned; what ships next; what you deliberately did NOT do and
why. One paragraph, honest voice. This is the paragraph the reader
remembers — do not bury it under solution recap.

<!--
  blog-saha.md — FLOW-12 blog format template (Saha et al. 5-section voice).

  Style reference: Saha et al. 2026 (n=25, κ=0.78) validated 5-section
  template for resume-grade reflective writing. Sections are ordered for
  reflective depth: Project → Issue → Codebase → Challenges → Solution,
  closed by a Takeaway paragraph the reader remembers.

  Use this variant for: process retrospectives, sprint reviews, "what worked
  and what didn't" essays. The resume-grade voice takes more craft than the
  engineering-blog `blog.md` voice; ship 1 per month, not 1 per week.

  Placeholders (substituted by synthesis.build_context() in
  src/deviate/core/synthesis.py):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace (e.g. "red → green → judge → refactor")
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Verify the Challenges section names ≥3 self-directed attempts.
    4. Delete this comment block before posting.
-->