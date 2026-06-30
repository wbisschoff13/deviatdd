---
title: "Run the /deviate-judge phase"
description: "Run the V4-Pro isolated JUDGE phase to evaluate the GREEN implementation against spec.md for correctness, completeness, and integrity; emit COMPLIANCE_PASS or COMPLIANCE_VIOLATION."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Run the /deviate-judge phase

This how-to covers `/deviate-judge` — the **JUDGE / TRAIN** phase of the micro layer. The slash command (`src/deviate/prompts/commands/deviate-judge.md`, registered as the `judge` Typer sub-app at `src/deviate/cli/__init__.py:787`) runs in an **isolated V4-Pro session** with no shared history from RED or GREEN and evaluates the GREEN commit against `spec.md` for correctness, completeness, and integrity only. It emits exactly one structured YAML verdict: `COMPLIANCE_PASS` (pipeline proceeds to REFACTOR) or `COMPLIANCE_VIOLATION` (implementation is rolled back, verdict is appended to `tasks.md`, and the structured `train_feedback` trains the next GREEN attempt). REFACTOR opportunities are explicitly out of scope for JUDGE — they surface as informational `REFACTOR NOTE:` entries in `train_feedback` on a passing verdict only.

The slash command is the standalone form. In the normal micro-cycle flow, `_run_judge_phase` (`src/deviate/cli/micro.py:1275`) is invoked automatically by `deviate run` between GREEN and REFACTOR; you reach this how-to when you want to re-run the phase standalone (after a manual rollback, to audit a hotfix, or when triaging a `JUDGE_AGENT_NO_FEEDBACK` failure). For the end-to-end dispatcher that wraps this phase, see [Run a task via the micro dispatcher](/how-to/run).

## Prerequisites

- **DeviaTDD workspace bootstrapped** — `deviate setup` has run, so `/deviate-judge` is in the agent prompt palette and `.deviate/config.toml` exists. If not, see [Bootstrap a DeviaTDD workspace](/how-to/setup).
- **GREEN has committed** — the task under evaluation must be in `GREEN` state on the active feature branch. JUDGE reads the diff from `red_commit_sha` (or the current HEAD if no RED exists for this session) up to HEAD (`_run_judge_phase`, `src/deviate/cli/micro.py:1291-1309`). A task that has not yet landed its GREEN commit produces a `NO_DIFF` verdict and is treated as PASS with that note — re-run only after the GREEN commit lands.
- **`spec.md` is present at the active feature path** — `{repo_root}/specs/{issue_epic}/{feature_slug}/spec.md` (resolved via `_resolve_spec_md` in the orchestrator). A missing `spec.md` triggers a FAILURE verdict with category `Spec Non-Compliance` and the note `SPEC_NOT_FOUND`; the slash command cannot evaluate requirements it cannot read.
- **V4-Pro model available for the JUDGE phase** — `.deviate/config.toml` resolves the `JUDGE` phase via `resolve_model_for_phase` (`src/deviate/state/config.py:137`). The default tier for JUDGE is V4 Pro (cached/compliance); per-phase overrides go under `[models].judge`. Confirm the backend is reachable; an unreachable model produces `JUDGE_AGENT_NO_FEEDBACK` for a `COMPLIANCE_VIOLATION` with no actionable rationale.
- **Clean `.deviate/session.json`** — the phase sets `session.force_transition_to("JUDGE")` before invoking the agent and writes `session.judge_rejected` and `session.train_feedback` on exit (`src/deviate/cli/micro.py:1491-1495`). An active session in a phase other than GREEN or IDLE that follows a previous JUDGE will abort.
- **Slash-command-capable agent** — Pi, OpenCode, Claude, or Factory running against the project root with the `/deviate-judge` slash installed at `.<agent>/commands/deviate-judge.md` by `deviate setup`.

## Steps

### 1. Confirm GREEN is the latest commit on the feature branch

JUDGE inspects the diff against the recorded `red_commit_sha`. If the branch has rolled past GREEN, the verdict will evaluate the wrong surface. Verify the working tree is clean and HEAD is the GREEN commit for the active task:

```bash
# HEAD must be the GREEN commit for the task under review
git log --oneline -3
git show HEAD --stat | head -20

# Session phase should be GREEN (post-GREEN, pre-JUDGE) or IDLE (re-evaluation)
jq '.current_phase, .active_issue_id' .deviate/session.json
```

If `current_phase` is `RED`, GREEN has not committed yet — re-run GREEN first via `deviate run TSK-NNN-NN` rather than invoking `/deviate-judge` standalone.

### 2. Invoke `/deviate-judge`

Run the slash command in the agent chat. Pass the task ID, issue ID, and repo root so the JUDGE prompt can locate `spec.md` and the append-only ledger:

```bash
/deviate-judge TSK-001-01 ISS-001-004 /path/to/repo
```

The slash command assembles the prompt from `core/core.md`, `core/micro-auto.md`, and `auto/judge.md` via `load_template` (`src/deviate/prompts/assembly.py:48`), appends the structured diff against `red_commit_sha`, and runs the JUDGE model in an isolated session. You do not invoke `deviate judge pre` or `deviate judge post` directly — the skill orchestrates both. The slash command emits a single YAML verdict block on stdout and nothing else.

### 3. Inspect the YAML verdict block

The slash command emits exactly one structured block per `<output_format_schemas>` in the JUDGE prompt (`src/deviate/prompts/commands/deviate-judge.md:138-153`). Three outcomes:

```yaml
phase: JUDGE
status: PASS
task_id: "TSK-001-01"
verdict: "COMPLIANCE_PASS"
rationale: "Implementation correctly satisfies all FR-NN / AC-NN requirements; tests validate the spec; no security, governance, tamper, or flow issues."
violations: []
train_feedback: |
  Optional: REFACTOR NOTE: <observation about refactoring opportunity>. Not blocking.
```

A `COMPLIANCE_VIOLATION` block carries a populated `train_feedback` string and a `violations[]` list (each entry: `category`, `file`, `detail`, `severity`, `requirement`, `recommendation`). The `_append_judge_feedback` helper (`src/deviate/cli/micro.py:1093`) injects this feedback under the matching `### TSK-NNN-NN` heading in `tasks.md` so the next GREEN attempt reads it as task context.

### 4. On PASS — proceed to REFACTOR or the next task

A passing verdict means the pipeline is unblocked. The session moves to `REFACTOR` (or `IDLE` if the profile is `fast` or `--no-refactor`). Continue with the micro dispatcher:

```bash
# Continue the cycle on this task (defaults to REFACTOR after a JUDGE PASS)
deviate run TSK-001-01

# Or pick up the next PENDING task for the active issue
deviate run
```

A `REFACTOR NOTE:` line in `train_feedback` is informational only — it does not block the pass and does not trigger a re-run. Surface it to the next REFACTOR phase if structural cleanup is in scope.

### 5. On FAILURE — let the orchestrator roll back and train

If you ran JUDGE standalone and got a `COMPLIANCE_VIOLATION`, you must roll back manually and re-arm GREEN with the feedback. The standalone slash command does not perform the orchestrator's automatic `git reset --hard HEAD~1` (preserving the RED test) that the in-cycle `_run_judge_phase` does at `src/deviate/cli/micro.py:2048-2053`:

```bash
# Roll back the GREEN commit, preserving RED
git reset --hard HEAD~1

# Confirm RED tests still fail on the parent commit
git log --oneline -3
mise run test 2>&1 | tail -20   # expected: RED test still failing

# Append judge feedback to tasks.md (the slash command writes this; verify it landed)
grep -A 6 "### TSK-001-01" specs/001-<epic>/issues/ISS-001-004-<slug>/tasks.md | tail -20

# Re-run GREEN with the feedback injected as task context
deviate run TSK-001-01
```

The orchestrator handles the same sequence automatically when JUDGE is invoked through `deviate run`. Use the manual form only when re-running a phase in isolation.

### 6. Verify the verdict landed and the next phase is reachable

After the slash command returns, confirm the verdict reached the session state, the ledger, and (on PASS) the phase advanced:

```bash
# Session state reflects the verdict
jq '{current_phase, judge_rejected, train_feedback, red_commit_sha}' .deviate/session.json

# Run-log recorded the JUDGE event (when invoked through the dispatcher)
jq -c 'select(.task_id=="TSK-001-01" and .phase=="JUDGE")' .deviate/run.jsonl

# On FAILURE, the feedback block landed in tasks.md
grep -B 1 -A 8 "## Judge Feedback" specs/001-<epic>/issues/ISS-001-004-<slug>/tasks.md

# On PASS, the next dispatcher call advances to REFACTOR (or IDLE for --no-refactor)
deviate run TSK-001-01 --dry-run
```

Expected state on PASS: `current_phase` advances to `REFACTOR`, `judge_rejected: false`, `train_feedback` empty (or containing only a `REFACTOR NOTE:` line). Expected state on FAILURE in standalone mode: GREEN is rolled back, `tasks.md` carries the feedback block, and the next `deviate run TSK-001-01` invokes GREEN with the feedback injected.

## Troubleshooting

### Slash command prints `SKILL_NOT_FOUND deviate-judge`

`deviate setup` did not install the slash into the active agent's command directory. Run `ls .<agent>/commands/` (e.g., `.claude/commands/`, `.opencode/commands/`) and confirm `deviate-judge.md` is present. If it is missing, re-run `mise run setup` (or `deviate setup` directly) to refresh the slash-command library. The skill is also loadable from the package itself — `_load_skill_content("JUDGE")` in `src/deviate/cli/micro.py:2841` falls back to the embedded `src/deviate/prompts/commands/deviate-judge.md` if the per-agent install is absent, so CLI invocations of `deviate judge` still work even without the slash.

### Verdict is `COMPLIANCE_VIOLATION SPEC_NOT_FOUND`

`spec.md` is missing at the expected path. The slash command resolves `{repo_root}/specs/{issue_epic}/{feature_slug}/spec.md` from the task record; a wrong `issue_id` argument (step 2) or a spec that was never written by `/deviate-specify` both land here. Re-run `/deviate-specify <ISSUE_ID>` to regenerate the spec, or pass the correct issue ID to `/deviate-judge`.

### Verdict is `JUDGE_AGENT_NO_FEEDBACK` on a `COMPLIANCE_VIOLATION`

The JUDGE model returned a violation verdict but populated no `rationale`, `train_feedback`, `summary`, or `violations` field (`src/deviate/cli/micro.py:1371-1387`). The orchestrator raises `PhaseFailedError` because there is nothing to train GREEN with. Two common causes: the JUDGE model endpoint rate-limited and returned a partial manifest, or the model is misconfigured to a tier that does not support the JUDGE schema. Confirm `jq '.models.judge // .models.default' .deviate/config.toml` resolves to a V4-Pro backend, then re-run `deviate run TSK-NNN-NN` (which retries the in-cycle JUDGE) or `/deviate-judge` after re-pointing the model.

### Verdict is `COMPLIANCE_VIOLATION Test Integrity Violation` and the diff is test-only

JUDGE treats a diff with no `src/` changes as `SUSPICIOUS` (`src/deviate/prompts/commands/deviate-judge.md:166`). This is the expected outcome when GREEN rewrote a test to weaken an assertion instead of implementing the production code. The `recommendation` field on the violation will name the specific assertion that was relaxed. Roll back GREEN, restore the original assertion from the RED commit, and re-run GREEN with the original spec still binding.

### Standalone `/deviate-judge` PASS but the next `deviate run` re-invokes GREEN instead of REFACTOR

The session phase did not advance — the slash command writes the verdict to stdout but does not mutate `.deviate/session.json` (only the in-cycle `_run_judge_phase` calls `session.force_transition_to("JUDGE")` then on to `REFACTOR` or back to `GREEN`). After a standalone PASS, force the session forward before re-invoking the dispatcher:

```bash
# Manually advance the session past GREEN so the dispatcher does not re-run it
jq '.current_phase = "JUDGE"' .deviate/session.json > .deviate/session.json.new
mv .deviate/session.json.new .deviate/session.json
deviate run TSK-001-01    # now advances to REFACTOR
```

Prefer running JUDGE inside the cycle (`deviate run TSK-001-01` without `--no-judge`) unless you are explicitly re-evaluating after a manual rollback or hotfix.

## Next Steps

- [Run a task via the micro dispatcher](/how-to/run) — the orchestrator that wraps `/deviate-judge` between GREEN and REFACTOR inside the full TDD cycle; the canonical entry point.
- [Reference: Slash Commands](/reference/slash-commands) — the full inventory of `/deviate-*` and `/tome-*` commands, including the JUDGE entry confirming `deviate-judge` 1.1.0 with aliases `/judge` and `/tdd.judge`.
- [Reference: `deviate` CLI flags](/reference/cli) — flags on `deviate run` (`--no-judge`, `--profile fast|secure|full`) that gate when JUDGE runs.
- Why JUDGE runs in an isolated session — design rationale for the no-history V4-Pro evaluation and the COMPLIANCE_PASS / COMPLIANCE_VIOLATION contract.