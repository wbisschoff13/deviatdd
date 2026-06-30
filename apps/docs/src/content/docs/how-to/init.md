---
title: "Initialize a repo with DeviaTDD conventions"
description: "Run `/deviate-init` to scaffold `mise.toml`, `specs/`, an empty `issues.jsonl` ledger, and a starter `constitution.md` for a fresh repository."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-001
---

# Initialize a repo with DeviaTDD conventions

This how-to covers `/deviate-init` — the macro-layer init phase that turns a plain git repository into a DeviaTDD-compliant workspace. The command is idempotent and project-type-aware: it detects the language from `mix.exs`, `pyproject.toml`, `package.json`, `Cargo.toml`, or `go.mod`, scaffolds a `mise.toml` whose `test` task passes with zero tests written (the **zero-test-pass invariant**), creates the `specs/` tree with a placeholder `constitution.md` and an empty append-only `issues.jsonl` ledger, and seeds union-merge rules into `.gitattributes` so concurrent branches can each append issues without conflict. After `/deviate-init` completes, the workspace is ready for the first feature slice via [Run the /deviate-explore phase](/how-to/explore).

## Prerequisites

- **A DeviaTDD workspace already bootstrapped** — `deviate` must be on `PATH` and `.deviate/config.toml` must exist. If you have not yet run setup, complete [Bootstrap a DeviaTDD workspace](/how-to/setup) first; `/deviate-init` will not scaffold `.deviate/`.
- **A git-initialized working directory** — `/deviate-init` resolves the repo root with `git rev-parse --show-toplevel` and aborts with `FAILURE: Not a git repository` otherwise. Initialize with `git init` and make at least one commit before running init.
- **A recognized project-type marker at the repo root** — exactly one of `mix.exs` (Elixir/Phoenix), `pyproject.toml` (Python), `package.json` (Node), `Cargo.toml` (Rust), or `go.mod` (Go). The detected type drives the `mise.toml` test/lint/format commands. Repos without a marker scaffold as `unknown` with `test = "echo 'No test framework' || true"` and are still init-successful.
- **An agent platform with `/deviate-init` available** — the slash command is installed by `deviate setup` into your agent's prompt directory. If the slash command is missing, see the setup how-to's troubleshooting section.

## Steps

### 1. Verify the preconditions from a clean shell

Confirm the three preconditions in one command so failures surface before the slash command runs. This is the only verification step that uses raw `git` — the rest of the how-to runs the slash command.

```bash
git rev-parse --show-toplevel          # must print the repo root, not exit 1
ls pyproject.toml mix.exs package.json Cargo.toml go.mod 2>/dev/null \
  | head -1                            # must print at least one marker file
which deviate                          # must print the deviate binary path
```

If any of these fail, fix the missing prerequisite and re-check before proceeding. The init slash command is idempotent, but a missing marker file changes the detected `project_type` to `unknown`.

### 2. Run the `/deviate-init` slash command

In your agent's prompt palette, run `/deviate-init`. The slash command is the only entry point — do not run `deviate init pre` / `deviate init post` directly. The slash command executes both stages for you.

```text
/deviate-init
```

The command runs to completion in a few seconds. It does not require user input, does not call an LLM (init is deterministic scaffolding), and produces a JSON contract on stdout that the slash command prints after the post-script stages the artifacts for commit.

### 3. Inspect the JSON contract

The slash command emits a JSON contract whose fields describe what the pre-script detected and created. Look for these three keys:

```json
{
  "phase": "deviate-init",
  "status": "READY",
  "project_type": "python",
  "artifacts_created": ["mise.toml", "specs/", "specs/issues.jsonl", "specs/constitution.md", ".gitattributes"],
  "mise_available": true
}
```

- `status` must be `READY`. Any other value is a failure.
- `project_type` must match the language you expect; if it reads `unknown`, your marker file is missing or the working directory is wrong.
- `mise_available` should be `true` so `mise run test` resolves at the repo root. If it is `false`, install mise and rerun the slash command — it is idempotent.

### 4. Verify the artifacts on disk

The post-script stages every init artifact, but the working tree is the source of truth. Confirm the scaffold landed correctly:

```bash
# mise.toml exists with the zero-test-pass test task
test -f mise.toml && grep -E '^test\s*=' mise.toml

# specs/ tree is in place
ls -la specs/

# issues.jsonl exists and is empty (zero bytes is the correct initial state)
test -f specs/issues.jsonl && [ ! -s specs/issues.jsonl ] && echo "empty ledger"

# constitution.md is scaffolded (not yet populated — research populates it)
test -f specs/constitution.md && head -3 specs/constitution.md

# Root .gitattributes has the union-merge driver for the ledger
grep "merge=union" .gitattributes
```

`git status` should list the staged artifacts:

```bash
git status --short
```

Expected entries: `M` or `A` on `mise.toml`, `specs/`, `specs/constitution.md`, `specs/issues.jsonl`, and `.gitattributes`. If the working tree is clean after init, the post-script did not stage — re-run the slash command (it is idempotent and will stage the existing files).

### 5. Commit the scaffold

Stage and commit the init artifacts as the first DeviaTDD commit on the branch. Use a conventional-commit message so future changelogs can derive from the log.

```bash
git commit -m "chore(deviate): initialize repo with DeviaTDD conventions"
```

The commit message should reference that the workspace now has a `mise.toml` with the zero-test-pass invariant, an empty `specs/issues.jsonl` ledger, and a stub `constitution.md`. No source code is committed by this commit — `/deviate-init` never writes implementation code.

## Troubleshooting

### `FAILURE: Not a git repository` on a freshly-cloned repo

The slash command resolves the repo root with `git rev-parse --show-toplevel` and bails with this JSON before any scaffolding runs. Fix by initializing a git repository in the working directory (or by `cd`-ing into the right repo). Run `git init` and make at least one commit, then re-run `/deviate-init`.

```bash
git init
git add -A && git commit -m "chore: initial commit"  # if you have files to commit
/deviate-init
```

### `project_type` is `unknown` after init

The pre-script detects the project type from marker files (`pyproject.toml`, `package.json`, etc.). If the working directory has no marker, the scaffolded `mise.toml` falls back to `test = "echo 'No test framework' || true"`, which passes the zero-test-pass invariant but blocks every micro-layer task. Diagnose by listing the repo root:

```bash
ls -la | grep -E "pyproject\.toml|package\.json|Cargo\.toml|go\.mod|mix\.exs"
```

If the marker is missing, scaffold the project (`uv init`, `npm init`, `cargo init`, etc.) and re-run `/deviate-init`. If the marker is present but detection still reports `unknown`, check that you are running the slash command from the repo root, not a subdirectory.

### `mise.toml` or `constitution.md` already exists — was it overwritten?

It was not. The pre-script skips regeneration when `mise.toml` or `specs/constitution.md` already exists at the repo root; the existing files are preserved verbatim and the new entries are appended to `artifacts_created` in the contract (without the `CREATE` semantic). To verify what was actually changed, read the contract's `artifacts_created` list and compare against `git status`:

```bash
git status --short
```

If the existing `mise.toml` does not have the zero-test-pass invariant (`test = "... || true"`), the pre-script left it untouched and you must hand-edit the file to add the `|| true` guard. This is a known edge case — the init phase favors preserving user content over enforcing the invariant on existing files.

### `mise_available: false` but `/deviate-init` still reports `READY`

The pre-script reports `mise_available` for diagnostic purposes but does not require it — `READY` is returned even when mise is missing, as long as the scaffolded `mise.toml` and `specs/` tree are valid. Install mise before running any `mise run` task, but `/deviate-init` itself does not need it. The verification commands in step 4 use raw `git`, `grep`, and `ls` and work without mise installed.

### `git status` is clean after the slash command

The post-script stages every artifact it can find at the repo root: `mise.toml`, `specs/`, `specs/constitution.md`, `specs/issues.jsonl`, `AGENTS.md` (if symlinked), and `.gitattributes`. If `git status` reports a clean tree, the files were either already committed on the branch or the post-script did not run. The slash command invokes both `pre` and `post`; if `post` failed (e.g., git hook failure), the artifacts are still on disk but not staged. Re-run the slash command — `post` retries the staging.

## Next Steps

- [Run the /deviate-explore phase](/how-to/explore) — the first task after init: read-only scan of the codebase that produces `specs/explore/<slug>.md` and routes on scope.
- [Bootstrap a DeviaTDD workspace](/how-to/setup) — prerequisite: if you have not yet run setup, do that first; `/deviate-init` does not scaffold `.deviate/`.
- [Reference: slash commands](/reference/slash-commands) — the canonical inventory of every `/deviate-*` slash command, including the aliases (`/init`, `spec:init`) for `/deviate-init`.
