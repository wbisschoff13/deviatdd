---
title: "Mise Tasks"
description: "Field-by-field reference for the `mise run` task surface in `mise.toml` — task names, shell invocations, dependencies, and descriptions."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Mise Tasks

Every `mise run <name>` invocation in this repository resolves to a `[tasks.<name>]` block in `mise.toml`. All invocations execute under the project-local Python toolchain pinned by the file's `[env]` and `[tools]` blocks (`python = "3.13"`, `uv = "latest"`).

## Task inventory

| Name | Run | Depends | Description |
|---|---|---|---|
| `test` | `uv run pytest tests/ -v` | — | Run unit tests |
| `test-e2e` | `bats tests/e2e/` | — | Run E2E tests via bats |
| `lint` | `uv run ruff check` | — | Lint Python |
| `lint-fix` | `uv run ruff check --fix` | — | Apply lint fixes |
| `format` | `uv run ruff format` | — | Format Python |
| `format-check` | `uv run ruff format --check` | — | Check formatting |
| `check-types` | `echo "No type checker configured"` | — | Type check |
| `check` | _(depends only)_ | `["lint", "format-check"]` | All validation checks |
| `fix` | _(depends only)_ | `["lint-fix", "format"]` | Format + lint fix |
| `setup` | `uv sync --extra dev && git config core.hooksPath .githooks` | — | Install deps + configure git hooks |
| `clean` | `rm -rf .ruff_cache/ .pytest_cache/ __pycache__/ .mypy_cache/ dist/ build/ *.egg-info/` | — | Remove artifacts |
| `dev` | `uv run deviate` | — | Run the deviate CLI (pass args directly, e.g. `mise run dev init`) |
| `install-tool` | `uv tool install --editable .` | — | Install package as editable tool via uv |
| `help` | `mise tasks` | — | List tasks |

Example — run the fast-lane validation bundle (composite of `lint` + `format-check`):

```
mise run check
```

Example — invoke a CLI subcommand via the `dev` passthrough:

```
mise run dev init
```

## Resolution notes

| Behaviour | Detail |
|---|---|
| Discovery | `mise tasks` reads `mise.toml` next to the repository root; aliased to `mise run help` |
| Toolchain | `[env].python = "3.13"` and `[tools].python = "3.13"` pin the interpreter; `uv run` adds a managed virtualenv on top |
| Dependency resolution | Every `uv run …` and `uv sync …` invocation reads `pyproject.toml` from the repository root |
| Composites | `check` and `fix` declare only `depends`; their shell `run` block is omitted and `mise` runs the listed tasks in declaration order |
| `check-types` placeholder | Currently a no-op (`echo "No type checker configured"`); kept so the validation bundle has a stable shape |
| Working directory | All invocations execute from the directory containing `mise.toml` (the repository root) |

## Source-of-Truth

| Attribute | Location |
|---|---|
| Task definitions | `mise.toml` lines 8-61 (one `[tasks.<name>]` block per task) |
| Toolchain pin | `mise.toml` lines 1-6 (`[env]` / `[tools]`) |
| Python dependency list | `pyproject.toml` |
| Bats E2E suite | `tests/e2e/` (consumed by `test-e2e`) |

## See Also

- [Reference intro](/reference/intro) — navigation map for the reference quadrant
- [CLI Reference](/reference/cli) — every `deviate` subcommand the `dev` task invokes
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — exercises `mise run setup`
- [`.deviate/config.toml` Schema](/reference/config-toml) — runtime config consumed by most Python-side tasks
