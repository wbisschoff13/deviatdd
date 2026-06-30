---
title: "Run the /deviate-red phase"
description: "Write a failing test for the next PENDING task in the active issue, verify it crashes (not passes), then commit the RED-state artifact via the post-script."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Run the /deviate-red phase

This how-to covers `/deviate-red` — the **RED** (test-writing) phase of the DeviaTDD micro-cycle, registered at `src/deviate/cli/__init__.py:784` as `red_app` (`src/deviate/cli/micro.py:118`). The slash command runs three internal sub-steps (`src/deviate/prompts/commands/deviate-red.md` execution_sequence): `deviate red pre` (emits a JSON contract describing the active task), the test-writing pass against that contract, and `deviate red post` (verifies the test still fails, appends a `RED` transition to `specs/**/tasks.jsonl`, advances `.deviate/session.json` to `RED`, and commits with `git commit --no-verify` because RED-phase tests are intentionally failing). You invoke the slash command and inspect the contract — the pre/post sub-commands are agent-internal and you should not run them by hand unless you are recovering a wedged post-script. If you want the dispatcher to walk every PENDING task in one shot, see [Run a task via the micro dispatcher](/how-to/run) instead.

## Prerequisites

- **`/deviate-tasks` produced `tasks.md` and the post-script committed** — the RED phase pulls task records from `specs/**/tasks.jsonl` (append-only) and `tasks.md` for the active issue, so the meso-layer must have finished. The pre-script returns `NO_PENDING_TASKS` when no `status: PENDING` row exists for the active issue. If tasks have not been generated yet, see [Run the /deviate-tasks phase](/how-to/tasks).
- **An active issue bound to the session** — `.deviate/session.json` must carry a non-null `active_issue_id` (`red_pre` resolves it via `_resolve_task_context`, `src/deviate/cli/micro.py:767`). Bind one with `deviate plan post --issue-id ISS-NNN-NNN` or pass `--task TSK-NNN-NN` to bypass the walk.
- **The per-issue worktree, on the feature branch** — `red_pre` and `red_post` resolve the worktree via `Path.cwd()` (`src/deviate/cli/micro.py:2495`, `src/deviate/cli/micro.py:2530`), so the slash command must run from inside the per-issue worktree created by `/deviate-specify`, not from the worktree-orchestrator root. `git rev-parse --abbrev-ref HEAD` must report the feature branch.
- **A clean working tree on the feature branch** — the post-script commits the failing test (`_commit_phase(..., no_verify=True)` at `src/deviate/cli/micro.py:2576`). Stash or commit any unrelated edits before invoking the slash command, otherwise the post-script fails with a non-zero `git commit` exit.
- **`mise run test` and `mise run lint` resolve locally** — `red_pre` writes `test_command: "mise run test"` and `lint_command: "mise run lint"` into the contract verbatim (`src/deviate/cli/micro.py:2500-2505`), and `red_post` re-invokes `mise run test` to confirm the test still fails (`_run_test_cmd`, `src/deviate/cli/micro.py:2510-2516`). A missing `.mise.toml` or a misconfigured `mise` install makes the post-script bail with a non-zero exit.
- **Reasoning-model availability for the micro layer** — `/deviate-red` resolves to V4 Flash (low-cost tier) by default per `specs/_product/architecture.md` and `src/deviate/state/config.py::resolve_phase_model`. Per-phase overrides go in `.deviate/config.toml` under `[models].red`.

## Steps

### 1. Confirm the session has an active issue with a PENDING task

Before invoking the slash command, verify the upstream gate. `red_pre` resolves the active issue and pulls the next `PENDING` row from `specs/**/tasks.jsonl` (`_resolve_first_pending`, `src/deviate/cli/micro.py:2556`); a missing row aborts with `NO_PENDING_TASKS` and exits non-zero.

```bash
# Session has an active issue
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('issue:', s.get('active_issue_id')); print('phase:', s.get('current_phase'))"

# At least one PENDING task row for the active issue
jq -r 'select(.issue_id=="ISS-NNN-NNN" and .status=="PENDING") | .id' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | head -3

# Inside the per-issue worktree, on the feature branch
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD

# Working tree is clean (post-script commits the failing test)
git status --porcelain
```

`current_phase` may be `IDLE` (immediately after `/deviate-tasks` committed) or `RED` (recovery from a prior wedged run). On a fresh session, `IDLE` is the expected landing state.

### 2. Run the slash command

Invoke `/deviate-red`. The slash command orchestrates the pre-script, the test-writing pass, and the post-script. The agent reads the JSON contract from `deviate red pre` on stdout (keys: `task_id`, `test_command`, `lint_command`, `spec_dir`) and then writes a failing test that exercises the contract's `task_id` against the `spec_dir`.

```text
/deviate-red
```

To pin the slash command to a specific task (skipping the walk), the agent may accept a positional argument; if your installed slash command does not, pass it through the underlying sub-command as a verification action:

```bash
# Verification only — agent-internal sub-command
deviate red pre --task TSK-NNN-NN
```

The slash command contract that the agent receives looks like this (`red_pre`, `src/deviate/cli/micro.py:2500-2505`):

```json
{
  "task_id": "TSK-NNN-NN",
  "test_command": "mise run test",
  "lint_command": "mise run lint",
  "spec_dir": "specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>"
}
```

### 3. Write the failing test against the contract

The slash command's test-writing pass (execution step `test_writing` in `src/deviate/prompts/commands/deviate-red.md`) translates the task's functional criteria into explicit Given/When/Then assertions in the repo's native test structure. The agent must:

1. Create the test file under the repository's test layout (e.g., `tests/<feature>/test_<module>.py`) and import only interfaces that *should* exist after the GREEN phase — declare minimal stubs if the target module is missing, so the test compiles.
2. Re-run `{test_command}` from the contract (`mise run test`) and confirm the suite fails because the assertion cannot be satisfied (e.g., `NameError: name 'JWTService' is not defined`). A passing test or a syntax-error crash both abort the phase.
3. Run `{lint_command}` from the contract (`mise run lint`) and fix any lint errors before the post-script.
4. If the test exercises git operations (running git commands, testing git-based tools), the slash command must isolate it: `create_temp_dir` + `git init` + fixture copy + scoped test invocation, never against `$REPO_ROOT`.

Do not write implementation code in this step — that is `/deviate-green`. Do not write tests for code that already exists in `src/` either; the test must fail for the *right* reason (missing function or wrong return value, not a syntax error).

### 4. Let the post-script verify and commit

The slash command calls `deviate red post` automatically. The post-script (`src/deviate/cli/micro.py:2528-2589`) does four things and you must not skip it:

1. `TEST_NOT_FOUND` if `_find_test_files(root)` returns no paths — abort and re-run step 3 (`src/deviate/cli/micro.py:2533-2535`).
2. Re-invokes `mise run test`; if the suite now passes, prints `RedMustPassError: Test passed, expected a failing test` and aborts (`src/deviate/cli/micro.py:2537-2541`). The test must fail.
3. Appends a `RED` transition row to `specs/**/tasks.jsonl` (`append_task_transition`, `src/deviate/cli/micro.py:2564-2567`) and forces the session to `current_phase: RED` (`session.force_transition_to("RED")`, `src/deviate/cli/micro.py:2572`).
4. Commits the failing test with `_commit_phase(f"test({scope}): RED phase - failing test", root, no_verify=True)` (`src/deviate/cli/micro.py:2576`) — the `--no-verify` flag is intentional because pre-commit hooks would refuse the intentionally-failing test.

If `deviate red post` exits non-zero, inspect the failure, fix the underlying cause, and re-run it. Do not commit by hand — only the post-script updates the ledger and the session atomically.

### 5. Verify the artifact, the ledger, and the session transition

After the slash command returns, confirm everything landed. The artifact (failing test) must be on disk and in the commit, the ledger must carry a `RED` row for the task, and the session must have advanced.

```bash
# Latest commit on the feature branch includes the failing test
git log --oneline -1
git show HEAD --stat | head -10

# Ledger has a RED row for the active task (last record wins)
jq -r 'select(.id=="TSK-NNN-NN") | [.id, .status, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# Session advanced to RED
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('phase:', s.get('current_phase')); print('red_commit_sha:', s.get('red_commit_sha'))"

# The test still fails when re-run (intentional, do not "fix" this)
mise run test -- tests/<feature>/test_<module>.py
```

A clean RED-phase run ends with `current_phase: RED`, a `status: RED` row for the active task, `red_commit_sha` populated in the session file, and the test still failing with the expected assertion or stub-missing error.

## Troubleshooting

### Pre-script prints `NO_PENDING_TASKS`

`.deviate/session.json` has an `active_issue_id` but no `specs/**/tasks.jsonl` row carries `status: PENDING` for that issue (`_resolve_first_pending`, `src/deviate/cli/micro.py:2556-2559`). Two common causes: the active issue was re-bound to a different epic after a `deviate plan post`, or every task for the issue already advanced to `RED`/`GREEN`/`JUDGE`/`REFACTOR`/`COMPLETED`. Re-bind the session with `deviate plan post --issue-id ISS-NNN-NNN`, or pass the explicit task ID to the pre-script with `deviate red pre --task TSK-NNN-NN`.

### Post-script prints `RedMustPassError: Test passed, expected a failing test`

`_run_test_cmd(root)` returned exit 0 (`src/deviate/cli/micro.py:2537-2541`) — your test does not fail for the *right* reason. The most common cause is writing a test against an interface that already exists in `src/`; the test passes because the implementation is already in place. Another cause is asserting on a constant (`assert True`) or a property that is already satisfied. Tighten the assertion to require a value the implementation cannot yet produce, or move the test to a function/module that does not yet exist, and re-run `deviate red post`.

### Post-script prints `TEST_NOT_FOUND`

`_find_test_files(root)` returned no paths (`src/deviate/cli/micro.py:2533-2535`). The test file was not written, was written outside the repo root, or was excluded by the discoverer (e.g., wrong naming convention). Confirm the file exists with `find . -path ./node_modules -prune -o -name 'test_*.py' -print` and that it lives under a directory your test runner indexes, then re-run `deviate red post`.

### Test crashes with a syntax error instead of an assertion failure

The test compiled but Python rejected it before any assertion ran. The slash command prompt's `edge_case_handling` table flags this: "Fix syntax, re-run, verify FAIL status." Read the traceback, fix the syntax (missing import, unclosed parenthesis, mismatched indentation), and re-run `mise run test` — the suite must end with a non-zero exit due to assertion failure or stub-missing `NameError`, not `SyntaxError`.

### Pre-script prints `FAILURE` with a `session.json` recovery hint

The pre-script could not resolve the active task — typically a missing issue source file (`ISSUE_NOT_FOUND`) or no bound session (`SPEC_NOT_FOUND`). Validate `.deviate/session.json` carries `active_issue_id`, that `specs/{epic}/issues/{slug}.md` exists on disk, and that the matching `specs/{epic}/issues/{slug}/tasks.jsonl` contains at least one `PENDING` row. If the issue file is missing, return to [Run the /deviate-shard phase](/how-to/shard) or re-bind the session via `deviate plan post --issue-id ISS-NNN-NNN`.

### Lint fails after writing the test

`mise run lint` returned non-zero during the test-writing pass. The slash command refuses to hand off to the post-script until lint is clean. Fix the lint issues (the `lint_command` from the contract is authoritative — do not run a different lint binary) and re-run `mise run lint` to confirm a clean exit before invoking `deviate red post`.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — the predecessor how-to that walks every PENDING task through `red → green → judge → refactor` in one invocation.
- [Run the /deviate-tasks phase](/how-to/tasks) — the upstream meso-layer step that produces the `tasks.jsonl` rows the RED phase consumes.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `/deviate-red` (`aliases: red, /spec.tdd.red, /red, /tdd.red`) at version 1.0.0.
- [Reference: `deviate` CLI flags](/reference/cli#deviate-red) — every flag on the underlying `deviate red pre` / `deviate red post` sub-commands.