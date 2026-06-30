---
title: "Run the /deviate-plan phase"
description: "Consume a spec-enriched issue and emit plan.md with strategy, workstation mappings, and risks — the meso-layer bridge between sharding and task decomposition."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
  - ISS-ADH-011
---

# Run the /deviate-plan phase

This how-to covers `/deviate-plan` — the first phase of the meso layer. The slash command consumes a spec-enriched issue file produced by [`/deviate-shard`](/how-to/shard), performs deterministic, lightweight codebase research (L_max ≤ 200ms per workstation file), and emits a planning artifact at `specs/<epic>/issues/<NNN>-<slug>/plan.md` containing an implementation strategy, workstation file mappings, data-flow analysis, risk register, integration points, and a constitutional alignment section. The planning artifact is the contract that the downstream [`/deviate-tasks`](/how-to/tasks) phase decomposes into executable Red→Green→Refactor units.

The slash command runs in two internal sub-steps orchestrated by the agent skill: the pre-script (`deviate plan pre`) either auto-claims a worktree for the next unblocked BACKLOG issue or emits a JSON contract if the agent is already inside a linked worktree, and the post-script (`deviate plan post`) validates `plan.md`, runs pre-commit hooks, commits the artifact, and advances the session to `TASKS`.

## Prerequisites

- **`/deviate-shard` completed** for the epic — one or more spec-enriched issue files must exist under `specs/<epic>/issues/<NNN>-<slug>.md`. Each issue file embeds the spec sections (`[USER_STORIES_LEDGER]`, `[ATDD_ACCEPTANCE_CRITERIA]`, `[EDGE_CASES_AND_BOUNDARIES]`, `[PERFORMANCE_CONSTRAINTS]`, `[SYSTEM_TOPOLOGY_MAPPING]`, `[THE_PROBLEM_CONTRACT]`, `[SCOPE_BOUNDARIES]`, `[UPSTREAM_REQUIREMENT_TRACING]`, `[MULTI_TIERED_VERIFICATION_TARGETS]`) as markdown sections; the plan phase reads those sections verbatim. If issues are missing or any of those sections is absent, run [`/deviate-shard`](/how-to/shard) (and its upstream `/deviate-prd`) first.
- **At least one BACKLOG issue in `specs/issues.jsonl`** — the pre-script auto-discovers the next unblocked `BACKLOG` row and claims it. A `RESEARCH` state in `.deviate/session.json` from a previous run blocks discovery; complete the prior phase or run `deviate inspect` to see the current state. To target a specific issue, pass `--issue <ISS-NNN>` to the slash command.
- **A clean working tree outside any linked worktree** — if `deviate plan pre` runs from the repo root (not a worktree) and the working tree is dirty, the auto-claim step will refuse to create the worktree. Either commit, stash, or reset untracked edits before invoking the slash command.
- **A reasoning model available for the orchestrating agent** — the meso layer routes plan to the cached/compliance tier (V4 Pro per `specs/DeviaTDD-architecture.md` §4 and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].plan`.
- **DeviaTDD workspace bootstrapped** — `deviate setup` has run, so `/deviate-plan` is in the agent prompt palette and `.deviate/config.toml` exists. If you have not done this yet, see [Bootstrap a DeviaTDD workspace](/how-to/setup).

## Steps

### 1. Confirm the spec-enriched issue file exists

Before invoking the slash command, verify that at least one spec-enriched issue has been registered. The pre-script halts with `ISSUE_NOT_FOUND` if the auto-discovery path resolves to a missing file.

```bash
# List issue candidates available for planning
ls specs/<epic>/issues/*.md

# Confirm at least one row in BACKLOG state
grep -E '"status":\s*"BACKLOG"' specs/issues.jsonl

# Sanity-check the required spec sections on the issue you intend to plan
grep -E '^\[(USER_STORIES_LEDGER|ATDD_ACCEPTANCE_CRITERIA|SYSTEM_TOPOLOGY_MAPPING|THE_PROBLEM_CONTRACT|SCOPE_BOUNDARIES|UPSTREAM_REQUIREMENT_TRACING|EDGE_CASES_AND_BOUNDARIES|PERFORMANCE_CONSTRAINTS|MULTI_TIERED_VERIFICATION_TARGETS)\]' \
  specs/<epic>/issues/<NNN>-<slug>.md
```

If no BACKLOG rows exist, halt and run [`/deviate-shard`](/how-to/shard) to populate the ledger. If a row exists but the issue file is missing any of those spec sections, halt with `INCOMPLETE_ISSUE_SPEC` and re-shard the affected slice.

### 2. Run `/deviate-plan`

The slash command is the single primary action for this how-to. Invoke it inside the agent chat. With no argument, the pre-script auto-discovers the next unblocked BACKLOG issue and creates a worktree; pass `--issue <ISS-NNN>` to target a specific issue:

```bash
# Auto-discover the next unblocked BACKLOG issue
/deviate-plan

# Target a specific issue by ID
/deviate-plan --issue ISS-007
```

The slash command orchestrates three sub-steps internally: the pre-script (next step), the agent-driven planning write (steps 4–8), and the post-script (step 9). You do not invoke `deviate plan pre` or `deviate plan post` as a CLI directly — the agent skill does.

### 3. Wait for the pre-script to claim a worktree or emit a contract

The slash command invokes `deviate plan pre` first. The pre-script has two branches:

- **Outside a linked worktree** — discovers the next unblocked BACKLOG issue (or honors `--issue`), calls `_claim_and_setup` to create the worktree at `specs/<bucket>/<slug>/`, copies `.deviate/` into it, and prints the worktree path plus a JSON contract. The agent then `cd`s into the printed worktree and re-issues `/deviate-plan`. The session advances from `RESEARCH → PLAN` on the first invocation; the second invocation lands in "contract mode" because the cwd is now a linked worktree.
- **Inside a linked worktree** — emits a JSON contract on stdout containing `issue_id`, `spec_path`, `plan_target`, `branch_name`, `worktree_full`, `constitution_path`, `constitution_test_command`, `constitution_lint_command`, `timestamp`, `status`, `phase: "plan_pre"`, `force`, and `dry_run`. When the discovered epic directory had workstation mapping data, the contract also includes a `file_structure` map of primary workstation paths.

If the pre-script returns `status: ISSUE_NOT_FOUND` or `NO_ACTIVE_ISSUE`, surface the token verbatim and halt. Common tokens are listed in the **Troubleshooting** section.

### 4. Read the spec-enriched issue file

Parse the JSON contract for `spec_path` (absolute), `plan_target` (absolute), and `issue_id`. Read the file at `spec_path` end-to-end and extract the embedded spec sections that the planning artifact must reference:

- `[SYSTEM_TOPOLOGY_MAPPING]` — workstation file paths and the epic domain this issue belongs to.
- `[THE_PROBLEM_CONTRACT]` — the user/system journey this issue delivers.
- `[SCOPE_BOUNDARIES]` — hard inclusions and defensive exclusions.
- `[UPSTREAM_REQUIREMENT_TRACING]` — FR and AC tokens that anchor user stories to tests.
- `[USER_STORIES_LEDGER]` — US-NNN user stories with FR traceability.
- `[ATDD_ACCEPTANCE_CRITERIA]` — Gherkin scenarios for each user story.
- `[EDGE_CASES_AND_BOUNDARIES]` — edge cases, error states, boundary conditions.
- `[PERFORMANCE_CONSTRAINTS]` — latency, throughput, resource limits.
- `[MULTI_TIERED_VERIFICATION_TARGETS]` — unit and integration test paths.

If a section header exists but the body is empty, the orchestrator proceeds with available sections and writes a `[WARNING]` note inside the plan. If a required section is missing entirely, halt with `INCOMPLETE_ISSUE_SPEC`.

### 5. Run a deterministic codebase state scan (L_max ≤ 200ms)

The planning skill is read-only on the codebase and budgeted for sub-second per-agent scans. Run the following narrow reconnaissance and stop:

```bash
# Recent commit landscape (1 call, ~20 commits)
git log --oneline -20

# Read the append-only ledger for related issues
sed -n '1,80p' specs/issues.jsonl

# Constitution excerpt for architectural invariants
test -f specs/constitution.md && head -200 specs/constitution.md || echo "NO_CONSTITUTION"

# Prior plans / tasks from related issues
ls specs/<epic>/issues/*/plan.md specs/<epic>/issues/*/tasks.md 2>/dev/null || true

# Macro-layer artifacts if present
ls specs/<epic>/design.md specs/<epic>/data-model.md 2>/dev/null || true
```

If the primary workstation file list (from `SYSTEM_TOPOLOGY_MAPPING`) is short — fewer than ~10 files — read each file one at a time with bounded offsets. If the list is long, narrow the scan to the top three by impact and add a `[PERFORMANCE_NOTE]` to the plan; do **not** read every file in the workstation map, the L_max constraint will be violated. Use `libref query <library> <topic>` for any library whose API signature is unclear — this is faster and offline versus a general web search.

### 6. Analyze prior implementations and identify integration points

Two scans inform implementation choices:

- **Prior implementation analysis** — search `specs/issues.jsonl` for rows that share FR tokens with the current issue. Read their `plan.md` (if present) and `tasks.md` (if present) to capture established patterns, naming conventions, or shared helpers. Run `git log --oneline -- specs/<epic>/issues/<NNN>-<prior-slug>/` for any feature branch whose work overlaps the workstation files in step 5. Flag merge-conflict boundaries where the new code touches the same files as in-flight work.
- **Integration point analysis** — for each file listed in `[SYSTEM_TOPOLOGY_MAPPING]`, determine the integration surface (functions, classes, modules the new code will call or be called by). Identify any registration points (DI container, plugin registry, CLI app registration, route table, migration chain) that must be updated. Map the data flow between existing components and the new code, including I/O boundaries and persistence layers.

Write both analyses into the plan body — they are how the downstream `/deviate-tasks` decomposes the issue into vertical slices without losing context.

### 7. Assess risk and constitutional alignment

Before writing the artifact, complete a focused risk sweep:

- **High-risk areas** — existing coupling, performance-sensitive paths (anything matching the issue's `[PERFORMANCE_CONSTRAINTS]`), security boundaries.
- **Test-coverage gaps** — workstation files with no current test file, or with tests touching only the happy path.
- **Defensive exclusions** — surface any `[SCOPE_BOUNDARIES]` clause that is adjacent to the planned change so the plan can re-affirm the exclusion.
- **Scope-vs-budget fit** — if the workstation map plus integration surface implies more than ~6 hours of work, flag the issue for re-sharding rather than expanding the plan.

Then align the planned approach with `specs/constitution.md`:

- **Architecture** — how the change fits the three-layer model (macro / meso / micro) and the existing module boundaries.
- **Testing** — framework, coverage target, and how the issue's `MULTI_TIERED_VERIFICATION_TARGETS` translate to specific test files.
- **Git isolation** — confirms the change is contained to a single feature branch, one issue, no cross-cutting refactors.

If `specs/constitution.md` is missing, write the alignment section as "no constitution found" and call it out in the plan summary; it does not block the plan phase.

### 8. Write `plan.md` to the issue workspace

Write the planning artifact to `plan_target` (the absolute path from the pre-script contract). Use **only** `## Section Name` headers, bullet points, and tables — never wrap the body in code fences or XML tags. The required structure is:

```text
## Plan Summary
- **Issue**: <issue_id> — <issue_title>
- **Implementation Strategy**: <1-2 sentence description of the overall approach>
- **Estimated Complexity**: <Low | Medium | High>
- **Estimated Effort**: <time estimate, e.g., 2-4 hours>

## Workstation Mapping
- **<file_path>**: <role in this issue — what needs to change and why>
  - **Current State**: <brief assessment of the file as-is>
  - **Changes Required**: <specific modifications needed>
  - **Integration Surface**: <interfaces, functions, or classes it connects to>

## Implementation Strategy
- **Phase 1**: <logical implementation phase — deliverable>
  - **Files**: <list of files>
  - **Approach**: <specific implementation approach>
  - **Verification**: <how to verify this phase>

## Data Flow Analysis
- <input → transformation → output → storage trace>

## Risk Assessment
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| <risk description> | <High/Medium/Low> | <High/Medium/Low> | <mitigation strategy> |

## Integration Points
- **<integration point>**: <what connects here and the contract expected>

## Constitutional Alignment
- **Architecture**: <how this aligns with the three-layer architecture>
- **Testing**: <test framework, approach, and coverage considerations>
- **Git Isolation**: <how git isolation invariants apply>
```

All file paths in the artifact MUST be relative to the repository root — do not include absolute paths or `~/` prefixes. If a `[WARNING]` (empty spec section) or `[PERFORMANCE_NOTE]` (scan exceeded 200ms) applies, include it under the relevant section, not as a top-level new section.

### 9. Wait for the post-script to validate and commit

The slash command invokes `deviate plan post` automatically once `plan.md` is on disk. The post-script:

1. Loads the session, asserts `current_phase: PLAN` (or `RESEARCH` if `--force` is set).
2. Resolves `plan_md = <specs_root>/<bucket>/<slug>/plan.md` from the append-only ledger.
3. Halts with `PLAN_NOT_FOUND` if the file is missing, or `PLAN_EMPTY` if the body is empty and `--force` is not set.
4. Commits the file with the conventional message `docs(<epic_num>-<issue_num>): create plan.md` (using `commit_artifact(..., no_verify=True)`).
5. Writes a `PLAN` row to `specs/<epic>/tasks.jsonl` so `/deviate-tasks` can pick up the artifact.
6. Advances the session to `current_phase: TASKS`.
7. Runs the pre-commit hook chain (lint + full test suite) with no-verify skipped on the planning commit itself.

If the post-script returns a failure token, fix the listed field in `plan.md` and re-run `/deviate-plan` — the slash command replays the post-script.

### 10. Verify the artifact is committed and the session advanced

Confirm the post-script landed everything and the session state machine advanced:

```bash
# The plan should be on the feature branch with the conventional commit message
git log --oneline -1
git show --stat HEAD -- specs/<epic>/issues/

# The plan file is non-empty and on disk
test -s specs/<epic>/issues/<NNN>-<slug>/plan.md && echo "plan.md OK"

# A PLAN ledger row was appended for the issue
grep -E '"phase":\s*"PLAN"' specs/<epic>/tasks.jsonl

# The session has advanced to TASKS
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

Expected `current_phase`: `TASKS` — the human does not gate this transition, the artifact landing is the gate.

## Troubleshooting

### Pre-script returns `NO_UNBLOCKED_ISSUES`

The auto-discovery branch in `deviate plan pre` could not find a `BACKLOG` row in `specs/issues.jsonl` whose blockers are all `COMPLETED` (or absent). Common causes: every BACKLOG issue has an unresolved `BLOCKED_BY` reference, or the ledger is empty because `/deviate-shard` has not run.

**Fix**: Run `grep '"status"' specs/issues.jsonl | sort | uniq -c` to inventory the ledger. If there are no `BACKLOG` rows, run [`/deviate-shard`](/how-to/shard) first. If all BACKLOG rows are blocked, complete the upstream issues (or amend the `BLOCKED_BY` chain via a small ledger edit plus a clear commit message), then re-invoke `/deviate-plan`.

### Slash command halts with `INCOMPLETE_ISSUE_SPEC`

The issue file is missing one or more required spec sections (`[USER_STORIES_LEDGER]`, `[ATDD_ACCEPTANCE_CRITERIA]`, plus the other anchors listed in step 4). The plan skill will not proceed without the section anchors because they are what the plan body cites.

**Fix**: Re-run [`/deviate-shard`](/how-to/shard) against the same `prd.md` so the affected issue file is regenerated with the full set of spec sections. If only one slice is missing, you can also re-shard a single slice by re-running `/deviate-shard --slice <NNN>` after amending the PRD; otherwise full re-shard is faster than manual patching.

### Pre-script returns `ISSUE_NOT_FOUND` even though the file exists

The ledger row points to a `source_file` that no longer matches a real file on disk — typically because someone manually moved or renamed an issue file. The pre-script reads the ledger as the source of truth.

**Fix**: Inspect the offending row with `grep <ISS-NNN> specs/issues.jsonl`. If the file moved intentionally, edit the row's `source_file` field to the new relative path. If the file was deleted, the row should be removed or its `status` set to `SUPERSEDED` in a fresh ledger entry. Because `specs/issues.jsonl` is append-only, corrections land as new rows — never rewrite a historical row. Then re-invoke `/deviate-plan --issue <ISS-NNN>`.

### Pre-commit hook fails inside the post-script

`deviate plan post` runs the repo's pre-commit chain (lint + full test suite, allow ≥ 180s). The most common failures are an unrelated test failure or a markdown linter rejecting a table format.

**Fix**: Run `mise run lint` and `mise run test` (or the constitution's equivalent `lint_command` / `test_command`) in isolation to identify the failing hook. For markdown lint complaints on `plan.md`, fix the table formatting (column alignment, empty-row syntax) — do not silence the linter. Once the suite is green, re-invoke `/deviate-plan`; the slash command replays the post-script and commits cleanly.

### Performance scan exceeded the 200ms budget

The workstation map has too many primary files for a single sub-second read pass, or a single file is large enough that reading it inline blows the budget. The skill flags this with a `[PERFORMANCE_NOTE]` and continues, but the plan quality suffers.

**Fix**: Re-run the slash command with a tightened scan. The agent's deterministic scanner caps the workstation map at the top three files by impact; ensure `[SYSTEM_TOPOLOGY_MAPPING]` in the issue file lists impact-ranked workstations (most-changed first). If a single file is dominant, request a follow-up issue that splits the workstation before re-planning.

### A `plan.md` already exists for this issue (re-plan scenario)

The skill reads any prior `plan.md` and incorporates its findings, but it does not delete the old artifact. If the prior plan was committed on the same branch, you will see two planning commits on the feature branch.

**Fix**: This is expected behavior on re-plan. Append a brief change-log section at the bottom of the new `plan.md` (do not modify the original sections) noting what changed since the prior plan, and re-run the slash command. If the old plan must be discarded, do so in a dedicated commit (`docs(plan): supersede prior plan`) — never amend a planning commit that has been pushed.

## Next Steps

- [How to run /deviate-tasks](/how-to/tasks) — the next meso phase; consumes `plan.md` and decomposes it into Red→Green→Refactor units with a fast-lane `mise run` invocation.
- [How to run /deviate-shard](/how-to/shard) — the upstream macro phase that produces the spec-enriched issue file `plan.md` consumes; plan halts with `INCOMPLETE_ISSUE_SPEC` until every required spec section is present.
- [How to run /deviate-prd](/how-to/prd) — the macro phase before shard; PRD content drives the slice boundaries that produce the issue ledger rows.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `deviate-plan`, including its aliases (`plan`, `spec:core:plan`, `spec.core.plan`, `/plan`) and `deviatdd-meso-layer` category.
- Explanation: git isolation invariants — why `deviate plan pre` creates a fresh worktree per issue and what the "no cross-cutting edits" rule protects against (see the explanation quadrant).
- [Explanation: three-layer DeviaTDD architecture](/explanation/three-layer-architecture) — where the meso plan phase sits between the macro (explore→shard) and micro (red→green→refactor) layers, and why plan is the meso entry point.
