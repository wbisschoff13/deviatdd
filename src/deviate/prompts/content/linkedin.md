# {{title}}

> {{verdict_story}}

## What I shipped

Two or three sentences. The change, the why, the result. Anchor to
`{{invariant_protected}}` — the durable claim. Lead with the outcome, not
the process. LinkedIn readers skim; the post must earn the second
sentence.

## Why it matters for builders

Career or workflow framing. The "if you ship X, you save Y" beat. What
the reader can take back to their team on Monday morning. Two or three
sentences. This section is what makes the post resume-grade vs.
product-noise.

## The technical bit

Anchor to `{{phase_summary}}` for the trace. Brief — LinkedIn readers
skim. Skip the architecture essay; name the seam. One short paragraph
or a tight bullet list. The point is to show competence, not exhaust
the reader.

## Open to builders

End on a question. Invite replies, follows, or DMs. LinkedIn's algorithm
rewards posts that generate comments in the first hour. A question is
the highest-leverage closer for that engagement curve.

<!--
  linkedin.md — FLOW-12 LinkedIn format template (resume-discoverability
  cross-post voice).

  LinkedIn posts serve a different function than the personal-website
  blog: they are the discoverability channel. The personal website is the
  central brand asset (per `developer-marketing-personal-branding-freelance`);
  LinkedIn provides the inbound audience that the website otherwise lacks.

  Use this variant for: cross-post of resume-grade blog posts. Do NOT
  use this for technical depth (the blog does that); use this for the
  career-narrative frame that hiring managers and peers actually engage
  with on LinkedIn.

  Voice rules:
    - First-person where natural. LinkedIn rewards personal voice.
    - Career-relevant framing. "Here's what I built and why it matters
      for builders" beats "Here's a technical walkthrough".
    - 150-300 words total. LinkedIn truncates longer posts; shorter is
      better.
    - End on a question or invitation. Drives comments.

  Placeholders (substituted by synthesis.build_context()):
    {{title}}              slug-derived heading
    {{verdict_story}}      judge-phase result; the lead
    {{phase_summary}}      phase trace
    {{invariant_protected}} invariant the change preserved or restored

  Editor workflow:
    1. Rewrite each section into publication prose.
    2. Replace the `{{ }}` placeholders with concrete details.
    3. Trim to 150-300 words. LinkedIn truncates longer posts.
    4. Verify the question / invitation is specific (not "thoughts?").
    5. Delete this comment block before posting.
-->