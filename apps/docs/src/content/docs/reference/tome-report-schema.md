---
title: "tome-classify Report Schema"
description: "Data schema for the Tome C1 classification report: capability table columns, action enum, status enum, gate precedence, and section structure."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-011
---

# tome-classify Report Schema

The data schema emitted by `/tome-classify` (Tome C1) and consumed by the four writer slash commands (`tome-write-tutorial`, `tome-write-how-to`, `tome-write-reference`, `tome-write-explanation`). Source: `src/deviate/prompts/commands/tome-classify.md` `<classification_report_schema>` block and `specs/_product/architecture.md:122-138` §4.1.

## Status Enum

The `Status` line at the top of the report resolves to exactly one of four values. The value is derived by the gate-precedence rule on the action column; first match wins.

| Value | Type | Default | Description |
|---|---|---|---|
| `setup-required` | `enum` | n/a | ANY row carries `action: setup-required`; halt and point at `/tome-setup` |
| `human-review` | `enum` | n/a | ANY row carries `action: human-review`; block all writers until human sign-off |
| `no-change` | `enum` | n/a | ALL rows carry `action: no-change`; skip writers and verifier (terminal gate) |
| `mixed` | `enum` | n/a | Otherwise (mixed `create` / `update` rows); developer runs the writer indicated by `doc_type` per row |

## Capability Table Columns

The seven columns of the `## Capabilities` table. An empty capability table is invalid output; rows with `action = setup-required` carry the literal lowercase `null` in `target_file`.

| Column | Type | Default | Description |
|---|---|---|---|
| `capability` | `string` | `null` | User-facing capability exposed or modified; one row per capability |
| `evidence` | `string` | `null` | Verbatim file paths and/or commit messages that justify the row; anchored to source, no speculation |
| `audience` | `enum` | `null` | One of `developer`, `operator`, `end-user`, `contributor`; multiple values comma-separated |
| `doc_type` | `enum` | `null` | One of `tutorial`, `how-to`, `reference`, `explanation`; drives which writer runs |
| `action` | `enum` | `null` | One of `create`, `update`, `no-change`, `human-review`, `setup-required`; drives gate behavior |
| `target_file` | `path` \| `null` | `null` | Repo-relative path under `apps/docs/src/content/docs/<quadrant>/`; literal `null` when action is `setup-required` |
| `confidence` | `decimal` | `null` | Closed `[0.0, 1.0]`; rows with `< 0.5` MUST carry `action = human-review` |

## Action Enum

Each capability row carries exactly one action from the closed five-value enum below. Drift between this enum and the verifier (C6) enum is a verifier-level finding.

| Value | Type | Default | Description |
|---|---|---|---|
| `create` | `enum` | n/a | New doc required; no existing page at `target_file`; developer runs the writer indicated by `doc_type` |
| `update` | `enum` | n/a | Existing doc at `target_file` requires revision; developer runs the writer against the existing page |
| `no-change` | `enum` | n/a | Diff is internal-only; no public docs affected; skip writers and `/tome-verify-docs` — terminal gate |
| `human-review` | `enum` | n/a | Classifier is uncertain on `doc_type`, `target_file`, or quadrant collision; block writers until developer confirms intent; verifier does not run |
| `setup-required` | `enum` | n/a | `apps/docs/` is absent in the target repo; halt all downstream work; point at `/tome-setup`; verifier does not run |

## Gate Precedence

The overall `Status` line is derived by evaluating the action column with these top-down rules; the first match wins.

| Order | Condition | Type | Resulting status |
|---|---|---|---|
| 1 | ANY row carries `setup-required` | condition | `setup-required` |
| 2 | ANY row carries `human-review` | condition | `human-review` |
| 3 | ALL rows carry `no-change` | condition | `no-change` |
| 4 | Otherwise (mixed `create` / `update` rows) | fallback | `mixed` |

## Report Sections

The report is a single markdown block with exactly three sections in this order, prefixed by the overall `Status` line.

| Section | Required | Type | Content |
|---|---|---|---|
| `**Status**: <...>` line | yes | `string` | One of `no-change`, `human-review`, `setup-required`, `mixed`; reflects gate-precedence outcome |
| `## Summary` | yes | `string` | One-paragraph change summary: what changed, why it matters for docs, which audiences are affected |
| `## Capabilities` | yes | `table` | Capability table with the seven columns above; MUST contain at least one row |
| `## No-Touch List` | yes when existing pages are candidate targets | `list[string]` | Files that must NOT be modified; existing valid content to preserve; otherwise `None — first-run classification` |

Example minimal report skeleton:

```
# Classification Report — 8daa502

**Status**: mixed

## Summary
<one-paragraph change summary>

## Capabilities
| capability | evidence | audience | doc_type | action | target_file | confidence |
|------------|----------|----------|----------|--------|-------------|------------|
| <name> | <paths> | developer | reference | update | reference/tome-report-schema.md | 0.9 |

## No-Touch List
- <files that must not be modified>
```

## See Also

- [tome-classify Modes](/reference/tome-classify-modes) — Input modes, action enum, gate behaviors, confidence range, and DocType-to-quadrant mapping (operational behavior)
- [Tome Writers](/reference/tome-write) — Reference for the four writer slash commands gated by this report
- [Slash Commands](/reference/slash-commands) — Inventory of all 31 shipped slash commands including `tome-classify`
- [Reference intro](/reference/intro) — Navigation map for the reference quadrant
- [Explanation: why a Python-only prompt runtime](/explanation/python-only-architecture) — Grounds why the classifier prompt lives as a Python package resource under `src/deviate/prompts/commands/`