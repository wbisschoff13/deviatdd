---
title: "Run the /deviate-execute phase"
description: "Execute a single DIRECT-mode task (boilerplate, config, docs, or trivial refactor) by running the /deviate-execute slash command — the pre/post pair, validation, and auto-commit, with no RED/GREEN/REFACTOR cycle."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Run the /deviate-execute phase

This how-to covers `/deviate-execute` — the **DIRECT execution** phase of the DeviaTDD micro layer, registered at `src/deviate/cli/__init__.py:789` as `execute_app` (`src/deviate/cli/micro.py:3162-3218`). The slash command runs three internal sub-steps (defined in `src/deviate/prompts/commands/deviate-execute.md`): `deviate execute pre` emits a JSON contract (`task_id`, `completion_criteria`); the agent implements the task with minimal, focused changes; `deviate execute post [task_id] [subject] [body]` appends a `COMPLETED` transition to `specs/**/tasks.jsonl`, runs pre-commit hooks, and commits with a Conventional Commit subject. There is no RED → GREEN → REFACTOR cycle — that path is reserved for tasks whose `execution_mode` is `TDD`; if you need the dispatcher to walk every `PENDING` task automatically, see [Run a task via the micro dispatcher](/how-to/run).

## Prerequisites

- **`/deviate-tasks` produced `tasks.md` with at least one `execution_mode: DIRECT` (or `IMMEDIATE`) task** — the EXECUTE phase pulls task records from `specs/**/tasks.jsonl` and respects each row's `execution_mode` field. The `execute_pre` handler (`src/deviate/cli/micro.py:3162-3183`) calls `_resolve_task_context` to discover the next eligible task; without a DIRECT-mode task the pre-script returns a `NO_PENDING_TASKS` exit. If you have not generated tasks yet, see [Run the /deviate-tasks phase](/how-to/tasks).
- **An active issue bound to the session** — `.deviate/session.json` must carry a non-null `active_issue_id`; the pre-script forces the session into the `EXECUTE` state (`force_transition_to("EXECUTE")` at `src/deviate/cli/micro.py:3174`) and stamps the active issue ID. Bind one with `deviate plan post --issue-id ISS-NNN-NNN`, or pass `--task TSK-NNN-NN` to the pre-script to bypass the session walk.
- **Tier classification justifies DIRECT** — use this skill only when task complexity ≤ 3, the change is trivial (typos, comments, config, asset syncs), the work is documentation-only, or the refactor is backed by existing test coverage. Anything requiring new test coverage belongs in the TDD cycle (`/deviate-red` → `/deviate-green` → `/deviate-refactor`); the slash command's `task_analysis` step explicitly recommends switching to TDD skills when the work outgrows the DIRECT tier.
- **The per-issue worktree, on the feature branch** — `execute_pre` and `execute_post` resolve via `Path.cwd()` (`src/deviate/cli/micro.py:3166`, `src/deviate/cli/micro.py:3196`), so the slash command must run from inside the per-issue worktree created by `/deviate-specify`. `git rev-parse --abbrev-ref HEAD` must report the feature branch.
- **A clean working tree on the feature branch** — the post-script commits directly via `_commit_phase` (`src/deviate/cli/micro.py:3217`); stash or commit any unrelated edits before invoking the slash command, otherwise the post-script fails with a non-zero `git commit` exit.
- **`mise run check` resolves locally** — the slash command's `validation` step runs `mise run check` (per `src/deviate/prompts/commands/deviate-execute.md` step 4). A missing `.mise.toml` or a misconfigured `mise` install makes the slash command bail before the post-script is invoked.
- **Reasoning-model availability for the EXECUTE phase** — `/deviate-execute` resolves the model via `resolve_model_for_phase("EXECUTE", root)` (`src/deviate/cli/micro.py:1913`). The default tier is V4 Pro (cached/compliance tier per `specs/_product/architecture.md`); per-phase overrides live in `.deviate/config.toml` under `[models].execute`.
- **`uv run` (or activated venv) on `PATH`** — the CLI sub-commands are invoked as `deviate execute …`; inside a worktree-orchestrator root the canonical wrapper is `uv run deviate execute …` per `.mise.toml`.

## Steps

### 1. Confirm the session has an active issue and a DIRECT-mode task

Before invoking the slash command, verify the upstream gate. `execute_pre` resolves the active issue via the session file and pulls the next eligible task from `specs/**/tasks.jsonl`; the pre-script requires `execution_mode` to be `DIRECT` (or `IMMEDIATE`).

```bash
# Session has an active issue
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('issue:', s.get('active_issue_id')); print('phase:', s.get('current_phase'))"

# At least one DIRECT-mode task for the active issue
jq -r 'select(.issue_id=="ISS-NNN-NNN" and .execution_mode=="DIRECT" and .status=="PENDING") | .id' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | head -3

# Inside the per-issue worktree, on the feature branch
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD

# Working tree is clean (post-script commits the implementation)
git status --porcelain
```

`current_phase` may be `IDLE` (fresh session) or `EXECUTE` (recovery from a prior wedged run). On a fresh session after `/deviate-tasks` has committed, `IDLE` is the expected landing state.

### 2. Invoke the slash command

Invoke `/deviate-execute`. The slash command drives the pre-script, the implementation pass, validation, and the post-script. The aliases `/x` and `/spec.execute` resolve to the same workflow (per `src/deviate/prompts/commands/deviate-execute.md` frontmatter `aliases`).

```text
/deviate-execute
```

The slash command prints progress through the workflow; you do not need to manually chain the sub-commands.

### 3. Read the pre-script contract on stdout

The slash command's first internal step runs `deviate execute pre` to emit a JSON contract (`src/deviate/cli/micro.py:3162-3183`). The contract carries:

| Field | Meaning |
|---|---|
| `task_id` | Identifier of the DIRECT-mode task the post-script will complete (e.g. `TSK-NNN-NN`) |
| `completion_criteria` | Literal string `Direct execution task — bypasses RED/GREEN/REFACTOR` (the EXECUTE phase has no behavioural acceptance gate beyond `mise run check`) |

If `task_id` is empty, the slash command halts and surfaces the situation — the pre-script may have needed a `--task` argument.

### 4. Implement the task with minimal, focused changes

Read each file that needs changing, apply the change, and stop. The slash command's `implementation` step enforces: do not scope-creep, do not add new files unless the task explicitly requires them, do not add "what" comments, preserve existing patterns (indentation, naming, file structure). For DIRECT tasks the implementation is typically a one-file edit, a config tweak, or a docs update.

### 5. Validate with `mise run check`

The slash command's `validation` step runs the canonical check bundle. Iterate on the code if it fails — never silence, never skip.

```bash
mise run check
```

The check bundle typically invokes `mise run lint` and `mise run test` (or `mise run check-types`); the exact wiring is whatever `.mise.toml` declares. The slash command will not invoke the post-script until this step exits zero.

### 6. Invoke the post-script to auto-commit

The slash command's `post_script` step runs `deviate execute post` to update the task ledger, stage files, run pre-commit hooks, and commit. The simplest invocation auto-discovers the current task and auto-generates the commit subject `feat(<TASK_ID>): execute result` (`src/deviate/cli/micro.py:3211`).

```bash
# Auto-discover the current task and auto-generate the subject
deviate execute post

# Custom subject (Conventional Commit, ≤ 50 chars)
deviate execute post TSK-NNN-NN "feat(TSK-NNN-NN): <subject>"

# Subject + body (wrap body at 72 chars per line)
deviate execute post TSK-NNN-NN "feat(TSK-NNN-NN): <subject>" "<body line 1>

<body line 2>"
```

The post-script allocates up to 180s for the full test suite via pre-commit hooks; the slash command surfaces `COMMIT_FAILED` if the commit lands non-zero. If the post-script fails and a manual fallback is required, follow the `manual_commit_fallback` step in the slash command (commit directly with `git commit -m "<subject>" -m "Mode: DIRECT" -m "Validation: manual-fallback"` and surface `git status` and `git log -1` to the user).

### 7. Verify the task advanced and the commit landed

After the slash command emits its `EXECUTE` handover manifest, confirm the task moved out of `PENDING` in the append-only ledger and the commit is on the feature branch.

```bash
# Task status moved PENDING → COMPLETED (last record wins)
jq -r 'select(.id=="TSK-NNN-NN") | [.id, .status, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# Latest commit on the feature branch includes the DIRECT implementation
git log --oneline -3
git show HEAD --stat | head -20

# Session returned to IDLE
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"

# Slash command emitted the EXECUTE manifest
# phase: "EXECUTE"
# task_id: "<TASK_ID>"
# status: "PASS"
```

A clean DIRECT run ends with `current_phase: IDLE`, the latest task record `status: COMPLETED`, and a single micro commit on the feature branch.

## Troubleshooting

### Pre-script returns empty `task_id` or `NO_PENDING_TASKS`

`_resolve_task_context` (`src/deviate/cli/micro.py:767`) found no `status: PENDING` row with `execution_mode: DIRECT` (or `IMMEDIATE`) for the active issue. The pre-script exits non-zero with `NO_PENDING_TASKS`. Two common causes: the active issue was bound to a different epic after a `deviate plan post`, or the tasks for the active issue were decomposed in TDD mode (not DIRECT). Re-bind with `deviate plan post --issue-id ISS-NNN-NNN`, or pass the task ID explicitly: `deviate execute pre --task TSK-NNN-NN`. If all tasks are TDD-mode, this is the expected outcome — route through the TDD cycle instead (`/deviate-red` → `/deviate-green` → `/deviate-judge` → `/deviate-refactor`).

### `mise run check` fails validation

The slash command refuses to invoke the post-script until validation exits zero. Read the failure output, fix the underlying issue (lint violation, type error, failing test), and re-run `mise run check`. Never silence a failing test to make a DIRECT task pass — DIRECT tasks are for work backed by existing coverage; if a new test is needed, the task was misclassified at the `/deviate-tasks` decision tree and must be regenerated as a TDD task.

### Post-script exits non-zero (`COMMIT_FAILED`)

The pre-commit hooks modified files mid-commit, a hook itself failed, or a stash / merge conflict surfaced. The slash command surfaces the error verbatim. First, run `git status` and `git diff` to inspect state. If a hook modified files, the post-script's re-stage logic (`_commit_phase`, `src/deviate/cli/micro.py:3217`) normally handles this — a non-zero exit here means a hook failed and must be fixed before the commit can land. As a last resort, follow the slash command's `manual_commit_fallback` step: `git commit -m "<subject>" -m "Mode: DIRECT" -m "Validation: manual-fallback"`. Never bypass the post-script silently — the post-script is what appends the `COMPLETED` transition to the ledger.

### Stash conflict, merge conflict, or detached HEAD

The slash command's `edge_case_handling` table halts the workflow on any of these conditions. Resolve the git state outside the slash command (`git stash pop`, `git rebase --abort`, `git checkout <branch>`), confirm `git rev-parse --abbrev-ref HEAD` reports the feature branch, and re-invoke `/deviate-execute`. Do not attempt to merge a DIRECT task into the orchestrator root — the per-issue worktree is the only valid execution context.

## Next Steps

- [Run the /deviate-tasks phase](/how-to/tasks) — the predecessor how-to that produced the `execution_mode: DIRECT` row the EXECUTE phase consumes.
- [Run a task via the micro dispatcher](/how-to/run) — the alternative entry point: `deviate run` walks the ledger and routes DIRECT-mode tasks through `_run_execute_phase` automatically when you have multiple tasks to clear.
- [Reference: Slash Commands](/reference/slash-commands#deviattd-micro-layer) — the inventory entry confirming `deviate-execute` aliases (`/x`, `/spec.execute`) and the `deviattd-micro-layer` category (double-`t` prefix is preserved verbatim).
- [Run the /deviate-red phase](/how-to/red) — the TDD-cycle entry point for tasks that should not have been classified as DIRECT; switch to the TDD cycle if the DIRECT tier check fails.
