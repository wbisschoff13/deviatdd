---
title: "Run the /deviate-adhoc phase"
description: "Emit a single spec-enriched vertical-slice issue from a natural-language task with lightweight discovery, shared PRD tracking, and flow_refs in one invocation."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-002-003
  - ISS-ADH-011
---

# Run the /deviate-adhoc phase

This how-to covers `/deviate-adhoc` — the macro-layer fast-path shortcut that compresses explore + research + PRD + shard into a single slash-command invocation for low-to-medium complexity tasks. The skill ingests a natural-language task description, runs a Complexity Gate (`ComplexityGate.classify()` at `src/deviate/core/complexity.py:18`), performs proportional codebase discovery, appends an `FR-ADHOC-NNN` entry to the shared append-only ledger at `specs/adhoc/prd.md`, writes one spec-enriched vertical-slice issue to `specs/adhoc/issues/{NNN}-{slug}.md`, registers it in `specs/issues.jsonl` as an `ISS-ADH-NNN` row, and commits the result on the active branch. The skill is the right call when the task is small enough to plan in one pass and you do not need a numbered epic bucket — for High complexity work, escalate to [`/deviate-research`](/how-to/research) instead. The slash command is registered at `src/deviate/cli/__init__.py:792`; the underlying prompt body lives at `src/deviate/prompts/commands/deviate-adhoc.md`.

## Prerequisites

- **DeviaTDD workspace bootstrapped** — `deviate setup` has run, so `.deviate/config.toml` exists and `/deviate-adhoc` is in the agent prompt palette. If you have not done this yet, see [Bootstrap a DeviaTDD workspace](/how-to/setup).
- **A clean working tree on the active branch** — the skill commits via the post-script, so any staged-but-uncommitted work will be swept into the `docs(adhoc): add issue {ISSUE_ID} - {title}` commit.
- **A natural-language task description (1–3 sentences)** — describe the problem space, not the implementation. The skill derives a kebab-case slug (max 40 chars) from this description and uses it for both the issue file path and the commit subject. Examples: `"Add a `--domain` filter flag to the `deviate inspect` CLI command"`, `"Surface the active flow_refs in the slice header of the Starlight sidebar"`.
- **Scope check passed mentally** — the task must be implementable by editing or adding ≤ 5 files in ≤ 3 distinct concerns. Tasks that span more than that exceed ad-hoc scope; the skill will warn and offer to split or escalate to the full deviation explore workflow. Use [`/deviate-explore`](/how-to/explore) for ambiguous or wide-scoped requests.
- **Slash-command-capable agent** — Pi, OpenCode, Claude, or Factory running against the project root with read access to the full repo (the Lightweight Discovery Pass walks the tree).
- **Optional: an existing `specs/explore/<slug>.md`** — when `/deviate-explore` classified the feature as Low/Medium complexity and routed here, the matching `explore.md` is consumed automatically as the primary discovery context (step 2.5 of the skill body), and the Lightweight Discovery Pass is skipped. If no explore file matches the slug, the skill falls back to in-pass grep/glob/read.

## Steps

### 1. Compose the task description

Draft 1–3 sentences that name the user-visible capability you want to ship. Avoid implementation hints (library names, file paths, internal symbols) — the skill does its own discovery and will warn when a description drifts into solution prescription.

Acceptable examples:

```text
"Add a `--domain` filter flag to the `deviate inspect` CLI command."
"Surface the active flow_refs in the slice header of the Starlight sidebar."
"Migrate the adhoc prompt body to consume flow_refs from the issues ledger instead of the post-script contract."
```

### 2. (Optional) Resolve Product-layer flow_refs in advance

If the task clearly maps to one or more Product-layer flows (`FLOW-01` Flows, `FLOW-02` Architecture, `FLOW-03` Release, plus domain-specific flows in `specs/_product/flows/`), you can pass them explicitly with `--flow-ref FLOW-01,FLOW-02`. The CLI validates each token against `^FLOW-\d{2,}$` (`src/deviate/cli/adhoc.py:16`) and rejects malformed values with `INVALID_FLOW_REF`.

If you skip this flag, the skill infers the mapping from the task description against `specs/_product/flows/flows-product.md` (and any domain-specific `flows-<domain>.md`) plus `specs/_product/release-next.md`. When inference is ambiguous, the skill emits `flow_refs: []` for the issue and surfaces a clarifying question in the `## Discovery Audit`. Empty `flow_refs` is valid for enabling/infrastructure tasks that touch zero Product-layer flows.

### 3. Run `/deviate-adhoc`

In the agent chat, invoke the slash command with the task description as the argument. Add `--flow-ref FLOW-XX,FLOW-YY` if you resolved the flow mapping in step 2:

```bash
/deviate-adhoc "Add a `--domain` filter flag to the `deviate inspect` CLI command."

# Explicit flow_refs override
/deviate-adhoc --flow-ref FLOW-01 "Surface the active flow_refs in the slice header of the Starlight sidebar."
```

The slash command is the single primary action for this how-to. It orchestrates `deviate adhoc pre`, the Lightweight Discovery Pass (or Existing Explore Check), the PRD append, the issue file write, the ledger registration, and `deviate adhoc post` (which commits) internally. You do not invoke `deviate adhoc pre` or `deviate adhoc post` directly — the skill does.

### 4. Wait for the Complexity Gate

The slash command invokes `deviate adhoc pre` first (`src/deviate/cli/adhoc.py:67-113`). The pre-script runs `ComplexityGate.classify(description)` and:

- **`LOW` or `MEDIUM`** — proceed. The skill emits a JSON contract on stdout with `status: READY`, `execution_mode: DIRECT`, `description`, `issue_id` (`adhoc-YYYYMMDDHHMMSS`), and `flow_refs`. The skill then performs the discovery pass and synthesizes the issue.
- **`HIGH`** — exit non-zero with `COMPLEXITY_GATE_REJECTION HIGH complexity tasks require --skip-gates to proceed`. Either break the task into smaller pieces and re-run, or escalate to [`/deviate-explore`](/how-to/explore) to initiate a full epic workflow. The `--skip-gates` flag bypasses the gate; use it only when you have already validated the scope manually and want to force the issue through the fast-path.

### 5. Read the Discovery Audit

The skill outputs a `## Discovery Audit` block that catalogs the grounding for the issue:

- **Target Files Identified** — existing files to modify and new files to create, with repo-relative paths.
- **Existing Patterns** — hooks, utilities, or conventions the task should follow.
- **Scope Boundary** — what is in-scope.
- **Excluded** — what is defensively excluded from this slice.
- **Flow Refs Resolved** — the final `flow_refs` list (explicit `--flow-ref` override wins over inferred mapping; `[]` when no flows match).

When the task spans more than 5 files or 3 distinct concerns, the skill warns in this block and asks before proceeding.

### 6. Read the Shared PRD Append

The skill outputs a `## Shared PRD Append` block confirming the new `FR-ADHOC-NNN` section was appended to `specs/adhoc/prd.md`. The PRD is append-only; the skill does not edit or delete prior FR sections. Each `FR-ADHOC-NNN` carries Description, Preconditions, Inputs/Outputs, User Stories, and Acceptance Criteria blocks.

### 7. Read the Target Issue Emission

The skill outputs a `## Target Issue Emission` block with the `File_Target_Path` for `specs/adhoc/issues/{NNN}-{slug}.md` and the full issue markdown. The issue carries the canonical section ordering (System Topology Mapping, The Problem Contract, Scope Boundaries, Upstream Requirement Tracing, User Stories Ledger, ATDD Acceptance Criteria, Edge Cases and Boundaries, Performance Constraints, Multi-Tiered Verification Targets, Demonstration Path) that matches the shard canonical format.

### 8. Read the Ledger Registration

The skill outputs a `## Ledger Registration` block with the exact `IssueRecord` JSON it appended to `specs/issues.jsonl`. The record follows the canonical schema:

```json
{"issue_id":"ISS-ADH-NNN","type":"adhoc","title":"...","status":"BACKLOG","source_file":"specs/adhoc/issues/NNN-slug.md","blocked_by":[],"coordinates_with":[],"timestamp":"ISO8601","created_at":"ISO8601","flow_refs":["FLOW-XX","..."]}
```

The record is appended (not overwritten) — `specs/issues.jsonl` is append-only per the ledger discipline.

### 9. Verify the artifact is on disk and committed

Confirm the post-script committed the new files to the active branch and the ledger row was appended:

```bash
# Issue file exists with the expected sections
ls specs/adhoc/issues/NNN-slug.md
grep -E "^## (User Stories Ledger|ATDD Acceptance Criteria|Edge Cases and Boundaries|Performance Constraints)$" specs/adhoc/issues/NNN-slug.md

# PRD append landed
grep -E "^## FR-ADHOC-NNN: " specs/adhoc/prd.md | tail -1

# Ledger registration (last record wins)
tail -1 specs/issues.jsonl | python -c "import json,sys; r=json.loads(sys.stdin.read()); print(r['issue_id'], r['type'], r['status'])"

# Commit landed on the active branch
git log --oneline -1
git show --stat HEAD -- specs/adhoc/
```

The latest commit message should be `docs(adhoc): add issue {ISSUE_ID} - {title}`. The diff should show the new `specs/adhoc/issues/NNN-slug.md`, a new `## FR-ADHOC-NNN` section appended to `specs/adhoc/prd.md`, and one new line appended to `specs/issues.jsonl`. The `BACKLOG` status in the ledger row is correct at this point — downstream phases (`specify`, `plan`, `tasks`) move it forward.

## Troubleshooting

### Pre-script exits with `COMPLEXITY_GATE_REJECTION`

`ComplexityGate.classify()` returned `HIGH` for the task description (or, in the absence of a richer classifier, the pre-script is conservatively rejecting). High-complexity work — multi-module coordination, new architecture, cross-cutting state management — must not run through the fast-path.

**Fix**: Either (a) split the task into smaller ad-hoc issues (each one passes the gate) and re-invoke `/deviate-adhoc` for each, (b) escalate to [`/deviate-explore`](/how-to/explore) for a full epic workflow that ends in [`/deviate-research`](/how-to/research) → [`/deviate-prd`](/how-to/prd) → [`/deviate-shard`](/how-to/shard), or (c) re-invoke with `--skip-gates` only after manually validating that the scope is in fact bounded. Do not bypass the gate on autopilot; it is the safeguard that keeps adhoc a true fast-path rather than a backdoor for complex engineering.

### Pre-script exits with `INVALID_FLOW_REF '<token>' is not a valid flow ID`

A `--flow-ref` token failed the `^FLOW-\d{2,}$` regex check (`src/deviate/cli/adhoc.py:16`). The format hint is `FLOW-XX` with at least two digits.

**Fix**: Re-run `/deviate-adhoc --flow-ref FLOW-01,FLOW-02` (or the correct flow IDs from `specs/_product/flows/flows-product.md`) with valid tokens. If you do not know the flow IDs, drop the `--flow-ref` flag entirely and let the skill infer from the task description against the Product-layer flows.

### Skill outputs `Could not infer Product-layer flow mapping — please re-run with --flow-ref FLOW-XX`

The task description did not match any Product-layer flow's Trigger or Problem statement, and no explicit `--flow-ref` was passed. The skill emits `flow_refs: []` in the issue frontmatter and ledger entry and continues — empty `flow_refs` is valid for enabling/infrastructure tasks.

**Fix**: If the task should map to a Product-layer flow, re-run `/deviate-adhoc --flow-ref FLOW-XX "..."` with the explicit override. If `specs/_product/` is missing entirely, the gap is upstream — initialize the Product-layer artifacts first (see [Bootstrap a DeviaTDD workspace](/how-to/setup)).

### Skill warns `task may exceed ad-hoc scope (>5 files or >3 concerns)`

The Lightweight Discovery Pass mapped more than 5 target files or more than 3 distinct concerns for the task description. The skill halts before emitting the issue and asks the human operator to confirm or split.

**Fix**: Either (a) re-run with a tighter task description that scopes the work to fewer files/concerns, (b) split into multiple ad-hoc issues (one per bounded concern) and run `/deviate-adhoc` for each, or (c) escalate to [`/deviate-explore`](/how-to/explore) → [`/deviate-research`](/how-to/research) → [`/deviate-prd`](/how-to/prd) → [`/deviate-shard`](/how-to/shard) for a fully orchestrated epic.

### Existing `specs/explore/<slug>.md` was not consumed

You ran `/deviate-explore` and routed here on Low/Medium Scope Sizing, but the skill's Existing Explore Check (step 2.5 of `src/deviate/prompts/commands/deviate-adhoc.md`) did not pick up the `explore.md`. The slug derived from the adhoc task description does not match any file under `specs/explore/`.

**Fix**: Either (a) re-run `/deviate-adhoc` with the exact problem statement you used for `/deviate-explore` so the derived slug matches, or (b) read `specs/explore/<slug>.md` manually and inline its findings into the adhoc task description. The check is slug-based, not semantic — the strings must align.

### Ledger registration fails or `deviate issues` tool is missing

The skill could not append to `specs/issues.jsonl` (e.g., the `deviate issues` subcommand is unavailable in this environment). The skill emits the full issue content to stdout and instructs the operator to register manually rather than lose the generated issue.

**Fix**: Manually append the JSON record printed in the `## Ledger Registration` block to `specs/issues.jsonl` (one line, append-only), then re-run `deviate adhoc post` to commit. Do not modify any other file outside `specs/adhoc/` and `specs/issues.jsonl` for this how-to.

## Next Steps

- [Run the /deviate-plan phase](/how-to/plan) — the next meso phase for the issue you just emitted; consumes the spec-enriched issue file and emits `plan.md` (the bridge between shard and tasks; `/deviate-specify` was absorbed into `/deviate-shard` per the v2.0 CHANGELOG).
- [Run the /deviate-explore phase](/how-to/explore) — the upstream macro phase that often routes here via Low/Medium Scope Sizing; the existing `explore.md` is consumed automatically.
- [Run the /deviate-research phase](/how-to/research) — the escalation path when the Complexity Gate rejects a high-complexity task; produces `design.md` + `data-model.md` and unlocks [`/deviate-prd`](/how-to/prd) and [`/deviate-shard`](/how-to/shard).
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `deviate-adhoc`, including its aliases (`adhoc`, `/deviate-adhoc`, `spec:adhoc`, `spec.adhoc`) and `deviatdd-macro-layer` category.
- [Reference: `deviate adhoc` CLI flags](/reference/adhoc) — the full pre/post contract, `--flow-ref` regex, and complexity gate semantics.
- [Explanation: append-only ledger discipline](/explanation/append-only-ledger) — why `specs/issues.jsonl` and `specs/adhoc/prd.md` are append-only with a `merge=union` driver and how the `BACKLOG` transition unblocks downstream `specify`/`plan`/`tasks` phases without rewriting prior rows.
- [Explanation: complexity gate rationale](/explanation/three-layer-architecture) — why the fast-path rejects high-complexity tasks and how the gate preserves the layered architecture (macro → meso → micro).