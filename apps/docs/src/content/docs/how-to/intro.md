---
title: "How-Tos: accomplish a specific task"
description: "Task-oriented guides for operators and contributors who already know what they want to do and just need the steps to do it."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-011
---

# How-Tos: accomplish a specific task

This quadrant is for readers who have prior context about DeviaTDD and now need to *get something done*. Each how-to covers exactly **one** operator or contributor task end-to-end — install DeviaTDD, run a particular slash command, scaffold a project, recover from a hotfix. The reading order is: pick the task you need, follow the steps, verify, troubleshoot. There is no learning narrative here; if you need foundational concepts, link out to a tutorial or an explanation.

## Getting Started

- [Bootstrap a DeviaTDD workspace](/how-to/setup) — run `deviate setup` to install the slash-command library, scaffold `.deviate/config.toml`, and seed the append-only ledger merge rules.
- [Initialize a repo with DeviaTDD conventions](/how-to/init) — scaffold `mise.toml`, `specs/`, and a starter `constitution.md` for a fresh repository.
- [Run the /deviate-constitution workflow](/how-to/constitution) — initialize or amend `specs/constitution.md`, the canonical governance artifact every macro phase consults; update tech-stack standards, testing mandates, or Definition of Done clauses.

## Daily Tasks

- [Scaffold a feature workspace](/how-to/feature) — run `deviate feature create <title>` to derive a kebab-case slug, create the `feat/<slug>` branch, scaffold `specs/<slug>/`, and reset the session; the greenfield entry point before `/deviate-explore` runs (also invoked implicitly by explore/specify/plan as phase step 1).
- [Run the /deviate-explore phase](/how-to/explore) — produce `specs/explore/<slug>.md` with a read-only scan of the codebase and route the next phase on Scope Sizing (Low/Medium → `/deviate-adhoc`, High → `/deviate-research`).
- [Run the /deviate-adhoc phase](/how-to/adhoc) — emit a single spec-enriched vertical-slice issue from a natural-language task with lightweight discovery, shared PRD tracking, and flow_refs; the macro-layer fast-path for Low/Medium complexity work that bypasses explore→research→prd→shard.

- [Run the /deviate-research phase](/how-to/research) — consume `explore.md` and produce `design.md` + `data-model.md` for HITL Gate 1 review.
- [Run the /deviate-prd phase](/how-to/prd) — compile the research artifacts into `prd.md`, the singular source of truth for downstream sharding.
- [Run the /deviate-shard phase](/how-to/shard) — decompose `prd.md` into self-contained Feature Vertical issues, register them in `specs/issues.jsonl`, and surface the DAG topology for HITL Gate 2 review.
- [Run the /deviate-plan phase](/how-to/plan) — claim the next unblocked BACKLOG issue from `specs/issues.jsonl`, create its dedicated git worktree at `.worktrees/feat/<epic>/<issue>/`, and emit `plan.md` (the meso bridge between shard and tasks; `/deviate-specify` was absorbed into `/deviate-shard` per the v2.0 CHANGELOG).
- [Run the /deviate-tasks phase](/how-to/tasks) — decompose a spec-enriched issue (with optional `plan.md` from `/deviate-plan`) into `tasks.md` — autonomous Red-Green-Refactor units, 30–90 min each, with deterministic `Verification` commands.
- [Run the /deviate-red phase](/how-to/red) — write a failing test for the next PENDING task in the active issue, verify it crashes (not passes), then commit the RED-state artifact via the post-script.
- [Run the /deviate-green phase](/how-to/green) — implement the minimal production code that turns the RED test green, then commit through the mandated `deviate green post` script and emit the `GREEN_STATE_ACHIEVED` handover manifest (or `yellow_trigger: true` after three failed post-script attempts).
- [Run the /deviate-yellow phase](/how-to/yellow) — evaluate a GREEN-phase test-amendment proposal via `/deviate-yellow` and commit or revert the changes via `deviate yellow post --approved` (or `--rejected`); the conditional TamperGuard-triggered amendment gate of the TDD micro-cycle.
- [Run the /deviate-judge phase](/how-to/judge) — run the V4-Pro isolated JUDGE phase (standalone or as a post-GREEN re-evaluation) against `spec.md` for correctness and integrity; emit `COMPLIANCE_PASS` or `COMPLIANCE_VIOLATION` with structured `train_feedback` that trains the next GREEN attempt on rejection.
- [Run the /deviate-refactor phase](/how-to/refactor) — improve structure and clarity of the GREEN implementation while preserving public behavior; the post-script re-runs the test suite, rejects any change that alters test output, and commits the cleanup.
- [Run the /deviate-execute phase](/how-to/execute) — execute a single DIRECT-mode task (boilerplate, config, docs, or trivial refactor with existing coverage) by running the `/deviate-execute` slash command; the pre/post pair, `mise run check` validation, and auto-commit, with no RED/GREEN/REFACTOR cycle.
- [Run a task via the micro dispatcher](/how-to/run) — invoke `deviate run` to resolve the next `PENDING` task (by ID or by walking the active issue) and route it through the TDD cycle or the `EXECUTE` phase per its `execution_mode`; the user-visible micro-layer entry point (no slash prompt at this layer).
- [Open the PR for the active worktree](/how-to/pr) — run `/deviate-pr` after `/deviate-tasks` lands; creates the GitHub PR from the per-issue branch, appends `COMPLETED` to `specs/issues.jsonl`, and unblocks dependents via the `blocked_by` resolver.

## Recovery & Maintenance

- [Run the /deviate-hotfix workflow](/how-to/hotfix) — decompose a bug report into 1–2 autonomous Red-Green-Refactor units via the `/deviate-hotfix` slash command; bypasses RED and commits a `tasks.md` of targeted, bounded bug fixes.

## Cross-Quadrant Links

- [`Tutorials: a guided tour`](/tutorials/intro) — beginner walkthroughs that build context before a how-to.
- [`Reference: look something up`](/reference/intro) — flag tables, schema details, and lookup material for already-running commands.
- [`Explanation: understand the why`](/explanation/intro) — design rationale and architectural context for the choices a how-to exercises.

## Next Steps

- [Bootstrap a DeviaTDD workspace](/how-to/setup) — the first concrete task for a new operator; everything else in this quadrant depends on it.
