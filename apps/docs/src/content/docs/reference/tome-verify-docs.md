---
title: "Tome Verify Docs"
description: "The C6 verifier command — five-check cross-doc pass over writer outputs, with PASS/FAIL/boundary/recommended-files report."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Tome Verify Docs

The Tome C6 verifier runs five read-only checks against files that the C2-C5 writers produced for the current commit (or codebase) and emits a human-readable report with per-file PASS/FAIL entries, boundary violations, human-review items, and a recommended-files-to-commit list. The verifier does not modify files and does not auto-route back to writers.

## Surface

| Attribute | Value |
|---|---|
| Slash command | `tome-verify-docs` |
| Aliases | `tome-verify-docs`, `/tome-verify-docs`, `spec:verify-docs`, `spec.verify-docs`, `spec:tome-verify-docs`, `spec.tome-verify-docs` |
| Category | `deviatdd-tome-layer` |
| Version | `1.0.0` |
| Component | C6 (Tome Verifier) |
| Flow | FLOW-09 |
| Source file | `src/deviate/prompts/commands/tome-verify-docs.md` |
| Writes to | nothing (read-only) |

## Inputs

| Source | Required | How obtained |
|---|---|---|
| Updated docs in `apps/docs/src/content/docs/` | yes (otherwise `[NO-UPDATES]`) | filesystem scan since last verified SHA |
| `/tome-classify` classification report | yes | conversation context; request paste if absent |
| Commit diff for current commit | diff modes only | `git diff HEAD~1..HEAD` (or the diff the writer was given) |
| Changed test files | diff modes only | `git diff --name-only HEAD~1..HEAD -- 'tests/'` |
| Current source files | `codebase` mode only | filesystem read of files referenced in updated docs |
| `specs/_product/architecture.md`, `domain-model.md` | optional (semantic anchors) | filesystem read |

When `<user_input>` is empty AND no `/tome-classify` report is in context AND no updated docs are present, the verifier halts with `[NO-UPDATES] no files to verify — confirm that at least one writer has run`.

## Verification Modes

The classifier report's `mode` field selects the evidence source for the per-file checks.

| Mode | Evidence source |
|---|---|
| `default` | `git diff HEAD~1..HEAD` (previous commit) |
| `sha` | `git diff <sha>~1..<sha>` (specific commit) |
| `merge-base` | `git diff $(git merge-base HEAD main)..HEAD` (branch since divergence from main) |
| `working-tree` | `git diff` (uncommitted and staged changes) |
| `codebase` | filesystem read of `src/`, `tests/`, `specs/`; no `git diff` anchor — the working tree is the source of truth |

## Five Per-File Checks

Every updated file is run through these checks in order. Each check produces a `[PASS]` / `[FAIL]` / `[n/a]` entry in the report; skipping any check invalidates the report.

### Check 1 — Factual Consistency

Verify every claim referencing a code path, command, config key, flag, file path, or test name matches the relevant source-of-truth.

| Mode set | Source-of-truth |
|---|---|
| diff modes (`default` / `sha` / `merge-base` / `working-tree`) | `git diff` range + changed test files + current `src/` and `tests/` for unchanged references |
| `codebase` | current working tree read directly |

| Outcome | Condition |
|---|---|
| `[PASS] factual: <summary>` | Every concrete reference resolves to a current file, function, flag, command, or test |
| `[FAIL-FACTUAL] <file>: <claim> does not match <evidence>` | Any concrete reference is stale, renamed, removed, or fabricated |

### Check 2 — Path Correctness vs Diátaxis Quadrant

Verify the file's directory matches its `doc_type` frontmatter.

| `doc_type` | Required directory |
|---|---|
| `tutorial` | `apps/docs/src/content/docs/tutorials/` |
| `how-to` | `apps/docs/src/content/docs/how-to/` |
| `reference` | `apps/docs/src/content/docs/reference/` |
| `explanation` | `apps/docs/src/content/docs/explanation/` |

| Outcome | Condition |
|---|---|
| `[PASS] path: <quadrant-a> matches doc_type: <quadrant-b>` | File path is under the directory `doc_type:` claims |
| `[FAIL-PATH] <file> is under <quadrant-a>/ but doc_type claims <quadrant-b>` | File path is under one quadrant while `doc_type` claims another |

### Check 3 — Command/Config/API Accuracy

Verify every command, code block, config snippet, or API example runs, parses, and resolves as written.

| Source-of-truth | Example |
|---|---|
| `package.json` scripts | Starlight / Astro build commands |
| Starlight / Astro config | `astro.config.mjs`, `content.config.ts` |
| Current source code | CLI subcommands, flags, defaults |
| Runtime defaults | CLI `--help` output, Typer defaults |

| Outcome | Condition |
|---|---|
| `[PASS] command: <summary>` | Examples would work if copy-pasted; config keys and API signatures match current source; defaults match runtime |
| `[PASS] command: n/a (no code blocks in this file)` | File contains no code blocks |
| `[FAIL-COMMAND] <file>: <example> uses <identifier> which does not exist / has been renamed to <new>` | Any example uses a renamed, removed, or never-existed identifier; any default is stale; any code block has a syntax error |

### Check 4 — No Cross-Type Contamination

Verify the prose register matches the file's `doc_type`.

| `doc_type` | Expected register |
|---|---|
| `tutorial` | learning narrative + expected-result-per-step + verification |
| `how-to` | prerequisites + numbered steps + verification |
| `reference` | factual tables of flags / fields / commands |
| `explanation` | discursive prose with rationale / mental model / trade-offs |

| `doc_type` | Violation | Outcome |
|---|---|---|
| `tutorial` | large reference tables | `[FAIL-REGISTER] <file>: tutorial contains reference-style table; consider \`tome-write-reference\`` |
| `tutorial` | architecture / trade-off essay | `[FAIL-REGISTER] <file>: tutorial contains explanation-style essay; consider \`tome-write-explanation\`` |
| `how-to` | "by the end of this tutorial…" preamble | `[FAIL-REGISTER] <file>: how-to contains tutorial framing; consider \`tome-write-tutorial\`` |
| `how-to` | conceptual prose, no operator task | `[FAIL-REGISTER] <file>: how-to contains explanation-style content; consider \`tome-write-explanation\`` |
| `reference` | step-by-step operator instructions | `[FAIL-REGISTER] <file>: reference contains how-to steps; consider \`tome-write-how-to\`` |
| `reference` | learning narrative walk-through | `[FAIL-REGISTER] <file>: reference contains tutorial narrative; consider \`tome-write-tutorial\`` |
| `explanation` | numbered operator steps with verification | `[FAIL-REGISTER] <file>: explanation contains how-to steps; consider \`tome-write-how-to\`` |
| `explanation` | "by the end of this tutorial…" preamble | `[FAIL-REGISTER] <file>: explanation contains tutorial framing; consider \`tome-write-tutorial\`` |
| `explanation` | reference tables dominate | `[FAIL-REGISTER] <file>: explanation contains reference tables; consider \`tome-write-reference\`` |

### Check 5 — Valid Starlight Location

Verify the file is in a location Starlight will pick up.

| Outcome | Condition |
|---|---|
| `[PASS] starlight-location: <summary>` | Path matches `apps/docs/src/content/docs/<quadrant>/<name>.md`; quadrant is one of `tutorials` / `how-to` / `reference` / `explanation`; extension is `.md`; filename is kebab-case |
| `[FAIL] starlight-location: <summary>` | File is under `apps/docs/` but outside `src/content/docs/` (e.g., `apps/docs/public/`, `apps/docs/src/pages/`, `apps/docs/astro.config.mjs`); extension is not `.md`; filename uses uppercase or underscores |
| Boundary violation (escalates to `## Boundary Violations` section) | File is under one writer-claimed quadrant but its `doc_type` claims a different quadrant |

## Report Output Format

The verifier emits a single markdown block with these sections in this order:

| Section | Form |
|---|---|
| Header | `# Verification Report — <sha-or-mode>` |
| Summary line | `**Status**: <PASS-ONLY \| FAIL \| HUMAN-REVIEW>` |
| Counts | `**Files Verified**: <n>`, `**Files PASS**: <n>`, `**Files FAIL**: <n>`, `**Boundary Violations**: <n>` |
| Per-File Results | one `### <file> — <PASS \| FAIL>` block per updated file, alphabetical order; five `[PASS\|FAIL]` sub-bullets per block |
| Boundary Violations | bullet list of every Check 2 FAIL and Check 4 register failure |
| Human-Review Items | bullet list of findings requiring developer judgment |
| Recommended Files to Commit | bullet list of PASS-only files; reads `None — human review required before commit` when status is `HUMAN-REVIEW` |

### Status Line

| Status | Condition |
|---|---|
| `PASS-ONLY` | Every updated file passed all five checks; no boundary violations; recommended-files list is non-empty and includes every updated file |
| `FAIL` | At least one file has one or more FAIL findings on Checks 1-5; recommended-files list excludes those files |
| `HUMAN-REVIEW` | The verifier detected an ambiguous finding that cannot be resolved by evidence alone (e.g., `/tome-classify` confidence < 0.5, conflicting `doc_type` vs path the developer must adjudicate); recommended-files list is empty |

### Per-File Block

The first line of each section carries the overall verdict (`PASS` or `FAIL`). The five sub-bullets are always emitted, in check order, with `[PASS]` or `[FAIL]` prefix — even when the file is overall PASS — so the developer can see every check ran. When a check is not applicable (e.g., Check 3 on a file with no code blocks), the sub-bullet reads `[PASS] command: n/a (no code blocks in this file)`.

### Recommended Files to Commit

| Condition | Outcome |
|---|---|
| File overall verdict is `PASS` | listed |
| File has any FAIL finding, boundary violation, or unresolved `[HUMAN-REVIEW]` item | excluded |
| Report status is `HUMAN-REVIEW` | list reads `None — human review required before commit` |

## Boundary Rules

The verifier is read-only and never auto-routes. These rules are surface-level invariants enforced across every verification pass.

| Rule | Behaviour |
|---|---|
| No writes to `apps/docs/`, `specs/`, `src/`, or `tests/` | The only output is the verification report |
| No auto-routing to writers | On FAIL or boundary violation, the verifier halts and surfaces the finding; the developer re-runs the relevant writer manually with updated evidence |
| No `<judge_feedback>` injection | v1 ships with no machine-parseable feedback pattern (per `specs/_product/architecture.md:20`) |
| Action enum reconciliation | The action values (`create`, `update`, `no-change`, `human-review`, `setup-required`) and `doc_type` values (`tutorial`, `how-to`, `reference`, `explanation`) must match the literal strings used by C1 and C2-C5; drift between this prompt and C1/C2-C5 prompts is itself a FAIL item |
| Five-check coverage | Every verification pass MUST cover all five checks — skipping any check invalidates the report |

Example invocation:

```
/tome-verify-docs
```

## Source-of-Truth

| Attribute | Location |
|---|---|
| Source file | `src/deviate/prompts/commands/tome-verify-docs.md` |
| C6 component declaration | `specs/_product/architecture.md` §3.3 |
| C2-C5 → C6 contract schema | `specs/_product/architecture.md` §4.2 |
| Data ownership boundary | `specs/_product/architecture.md` §5 |
| Flow traceability | `specs/_product/architecture.md` §7 (C6 → FLOW-09) |
| `VerificationReport` entity | `specs/_product/domain-model.md` (`pass_items`, `fail_items`, `boundary_violations`, `recommended_files`) |

## See Also

- [Slash Commands](/reference/slash-commands) — inventory of all 31 commands; the row for `tome-verify-docs` lists aliases, category, and version
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — operator task that exercises the slash-command installer end-to-end
- [How-To intro](/how-to/intro) — operator-task quadrant
- [Explanation intro](/explanation/intro) — rationale and design choices quadrant