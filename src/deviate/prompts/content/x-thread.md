<!--
  x-thread.md — FLOW-12 x-thread format blueprint (X / Twitter-native voice).

  --------------------------------------------------------------------------
  IMPORTANT — this file is NOT rendered. The synthesis pipeline loads it
  (via load_template("x-thread") in src/deviate/core/synthesis.py) but
  render_template() short-circuits x-thread to render_x_thread(context)
  which builds the 6-post draft from the anchor pool. The {{post_N}}
  slots below are documentation, not slots the engine fills.

  This file exists so a human editor (and a future engineer reading the
  template source) can see the intended thread arc without having to
  reverse-engineer the slicer. If you change the arc, change the
  matching synthesis logic in slice_x_thread_posts() too.
  --------------------------------------------------------------------------

  Slot narrative — read top to bottom, post 1/6 is the hook:

    1/6 — hook.        State the result or the surprising fact. One line,
                       no setup. The post a stranger retweets without
                       reading the rest of the thread.

    2/6 — context.     Who is affected; what was expensive or broken
                       before; why this matters now. Name the actor and
                       the cost of the status quo. Concrete > abstract.

    3/6 — the move.    What we tried, named specifically. The action,
                       not the rationale. Avoid "we decided to" — write
                       "we built X" or "we replaced Y with Z".

    4/6 — proof.       Number, measurement, or before/after. The single
                       fact that converts a sympathetic reader into a
                       believer. If you have no number, name the test
                       count or the surface area reduced.

    5/6 — invariant.   What is now true that was not before. The durable
                       claim — the thing a reader can repeat back to
                       their team without re-reading the post.

    6/6 — payoff + CTA. Recap the takeaway in one sentence; invite a
                        reply, a follow, a repo link, or a question.
                        Threads without a CTA lose engagement at the
                        final post.

  Voice rules:
    - Tweet-native. Lower-case acceptable. Em dashes for emphasis.
    - Each post must stand alone — readers land mid-thread.
    - One idea per post. If a post tries to land two, split it.
    - Line breaks inside a post are fine if total stays ≤ 280 chars.
    - No corporate filler. "We're excited to announce" is a tell.

  --------------------------------------------------------------------------
  How synthesis produces the draft (see slice_x_thread_posts in
  src/deviate/core/synthesis.py:119-142):
  --------------------------------------------------------------------------

    Post 1 ← verdict_story (the result — usually a strong hook)
    Post 2 ← "Phase trace: <phase_summary>" (context — meta, weak)
    Post 3 ← "Invariant protected: <invariant_protected>" (the move)
    Post 4 ← "Title: <slug>" (placeholder — always rewrite)
    Post 5 ← "Each step verified by the DeviaTDD micro-cycle." (boilerplate)
    Post 6 ← "Drafts only — review, edit, publish manually." (CTA)

  The human editor is expected to:
    1. REWRITE posts 2, 4, and 5 (they are meta-narration, not thread voice).
    2. REORDER posts if the narrative arc demands it (post 4 is rarely the
       right slot for a proof point).
    3. ADD a concrete number or measurement somewhere in posts 2–5.
    4. KEEP posts ≤ 280 characters after edit.
    5. DELETE this comment block before publishing.

  --------------------------------------------------------------------------
  Rendered output shape (verified by tests/test_content/test_x_thread_format.py):
  --------------------------------------------------------------------------
  The draft is six posts separated by "---" lines. Each post is the
  content of one {{post_N}} slot as produced by the slicer. The template
  file is NOT in the output — only the slicer's posts are.
-->