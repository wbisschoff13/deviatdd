---
title: "Run the /deviate-shard phase"
description: "Decompose prd.md into self-contained Feature Vertical issues; append to specs/issues.jsonl with a DAG dependency topology."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
---

# Run the /deviate-shard phase

This how-to covers `/deviate-shard` — the final macro-layer phase that decomposes an approved [`prd.md`](/how-to/prd) into self-contained Feature Vertical issue files under `specs/{epic}/issues/`, registers them as `BACKLOG` rows in `specs/issues.jsonl`, and emits the DAG dependency topology that downstream [`/deviate-plan`](/how-to/plan) and [`/deviate-tasks`](/how-to/tasks) consume. After the slash command finishes, the human reviews every sharded issue for completeness, edge cases, and scope correctness — this is the **non-bypassable HITL Gate 2** that catches spec errors at the shard boundary before they cascade into dozens of task implementations.

## Prerequisites

- **`/deviate-prd` completed for the same epic** — `specs/{epic}/prd.md` must exist and contain explicit `FR-{NNN}-{ID}` and `AC-{NNN}-{ID}-{NN}` tokens. The pre-script returns `NO_PRD` if the file is missing and `MALFORMED_PRD_CONTRACT` if the tokens are absent or malformed — the slash command will halt immediately on either condition.
- **HITL Gate 1 already passed** — the design review from `/deviate-research` must be closed (every `## Pending HITL Decisions` row `RESOLVED`). The shard phase consumes the same epic bucket that research allocated; if you skipped research, run it first so the data model and architecture constraints are anchored before sharding.
- **A clean working tree on the active epic branch** — `deviate shard pre` discovers the latest epic bucket under `specs/` and validates the working tree. Uncommitted edits will cause the pre-script to fail.
- **A reasoning model available for the orchestrating agent** — the macro layer routes shard to the high-cost tier (Qwen 3.7+ Thinking or V4 Pro per `specs/DeviaTDD-architecture.md` §3 and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].shard`.
- **The original problem statement threaded through from explore** — the shard phase re-reads `explore.md`, `design.md`, and `data-model.md` for context, so the vertical-slice clusters stay anchored to the same problem space the upstream phases explored.
- **`specs/_product/` (optional)** — when present, the shard phase reads `specs/_product/flows/flows-product.md` (and domain-specific flows) to map each `FR-{NNN}-{ID}` to `FLOW-XX` IDs and emits `flow_refs: [FLOW-XX, ...]` in each shard's frontmatter. Missing `specs/_product/` is a soft gap — shards emit `flow_refs: []` and the manifest logs the gap; the slash command does not halt.

## Steps

### 1. Confirm `prd.md` exists and carries FR/AC tokens

Before invoking the slash command, verify the upstream PRD is in place and structured for deterministic parsing. The pre-script halts with `MALFORMED_PRD_CONTRACT` if the tokens are missing or inconsistent, so a pre-flight check saves a round-trip.

```bash
# Find the latest epic bucket and its PRD
ls -t specs/NNN-*/prd.md | head -1

# Confirm FR-{NNN}-{ID} tokens are present and unique
grep -oE 'FR-[0-9]{3}-[A-Za-z0-9_-]+' specs/NNN-*/prd.md | sort -u

# Confirm AC-{NNN}-{ID}-{NN} tokens are present
grep -oE 'AC-[0-9]{3}-[A-Za-z0-9_-]+-[0-9]{2}' specs/NNN-*/prd.md | sort -u

# Sanity-check the working tree is clean
git status specs/
```

If any FR or AC token is missing, halt and re-run `/deviate-prd` with a tighter contract.

### 2. Run `/deviate-shard` with the same problem statement

The slash command is the single primary action for this how-to. Pass the same problem statement you threaded through `/deviate-explore`, `/deviate-research`, and `/deviate-prd` so the vertical-slice clustering stays anchored.

```bash
/deviate-shard <your-problem-statement>
```

If you know the epic slug, pass it explicitly to skip auto-discovery of the latest bucket:

```bash
/deviate-shard --epic <NNN-slug> <your-problem-statement>
```

The slash command orchestrates five sub-steps internally: the pre-script (next step), the constitutional pre-flight, the PRD read, the vertical-slicing + issue generation pass (step 4), and the post-script (step 7). You do not invoke them directly.

### 3. Wait for the pre-script to emit the JSON contract

The slash command invokes `deviate shard pre` first. The pre-script discovers the latest epic bucket under `specs/`, validates that `prd.md` exists, computes `next_issue_id` from the existing `specs/issues.jsonl` ledger, and emits a JSON contract on stdout.

The contract contains `status`, `phase`, `repo_root`, `git_branch`, `epic_slug`, `epic_id`, `feature_dir`, `prd_path`, `constitution_path`, `issues_dir` (where shard files land), `issues_ledger` (`specs/issues.jsonl`), `next_issue_id` (the next available `ISS-NNN`), `plan_target` (where the execution manifest goes), `dry_run`, and `timestamp`. The orchestrator threads these into the issue-generation pass.

If the pre-script returns `status: NO_EPIC`, no epic slug could be resolved — re-run `/deviate-prd` first. If it returns `NO_PRD`, the PRD file is missing from the discovered bucket. Any other failure is surfaced verbatim; the agent does not proceed.

### 4. Watch the Internal ICoT ledger and the manifest get written

For non-trivial features, the slash command executes an internal four-pass engineering ledger before emitting any file payloads:

- **Pass 1 (Topological Layout)** — groups related `FR-{NNN}-{ID}` tokens into cohesive feature clusters. Each cluster becomes one vertical slice. A slice may contain zero FRs (enabling slices for tooling, infrastructure, or refactoring) or several. The pass verifies cumulative coverage: every FR from the PRD must appear in at least one slice.
- **Pass 2 (Boundary Demarcation)** — establishes hard inclusions and defensive exclusions for every slice so the downstream micro-loop cannot drift into adjacent scope.
- **Pass 2.1 (FR-to-Flow Traceability)** — maps each `FR-{NNN}-{ID}` to one or more `FLOW-XX` IDs read from `specs/_product/flows/flows-product.md` (and domain-specific flows). Each generated shard's frontmatter carries `flow_refs: [FLOW-XX, ...]`. Enabling slices with zero FRs emit `flow_refs: []`.
- **Pass 3 (Horizontal Slice Audit)** — enumerates the layers each slice touches (database, API, business logic, UI). A slice with one or more FRs that touches only one layer is a horizontal slice — flagged `HORIZONTAL_SLICE_DETECTED` and re-clustered with adjacent FRs until it cuts through at least two layers with end-to-end behavior. A "state issue" or "database schema issue" is the named anti-pattern.
- **Pass 4 (Verification Mapping)** — pairs every tracked `AC-{NNN}-{ID}-{NN}` within a slice with an executable `## Demonstration Path` bash block.

After the ledger, the orchestrator writes one shard issue markdown per slice to `<repo_root>/<issues_dir>/<NNN>-<kebab-slug>.md` and writes the execution manifest JSON to `plan_target` (`<repo_root>/.deviate/artifacts/manifest_shard.json`).

### 5. Inspect the manifest before post-script commits

The manifest is the contract between the LLM and the post-script. If `issues` is missing or empty, `deviate shard post` halts with `SHARD_HALTED: manifest missing 'issues' array`. Inspect it before the post-script runs:

```bash
cat .deviate/artifacts/manifest_shard.json | python -m json.tool
```

Each entry in `issues` must be `IssueRecord`-shaped — `issue_id`, `type`, `title`, `source_file`, `blocked_by`, `coordinates_with`, `flow_refs`. The post-script also re-validates that every `source_file` matches `specs/{epic}/issues/<file>.md`; downstream `deviate meso run` relies on this shape to derive the epic bucket and issue slug.

### 6. Resolve HITL Gate 2 — review every shard before the post-script commits

This is the **only** gate that catches spec errors before they cascade into task implementations. The post-script is mechanical and will register every shard listed in the manifest; it does not validate the slices themselves. Walk the `## Issues` directory and review each shard end-to-end:

```bash
ls specs/NNN-*/issues/
```

Pay particular attention to:

- **Vertical slice integrity** — confirm each shard cuts through the layers it claims (database + API + logic + UI where applicable). Reject any shard that is a horizontal layer ("add migration", "add endpoint", "add component").
- **`## Demonstration Path`** — every `AC-{NNN}-{ID}-{NN}` must map to a copy-pasteable bash block. If a shard's demo path is generic or missing, reject and re-cluster.
- **DAG sanity** — the `blocked_by` arrays must form a directed acyclic graph. Sequential dependencies are correct; lateral overlaps belong in `coordinates_with`. If the post-script detects a circular dependency chain, it halts with `TOPOLOGY_LOOP_FAULT`.
- **Coverage check** — every `FR-{NNN}-{ID}` from the PRD must appear in at least one shard's frontmatter. The post-script does not re-run the cumulative coverage check, so do it here.
- **Enabling-slice exemption** — shards with zero FRs (tooling, refactoring) are valid but must still deliver a complete, independently verifiable capability. Reject any "enabling" shard that does not.

If any shard fails review, halt before the post-script runs and either amend the manifest (delete the failing entry, add a corrected one) or re-run `/deviate-shard` with a tighter problem statement.

### 7. Run the post-script to register, stage, and commit

Once every shard has cleared review, run the post-script directly to register issues in the ledger, stage the artifact set, and create the commit. The post-script runs pre-commit hooks — including the full test suite — so allocate a timeout of at least **180 seconds (3 minutes)**:

```bash
deviate shard post .deviate/artifacts/manifest_shard.json
```

The post-script:

1. Reads the manifest, validates that all shard files exist at the expected paths.
2. Registers each shard as `BACKLOG` in `specs/issues.jsonl` via inline `append_issue_record()`. The append is idempotent against `(issue_id, source_file)` — re-running with an unchanged manifest emits `LEDGER_IDEMPOTENT` for each row.
3. Runs pre-commit hooks (full test suite, formatters, linters).
4. Stages `specs/issues.jsonl` + the shard files and creates a single commit `docs({epic_num}): shard issue files and ledger`.
5. Resets the session to `IDLE`.

### 8. Verify the ledger, the commit, and the artifact set

Confirm every piece landed.

```bash
# Latest commit should include both the ledger and the shard files
git log --oneline -1
git show HEAD --stat | grep -E "issues\.jsonl|issues/[0-9]+-.*\.md"

# Every shard from the manifest is registered as BACKLOG
jq -r '.issues[].issue_id' .deviate/artifacts/manifest_shard.json \
  | while read id; do
      grep "\"$id\"" specs/issues.jsonl | tail -1
    done

# No FR token from the PRD was orphaned
grep -oE 'FR-[0-9]{3}-[A-Za-z0-9_-]+' specs/NNN-*/prd.md | sort -u > /tmp/prd_frs.txt
grep -hoE 'FR-[0-9]{3}-[A-Za-z0-9_-]+' specs/NNN-*/issues/*.md | sort -u > /tmp/shard_frs.txt
diff /tmp/prd_frs.txt /tmp/shard_frs.txt && echo "FR coverage OK"

# Session has been reset
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

Expected session phase: `IDLE`. The session transitions out of `SHARD` once the post-script commits.

## Troubleshooting

### Pre-script returns `NO_EPIC`

`deviate shard pre` could not discover any epic bucket under `specs/`. Either no epic directory exists yet or `discover_latest_epic()` cannot parse the existing directories. Run `/deviate-prd` first to create the bucket; if the bucket exists but is being skipped, confirm the directory name matches the `<NNN>-<slug>` pattern.

### Pre-script returns `MALFORMED_PRD_CONTRACT`

The PRD is missing `FR-{NNN}-{ID}` or `AC-{NNN}-{ID}-{NN}` tokens, or the tokens are inconsistent across sections. Open `prd.md` and confirm every functional requirement line carries the `FR-NNN-ID` format and every acceptance criterion carries the `AC-NNN-ID-NN` format. Re-run `/deviate-prd` with a tightened contract if the upstream PRD was ambiguous.

### Post-script halts with `SHARD_HALTED: manifest missing 'issues' array`

The LLM emitted a manifest without an `issues` array, or the array is empty. Open `.deviate/artifacts/manifest_shard.json` — if the array is present in the file but the post-script still halts, you may have written the file in a different shape than `IssueRecord` (e.g., the older `files_modified` schema). Re-write the manifest with the canonical `IssueRecord` shape and re-run the post-script.

### Cumulative FR coverage fails — one or more FRs unmapped

After writing all shards, the orchestrator runs an internal coverage check. If any FR from the PRD does not appear in any shard's frontmatter, it halts with `INCOMPLETE_FR_COVERAGE` and lists the missing FRs. Either re-cluster by adding the orphaned FR to an existing shard (amend the manifest and the shard file) or add a new shard that absorbs the FR end-to-end.

### Circular dependency in DAG

If the manifest's `blocked_by` arrays form a cycle (e.g., `A.blocked_by = [B]` and `B.blocked_by = [A]`), the post-script halts with `TOPOLOGY_LOOP_FAULT`. Open the manifest, find the cycle, and either drop one of the dependencies or convert one to `coordinates_with` (lateral knowledge overlap, not a sequential blocker).

### Post-script times out or fails on pre-commit hooks

The post-script runs pre-commit hooks including the full test suite. On large repos or slow CI, this can exceed 3 minutes. If it times out, increase the timeout to ≥ 180s and re-run. If it still fails, read the post-script output; common causes are:

- A pre-commit hook is rejecting content in a shard file (e.g., a markdown linter rejecting the Gherkin block style or a YAML schema validator rejecting the `flow_refs` shape).
- The test suite is failing for an unrelated reason. Run `mise run test` (or your repo's `TEST_COMMAND` from `specs/constitution.md`) in isolation to diagnose.

If the commit is partial, restore the working tree (`git checkout -- specs/NNN-*/issues/ specs/issues.jsonl`) and re-run the post-script once the underlying issue is fixed. Because `specs/issues.jsonl` is union-merged (`merge=union` in `.gitattributes`, seeded by `deviate setup`), concurrent appends from another branch will not conflict at merge time.

### `specs/_product/` missing — shards emit empty `flow_refs`

This is a soft gap, not a halt. The manifest logs `flow_refs: []` for every shard and the slash command continues. If you intended flow traceability, scaffold `specs/_product/` with `flows/flows-product.md` (and domain-specific flows) before re-running shard. If you intentionally do not maintain a product layer, the gap is acceptable and the `flow_refs: []` rows are correct.

## Next Steps

- [How to run /deviate-prd](/how-to/prd) — the prerequisite phase; shard consumes the PRD file the prd phase produces.
- [How to run /deviate-research](/how-to/research) — closes HITL Gate 1; without it the data model and architecture constraints are not anchored before sharding.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `deviate-shard`, including its aliases (`shard`, `spec:full:shard`, `/shard`) and `deviatdd-macro-layer` category.
- [Explanation: HITL Gate 2](/explanation/hitl-gates) — why the post-shard review gate exists and what spec errors it is designed to catch before task decomposition.
- [Explanation: append-only ledger discipline](/explanation/append-only-ledger) — why `specs/issues.jsonl` is append-only with a `merge=union` driver (`src/deviate/cli/__init__.py:666-672`, seeded by `deviate setup`) and how concurrent branch appends stay conflict-free at merge time.
- [Explanation: vertical-slice mandate](/explanation/three-layer-architecture) — the rationale for the "no horizontal slices" anti-pattern gate and why Pass 3 of the Internal ICoT re-clusters single-layer slices.