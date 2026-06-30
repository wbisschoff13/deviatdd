---
title: "Run a task via the micro dispatcher"
description: "Invoke `deviate run` to resolve the next PENDING task by ID or by walking the active issue, then route it through the TDD cycle or the EXECUTE phase per its `execution_mode`."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Run a task via the micro dispatcher

This how-to covers `deviate run` — the micro-layer dispatcher (`run_command`, `src/deviate/cli/micro.py:3317-3425`, registered at `src/deviate/cli/__init__.py:799`). The micro layer has no slash prompt by mandate; the operator (or the agent harness) invokes the dispatcher directly. The dispatcher resolves a task either by the explicit `task_id` positional argument or by walking `.deviate/session.json` for the next `PENDING` task tied to the active issue, then routes it to the TDD cycle (`red` → `green` → `judge` → `refactor`) or the single-shot `EXECUTE` phase based on the task record's `execution_mode` field (default `TDD`). It logs every phase transition to `.deviate/run.jsonl` via `RunLogger`.

## Prerequisites

- **`/deviate-tasks` produced `tasks.md` for the active issue** — the dispatcher pulls task records from `specs/**/tasks.jsonl` (append-only), so the issue must have been sharded and decomposed first. If you have not generated tasks yet, see [Run the /deviate-tasks phase](/how-to/tasks).
- **An active issue bound to the session** — `.deviate/session.json` must carry a non-null `active_issue_id`. Without an active issue, `deviate run` (with no arguments) prints `NO_PENDING_TASKS` and exits non-zero. Bind one via `deviate plan post --issue-id ISS-NNN-NNN` or pass the task ID explicitly to bypass the walk.
- **A clean worktree on the feature branch for the active issue** — `deviate run` invokes the TDD cycle's pre-script, which checks `git status` (no uncommitted edits) and reuses the per-issue worktree convention from `/deviate-tasks` (`git rev-parse --abbrev-ref HEAD` must report the feature branch).
- **Reasoning-model availability for the dispatched phase** — the micro layer reads the model tier from `.deviate/config.toml` `[models]`. TDD resolves `red`/`green`/`refactor` to V4 Flash and `judge` to V4 Pro. `EXECUTE` resolves to the configured `EXECUTE` model. Confirm the workspace is `deviate setup`-bootstrapped.
- **A recognized task ID format** — when you pass an explicit ID, the dispatcher validates `^TSK-\d{3}-\d{2}$` (`_resolve_task_context`, `src/deviate/cli/micro.py:767`). A malformed ID prints `TASK_NOT_FOUND` and exits; an unknown ID prints `TASK_NOT_FOUND` against the matched pattern.
- **`uv run` (or activated venv) on `PATH`** — the dispatcher is invoked as `deviate run`, but inside a worktree-orchestrator root the canonical wrapper is `uv run deviate run …` per `.mise.toml`.

## Steps

### 1. Resolve the session and confirm an active issue

Before dispatching, verify the session has an issue bound. The dispatcher walks the session file to pick the next `PENDING` task; a missing `active_issue_id` aborts the walk.

```bash
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('phase:', s.get('current_phase')); print('active:', s.get('active_issue_id'))"

# Append-only ledger has at least one PENDING task for the active issue
jq -r 'select(.issue_id=="ISS-NNN-NNN" and .status=="PENDING") | .id' specs/issues/issues.jsonl | head -5
```

`current_phase` should be `TASKS` (the prior `/deviate-tasks` output) or any later micro state (`RED`, `GREEN`, `JUDGE`, `REFACTOR`, `EXECUTE`). On a fresh session, `IDLE` is the landing state and the walk has nothing to pick.

### 2. Pick the task — by ID or by walking

The dispatcher accepts an optional positional `task_id`. Pass it when you want to run a specific task out of order; omit it to let the dispatcher walk the append-only ledger for the next `PENDING` task tied to `session.active_issue_id` (`_resolve_task_context`, `src/deviate/cli/micro.py:765-788`).

```bash
# Walk: pick the next PENDING task for the active issue
deviate run

# Explicit: run a specific task
deviate run TSK-NNN-NN

# Bulk: run every PENDING task for the active issue
deviate run --all
```

For a dry resolution (no execution), pass `--dry-run` to print the resolved task and exit:

```bash
deviate run --dry-run
deviate run --all --dry-run
```

### 3. Dispatch the resolved task

Run the dispatcher. The dispatcher's body (`run_command`, `src/deviate/cli/micro.py:3338-3425`) prints `RUN_START`, calls `_resolve_task_context`, then routes through `_run_single` (or `_run_all` for `--all`) which calls `_dispatch_task`. Routing is driven by `task.get("execution_mode", "TDD")` (`_dispatch_task`, `src/deviate/cli/micro.py:2096`):

- `execution_mode: "TDD"` (default) → `_run_tdd_cycle` → `red` → `green` → `judge` (optional) → `refactor` (optional).
- `execution_mode: "EXECUTE"` → `_run_execute_phase` → direct change with no RED/GREEN/REFACTOR steps (used for trivial config, docs, and pure refactors per the `/deviate-tasks` decision tree).

Override the profile to skip phases:

```bash
# Default profile = full (RUN + JUDGE + REFACTOR)
deviate run TSK-001-01 --profile fast          # skip JUDGE
deviate run TSK-001-01 --no-refactor           # skip REFACTOR only
deviate run TSK-001-01 --no-judge --no-refactor
```

Valid profiles: `full`, `fast`, `secure`. The profile resolves to specific `no_judge`/`no_refactor` defaults via `resolve_profile`; explicit `--no-judge` / `--no-refactor` flags take precedence.

For JSONL output (consumable by an external orchestration monitor):

```bash
deviate run TSK-001-01 --json --verbose
```

### 4. Inspect the run log

The dispatcher records every phase transition, retry, and decision to `.deviate/run.jsonl` via `RunLogger` (`run_logger = RunLogger(root)` and `_log_run("RUN_START", …)` at `src/deviate/cli/micro.py:3396-3401`). Inspect it to confirm the route that was taken:

```bash
# Pull just this run's events
jq -c 'select(.task_id=="TSK-001-01")' .deviate/run.jsonl

# Show the sequence of phases for a task
jq -r 'select(.task_id=="TSK-001-01") | [.event, .phase // "-", (.detail // "" | tostring)[:80]] | @tsv' \
  .deviate/run.jsonl
```

Expected sequence for a `TDD` task: `RUN_START`, `TASK_DISPATCH`, `PHASE_START red`, `PHASE_START green`, `PHASE_START judge` (unless skipped), `PHASE_START refactor` (unless skipped), `TASK_COMPLETE`. For an `EXECUTE` task: `RUN_START`, `TASK_DISPATCH`, `PHASE_START EXECUTE`, `TASK_COMPLETE`.

### 5. Verify the task advanced and the commit landed

After the dispatcher returns, confirm the task moved out of `PENDING` in the append-only ledger and (for TDD tasks) the micro commit landed on the feature branch.

```bash
# Task status moved from PENDING → COMPLETED (last record wins)
jq -r 'select(.id=="TSK-001-01") | [.id, .status, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# Latest commit on the feature branch includes the micro changes
git log --oneline -3
git show HEAD --stat | head -20

# Session phase advanced (TDD: IDLE → RED → GREEN → JUDGE → REFACTOR → IDLE; EXECUTE: IDLE → EXECUTE → IDLE)
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

A `TDD` task that landed cleanly ends with `current_phase: IDLE` and `status: COMPLETED` in the latest task record. A task that hit `JUDGE` rejection or `RED`-only retry will show `status: RED` or a still-running phase — re-run `deviate run TSK-NNN-NN` (with the same ID) to resume from the recorded `start_phase`.

## Troubleshooting

### Dispatcher prints `NO_PENDING_TASKS`

`.deviate/session.json` has an `active_issue_id` but `specs/**/tasks.jsonl` (for that issue) has no row with `status: PENDING`. Two common causes: the active issue was bound to a different epic after a `deviate plan post`, or all tasks for the issue were already completed in a prior run. Re-bind with `cat > /tmp/issue.json <<EOF { "active_issue_id": "ISS-NNN-NNN" } EOF && deviate plan post --issue-id ISS-NNN-NNN`, or pass the explicit task ID to run a specific task out of the walk.

### Dispatcher prints `TASK_NOT_FOUND` against a specific ID

The `task_id` either failed the format check (`^TSK-\d{3}-\d{2}$`) or matched but no record exists in any `specs/**/tasks.jsonl`. The dispatcher prints the malformed shape verbatim (`Unrecognised task ID format: T001`). Fix by using the canonical `TSK-NNN-NN` shape from the `/deviate-tasks` output, or re-run `/deviate-tasks <ISSUE_ID>` if the ledger lost the row.

### Dispatcher prints `TASK_ALREADY_DONE`

The session is in `IDLE` and the task's latest status is `COMPLETED`, `REFACTOR`, `JUDGE`, or `YELLOW` (`_run_single`, `src/deviate/cli/micro.py:2139-2146`). The dispatcher exits zero without re-running. To re-execute (e.g., after a hotfix rollback), clear the latest task transition in the ledger and re-bind the session, or invoke `/deviate-hotfix` instead — it is the recovery path that intentionally re-runs completed tasks.

### `execution_mode: EXECUTE` task ran but no micro cycle observed

This is the expected path for tasks whose `execution_mode` was set to anything other than `TDD` in the `/deviate-tasks` decision tree (`src/deviate/prompts/commands/deviate-tasks.md` execution step 4b — trivial config, docs, pure refactors with existing coverage). The dispatcher routes to `_run_execute_phase` (`src/deviate/cli/micro.py:2117-2118`) and emits a single `PHASE_START EXECUTE` event. To force the task into the full TDD cycle, regenerate `tasks.md` via `/deviate-tasks` after editing the decision-tree trigger (e.g., adding new acceptance criteria) — do not change `execution_mode` post-hoc.

### `--profile secure` refused to override `--no-judge`

`resolve_profile` (`src/deviate/cli/micro.py:3394`) maps the profile to baseline `no_judge`/`no_refactor` values that override the caller's flags in *some* profiles (the secure profile forces both off). If you need to keep both phases, switch to `--profile full` and pass `--no-refactor` explicitly — the explicit flag wins when it disagrees with the profile baseline.

### `deviate run` hangs after `RUN_START` and never prints `PHASE_START`

The reasoning model for the first phase (default `red`) is unavailable or rate-limited. The dispatcher prints `[yellow]RETRY EXECUTE (attempt N)` only on EXECUTE-mode retries; for TDD-mode stalls, cancel the invocation (`Ctrl-C` once — the `try / finally` block at `src/deviate/cli/micro.py:3403-3424` closes the `RunLogger`), confirm the configured model tier with `jq '.models' .deviate/config.toml`, and re-run.

## Next Steps

- [Run the /deviate-tasks phase](/how-to/tasks) — the predecessor how-to that produces the `tasks.jsonl` rows the dispatcher consumes.
- [Reference: `deviate` CLI flags](/reference/cli#deviate-run) — every flag on `deviate run`, including `--profile`, `--all`, `--dry-run`, `--json`, `--agent`, and `--verbose`.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry confirming the micro layer has no slash prompt (`/deviate-run` is intentionally absent; `deviate run` is the direct invocation).
