---
title: "Run the /deviate-research phase"
description: "Consume explore.md and produce design.md + data-model.md; surface architectural decisions for HITL Gate 1 review."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
---

# Run the /deviate-research phase

This how-to covers `/deviate-research` — the second phase of the macro layer that consumes the empirical `explore.md` produced by [`/deviate-explore`](/how-to/explore) and emits a reasoned architectural design (`design.md`) plus a data model (`data-model.md`). After the slash command finishes, the human reviews the artifacts and either approves the design (unlocking [`/deviate-prd`](/how-to/prd)) or amends it. This phase is the only place a constitutional violation can be caught before downstream plan/tasks/implementation work begins, so the review step is the **non-bypassable HITL Gate 1** of the framework.

## Prerequisites

- **`/deviate-explore` completed** for the same feature — `specs/explore/<explore-slug>.md` must exist and pass `validate_artifact()`. The research phase reads `## File Registry`, `## Discovery Audit Results`, `## Architectural Baselines`, `## Ecosystem Research`, and `## Scope Sizing` from that file as the authoritative empirical input. If those sections are missing, run explore first.
- **`specs/constitution.md` present** — the research phase runs a constitutional alignment audit (Subagent Gamma) that quotes the `Architectural Principles` and `Testing Protocols` sections verbatim. Greenfield projects are an explicit exception: if the pre-script reports `is_greenfield=true`, the orchestrator bootstraps `specs/constitution.md` from explore findings before the subagent fork.
- **A clean working tree on the active feature branch** — `deviate research pre` allocates a numbered epic bucket at `specs/NNN-<explore-slug>/` and validates the working tree is clean. Uncommitted edits will cause the pre-script to fail.
- **A reasoning model available for the orchestrating agent** — the macro layer routes research to the high-cost tier (Qwen 3.7+ Thinking or V4 Pro per `specs/DeviaTDD-architecture.md` §4 and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].research`.
- **The same problem statement used for explore** — the research phase threads the original `<user_input>` through to Subagent Alpha, so the architectural analysis stays anchored to the same question that drove exploration.

## Steps

### 1. Confirm `explore.md` exists and is committed

Before invoking the slash command, verify the upstream artifact is in place. The pre-script returns `STATUS: EXPLORE_NOT_FOUND` if the file is missing or the working tree has uncommitted changes.

```bash
# Find the most recent explore.md
ls -t specs/explore/*.md | head -1

# Confirm it is committed (no uncommitted edits)
git status specs/explore/

# Sanity-check the required sections
grep -E "^## (File Registry|Discovery Audit Results|Architectural Baselines|Ecosystem Research|Scope Sizing)" specs/explore/<slug>.md
```

If the explore file is missing any of those sections, halt and re-run `/deviate-explore` with a tighter scope.

### 2. Run `/deviate-research` with the same problem statement

The slash command is the single primary action for this how-to. Pass the same problem statement you used for `/deviate-explore` so the architectural analysis stays anchored.

```bash
/deviate-research <your-problem-statement>
```

If you know the explore slug, pass it explicitly to skip auto-discovery:

```bash
/deviate-research --slug <explore-slug> <your-problem-statement>
```

The slash command orchestrates three sub-steps internally: the pre-script (next step), the subagent fork (step 4), and the post-script (step 7). You do not invoke them directly.

### 3. Wait for the pre-script to allocate the epic bucket

The slash command invokes `deviate research pre` first. The pre-script validates `explore.md`, transitions the session from `EXPLORE` to `RESEARCH`, pre-allocates `specs/NNN-<explore-slug>/` as the numbered epic bucket, and emits a JSON contract on stdout.

The contract contains `repo_root`, `git_branch`, `feature_slug`, `feature_dir`, `explore_md_path`, `design_target`, `data_model_target`, `constitution_path`, `epic_id`, and `is_greenfield` (boolean). The orchestrator threads these into the subagent prompts.

If the pre-script returns `STATUS: EXPLORE_NOT_FOUND`, halt and re-run `/deviate-explore`. Any other failure is surfaced verbatim; the agent does not proceed.

### 4. Wait for the subagent fork (or single linear pass)

For non-trivial features (the default), the orchestrator spawns three subagents in parallel:

- **Subagent Alpha** — Principal Systems Architect. Produces fragments for `## Recommended Architecture`, `## Options Matrix`, `## Rejected Options`, `## Design Trade-Offs`.
- **Subagent Beta** — Senior Data Modeler. Produces fragments for `## Entity Definitions`, `## Relationship Graph`, `## Schema Tables`, `## State Transitions`, `## Data Flow`.
- **Subagent Gamma** — Adversarial Architect. Produces fragments for `## Contrarian Viewpoints`, `## Risk Register`, and `## Constitutional Alignment Audit`.

For trivial features (one-file, one-script, single-language micro-projects), the fork collapses to a single linear pass and the subagent is skipped. The decision is made by the orchestrator based on the explore brief, not by you.

### 5. Scan Subagent Gamma's output for a Constitutional Violation block

This is the **only** gate against committing a constitutional violation. The post-script (`deviate research post`) is mechanical and will commit whatever files are pointed at it; it does not know about constitutional rules. The agent-level scan in this step is what protects the ledger.

If any row in Gamma's `## Constitutional Alignment Audit` has `Alignment: Violation`, the orchestrator:

1. Writes a `Constitutional Violation` block to `design_target` (top-level alert).
2. **Does not** write `data-model.md`.
3. **Does not** call the post-script.
4. Surfaces the violation to you and halts.

If you see a `Constitutional Violation` block in the agent's output, do not run the post-script. Amend the constitution, amend the design, or re-run `/deviate-explore` with a different problem statement.

### 6. Review `design.md` and `data-model.md`

Once the subagent fork completes and no violation is surfaced, the orchestrator merges the fragments into the two output contracts. Both files live under the pre-allocated epic bucket — typically `specs/NNN-<explore-slug>/design.md` and `specs/NNN-<explore-slug>/data-model.md`.

```bash
ls specs/NNN-*/
```

Read both files end-to-end. Pay particular attention to:

- **The `## Options Matrix`** — confirm the recommended option matches your domain understanding, and that every claim is anchored to a source path or verbatim quote.
- **The `## Risk Register`** — confirm risks are realistic (likelihood/impact ratings) and mitigations are concrete.
- **The `## Pending HITL Decisions` table** — every row with `Status: PENDING` will block `/deviate-prd` until you resolve it.
- **The `## Schema Tables`** in `data-model.md` — confirm the schema language matches the constitution's `Tech Stack Standards` (e.g., Pydantic models for Python, SQL DDL for SQL repos, Mongoose schemas for Node).

### 7. Resolve every PENDING HITL decision

The `## Pending HITL Decisions` table in `design.md` is the mechanism that enforces HITL Gate 1. The orchestrator will prompt you with a question for each row whose `Status: PENDING`. For each row:

- **Approve the recommended resolution** — change `Status` to `RESOLVED`. The gate is passed.
- **Reject and amend the design** — change the design first, then change `Status` to `RESOLVED`.
- **Defer to a later phase** — leave `Status: PENDING`; `/deviate-prd` will halt and re-display the table.

If any row is `PENDING` when `/deviate-prd` runs, the pre-script for that phase halts and the human must resolve it before PRD can proceed. Treat the table as the single source of truth for unresolved architectural questions.

### 8. Verify the commit and the artifacts

The post-script validates both artifacts, runs pre-commit hooks (including the full test suite — allow at least 180s), creates a single commit, and saves the session. Confirm everything landed.

```bash
# Latest commit should include both research artifacts
git log --oneline -1
git show HEAD --stat | grep -E "design\.md|data-model\.md"

# Both files should be readable
test -f specs/NNN-<slug>/design.md && echo "design.md OK"
test -f specs/NNN-<slug>/data-model.md && echo "data-model.md OK"

# The session should have advanced to AWAITING_HITL_GATE_1
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

Expected session phase: `RESEARCH` (still) with status `AWAITING_HITL_GATE_1` — the human review of the artifacts is the gate, not the commit.

## Troubleshooting

### Pre-script returns `STATUS: EXPLORE_NOT_FOUND`

`specs/explore/<slug>.md` is missing, the file is uncommitted, or the explore phase has not been run for this feature. Re-run `/deviate-explore <problem-statement>` first; the research phase has no fallback if the empirical context is absent.

### Subagent Gamma surfaces a `Constitutional Violation` block

The proposed architecture violates a clause in `specs/constitution.md`. The orchestrator writes a `Constitutional Violation` block to `design.md` and halts without committing. Read the block — it names the violating decision, the violated constitutional clause, and the rejected alternative. Then pick one of three actions:

- **Amend the constitution** to permit the architecture (use `/deviate-constitution`).
- **Amend the design** to comply with the constitution (edit `design.md` and re-run the subagent fork or amend the matrix directly).
- **Re-run `/deviate-explore`** with a different problem statement that does not push against the constitutional clause.

Never run the post-script manually after a `Constitutional Violation` block — the post-script is mechanical and will commit the violating architecture.

### `deviate prd pre` halts on a `PENDING` HITL decision

You approved the design without resolving every row in `## Pending HITL Decisions`. Re-open `design.md`, find rows with `Status: PENDING`, and either change `Status` to `RESOLVED` (with a note in the `Recommended Resolution` column) or amend the design to remove the row. The gate rule is: zero `PENDING` rows in the table before `/deviate-prd` will run.

### Post-script times out or fails

The post-script runs pre-commit hooks including the full test suite. On large repos or slow CI, this can exceed 3 minutes. If it times out, increase the timeout to ≥ 180s and re-run. If it still fails, read the post-script output; common causes are:

- A pre-commit hook is rejecting content in `design.md` or `data-model.md` (e.g., a lint rule against the source-anchor quote style, or a markdown linter rejecting the tables).
- The test suite is failing for an unrelated reason. Run `mise run test` (or your repo's `TEST_COMMAND` from the constitution) in isolation to diagnose.

If the commit is partial, restore the working tree (`git checkout -- specs/NNN-*/`) and re-run the post-script once the underlying issue is fixed.

### Numbered epic bucket was allocated but no artifacts landed

`deviate research pre` allocates `specs/NNN-<slug>/` even on the adhoc routing path (where the actual research artifacts go to `specs/adhoc/` instead). If the slash command routed to adhoc because `## Scope Sizing` in `explore.md` classified the feature as low-complexity, the numbered directory is an untracked artifact and can be cleaned up with `git clean -fd specs/NNN-*/`. The explore file remains in `specs/explore/` for adhoc reuse.

## Next Steps

- [How to run /deviate-prd](/how-to/prd) — the next macro phase after research; the pre-script enforces that every `PENDING` HITL decision is resolved before PRD will run.
- [How to run /deviate-explore](/how-to/explore) — the prerequisite phase; research consumes the explore brief.
- [Reference: `deviate research pre` / `deviate research post`](/reference/cli) — the CLI surface for the pre/post scripts; flag tables and exit-code semantics.
- [Reference: HITL Gate 1 triggers](/reference/hitl-gates#gate-1) — the exact conditions that cause Gate 1 to halt downstream phases.
- [Explanation: HITL Gate 1](/explanation/hitl-gates) — why the design review gate exists, what it prevents, and how it interacts with the constitutional alignment audit.
- [Explanation: append-only ledger discipline](/explanation/append-only-ledger) — why `specs/issues.jsonl` and the per-issue `tasks.jsonl` are append-only and how the research commit fits into the ledger.
