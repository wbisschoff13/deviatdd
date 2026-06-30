---
title: "Slash Commands"
description: "Inventory of all 31 slash commands shipped under src/deviate/prompts/commands/, with name, aliases, layer, category, and version."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Slash Commands

Inventory of every slash command shipped under `src/deviate/prompts/commands/`, listing name, aliases, category, version, and a one-line description for each. Slash commands are the prompt layer that drives the DeviaTDD three-layer workflow and the Tome docs subsystem; they are installed into per-agent command directories by `deviate setup`.

## Frontmatter Schema

Each command's YAML frontmatter is composed of the following fields. Some fields (`layer`, `aliases`) are present only on commands that map to an assembly phase.

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | `<file-stem>` | Slash-command identifier (matches the file stem) |
| `description` | `string` | `""` | Single-sentence purpose shown in agent autocomplete |
| `category` | `enum` | `deviatdd-macro-layer` | Routing label for assembly and command-indexing |
| `version` | `semver` | `1.0.0` | Slash-command template version (semver) |
| `layer` | `enum` | `null` | Phase-layer mapping (`macro` / `meso` / `micro`); present only on phases with an auto-prefix |
| `aliases` | `list[string]` | `[]` | Alternate invocations accepted by agent autocomplete |

## Categories

The six `category` values observed across the shipped command set. Note: two files carry a typo'd prefix `deviattd-` (double `t`); both spellings are preserved verbatim below.

| Category | Count | Used by |
|---|---|---|
| `deviatdd-macro-layer` | 8 | `deviate-adhoc`, `deviate-constitution`, `deviate-explore`, `deviate-init`, `deviate-prd`, `deviate-research`, `deviate-shard`, `deviate-triage` |
| `deviattd-macro-layer` | 6 | `deviate-e2e`, `deviate-green`, `deviate-hotfix`, `deviate-prune`, `deviate-red`, `deviate-refactor` (typo: double-`t` prefix) |
| `deviatdd-meso-layer` | 4 | `deviate-plan`, `deviate-pr`, `deviate-review`, `deviate-tasks` |
| `deviattd-micro-layer` | 3 | `deviate-execute`, `deviate-judge`, `deviate-yellow` (typo: double-`t` prefix) |
| `deviatdd-product-layer` | 3 | `deviate-architecture`, `deviate-flows`, `deviate-release` |
| `deviatdd-tome-layer` | 7 | `tome-classify`, `tome-setup`, `tome-verify-docs`, `tome-write-explanation`, `tome-write-how-to`, `tome-write-reference`, `tome-write-tutorial` |

## Deviate Commands — Macro Layer

| Command | Version | Aliases | Description |
|---|---|---|---|
| `deviate-adhoc` | `1.0.0` | `adhoc`, `/deviate-adhoc`, `spec:adhoc`, `spec.adhoc` | Emit a single ad-hoc vertical-slice issue from a natural-language task with lightweight discovery, shared PRD tracking, and flow_refs |
| `deviate-constitution` | `1.0.0` | `constitution`, `/deviate-constitution`, `spec:constitution`, `spec.constitution` | Initialize or update `specs/constitution.md` — the authoritative governance artifact defining tech stack, testing mandates, and DoD |
| `deviate-explore` | `2.0.0` | `/deviate-explore`, `/explore`, `spec:full:explore` | Read-only structural scan of the codebase; emits raw `explore.md` (what exists, not what to do) |
| `deviate-init` | `1.0.0` | `/deviate-init`, `/init`, `spec:init` | Initialize a repo with DeviaTDD conventions — `mise.toml` (zero-test-pass), `specs/` + `issues.jsonl`, `constitution.md` scaffold |
| `deviate-prd` | `1.0.0` | `prd`, `/deviate-prd`, `spec:full:prd`, `spec.full.prd` | Compile `explore.md` into `prd.md` — the singular source of truth for downstream sharding into `specs/issues.jsonl` |
| `deviate-research` | `2.0.0` | `/deviate-research`, `/research`, `spec:full:research`, `tools:research` | Architectural analysis — produce `design.md` (options, trade-offs, risk register) and `data-model.md` from `explore.md` |
| `deviate-shard` | `1.0.0` | `shard`, `/deviate-shard`, `spec:full:shard`, `/shard` | Decompose `prd.md` into self-contained Feature Vertical issues registered in `specs/issues.jsonl` with a DAG dependency topology |
| `deviate-triage` | `1.0.0` | `triage`, `/deviate-triage`, `spec:triage`, `spec.triage` | Classify requirements against fixed predicates (`FULL`, `CORE`, `TDD`, `NONE`) for deterministic workflow routing |

## Deviate Commands — Meso Layer

| Command | Version | Aliases | Description |
|---|---|---|---|
| `deviate-plan` | `1.0.0` | `plan`, `/deviate-plan`, `spec:core:plan`, `spec.core.plan`, `/plan` | Per-issue localized research — scan codebase and prior implementations; produce `plan.md` with strategy, file mappings, and risks |
| `deviate-tasks` | `1.0.0` | `tasks`, `/deviate-tasks`, `spec:core:tasks`, `spec.core.tasks`, `/tasks` | Decompose a spec-enriched issue into `tasks.md` — autonomous Red-Green-Refactor units (vertical, 30-90 min each) |
| `deviate-pr` | `1.0.0` | `pr`, `/deviate-pr`, `tools:pr` | Create a PR from the current worktree branch; on merge, append `COMPLETED` to `specs/issues.jsonl` to unblock dependents |
| `deviate-review` | `2.0.0` | `review`, `/deviate-review`, `/review` | HITL Gate 3 PR review — structured scan across Security, Clean Code, Pragmatism, Idiomacy, Constitution, PRD, and Flow Coverage |

## Deviate Commands — Micro Layer

| Command | Version | Aliases | Description |
|---|---|---|---|
| `deviate-red` | `1.0.0` | `red`, `/spec.tdd.red`, `/red`, `/tdd.red` | Execute the RED (test-writing) phase of TDD for a single task |
| `deviate-green` | `1.0.0` | `green`, `/spec.tdd.green`, `/green`, `/tdd.green` | Execute the GREEN (implementation) phase of TDD for a single task |
| `deviate-refactor` | `1.0.0` | `refactor`, `/spec.tdd.refactor`, `/refactor`, `/tdd.refactor` | TDD REFACTOR phase — behavior-preserving structural improvement after tests pass |
| `deviate-yellow` | `1.0.0` | `yellow`, `/spec.tdd.yellow`, `/yellow`, `/tdd.yellow` | TDD YELLOW phase — evaluate proposed test changes from the GREEN phase for conditional amendment |
| `deviate-judge` | `1.1.0` | `judge`, `/judge`, `/tdd.judge` | TDD JUDGE phase — review GREEN implementation against `spec.md` for correctness and integrity; emit `COMPLIANCE_PASS` |
| `deviate-execute` | `1.0.0` | `execute`, `/spec.execute`, `/x` | Direct task execution (no TDD cycle) for low-complexity tasks, trivial changes, docs, or refactors with existing coverage |

## Deviate Commands — TDD Adjacent (macro-typed)

These commands run in the micro-cycle context but are typed with the macro-layer category.

| Command | Version | Aliases | Description |
|---|---|---|---|
| `deviate-e2e` | `1.0.0` | `e2e`, `/spec.tdd.e2e`, `/e2e`, `/tdd.e2e` | Run final E2E verification after all tasks complete — user-facing tests confirming the feature meets intent |
| `deviate-prune` | `1.0.0` | `prune`, `/spec.tdd.prune`, `/prune`, `/tdd.prune` | TDD PRUNE phase — remove implementation-coupled and redundant tests while preserving public behavioral contracts |
| `deviate-hotfix` | `1.0.0` | `hotfix`, `/spec.hotfix`, `/hotfix` | Decompose bug reports into autonomous Red-Green-Refactor hotfix units |

## Deviate Commands — Product Layer

| Command | Version | Aliases | Description |
|---|---|---|---|
| `deviate-flows` | `1.2.0` | `flows`, `/deviate-flows`, `spec:flows`, `spec.flows` | FLOW-01 flows authoring — discover customer flows, write concise `flows-<domain>.md`, and maintain `specs/_product/flows/index.md` |
| `deviate-architecture` | `1.0.0` | `architecture`, `/deviate-architecture`, `spec:architecture`, `spec.architecture` | FLOW-02 architecture authoring — produce `specs/_product/architecture.md` and `domain-model.md` as cross-epic contracts (requires flows) |
| `deviate-release` | `1.0.0` | `release`, `/deviate-release`, `spec:release`, `spec.release` | FLOW-03 release planning — compile the next coherent release from flows/architecture and write `specs/_product/release-next.md` |

## Tome Commands — Tome Layer

| Command | Version | Aliases | Description |
|---|---|---|---|
| `tome-classify` | `1.0.0` | `tome-classify`, `/tome-classify`, `spec:classify`, `spec.classify`, `spec:tome-classify`, `spec.tome-classify` | Tome C1 — ingest commit, branch, or whole-codebase evidence and emit a Diátaxis classification report naming the required doc-type quadrants |
| `tome-setup` | `1.0.0` | `tome-setup`, `/tome-setup`, `spec:setup`, `spec.setup`, `spec:tome-setup`, `spec.tome-setup` | Tome C7 — idempotent bootstrap of `apps/docs/` with Starlight, the four Diátaxis quadrants, and `content.config.ts` |
| `tome-verify-docs` | `1.0.0` | `tome-verify-docs`, `/tome-verify-docs`, `spec:verify-docs`, `spec.verify-docs`, `spec:tome-verify-docs`, `spec.tome-verify-docs` | Tome C6 — read-only cross-doc verification over C2-C5 outputs, checking factual consistency, paths, and Diátaxis purity |
| `tome-write-tutorial` | `1.0.0` | `tome-write-tutorial`, `/tome-write-tutorial`, `spec:write-tutorial`, `spec.write-tutorial`, `spec:tome-write-tutorial`, `spec.tome-write-tutorial` | Tome C2 — write one tutorial page under `apps/docs/.../tutorials/` when `tome-classify` selects `tutorial` |
| `tome-write-how-to` | `1.0.0` | `tome-write-how-to`, `/tome-write-how-to`, `spec:write-how-to`, `spec.write-how-to`, `spec:tome-write-how-to`, `spec.tome-write-how-to` | Tome C3 — write one how-to page under `apps/docs/.../how-to/` when `tome-classify` selects `how-to` |
| `tome-write-reference` | `1.0.0` | `tome-write-reference`, `/tome-write-reference`, `spec:write-reference`, `spec.write-reference`, `spec:tome-write-reference`, `spec.tome-write-reference` | Tome C4 — write one reference page under `apps/docs/.../reference/` when `tome-classify` selects `reference` |
| `tome-write-explanation` | `1.0.0` | `tome-write-explanation`, `/tome-write-explanation`, `spec:write-explanation`, `spec.write-explanation`, `spec:tome-write-explanation`, `spec.tome-write-explanation` | Tome C5 — write one explanation page under `apps/docs/.../explanation/` when `tome-classify` selects `explanation` |

## Installation Targets

`deviate setup` discovers installed agent platforms by scanning for `.claude/`, `.opencode/`, `.factory/`, and `.pi/` directories in the workdir. Each detected platform receives a flat copy of every command. Defined in `src/deviate/cli/__init__.py::_get_agent_command_dir`.

| Agent | Target directory | Layout |
|---|---|---|
| `claude` | `<workdir>/.claude/commands/` | flat `.md` |
| `opencode` | `<workdir>/.opencode/commands/` | flat `.md` |
| `factory` | `<workdir>/.factory/commands/` | flat `.md` |
| `pi` | `<workdir>/.pi/prompts/` | flat `.md` |

The installer at `src/deviate/cli/__init__.py::_install_commands_to_agents` walks every file in `src/deviate/prompts/commands/` (sorted by `discover_commands()`) and writes each composed command (frontmatter stripped to `name`/`description` only) into every detected platform's command directory. Aggregate summary output is emitted per-agent.

## Source-of-Truth

| Attribute | Location |
|---|---|
| Command file | `src/deviate/prompts/commands/<name>.md` |
| Discovery | `src/deviate/core/commands.py::discover_commands` |
| Composition | `src/deviate/core/commands.py::compose_command_body` (prepends `core.md` + `{layer}-command.md`) |
| Installation | `src/deviate/cli/__init__.py::_install_commands_to_agents` (lines 532-562) |
| Agent routing | `src/deviate/cli/__init__.py::_get_agent_command_dir` |

## See Also

- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — exercises slash-command installation via `deviate setup`
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
- [How-To intro](/how-to/intro) — operator-task quadrant
- [Explanation intro](/explanation/intro) — rationale and design choices quadrant
- [Tutorials intro](/tutorials/intro) — guided-learning quadrant
