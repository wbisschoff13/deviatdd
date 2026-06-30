---
title: "Tome Setup Command"
description: "Reference for /tome-setup — idempotent Starlight scaffold under apps/docs/: four quadrant dirs, index.md, _meta/, content.config.ts extending docsSchema()."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Tome Setup Command

The Tome C7 slash command that idempotently scaffolds a Starlight docs site under `apps/docs/` with the four Diátaxis quadrant directories, `index.md`, `_meta/`, `src/content.config.ts` extending `docsSchema()` with the Tome frontmatter fields, and (unless suppressed) a four-page starter set. Source prompt at `src/deviate/prompts/commands/tome-setup.md`; contract at `specs/_product/architecture.md:105-117` (C7) and §3.4 (FLOW-10).

## Command Identity

| Field | Value |
|---|---|
| `name` | `tome-setup` |
| `category` | `deviatdd-tome-layer` |
| `version` | `1.0.0` |
| `layer` | `null` (not an assembly phase) |
| `aliases` | `tome-setup`, `/tome-setup`, `spec:setup`, `spec.setup`, `spec:tome-setup`, `spec.tome-setup` |
| Source prompt | `src/deviate/prompts/commands/tome-setup.md` |
| Architecture contract | `specs/_product/architecture.md:105-117` |
| Flow ref | FLOW-10 |

## Input Contract

| Argument | Required | Default | Description |
|---|---|---|---|
| `--no-starter-set` | no | `false` | Suppress the starter-set seed step on first run; scaffold + dirs + config still materialize |
| `<target_repo_root>` | no | `process.cwd()` | Override the working directory for `apps/docs/` resolution; default is the directory in which the developer ran `/tome-setup` |

If `apps/docs/` already exists in the target root, the developer is informed and the run is treated as an idempotent re-run (no diff against committed state).

## Scaffold Steps

Five ordered steps. Each step has a first-run action, a re-run policy, and a postcondition.

| # | Step | First-run action | Re-run policy | Postcondition |
|---|---|---|---|---|
| 1 | Scaffold `apps/docs/` with Starlight | Emit `npm create astro@latest -- --template starlight apps/docs` plus `cd apps/docs && npm install` (developer-confirmed or agent-mediated) | SKIP — `apps/docs/` already exists | `apps/docs/package.json` and `apps/docs/astro.config.mjs` both exist with `@astrojs/starlight` declared |
| 2 | Create quadrant directories | `mkdir -p apps/docs/src/content/docs/{tutorials,how-to,reference,explanation,_meta}` | ADD MISSING ONLY — each absent dir gets `mkdir -p`; existing dirs untouched | All five dirs exist |
| 3 | Add `src/content.config.ts` | Write the canonical block extending `docsSchema()` with the five Tome frontmatter fields | PATCH ONLY — add any missing Tome field declarations, preserve unrelated config, never overwrite | The file declares all five Tome-specific fields |
| 4 | Add `index.md` and `_meta/*.yml` | Create `index.md` (landing page) plus four per-quadrant `_meta/<quadrant>.yml` sidebar files | SKIP if present — never overwrite a developer's customized file | `index.md` and four `_meta/*.yml` files exist |
| 5 | Seed starter set | Write one file per quadrant (explanation, reference, how-to, tutorial) | SKIP if present — never overwrite developer-owned files; treat as developer-owned when `related_issues` is non-empty | Four starter files exist, each with `status: draft` and `related_issues: []` |

Step 5 is also skipped (regardless of state) when `--no-starter-set` is passed.

## Quadrant Directory Names

The four quadrant directories are exactly these names. Drift between these names and the writers' (C2-C5) hardcoded targets is a C6 verifier finding. Note: `how-to` is singular with a hyphen, not `how-tos`.

| Directory | Writer | Quadrant enum value |
|---|---|---|
| `apps/docs/src/content/docs/tutorials/` | `tome-write-tutorial` (C2) | `tutorial` |
| `apps/docs/src/content/docs/how-to/` | `tome-write-how-to` (C3) | `how-to` |
| `apps/docs/src/content/docs/reference/` | `tome-write-reference` (C4) | `reference` |
| `apps/docs/src/content/docs/explanation/` | `tome-write-explanation` (C5) | `explanation` |

## Frontmatter Schema Fields

`src/content.config.ts` extends `docsSchema()` with the five Tome-specific frontmatter fields below. Drift between this schema and the markdown writers (C2-C5) is a Starlight-side validation failure detected at build time.

| Field | Type | Allowed values | Source-of-truth |
|---|---|---|---|
| `doc_type` | `enum` | `tutorial` \| `how-to` \| `reference` \| `explanation` | `specs/_product/architecture.md` (DocType enum, §`data-model`) |
| `status` | `enum` | `draft` \| `reviewed` | `specs/_product/architecture.md` (writer frontmatter schema) |
| `last_verified_at` | `string` (ISO date) | `YYYY-MM-DD` | `specs/_product/architecture.md` (writer frontmatter schema) |
| `verified_sha` | `string` | commit SHA (full or short form) | `specs/_product/architecture.md` (writer frontmatter schema) |
| `related_issues` | `array<string>` | issue IDs (`ISS-XXX`, `ISS-ADH-XXX`); empty list allowed | `specs/_product/architecture.md` (writer frontmatter schema) |

The writers (C2-C5) additionally emit the two Starlight-default fields inherited from `docsSchema()`: `title` (≤ 80 chars) and `description` (≤ 160 chars).

Canonical `extend` shape (truncated; full block at `src/deviate/prompts/commands/tome-setup.md` Step 3):

```ts
extend: (ctx) => ctx.z.object({
  doc_type: ctx.z.enum(['tutorial','how-to','reference','explanation']),
  status: ctx.z.enum(['draft','reviewed']),
  last_verified_at: ctx.z.string().date(),
```

## Starter Set

Four starter files, one per quadrant. Each carries `status: draft` and `related_issues: []` so the developer can recognize and replace them. The `starter-` filename prefix is reserved; the C6 verifier treats `starter-*` files as replaceable boilerplate unless `related_issues` is non-empty.

| Path | Quadrant | Body shape |
|---|---|---|
| `apps/docs/src/content/docs/explanation/starter-architecture.md` | `explanation` | 3-5 paragraphs framing why a docs system needs Diátaxis; explicit "We chose X because Y, accepting Z" trade-off framing |
| `apps/docs/src/content/docs/reference/starter-config.md` | `reference` | Single table of the five Tome frontmatter fields with columns `field \| type \| default \| description` |
| `apps/docs/src/content/docs/how-to/starter-first-task.md` | `how-to` | `## Prerequisites`, `## Steps` (3 numbered steps each with `Expected result:`), `## Verification` |
| `apps/docs/src/content/docs/tutorials/starter-first-run.md` | `tutorial` | `## Prerequisites`, `## Step 1 — <verb>`, `## Step 2 — <verb>`, `## Verification`, `## Next Steps` |

The `--no-starter-set` flag suppresses step 5 entirely on first run; on re-runs the starter set is never touched regardless of the flag.

## Readiness Signals

The setup log ends with exactly one of these three signals. The signal is the last line of every setup run.

| Signal | Meaning | When emitted |
|---|---|---|
| `[READY]` | `apps/docs/src/content/docs/` exists with quadrant dirs, `index.md`, `_meta/`, `content.config.ts`, and (unless opted out) the starter set | All five steps completed or skipped because already done |
| `[READY-NO-STARTER]` | Same as `[READY]` but the starter set was suppressed via `--no-starter-set` | Steps 1-4 completed; step 5 suppressed |
| `[BLOCKED]` | Setup halted before reaching `[READY]`; remediation message present | Any step's precondition failed (developer declined Starlight scaffold, dependency conflict, permissions error) |

After `[READY]` or `[READY-NO-STARTER]`, `/tome-classify` (C1) is unblocked and may begin proposing target files. After `[BLOCKED]`, C1 continues to emit `setup-required` for every row and halts.

## Idempotency Contract

| Trigger | Behavior |
|---|---|
| `apps/docs/` absent | First-run path: execute steps 1-5 linearly in order, respecting the `--no-starter-set` flag at step 5 |
| `apps/docs/` present | Re-run path: skip step 1; steps 2-4 are ADD-MISSING-ONLY or SKIP-IF-PRESENT; step 5 is always SKIP-IF-PRESENT (or suppressed by `--no-starter-set`) |
| Starlight dependency conflict | Halt with `[BLOCKED]` and a remediation message; roll back any partial scaffold by removing `apps/docs/` and re-emitting the bootstrap command |

Re-runs MUST produce zero diff against committed state.

## Out-of-Scope

C7 explicitly does NOT write to the following paths and operations — they are writer, verifier, or developer territory.

| Path / Operation | Owner |
|---|---|
| `apps/docs/src/content/docs/<quadrant>/*.md` (post-starter) | C2-C5 writers (`tome-write-tutorial`, `tome-write-how-to`, `tome-write-reference`, `tome-write-explanation`) |
| Cross-doc verification over C2-C5 outputs | `tome-verify-docs` (C6) |
| Calling `/tome-classify` after setup | Developer invokes C1 separately |
| `specs/constitution.md`, `specs/_product/architecture.md`, `specs/_product/domain-model.md` | Read-only seeds; never modified by setup |
| `src/deviate/**` (any DeviaTDD-internal path) | Setup runs in the target repo, not in DeviaTDD's own repo (per `specs/_product/architecture.md:18`) |
| Running `npm install` automatically in agent-mediated mode | Developer runs the bootstrap command and confirms |

## Source Anchors

| Anchor | Purpose |
|---|---|
| `specs/_product/architecture.md:105-117` | C7 component declaration, scaffold steps, idempotency contract, C1 precondition |
| `specs/_product/architecture.md` §3.4 | FLOW-10 — idempotency contract, scaffold steps, starter set, precondition for C1 |
| `specs/_product/architecture.md` §4.3 | C7 → C1 contract: `apps/docs/src/content/docs/` existence gates C1 |
| `specs/_product/architecture.md` §5 | Data ownership: C7 is the only writer of `content.config.ts`, `index.md`, `_meta/` |
| `specs/_product/domain-model.md` | `StarlightQuadrant` enum (tutorials, how-to, reference, explanation); `TomeFrontmatter` entity |

## See Also

- [Slash Commands](/reference/slash-commands) — full inventory of all 31 shipped commands including `tome-setup`
- [Tome Writers](/reference/tome-write) — C2-C5 writer reference (downstream of `tome-setup`)
- [Tome Classify Modes](/reference/tome-classify-modes) — C1 classifier modes, including the `setup-required` halt triggered when C7 has not run
- [Tome Report Schema](/reference/tome-report-schema) — classification report contract that C1 emits and C7's readiness unblocks
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
- [How-To intro](/how-to/intro) — operator-task quadrant
- [Explanation: why a Python-only prompt runtime](/explanation/python-only-architecture) — grounds why setup runs in the target repo, not in `src/deviate/`
