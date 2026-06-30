---
title: "Run the product-layer workflow"
description: "Run /deviate-flows, /deviate-architecture, and /deviate-release to author specs/_product/flows/, architecture.md, and release-next.md."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-010
---

# Run the product-layer workflow

This how-to covers the product-layer authoring chain — the three slash commands that live above the macro layer and produce the cross-epic contracts that downstream exploration, research, and sharding consume. Run them in order: [`/deviate-flows`](/reference/slash-commands#deviate-commands--product-layer) discovers customer flows and writes `specs/_product/flows/flows-<domain>.md` plus `index.md`; [`/deviate-architecture`](/reference/slash-commands#deviate-commands--product-layer) consumes those flows and produces `specs/_product/architecture.md` (cross-epic integration) and `specs/_product/domain-model.md` (entity-relationship map); [`/deviate-release`](/reference/slash-commands#deviate-commands--product-layer) compiles the next coherent release from both into `specs/_product/release-next.md`, the compass for downstream [`/deviate-explore`](/how-to/explore). Each command enforces a non-bypassable precondition gate on the previous artifact, so the chain cannot be run out of order.

## Prerequisites

- **A bootstrapped DeviaTDD workspace** — `deviate` must be on `PATH`, `.deviate/config.toml` must exist, and the project must be initialized. If any of those are missing, finish [Bootstrap a DeviaTDD workspace](/how-to/setup) and [Initialize a repo with DeviaTDD conventions](/how-to/init) before proceeding; the product-layer commands assume both have already run.
- **`specs/constitution.md` present and committed** — `/deviate-architecture` runs a constitutional alignment audit before it emits `architecture.md`. If the constitution is missing or has not been amended for the current tech stack, finish [Run the /deviate-constitution workflow](/how-to/constitution) first; a constitutional conflict surfaces as `[yellow]CONSTITUTION_CONFLICT[/]` and halts architecture authoring.
- **A coherent product-scope idea** — the product layer is for cross-epic, customer-visible surface area, not for a single feature. Before `/deviate-flows` runs, you should be able to name the actor, the job-to-be-done, the trigger, preconditions, a happy path, and a success state at a level that spans multiple epics. Single-feature ideas belong in [Run the /deviate-explore phase](/how-to/explore) instead.
- **An agent platform with the product-layer slash commands installed** — `/deviate-flows`, `/deviate-architecture`, and `/deviate-release` are installed into your agent's prompt directory by `deviate setup`. If the slash commands are missing, re-run setup or consult the slash-command reference's [Product Layer section](/reference/slash-commands#deviate-commands--product-layer).
- **A clean working tree on the active feature branch** — each command writes one or more files under `specs/_product/` and the post-script commits them. Uncommitted edits in that directory will block the run.

## Steps

### 1. Run `/deviate-flows` to discover customer flows

The first slash command in the chain. `/deviate-flows` conducts a conversational discovery of customer flows (actor, job-to-be-done, trigger, preconditions, happy path, alternate paths, success state), writes each accepted flow to `specs/_product/flows/flows-<domain>.md` with a `## FLOW-NN <Name>` header, and appends a row to `specs/_product/flows/index.md` for every flow authored. Multiple flows within the same domain land in the same file (FLOW-01 = `flows-product.md`); flows for a different domain land in a new file.

```text
/deviate-flows <describe your customer flow or product domain>
```

The slash command refuses to skip the conversational discovery — if any of actor, job-to-be-done, trigger, preconditions, happy path, or success state is ambiguous, it halts with a clarifying question (FLOW-01 invariant 4, `src/deviate/prompts/commands/deviate-flows.md:51-54`). Flow IDs are zero-padded sequential (`FLOW-NN`) and are the cross-layer traceability anchors downstream `deviate shard` and `deviate adhoc` use to populate `flow_refs:` frontmatter.

### 2. Run `/deviate-architecture` to author cross-epic architecture

The second slash command. `/deviate-architecture` consumes the flow files from step 1 (the FLOW-02 precondition) and emits two artifacts: `specs/_product/architecture.md` (components, integration contracts, data-ownership boundaries, dependency graph with FLOW-NN citations) and `specs/_product/domain-model.md` (entity-relationship map, kept terse: entity name, attributes, relationships). The slash command classifies every requested architectural change as **Local**, **Context-Bridging**, or **Context-Creating**, and surfaces any of these that span epics for HITL Gate 1 review.

```text
/deviate-architecture <describe the architectural intent or component boundary>
```

If the precondition is unmet, the slash command halts with `[red]FLOWS_MISSING[/]` and recommends running `/deviate-flows` first. If the constitution and your architecture conflict, it halts with `[yellow]CONSTITUTION_CONFLICT[/]` and surfaces the offending clause; resolve the conflict (amend the constitution or amend the architecture) before re-running. Architecture here is strictly cross-epic — epic-local or feature-local concerns belong in [Run the /deviate-plan phase](/how-to/plan) instead.

### 3. Run `/deviate-release` to plan the next coherent release

The third slash command. `/deviate-release` compiles the next coherent release from the flows and architecture (the FLOW-03 preconditions) and writes `specs/_product/release-next.md` with a Goal, Constraints, Included Flows table, Included Work table (every row carries a `Flow Refs` column of `FLOW-NN` IDs), and an `## Acceptance Criteria` section whose first criterion cites `deviate setup` installation semantics when product-layer skills are part of the release scope.

```text
/deviate-release <describe your release goal>
```

Re-running `/deviate-release` for the same release target overrides the prior `release-next.md`. The slash command surfaces a `[yellow]RELEASE_OVERRIDE[/]` banner before writing, and preserves a `[yellow]WARN[/]` if the prior release had any non-trivial Acceptance Criteria the new release omits. After writing, the slash command does not trigger downstream exploration itself — it surfaces the file path and recommends `/deviate-explore` as the next step.

### 4. Verify the product-layer chain

Confirm all three artifacts exist and the chain is internally consistent. The product-layer commands do not call into the macro layer, so this verification is purely a filesystem check — no LLM call, no pre/post-script.

```bash
# All three artifacts must exist
test -f specs/_product/flows/index.md && echo "flows/index.md OK"
test -f specs/_product/architecture.md && echo "architecture.md OK"
test -f specs/_product/release-next.md && echo "release-next.md OK"

# At least one FLOW-NN row must exist in the index
grep -cE "^\| FLOW-[0-9]+ " specs/_product/flows/index.md

# Architecture.md must cite at least one FLOW-NN
grep -cE "FLOW-[0-9]+" specs/_product/architecture.md

# release-next.md's Included Work table must carry Flow Refs
grep -cE "\| FLOW-[0-9]+" specs/_product/release-next.md

# All three artifacts must be committed
git status specs/_product/
```

If any artifact is missing, return to the corresponding step. If `git status` shows uncommitted edits, stage and commit them as a single `docs(product): ...` commit before invoking downstream `/deviate-explore`. If the FLOW-NN citations are absent from `architecture.md` or `release-next.md`, the slash command's traceability contract is broken — re-run the step with a stronger prompt that names the flow IDs explicitly.

## Troubleshooting

### `[red]FLOWS_MISSING[/]` from `/deviate-architecture`

The architecture slash command found no flow files under `specs/_product/flows/` and refused to author cross-epic architecture without upstream flows (per FLOW-02 Preconditions at `specs/_product/flows/flows-product.md:47`).

Run `/deviate-flows` first to populate at least one `flows-<domain>.md` file. Then re-run `/deviate-architecture`. Do not bypass the gate by hand-authoring an empty `flows-product.md` — the slash command reads conversational discovery output, not the file content, and a fabricated seed will fail downstream `deviate shard` cross-references.

### `[red]ARCH_OR_FLOWS_MISSING[/]` from `/deviate-release`

The release slash command found neither `specs/_product/architecture.md` nor any flow file and refused to compile a release without both (per FLOW-03 Preconditions at `specs/_product/flows/flows-product.md:77-79`).

Confirm both files exist with the verification commands in step 4. If either is missing, return to the corresponding step. If both exist but the slash command still halts, the precondition gate is reading the wrong path — check that `specs/_product/` resolves to the same `repo_root` the slash command sees (it must, but a stale worktree or detached HEAD can occasionally mask the path).

### `[yellow]CONSTITUTION_CONFLICT[/]` from `/deviate-architecture`

The architecture slash command detected a clause in `specs/constitution.md` (tech stack, testing protocol, or architectural principle) that the proposed architecture violates.

Open `specs/constitution.md` and locate the offending clause quoted in the conflict message. Decide which side is correct: amend the constitution if the clause is stale, or amend the architecture to align with the clause. Either way, do not paper over the conflict with a `[yellow]WARN[/]` override — the constitution is the authoritative governance artifact, and the slash command refuses to overwrite the conflict on a re-run until it is resolved. Use [Run the /deviate-constitution workflow](/how-to/constitution) for the amendment.

### `[yellow]RELEASE_OVERRIDE[/]` from `/deviate-release`

The release slash command is about to overwrite a prior `specs/_product/release-next.md`. The `[yellow]WARN[/]` line in the banner lists any non-trivial Acceptance Criteria from the prior release that the new release omits.

Read the warn list carefully. If the omissions are intentional, confirm the override and proceed. If they are accidental, abort the run, fold the omitted criteria back into the release goal, and re-run. Override semantics are documented at `src/deviate/prompts/commands/deviate-release.md:45-49` — once the override commits, the prior Acceptance Criteria are gone and recovering them requires `git log` archaeology on `release-next.md`.

### `/deviate-flows` halts with a clarifying question

The flows slash command will not emit a flow block until actor, job-to-be-done, trigger, preconditions, happy path, and success state are unambiguous (FLOW-01 invariant 4, `src/deviate/prompts/commands/deviate-flows.md:51-54`).

Answer the question concretely with a single sentence per field. If you cannot answer it, the customer-facing flow you are trying to capture is not yet ready to be product-layer specification — return to the customer-discovery phase (interviews, support-ticket triage, or product analytics) and gather the missing signal before re-running. The conversation-first discipline is intentional; it is the gate that keeps bloat out of `flows-<domain>.md` (≤35 lines per block, see FLOW-01 invariant 8).

## Next Steps

- [Reference: product-layer slash commands](/reference/slash-commands#deviate-commands--product-layer) — version, aliases, and full description for `/deviate-flows`, `/deviate-architecture`, and `/deviate-release`.
- [Why a Three-Layer Architecture](/explanation/three-layer-architecture) — design rationale for the Macro / Meso / Micro partition and where the product layer sits above it.
- [Run the /deviate-explore phase](/how-to/explore) — the natural next step after `/deviate-release`; consumes `release-next.md` as the guiding compass for the first epic.
- [Run the /deviate-constitution workflow](/how-to/constitution) — back-link for resolving `[yellow]CONSTITUTION_CONFLICT[/]` triggers surfaced in step 2.