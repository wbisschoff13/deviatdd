---
title: "Run the /deviate-yellow phase"
description: "Evaluate a GREEN-phase test-amendment proposal via `/deviate-yellow`, then commit or revert the changes via `deviate yellow post --approved` (or `--rejected`)."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Run the /deviate-yellow phase

This how-to covers the **YELLOW** (conditional test amendment) phase of the DeviaTDD micro-cycle, implemented by the `/deviate-yellow` slash command and paired with `deviate yellow pre` / `deviate yellow post` hooks (`src/deviate/prompts/commands/deviate-yellow.md`, registered as `cli.add_typer(yellow_app, name="yellow")` at `src/deviate/cli/__init__.py:786`). YELLOW is not part of the default `red → green → judge → refactor` cycle — it fires only when the GREEN phase emits `yellow_trigger: true` in its handover (tests persistently failed after three implementation attempts). An isolated V4 Pro judge evaluates the proposed test changes, then the operator commits them with `deviate yellow post --approved` or reverts them with `deviate yellow post --rejected` (per `specs/DeviaTDD-architecture.md:204-209`).

## Prerequisites

- **A `yellow_trigger: true` handover from the GREEN phase** — YELLOW only fires when GREEN emits the trigger after three failed `deviate green post` attempts (`src/deviate/prompts/commands/deviate-green.md` handover_emission step). The trigger carries a `rationale` and a `test_changes` payload describing which test files the GREEN agent believes must change. If GREEN emitted `status: PASS`, this how-to does not apply — re-run `/deviate-refactor` instead.
- **`deviate-yellow` skill installed in the active agent** — `deviate yellow pre` calls `_load_skill_content("YELLOW")` (`src/deviate/cli/micro.py:2753`) and prints `[yellow]SKILL_NOT_FOUND[/] deviate-yellow` when the prompt is missing. Run `deviate setup` if the slash command is not wired into your agent's command directory.
- **A clean worktree on the active issue's feature branch** — YELLOW mutates the test files GREEN touched; the pre-script detects phase changes via `git status --porcelain` (`_detect_phase_changes`, `src/deviate/cli/micro.py:2756`) and the post-script either commits them or runs `git restore .` (lines 2802, 2810). An uncommitted scratch file outside the proposal will be reverted on rejection — commit or stash it first.
- **V4 Pro reasoning-model availability** — YELLOW runs in an isolated session on the premium compliance tier (`src/deviate/prompts/commands/deviate-yellow.md` model-tier section) for cache-sacrifice integrity. Confirm the model tier via `jq '.models' .deviate/config.toml` and that the configured V4 Pro endpoint is reachable from the worktree.
- **`uv run` (or an activated venv) on `PATH`** — the pre-script and post-script are invoked as Python CLI commands per `.mise.toml`; inside the canonical wrapper the form is `uv run deviate yellow pre …`.

## Steps

### 1. Confirm the GREEN handover set `yellow_trigger: true`

Before invoking YELLOW, inspect the latest GREEN handover the micro dispatcher recorded. YELLOW is a conditional phase; running it on a passing GREEN is a misroute. The trigger lives in the latest task record whose `status` is `GREEN` or `YELLOW` across every `specs/**/tasks.jsonl` ledger file (the post-script walks the same set at `src/deviate/cli/micro.py:2795-2799`).

```bash
# Find the most recent GREEN or YELLOW ledger row for the active issue
jq -r 'select(.status=="GREEN" or .status=="YELLOW") | [.id, .status, .yellow_trigger, .rationale] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# Confirm the session is parked on YELLOW (the dispatcher only routes here on yellow_trigger=true)
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

A `yellow_trigger: true` row with a non-empty `rationale` and a `current_phase` of `GREEN` (the dispatcher set it back to GREEN when handing off) is the precondition. If the latest row says `status: PASS` and `yellow_trigger: false`, `/deviate-yellow` is not the next phase — run `/deviate-refactor`.

### 2. Emit the pre-script contract

The pre-script is the agent's evidence pack — it lists the files GREEN touched and the test files in scope. Run it (or let the `/deviate-yellow` slash command run it via its pre-hook) and capture the JSON for the operator's review:

```bash
deviate yellow pre
# or, scoped to a specific task
deviate yellow pre --task TSK-NNN-NN
```

Expected JSON shape (`yellow_pre`, `src/deviate/cli/micro.py:2746-2765`):

```json
{
  "proposed_changes": ["<relative paths of files GREEN modified>"],
  "rationale": "YELLOW phase - review proposed test amendments",
  "test_files": ["<test files the proposal touches>"]
}
```

A `SKILL_NOT_FOUND` line means `deviate-yellow` is not installed in this worktree — re-run `deviate setup` and re-run the pre-script before invoking `/deviate-yellow`.

### 3. Run `/deviate-yellow` and read the verdict

Run the slash command inside the agent. It evaluates the proposal against the four-factor rubric in `src/deviate/prompts/commands/deviate-yellow.md` `evaluation_guidelines` — necessity, scope, spec alignment, rationale sufficiency — and emits a YAML handover manifest:

```yaml
phase: YELLOW
status: SUCCESS        # or FAILURE
rationale: "Test amendment approved — changes are necessary and spec-aligned"
task_id: "TSK-NNN-NN"
yellow_trigger: false
test_changes:
  files_to_modify:
    - path: "tests/path/to/test_file.py"
      verdict: "ACCEPTED"   # or REJECTED
```

Read the verdict carefully. On `status: FAILURE` the rationale names which factor failed (e.g., "Implementation could be rewritten to match existing test assertions" — `src/deviate/prompts/commands/deviate-yellow.md` output_format_schemas). Mixed verdicts (some files ACCEPTED, some REJECTED) are not supported — YELLOW is all-or-nothing.

### 4. Commit or revert via `deviate yellow post`

Apply the verdict. The two flags are mutually exclusive — passing both prints `MUTUALLY_EXCLUSIVE` and exits 1 (`yellow_post`, `src/deviate/cli/micro.py:2773-2777`):

```bash
# Accept the amendment — commits the test changes and advances the session to JUDGE
deviate yellow post --approved

# Reject the amendment — runs `git restore .`, reverts every change, returns session to GREEN
deviate yellow post --rejected
```

Behavior on each branch (per `src/deviate/cli/micro.py:2801-2816`):

- `--approved`: `_commit_phase` writes the commit with subject `feat: YELLOW phase - approved amendments`, appends `YELLOW_APPROVED` to the most recent `GREEN`/`YELLOW` ledger row, and `force_transition_to("JUDGE")` so `/deviate-judge` runs next.
- `--rejected`: `git restore .` reverts every modification, appends `YELLOW_REJECTED` to the latest GREEN/YELLOW row, and `force_transition_to("GREEN")` so the next `deviate run` loops back through RED → GREEN with the original test suite intact.

### 5. Verify the ledger, session, and commit landed

Confirm the post-script's side effects match the verdict. Three independent checks — they all should agree:

```bash
# 1. Ledger: latest YELLOW-row transition carries the verdict status
jq -r 'select(.status=="YELLOW") | [.id, .timestamp] | @tsv' \
  specs/NNN-<epic>/issues/ISS-NNN-NNN-<slug>/tasks.jsonl | tail -1

# 2. Session: JUDGE on approval, GREEN on rejection
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"

# 3. Working tree: clean with the expected commit on top (or fully reverted)
git status --porcelain
git log --oneline -1
```

On approval you should see a clean tree with `feat: YELLOW phase - approved amendments` as `HEAD` and `current_phase: JUDGE` in `.deviate/session.json`. On rejection the tree must be clean (the `git restore .` removed every uncommitted change) and `current_phase: GREEN`.

## Troubleshooting

### `deviate yellow pre` prints `SKILL_NOT_FOUND`

The `deviate-yellow` prompt is missing from the active agent's command directory. `deviate setup` walks every detected agent (`.claude/commands/`, `.opencode/commands/`, `.factory/commands/`, `.pi/prompts/`) and copies every command. Re-run `deviate setup` to (re)install `deviate-yellow`, then re-run the pre-script and the slash command. If the slash command is present but the JSON contract never appears, the worktree is outside the workspace that ran `deviate setup` — `cd` into the bootstrapped root.

### YELLOW verdict is `FAILURE` with `reason: "NO_PROPOSAL"` or `"NO_CHANGES_PROPOSED"`

The YELLOW agent received an empty proposal (`src/deviate/prompts/commands/deviate-yellow.md` edge_case_handling). Most common cause: the GREEN handover carried `yellow_trigger: true` but `test_changes` was empty (the GREEN agent flagged the trigger but did not name a file). Inspect the latest GREEN row in the append-only ledger:

```bash
jq -r 'select(.status=="GREEN") | .test_changes' specs/**/tasks.jsonl | tail -1
```

If `test_changes: {}`, the RED test's assertion probably matched what GREEN wrote — re-run `/deviate-green` instead. If the field is populated but `deviate yellow pre` showed an empty `proposed_changes`, the working tree was already clean before YELLOW ran; the post-script's `git restore .` is a no-op and there is nothing to commit or revert.

### Verdict says ACCEPTED for some files, REJECTED for others

YELLOW does not support partial amendments — the edge-case table (`src/deviate/prompts/commands/deviate-yellow.md` edge_case_handling) treats a mixed verdict as a whole-proposal FAILURE. Either accept all proposed changes (`--approved`) or revert all of them (`--rejected`). If only a subset is genuinely justified, return to `/deviate-green` and rewrite the GREEN rationale to single out the files GREEN must modify to pass; YELLOW will re-evaluate the scoped proposal on the next loop.

### `--approved` ran but `current_phase` is still `GREEN`

The post-script's force-transition writes `.deviate/session.json` after committing (`src/deviate/cli/micro.py:2805-2807`). If the file shows `GREEN` afterwards, the `force_transition_to("JUDGE")` call ran against a `SessionState` object that loaded a stale snapshot. Inspect for the typical concurrency hazard — another shell wrote to `session.json` between the pre-script and the post-script:

```bash
# Stale-write diagnostic
ls -la .deviate/session.json
git log --oneline .deviate/session.json | head -3
```

Fix by re-running `deviate yellow post --approved` from inside the original worktree; do not edit `.deviate/session.json` by hand — the schema versions tightly with `SessionState` (`src/deviate/state/session.py`).

### `--rejected` ran but `git status` still shows modified files

The post-script runs `git restore .` without `check=True` (`src/deviate/cli/micro.py:2810`), so a non-zero git exit (e.g., a hook failure, a locked index) does not raise. Verify manually:

```bash
git restore .
git status --porcelain    # must be empty
```

If files persist, the proposal modified files outside the active worktree (e.g., a worktree-bound symlink) or `git restore` refused due to an unmerged path. Resolve the conflict manually (`git checkout -- <path>` after confirming the GREEN-side diff is the one to keep) and re-run `/deviate-green`. Do not re-run `deviate yellow post --rejected` over a manually resolved tree — the YELLOW_APPROVED/YELLOW_REJECTED ledger append will double-fire.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — the predecessor how-to that walks the full `red → green → [yellow?] → judge → refactor` cycle for a `PENDING` task.
- [Run the /deviate-tasks phase](/how-to/tasks) — the upstream how-to that produces the `tasks.jsonl` rows YELLOW reads; if you reached YELLOW without a tasks file, start here.
- [Reference: Slash Commands](/reference/slash-commands) — inventory entry for `deviate-yellow` (version `1.0.0`, aliases `yellow`, `/spec.tdd.yellow`, `/yellow`, `/tdd.yellow`) and the flag surface for `deviate yellow pre` (`--task`) and `deviate yellow post` (`--approved`, `--rejected`).
