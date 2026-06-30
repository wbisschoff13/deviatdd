---
title: "Run the /deviate-review phase"
description: "Run HITL Gate 3 — single-pass PR review across Security, Clean Code, Pragmatism, Idiomacy, Constitution, PRD Alignment, and Flow Coverage; optionally persist the report."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-004
  - ISS-001-002
---

# Run the /deviate-review phase

This how-to covers `/deviate-review` — the meso-layer HITL Gate 3 that runs after every task in every issue-scoped `tasks.jsonl` ledger has reached a terminal state (`COMPLETED` or `FAILED`) and all DAG dependencies are satisfied. The slash command performs a fast single-pass scan (V4 Flash) over the merged PR's raw text diff **and** a tree-sitter–derived structured AST diff, evaluating seven domains in parallel: Security, Clean Code, Pragmatism, Idiomacy, Constitution, PRD Alignment, and Flow Coverage. Findings surface as chat text for human judgment; the optional `deviate review post` command persists the report to `.deviate/review/reports/` for archival. After review, the natural next action is to merge the feature branch into `main` (or run [`/deviate-pr`](/how-to/pr) if you have not yet opened the PR).

## Prerequisites

- **All task entries in every issue-scoped `tasks.jsonl` ledger have reached terminal states** — HITL Gate 3 is the *micro-to-idle* boundary, enforced by the human reviewer (not by `deviate review pre`). If even one task is still `IN_PROGRESS` when review runs, the diff under review is incomplete and the seven-domain scan will reflect a half-built feature. Confirm with `grep -RE '"status":\s*"(IN_PROGRESS|PENDING)"' specs/<epic>/issues/ || echo OK`.
- **A clean feature branch with commits ahead of `main`** — `deviate review pre` computes `git merge-base <base>..<target>` and only emits a non-empty diff if the branch has commits `main` does not. If the branch is already merged, the slash command emits `SKIP: no changes since {base_branch}` and exits.
- **`specs/constitution.md` present at the repo root** — the Constitution domain of the scan quotes the `Architectural Principles` and `Testing Protocols` sections verbatim. If the constitution is missing, the slash command continues with a `no constitution to check` note but the Constitution domain is scored N/A.
- **A PRD file reachable from the active branch** — the slash command resolves `prd_path` with epic priority (`specs/<epic>/prd.md`) over the adhoc fallback (`specs/adhoc/prd.md`). If both are absent, the PRD Alignment domain is skipped. Branch-name slug drives epic lookup: a branch named `epic/007-tome-how-to` resolves to `specs/007-tome-how-to/prd.md`.
- **`specs/_product/` (optional but recommended)** — the Flow Coverage domain reads `specs/_product/flows/index.md`, the parent issue's `flow_refs` in `specs/issues.jsonl`, and `specs/_product/release-next.md` to verify the diff preserves each named flow's Trigger and Happy Path. When `specs/_product/` is absent, the slash command notes `PRODUCT_LAYER_ABSENT` in the Compliance Matrix and skips that domain.
- **The fast-tier model available for the orchestrating agent** — the meso layer routes review to V4 Flash per `specs/DeviaTDD-architecture.md` §4 and `src/deviate/state/config.py::resolve_phase_model`. Per-phase overrides go in `.deviate/config.toml` under `[models].review`.
- **A description of the PR for context** — pass the same problem statement threaded through [`/deviate-explore`](/how-to/explore), [`/deviate-research`](/how-to/research), [`/deviate-prd`](/how-to/prd), and [`/deviate-shard`](/how-to/shard) so the seven-domain scan stays anchored.

## Steps

### 1. Confirm every task has reached a terminal state

Before invoking the slash command, verify the micro-layer has finished. The pre-script does not check task state — that gate is enforced by the human reviewer running `/deviate-review` at the right moment. If even one task is still `IN_PROGRESS`, the diff under review will be incomplete.

```bash
# Confirm no IN_PROGRESS or PENDING tasks remain across all issues in the epic
grep -RE '"status":\s*"(IN_PROGRESS|PENDING)"' specs/<epic>/issues/ || echo "OK — all tasks terminal"

# Confirm the merge-base has commits ahead of main
git log --oneline main..HEAD | head -5
```

If any task is non-terminal, halt and complete the red→green→refactor→judge loop before running review.

### 2. Run `deviate review pre` to inspect the JSON contract

The slash command invokes `deviate review pre` internally as its first step, but you can run it directly to inspect the structured diff before launching the agent. This is useful when you want to scope a complex review manually.

```bash
# Default base branch is main; target defaults to HEAD (the current branch)
deviate review pre

# Explicit base + target for a self-contained review on a non-default branch
deviate review pre --base main --branch feature/007-tome-how-to
```

The contract contains `status`, `diff` (raw unified diff against merge-base), `structured_diff` (per-file symbol-level change metadata for ALL changed files), `structured_diff_markdown` (pre-rendered compact markdown table for direct inclusion in LLM prompts), `constitution_path` (or `constitution_warning: true` if absent), `prd_path` (or `prd_warning: true` if absent), `base_branch`, `report_exists` (boolean — true if `.deviate/review/reports/` already has content), and `timestamp` (ISO-8601 UTC).

If `diff` is empty, the branch has not diverged from `main` — the slash command will emit `SKIP: no changes since {base_branch}` and exit. If `structured_diff` is empty but `diff` is not, tree-sitter failed to parse the diff (e.g., unsupported language); the review proceeds on the raw text diff only.

### 3. Run `/deviate-review` with the PR description

The slash command is the single primary action for this how-to. Pass a short PR description so the scan's findings can reference it; the slash command also reads `constitution_path` and `prd_path` from the pre-script contract automatically.

```bash
/deviate-review <pr-description>
```

If the feature branch is named `epic/<slug>` and the matching `specs/<slug>/prd.md` exists, the slash command picks it up via the pre-script's `_resolve_prd` helper. To review a branch that is not currently checked out, pass the branch name explicitly:

```bash
/deviate-review --base main --branch feature/007-tome-how-to <pr-description>
```

The slash command orchestrates four internal steps: the pre-script (step 2 above), the seven-domain single-pass scan (step 4), the chat-text surface (step 5), and the optional apply step (step 6). You do not invoke these sub-steps directly.

### 4. Read the seven-domain findings

The slash command evaluates every domain in a single pass and emits findings to chat text. For each domain, it produces Positive Patterns, Critical Issues (with severity `[HIGH]`/`[MEDIUM]`/`[LOW]`), Suggestions, and Opportunities. Reference specific `| Language | Kind | Name | Change |` rows from the structured diff table in the analysis. For the Flow Coverage domain, cite the specific `FLOW-XX` ID and the flow definition file (e.g., `specs/_product/flows/flows-tome.md:42`).

The seven domains are:

1. **Security** — hardcoded secrets, command-injection via subprocess, permission gaps, unreviewed new dependencies, path traversal from structured diff paths.
2. **Clean Code** — dead code (removed symbols without call-site cleanup), duplicate definitions across task boundaries, unused imports, cyclomatic complexity spikes, naming convention violations.
3. **Pragmatism** — over-engineered solutions, unnecessary breaking changes from renames, missing edge case coverage, principle-of-least-surprise violations.
4. **Idiomacy** — per-language idiom violations detected via the structured diff: Python list comprehensions vs `map`/`filter`, TypeScript strict null checks, Rust ownership patterns, Go error handling, SQL JOIN patterns.
5. **Constitution** — append-only ledger integrity (`specs/issues.jsonl`, `tasks.jsonl`), clean `COMPLETED` terminal states, no orphaned lines, no HITL gate bypasses, no Git Isolation Principle violations, no Tamper Guard breaches, no model tiering violations.
6. **PRD Alignment** — `added` symbols traceable to PRD requirements, no scope creep, no missing features (`removed` symbols that should have been `modified`), AC coverage gaps.
7. **Flow Coverage** — for each `FLOW-XX` named in the parent issue's `flow_refs`, verify the flow still exists in `specs/_product/flows/index.md` and the diff preserves or extends the flow's Trigger and Happy Path. A `removed` symbol that closes off a flow's user-visible capability = `[CRITICAL]` `FLOW_BREAKAGE`.

### 5. Inspect the Compliance Matrix and Quick Fix Summary

The slash command emits a Compliance Matrix and a tagged Quick Fix Summary at the end of its output. Each item carries a category prefix so you can filter by type:

- **`[CRITICAL]`** — must-fix: security, data loss, broken builds, flow breakage.
- **`[SUGGESTION]`** — worth fixing: clean code, idiomacy, minor issues.
- **`[OPPORTUNITY]`** — deferrable: future work, nice-to-have improvements.

If all seven domains are clean, the slash command emits `/deviate-review: CLEAN — no issues across 7 domains` and exits. There is nothing to apply — proceed to step 7.

### 6. (Optional) Apply selected fixes interactively

If the findings contain `[CRITICAL]`, `[SUGGESTION]`, or `[OPPORTUNITY]` items, the slash command prompts you with a `question` tool offering four scopes: **Critical only**, **Quick fixes only**, **Critical + Suggestions**, **All changes**. Pick one, then the agent iterates the filtered Quick Fix Summary, applying each fix via the `edit` tool one at a time, and reports `Applied N of M fixes:` followed by the per-item outcome.

```text
Applied 3 of 4 fixes:
  ✓ src/db.py:25 — parameterize SQL query
  ✓ src/config.ts:10 — made apiKey optional
  ✓ src/utils.py:7 — updated callers
  - src/mod.py:50-65 — skipped (opportunity, not in selected scope)
```

The apply step is **HITL-driven**, not auto-rolled. You decide which scope to apply; the agent never picks for you. If the `edit` tool fails on a fix (e.g., the line has drifted), the agent logs the error, continues with the remaining items, and reports the failure in the summary.

### 7. (Optional) Persist a review report

By default the slash command surfaces findings as chat text only. If you want a durable artifact for compliance, audit, or team-wide review, pipe the rendered findings into `deviate review post`. The command writes the report to `.deviate/review/reports/review-report-<YYYYMMDDTHHMMSS>.md` with no git commit (`report_exists` will flip to `true` for the next pre-script invocation).

```bash
# From a heredoc / file, or piped from the slash command's chat output
deviate review post "$(cat .deviate/review/reports/scratch.md)"
```

If `content` is omitted and stdin is a TTY, the command emits `SKIP no report content provided` and exits with code 0 — no directory is created. To skip persistence entirely, do nothing — the chat output is the source of truth.

### 8. Verify the review landed

Confirm the review artifacts (or skip-verdict) are in place before proceeding to merge or PR creation.

```bash
# If you ran post: a timestamped report exists in .deviate/review/reports/
ls -1 .deviate/review/reports/ | tail -5

# If you did not: the slash command's final chat message is the verdict.
# Look for one of: "/deviate-review: CLEAN", "Applied N of M fixes", or "SKIP: no changes since main"

# Confirm the working tree is unchanged by the slash command itself
# (the apply step edits files, but the post step never commits)
git status --short
```

Expected outcome: either a `CLEAN` verdict or a populated `.deviate/review/reports/` directory, with `git status` showing only the files the apply step edited (and nothing staged unless you commit them yourself).

## Troubleshooting

### Slash command emits `SKIP: no changes since {base_branch}`

The active branch has no commits ahead of `main` (or whichever `--base` you passed). This is the normal end-state after a feature branch has already been merged. Either:

- Pass `--branch` explicitly to point at a different target (`deviate review pre --base main --branch feature/old-name`).
- Confirm the branch is what you think it is (`git rev-parse --abbrev-ref HEAD`) and that `git log --oneline <base>..HEAD` shows the expected commits.

### `prd_warning: true` in the pre-script JSON

The pre-script could not resolve a PRD for the active branch. `_resolve_prd` first looks for `<epic_slug>/prd.md` derived from the branch name (`epic/<slug>` → `specs/<slug>/prd.md`), then falls back to `specs/adhoc/prd.md`. If both are absent, the slash command notes `no PRD for traceability context` and skips the PRD Alignment domain in the Compliance Matrix. If you expected a PRD to be present:

```bash
# Check what branch you are on
git rev-parse --abbrev-ref HEAD

# Confirm the expected PRD path
ls specs/<epic>/prd.md 2>/dev/null || ls specs/adhoc/prd.md 2>/dev/null
```

If neither exists, run [`/deviate-prd`](/how-to/prd) (or the upstream [`/deviate-shard`](/how-to/shard) for an epic) before re-running review.

### `constitution_warning: true` in the pre-script JSON

`specs/constitution.md` is missing from the repo root. The slash command continues with a `no constitution to check` note and scores the Constitution domain N/A in the Compliance Matrix. If the constitution should exist:

```bash
test -f specs/constitution.md && echo "OK" || echo "MISSING — bootstrap from /deviate-setup or /deviate-init"
```

Without a constitution, the review cannot detect append-only-ledger breaches, HITL gate bypasses, Git Isolation Principle violations, or model tiering violations. Re-bootstrap with `/deviate-setup` (or create the constitution manually) before re-running if those checks are needed.

### `structured_diff` is empty but `diff` is populated

Tree-sitter failed to parse one or more source files (commonly: unsupported language, syntax error in a newly added file, or `tree-sitter` not installed in the venv). The slash command proceeds with raw text diff only and notes `no structured diff available` in the output. To restore per-language symbol analysis:

```bash
# Confirm tree-sitter is available
uv run python -c "from deviate.core.treesitter import extract_changed_symbols; print('OK')"
```

If the import fails, reinstall the dev environment with `mise run install-tool`. If the import succeeds but the diff contains a language the parser does not recognize, fall back to the raw text diff for that file — the slash command handles unknown languages by emitting `language: "unknown"` with empty symbols.

### Flow Coverage domain skipped with `PRODUCT_LAYER_ABSENT`

The `specs/_product/` directory is missing, so the Flow Coverage domain cannot resolve the parent issue's `flow_refs` against `specs/_product/flows/index.md`. The slash command continues with the other six domains and notes `PRODUCT_LAYER_ABSENT` in the Flow Coverage row of the Compliance Matrix. This is expected for projects that have not yet onboarded the product layer. If product-layer traceability matters, scaffold `specs/_product/` per `specs/_product/architecture.md` §3 (the C7 setup territory) and re-run review.

### Quick Fix Summary apply step edited the wrong line

The apply step uses the line number from the slash command's diff-citation context, but if the file was edited between the scan and the apply step (e.g., a concurrent fix), the line number will be stale. The agent logs the `edit` tool failure, continues with remaining fixes, and reports the failure in `Applied N of M fixes:`. To recover:

1. Re-run `/deviate-review` to get a fresh diff citation.
2. Apply the fix manually with the current line number.

Never run `deviate review post` with stale scan findings — the persisted report would not match the actual diff at merge time.

### Review surfaced `[CRITICAL] FLOW_BREAKAGE`

A `removed` symbol closed off a flow's user-visible capability named in the parent issue's `flow_refs`. This is the highest-severity finding the slash command emits. The flow's `Trigger` or `Happy Path` is no longer reachable from the implementation. Do not merge. Either:

- Restore the removed symbol (re-run the affected task or hotfix it with [`/deviate-hotfix`](/how-to/hotfix)).
- Amend the parent issue's `flow_refs` in `specs/issues.jsonl` if the flow is no longer in scope (treat this as a PRD change — re-run [`/deviate-prd`](/how-to/prd) and [`/deviate-shard`](/how-to/shard)).
- Amend the flow definition in `specs/_product/flows/flows-*.md` if the user-visible behavior was intentionally replaced.

## Next Steps

- [How to create a PR with /deviate-pr](/how-to/pr) — the natural next step after a CLEAN review verdict; opens the PR and on merge appends `COMPLETED` to `specs/issues.jsonl` to unblock dependents.
- [How to run /deviate-shard](/how-to/shard) — the meso phase that produced the issue files under review; if review surfaced a structural PRD error, re-shard the affected slice.
- [How to run a hotfix with /deviate-hotfix](/how-to/hotfix) — when review surfaced a `[CRITICAL]` that needs surgical repair without re-running the full red→green→refactor→judge loop.
- [Reference: deviate slash commands](/reference/slash-commands#deviate-review) — the canonical signature and aliases for `/deviate-review` (also reachable as `/review`).
- [Reference: macro run lifecycle](/reference/macro-run) — how the meso-layer phases wire into the macro and micro layers; review is the meso-side terminal phase.
- [Explanation: HITL Gate 3](/explanation/hitl-gates) — design rationale for the final merge audit, why findings surface as chat text rather than auto-committed reports, and how it interacts with the constitutional alignment audit and the product-layer Flow Coverage domain.