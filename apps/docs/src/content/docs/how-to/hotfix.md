---
title: "Run the /deviate-hotfix workflow"
description: "Decompose a bug report into 1–2 autonomous Red-Green-Refactor units via /deviate-hotfix, bypassing RED and committing a tasks.md of targeted fixes."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
  - ISS-ADH-011
---

# Run the /deviate-hotfix workflow

This how-to covers the **HOTFIX** (urgent bug-fix) micro-path, registered at `src/deviate/cli/__init__.py:791` as `cli.add_typer(hotfix_app, name="hotfix")` and backed by `src/deviate/cli/micro.py:3260-3288` (`hotfix_pre` and `hotfix_post`). The `/deviate-hotfix` slash command orchestrates the same pre-script / analysis / post-script sequence the other micro phases use, but it intentionally **bypasses RED** — the `hotfix_pre` contract emits `bypasses_red: true` (`src/deviate/cli/micro.py:3268-3271`) and the task ledger is never walked for a `PENDING` row. The skill is also bounded by the `<hotfix_constraints>` in `src/deviate/prompts/commands/deviate-hotfix.md`: 1–2 tasks, exactly 2 files per task (broken file + test file), 15–45 minutes per task, `[RED]` bullet written before `[GREEN]` bullet. If the bug requires more than two tasks, the slash command rejects to `/deviate-tasks`. You invoke the slash command, review the generated `tasks.md`, and let the post-script commit — the `deviate hotfix pre` / `deviate hotfix post` sub-commands are agent-internal and you should not run them by hand unless you are recovering a wedged post-script.

## Prerequisites

- **A bug report in the conversation or in `$ARGUMENTS`** — the `<user_input>` block of `deviate-hotfix.md` carries the bug text (`<context>` at the end of the prompt). If the report is missing, the slash command emits `NO_BUG_LOCATION` and falls back to `grep` for keywords (`edge_case_handling` table). Be explicit: name the function, the file, and the line range if you have it.
- **An active issue bound to the session** — `hotfix_pre` resolves a task via `_resolve_task_context` (`src/deviate/cli/micro.py:3265`); when the session carries no `active_issue_id` the pre-script falls back to the next `PENDING` row from `specs/**/tasks.jsonl`. If you are starting a new bug fix with no issue yet, scaffold one via `/deviate-shard` first (see [Run the /deviate-shard phase](/how-to/shard)).
- **A feature branch (NOT `main` or `master`)** — the `WRONG_BRANCH` edge case in the prompt aborts the slash command on default branches. `git rev-parse --abbrev-ref HEAD` must report a `feat/...`, `fix/...`, or per-issue branch. If you are on the default branch, run `deviate feature start ISS-NNN-NNN` to create one.
- **The `deviate-hotfix` skill installed in the active agent** — the slash command lives at `src/deviate/prompts/commands/deviate-hotfix.md` (version `1.0.0`, aliases `hotfix`, `/spec.hotfix`, `/hotfix`) and is installed to the active agent's command directory by `deviate setup`. Run `deviate setup` if `/deviate-hotfix` is not wired into your agent.
- **Reasoning-model availability for HOTFIX** — the slash command runs on the macro-layer tier (V4 Pro or Qwen 3.7+ [Thinking] per `specs/_product/architecture.md` and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].hotfix`. Confirm `jq '.models.hotfix // .models.default' .deviate/config.toml` returns a reachable model name.
- **A clean working tree on the feature branch** — the post-script stages and commits `tasks.md` via `_commit_phase("feat: HOTFIX phase", root)` (`src/deviate/cli/micro.py:3287`). Stash or commit any unrelated edits before invoking the slash command.
- **`uv run` (or an activated venv) on `PATH`** — the pre-script and post-script are invoked as Python CLI commands per `.mise.toml`; inside the canonical wrapper the form is `uv run deviate hotfix pre`.

## Steps

### 1. Confirm the bug report, the branch, and the session

Before invoking the slash command, verify the upstream gate. The HOTFIX path is for **urgent, bounded** bug fixes — if the change touches more than 2 files, spans multiple concerns, or has no clear bug description, escalate to `/deviate-tasks` instead.

```bash
# Bug report is in scope (function name, file, line range or reproduction steps)
echo "$BUG_REPORT" | head -3

# On a feature branch, not the default branch
git rev-parse --abbrev-ref HEAD
# Expected: feat/... or fix/... — NOT main / master

# Session is bound (or no active issue is fine for ad-hoc hotfixes)
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('issue:', s.get('active_issue_id')); print('phase:', s.get('current_phase'))"

# Working tree is clean
git status --porcelain
```

If `git status --porcelain` shows unstaged work, the post-script will refuse to commit cleanly. Stash (`git stash push -m "wip"`) or commit (`git commit -am "..."`) first. If you are on `main` or `master`, run `deviate feature start ISS-NNN-NNN` to create a per-issue branch.

### 2. Run the pre-script and inspect the contract

The pre-script (`hotfix_pre`, `src/deviate/cli/micro.py:3260-3273`) resolves the active task context, prints a JSON contract to stdout, and exits. The contract carries `bypasses_red: true` so the post-script will not require a prior `RED` row. Run it as a verification action (the slash command will also run it):

```bash
# Verification only — agent-internal sub-command
deviate hotfix pre
# or, scoped to a specific task
deviate hotfix pre --task TSK-NNN-NN
```

Expected JSON shape (per `src/deviate/cli/micro.py:3267-3271`):

```json
{
  "issue_context": "HOTFIX: fix null pointer crash in parser",
  "bypasses_red": true,
  "completion_criteria": "Bug fix — bypasses RED phase"
}
```

The `issue_context` field mirrors the active task's `description` from `specs/**/tasks.jsonl` when a task is bound. If the JSON comes back empty, the session has no `active_issue_id` and the next PENDING walk returned no rows — the hotfix will operate in ad-hoc mode and you must pass the bug description explicitly in the slash command's user input.

### 3. Run `/deviate-hotfix` and review the analysis

Invoke the slash command inside the agent. The execution sequence (`src/deviate/prompts/commands/deviate-hotfix.md` `execution_sequence`) runs four sub-steps:

```text
/deviate-hotfix Fix division-by-zero in cart.py::calc_total when cart is empty
```

The slash command will:

1. **bug_analysis** — read `specs/constitution.md` for invariants, `grep` for the function or error message, identify the broken file and the matching test file (`*.spec.*`, `*_test.*`, `test_*.py`), and read the broken file to confirm the root cause.
2. **task_generation** — produce 1–2 tasks, each with `[Task_Type]: Bugfix`, `[Execution_Mode]: TDD`, `[Test_Strategy]: Sociable_Unit`, a `Verification` command, `[Estimated_Time]: 15–45 minutes`, `[Files_Touched]` exactly 2 files, and `[Task_Details]` with `[RED]`, `[GREEN]`, `[EDGE_CASES]`, `[ACCEPTANCE]` bullets.
3. **output_writing** — render to `tasks.md` at the workspace root with the schema in the prompt's `output_writing` step (`# Hotfix Tasks: {BRANCH_NAME}` / `## Hotfix: Fix {bug_short_name}` / `### Tasks`).

If the slash command reports the bug is unbounded (`MULTIPLE_BUGS` with > 2 distinct fixes, or `NO_BUG_LOCATION` with no grep hits), it rejects to `/deviate-tasks`. Stop here and re-plan via the meso layer.

### 4. Verify `tasks.md` against the constraints

Before the post-script commits, inspect the generated file. The `<hotfix_constraints>` block (`src/deviate/prompts/commands/deviate-hotfix.md`) is the contract — every generated task must satisfy it:

```bash
# File exists and is non-empty
test -s tasks.md && wc -l tasks.md

# 1-2 tasks only — must NOT have T003+
grep -E '^- \[ \] \[T00[3-9]\]' tasks.md   # must be empty
grep -cE '^- \[ \] \[T00[1-2]\]' tasks.md  # must be 1 or 2

# Each task touches exactly 2 files
grep -cE '^\s+- \S+\.(py|ts|js|go|rs|sh)$' tasks.md   # must be 2 per task

# RED bullet comes before GREEN bullet per task
awk '/^- \[ \] \[T00/{t=$0; print t, "[RED]=" (red?"yes":"NO"), "[GREEN]=" (green?"yes":"NO")} /\[RED\]/{red=1} /\[GREEN\]/{green=1} /^## /{red=0;green=0}' tasks.md
```

If any constraint fails, edit `tasks.md` directly (this is the one artifact HOTFIX lets you touch before the post-script) or re-invoke `/deviate-hotfix` with a narrower bug report. Do not commit the broken file yourself — the post-script owns the commit.

### 5. Let the post-script commit the hotfix

The slash command calls `deviate hotfix post` automatically. The post-script (`src/deviate/cli/micro.py:3276-3288`) does two things and you must not skip it:

1. `_validate_manifest(manifest)` — if the slash command handed a manifest path, validates it; otherwise accepts the implicit `{"commit_subject": "feat: HOTFIX phase"}` default.
2. `_commit_phase("feat: HOTFIX phase", root)` — stages `tasks.md` (and any pre-staged working-tree changes) and commits with the conventional `feat:` subject. Pre-commit hooks run; allocate at least 180 s (3 minutes) — the hooks include the full test suite.

If `deviate hotfix post` exits non-zero, inspect the failure, fix the underlying cause, and re-run it. Do not commit by hand — only the post-script records the HOTFIX artifact atomically.

### 6. Verify the artifact, the branch, and the commit landed

After the slash command returns, confirm everything landed. The `tasks.md` must be on disk and in the commit, the branch must still be a feature branch, and the file's contents must conform to the constraints:

```bash
# tasks.md is committed on the feature branch
git log --oneline -3
git show HEAD --stat | head -10

# Feature branch is intact (no accidental default-branch commit)
git rev-parse --abbrev-ref HEAD
# Expected: feat/... or fix/...

# Working tree is clean post-commit
git status --porcelain
# Expected: empty

# tasks.md is tracked and non-empty
git ls-files --error-unmatch tasks.md
wc -l tasks.md
```

The verification command from the first task (e.g., `pytest tests/test_cart.py::test_calc_total_empty_cart -v`) is now the gate for the actual bug fix. Run the original `/deviate-red` → `/deviate-green` → `/deviate-judge` cycle against T001 (and T002 if generated) to land the actual code change — `/deviate-hotfix` only scaffolds and commits the task list.

## Troubleshooting

### Pre-script returns `FAILURE` with `NO_BUG_LOCATION`

The slash command could not locate the bug via `grep` and the user input did not name a function or file. Inspect what the agent searched for in the chat log, then re-invoke `/deviate-hotfix` with a more concrete bug report:

```text
/deviate-hotfix Bug: NameError: name 'JWTService' is not defined at src/auth/handler.py:42 when token header is missing
```

If the function genuinely does not exist (e.g., a typo in a constant), the bug is a feature, not a hotfix — escalate to `/deviate-tasks` and plan the addition properly.

### Pre-script returns `FAILURE` with `WRONG_BRANCH`

The current branch is `main` or `master`. The prompt's `edge_case_handling` table aborts hotfixes on default branches because they bypass the meso-layer review gate. Create a feature branch first:

```bash
deviate feature start ISS-NNN-NNN
# or, ad-hoc:
git checkout -b fix/<short-bug-slug>
```

Then re-invoke `/deviate-hotfix` from the new branch.

### Generated `tasks.md` has 3+ tasks

The prompt's `<max_tasks>1-2</max_tasks>` and `MULTIPLE_BUGS` edge case both reject expansions beyond T002. If the slash command emits a `tasks.md` with T003+, it violated the constraint — re-invoke `/deviate-hotfix` with a narrower bug report that isolates one bug at a time. If the underlying problem truly spans three or more concerns, the work is feature work, not a hotfix — re-plan via `/deviate-tasks` and let the meso layer decompose it properly.

### Post-script fails pre-commit hooks

`_commit_phase` runs pre-commit hooks (lint + full test suite) on the staged `tasks.md` (`src/deviate/cli/micro.py:3287` + the precommit hook chain from `.githooks/`). A failing hook aborts the commit. Inspect the hook output:

```bash
# Run the same hook the post-script ran, manually
pre-commit run --all-files
# or, the specific failing hook
pre-commit run <hook-id> --files tasks.md
```

Fix the underlying lint or test failure (do not bypass hooks — `--no-verify` is not honored by `_commit_phase` for HOTFIX), then re-invoke `/deviate-hotfix` to regenerate `tasks.md` and re-run the post-script.

### Post-script times out (>180s)

The post-script allocates a 180 s budget because the precommit hooks include the full test suite (`src/deviate/prompts/commands/deviate-hotfix.md` `post_script` step, warning). If the suite genuinely takes longer, split it: confirm the slowness is reproducible with `mise run test` directly, then run the same command under `pytest -x` to short-circuit on first failure. If only the HOTFIX commit is timing out (other commits finish), the test suite has slow tests that were already there — escalate to the maintainer rather than raising the timeout in the post-script.

### Slash command completed but `tasks.md` is missing

The post-script commits `tasks.md` only if it exists and is non-empty. If the slash command reported success but `git ls-files tasks.md` returns nothing, the slash command's `output_writing` step wrote to a different path (the prompt's example uses "workspace root" but does not lock the absolute path). Check the chat log for the `tasks.md` path the agent reported, then `git add` and commit it manually with the conventional subject `feat: HOTFIX phase - <bug-slug>`, append a recovery note to the issue thread, and re-run the post-script next time you invoke `/deviate-hotfix` from the same branch.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — once `/deviate-hotfix` lands `tasks.md`, run the generated T001 (and T002 if any) through `red → green → judge → refactor` via the dispatcher; the HOTFIX skill only scaffolds and commits the task list.
- [Run the /deviate-shard phase](/how-to/shard) — the upstream how-to that produces the `specs/issues.jsonl` entry and the per-issue spec the HOTFIX skill references; if you reached hotfix without an issue, start here.
- [Run the /deviate-tasks phase](/how-to/tasks) — the broader decomposition path for fixes that exceed the 1–2-task HOTFIX budget; re-route to this when the slash command rejects with `MULTIPLE_BUGS` or `NO_BUG_LOCATION`.
- [Reference: Slash Commands](/reference/slash-commands) — inventory entry for `deviate-hotfix` (version `1.0.0`, aliases `hotfix`, `/spec.hotfix`, `/hotfix`, category `deviattd-macro-layer`) and the flag surface for the underlying `deviate hotfix pre` (`--task`) and `deviate hotfix post` (positional `<manifest>`).
