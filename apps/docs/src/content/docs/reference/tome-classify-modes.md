---
title: "tome-classify Modes"
description: "Input modes, action enum, gate precedence, gate behaviors, confidence range, and report schema for the Tome C1 classifier slash command."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-011
---

# tome-classify Modes

The five input modes, five action enum values, four-rule gate precedence, three gate behaviors, confidence range, and report schema of `/tome-classify` — the read-only Tome C1 classifier that ingests commit, branch, or whole-codebase evidence and emits a Diátaxis classification report naming the writers the developer should subsequently invoke.

## Input Modes

| Mode | Invocation | Evidence source |
|---|---|---|
| `default` | `/tome-classify` (no args) | `git diff HEAD~1..HEAD` |
| `sha` | `/tome-classify <sha>` | `git diff <sha>~1..<sha>` |
| `merge-base` | `/tome-classify --merge-base` | `git diff $(git merge-base HEAD main)..HEAD` |
| `working-tree` | `/tome-classify --working-tree` | `git diff` + `git diff --staged` |
| `codebase` | `/tome-classify --codebase` | full repo tree (no diff; see Codebase Evidence) |

Argument parsing resolves mode by top-down precedence; the first match wins on conflict. An unparseable argument aborts the run with a one-line error pointing at this section. The `codebase` mode emits the `target_sha` header as `codebase:<head-short-sha>` to disambiguate from a real commit SHA.

## Action Enum

Each capability row carries exactly one action from the closed enum below. Drift between this enum and the verifier (C6) enum is a verifier-level finding.

| Action | Meaning | Downstream effect |
|---|---|---|
| `create` | New doc required; no existing page at `target_file` | Developer runs the writer indicated by `doc_type` |
| `update` | Existing doc at `target_file` requires revision | Developer runs the writer against the existing page |
| `no-change` | Diff is internal-only; no public docs affected | `SKIP` writers and `/tome-verify-docs` — terminal gate |
| `human-review` | Classifier is uncertain on `doc_type`, `target_file`, or quadrant collision | `BLOCK` writers until developer confirms intent; verifier does not run |
| `setup-required` | `apps/docs/` is absent in the target repo | `HALT` all downstream work; point at `/tome-setup`; verifier does not run |

## Gate Precedence

The overall `Status` line at the top of the report is evaluated by the following top-down rules; first match wins.

| Order | Condition | Resulting status | Effect |
|---|---|---|---|
| 1 | ANY row carries `setup-required` | `setup-required` | Halt; point at `/tome-setup` |
| 2 | ANY row carries `human-review` | `human-review` | Block all writers until human sign-off |
| 3 | ALL rows carry `no-change` | `no-change` | Skip writers and verifier |
| 4 | Otherwise (mixed `create` / `update` rows) | `mixed` | Developer runs the writer indicated by `doc_type` per row |

## Gate Behaviors

The three downstream gates that drive writer and verifier invocation.

| Gate | Trigger | Behavior |
|---|---|---|
| `no-change` gate | All rows carry `no-change` | Terminal skip; writers (`tome-write-*`) and `/tome-verify-docs` do NOT run; the report is the final output |
| `human-review` gate | Any row carries `human-review` | Blocking; developer either confirms the classification in-place (updating the row's `action`) or overrides `target_file` or `doc_type`; verifier does NOT run while any row remains `human-review`; classifier does NOT auto-retry |
| `setup-required` gate | `apps/docs/` is absent in the target repo | Hard halt; classifier does NOT propose `target_file` values; classifier points the developer at `/tome-setup` and exits |

## Confidence Range

`confidence` is a closed decimal in `[0.0, 1.0]`. Rows below the threshold force a blocking action.

| Range | Required `action` | Rationale |
|---|---|---|
| `0.7` – `0.9` (codebase mode high) | concrete (`create` / `update` / `no-change`) | Capability is declared in a manifest (e.g., `[project.scripts]` entry, `bin` in `package.json`, Typer subcommand definition) |
| `0.5` – `0.7` (codebase mode medium) | concrete | Capability is implicit in module structure (e.g., `src/deviate/cli/macro.py` exposes a macro sub-app); surface is fuzzy |
| `>= 0.5` | concrete | Sufficient signal to route the row to a writer or skip |
| `< 0.5` | `human-review` | Classifier is uncertain on `doc_type` or `target_file`; developer must confirm |

## Classification Report Sections

The report is a single markdown block with exactly three sections in this order, prefixed by an overall `Status` line. An empty capability table is invalid output.

| Section | Required | Content |
|---|---|---|
| `Status` line | yes | One of `no-change`, `human-review`, `setup-required`, `mixed`; reflects gate-precedence outcome |
| `## Summary` | yes | One-paragraph change summary: what changed, why it matters for docs, which audiences are affected |
| `## Capabilities` | yes | Capability table (see Capability Table Columns); MUST contain at least one row |
| `## No-Touch List` | yes when existing pages are candidate targets; `None — first-run classification` otherwise | Files that must NOT be modified; existing valid content to preserve |

## Capability Table Columns

The capability table's seven columns and their semantics. Rows with `action = setup-required` carry literal `null` in `target_file`.

| Column | Type | Description |
|---|---|---|
| `capability` | `string` | User-facing capability exposed or modified |
| `evidence` | `string` | Verbatim file paths and/or commit messages that justify this row; anchored to source, no speculation |
| `audience` | `enum` | `developer`, `operator`, `end-user`, or `contributor`; multiple values comma-separated |
| `doc_type` | `enum` | `tutorial`, `how-to`, `reference`, or `explanation`; drives which writer runs |
| `action` | `enum` | `create`, `update`, `no-change`, `human-review`, or `setup-required`; drives gate behavior |
| `target_file` | `path` \| `null` | Repo-relative path under `apps/docs/src/content/docs/<quadrant>/`; literal `null` when action is `setup-required` |
| `confidence` | `decimal` | Closed `[0.0, 1.0]`; rows with `< 0.5` MUST carry `action = human-review` |

## DocType → Quadrant Mapping

Drives which writer (`tome-write-tutorial`, `tome-write-how-to`, `tome-write-reference`, `tome-write-explanation`) the developer subsequently invokes.

| DocType | Target quadrant | Writer invoked |
|---|---|---|
| `tutorial` | `apps/docs/src/content/docs/tutorials/` | `tome-write-tutorial` |
| `how-to` | `apps/docs/src/content/docs/how-to/` | `tome-write-how-to` |
| `reference` | `apps/docs/src/content/docs/reference/` | `tome-write-reference` |
| `explanation` | `apps/docs/src/content/docs/explanation/` | `tome-write-explanation` |

## See Also

- [Slash Commands](/reference/slash-commands) — Inventory of all 31 slash commands including `tome-classify`
- [Tome Writers](/reference/tome-write) — Reference for the four writer slash commands gated by this report
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — exercises slash-command installation via `deviate setup`
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
- [How-To intro](/how-to/intro) — operator-task quadrant
- [Explanation intro](/explanation/intro) — rationale and design choices quadrant
- [Tutorials intro](/tutorials/intro) — guided-learning quadrant