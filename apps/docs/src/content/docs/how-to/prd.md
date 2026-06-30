---
title: "Run the /deviate-prd phase"
description: "Compile explore.md, design.md, and data-model.md into prd.md — the singular source of truth for downstream sharding into specs/issues.jsonl."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
  - ISS-ADH-011
---

# Run the /deviate-prd phase

This how-to covers `/deviate-prd` — the third phase of the macro layer that compiles the upstream exploration and research artifacts (`explore.md`, `design.md`, `data-model.md`) into a single, deeply coherent Product Requirements Document (`prd.md`). The PRD is the **singular source of truth** for the next phase, [`/deviate-shard`](/how-to/shard), which decomposes it into vertical-slice issues registered in the append-only ledger at `specs/issues.jsonl`. PRD enforces the **Ambiguity Interrogation** halt gate: if the upstream research left any architectural parameters unresolved, the slash command halts with `AMBIGUITY_INTERROGATION` rather than emitting a brittle spec — you fix the research first, then re-run. PRD is also the last gatekeeper before downstream sharding and HITL Gate 2, so every Functional Requirement (`FR-NNN`) and Gherkin Acceptance Criterion (`AC-NNN`) token must be unambiguous and sharding-ready.

## Prerequisites

- **`/deviate-research` completed and committed** for the same epic — the PRD phase reads `design.md` and `data-model.md` from the numbered epic bucket at `specs/NNN-<slug>/`. If either is missing, `deviate prd pre` halts with `PRD: missing upstream artifacts`. If those files are uncommitted, the working-tree check inside the pre-script will fail.
- **HITL Gate 1 passed** — `design.md`'s `## Pending HITL Decisions` table must have **zero** rows with `Status: PENDING`. The pre-script scans the table line-by-line (`src/deviate/cli/macro.py::_check_pending_hitl_decisions`) and halts with `PRD: HITL Gate 1 not passed — pending decisions exist` if any row is still open. This is a non-bypassable gate; if you have not yet resolved every PENDING decision, finish the [`/deviate-research`](/how-to/research) review first.
- **`specs/constitution.md` present** — the constitutional pre-flight extracts the tech-stack standards, testing protocols, and architectural principles before PRD generation. The PRD must respect every active clause; a constitutional violation surfaced here means the upstream research was misaligned and should be re-run, not papered over.
- **Clean working tree on the active feature branch** — the pre-script validates upstream artifacts and the post-script will commit a fresh `prd.md`; uncommitted edits to `design.md` or `data-model.md` will block the run.
- **A reasoning model available for the orchestrating agent** — the macro layer routes PRD to the high-cost tier (Qwen 3.7+ Thinking or V4 Pro per `specs/DeviaTDD-architecture.md` §4 and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].prd`.
- **The same problem statement used for explore and research** — keep the original `<user_input>` anchored through to PRD generation so the requirements stay aligned with the question that drove exploration.

## Steps

### 1. Confirm research artifacts are committed and Gate 1 is satisfied

Before invoking the slash command, verify the upstream state. The pre-script returns `PRD: missing upstream artifacts` if either file is absent, and `PRD: HITL Gate 1 not passed — pending decisions exist` if any HITL row is still open. Catching these before the slash command runs gives you a clearer error than the post-script halt chain.

```bash
# Find the active epic bucket
ls -dt specs/NNN-*/ 2>/dev/null | head -1

# Both research artifacts must exist and be committed
test -f specs/NNN-<slug>/design.md && echo "design.md OK"
test -f specs/NNN-<slug>/data-model.md && echo "data-model.md OK"
git status specs/NNN-<slug>/

# Zero PENDING rows in design.md's HITL table
grep -c "| PENDING |" specs/NNN-<slug>/design.md    # must print 0
```

If `grep -c` prints anything other than `0`, open `design.md`, find rows whose `Status:` is `PENDING`, resolve each one (either change `Status` to `RESOLVED` with a note, or amend the design), then re-check.

### 2. Run `/deviate-prd` with the same problem statement

The slash command is the single primary action for this how-to. Pass the same problem statement you used for `/deviate-explore` and `/deviate-research` so the PRD generation stays anchored to the same question. If you know the epic slug, pass `--epic` to skip auto-discovery.

```bash
/deviate-prd <your-problem-statement>

# or, with an explicit epic slug:
/deviate-prd --epic "<NNN-<slug>>" <your-problem-statement>
```

The slash command orchestrates six sub-steps internally: the pre-script (step 3), the constitutional pre-flight + upstream artifact analysis (step 4), the PRD generation (step 5), the manifest writing (step 6), and the post-script commit (step 7). You do not invoke any of them directly.

### 3. Wait for the pre-script to validate and emit a contract

The slash command invokes `deviate prd pre` first. The pre-script discovers the latest numbered epic bucket under `specs/`, validates that both `design.md` and `data-model.md` exist inside that bucket, scans `design.md` for any PENDING HITL decisions, transitions the session from `RESEARCH` to `PRD`, and emits a JSON contract on stdout (`src/deviate/cli/macro.py::prd_pre`).

The contract contains `repo_root`, `git_branch`, `session_path`, `current_phase`, `timestamp`, `epic_slug`, `feature_bucket`, `design_path`, `data_model_path`, `plan_target` (absolute path to `.deviate/artifacts/manifest_prd.json`), and `issue_id`. The orchestrator threads these into the PRD-generation prompt.

If the pre-script halts with `PRD: no epic discovered`, no numbered epic bucket exists under `specs/` — confirm you ran `/deviate-research` and that it produced the `specs/NNN-<slug>/` directory. If it halts with `PRD: missing upstream artifacts`, the pre-script prints the absolute paths it expected. If it halts with `PRD: HITL Gate 1 not passed`, the listed decision IDs are unresolved — return to step 1.

### 4. Wait for the constitutional pre-flight and upstream artifact analysis

The orchestrator reads three things from the pre-script contract and the filesystem:

1. **Constitution** (`constitution_path`) — tech-stack standards, testing protocols, architectural principles, performance and security constraints. The PRD must respect every active clause.
2. **Explore brief** (`explore_md_path` from research) — the empirical context that drove the discovery phase.
3. **Research artifacts** (`design_path`, `data_model_path`) — the architectural design, options matrix, risk register, entity definitions, schema tables, and state transitions.

If any of these is missing, empty, or fails to parse, the orchestrator surfaces the failure verbatim. There is no silent fallback — PRD is the *compilation* phase, not a research rediscovery phase. If research was thin, fix it; do not let PRD paper over gaps.

### 5. Wait for the PRD generation

The orchestrator writes the PRD content to `prd_path` (absolute path from the contract) following the `<output_format_schemas>` block shipped in `src/deviate/prompts/commands/deviate-prd.md`. Two non-negotiable structural rules:

- Every Functional Requirement carries a unique sequential `FR-NNN` token (e.g. `FR-001`, `FR-002`).
- Every Acceptance Criterion carries an `AC-NNN-NN` token and uses strict Gherkin syntax — `Given` / `When` / `Then` triples only. The post-script calls `validate_gherkin_syntax()` (`src/deviate/core/validation.py::73`) and halts with `PRD: invalid Gherkin syntax: …` if any block fails.

The PRD also produces an `## Issue Sharding Strategy` section that pre-declares the vertical-slice topology — every FR maps to at least one shard, every AC co-locates with its parent FR, and enabling shards (tooling, infrastructure, refactors) may carry zero FRs.

This step can take several minutes on the high-cost tier model. Let it run; do not interrupt the orchestrator mid-generation.

### 6. Wait for the manifest writing

After PRD generation, the orchestrator writes an execution manifest to `plan_target` (absolute path from the contract, typically `.deviate/artifacts/manifest_prd.json`). The manifest's required fields — `epic_slug` and `prd_requirements` (the list of `FR-NNN` tokens that must appear in `prd.md`) — are non-empty; the post-script halts with `PRD: manifest missing 'epic_slug'` if either is missing.

```json
{
  "task_id": "prd",
  "epic_slug": "<NNN-<slug>>",
  "prd_requirements": ["FR-001", "FR-002", "FR-003"],
  "files_modified": [
    {
      "path": "<feature_dir>/prd.md",
      "action": "created",
      "purpose": "Product Requirements Document for feature epic"
    }
  ],
  "commit_subject": "docs(<epic_num>): create prd.md",
  "validation": { "lint": "SKIP", "typecheck": "SKIP", "tests": "SKIP", "summary": "PRD document generated" }
}
```

### 7. Handle an AMBIGUITY_INTERROGATION block (if surfaced)

If the orchestrator cannot resolve hidden assumptions, missing technical schemas, unstated edge-case bounds, or protocol gaps from the upstream research, it halts the primary execution pipeline and emits **only** three blocks: `## Decision Readiness`, `## Clarification Log`, and `# SESSION_STATE`. The post-script is **skipped** — no commit happens.

This is the **Ambiguity Interrogation** halt gate, distinct from HITL Gate 1. Gate 1 catches unresolved HITL decisions in `design.md`; Ambiguity Interrogation catches new ambiguities the PRD compiler discovers when it tries to write the requirements. If you see this block, do not run the post-script manually. Pick one of three actions:

- **Amend the research artifacts** (preferred) — edit `design.md` or `data-model.md` to close the gap, commit, then re-run `/deviate-prd`.
- **Add a `RESOLVED-Q-NNN` row** to the `## Ambiguity Resolution and Stakeholder Decisions` table in `prd.md` directly, then run the post-script with `--force` (not recommended — bypasses the constitutional pre-flight).
- **Re-run `/deviate-research`** with a tighter problem statement that does not push against the gap.

### 8. Wait for the post-script to commit

The slash command invokes `deviate prd post <plan_target>` (`src/deviate/cli/macro.py::prd_post`) which:

1. Loads the manifest and validates `epic_slug` is non-empty.
2. Validates `prd.md` exists at `<specs_root>/<epic_slug>/prd.md` and is non-empty.
3. Validates required sections per `ARTIFACT_VALIDATORS["prd"]` (`Document Control and Metadata`, `System Objectives and Scope Boundary`, `Architectural Constraints and Prerequisites`, `Functional Flow and Sequence Architecture`, `Functional Requirements and Epics`, `Issue Sharding Strategy`).
4. Validates Gherkin syntax; halts with `PRD: invalid Gherkin syntax: …` on failure.
5. Cross-checks that every `FR-NNN` listed in `manifest.prd_requirements` appears in `prd.md`; warns on missing (does not halt).
6. Runs pre-commit hooks (which include the full test suite — **allocate at least 180s / 3 minutes** for this step).
7. Stages and commits `prd.md` with message `docs(<epic_num>): create prd.md`.
8. Saves the session in `PRD` phase.

If the post-script exits with `status: FAILURE`, surface the `reason` verbatim — the post-script is mechanical and reports exactly which check failed.

### 9. Verify the PRD, the manifest, and the commit

Confirm everything landed. The PRD must exist at the epic bucket, the manifest must be readable, the commit must include the file, and the session must have advanced.

```bash
# Latest commit must include prd.md
git log --oneline -1
git show HEAD --stat | grep "prd.md"

# PRD file is readable and has the required sections
test -f specs/NNN-<slug>/prd.md && echo "prd.md OK"
grep -E "^# (Document Control and Metadata|System Objectives and Scope Boundary|Architectural Constraints and Prerequisites|Functional Flow and Sequence Architecture|Functional Requirements and Epics|Issue Sharding Strategy)" specs/NNN-<slug>/prd.md

# Manifest is readable and has the required fields
test -f .deviate/artifacts/manifest_prd.json && echo "manifest OK"
cat .deviate/artifacts/manifest_prd.json | python -c "import json,sys; m=json.load(sys.stdin); print('epic_slug:', m['epic_slug']); print('FRs:', m['prd_requirements'])"

# Every FR in the manifest appears in prd.md
for fr in $(python -c "import json; print(' '.join(json.load(open('.deviate/artifacts/manifest_prd.json'))['prd_requirements']))"); do
  grep -q "$fr" specs/NNN-<slug>/prd.md && echo "$fr OK" || echo "$fr MISSING"
done

# Session advanced to PRD
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

Expected session phase: `PRD`. The next phase (`SHARD`) is unlocked but does not auto-run — it waits for you to call `/deviate-shard` explicitly.

## Troubleshooting

### Pre-script halts with `HITL GATE 1 — UNRESOLVED DECISIONS`

`design.md` still has one or more rows in `## Pending HITL Decisions` with `Status: PENDING`. The pre-script lists the decision IDs it found. Re-open `design.md`, find those rows, and either change `Status` to `RESOLVED` (with a note in the `Recommended Resolution` column) or amend the design to remove the row. The gate rule is: **zero** PENDING rows in the table before `/deviate-prd` will run. Never bypass with `--force` — Gate 1 exists to catch design errors before they cascade into PRD, shard, plan, tasks, and 25+ Micro cycles.

### Pre-script halts with `PRD: no epic discovered`

`deviate prd pre` lists `specs/` and finds no `NNN-<slug>/` directory. Confirm you ran `/deviate-research` (which allocates the bucket) and that the directory was not deleted or moved. If you intend to skip research and emit an ad-hoc PRD instead, use [`/deviate-adhoc`](/how-to/adhoc) — it does not require a numbered epic bucket.

### Pre-script halts with `PRD: missing upstream artifacts`

The pre-script found the epic bucket but `design.md` and/or `data-model.md` is absent inside it. Re-run `/deviate-research`; PRD has no fallback if the architectural artifacts are missing. The pre-script prints the absolute paths it expected — diff them against your filesystem to find the missing file.

### AMBIGUITY_INTERROGATION block in the orchestrator output

The PRD compiler discovered hidden assumptions, missing technical schemas, or protocol gaps that the upstream research did not close. The orchestrator emitted `## Decision Readiness`, `## Clarification Log`, and `# SESSION_STATE` only — no `## Functional Requirements and Epics` block, no post-script call, no commit. Do **not** invoke `deviate prd post` manually; the manifest was never written and the post-script would halt with `PRD: manifest missing 'epic_slug'`. Instead, return to step 7: amend `design.md` / `data-model.md`, commit, then re-run `/deviate-prd`.

### Post-script halts with `PRD: invalid Gherkin syntax: …`

The PRD generation produced an Acceptance Criterion that does not match strict Gherkin `Given` / `When` / `Then` triples (`src/deviate/core/validation.py::validate_gherkin_syntax`). The post-script prints the offending errors. The fix is to edit `prd.md` so every `AC-NNN-NN` block has all three clauses (`Given`, `When`, `Then`) verbatim — common pitfalls are `And` chains without a preceding `Given`, missing `Then` assertions, or prose without the keyword markers. After editing, re-run `deviate prd post .deviate/artifacts/manifest_prd.json`.

### Post-script warns `PRD_WARNING missing requirements in prd.md: [...]`

The post-script cross-checked `manifest.prd_requirements` against the FR tokens in `prd.md` and found that one or more declared FRs are missing from the body. This is a **warning**, not a halt — the commit will proceed, but the manifest and the PRD are out of sync. Either (a) regenerate `prd.md` so all `FR-NNN` tokens from the manifest appear, or (b) regenerate the manifest to match the FRs the PRD actually contains. Do not let this drift; downstream `/deviate-shard` reads `prd_requirements` from the manifest to know which slices to emit.

### Post-script times out or fails during pre-commit hooks

The post-script runs pre-commit hooks including the full test suite (`mise run test` or whatever the constitution mandates). On large repos or slow CI, this can exceed 3 minutes. Allocate at least 180s for the post-script invocation; if it still times out, run `mise run test` in isolation to diagnose the underlying failure. If the commit is partial, restore the working tree (`git checkout -- specs/NNN-<slug>/prd.md`) and re-run the post-script once the test failure is fixed.

### Session did not advance to `PRD`

The session in `.deviate/session.json` should report `current_phase: PRD` after a successful post-script. If it still reads `RESEARCH`, the post-script failed silently or you ran the slash command in an agent session that bypassed the session state machine. Re-run `deviate prd post .deviate/artifacts/manifest_prd.json` directly to drive the state machine forward.

## Next Steps

- [How to run /deviate-shard](/how-to/shard) — the next macro phase; consumes `prd.md` and decomposes it into vertical-slice issue files registered in `specs/issues.jsonl`. Gates on the PRD passing all required sections and a clean Gherkin parse.
- [How to run /deviate-research](/how-to/research) — the prerequisite phase; PRD will halt with `PRD: HITL Gate 1 not passed` until every PENDING HITL decision in `design.md` is RESOLVED.
- [How to run /deviate-explore](/how-to/explore) — the phase before research; PRD reads `explore.md` as empirical context.
- [Reference: `deviate prd pre` / `deviate prd post`](/reference/cli) — the CLI surface for the pre/post scripts; flag tables (`--epic`, `--dry-run`, `--force`), exit-code semantics, and the manifest schema.
- Reference: PRD required sections — the `ARTIFACT_VALIDATORS["prd"]` list and the Gherkin validator rule set that the post-script enforces.
- [Reference: HITL Gate 1 triggers](/reference/hitl-gates#gate-1) — the exact conditions that cause Gate 1 to halt the PRD phase.
- [Explanation: HITL Gate 1](/explanation/hitl-gates) — why the design review gate exists, what it prevents, and how it interacts with the PRD compiler's Ambiguity Interrogation halt.
- [Explanation: append-only ledger discipline](/explanation/append-only-ledger) — why `specs/issues.jsonl` is append-only and how the PRD commit fits into the broader ledger invariants.