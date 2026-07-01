---
title: "Why Diátaxis: The Architecture Behind This Docs Site"
description: "Why we chose Diátaxis's four-quadrant model for the DeviaTDD documentation site, the trade-offs we accepted, and what we rejected."
doc_type: explanation
status: draft
last_verified_at: 2026-07-01
verified_sha: c533ead
related_issues: []
---

This site is organised by the [Diátaxis framework](https://diataxis.fr/) — four registers (Tutorials, How-To, Reference, Explanation) that answer four different reader questions. We chose Diátaxis because DeviaTDD itself operates as a four-layer phase model (Macro → Meso → Micro), and a docs site that mirrors that cadence lets a reader pick the register that matches the moment.

## The problem with single-stream docs

A single docs stream (e.g., one big `docs/` folder, ordered by date or by feature) forces the reader to scan for the answer shape they need. A contributor looking up a flag does not want to read a tutorial; a beginner who needs a walkthrough does not want a parameter table. Single-stream docs punish both, and writers end up burying both kinds of content in the same prose.

## What we chose and why

We chose Diátaxis because the four-quadrant model matches DeviaTDD's three-layer architecture plus the human-in-the-loop gate between them. The mapping is:

- **Tutorials** — learning-oriented, mirrors the *Macro* layer (explore → research → prd → shard) for a reader who is new
- **How-To** — task-oriented, mirrors the *Meso* layer (plan → tasks) plus the *Micro* loop (red → green → refactor) for a reader with a specific job
- **Reference** — information-oriented, mirrors the *append-only ledgers* and the `src/deviate/` source-of-truth files
- **Explanation** — understanding-oriented, mirrors the *architecture* and *governance* surface

## Trade-offs we accepted

Adopting Diátaxis costs us: (1) every page must declare which quadrant it belongs to, which means writers can no longer blur registers inside a single file; (2) the IA is strict — a "quick start" that reads like a tutorial but is filed under how-to is a verifier finding; (3) theme sub-directories (e.g., `how-to/tdd-micro-cycle/`) pre-empt the writer's instinct to organise by topic, and any new theme has to be approved by the human.

The cost is paid for: a contributor running `/tasks` can `/how-to tdd-micro-cycle red` and reach the exact recipe without scrolling past narrative; a new operator running `deviate setup` can follow the tutorial without skimming past flag tables.

## Cross-references

- The first-task recipe lives at [How-To → Getting Started → Run Your First DeviaTDD Task](../../how-to/getting-started/starter-first-task.md)
- The config field reference lives at [Reference → Config Schema → Config Field Reference](../../reference/config/starter-config.md)
- The end-to-end tutorial lives at [Tutorials → Run Your First DeviaTDD Cycle](../../tutorials/starter-first-run.md)
