---
title: "Execution Profiles"
description: "Execution-profile preset surface — ExecutionProfile literal, resolve_profile() skip-flag mapping, --profile CLI flag, and composable --no-judge/--no-refactor overrides."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-002-001
---

# Execution Profiles

Preset config-group surface that controls which micro-cycle phases execute (`red`, `green`, `judge`, `refactor`). Resolved per `deviate run` invocation via `resolve_profile()` in `src/deviate/core/profile.py`; gated by the `--profile` CLI flag with composable `--no-judge` / `--no-refactor` boolean overrides.

## `ExecutionProfile` Type

| Name | Type | Definition | Description |
|---|---|---|---|
| `ExecutionProfile` | `Literal["full", "fast", "secure"]` | `src/deviate/core/profile.py:4` | Constrains the `--profile` CLI input; rejects any other value at Typer callback time |

## `DeviateConfig.profile` TOML Field

Stored under `<workdir>/.deviate/config.toml` and emitted by `deviate setup`. See [`.deviate/config.toml` Schema](/reference/config-toml) for the full top-level scalar table.

| Field | Type | Default | Validation | Description |
|---|---|---|---|---|
| `profile` | `string` | `"default"` | freeform `str` (no `Literal` constraint) | Preset config-group name; documented values are `"default"`, `"full"`, `"fast"`, `"secure"` but the field accepts arbitrary text |

The `DeviateConfig` model (`src/deviate/state/config.py:107`) validates the field only as a free-form `str`. The TOML comment emitted by `deviate setup` (`src/deviate/cli/__init__.py:85`) reads `Preset config group: "default", "full", "fast", or "secure"`. The value is **not consumed at runtime** by `resolve_profile()` — phase execution is gated exclusively by the `--profile` CLI flag on `deviate run`.

## `resolve_profile()` Mapping

`resolve_profile(profile, no_judge=None, no_refactor=None) -> tuple[bool, bool]` returns the `(no_judge, no_refactor)` pair forwarded to `_run_single` and `_run_all` as `no_judge` / `no_refactor` keyword arguments.

| Profile | `no_judge` | `no_refactor` | Phases run |
|---|---|---|---|
| `full` | `false` | `false` | RED + GREEN + JUDGE + REFACTOR |
| `fast` | `true` | `true` | RED + GREEN |
| `secure` | `false` | `true` | RED + GREEN + JUDGE |
| _any other_ | _(raises `ValueError`)_ | _(raises `ValueError`)_ | Typer callback rejects with `Invalid profile '<name>'. Must be one of: full, fast, secure` |

Source: `_PROFILE_DEFAULTS` at `src/deviate/core/profile.py:6-11`; resolver at `src/deviate/core/profile.py:16-32`.

## Composable Boolean Overrides

`--no-judge` and `--no-refactor` are forwarded to `resolve_profile()` as explicit arguments. When either is set to a concrete `bool` (`true` or `false`), it overrides the profile baseline; when `None` (the default), the profile's baseline is retained.

| `--no-judge` | `--no-refactor` | `--profile` | Effective `(no_judge, no_refactor)` |
|---|---|---|---|
| `None` | `None` | `full` | `(false, false)` |
| `true` | `None` | `full` | `(true, false)` |
| `None` | `true` | `full` | `(false, true)` |
| `None` | `None` | `fast` | `(true, true)` |
| `false` | `None` | `fast` | `(false, true)` — explicit `false` overrides `fast`'s `true` baseline |
| `true` | `true` | `secure` | `(true, true)` — explicit flags win over `secure`'s `(false, true)` baseline |

Source: `resolve_profile()` precedence at `src/deviate/core/profile.py:27-31`.

## `--profile` CLI Flag

| Flag | Type | Default | Valid values | Description |
|---|---|---|---|---|
| `--profile` | `enum` | `"full"` | `full` \| `fast` \| `secure` | Execution profile; mapped to `(no_judge, no_refactor)` via `resolve_profile()`; rejected at Typer callback for any other value |

Defined on `deviate run` at `src/deviate/cli/micro.py:3322-3327`. The Typer callback `_validate_profile` (`src/deviate/cli/micro.py:3308-3314`) raises `typer.BadParameter` for invalid values. The full flag table for `deviate run` lives in [CLI Reference — `deviate run`](/reference/cli#deviate-run).

## Validation

| Condition | Behaviour | Source |
|---|---|---|
| `profile` not in `_PROFILE_DEFAULTS` | `resolve_profile()` raises `ValueError`; Typer callback re-raises as `typer.BadParameter` with message `Invalid profile '<name>'. Must be one of: full, fast, secure` | `src/deviate/core/profile.py:21-24`; `src/deviate/cli/micro.py:3308-3314` |
| `no_judge` / `no_refactor` typed as `bool` (not `Optional`) | `no_judge: bool \| None` on `run_command` accepts `None`; concrete `bool` overrides profile baseline | `src/deviate/cli/micro.py:3328-3331` |
| `DeviateConfig.profile` set to arbitrary text (e.g., `"banana"`) | Pydantic accepts the value (no `Literal`); only the CLI callback enforces the allowlist | `src/deviate/state/config.py:107` |

## Source-of-Truth

| Attribute | Location |
|---|---|
| `ExecutionProfile` literal | `src/deviate/core/profile.py:4` |
| `_PROFILE_DEFAULTS` map | `src/deviate/core/profile.py:6-11` |
| `resolve_profile()` function | `src/deviate/core/profile.py:16-32` |
| `DeviateConfig.profile` field | `src/deviate/state/config.py:107` |
| TOML comment annotation | `src/deviate/cli/__init__.py::_CONFIG_TOML_COMMENTS["profile"]` (line 85) |
| `--profile` Typer option | `src/deviate/cli/micro.py:3322-3327` |
| `--profile` Typer callback | `src/deviate/cli/micro.py::_validate_profile` (lines 3308-3314) |
| `resolve_profile()` call site | `src/deviate/cli/micro.py:3394` |
| Downstream consumer (`_run_single`, `_run_all`) | `src/deviate/cli/micro.py:3415-3422` |

## Examples

Run a micro task through the `fast` profile (skip JUDGE and REFACTOR):

```
deviate run TSK-001-03 --profile fast
```

Skip only REFACTOR on top of the `full` profile baseline:

```
deviate run TSK-001-03 --profile full --no-refactor
```

Override `secure`'s JUDGE-on default with an explicit `--no-judge`:

```
deviate run TSK-001-03 --profile secure --no-judge
```

## See Also

- [`.deviate/config.toml` Schema](/reference/config-toml) — the top-level `profile` scalar field, its free-form-string constraint, and the TOML comment annotation
- [CLI Reference — `deviate run`](/reference/cli#deviate-run) — the `--profile`, `--no-judge`, `--no-refactor` rows on the micro dispatcher
- [Model Routing](/reference/model-routing) — per-phase MODEL overrides under `[models]`; a distinct surface from phase-skip profiles, resolved by a different function (`resolve_phase_model`)
- [How to run a task via the micro dispatcher](/how-to/run) — exercises `--profile fast`, `--profile secure`, and the composable boolean overrides in a full TDD cycle
- [How to run the /deviate-judge phase](/how-to/judge) — how the JUDGE phase yields to a `fast` profile or `--no-judge` and transitions to REFACTOR (or `IDLE` on `--no-refactor`)
- [Reference: look something up](/reference/intro) — quadrant index
