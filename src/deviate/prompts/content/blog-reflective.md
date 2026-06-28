# {{title}}

> {{verdict_story}}

## About the project

Who this work is for; what the project is; the code snippet or commit that
grounds the post. Anchor to `{{invariant_protected}}` only if it sets
stakes. One short paragraph. Assume the reader knows the domain — do not
introduce the project from scratch.

## The decision / issue

What you addressed; why now. For a retrospective, name the arc of the
project that surfaced this work; for a decision essay, name the moment a
choice had to be made. Anchor to `{{phase_summary}}` for the trace. One
short paragraph. Be specific — vague problems get vague engagement.

## Codebase / system

The tech stack, system shape, or workflow the reader needs to follow the
rest. A short ASCII diagram or one sentence per component is enough. Cite
`src/` paths verbatim. Skip the architecture essay — name the seams, not
the philosophy.

## What I tried (and what failed)

The interesting part. For a retrospective: at least three self-directed
attempts (one of which is the one that worked); who you reached out to (or
why you didn't). For a decision essay: the alternatives considered, with
the reason each was rejected. Cite constitution clauses or research
sources when relevant. This is the paragraph that does the heavy lifting
for resume credibility. Be honest about what failed — vague attempts
signal vague work.

## Solution

The final approach; the test or commit that proves it; the PR or commit
that landed it. Anchor to `{{invariant_protected}}` — the durable claim
is what the reader can repeat back to their team. One paragraph. End
with a link.

## Takeaway

What you learned; what ships next; what you deliberately did NOT do and
why. One paragraph, honest voice. This is the paragraph the reader
remembers — do not bury it under solution recap.

<!--
  blog-reflective.md — FLOW-12 blog format template (merged Saha +
  narrative reflective voice).

  This template covers BOTH:

    1. Process retrospective (Saha et al. 2026 5-section template):
       a longitudinal "what I learned shipping X" essay. Resume-grade
       voice. Use for sprint reviews, what-worked-what-didn't posts.

    2. Decision-rationale essay (Problem → Attempt → Failure → Pivot →
       Insight narrative arc): a "why I made this decision" essay.
       Framework-essay voice. Use when the structural lesson matters
       more than the technical walkthrough.

  The 6 sections above accept both shapes:

    About the project     → context for either shape
    The decision / issue  → the arc (retrospective) OR the choice point (essay)
    Codebase / system     → technical grounding
    What I tried          → 3+ attempts (retrospective) OR alternatives rejected (essay)
    Solution              → the result either way
    Takeaway              → the lesson either way

  Use this variant for: any reflective, resume-grade blog post. Cadence:
  1 per month. The reflective voice takes more craft than the
  engineering-blog `blog.md` voice; ship 1 per month, not 1 per week.

  Do NOT use this for:
    - Technical walkthroughs of what changed ("here is the new feature"):
      use `blog` instead.
    - Tutorials / capability launches ("here is how to use X"):
      use `blog-devrel` instead.

  Placeholders (substituted by synthesis.build_context()):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace (e.g. "red → green → judge → refactor")
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Pick a shape: retrospective OR decision essay. The "What I tried"
       section adapts to whichever you picked.
    4. Verify the "What I tried" section names ≥3 attempts / alternatives.
    5. Delete this comment block before posting.
-->