---
title: "Run the /deviate-constitution workflow"
description: "Initialize or amend specs/constitution.md — the authoritative governance artifact defining architectural standards, testing mandates, and Definition of Done — via the /deviate-constitution slash command."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-002-004
---

# Run the /deviate-constitution workflow

This how-to covers `/deviate-constitution` — the macro-layer slash command registered at `src/deviate/cli/__init__.py:793` (`cli.add_typer(constitution_app, name="constitution")`) and backed by `src/deviate/cli/constitution.py`. The slash command initializes or amends `specs/constitution.md`, the canonical governance artifact every downstream phase consults (`deviate explore` rejects on missing sections at `src/deviate/cli/macro.py:205` via `_validate_constitution("EXPLORE")`; research, plan, and tasks all invoke the same gate at `src/deviate/cli/_common.py:111`). The `<execution_sequence>` in `src/deviate/prompts/commands/deviate-constitution.md` runs five agent-internal steps: `pre_script` (resolves git state and constitution path), `project_analysis` (parses `pyproject.toml`, `package.json`, `mix.exs`, CI configs), `constitution_generation` (writes the markdown), `manifest_writing` (emits the execution manifest JSON), and `post_script` (validates and commits). You provide the governance intent in natural language; the slash command orchestrates the rest. If you need to scaffold `specs/constitution.md` from a fresh repo instead, see [Initialize a repo with DeviaTDD conventions](/how-to/init) — `/deviate-init` writes a starter `constitution.md` placeholder the same slash command can later populate.

## Prerequisites

- **`specs/constitution.md` exists at the repository root** — the slash command's `pre_script` step invokes `deviate constitution pre`, which fails immediately with `constitution.md not found at <path>` if the file is absent (`src/deviate/cli/constitution.py:72-73`). If you are starting from a greenfield repo, bootstrap with `/deviate-init` first (it seeds a `constitution.md` placeholder from `src/deviate/prompts/constitution_seed.md`), or scaffold a placeholder manually with `deviate constitution generate [--force]`.
- **A description of the governance change** — the slash command's `project_analysis` step needs context: which tech-stack section to amend (Backend, Frontend, Database, Infrastructure, Tooling), which clauses to add or relax (Testing Protocols, Definition of Done, HITL gates), or which stack decisions need codifying. Without input, the slash command reads existing project-state files and falls back to the minimum standard structural template (per `<edge_case_handling>` in `deviate-constitution.md`).
- **The `deviate-constitution` skill installed in the active agent** — the slash command lives at `src/deviate/prompts/commands/deviate-constitution.md` (version `1.0.0`, aliases `constitution`, `/spec.constitution`, `spec:constitution`, `deviate-constitution`) and is installed to every active agent's command directory by `deviate setup` (see [Bootstrap a DeviaTDD workspace](/how-to/setup)). Run `deviate setup` if `/deviate-constitution` is not wired into your prompt palette.
- **A clean working tree on the relevant branch** — the slash command's `post_script` step runs `commit_artifact(path=const_path, message="Update constitution")` (`src/deviate/cli/constitution.py:106`) on the staged file. Stash or commit any unrelated edits before invoking the slash command; pre-commit hooks (running the full test suite per `.mise.toml`) need a clean tree to land.
- **`specs/constitution.md` is not the same file across branches in conflicting ways** — the constitution is read by every macro-phase pre-script via `resolve_constitution(repo_root)` (`src/deviate/core/constitution.py:41`); if you are mid-worktree with a stale constitution, the new phase runs will reject until the file converges. Confirm `git log --oneline -5 -- specs/constitution.md` matches the expectations of any in-flight feature branches.
- **Reasoning-model availability for the CONSTITUTION phase** — the slash command routes through the macro-layer tier (V4 Pro or Qwen 3.7+ [Thinking] per `specs/_product/architecture.md` and `src/deviate/state/config.py::resolve_phase_model`). Per-phase overrides go in `.deviate/config.toml` under `[models].constitution`; confirm `jq '.models.constitution // .models.default' .deviate/config.toml` returns a reachable model name (the `claude` backend ignores model config silently).
- **`uv run` (or an activated venv) on `PATH`** — the pre-script and post-script are invoked as Python CLI commands per `.mise.toml`; inside the canonical wrapper the form is `uv run deviate constitution pre`. The slash command invokes them on your behalf, so this matters only when recovering a wedged post-script manually.

## Steps

### 1. Confirm the upstream gate

Before invoking the slash command, verify the constitution file is in place and the working tree is clean. The slash command refuses to write without a placeholder to anchor against, and the post-script refuses to commit on a dirty tree.

```bash
# Constitution file exists at the canonical path
test -f specs/constitution.md && echo "OK" || echo "MISSING"

# Inspect the current top-level sections (the slash command must preserve these)
grep -E "^## " specs/constitution.md

# Working tree is clean (post-script commits the change)
git status --porcelain

# Branch is not detached
git rev-parse --abbrev-ref HEAD
```

If the file is missing, run `deviate constitution generate` first (per `src/deviate/cli/constitution.py:38-63`) to seed the placeholder from `constitution_seed.md`, or pivot to `/deviate-init` for a full greenfield bootstrap. If `git status --porcelain` shows unstaged work, stash (`git stash push -m "wip"`) or commit before invoking the slash command.

### 2. Invoke the slash command with the governance intent

Invoke `/deviate-constitution` and pass the natural-language change as `$ARGUMENTS`. The slash command handles path resolution, project-state analysis, file generation, manifest writing, and the post-script; you only describe the change.

```text
/deviate-constitution "Move Test Runner from pytest to uv-managed nox, raise coverage threshold to 85%, add an explicit SECURITY clause forbidding subprocess shell=True"
```

The slash command's `<execution_sequence>` step 1 (`pre_script`) runs `deviate constitution pre` on your behalf; you do not need to invoke it manually. The same applies to `post_script` — the slash command chains `deviate constitution post "$PLAN_TARGET"` after writing the manifest.

### 3. Watch the pre-script contract on stdout

The slash command's first internal step runs `deviate constitution pre` and parses the JSON contract on stdout (`src/deviate/cli/constitution.py:66-83`). The contract carries:

| Field | Meaning |
|---|---|
| `constitution_path` | Absolute path to `specs/constitution.md` the slash command will write to (resolved from `Path.cwd() / specs/constitution.md` per `src/deviate/cli/constitution.py:70`) |
| `test_command` | The `TEST_COMMAND:` line extracted from the constitution (e.g. `pytest tests/ -v` per `specs/constitution.md` §3); used by downstream macro phases as `constitution_test_command` |
| `lint_command` | The `LINT_COMMAND:` line extracted from the constitution (e.g. `ruff check .`); surfaced as `constitution_lint_command` for plan, tasks, execute, and review |
| `type_check_command` | The `TYPE_CHECK_COMMAND:` line extracted from the constitution, when present (`src/deviate/core/constitution.py:55-59` defines the marker set) |
| `status` | `READY` (proceed) or `FAILURE` with `reason` (halt) — surfaces from `validate_constitution` and `validate_sections` checks |

If the slash command prints a `Constitution validation failed` or `Missing required section: ## TESTING_PROTOCOLS` block, the file is missing required sections — see the first troubleshooting entry below.

### 4. Confirm the slash command's project analysis and generated constitution

The slash command's `project_analysis` step reads `package.json`, `mix.exs`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `terraform/`, and CI configuration files (per `<project_state_sources>` in `deviate-constitution.md`) and merges those signals with any active context you supplied. The `constitution_generation` step then writes the merged markdown to `constitution_path`.

Confirm the file landed before the post-script runs:

```bash
# File is non-empty and starts with the required header
test -s specs/constitution.md && head -3 specs/constitution.md

# Required sections are present (validate_sections check the pre-script ran)
grep -E "^## (Architectural Principles|Tech Stack Standards|Testing Protocols|Definition of Done|Version History)" specs/constitution.md

# TESTING_PROTOCOLS section has the test/lint command keys the rest of the macro layer pulls
grep -E "TEST_COMMAND|LINT_COMMAND" specs/constitution.md
```

The slash command will halt and surface the failure if any required section is missing (per `<edge_case_handling>` MALFORMED_EXISTING_CONSTITUTION); if it slips through, the post-script catches it via `validate_sections(const_path, sections)` at `src/deviate/cli/constitution.py:102`.

### 5. Let the post-script validate and commit

The slash command's final internal step runs `deviate constitution post "$PLAN_TARGET"` with the manifest written during step 4 (`src/deviate/cli/constitution.py:86-107`). The post-script reads the manifest, validates that requested sections exist (`validate_sections(const_path, sections)`), then calls `commit_artifact(path=const_path, message="Update constitution")` and emits `{"status": "SUCCESS"}` on stdout.

Allocate up to **180 seconds** for the post-script — `commit_artifact` triggers pre-commit hooks including the full test suite per `.mise.toml`, and constitutional changes routinely touch every phase's gate behavior, so a slow test run can stretch the commit. If you need to recover a wedged post-script, run it by hand:

```bash
# Plan target is the manifest path the agent emitted; reconstruct from .git/index or last step output
deviate constitution post "$PLAN_TARGET"
```

### 6. Verify the change landed and the downstream gates still resolve

After the slash command emits its `READY` handover manifest, confirm the file updated, the commit landed, and the downstream macro phases can read the new commands.

```bash
# Commit is on the active branch with the standard "Update constitution" subject
git log --oneline -3 -- specs/constitution.md

# File diff matches the governance change you requested
git show HEAD -- specs/constitution.md | head -40

# Pre-script still extracts the commands cleanly (downstream gates read these)
deviate constitution pre | jq '.test_command, .lint_command'
```

The downstream check is non-negotiable: `deviate explore` / `deviate research` / `deviate plan` / `deviate tasks` all funnel through `_resolve_constitution_commands` (`src/deviate/cli/meso.py:241-252`, `src/deviate/cli/macro.py:126-149`) and pass the extracted commands downstream as `constitution_test_command` and `constitution_lint_command`. A constitution that exists but fails `extract_commands` (because the lines were reformatted or the section heading was retitled) silently breaks every macro phase.

## Troubleshooting

### Pre-script fails: `constitution.md not found`

`deviate constitution pre` exits with `status: FAILURE, reason: "constitution.md not found at <path>"` (`src/deviate/cli/constitution.py:72-73`). The slash command halts and surfaces the reason. The file was deleted, never created, or the slash command was invoked from outside the repository root. Run `deviate constitution generate` to seed the placeholder from `constitution_seed.md`, or pivot to `/deviate-init` for a full greenfield bootstrap. Confirm `Path.cwd()` is the repo root — the pre-script uses `Path.cwd() / "specs" / "constitution.md"` (`src/deviate/cli/constitution.py:70`), so a worktree at `.worktrees/feat/<epic>/<issue>/` is the correct execution context.

### Pre-script fails: `Missing required section: ## TESTING_PROTOCOLS`

The placeholder exists but does not carry the section the rest of the macro layer extracts commands from. The pre-script enforces this via `validate_sections(const_path, ["## TESTING_PROTOCOLS"])` at `src/deviate/cli/constitution.py:78`. Two common causes: the section was renamed (extract_commands looks for `TEST_COMMAND:` / `LINT_COMMAND:` / `TYPE_CHECK_COMMAND:` lines under any heading, but the heading must be intact for downstream gates that consume the section text), or the placeholder was generated by an older `constitution_seed.md` revision that used a different heading. Edit `specs/constitution.md` to restore the heading and add the three command lines in the `### Framework` subsection, then re-run `/deviate-constitution`.

### Post-script reports missing sections from the manifest

`deviate constitution post` exits with `status: FAILURE, reason: "Missing sections: <list>"` (`src/deviate/cli/constitution.py:103`). The slash command's manifest named sections that the generated constitution does not contain. Either the generation step dropped a section (review the previous step's output and the file diff), or the manifest drifted from the file (regenerate by re-invoking the slash command — `<edge_case_handling>` MALFORMED_EXISTING_CONSTITUTION preserves valid sections and skips missing ones). Never run `deviate constitution post` with a hand-edited manifest that contradicts the file — the post-script is mechanical and will emit `SUCCESS` even if the file is incomplete.

### Want to regenerate `specs/constitution.md` from scratch

The macro-layer flow is incremental — it preserves valid sections and increments the version string — but a complete reset is sometimes warranted (e.g., after a major org-wide governance rewrite). Use `deviate constitution generate --force` to overwrite the placeholder (`src/deviate/cli/constitution.py:38-63`), then re-invoke `/deviate-constitution` to repopulate from scratch. A force-regenerate is destructive: it clobbers the version history list and resets every section to the seed template's `> TBD` placeholders. Commit the reset on its own before re-populating so the diff history is readable.

### Post-script times out or `commit_artifact` returns non-zero

Pre-commit hooks (including the full `mise run test` suite and any `mise run lint` bundles declared in `.mise.toml`) are stricter than usual for constitutional changes — every macro phase reads the file, so the change can break in-flight features. Increase the post-script timeout to ≥ 180s and re-run. If `commit_artifact` still fails, run `git status` to inspect partial staging, `git diff` to inspect the unstaged buffer, and `mise run check` in isolation to diagnose which gate rejected. If the commit is partial, `git restore --staged specs/constitution.md` and re-run the slash command once the underlying issue is fixed.

## Next Steps

- [Initialize a repo with DeviaTDD conventions](/how-to/init) — the greenfield how-to that scaffolds the `specs/constitution.md` placeholder this workflow later populates; the `EXIT_FRESH_INIT` route in `/deviate-init` is the right starting point for a new repo.
- [Bootstrap a DeviaTDD workspace](/how-to/setup) — the one-time bootstrap that installs the `/deviate-constitution` slash command into every active agent's command directory; required if the slash command is missing from your prompt palette.
- [Run the /deviate-explore phase](/how-to/explore) — the first macro phase that validates the constitution via `_validate_constitution("EXPLORE")` (`src/deviate/cli/macro.py:205`); a successfully amended constitution here unblocks any `## Missing sections` fix surfaced during explore.
- [Run the /deviate-research phase](/how-to/research) — surfaces a `Constitutional Violation` block when a proposed architecture contradicts `specs/constitution.md`; amendment via `/deviate-constitution` is one of three resolutions named in the research how-to.
- [Reference: `/deviate-constitution` slash command entry](/reference/slash-commands#deviatdd-macro-layer) — the inventory entry confirming `deviate-constitution` aliases (`constitution`, `/deviate-constitution`, `spec:constitution`, `spec.constitution`) and the `deviatdd-macro-layer` category, version `1.0.0`.
- [Reference: `deviate constitution pre` / `deviate constitution post`](/reference/cli) — the CLI surface for the pre/post sub-commands; flag tables and exit-code semantics for manual recovery.
