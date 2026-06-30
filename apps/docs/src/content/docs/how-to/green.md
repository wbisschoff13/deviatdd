---
title: "Run the /deviate-green phase"
description: "Implement the minimal production code that makes the failing RED test pass, then commit via the mandated post-script and emit the GREEN_STATE_ACHIEVED handover manifest."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
  - ISS-ADH-011
---

# Run the /deviate-green phase

This how-to covers `/deviate-green` — the GREEN (implementation) phase of the DeviaTDD micro-cycle (slash-command source `src/deviate/prompts/commands/deviate-green.md:1-15`, registered at `src/deviate/cli/__init__.py:785`). The slash command takes a previously-failing test from [`/deviate-red`](/how-to/run) (or the RED handover manifest in conversation context), writes the **minimum** production code needed to turn it green, runs the contract `test_command` and `lint_command`, then commits through the mandated `deviate green post` script. After GREEN lands cleanly, the agent emits a `GREEN_STATE_ACHIEVED` handover manifest with `next_phase: "/deviate-refactor"`; after three failed `deviate green post` attempts, the agent emits a `yellow_trigger: true` manifest that hands off to `/deviate-yellow` for amendment review.

The slash command is the direct, manual GREEN path. In most workflows the same phase runs automatically inside [`deviate run`](/how-to/run) (the micro dispatcher), which resolves the next `PENDING` task and routes it through `red` → `green` → `judge` → `refactor` per the task's `execution_mode`. Use this how-to when you need to re-run GREEN for a single task outside the dispatcher (e.g., after a Judge rejection, after a contract-drift fix, or when running an isolated micro session).

## Prerequisites

- **`/deviate-red` completed for the same task** — the failing test file must already exist and be discoverable on the feature branch. The GREEN phase reads the failing assertions directly from the test file (or, if available, from the RED handover manifest in conversation context). If the test file is missing, the pre-script halts with `NO_TASKS_REMAINING` or the agent must re-derive requirements from `spec.md` and `data-model.md`. See [Run a task via the micro dispatcher](/how-to/run) for the canonical Red→Green path.
- **A clean worktree on the feature branch for the active issue** — `deviate green post` invokes the pre-commit hook chain (lint, format-check, tests) and creates the GREEN commit on the current branch. The pre-script does NOT auto-claim a worktree the way `deviate plan pre` does; you must already be on the per-issue branch created by `/deviate-specify` or `/deviate-tasks`. Verify with `git rev-parse --abbrev-ref HEAD` and `git status` (no uncommitted edits to unrelated files).
- **`spec.md`, `data-model.md`, and `constitution.md` accessible** — the implementation step extracts the schema and gate semantics from these specs to write code that satisfies the failing assertions without breaking existing functional signatures. If any spec is missing or stale, the contract-drift check will halt execution (`API_SIGNATURE_CONFLICT`).
- **Reasoning-model availability for V4 Flash** — the GREEN phase is routed to the low-cost tier per `specs/DeviaTDD-architecture.md` §4 and `src/deviate/state/config.py::resolve_phase_model`. Confirm the workspace is `deviate setup`-bootstrapped and `.deviate/config.toml` `[models].green` resolves (default: `v4-flash`). If you need to override the tier, set `[models].green = "v4-pro"` per-phase.
- **Test isolation ready when tests touch `git`** — if the failing test involves git operations (worktree creation, branch mutation, etc.), the implementation step MUST run the test in a temp dir via `create_temp_dir` + `git init`, not the project repo. The test file itself is expected to handle isolation through a fixture; the GREEN agent just runs the contract `test_command` as-issued.
- **`uv run` (or activated venv) on `PATH`** — the slash command is invoked as `/deviate-green`, but the post-script it shells out to is `deviate green post` (Python CLI). The canonical wrapper is `uv run deviate green post` per `.mise.toml`.

## Steps

### 1. Confirm the failing test is staged and the contract is recoverable

Before invoking the slash command, verify the RED artefacts are present. The pre-script emits a JSON contract on stdout that names the `task_id`, `test_command`, and `lint_command`; if you don't have the contract in conversation context, derive it from the test file path and the project's `pyproject.toml` (or `package.json`, etc.).

```bash
# Confirm the feature branch is checked out and clean
git rev-parse --abbrev-ref HEAD
git status --short

# Locate the failing test from the prior RED phase
ls tests/ 2>/dev/null || find . -path ./node_modules -prune -o -name "test_*.py" -print | head -5

# Confirm the test still fails against the current (pre-GREEN) code
{test_command} 2>&1 | tail -20
```

If `git status` shows uncommitted edits to non-test files, commit or stash them before invoking `/deviate-green` — the post-script's pre-commit hook will refuse a dirty tree. If the test passes already, GREEN has nothing to do; re-run `/deviate-red` to regenerate a failing assertion or skip directly to `/deviate-refactor`.

### 2. Run `/deviate-green`

The slash command is the single primary action for this how-to. Invoke it inside the agent chat. The slash command orchestrates three sub-steps internally: the pre-script (next step), the agent-driven implementation write (steps 4–6), and the post-script (step 7). You do NOT invoke `deviate green pre` or `deviate green post` as a CLI directly — the agent skill does.

```bash
# Auto-discover the next RED task via the pre-script contract
/deviate-green

# Optionally narrow by task ID (forwarded as a hint to the pre-script)
/deviate-green TSK-NNN-NN
```

The slash command runs `deviate green pre` first to emit a JSON contract on stdout, then loads system requirements, then hands off to the implementation step. If you pass a `task_id`, the pre-script uses it to locate the corresponding test file; otherwise it walks the append-only ledger for the most recent RED entry on the active issue.

### 3. Wait for the pre-script to emit the JSON contract

The pre-script (`green_pre`, `src/deviate/cli/micro.py:2592`) prints a JSON contract on stdout and exits. The contract contains: `status`, `task_id`, `test_command`, `lint_command`, `spec_dir`, `feature_slug`, `task_title`, `task_type`, `task_mode`, `test_strategy`, `verification`, `estimated_time`, `dependency`, `rationale`, `task_details`, `files_touched`, `universal_constraints`, `repo_root`, `git_branch`, `timestamp`.

- If `status` is `READY` — proceed to step 4.
- If `status` is `NO_TASKS_REMAINING` — there is no RED entry on the ledger for the active issue. Surface the message to the user; recommend running `/deviate-red` first or picking a different task ID.
- If `status` is `FAILURE` — surface the `reason` field verbatim and halt.

### 4. Read the failing test and load the spec context

Parse the JSON contract for `test_command`, `lint_command`, `task_id`, and `files_touched`. The agent-driven implementation step begins by reading the failing test end-to-end and loading the upstream spec context:

1. Read the target test file to isolate the exact assertion expectations (imports, fixtures, parametrizations, expected exception types).
2. Read `specs/constitution.md` for tech-stack standards and the testing protocol.
3. Read `specs/<epic>/spec.md` for the technical contract and `data-model.md` for type signatures.
4. Read the task description in `tasks.md` — this may contain updated context or **Judge Feedback** from a previous JUDGE/YELLOW rejection cycle that changes what "minimal" means.
5. Parse the test framework conventions (pytest fixtures, parametrize markers, monkeypatch scope) so the implementation matches rather than fights the harness.

If any spec section contradicts a test assertion (contract drift), halt immediately and report `API_SIGNATURE_CONFLICT` with the offending file path and clause. Do not write code against a drifted contract — fix the test or re-shard the spec first.

### 5. Implement the minimal code change

Write the smallest production-code change that turns the failing assertion green. The implementation rules are strict:

1. Implement **only** the production code required to satisfy the failing assertions — no speculative features, no unused helpers, no extra refactors (REFACTOR is a separate phase).
2. Maintain existing functional signatures — do not rename parameters, change return types, or alter module boundaries that the test imports.
3. Touch **only** the production files named in `files_touched` plus obvious siblings they import. If a refactor would touch unrelated files, defer it to `/deviate-refactor`.
4. If the test involves git operations, run the contract `test_command` against a temp-dir-isolated repo (`create_temp_dir` + `git init` + copy fixtures) — never against the project repo, which would mutate the working tree mid-phase.

After writing the code, run both verification commands from the contract. Loop until both pass cleanly (exit code 0, no warnings escalated to errors):

```bash
{test_command}
{lint_command}
```

If lint fails, fix the lint issues and re-run both commands. If tests fail, iterate on the implementation — do NOT modify the test file (GREEN cannot change tests; if the test is wrong, escalate to `/deviate-yellow`).

### 6. Wait for the agent to run the post-script (mandatory)

After the implementation is verified locally, the agent runs `deviate green post` (`green_post`, `src/deviate/cli/micro.py:2628`). **This step is non-bypassable** — the post-script is the only accepted way to land the GREEN commit. Manual `git add` + `git commit` are not detected by the orchestrator and trigger fallback warnings.

The post-script:

1. Stages all changed files under the feature branch.
2. Runs the pre-commit hook chain (lint, format-check, full test suite).
3. Updates the append-only task ledger (`specs/**/tasks.jsonl`) with the GREEN transition.
4. Creates the GREEN commit using the conventional format.

**Allocate at least 180 seconds (3 minutes) of timeout** when the agent shells out to this command — the pre-commit hook runs the full test suite, which can take 20–60 seconds per test run plus retry overhead.

If `deviate green post` returns non-zero or its output contains `COMMIT_FAILED`, inspect the pre-commit hook output to identify the failing check (lint / format / test), fix the underlying problem, re-run the test/lint locally to confirm, and ask the agent to re-invoke `deviate green post`. After **3 failed attempts**, do NOT keep retrying — the agent must emit a YELLOW_TRIGGER manifest instead (see step 7b).

### 7. Verify the GREEN state landed (commit + handover manifest)

After the post-script returns zero, the agent emits a `GREEN_STATE_ACHIEVED` handover manifest as a fenced ```` ```yaml ```` block. Confirm the manifest's fields and the on-disk state:

```bash
# Latest commit on the feature branch includes the GREEN changes
git log --oneline -3
git show HEAD --stat | head -20

# Append-only ledger advanced the task from RED → GREEN (last record wins)
jq -r 'select(.task_id=="TSK-NNN-NN") | [.id, .status, .timestamp] | @tsv' \
  specs/<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -3

# Session phase advanced
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

The handover manifest's `status` must be `PASS`, `yellow_trigger: false`, `verification_command` must echo what you ran in step 5, and `next_phase` must be `/deviate-refactor`. The session phase advances to `GREEN` (or `REFACTOR` after the next phase lands). If any field disagrees with the on-disk state, halt — do not proceed to REFACTOR with a mismatched manifest.

### 7b. (Failure path) Emit a YELLOW_TRIGGER manifest after 3 failed post-script attempts

If `deviate green post` fails three times in a row with the same root cause (tests persistently fail, lint cannot be satisfied without breaking signatures, etc.), the agent must emit a YELLOW_TRIGGER manifest instead of `GREEN_STATE_ACHIEVED`:

```yaml
phase: "GREEN"
task_id: "TSK-NNN-NN"
status: "FAIL"
yellow_trigger: true
test_changes:
  "tests/path/to/test_file.py": "DESCRIPTION_OF_NEEDED_CHANGE"
rationale: "WHY_TESTS_CANNOT_PASS_WITH_CURRENT_IMPLEMENTATION_APPROACH"
next_phase: "/deviate-yellow"
```

Do NOT proceed to a PASS handover while this state holds. The orchestrator will route to `/deviate-yellow` for an isolated amendment review where the test changes are evaluated out-of-band. The TDD state machine permits this exact escape hatch; without it, a broken test would deadlock the micro cycle.

## Troubleshooting

### Pre-script returns `NO_TASKS_REMAINING`

The active issue has no RED entry in `specs/**/tasks.jsonl`, meaning the prior `/deviate-red` phase never landed a failing test (or the append-only ledger was reset). Re-run `/deviate-red` for the same `task_id` to regenerate a failing test, then re-invoke `/deviate-green`. If you ran `/deviate-green` by accident without first going through RED, that is the fix — RED must precede GREEN.

### Pre-script returns `FAILURE` with a contract-drift message

The pre-script detected that the contract schema (likely `data-model.md` or `spec.md`) doesn't match the test file's assertions. This is the contract-drift guard firing — GREEN cannot proceed because the implementation would either violate the spec or fight the test. Halt the phase, read the drift message to identify the conflicting file and clause, and either (a) re-shard the affected spec section if the test is correct, or (b) regenerate the test if the spec was updated after RED.

### Lint passes locally but `deviate green post` reports lint failure

The post-script runs the project's pre-commit hooks, which can apply stricter rules than the bare `lint_command` (e.g., `ruff format --check` on top of `ruff check`). Re-run the full hook locally to reproduce:

```bash
git diff --cached --name-only
pre-commit run --files $(git diff --cached --name-only)
```

Fix the surfaced issues (formatting, import order, type annotations), `git add` the corrections, and re-invoke `/deviate-green` so the agent can re-run `deviate green post`. The post-script will refuse to commit until every hook passes.

### `deviate green post` returns `COMMIT_FAILED` with a pre-commit hook traceback

The hook chain itself errored (not a lint/test failure — a Python traceback in `.pre-commit-config.yaml` or a missing dependency). The pre-commit traceback is in the post-script's stderr. Common causes: a hook version pinned to an unavailable tool, a virtualenv not activated at hook runtime, or a repo URL that no longer resolves. Fix the `.pre-commit-config.yaml` and re-invoke the post-script. If you need to bypass a specific hook for one phase only, edit the file rather than passing `--no-verify` — the orchestrator's fallback warnings will mark the commit as suspect regardless.

### Tests pass locally but fail under `deviate green post`

The post-script runs the full test suite, not just the contract `test_command` from the pre-script. A passing contract test does not guarantee passing sibling tests if the GREEN implementation regressed an unrelated module. Inspect the failing test's traceback — if it touches code your GREEN change modified, fix the regression in `src/`. If it touches unrelated code, the failure is pre-existing and out of scope for this phase; fix it in a separate task or open an issue, then re-invoke `/deviate-green`.

### Git-isolation test corrupted the project worktree

If the failing test involves git operations and the GREEN agent ran it against the project repo instead of a temp dir (skipping the `create_temp_dir` + `git init` isolation step), the test may have created phantom worktrees, branches, or stash entries inside the project repo. Audit the working tree, remove the orphans, and re-run the test under isolation. The slash command's contract notes this as a hard rule — if the agent skipped it, surface the violation and re-issue `/deviate-green` with an explicit reminder in the user input.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — the canonical path that runs RED → GREEN → JUDGE → REFACTOR in one invocation; use this when the GREEN failure isn't a contract drift and you want the full micro cycle.
- [Run the /deviate-refactor phase](/how-to/refactor) — the next phase after GREEN_STATE_ACHIEVED; cleans up the minimal implementation into idiomatic code without changing behaviour.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `deviate-green` (category `deviattd-macro-layer`, version `1.0.0`, aliases `green`, `/spec.tdd.green`, `/green`, `/tdd.green`).
