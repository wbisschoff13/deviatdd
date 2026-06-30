---
title: "Your first RED → GREEN → REFACTOR cycle"
description: "Walk one task through the DeviaTDD micro-cycle with /deviate-red, /deviate-green, and /deviate-refactor, verifying at each step."
doc_type: tutorial
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Your first RED → GREEN → REFACTOR cycle

By the end of this tutorial you will have walked a single task end-to-end through the DeviaTDD micro-cycle: you will have written a failing test, watched an implementation turn it green, then cleaned up the code without changing its behavior. Every creative step is a slash command; your hands stay on the keyboard only to read state and verify the agent's work.

## Prerequisites

Before you start, make sure your workspace is bootstrapped and you have a task ready to cycle:

- **DeviaTDD installed and the slash-command library installed** — see [Bootstrap a DeviaTDD workspace](/how-to/setup). After this, `/deviate-red`, `/deviate-green`, and `/deviate-refactor` appear in your agent's command palette.
- **An active issue bound to the session** — `.deviate/session.json` carries a non-empty `active_issue_id`. If yours is empty, run `/deviate-plan` against the issue, or pass `--issue-id ISS-NNN-NNN` to bind it.
- **A `tasks.md` for the active issue with at least one `status: PENDING` row** — produced by `/deviate-tasks`. The pre-script in each phase will pick the next one for you.
- **A clean working tree on the per-issue feature branch** — confirmed by `git status --porcelain` returning empty output.

## Step 1 — Read the task you are about to cycle

Before invoking any slash command, look at what the agent will work on. The pre-script in each phase reads `.deviate/session.json` and the append-only ledger to pick the next `PENDING` task; nothing magical happens. Run this verification command to read the session state:

```bash
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('issue:', s.get('active_issue_id')); print('phase:', s.get('current_phase'))"
```

Expected result:

```
issue: ISS-NNN-NNN
phase: IDLE
```

`IDLE` is the expected landing state on a fresh session after `/deviate-tasks` committed. If `current_phase` is anything else (for example `RED` or `GREEN`), the session is mid-recovery from a prior run — see [Troubleshooting in the /deviate-red how-to](/how-to/red#troubleshooting) before continuing.

## Step 2 — Write the failing test with `/deviate-red`

The RED phase is where the agent writes a test for the next `PENDING` task. The test must fail for the *right* reason — because the implementation does not exist yet, not because of a syntax error. Invoke the slash command:

```text
/deviate-red
```

The slash command runs three internal sub-steps: it calls `deviate red pre` to print a JSON contract (with `task_id`, `test_command`, `lint_command`), writes a failing test that exercises the contract's task against the spec, then calls `deviate red post` to verify the test still fails and commit it. **You do not run any of those sub-commands by hand.** The agent tells you when the test is written.

When the slash command returns, verify the artifact landed as a RED-state commit:

```bash
# Latest commit on the feature branch is the failing test
git log --oneline -1

# The session advanced to RED
cat .deviate/session.json | python -c "import json,sys; print('phase:', json.load(sys.stdin).get('current_phase'))"

# The test still fails (this is intentional — do not "fix" it)
mise run test -- tests/<feature>/test_<module>.py
```

Expected result:

- The `git log` line ends with `test(<scope>): RED phase - failing test`.
- `phase:` prints `RED`.
- `mise run test` exits non-zero with an assertion failure or a `NameError` for a stub that the implementation has not yet provided.

If `mise run test` shows a syntax error instead of an assertion failure, see [Test crashes with a syntax error](/how-to/red#test-crashes-with-a-syntax-error-instead-of-an-assertion-failure). If the suite passes, the slash command aborts with `RedMustPassError` — tighten the assertion and re-run.

## Step 3 — Implement with `/deviate-green`

The failing test is your specification. Now invoke the slash command that writes the minimum production code to turn it green:

```text
/deviate-green
```

The slash command writes minimal implementation code under `src/`, re-runs `mise run test` until it passes, then calls `deviate green post` to commit and advance the session. **You do not write implementation code by hand in this tutorial — that is the agent's job.** The agent tells you when GREEN is achieved.

When the slash command returns, verify the test now passes:

```bash
# Latest commit on the feature branch is the implementation
git log --oneline -2

# The test passes, and lint is clean
mise run test
mise run lint

# The session advanced to GREEN
cat .deviate/session.json | python -c "import json,sys; print('phase:', json.load(sys.stdin).get('current_phase'))"
```

Expected result:

- The most recent commit message references the GREEN phase (for example, `feat(<scope>): implement <function-name>`).
- `mise run test` exits 0 with no failures.
- `mise run lint` exits 0.
- `phase:` prints `GREEN`.

If `mise run test` still shows a failure after the slash command reports success, do not retry by hand — see [Troubleshooting in the /deviate-green how-to](/how-to/green#troubleshooting).

## Step 4 — Clean up with `/deviate-refactor`

Tests are green; the implementation is correct but may not yet be tidy. Invoke the cleanup slash command:

```text
/deviate-refactor
```

The slash command looks for code smells (duplicated logic, large functions, unclear names), applies targeted refactors that preserve behavior, then calls `deviate refactor post` to re-run the test suite and commit only if the tests still pass.

When the slash command returns, verify nothing changed except structure:

```bash
# A new commit on the feature branch is a refactor
git log --oneline -3

# The test suite still passes (refactor must be behavior-preserving)
mise run test

# The session returned to IDLE
cat .deviate/session.json | python -c "import json,sys; print('phase:', json.load(sys.stdin).get('current_phase'))"
```

Expected result:

- A new commit appears whose message starts with `refactor(<scope>)`.
- `mise run test` exits 0 with the same pass count as before the refactor.
- `phase:` prints `IDLE`.

If the post-script refused to commit, the refactor changed behavior — re-invoke `/deviate-refactor` against the last GREEN commit and try a smaller cleanup.

## Verification

You have completed one full TDD cycle. To confirm everything landed:

```bash
# Three commits on the feature branch, in order: RED, GREEN, REFACTOR
git log --oneline -3

# Append-only ledger records the cycle (last record per task wins)
jq -r 'select(.id=="TSK-NNN-NN") | [.id, .status, .timestamp] | @tsv' \
  specs/<NNN>-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -3
```

Expected result:

- Three commits in order: `test(...): RED phase - failing test`, then `feat(...): ...`, then `refactor(...): ...`.
- The latest row for the task ID in `tasks.jsonl` carries `status: COMPLETED` (or `REFACTOR` if the auto-advance did not fire).
- The session's `current_phase` is `IDLE`.

## Walk the whole cycle in one shot (optional)

If you would rather let the micro dispatcher drive the cycle, `deviate run` walks the next `PENDING` task through RED → GREEN → REFACTOR in a single invocation. It is a verification-only path — you invoke it once and inspect `.deviate/run.jsonl`:

```bash
deviate run
```

For a learning walkthrough, prefer the three slash commands above — they are the canonical way to feel each phase land.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — when you are comfortable with the cycle, let `deviate run` walk every PENDING task in one shot.
- [Run the /deviate-red phase](/how-to/red) — the deep-dive reference for the RED phase, including all flags, edge cases, and recovery paths.
- [Tutorials: a guided tour](/tutorials/intro) — return to the tutorial index to find the next guided walkthrough.