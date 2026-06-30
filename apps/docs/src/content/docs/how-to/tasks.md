---
title: "Run the /deviate-tasks phase"
description: "Decompose a spec-enriched issue (with optional plan.md from /deviate-plan) into tasks.md — autonomous Red-Green-Refactor units, each 30–90 min, with deterministic Verification commands."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
---

# Run the /deviate-tasks phase

This how-to covers `/deviate-tasks` — the meso-layer phase that decomposes a spec-enriched issue file (the output of [`/deviate-shard`](/how-to/shard)) into a vertical-slice `tasks.md` artifact. When [`/deviate-plan`](/how-to/plan) preceded it, `tasks.md` reads from `plan.md` for workstation and risk-mapping context; otherwise the slash command reads spec content directly from the issue file's embedded `## User Stories Ledger` and `## ATDD Acceptance Criteria` sections (with a fallback to an adjacent `spec.md` per `src/deviate/prompts/commands/deviate-tasks.md`). Each task is a deterministic instruction for the downstream TDD layer — Mode (`TDD` / `IMMEDIATE`), Test Strategy, Verification command, file list with `Rationale`, and a four-to-eight bullet `Details` block under the issue directory at `specs/{epic}/issues/{slug}/tasks.md`. The slash command orchestrates the pre-script (`deviate tasks pre`, which detects the worktree and emits a JSON contract), the task generation pass, and the post-script (`deviate tasks post`, which validates task ID format `TSK-{NNN}-{NN}` and commits) — you invoke them only as the slash command's internal sub-steps.

## Prerequisites

- **`/deviate-shard` completed for the same epic** — the tasks phase reads from the spec-enriched issue file (`specs/{epic}/issues/{slug}.md`) registered in `specs/issues.jsonl`. If the issue file lacks embedded spec sections, an adjacent `spec.md` must exist in the same issue directory as the legacy fallback. The pre-script returns `ISSUE_NOT_FOUND` when the active issue's source file does not exist, or `SPEC_NOT_FOUND` when the session has no `active_issue_id` — both halts surface verbatim and require running `/deviate-shard` first.
- **HITL Gate 2 (post-shard review) passed** — every shard issue is reviewed for vertical-slice integrity, complete `## Demonstration Path` blocks, DAG sanity, and FR coverage before `deviate shard post` commits the ledger. Tasks inherits the gate; if the shard review surfaced anything unresolved, return to [`/deviate-shard`](/how-to/shard) step 6 before running tasks.
- **Active worktree on the feature branch for this issue** — `deviate tasks pre` resolves the worktree via `Path.cwd()` (`src/deviate/cli/meso.py:939`), so the slash command must run from inside the per-issue worktree, not from the worktree-orchestrator root. `_resolve_bucket_dir()` and `_source_stem()` then derive `tasks_target = <specs_root>/<bucket>/<slug>/tasks.md` from the active issue's `source_file` (`src/deviate/cli/meso.py:967`).
- **A clean session in `PLAN`, `SPECIFY`, or `TASKS` phase** — `_load_session_accept()` accepts those three pre-script gates (`src/deviate/cli/meso.py:915`); the session may have advanced through `_plan_post` or still be in `SHARD` after a manual recovery. Pass `--force` to bypass phase validation when running on a branch where the state machine was reset between attempts.
- **(Optional) `plan.md` from `/deviate-plan` in the same issue directory** — when present, tasks reads it for `RISK_REGISTER`, workstation mapping, and architectural context (`src/deviate/prompts/commands/deviate-tasks.md` execution step 2). Absent `plan.md` is a soft gap — the slash command falls back to spec-only decomposition and the artifact still lands, with a noted `[WARNING]` on any tasks touching areas the plan would have clarified.
- **A reasoning model available for the orchestrating agent** — the meso layer routes tasks to the mid-cost tier (V4 Pro or a configured override per `specs/DeviaTDD-architecture.md` §4 and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].tasks`.
- **A `specs/constitution.md` matching the active repository** — the pre-script pulls `constitution_test_command` and `constitution_lint_command` from the constitution (`_resolve_constitution_commands`, `src/deviate/cli/meso.py:956`) so the generated `Verification` commands honor your test runner and lint runner. A missing or stale constitution risks `Verification` lines that no agent can run; validate with `test -f specs/constitution.md`.

## Steps

### 1. Confirm the active issue, the worktree, and (optionally) the plan

Before invoking the slash command, verify the upstream gates. The pre-script halts with `ISSUE_NOT_FOUND` when the active issue's source file is missing and `SPEC_NOT_FOUND` when the session has no `active_issue_id` — both halts are easier to diagnose from a pre-flight than after the slash command's first sub-step.

```bash
# Session has an active issue (advance this with `deviate plan post --issue-id ISS-NNN-NNN` if needed)
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('issue:', s.get('active_issue_id')); print('phase:', s.get('current_phase'))"

# The active issue's source file exists in the ledger
jq -r 'select(.issue_id=="ISS-001-001") | .source_file' specs/issues.jsonl
test -f specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>.md && echo "issue file OK"

# Spec source: embedded sections in the issue file (preferred) or spec.md (fallback)
grep -E "^## User Stories Ledger|^## ATDD Acceptance Criteria" specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>.md
test -f specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/spec.md && echo "spec.md fallback OK"

# Optional plan.md from /deviate-plan is present when expected
test -f specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/plan.md && echo "plan.md OK"

# cwd is the worktree-rooted per-issue branch (not the orchestrator root)
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
```

If the slash command will run in the same per-issue worktree the previous phase used, `git status` should also be clean. Uncommitted edits on `plan.md` or the issue file will be swept up by the post-script's commit.

### 2. Run `/deviate-tasks`

The slash command is the single primary action for this how-to. It orchestrates the pre-script, the spec/plan ingestion pass, the task generation, and the post-script internally. Pass the active issue ID if it is not yet anchored to the session — otherwise the slash command reads it from `.deviate/session.json`.

```bash
/deviate-tasks
```

Or pass the issue ID explicitly to bind the session before the slash command runs:

```bash
/deviate-tasks ISS-001-001
```

The slash command routes through five sub-steps internally: the pre-script (next step), the spec/plan ingestion (step 4), the workstation-mapping + task construction pass (step 5), the file write (step 6), and the post-script (step 7). You do not invoke any of them directly.

### 3. Wait for the pre-script to detect the worktree and emit a contract

The slash command invokes `deviate tasks pre` (`src/deviate/cli/meso.py::_tasks_pre`). The pre-script:

1. Loads the session and accepts phases `PLAN`, `SPECIFY`, or `TASKS` (`_load_session_accept`).
2. Resolves `issue_id` from `session.active_issue_id`.
3. Locates the issue file via `_find_issue_file(issue_id)` and prints `[green]SPEC_DISCOVERED[/] <path>`. If absent, prints `[red]ISSUE_NOT_FOUND[/]` and emits `status: ISSUE_NOT_FOUND`.
4. Calls `Path.cwd()` for `worktree_full` and `git rev-parse --abbrev-ref HEAD` for `branch_name`, printing `[green]WORKTREE[/] <path> [<branch>]` — the pre-script assumes the worktree is the current working directory.
5. Resolves `constitution_path`, `constitution_test_command`, `constitution_lint_command` for the generated `Verification` lines.
6. Resolves `tasks_target = <specs_root>/<bucket>/<slug>/tasks.md` from the active issue's `source_file` via `_resolve_bucket_dir()` + `_source_stem()`.
7. Emits a JSON contract on stdout with `issue_id`, `spec_path`, `tasks_target`, `worktree_full`, `branch_name`, `constitution_path`, `constitution_test_command`, `constitution_lint_command`, `status`, `phase: "tasks_pre"`, `force`, `dry_run`, and `timestamp`.

If the contract reports `status: ISSUE_NOT_FOUND`, the slash command halts — confirm the active issue in `specs/issues.jsonl` resolves to a file that exists on disk. If it reports `status: SPEC_NOT_FOUND`, return to step 1 and bind an `active_issue_id`.

### 4. Wait for spec and plan ingestion

The orchestrator reads the spec source from `spec_path`. There are two cases (`src/deviate/prompts/commands/deviate-tasks.md` `<system_instructions>` and `<edge_case_handling>`):

- **Primary path** — the issue file contains embedded `## User Stories Ledger` and `## ATDD Acceptance Criteria` sections. The orchestrator reads spec content directly from the issue file and ignores `spec.md` even if present. Precedence rule per spec `AC-ADHOC-003-07`.
- **Legacy path** — the issue file lacks embedded sections. The orchestrator falls back to the adjacent `spec.md` file in the same issue directory and logs `[WARNING] issue file lacks embedded spec sections`. If `spec.md` is also missing or missing required sections, the slash command halts with `Invalid spec source — missing required sections`.

When `plan.md` exists in the same issue directory, the orchestrator also reads it for `RISK_REGISTER`, workstation mapping, and architectural risk context (execution step 2 of the prompt). Absent `plan.md` is acceptable; the orchestrator decomposes from spec alone.

Research artifacts (`design.md`, `data-model.md` from [`/deviate-research`](/how-to/research)) are not consumed directly at this stage — they live one level up at `specs/{epic}/` and surface context only when the spec or plan references them.

### 5. Watch the workstation mapping and task construction pass

The orchestrator runs four internal transforms before writing the artifact (`src/deviate/prompts/commands/deviate-tasks.md` execution steps 3 and 4):

- **Workstation Mapping** — for every user story, map the files touched from the spec source's `SYSTEM_TOPOLOGY_MAPPING` and `PROJECT_STRUCTURE` sections. Group related files (a service + its test file, a handler + its route registration) into workstation clusters.
- **Task Grouping (4a)** — group workstation clusters into **Batched Logical Units** (vertical slices), each delivering one or more acceptance criteria.
- **Execution Mode (4b)** — apply the decision tree per task. Default to `IMMEDIATE` when in doubt; reserve `TDD` for new business logic, state mutations, API endpoints, integration boundaries, bug fixes, and non-trivial acceptance criteria (decision-tree branches 3–5 and 7 in the prompt). Trivial config/docs/boilerplate and pure refactors with existing test coverage are `IMMEDIATE`.
- **Verification + Rationale (4c, 4e)** — every task gets a deterministic `Verification` CLI command (defaults to `constitution_test_command` when no specific runner applies), an explicit inline `Dependency` (when applicable), and a `[File_Rationale]` tying every file to a story ID and AC.

TDD tasks must have at least one **Red** bullet (specific test case + assertion) and one **Green** bullet (function signature + logic). IMMEDIATE tasks use **Implementation** in place of Red/Green. Every task's `Details` block carries 4–8 bullets covering **Edge Cases** and **Acceptance** where applicable (`src/deviate/prompts/commands/deviate-tasks.md` `<output_format_schemas>`).

This step can take several minutes on the mid-cost tier model. Let it run; do not interrupt the orchestrator mid-generation.

### 6. Confirm the artifact write and task ID format

After task generation, the orchestrator writes the entire decomposition directly to `tasks_target` with no preamble, no postamble, no XML wrapper — the file content **is** the ledger body. The post-script's task-ID validator (`src/deviate/cli/meso.py::_tasks_post`) enforces strict format `^TSK-\d{3}-\d{2}:$` per task, so verify the format before the post-script runs:

```bash
cat specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md | head -50

# Mandatory task ID pattern — every task heading line must match TSK-NNN-NN
grep -oE '^TSK-[0-9]{3}-[0-9]{2}:' specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md | sort -u

# No banned legacy ID shapes (T001:, T-001:, TASK1:, TSK001:)
! grep -E '^(T[0-9]{3}:|T-[0-9]{3}:|TASK[0-9]+:|TSK[0-9]{3}:)' specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md && echo "no legacy IDs"

# Phase headers use ## Phase N: <Feature Slice Name>
grep -E '^## Phase [0-9]+:' specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md
```

If the artifact has malformed IDs (the legacy `T001:` shapes), halt before the post-script runs and ask the orchestrator to regenerate. The post-script will reject the file and surface a diagnostic, but a pre-emptive check is faster.

### 7. Run the post-script to validate and commit

Once the artifact is in the right shape, invoke the post-script directly. The post-script loads the session (must be in `TASKS` — use `--force` to bypass), re-resolves the artifact path from the active issue, validates non-empty content unless `--force` is passed, runs pre-commit hooks (the full test suite, ~180s allocation), commits as `docs(<epic_num>-<issue_num>): create tasks.md` via `commit_artifact(..., no_verify=True)` (`src/deviate/cli/meso.py::_tasks_post`), transitions the session to `IDLE`, and prints `[green]COMMITTED[/] tasks.md at <sha[:8]>`.

```bash
deviate tasks post
```

The `--force` and `--issue-id` flags are available for recovery flows:

```bash
deviate tasks post --issue-id ISS-001-001
deviate tasks post --force                # bypass session-phase check
```

After the post-script returns, `TERMINATE HERE` per the slash command contract — the operator hands off to the TDD layer (`/deviate-red` → `/deviate-green` → `/deviate-judge` → `/deviate-refactor`) for each task.

### 8. Verify the artifact, the commit, and the session transition

Confirm every piece landed. The artifact must exist at the per-issue path, the ledger commit must include it, and the session must have advanced to `IDLE`.

```bash
# Latest commit must include tasks.md at the per-issue path
git log --oneline -1
git show HEAD --stat | grep "tasks.md"

# Artifact is readable and has the required sections
test -f specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md && echo "tasks.md OK"
grep -E '^(# Implementation Tasks: |## Phase [0-9]+:|## Implementation Strategy|## Universal Test Constraints|## Universal API Design Constraint)' \
  specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md

# Every task heading line is valid
grep -oE '^TSK-[0-9]{3}-[0-9]{2}:' specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md | wc -l   # expected ≥ 1, ≤ 10 per issue

# Each task carries Verification command and at least one Files entry
grep -c "Verification" specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md
grep -c "Files" specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md

# Session advanced to IDLE (handoff to TDD layer)
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

Expected session phase: `IDLE`. The session exits `TASKS` once the post-script commits. The TDD layer is now unlocked but does not auto-run — it waits for `/deviate-red <TASK_ID>` against each task.

## Troubleshooting

### Pre-script emits `ISSUE_NOT_FOUND`

`deviate tasks pre` could not locate the issue file for the active `issue_id`. The pre-script prints the missing identifier. Two common causes: the active issue id in `.deviate/session.json` was reset by an earlier `deviate plan post` against a different issue (re-bind with `cat > /tmp/issue.json <<EOF ... EOF` then `deviate plan post --issue-id ISS-NNN-NNN`), or the issue file was deleted at the path recorded in `specs/issues.jsonl`'s `source_file` (`grep "<ISSUE_ID>" specs/issues.jsonl` returns the expected path). Restore the file or run `/deviate-shard` again to re-emit.

### Pre-script emits `SPEC_NOT_FOUND` or `NO_ACTIVE_ISSUE`

The session file has no `active_issue_id` — the tasks phase requires a bound issue. Either pass `--issue-id` to the slash command or run an intermediate `deviate plan post --issue-id ISS-NNN-NNN` to anchor the session. If you only need to run tasks (skipping plan), advance the session from `SHARD` directly with `deviate specify post` then `deviate tasks pre --force` (the pre-script accepts `SPECIFY` as a valid prior phase).

### Post-script halts with `TASKS_EMPTY`

The post-script found the artifact at `tasks_target` but it was empty (or contained only whitespace). The `--force` flag bypasses this check (`src/deviate/cli/meso.py::_tasks_post`), but the more reliable fix is to re-run `/deviate-tasks` so the orchestrator regenerates the content. An empty artifact usually means the spec ingestion in step 4 returned no workstation mappings — re-check that the spec source has the required embedded sections or that `spec.md` is non-empty.

### Post-script rejects the file with task ID format violations

The artifact contains task heading lines that do not match the strict `^TSK-\d{3}-\d{2}:$` pattern. Common offenders are the legacy `T001:`, `T-001:`, `TASK1:`, or `TSK001:` shapes. The post-script prints the offending lines. Either re-run `/deviate-tasks` with a tighter instruction or hand-edit the heading lines in place. After manual edits, re-run `deviate tasks post --force` to skip the empty-check (the format check still runs) — or fix the orchestrator output and rerun without `--force`.

### Post-script times out or fails on pre-commit hooks

The post-script runs pre-commit hooks including the full test suite (`mise run test` or whatever the constitution mandates). On large repos or slow CI this can exceed 3 minutes. Allocate at least **180s** for the post-script invocation; if it still times out, run `mise run test` in isolation to diagnose. If the commit is partial, restore the working tree (`git checkout -- specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md`) and re-run the post-script once the test failure is fixed.

### `plan.md` was expected but is missing

The optional upstream [`/deviate-plan`](/how-to/plan) was skipped or its artifact was not committed. Tasks is robust to a missing `plan.md` — the orchestrator decomposes from spec alone — but tasks touching risky areas carry `[WARNING]` markers. If the missing `plan.md` was unintentional, run `/deviate-plan <ISSUE_ID>` and re-run `/deviate-tasks` so the artifact reflects the plan-derived risk register and workstation map. If the issue was simple enough to skip plan, the warning markers are acceptable and the artifact is correct as-is.

### Circular task dependencies in the generated `Dependency` graph

The orchestrator's decision-tree emits a `Dependency` for each task that requires an upstream task. If you see a cycle (Task A depends on B, B depends on A), the post-script halts and the orchestrator surfaces a diagnostic. Hand-edit the `Dependency` fields to break the cycle — typically one link was misplaced in step 5 — then re-run `deviate tasks post --force`. For more than two tasks in the cycle, draw the graph first (`grep -E '^\*\*Dependency\*\*: T' tasks.md`) before breaking links.

### Session did not advance to `IDLE`

The session in `.deviate/session.json` should report `current_phase: IDLE` after a successful post-script. If it still reads `SHARD`, `PLAN`, or `TASKS`, the post-script exited before completing the state-machine transition. Re-run `deviate tasks post` directly. If the file is unchanged the post-script prints `[yellow]COMMIT_SKIP[/] tasks.md — no changes to stage`; that is a soft recovery — touch the file (`touch specs/NNN-<slug>/issues/ISS-NNN-NNN-<slug>/tasks.md`) and re-run.

## Next Steps

- [How to run /deviate-shard](/how-to/shard) — the prerequisite phase; tasks reads from the spec-enriched issue file shard produces. HITL Gate 2 must have passed before tasks runs.
- [How to run /deviate-plan](/how-to/plan) — the optional per-issue research phase; when present, its `plan.md` enriches the tasks decomposition with risk register and workstation map.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `deviate-tasks`, including its aliases (`tasks`, `/deviate-tasks`, `spec:core:tasks`, `spec.core.tasks`, `/tasks`) and `deviatdd-meso-layer` category.
- [Reference: Macro Run Pipeline](/reference/macro-run) — how the macro and meso layers compose; tasks is the meso phase that hands off to the TDD layer.
- [Explanation: append-only ledger discipline](/explanation/append-only-ledger) — why `specs/issues.jsonl` is append-only with `merge=union` seeded by `deviate setup`, and how a per-issue `tasks.md` commit slots into the broader ledger invariants.
- [Explanation: vertical-slice mandate](/explanation/three-layer-architecture) — the rationale for the 30–90 minute vertical-slice granularity rule and why the decision tree defaults `IMMEDIATE` over speculative `TDD`.
