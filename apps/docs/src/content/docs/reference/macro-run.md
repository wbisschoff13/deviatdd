---
title: "Macro Run Pipeline"
description: "Single-invocation macro pipeline running explore→research→prd→shard phases sequentially, advancing the session through each gate."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-008
---

# Macro Run Pipeline

Single-invocation automation of the macro layer that runs `explore → research → prd → shard` sequentially as one CLI command.

## Command

| Field | Value |
|---|---|
| Command | `deviate macro run` |
| Source | `src/deviate/cli/macro.py` (`macro_run_command`) |
| Registered as | `cli.add_typer(macro_app, name="macro")` (`src/deviate/cli/__init__.py:783`) |
| Typer group | `macro_app = typer.Typer(no_args_is_help=True)` |

## Flags

| Name | Type | Default | Description |
|---|---|---|---|
| `--target` | `string` | `null` | Target feature bucket slug; resolves to `<specs_root>/<target>`; defaults to the latest epic discovered via `discover_latest_epic()` |
| `--from` | `enum` | `null` | Resume from a specific phase; one of `explore`, `research`, `prd`, `shard`; forces session transition to the preceding required state |
| `--dry-run` | `bool` | `false` | Emit JSON contracts and slim-prompt bodies for each phase without side effects; no agent call, no commits, no session transitions |
| `--force` | `bool` | `false` | Bypass pre-flight guards when invoking each phase's `post` script |

## Phase Order

Phases execute in the fixed order below. When `--from` is supplied, execution starts at the named phase and the session is force-transitioned to the required preceding state.

| # | Phase | Required upstream artifact | Produced artifact | Session transition on exit |
|---|---|---|---|---|
| 1 | `explore` | _(none)_ | `specs/<bucket>/explore.md` | `IDLE → EXPLORE` |
| 2 | `research` | `specs/<bucket>/explore.md` | `specs/<bucket>/design.md`, `specs/<bucket>/data-model.md` | `EXPLORE → RESEARCH` |
| 3 | `prd` | `design.md`, `data-model.md` | `specs/<bucket>/prd.md`, `.deviate/artifacts/manifest_prd.json` | `RESEARCH → PRD` |
| 4 | `shard` | `prd.md` | entries appended to `specs/issues.jsonl`, `.deviate/artifacts/manifest_shard.json` | `PRD → SHARD → IDLE` |

Upstream-missing halts: phase `research` halts with `UPSTREAM_MISSING` if `explore.md` is absent.

## Session Predecessor Map

When `--from` is supplied, the session is force-transitioned to the required preceding state before the named phase runs.

| `--from` value | Required preceding `current_phase` |
|---|---|
| `explore` | `IDLE` |
| `research` | `EXPLORE` |
| `prd` | `RESEARCH` |
| `shard` | `PRD` |

On successful completion of the full pipeline, the session is force-transitioned to `IDLE`.

## Halts

| Token | Trigger | Source line |
|---|---|---|
| `MACRO: INVALID_PHASE` | `--from` value not in `_PHASE_ORDER` | `_macro_run` (`src/deviate/cli/macro.py:827`) |
| `MACRO: BUCKET_NOT_FOUND` | `--target` slug does not exist under `specs/` | `_macro_discover_bucket` (`src/deviate/cli/macro.py:756`) |
| `MACRO: no epic discovered` | No target provided and `discover_latest_epic()` returned empty | `_macro_run` (`src/deviate/cli/macro.py:831`) |
| `RESEARCH: UPSTREAM_MISSING` | `research` phase reached without `explore.md` | `_cycle_phase` (`src/deviate/cli/macro.py:776`) |

## Example

```
deviate macro run --target auth-jwt
```

Resume from a specific phase, bypassing the explore/research/prd outputs and forcing the session to the required predecessor state:

```
deviate macro run --target auth-jwt --from shard --force
```

Dry-run prints the JSON contract and slim prompt for every phase in the run without mutating state:

```
deviate macro run --target auth-jwt --dry-run
```

## See Also

- [Slash Commands](/reference/slash-commands) — Inventory of the per-phase slash commands (`/deviate-explore`, `/deviate-research`, `/deviate-prd`, `/deviate-shard`) that this pipeline automates
- [How to run /deviate-explore](/how-to/explore) — procedural walkthrough of the first phase in the sequence
- [How to run /deviate-research](/how-to/research) — procedural walkthrough of the second phase in the sequence
- [Reference: look something up](/reference/intro) — quadrant index