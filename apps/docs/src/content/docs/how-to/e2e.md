---
title: "Run the /deviate-e2e phase"
description: "Run end-to-end (E2E) tests via bats after every task reaches REFACTOR or COMPLETED; the post-script commits the suite and runs pre-commit hooks."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
  - ISS-ADH-011
---

# Run the /deviate-e2e phase

This how-to covers `/deviate-e2e` — the **E2E_TEST_ORCHESTRATOR** (final verification) phase of the DeviaTDD micro-cycle, registered at `src/deviate/cli/__init__.py:790` as `cli.add_typer(e2e_app, name="e2e")` and backed by `src/deviate/cli/micro.py:3226-3252` (`e2e_pre` and `e2e_post`). E2E runs **after every task in `tasks.jsonl` reaches a terminal status** (`REFACTOR` or `COMPLETED`), distinct from the per-task `red → green → judge → refactor` loop the micro-layer executes. The slash command detects project type (CLI / Web / API / Library), selects the matching E2E strategy, enforces **Product-layer flow coverage** via `flow_refs` → `tasks.md`, and runs the canonical bats suite via `mise run test-e2e` (`mise.toml:12-14`). The slash command is the user-facing action — the pre/post sub-commands are agent-internal and you should not run them by hand unless you are recovering a wedged post-script. After it lands, the natural follow-up is `/deviate-pr` (or `tools:review → tools:walkthrough → tools:pr` per the prompt's `<tier_classification>`) to close the issue.

## Prerequisites

- **Every task in `specs/**/tasks.jsonl` has terminal status (`REFACTOR` or `COMPLETED`)** — `e2e_pre` calls `_all_tasks_complete(root)` (`src/deviate/cli/micro.py:3230`) which walks every ledger row and rejects if any record has a non-terminal status. The slash command emits `INCOMPLETE_TASKS` (red banner, exit 1, no contract) until the gate clears. If any row is `PENDING` / `RED` / `GREEN` / `JUDGE`, return to [Run a task via the micro dispatcher](/how-to/run) or the relevant micro-phase how-to and finish the cycle before invoking `/deviate-e2e`.
- **The per-issue worktree, on the feature branch** — `e2e_pre` resolves `root = Path.cwd()` (`src/deviate/cli/micro.py:3228`), so the slash command must run from inside the per-issue worktree created by `/deviate-specify`, not from the worktree-orchestrator root. `git rev-parse --abbrev-ref HEAD` must report the feature branch.
- **A reachable base branch (`main` or `master`)** — STEP_3 of the slash command (`src/deviate/prompts/commands/deviate-e2e.md`) diffs HEAD against the base branch (`git diff $BASE_BRANCH...HEAD --name-only`) to enumerate `CHANGED_FILES`. If the base branch is missing or renamed, the diff returns empty and `CHANGED_FILES` carries no files — coverage is unverifiable.
- **Bats installed locally** — the canonical E2E invocation is `mise run test-e2e`, which runs `bats tests/e2e/` per `[tasks.test-e2e]` in `mise.toml:12-14`. `bats --version` must exit 0; install via Homebrew (`brew install bats-core`), apt (`apt install bats`), or mise (`mise use bats@latest`).
- **Tests in `tests/e2e/` for CLI projects (or equivalent for Web / API)** — STEP_5 (`src/deviate/prompts/commands/deviate-e2e.md`) discovers `e2e`, `e2e-tests`, `tests-e2e` directories and `.bats` / `.test.ts` / `.spec.ts` / `test_*.py` files in those paths. Library projects (no user-facing workflows) skip E2E with a warning; CLI projects without a bats suite must scaffold one or this skill emits `E2E_TEST_COVERAGE: SKIPPED` in the report.
- **A clean working tree on the feature branch** — the post-script stages and commits E2E artifacts via `_commit_phase("feat: E2E phase", root)` (`src/deviate/cli/micro.py:3251`). Stash or commit any unrelated edits before invoking the slash command.
- **`specs/_product/flows/index.md` (when the Product layer is present)** — STEP_2.5 (`src/deviate/prompts/commands/deviate-e2e.md`) reads the parent issue's `flow_refs` and the flow catalog. If absent, the slash command emits `PRODUCT_LAYER_ABSENT` in the report and continues without flow coverage; treat this as a soft signal, not a blocker.
- **`uv run` (or an activated venv) on `PATH`** — the pre-script and post-script are Python CLI commands per `.mise.toml`; inside the canonical wrapper the form is `uv run deviate e2e pre` / `post`.
- **Reasoning-model availability for the E2E phase** — `/deviate-e2e` runs in the macro-layer tier (V4 Pro or Qwen 3.7+ [Thinking] per `specs/_product/architecture.md` and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].e2e`. `jq '.models.e2e // .models.default' .deviate/config.toml` must return a reachable model name.

## Steps

### 1. Confirm every task has reached a terminal status

Before invoking the slash command, verify the upstream gate. `e2e_pre` aborts with `INCOMPLETE_TASKS` if any row in `specs/**/tasks.jsonl` is not `REFACTOR` or `COMPLETED` (`src/deviate/cli/micro.py:3226-3237`, gate at line 3230). The slash command prints the red banner, exits 1, and writes no JSON contract until the gate clears.

```bash
# Per-task latest ledger row (newest status per task ID)
jq -r 'select(.issue_id=="ISS-NNN-NNN") | [.id, .status, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -n +2

# Distinct statuses on the file — only REFACTOR / COMPLETED should appear
jq -r '.status' specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl \
  | sort -u

# Session is parked on E2E
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('phase:', s.get('current_phase')); print('issue:', s.get('active_issue_id'))"

# Bats is installed and discoverable
bats --version
```

Expected: every per-task row reads `REFACTOR` or `COMPLETED`, and `current_phase` is `E2E`. If the scan returns `PENDING`, `RED`, `GREEN`, or `JUDGE`, the micro-cycle is not finished — return to [Run a task via the micro dispatcher](/how-to/run) (or the relevant micro-phase how-to: red → green → yellow? → judge → refactor) and finish each task before invoking `/deviate-e2e`.

### 2. Run the pre-script and inspect the contract

The pre-script (`e2e_pre`, `src/deviate/cli/micro.py:3226-3237`) walks the active task ledger, prints a JSON contract on stdout, and exits 0 only when the gate clears. The contract enumerates the unit-test paths that the E2E suite must coexist with (E2E complements unit tests; it does not duplicate integration coverage). Run it as a verification action (the slash command will also run it):

```bash
# Verification only — agent-internal sub-command
deviate e2e pre
```

Expected JSON shape (per `src/deviate/cli/micro.py:3234-3236`):

```json
{
  "test_paths": [
    "tests/test_foo.py",
    "tests/test_bar.py"
  ]
}
```

If the JSON comes back missing or empty, `_all_tasks_complete` returned `False` upstream — re-run step 1 and finish the open tasks first.

### 3. Run `/deviate-e2e` and walk STEP_0..STEP_10

Invoke the slash command inside the agent. The execution sequence (`src/deviate/prompts/commands/deviate-e2e.md` `execution_sequence`) runs ten steps:

```text
/deviate-e2e
```

The slash command will:

1. **STEP_0** `DISCOVER_TASK_CONTEXT` — call `deviate e2e pre` (or surface a cached contract) and resolve the JSON to `READY` / `NO_TASKS_REMAINING` / `PHASES_INCOMPLETE` / `FAILURE`.
2. **STEP_1** `VERIFY_ALL_PHASES_COMPLETE` — re-walk `tasks.jsonl` and confirm every task ID has a terminal row.
3. **STEP_2** `LOAD_CONTEXT` — read `specs/constitution.md`, `<SPEC_DIR>/spec.md`, `<SPEC_DIR>/tasks.md`.
4. **STEP_2.5** `PRODUCT_LAYER_FLOW_COVERAGE` — read `specs/issues.jsonl` for the parent issue's `flow_refs`, then `specs/_product/flows/index.md` for each named `FLOW-XX`, and require `**Flow References**` in `tasks.md`. Missing or empty → emit `PRODUCT_LAYER_ABSENT` / `NO_FLOWS_NAMED` / `FLOW_PROPAGATION_GAP` in the report and continue (do **not** halt).
5. **STEP_3** `FETCH_GIT_DIFF` — `git diff $BASE_BRANCH...HEAD --name-only` for `CHANGED_FILES`, plus the full diff for analysis.
6. **STEP_4** `DETECT_PROJECT_TYPE` — classify as CLI / Web / API / Library (Library skips E2E with a warning).
7. **STEP_5** `DISCOVER_EXISTING_E2E_TESTS` — locate `e2e`, `e2e-tests`, `tests-e2e` directories and `.bats` / `.test.ts` / `.spec.ts` / `test_*.py` files.
8. **STEP_6** `ANALYZE_TASKS_FOR_E2E` — extract `[E2E]`-tagged tasks and user-workflow tasks from `tasks.md`.
9. **STEP_7** `GENERATE_OR_UPDATE_E2E_TESTS` — extend or create bats / Playwright / pytest files matching the detected project type. CLI projects get `@test "E2E_001 ..."` blocks with `setup()` / `teardown()` using `mktemp -d` per the prompt's `<cli_strategy>` (exit-code rigor, stream capture, stable selectors).
10. **STEP_8** `VERIFY_UNIT_TESTS` — run the contract's `test_command` (e.g., `mise run test`); abort on failure with `E2E_REQUIRES_UNIT_TESTS_PASS`.
11. **STEP_9** `EXECUTE_E2E_TESTS` — invoke `mise run test-e2e` (the canonical bats invocation per `mise.toml:12-14`) and capture pass / fail counts.
12. **STEP_10** `POST_SCRIPT` — call `deviate e2e post` automatically.

### 4. Verify the E2E suite passes and the report maps flows

Before the post-script commits, inspect the test run and the `# E2E Testing Report` the slash command emits (per `<output_contract>` in `src/deviate/prompts/commands/deviate-e2e.md`). The report must include a `## Flow Coverage Matrix` mapping each `FLOW-XX` from the issue's `flow_refs` to at least one bats scenario, and `## E2E_TEST_COVERAGE` with both unit and E2E results.

```bash
# Suite passed (exit 0 on success)
mise run test-e2e

# Coverage matrix carries a row per named flow
grep -E "^\| FLOW-" <report-path>   # one row per FLOW-XX in flow_refs

# Unit tests still pass (STEP_8 gate)
mise run test

# Each new or updated .bats file is staged
git status --porcelain
```

If any bats test fails, fix the assertion or the implementation before invoking the post-script — the post-script does not re-run the suite itself (it only stages and commits). If the coverage matrix is empty for a flow that has tests, the slash command violated STEP_2.5; re-invoke `/deviate-e2e` with a narrower context, regenerate the report, then post.

### 5. Let the post-script commit the E2E artifacts

The slash command calls `deviate e2e post` automatically. The post-script (`src/deviate/cli/micro.py:3240-3252`) accepts an optional positional `<manifest>` (a path to a JSON manifest whose `commit_subject` field overrides the default) and does two things — you must not skip it:

1. `_validate_manifest(manifest)` — if the slash command handed a manifest path, validates it; otherwise accepts the implicit `{"commit_subject": "feat: E2E phase"}` default.
2. `_commit_phase("feat: E2E phase", root)` — stages all new or updated E2E test files (`.bats`, `.test.ts`, etc.), runs pre-commit hooks (lint + full test suite per `.githooks/`), and commits with the conventional `feat:` subject. Allocate at least 180 s (3 minutes) — the pre-commit hooks include the full unit-test suite.

If `deviate e2e post` exits non-zero, inspect the failure, fix the underlying cause, and re-run it. Do not commit by hand — only the post-script records the E2E artifact atomically.

### 6. Verify the artifact, the branch, and the commit landed

After the slash command returns, confirm everything landed. The E2E test files must be on disk and in the commit, the branch must still be a feature branch, and both the unit and E2E suites must be green:

```bash
# E2E files are committed on the feature branch
git log --oneline -3
git show HEAD --stat | grep -E '\.(bats|test\.ts|spec\.ts|test_.*\.py)$'

# Feature branch is intact (no accidental default-branch commit)
git rev-parse --abbrev-ref HEAD
# Expected: feat/... or fix/...

# Working tree is clean post-commit
git status --porcelain
# Expected: empty

# Both unit and E2E suites pass after the commit
mise run test
mise run test-e2e
```

The post-script's commit subject (`feat: E2E phase`) is the gate for downstream phases. The natural follow-up is [Open the PR for the active worktree](/how-to/pr) — runs `/deviate-pr` (or `tools:review → tools:walkthrough → tools:pr`), creates the GitHub PR, appends `COMPLETED` to `specs/issues.jsonl`, and unblocks dependents via the `blocked_by` resolver.

## Troubleshooting

### Pre-script returns `INCOMPLETE_TASKS`

The active ledger has at least one row whose status is not `REFACTOR` or `COMPLETED` (`e2e_pre`, `src/deviate/cli/micro.py:3230-3232`). The micro-cycle is not yet finished. Inspect the open task:

```bash
# Find the first non-terminal row
jq -r 'select(.status != "REFACTOR" and .status != "COMPLETED") | [.id, .status] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | head -1
```

If it reports `PENDING`, the task has never been started — run [Run a task via the micro dispatcher](/how-to/run) (or the relevant micro-phase how-to: red → green → yellow? → judge → refactor) until the row reaches `REFACTOR`. If the row is stuck at `RED` or `GREEN`, the previous phase's post-script never landed — re-invoke that phase and let it commit, then re-run `/deviate-e2e`.

### Bats is not on `PATH`

`mise run test-e2e` shells out to `bats` directly (`mise.toml:12-14`), and `bats --version` exited non-zero in step 1. Install bats, then re-run the slash command:

```bash
brew install bats-core        # macOS / Homebrew
sudo apt install bats          # Debian / Ubuntu
mise use bats@latest           # if you standardize via mise
```

If bats is installed in a non-standard location, export `PATH` so the canonical invocation can resolve it, or invoke the slash command from inside the worktree so mise's shim picks it up.

### `STEP_8` aborts with `E2E_REQUIRES_UNIT_TESTS_PASS`

The unit-test suite ran in STEP_8 (`src/deviate/prompts/commands/deviate-e2e.md`) failed before E2E was executed. This is a hard gate — E2E must not run on a red unit suite. Inspect the failure:

```bash
mise run test
```

Fix the regression (a test that used to pass now fails because of a REFACTOR-phase edit, or a missed GREEN commit), commit the fix, and re-invoke `/deviate-e2e`. If the failure is unrelated to this feature's work (a flaky test, a missing dependency in the env), address the underlying test before resuming E2E — do not skip STEP_8.

### Post-script fails pre-commit hooks

`_commit_phase` runs pre-commit hooks (lint + full test suite) on the staged E2E files (`src/deviate/cli/micro.py:3251` + the pre-commit hook chain from `.githooks/`). A failing hook aborts the commit. Inspect the hook output:

```bash
# Run the same hook the post-script ran, manually
pre-commit run --all-files
# or, the specific failing hook
pre-commit run <hook-id> --files <new-e2e.bats>
```

Fix the underlying lint or test failure (do not bypass hooks — `--no-verify` is not honored by `_commit_phase` for E2E), then re-invoke `/deviate-e2e` to regenerate the suite and re-run the post-script.

### Post-script times out (>180s)

The post-script allocates a 180 s budget because the pre-commit hooks include the full unit-test suite (`src/deviate/prompts/commands/deviate-e2e.md` STEP_10, warning). If the suite genuinely takes longer, split it: confirm the slowness is reproducible with `mise run test` directly, then run the same command under `pytest -x` to short-circuit on first failure. If only the E2E commit is timing out (other commits finish), the unit-test suite has slow tests that were already there — escalate to the maintainer rather than raising the timeout in the post-script.

### Report shows `FLOW_PROPAGATION_GAP` or `FLOW_COVERAGE: NO_FLOWS_NAMED`

The slash command emitted the report but the `## Flow Coverage Matrix` is empty or warns about a missing `**Flow References**` propagation gap. This is a soft signal: E2E ran, but the meso layer did not link the parent issue's `flow_refs` to the per-task entries in `tasks.md`. Re-run the upstream how-to that produced `tasks.md` (see [Run the /deviate-tasks phase](/how-to/tasks)) and inject the `**Flow References**` bullet per task, then re-run `/deviate-e2e`. If `flow_refs` is empty by design (the parent issue has no user-facing flow), append `NO_FLOWS_NAMED` to the PR description and move on.

## Next Steps

- [Open the PR for the active worktree](/how-to/pr) — the natural follow-up once `/deviate-e2e` lands the suite and the post-script commits; closes the issue via `COMPLETED` in `specs/issues.jsonl` and unblocks dependents.
- [Run a task via the micro dispatcher](/how-to/run) — the upstream how-to if a task was still `PENDING` / `RED` / `GREEN` / `JUDGE` when you invoked `/deviate-e2e`; resolves the next task and routes it through the TDD cycle until it reaches `REFACTOR`, then re-run E2E.
- [Run the /deviate-tasks phase](/how-to/tasks) — the upstream meso layer how-to that produced `tasks.md`; re-invoke it with explicit `**Flow References**` propagation when E2E reports `FLOW_PROPAGATION_GAP`.
- [Reference: Slash Commands](/reference/slash-commands) — inventory entry for `deviate-e2e` (version `1.0.0`, aliases `e2e`, `/spec.tdd.e2e`, `/e2e`, `/tdd.e2e`, category `deviattd-macro-layer` with the typo'd `deviattd-` prefix preserved verbatim).
