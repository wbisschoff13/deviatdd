---
title: "Tome Writers"
description: "Reference for the four Tome writer slash commands — quadrant confinement, per-writer self-verify, output frontmatter schema, and failure modes."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Tome Writers

The four quadrant-disciplined writer slash commands (Tome C2–C5) that produce one Starlight page each under `apps/docs/src/content/docs/`, each confined to its assigned Diátaxis quadrant, each emitting valid Tome frontmatter, each running a built-in self-verify before delivery.

## Writer Inventory

| Command | Tier | Quadrant | Target Directory | Version | Source |
|---|---|---|---|---|---|
| `tome-write-tutorial` | C2 | tutorial | `apps/docs/src/content/docs/tutorials/` | `1.0.0` | `src/deviate/prompts/commands/tome-write-tutorial.md` |
| `tome-write-how-to` | C3 | how-to | `apps/docs/src/content/docs/how-to/` | `1.0.0` | `src/deviate/prompts/commands/tome-write-how-to.md` |
| `tome-write-reference` | C4 | reference | `apps/docs/src/content/docs/reference/` | `1.0.0` | `src/deviate/prompts/commands/tome-write-reference.md` |
| `tome-write-explanation` | C5 | explanation | `apps/docs/src/content/docs/explanation/` | `1.0.0` | `src/deviate/prompts/commands/tome-write-explanation.md` |

All four carry `category: deviatdd-tome-layer` in their YAML frontmatter and ship six aliases each (the bare name, `/<name>`, the `spec:write-<doc>`, `spec.write-<doc>`, `spec:tome-write-<doc>`, and `spec.tome-write-<doc>` forms).

## Writer Prompt Frontmatter

The YAML header each writer `.md` carries under `src/deviate/prompts/commands/`. Parsed by `src/deviate/core/commands.py::discover_commands` and the installer at `src/deviate/cli/__init__.py::_install_commands_to_agents`.

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | `<file-stem>` | Slash-command identifier matching the file stem |
| `description` | `string` | `""` | Single-sentence purpose shown in agent autocomplete |
| `category` | `enum` | `deviatdd-tome-layer` | Routing label for `assembly.py::_LAYER_MAP` and command indexing |
| `version` | `semver` | `1.0.0` | Slash-command template version in semver form |
| `aliases` | `list[string]` | `[]` | Alternate invocations accepted by agent autocomplete |

The four writers add no `layer` field (they map to the tome-layer category, not the macro/meso/micro assembly layers).

## Output Frontmatter Schema

Every markdown file emitted by C2–C5 MUST begin with this YAML block. Field order is fixed for parser compatibility with the extended `docsSchema()` produced by C7's `src/content.config.ts`. Source: `specs/_product/architecture.md:70-83`.

| Field | Type | Default | Description |
|---|---|---|---|
| `title` | `string` | `""` | Sidebar label; ≤80 chars, ≤40 ideal; surface-name driven |
| `description` | `string` | `""` | One-sentence summary; ≤160 chars |
| `doc_type` | `enum` | `""` | One of `tutorial` \| `how-to` \| `reference` \| `explanation`; MUST match the quadrant the file lives in |
| `status` | `enum` | `draft` | One of `draft` \| `reviewed`; new pages emit `draft` |
| `last_verified_at` | `date` | `null` | ISO-8601 `YYYY-MM-DD`; date the content was last validated against current code |
| `verified_sha` | `string` | `null` | Commit SHA the examples and tables were validated against; short or full form accepted |
| `related_issues` | `list[string]` | `[]` | Issue IDs this page addresses (e.g. `ISS-123`, `ISS-ADH-011`); empty list allowed |

The `doc_type` value MUST match the quadrant directory the file lives in: `tutorial` only inside `tutorials/`, `how-to` only inside `how-to/`, `reference` only inside `reference/`, `explanation` only inside `explanation/`. Drift between `doc_type` and parent path is a C6 verifier finding.

Example frontmatter fields for a freshly created page (see the schema table above for the full block):

```
doc_type: reference
status: draft | reviewed
verified_sha: <commit-SHA>
```

## Per-Writer Self-Verify

Each writer runs these checks in order before emitting. Any failure aborts emission and surfaces a one-line message. Source: `specs/_product/architecture.md:66-70` and the `<self_verify>` block of every writer prompt.

| # | Check | Failure Response |
|---|---|---|
| 1 | Resolved `<target_file>` is under the writer's assigned quadrant | Emit `[REJECT] <writer>: target '<path>' is outside the <quadrant>/ quadrant` and halt |
| 2 | Frontmatter `doc_type` equals the writer's quadrant value | Halt with one-line frontmatter failure |
| 3 | All seven frontmatter fields are present and non-empty (`related_issues` may be `[]`) | Halt with one-line frontmatter failure |
| 4 | Title is sidebar-friendly (≤40 chars ideal, distinct from siblings) and the slug is descriptive kebab-case | Emit navigation failure and halt |
| 5 | Content stays in the writer's doc_type register (no step-by-step instructions in C4, no tutorial narrative in C3, etc.) | Flag back to `/tome-classify` for re-classification; halt |
| 6 | `## See Also` section is present with cross-quadrant links | Halt with one-line failure |
| 7 | Tables use `Name | Type | Default | Description` columns (or analogous) with no omitted columns | Halt with one-line failure |
| 8 | Code examples ≤5 lines and validated against `verified_sha` | Halt with one-line failure |
| 9 | Existing target file was read first and all still-valid rows are preserved (updates only) | Halt with surface diff to user |
| 10 | Grouping decision applied if quadrant already has 10+ single-entry pages on related surfaces | Emit `[CONSOLIDATED]` or family-directory decision and continue |

Checks 1, 2, 3, 6, 9 are blocking. Check 5 routes back to the classifier for re-routing rather than auto-correcting register drift.

## Quadrant Confinement

The four writers write to exactly one path family each. Every other path is out of scope.

| Path | Allowed Writer |
|---|---|
| `apps/docs/src/content/docs/tutorials/*.md` | `tome-write-tutorial` (C2) |
| `apps/docs/src/content/docs/how-to/*.md` | `tome-write-how-to` (C3) |
| `apps/docs/src/content/docs/reference/*.md` | `tome-write-reference` (C4) |
| `apps/docs/src/content/docs/explanation/*.md` | `tome-write-explanation` (C5) |
| `apps/docs/src/content/docs/index.md` | none (C7 setup territory) |
| `apps/docs/src/content/docs/_meta/**` | none (C7 setup territory) |
| `apps/docs/src/content.config.ts` | none (C7 setup territory) |
| `apps/docs/package.json`, `apps/docs/astro.config.mjs` | none (C7 setup territory or out of scope) |
| `src/deviate/**`, `tests/**`, `specs/**` | none (read-only by C2–C5) |

A writer that needs to touch a different quadrant emits a `[REJECT]` boundary violation and halts. Auto-routing to another writer is forbidden.

## Input Contract

| Argument | Required | Default | Meaning |
|---|---|---|---|
| `<target_file>` | yes | derived from `/tome-classify` report | Relative path under `apps/docs/src/content/docs/<quadrant>/` where the page will be written |
| classification report excerpt | no | prior context | Capability row from `/tome-classify` (`capability`, `evidence`, `audience`, `doc_type`, `action`, `target_file`, `confidence`); if absent, the writer requests it from the user |

If `<target_file>` is empty or unpopulated, the writer halts with `MISSING_TARGET_FILE` and does not infer a path from prior conversation.

## Classification Report Contract

The report C2–C5 consume, emitted by C1 (`tome-classify`). Source: `specs/_product/architecture.md:122-138`.

| Field | Type | Description |
|---|---|---|
| `capability` | `string` | User-facing capability being documented |
| `evidence` | `string` | Files, commits, or specs justifying the doc action |
| `audience` | `enum` | One of `user` \| `operator` \| `contributor` \| `internal` |
| `doc_type` | `enum` | One of `tutorial` \| `how-to` \| `reference` \| `explanation` |
| `action` | `enum` | One of `create` \| `update` \| `no-change` \| `human-review` \| `setup-required` |
| `target_file` | `path` | Relative path under `apps/docs/src/content/docs/` |
| `confidence` | `float` | `0.0`–`1.0`; values `< 0.5` route to `[HUMAN-REVIEW]` and block writers |

A writer only fires when C1's capability table contains a row whose `doc_type` matches the writer's quadrant AND whose `action` is `create` or `update`.

## Failure Modes

| Condition | Emit | Writer Response |
|---|---|---|
| Target outside writer's quadrant | `[REJECT] <writer>: target '<path>' is outside the <quadrant>/ quadrant` | Halt; flag back to `/tome-classify` |
| Tutorial-style content requested from C4/C5 (learning narrative walking a beginner) | register violation | Flag back to `/tome-classify` for re-classification to `tome-write-tutorial` |
| How-to-style content requested from C4/C5 (operator task steps with prereqs + verification) | register violation | Flag back to `/tome-classify` for re-classification to `tome-write-how-to` |
| Explanation-style content requested from C3/C4 (rationale, mental models, trade-offs) | register violation | Flag back to `/tome-classify` for re-classification to `tome-write-explanation` |
| `apps/docs/` does not exist | `[SETUP-REQUIRED]` | Halt; point at `/tome-setup` |
| C1 report confidence `< 0.5` on targeted capability | `[HUMAN-REVIEW]` | Halt; wait for human confirmation |
| Existing target file has unmergeable structure | preserve-valid-content check failure | Halt; surface diff to user |
| New page has no inbound links (orphan) | `[DEAD-LINK]` | Halt; request a parent to link in |
| Quadrant intro describes a different IA than the new page fits | `[INTRO-MISMATCH]` | Continue writing; mark intro for the next pass |
| Missing or empty `<target_file>` argument | `MISSING_TARGET_FILE` | Halt; do not infer a path from prior conversation |

## See Also

- [Slash Commands](/reference/slash-commands) — full inventory of all 31 shipped commands including the four writers
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
- [How-To intro](/how-to/intro) — operator-task quadrant
- [Explanation: why a Python-only prompt runtime](/explanation/python-only-architecture) — grounds why the writer prompts live as Python package resources