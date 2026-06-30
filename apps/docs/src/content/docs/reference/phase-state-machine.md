---
title: "Phase State Machine"
description: "The 16 valid SessionState.current_phase values, the per-phase artifact map, and the SessionState model fields that gate phase transitions."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-003
---

# Phase State Machine

The set of 16 valid `SessionState.current_phase` values, the artifacts each phase requires on disk, and the `SessionState` model fields that gate transitions. Source of truth: `src/deviate/state/config.py`.

## Valid Phases

The 16 strings accepted by `SessionState.current_phase`, enforced by the `_validate_phase` field validator (`src/deviate/state/config.py:205`). Any other value raises `ValueError` with the message `Invalid phase '<v>'. Must be one of: <sorted list>`.

| Phase | Purpose |
|---|---|
| `IDLE` | Default session state; no active workflow |
| `EXPLORE` | Macro — read-only structural codebase scan |
| `RESEARCH` | Macro — architectural analysis producing `design.md` and `data-model.md` |
| `PRD` | Macro — Product Requirements Document compilation |
| `SHARD` | Macro — decompose PRD into issue ledger entries |
| `SPECIFY` | Meso — finalize spec-enriched issue (HITL Gate 2 surface) |
| `PLAN` | Meso — per-issue localized research and plan authoring |
| `TASKS` | Meso — decompose spec into autonomous TDD task units |
| `RED` | Micro — write failing tests |
| `GREEN` | Micro — minimal implementation to pass tests |
| `YELLOW` | Micro — evaluate proposed test amendments |
| `JUDGE` | Micro — review GREEN against spec; emit `COMPLIANCE_PASS` |
| `REFACTOR` | Micro — behavior-preserving structural improvement |
| `E2E` | Micro — final end-to-end verification |
| `EXECUTE` | Micro — direct task execution (no TDD cycle) for low-complexity tasks |
| `HOTFIX` | Micro — decompose bug reports into autonomous hotfix units |

## Phase Artifact Map

`_PHASE_ARTIFACT_MAP` (`src/deviate/state/config.py:47`) declares the artifacts expected to exist on disk before a phase is considered valid. `validate_filesystem_state` walks the map and returns the list of missing paths. Phases not listed have no artifact precondition.

| Phase | Required artifact(s) |
|---|---|
| `RESEARCH` | `explore.md` |
| `PRD` | `design.md`, `data-model.md` |
| `SHARD` | `prd.md` |
| `SPECIFY` | `spec.md` |
| `PLAN` | `plan.md` |
| `TASKS` | `spec.md`, `tasks.md` |

Artifact paths resolve under `<repo_path>/specs/<epic_slug>/<artifact>` when `epic_slug` is supplied, or `<repo_path>/<artifact>` otherwise (`src/deviate/state/config.py:73-77`).

## SessionState Model

The `SessionState` Pydantic model is the runtime representation of one DeviaTDD session. Defined at `src/deviate/state/config.py:195`.

| Field | Type | Default | Description |
|---|---|---|---|
| `current_phase` | `enum` (16 values) | `"IDLE"` | Active workflow phase; validated against `_VALID_PHASES` |
| `active_issue_id` | `string` | `null` | Identifier of the in-flight issue from `specs/issues.jsonl` |
| `last_command` | `string` | `""` | Last slash command invoked in the session |
| `yellow_triggered` | `bool` | `false` | Whether YELLOW amended a prior test in the current loop |
| `train_feedback` | `string` | `""` | Coach feedback carried forward from REFACTOR |
| `judge_rejected` | `bool` | `false` | Whether JUDGE failed and forced a redo loop |
| `red_commit_sha` | `string` | `""` | Commit SHA captured at RED for tamper-guard rollback |
| `timestamp` | `datetime` | `datetime.now(timezone.utc)` | Last-mutation timestamp in UTC |

## Transitions

| Method | Behavior |
|---|---|
| `transition_to(phase)` | Returns new `SessionState` with `current_phase=phase`; resets `yellow_triggered` and `judge_rejected` to `false`; preserves `active_issue_id`, `last_command`, `train_feedback`, `red_commit_sha`; stamps new `timestamp` |
| `force_transition_to(phase)` | Returns new `SessionState` with `current_phase=phase`; preserves all fields including `yellow_triggered` and `judge_rejected`; used for resume / replay; stamps new `timestamp` |
| `_validate_phase(v)` | Field validator; rejects any string outside `_VALID_PHASES` with `ValueError` |
| `save(path)` | Writes JSON via `model_dump_json(indent=2)`; creates parent directories as needed |
| `load(path)` | Classmethod; reads JSON from `path`; returns `SessionState()` defaults if the file is absent |
| `validate_filesystem_state(phase, epic_slug, repo_path)` | Static method; delegates to module-level `validate_filesystem_state`; returns list of missing artifact paths |
| `reconstruct_from_worktree(worktree)` | Static method; delegates to module-level `reconstruct_from_worktree`; rebuilds `current_phase` from worktree markers |

## Source-of-Truth

| Attribute | Location |
|---|---|
| Valid-phase frozenset | `src/deviate/state/config.py::_VALID_PHASES` (lines 26-45) |
| Artifact map | `src/deviate/state/config.py::_PHASE_ARTIFACT_MAP` (lines 47-54) |
| Phase validator | `src/deviate/state/config.py::SessionState._validate_phase` |
| Filesystem validator | `src/deviate/state/config.py::validate_filesystem_state` |
| Worktree reconstructor | `src/deviate/state/config.py::reconstruct_from_worktree` |
| Transition method | `src/deviate/state/config.py::SessionState.transition_to` |
| Forced transition | `src/deviate/state/config.py::SessionState.force_transition_to` |
| Persistence | `src/deviate/state/config.py::SessionState.save` / `SessionState.load` |

## See Also

- [Slash Commands](/reference/slash-commands) — which slash command drives each phase
- [Macro Run Pipeline](/reference/macro-run) — sequential invocation of macro phases (`EXPLORE → RESEARCH → PRD → SHARD`)
- [Inspect Issues](/reference/inspect-issues) — query the issue ledger that the meso and micro phases feed
- [How-To intro](/how-to/intro) — operator-task quadrant; each phase has a dedicated how-to (e.g., `red`, `green`, `plan`)
- [Explanation intro](/explanation/intro) — rationale and design choices quadrant
- [Tutorials intro](/tutorials/intro) — guided-learning quadrant
- [Reference intro](/reference/intro) — quadrant index
