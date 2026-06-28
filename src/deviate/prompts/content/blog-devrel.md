# {{title}}

> {{verdict_story}}

## Introduction

Contract with the reader: what they will learn, what tech they will use,
how long it takes. Two or three sentences. Concrete > abstract. If the
reader finishes the intro and cannot state the takeaway in one sentence,
the intro failed.

## Background

Why this problem matters now; what was expensive or wrong about the status
quo. Anchor to `{{invariant_protected}}` if it sets stakes. One short
paragraph. Borrow a fact from `{{verdict_story}}` only if it grounds the
urgency — no preamble.

## Main Content

Walk through the approach. Anchor the arc to `{{phase_summary}}`. Code
snippets MUST be copy-paste runnable (developers test posts by pasting
them). Name the choices, not the files — readers skim for judgment, not
diffs. Use headings, tables, or bullet lists when they earn their keep.
Link to the spec or commit at the end of each major section.

## Conclusion

Recap the takeaway in one sentence. CTA: invite a reply, a follow, a
repo link, or a question. Bridge to the next-level resource (a deeper
blog, the docs site, the relevant `FLOW-XX`). Conclusion without a CTA
loses engagement at the final scroll.

## Takeaway

What we learned; what ships next; what we deliberately did NOT do and
why. One paragraph, honest voice. The paragraph the reader remembers.

<!--
  blog-devrel.md — FLOW-12 blog format template (DevRel Bridge 4-section voice).

  Style reference: DevRel Bridge 2024 — validated 4-section template
  (Intro → Background → Main Content → Conclusion) for tutorial and
  capability-launch posts. Closer to Stripe / Cloudflare engineering blog
  than the Saha reflective template.

  Use this variant for: tutorial posts ("How the AST parser detects library
  hallucinations"), capability launches ("Deviate v0.1 ships"), and any post
  whose primary purpose is teaching a concrete technique.

  Code-related requirements:
    - Code snippets must be copy-paste runnable.
    - Introduction = contract with reader.
    - Conclusion includes CTA + bridge to next-level resource.

  Placeholders (substituted by synthesis.build_context()):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Verify every code snippet runs as written.
    4. Delete this comment block before posting.
-->