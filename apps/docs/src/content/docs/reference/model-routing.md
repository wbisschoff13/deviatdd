---
title: "Model Routing"
description: "Per-phase model overrides, resolution order, recommended tier map, and backend-flag compatibility for the [models] section of .deviate/config.toml."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-005
  - ISS-ADH-011
---

# Model Routing

Per-phase model override surface configured under the `[models]` table in `.deviate/config.toml` and resolved at agent-invocation time by `resolve_model_for_phase` in `src/deviate/state/config.py`.

## Resolution Order

`resolve_phase_model(phase, models)` (case-insensitive) returns the model ID for a phase in this fixed order:

| # | Source | Returns |
|---|---|---|
| 1 | Phase-specific key matching `phase.lower()` (e.g. `judge`, `plan`, `red`) | That value |
| 2 | `default` key in `[models]` | That value |
| 3 | No match | `None` — backend falls back to its native default |

Empty-string values are skipped at lookup-build time (`{k.lower(): val for k, val in models.items() if val}`), so `red = ""` is treated as unset.

## Recommended Phase Tier Map

The default tier per phase, sourced from `specs/DeviaTDD-api.md` §5 and `AGENTS.md` "Model Tiering" block. Tier is policy-level guidance, not enforced by code — operators override per `[models]` keys.

| Phase | Recommended tier | Rationale |
|---|---|---|
| `idle` | n/a | No agent invocation |
| `explore` | V4 Flash (low-cost) | One-shot structural scan |
| `research` | Qwen 3.7+ [Thinking] | Architectural reasoning |
| `prd` | Qwen 3.7+ [Thinking] | Long-form synthesis |
| `shard` | Qwen 3.7+ [Thinking] | DAG dependency decomposition |
| `specify` | n/a | No agent invocation |
| `plan` | V4 Pro (cached/compliance) | Issue-scoped localized research |
| `tasks` | V4 Pro | Decomposition into 30-90 min units |
| `red` | V4 Flash | Cache-hit on GREEN/REFACTOR prefix |
| `green` | V4 Flash | Same session as RED; cache reuse |
| `yellow` | V4 Pro | Isolated session, compliance gate |
| `judge` | V4 Pro | Isolated session, breaks recursive subjectivity |
| `refactor` | V4 Flash | Same session as RED/GREEN; cache reuse |
| `e2e` | V4 Flash | Single invocation |
| `execute` | V4 Flash | Single invocation |
| `hotfix` | V4 Flash | Single invocation |

## Valid Phase Keys

The 16 canonical phase names (from `_VALID_PHASES` in `src/deviate/state/config.py` lines 26-45) accepted as keys in `[models]`. Keys are matched case-insensitively; canonical form is uppercase.

| Canonical key | Used by CLI |
|---|---|
| `IDLE` | `deviate-init` |
| `EXPLORE` | `deviate-explore` |
| `RESEARCH` | `deviate-research` |
| `PRD` | `deviate-prd` |
| `SHARD` | `deviate-shard` |
| `SPECIFY` | (internal) |
| `PLAN` | `deviate-plan` |
| `TASKS` | `deviate-tasks` |
| `RED` | `deviate-red` |
| `GREEN` | `deviate-green` |
| `YELLOW` | `deviate-yellow` |
| `JUDGE` | `deviate-judge` |
| `REFACTOR` | `deviate-refactor` |
| `E2E` | `deviate-e2e` |
| `EXECUTE` | `deviate-execute` |
| `HOTFIX` | `deviate-hotfix` |

## Backend Compatibility

The `MODEL_FLAGS` map in `src/deviate/core/agent.py` (lines 78-83) controls which backends honor the resolved model ID:

| Backend | Accepts `--model` | Behavior when `[models]` is set |
|---|---|---|
| `opencode` | yes | Forwards `--model <id>` to the backend subprocess |
| `droid` | yes | Forwards `--model <id>` to the backend subprocess |
| `pi` | yes | Forwards `--model <id>` to the backend subprocess |
| `claude` | no | Ignores the resolved value silently; agent uses its own session default |

Resolution to `None` (no `[models]` section, no phase match, no `default`) means no `--model` flag is appended regardless of backend.

## Configuration

The `[models]` table is a `dict[str, str]` field on `DeviateConfig` (`src/deviate/state/config.py:115`). The loader at `_load_deviate_config_toml` (lines 124-133) silently returns `None` if the file is missing or unparseable — missing config means no model routing.

| Field | Type | Default | Description |
|---|---|---|---|
| `<phase>` | `string` | `null` | Model ID override for one phase (any of the 16 canonical phase names, case-insensitive) |
| `default` | `string` | `null` | Fallback model ID applied to any phase without an explicit override |

Example:

```toml
[models]
default = "deepseek/deepseek-v4-flash"
judge = "deepseek/deepseek-v4-pro"
research = "qwen/qwen3-235b-a22b-thinking"
```

## Source-of-Truth

| Attribute | Location |
|---|---|
| Resolution algorithm | `src/deviate/state/config.py::resolve_phase_model` (lines 136-152) |
| Loader | `src/deviate/state/config.py::resolve_model_for_phase` (lines 155-168) |
| Valid phase set | `src/deviate/state/config.py::_VALID_PHASES` (lines 26-45) |
| Pydantic model | `src/deviate/state/config.py::DeviateConfig.models` (line 115) |
| Backend dispatch | `src/deviate/core/agent.py::MODEL_FLAGS` (lines 78-83) |
| CLI invocation point | `src/deviate/cli/micro.py` lines 902, 985, 1320, 1522, 1581, 1913, 1978 |
| Macro invocation point | `src/deviate/cli/macro.py` line 740 |
| Meso invocation point | `src/deviate/cli/meso.py` line 1345 |
| TOML field comment | `src/deviate/cli/__init__.py::_CONFIG_TOML_COMMENTS["models"]` (line 89) |

## See Also

- [`.deviate/config.toml` Schema](/reference/config-toml) — full file schema including `[models]` table grammar and emit order
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — exercises `deviate setup`, which writes `.deviate/config.toml`
- [Phase State Machine](/reference/phase-state-machine) — the 16 valid phases and the artifact map per phase
- [Slash Commands](/reference/slash-commands) — slash-command inventory per phase and layer
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
