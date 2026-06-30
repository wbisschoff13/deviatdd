---
title: "Run the /deviate-explore phase"
description: "Produce specs/explore/<slug>.md with a read-only scan of the codebase and route the next phase on Scope Sizing (Low/Medium → /deviate-adhoc, High → /deviate-research)."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
---

# Run the /deviate-explore phase

This how-to covers `/deviate-explore` — the first phase of the macro layer. The skill runs a read-only structural scan of the active repository and produces a single artifact at `specs/explore/<slug>.md` that catalogs what EXISTS (file registry, dependency manifests, architectural baselines, ecosystem research) without recommending any design. On the way out, the skill's `## Scope Sizing` table classifies the feature as Low, Medium, or High complexity, and the operator routes the next phase to [`/deviate-adhoc`](/how-to/adhoc) (Low/Medium) or [`/deviate-research`](/how-to/research) (High) based on that row.

The slash command is read-only by mandate — the skill never writes code, tests, or configuration. The post-script runs the full precommit hook chain (including the test suite, ~180s allocation) and commits the artifact with `docs(explore): scan <slug>`.

## Prerequisites

- **DeviaTDD workspace bootstrapped** — `deviate setup` has run, so `.deviate/config.toml` exists and `/deviate-explore` is in the agent prompt palette. If you have not done this yet, see [Bootstrap a DeviaTDD workspace](/how-to/setup).
- **A valid `specs/constitution.md`** — either created by `deviate init` for a fresh repo, or written by the operator after the first `/deviate-research` pass. The pre-script validates the constitution against the four required sections (`Tech Stack Standards`, `Testing Protocols`, `Architectural Principles`, `Definition of Done`); a missing or malformed constitution triggers `MALFORMED_CONSTITUTION` and halts. Greenfield projects are an explicit exception: the pre-script auto-detects `is_greenfield=true` and the orchestrator bootstraps a constitution from the explore findings downstream.
- **A clean working tree** — `git status` reports no uncommitted changes in tracked files. The explore commit lands on the active feature branch, so any staged-but-uncommitted work will be swept up into the post-script's commit.
- **A short problem statement** — a 1–2 sentence description of the feature bucket that names the *problem space*, not the solution. Example: `"Add JWT-based authentication to the public API endpoints."`. The skill derives a 2–3 word kebab-case slug from this statement (`auth-jwt`).
- **Slash-command-capable agent** — Pi, OpenCode, Claude, or Factory running against the project root. The agent must have read access to the full repo (no narrow file selection — the Codebase Scanner subagent walks the tree).

## Steps

### 1. Compose the problem statement

Draft a 1–2 sentence description of the feature bucket. Avoid implementation hints; the skill is read-only by mandate, and a problem statement that names a specific library or pattern can trigger `STATUS: IMPLEMENTATION_DRIFT_DETECTED` if a subagent picks it up as a directive.

Examples of acceptable problem statements:

```text
"Add JWT-based authentication to the public API endpoints."
"Introduce a background worker pool for async email delivery."
"Migrate the legacy CSV import path to streaming."
```

### 2. Run `/deviate-explore`

In the agent chat, invoke the slash command with the problem statement as the argument:

```bash
/deviate-explore "Add JWT-based authentication to the public API endpoints."
```

The slash command is the single primary action for this how-to. It orchestrates the pre-script, the subagent fork, the artifact write, and the post-script internally. You do not invoke `deviate explore pre` or `deviate explore post` directly — the skill does.

### 3. Wait for the pre-script to emit the contract

The slash command invokes `deviate explore pre` first. The pre-script derives the slug from your problem statement, creates `specs/explore/`, validates the constitution, and emits a JSON contract on stdout.

The contract contains: `repo_root`, `git_branch`, `feature_slug`, `feature_dir` (`specs/explore/`), `specs_directory`, `spec_target` (absolute path the orchestrator will write), `constitution_path`, `test_command`, `lint_command`, `type_check_command`, `constitution_test_command`, `constitution_lint_command`, `epic_id` (the explore slug), and `is_greenfield` (boolean).

If the pre-script returns a failure token, surface it verbatim and halt. Common tokens are listed in the **Troubleshooting** section.

### 4. Wait for the subagent fork (or single linear pass)

For non-trivial features (the default), the orchestrator spawns two read-only subagents in parallel:

- **Codebase Scanner** — walks the repo, captures file registry, dependency manifests, and architectural baselines. Returns fragments for `## Discovery Audit Results`, `## File Registry`, `## Constitution Quotes`, and `## Architectural Baselines`.
- **Ecosystem Researcher** — runs `libref` queries and (if needed) web searches for industry patterns. Returns fragments for `## Ecosystem Research`.

For trivial repos (one-file, one-script, single-language micro-projects), the fork collapses to a single linear pass and the subagents are skipped — the orchestrator walks the tree itself.

Both subagents are strictly discovery-only. They do not write files, generate code, run tests, or make any modifications.

### 5. Read the Status Summary

The skill outputs a `## Status Summary` table at the end of the artifact. The key fields:

- `STATUS: SUCCESS` — the explore artifact is on disk and validated.
- `EXPLORE_SLUG` — the slug derived from the problem statement.
- `GIT_BRANCH` — the branch the explore was committed to.
- `SPEC_TARGET` — the relative path to the explore artifact.
- `NEXT_ACTION` — the recommended next slash command.

### 6. Route on Scope Sizing

Open `specs/explore/<slug>.md` and find the `## Scope Sizing` table. The `Estimated Complexity` row drives the next step:

- **Low or Medium** → run [`/deviate-adhoc`](/how-to/adhoc) with the same problem statement. The adhoc skill detects the existing `explore.md` automatically via its `Existing Explore Check` (step 2.5) and consumes it as input.
- **High** → run [`/deviate-research`](/how-to/research) with the explore slug. The research skill consumes `explore.md` as input and produces `specs/NNN-<slug>/design.md` plus `data-model.md`.

### 7. Verify the artifact is committed

Confirm the post-script committed the explore.md to the feature branch:

```bash
git log --oneline -1
git show --stat HEAD -- specs/explore/
```

The latest commit message should be `docs(explore): scan <slug>`. The diff should show only the new `specs/explore/<slug>.md` file (the artifact is a spec, not a Tome doc — it carries no frontmatter).

## Troubleshooting

### Pre-script exits with `MALFORMED_CONSTITUTION`

`specs/constitution.md` is missing one or more required sections (`Tech Stack Standards`, `Testing Protocols`, `Architectural Principles`, `Definition of Done`).

**Fix**: Run `/deviate-constitution` to regenerate the constitution, or manually add the missing sections to `specs/constitution.md`. Re-run `/deviate-explore` after the constitution is valid.

### Pre-script exits with `LEDGER_DIRTY` or `CLAIM_REJECTED`

The append-only ledgers (`specs/issues.jsonl`, `specs/**/tasks.jsonl`) have an unresolved claim or are mid-write — typically a half-written record from a prior skill abort.

**Fix**: Surface the status token to the operator verbatim. The skill will not retry automatically. Resolve the ledger conflict (the token names the file) before re-invoking `/deviate-explore`.

### Skill outputs `STATUS: IMPLEMENTATION_DRIFT_DETECTED`

A subagent or follow-up step attempted to write code, tests, or configuration outside the explore.md target. The skill is read-only by mandate; this is a hard-stop failure.

**Fix**: Restart the agent session and re-run `/deviate-explore` with a tighter problem statement. Do not include implementation hints (library names, pattern names, file paths) in the problem statement text — describe the problem space only.

### `WEB_SEARCH_UNAVAILABLE` in Ecosystem Research

The ecosystem research subagent could not reach the web (no `web_search` tool in the agent, or network restrictions).

**Fix**: Soft failure. The skill continues with local findings only. Register the library locally with `libref add <source-url>`, then re-invoke `/deviate-explore` if ecosystem context is critical to scoping the feature.

### Post-script hook times out

The post-script runs precommit hooks (full test suite). The skill allocates ~180s for the post-script; a test suite that routinely exceeds 180s will trip this guard.

**Fix**: Investigate slow tests with `pytest --durations=10` on the local machine first. The post-script timeout is a deliberate guard against runaway test loops — address the underlying slow tests, do not raise the timeout to mask them.

### Explore artifact rejected with missing verbatim quotes

The post-script validates that every row in the `## File Registry` table carries a verbatim quote (≤ 10 lines). Rows without quotes are rejected.

**Fix**: Edit `specs/explore/<slug>.md` to add a ≤ 10 line verbatim snippet to each row, then re-run `deviate explore post --slug "<slug>"` to re-validate and re-commit. Do not change any other field in the artifact.

## Next Steps

- [How to run /deviate-adhoc](/how-to/adhoc) — the next phase for Low/Medium complexity features; the adhoc skill consumes `explore.md` automatically.
- [How to run /deviate-research](/how-to/research) — the next phase for High complexity features; the research skill consumes `explore.md` as input.
- [Reference: explore command contract](/reference/explore) — the full JSON contract, slug rules, and status token list.
- Explanation: why explore is read-only — the design rationale for the discovery-only mandate (see the explanation quadrant).
