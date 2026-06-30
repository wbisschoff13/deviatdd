---
title: "Run the /deviate-refactor phase"
description: "Improve structure and clarity of GREEN-phase implementation while preserving public behavior; the post-script re-runs the test suite, rejects any change that alters test output, and commits the cleanup."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Run the /deviate-refactor phase

This how-to covers `/deviate-refactor` — the **REFACTOR** (cleanup) phase of the DeviaTDD micro-cycle, registered at `src/deviate/cli/__init__.py:788` as `refactor_app` (`src/deviate/cli/micro.py:122`) and exposed as `deviate refactor pre` / `deviate refactor post` (`src/deviate/cli/micro.py:2899` and `src/deviate/cli/micro.py:3064`). REFACTOR sits at the end of the default `red → green → [yellow?] → judge → refactor` cycle; the slash command itself orchestrates a JSON contract emission, a behavior-preserving structural pass, and a regression gate that re-runs the test suite and restores the worktree on any delta. The slash command is the user-facing action — the pre/post sub-commands are agent-internal and you should not run them by hand unless you are recovering a wedged post-script. If you want the dispatcher to walk every PENDING task through the full cycle in one shot, see [Run a task via the micro dispatcher](/how-to/run) instead.

## Prerequisites

- **GREEN has committed on the feature branch** — the post-script aborts with `MISSING_GREEN_PHASE` when the most recent ledger row for the active task is not `status: GREEN` (`refactor_post`, `src/deviate/cli/micro.py:3081-3087`). The `_resolve_latest_task(root, issue_id, "GREEN")` walk only looks at rows tagged GREEN, so a JUDGE-pipeline resume is fine as long as GREEN already landed. If GREEN has not committed, return to the slash command that produced GREEN and re-run it before invoking `/deviate-refactor`.
- **The per-issue worktree, on the feature branch** — `refactor_pre` and `refactor_post` both resolve `root = Path.cwd()` (`src/deviate/cli/micro.py:2903` and `src/deviate/cli/micro.py:3066`), so the slash command must run from inside the per-issue worktree created by `/deviate-specify`, not from the worktree-orchestrator root. `git rev-parse --abbrev-ref HEAD` must report the feature branch.
- **A clean working tree before the refactor pass** — the post-script runs `git restore .` on any regression or type-mismatch detection (`src/deviate/cli/micro.py:3115-3117` and `src/deviate/cli/micro.py:3128`). Stash or commit any unrelated scratch edits before invoking the slash command, otherwise the rollback will revert them.
- **A `src/**/*.py` source tree** — `refactor_pre` enumerates the refactor candidate set with `_find_source_files(root)` (`src/deviate/cli/micro.py:2324-2325`, called at `src/deviate/cli/micro.py:2906`) which globs `src/**/*.py` and returns sorted paths. A repo with no `src/` tree produces an empty `files_to_refactor` list and the contract has nothing to scope; the slash command treats that as a no-op.
- **A working test suite** — the post-script captures `_run_pytest(root)` output **before** the refactor and again **after**, then compares `_normalize_pytest_output(proc_before.stdout)` against the same normalization of `proc_after.stdout` plus their return codes (`src/deviate/cli/micro.py:3105-3127`). A failing baseline (return code 0 unreachable) makes every refactor delta indistinguishable from a regression; land GREEN on a green suite before running REFACTOR.
- **`uv run` (or activated venv) on `PATH`** — the pre-script and post-script are invoked as Python CLI commands per `.mise.toml`; inside the canonical wrapper the form is `uv run deviate refactor pre` / `post`.
- **Reasoning-model availability for the micro layer** — `/deviate-refactor` resolves to V4 Flash (low-cost tier) by default per `specs/_product/architecture.md` and `src/deviate/state/config.py::resolve_phase_model`. Per-phase overrides go in `.deviate/config.toml` under `[models].refactor`.

## Steps

### 1. Confirm the active task has a `GREEN` ledger row

Before invoking the slash command, verify the upstream gate. The post-script uses `_resolve_latest_task(root, issue_id, "GREEN")` to look up the GREEN entry that authorizes the refactor pass; a missing row aborts with `MISSING_GREEN_PHASE` and exits 1 (`src/deviate/cli/micro.py:3081-3087`). The slash command runs from the per-issue worktree, so the active issue is the one bound to the session.

```bash
# Latest GREEN row for the active issue (the post-script walks every specs/**/tasks.jsonl)
jq -r 'select(.issue_id=="ISS-NNN-NNN" and .status=="GREEN") | [.id, .status, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# Session is parked on REFACTOR (the GREEN→JUDGE→REFACTOR handoff left it here)
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('phase:', s.get('current_phase')); print('issue:', s.get('active_issue_id'))"

# Inside the per-issue worktree, on the feature branch
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD

# Working tree is clean (the post-script will git restore on any regression)
git status --porcelain
```

`current_phase` should be `REFACTOR` (immediately after JUDGE passed) or `GREEN` (a JUDGE-skip profile). A landing state of `JUDGE` means the JUDGE phase has not yet emitted its verdict — wait for the JUDGE post-script to commit or run the JUDGE phase first.

### 2. Run the slash command

Invoke `/deviate-refactor`. The slash command (`src/deviate/prompts/commands/deviate-refactor.md` execution_sequence) drives six steps: emit the pre-script contract, load the architectural contracts (`specs/constitution.md`, `spec.md`, `data-model.md`), analyze the GREEN commit (`git log -2 --oneline --stat` plus `git diff HEAD~2..HEAD --stat`), apply refactoring patterns (extract function, rename, move, consolidate), verify behavior invariance with the test command, then call the post-script.

```text
/deviate-refactor
```

The slash command's pre-script emits a JSON contract on stdout (`refactor_pre`, `src/deviate/cli/micro.py:2899-2910`):

```json
{
  "files_to_refactor": [
    "src/deviate/cli/micro.py",
    "src/deviate/cli/feature.py",
    "..."
  ]
}
```

`files_to_refactor` is the closed candidate set the slash command is allowed to touch. The post-script then re-derives the actually-changed files via `_detect_phase_changes(root)` (`src/deviate/cli/micro.py:3109`) and validates only the changed Python files against the static checks. Editing any path outside `src/**/*.py` is a micro-sandboxing violation and the post-script's regression check will catch it implicitly (the pre- and post-test runs would diverge because `tests/` lives outside the source set).

### 3. Apply behavior-preserving refactors against the contract

The slash command's refactoring pass (execution steps `analyze_green_implementation` and `apply_refactoring_patterns` in `src/deviate/prompts/commands/deviate-refactor.md`) translates the GREEN implementation into a cleaner structure. The agent must:

1. Review `git log -2 --oneline --stat` and `git diff HEAD~2..HEAD --stat` to see the RED-then-GREEN surface and identify code smells in the implementation (duplication, large functions, deep nesting, contract violations, obscure naming, tight coupling).
2. Apply targeted refactoring patterns from the prompt's `apply_refactoring_patterns` list — Extract Function/Method, Rename Variable/Function, Move Function/Logic, Replace Conditional with Polymorphism, Consolidate Duplicate Fragments.
3. Stay inside the `files_to_refactor` set from the pre-script contract. Do not edit `tests/**`, `specs/**`, `*.md`, or any path outside `src/**` — those are out-of-scope for the REFACTOR phase and trigger the post-script's regression gate.
4. Re-run the test command from the pre-script contract (`mise run test`, supplied by the prompt's `test_command` placeholder) and confirm the suite still passes unchanged. If a test now fails, the refactor has introduced a behavior change — revert and re-apply.
5. Run the lint command from the contract (`mise run lint`) and fix any lint regressions before handing off.

Do not write new tests in this step — that is `/deviate-red` territory. Do not modify the GREEN implementation's public behavior, public return values, or public signatures; the test suite is the contract and the post-script compares the suite's normalized output to the pre-refactor baseline.

### 4. Let the post-script verify behavior invariance and commit

The slash command calls `deviate refactor post` automatically. The post-script (`src/deviate/cli/micro.py:3064-3151`) does six things and you must not skip it:

1. `_find_test_files(root)` returns the on-disk test set; an empty set prints `NO_TESTS_TO_CHECK` and exits 0 without committing (`src/deviate/cli/micro.py:3067-3071`). This is a soft pass — a no-test repo cannot detect regressions, so the post-script declines to claim a refactor passed.
2. Resolves `session.active_issue_id` and calls `_resolve_latest_task(root, issue_id, "GREEN")`; if no GREEN row exists, prints `MISSING_GREEN_PHASE` and aborts with exit 1 (`src/deviate/cli/micro.py:3079-3087`).
3. Captures a pre-refactor pytest baseline via `_run_pytest(root)` and normalizes its stdout (`src/deviate/cli/micro.py:3105-3107`).
4. Detects the changed files with `_detect_phase_changes(root)` and runs `_check_return_type_mismatch` on each `.py` file in the changed set (`src/deviate/cli/micro.py:3109-3113`). If tree-sitter reports return-type mismatches, dead code, duplicate blocks ≥ 5 lines, or cyclomatic complexity ≥ 10, the script runs `git restore .`, prints `RefactorRegressionError: <issues>`, and aborts (`src/deviate/cli/micro.py:3114-3121`).
5. Captures a post-refactor pytest run; if `after_returncode != before_returncode` or `after_output != before_output`, runs `git restore .`, prints `RefactorRegressionError: Test regression detected after refactor`, and aborts (`src/deviate/cli/micro.py:3123-3132`).
6. Commits the refactor with `_commit_phase(f"refactor({scope}): REFACTOR phase — code cleanup", root)` (`src/deviate/cli/micro.py:3134-3136`), appends a `COMPLETED` transition to the append-only ledger (`_append_status_transition(task_record, "COMPLETED", green_task[1])`, `src/deviate/cli/micro.py:3142`), forces the session to `IDLE` with `yellow_triggered: false`, and saves it (`src/deviate/cli/micro.py:3145-3147`).

If `deviate refactor post` exits non-zero, inspect the failure, fix the underlying cause (most often a static-analysis violation or a test output delta), and re-run it. Do not commit by hand — only the post-script updates the ledger and the session atomically.

### 5. Verify the artifact, the ledger, and the session transition

After the slash command returns, confirm everything landed. The artifact (refactored implementation) must be on disk and in the commit, the ledger must carry a `COMPLETED` row for the GREEN task, and the session must have returned to `IDLE`.

```bash
# Latest commit on the feature branch is the refactor commit
git log --oneline -1
git show HEAD --stat | head -10

# Ledger has a COMPLETED row for the task that was GREEN (last record wins)
jq -r 'select(.id=="TSK-NNN-NN") | [.id, .status, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# Session advanced to IDLE
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('phase:', s.get('current_phase')); print('yellow_triggered:', s.get('yellow_triggered'))"

# The test suite still passes after the refactor (the post-script's gate)
mise run test
```

A clean REFACTOR-phase run ends with `current_phase: IDLE`, `status: COMPLETED` in the latest task record, `yellow_triggered: false`, and the test suite still passing with the same normalized output as the pre-refactor baseline.

## Troubleshooting

### Post-script prints `MISSING_GREEN_PHASE`

`_resolve_latest_task(root, issue_id, "GREEN")` returned `None` (`src/deviate/cli/micro.py:3081-3087`). The most common cause is invoking `/deviate-refactor` on a fresh task that has not yet been through `/deviate-green` — REFACTOR only runs after GREEN has committed. Another cause: a prior abort left the ledger without a `status: GREEN` row (e.g., a manual `git reset` between GREEN and REFACTOR). Re-run `/deviate-green` to land the GREEN commit and let the dispatcher pick up at REFACTOR on the next `deviate run`.

### Post-script prints `RefactorRegressionError: Test regression detected after refactor`

`_run_pytest(root)` after the refactor diverged from the baseline (`src/deviate/cli/micro.py:3123-3132`). Two common causes: the refactor changed observable behavior (different return values, different exception types, different log lines that pytest captured) or the refactor touched a test file (the suite is the invariant — modifying it always changes the baseline). The post-script already ran `git restore .` so the working tree is back to the pre-refactor state. Re-apply the refactor more narrowly: extract only the function body, leave the signature and observable behavior intact, and re-run the post-script.

### Post-script prints `RefactorRegressionError: <type-issue / duplicate / dead code / complexity>`

`_check_return_type_mismatch` reported a static-analysis violation on a changed `.py` file (`src/deviate/cli/micro.py:3114-3121`). The check uses tree-sitter to inspect return-type annotations against literal return values, then runs the project's `extract_dead_code`, `detect_duplicate_blocks` (≥ 5 lines), and `estimate_cyclomatic_complexity` (≥ 10) helpers. The post-script already ran `git restore .`, so the tree is clean. Address the named issue in a follow-up pass: tighten the return-type annotation to match the literal, remove the dead function, consolidate the duplicate block, or split the high-complexity function. Re-run `deviate refactor post` after the fix.

### Pre-script emits an empty `files_to_refactor` list

`_find_source_files(root)` returned an empty list (`src/deviate/cli/micro.py:2906`, glob `src/**/*.py`). The repo has no `src/` tree at the worktree root, so there is nothing to scope. The slash command treats this as a no-op and the post-script's `_find_test_files` may also be empty, printing `NO_TESTS_TO_CHECK` and exiting 0. If your project's source lives outside `src/**`, you are using the micro layer against a layout it does not support — return to the layout decision in `/deviate-init` and either move sources under `src/` or skip the micro cycle for this worktree.

### Post-script prints `NOTHING_CHANGED` instead of `REFACTOR_POST_OK`

`_commit_phase` returned a falsy value (`src/deviate/cli/micro.py:3148-3149`). The post-script detected no staged changes — typically because the refactor pass produced a no-op (the implementation was already clean) or because all attempted edits ended up in a file that was rolled back by the regression check. Inspect `git status` and the latest `git log`; if the refactor is genuinely a no-op the task is already done and you can move to `/deviate-pr`. If the refactor produced a partial delta that the post-script rejected, re-apply more carefully per the troubleshooting entries above.

### Post-script prints `LEDGER_UPDATE_FAILED`

The `TaskRecord.model_validate(green_task[0])` call or the `append_task_transition(record, green_task[1])` call raised (`src/deviate/cli/micro.py:3091-3097`). The most common cause is a malformed `tasks.jsonl` row — a missing `id` field, a non-`TaskRecord` shape, or a file-permission issue. Validate the ledger file parses with `jq '.' specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl` and that the GREEN row carries the `id` field. Do not hand-edit the ledger to bypass the failure — `TaskRecord`'s schema version is the source of truth and the post-script's atomicity prevents a half-applied refactor.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — the predecessor how-to that walks every PENDING task through `red → green → [yellow?] → judge → refactor` in one invocation.
- [Run the /deviate-green phase](/how-to/green) — the upstream micro-phase that produces the GREEN commit REFACTOR requires; if you reached REFACTOR without a GREEN row, start here.
- [Open the PR for the active worktree](/how-to/pr) — the natural follow-up once all tasks for the issue are `COMPLETED`; emits `PR_OPENED` and unblocks dependent issues via the `blocked_by` resolver.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `/deviate-refactor` (`aliases: refactor, /spec.tdd.refactor, /refactor, /tdd.refactor`) at version 1.0.0.
- [Reference: `deviate` CLI flags](/reference/cli#deviate-refactor) — every flag on the underlying `deviate refactor pre` (`--task`) and `deviate refactor post` sub-commands.
