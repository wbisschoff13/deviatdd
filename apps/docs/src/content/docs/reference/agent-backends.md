---
title: "Agent Backends"
description: "Agent platform mapping — user-facing names, backend binaries, executing commands, model-flag dispatch, and per-agent slash-command directories."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Agent Backends

Agent platform selection in DeviaTDD — the five user-facing names exposed by `--agent`, the four backend binaries that meso/micro layers actually invoke, the per-backend model-flag dispatch, and the per-agent slash-command directory conventions used by `deviate setup`.

## User-Facing Names and Backend Mapping

Five user-facing agent platform names are accepted by `--agent` and the interactive `deviate init` prompt. The list is fixed at `src/deviate/cli/__init__.py:45` and the backend map at `src/deviate/cli/__init__.py:51-57`.

| User-facing name | Backend | Executing command | Notes |
|---|---|---|---|
| `factory` | `droid` | `droid exec` | Factory Droid IDE; selection prompt and `--agent` accept `factory`, but meso/micro layers dispatch the `droid` binary |
| `droid` | `droid` | `droid exec` | Direct `droid` selection; same executing binary as `factory` |
| `claude` | `claude` | `claude -p --permission-mode auto` | Print mode, `--permission-mode auto`; `--model` is ignored |
| `opencode` | `opencode` | `opencode run` | Default backend when none is persisted in `.deviate/config.toml` |
| `pi` | `pi` | `pi -p` (or `pi --mode rpc --no-session` when `pi_rpc = true`) | Native slash-command discovery via `<workdir>/.pi/prompts/` |

`AGENT_CHOICES` (the validated set accepted by `--agent`) is `("factory", "droid", "claude", "opencode", "pi")` — five values. `AGENT_TO_BACKEND` (the runtime map) has four target backends (`droid`, `claude`, `opencode`, `pi`) because `factory` collapses to `droid`.

## Backend Executing Commands

Backend-to-binary mapping resolved at agent invocation time in `src/deviate/core/agent.py:63-69`. The meso and micro layers call `AgentBackend.invoke(prompt, backend=...)` which splits the literal into argv.

| Backend | `BACKEND_COMMANDS` literal | Default invocation | Source |
|---|---|---|---|
| `opencode` | `opencode run` | `opencode run [flags] [model]` | `src/deviate/core/agent.py:64` |
| `claude` | `claude -p --permission-mode auto` | `claude -p --permission-mode auto` | `src/deviate/core/agent.py:65` |
| `droid` | `droid exec` | `droid exec [flags] [model]` | `src/deviate/core/agent.py:66` |
| `pi` | `pi -p` | `pi -p` (or `pi --mode rpc --no-session` when `pi_rpc = true`) | `src/deviate/core/agent.py:67`, `PI_RPC_COMMAND` at `src/deviate/core/agent.py:71` |
| `stub` | `stub` | test-only no-op backend | `src/deviate/core/agent.py:68` |

The `stub` backend is a test fixture and is not in `AGENT_CHOICES`; it appears only in `BACKEND_COMMANDS` for unit tests of `AgentBackend`.

## Model-Flag Dispatch

Per-backend `--model` flag behaviour resolved in `src/deviate/core/agent.py:78-83`. The resolved value comes from `resolve_phase_model` in `src/deviate/state/config.py` (see [`.deviate/config.toml` Schema](/reference/config-toml)).

| Backend | Accepts `--model` | Behaviour |
|---|---|---|
| `pi` | yes | Forwards `--model <id>` |
| `claude` | no | Ignores the resolved value silently |
| `opencode` | yes | Forwards `--model <id>` |
| `droid` | yes | Forwards `--model <id>` |

`MODEL_FLAGS[backend] is None` means the backend does not accept the flag; the resolved model value is dropped.

## Agent Selection Source-of-Truth

Agent backend selection resolves in this order, used by `deviate run`, `deviate setup`, and the meso/micro dispatchers:

| Source | Path / Flag | Precedence |
|---|---|---|
| CLI flag | `--agent <name>` on `deviate run`, `deviate setup`, `deviate init` | 1 (highest) |
| Persisted config | `.deviate/config.toml` → `[agent].backend` | 2 |
| Built-in default | `opencode` (`AgentConfig.backend` default) | 3 (lowest) |

| Field | Type | Default | Description |
|---|---|---|---|
| `[agent].backend` | `enum` | `"opencode"` | Stored backend literal; one of `"opencode"`, `"claude"`, `"droid"`, `"pi"` — `factory` is **not** a valid stored value because the prompt maps it to `droid` before persisting |
| `[agent].timeout` | `int` | `600` | Agent invocation timeout in seconds (`gt=0`) |
| `[agent].pi_rpc` | `bool` | `false` | Opt-in RPC mode for Pi; spawns `pi --mode rpc --no-session` instead of `pi -p` |

`_validate_agent_choice` (Typer callback) at `src/deviate/cli/__init__.py:363-374` rejects any `--agent` value not in `AGENT_CHOICES`. The same callback permits `None` (no flag passed) so non-interactive init can fall back to a persisted value.

## Per-Agent Slash-Command Directories

`deviate setup` discovers installed platforms by scanning the workdir for `.claude/`, `.opencode/`, `.factory/`, and `.pi/` directories. The destination path is resolved by `_get_agent_command_dir` at `src/deviate/cli/__init__.py:517-529` and then written by `_install_commands_to_agents` at `src/deviate/cli/__init__.py:532-562`. All targets require flat `.md` files — nested folders are ignored by the discovery layer.

| Agent name | Target directory | Layout | Source |
|---|---|---|---|
| `claude` | `<workdir>/.claude/commands/` | flat `.md` | `_get_agent_command_dir` (line 525-526) |
| `opencode` | `<workdir>/.opencode/commands/` | flat `.md` | `_get_agent_command_dir` (line 525-526) |
| `factory` | `<workdir>/.factory/commands/` | flat `.md` | `_get_agent_command_dir` (line 525-526) |
| `pi` | `<workdir>/.pi/prompts/` | flat `.md` | `_get_agent_command_dir` (line 527-528) |
| `droid` | _(none — returns `None`)_ | — | `droid` is a valid `--agent` value and a valid `[agent].backend` value, but `_get_agent_command_dir("droid", ...)` returns `None`; `_install_commands_to_agents` prints `SKIP Unknown agent: droid` |

The per-agent command discovery rule differs from the runtime backend: the command-directory map only knows `claude`, `opencode`, `factory`, and `pi` — `droid` is recognized at agent-invocation time (via `BACKEND_COMMANDS["droid"]`) but is not a slash-command install target.

Example (`_get_agent_command_dir` for the four install targets):

```
.claude/commands/      # --agent claude
.opencode/commands/    # --agent opencode
.factory/commands/     # --agent factory
.pi/prompts/           # --agent pi
```

The installer walks `src/deviate/prompts/commands/` (sorted by `discover_commands()` in `src/deviate/core/commands.py`) and writes each composed command (frontmatter stripped to `name` / `description` only) into every detected platform's command directory. Aggregate summary output is emitted per-agent: one `[green]INSTALL[/] <count> commands → <agent>` line per agent rather than one line per (command × agent).

## Validation and Errors

| Condition | Behaviour | Source |
|---|---|---|
| `--agent` not in `AGENT_CHOICES` | Typer error: `Invalid agent '<value>'. Must be one of: factory, droid, claude, opencode, pi` | `_validate_agent_choice` at `src/deviate/cli/__init__.py:363-374` |
| `[agent].backend` not in `Literal["opencode", "claude", "droid", "pi"]` | Pydantic `ValidationError` | `AgentConfig.backend` at `src/deviate/state/config.py:14` |
| `[agent].timeout <= 0` | Pydantic `ValidationError` (`gt=0`) | `AgentConfig.timeout` at `src/deviate/state/config.py:18` (implied by `Field(gt=0)`) |
| `--agent` omitted in non-interactive session with no persisted `[agent].backend` | `NO_AGENT_SELECTED` token on stderr, exit `1` | `deviate setup` at `src/deviate/cli/__init__.py:587-655` |
| Backend binary missing on `PATH` | `AgentBinaryNotFoundError` raised by `AgentBackend.invoke`; meso/micro surface as `AgentBinaryNotFound` failure | `src/deviate/core/agent.py:379-384` |
| Unknown backend literal at invoke time | `AgentBinaryNotFoundError(f"Unknown backend: {backend_name}")` | `src/deviate/core/agent.py:362-363` |
| `_get_agent_command_dir` returns `None` | `_install_commands_to_agents` prints `SKIP Unknown agent: <name>` and continues | `src/deviate/cli/__init__.py:544-547` |

## Source-of-Truth

| Attribute | Location |
|---|---|
| User-facing choices | `src/deviate/cli/__init__.py::AGENT_CHOICES` (line 45) |
| Backend mapping | `src/deviate/cli/__init__.py::AGENT_TO_BACKEND` (lines 51-57) |
| Validator callback | `src/deviate/cli/__init__.py::_validate_agent_choice` (lines 363-374) |
| Config read | `src/deviate/cli/__init__.py::_read_agent_backend_from_config` (lines 270-286) |
| Backend resolution | `src/deviate/cli/__init__.py::_resolve_agent_to_backend` (lines 289-296) |
| Backend literals | `src/deviate/core/agent.py::BACKEND_COMMANDS` (lines 63-69) |
| Pi RPC command | `src/deviate/core/agent.py::PI_RPC_COMMAND` (line 71) |
| Model-flag dispatch | `src/deviate/core/agent.py::MODEL_FLAGS` (lines 78-83) |
| Command dir resolver | `src/deviate/cli/__init__.py::_get_agent_command_dir` (lines 517-529) |
| Installer | `src/deviate/cli/__init__.py::_install_commands_to_agents` (lines 532-562) |
| Pydantic model | `src/deviate/state/config.py::AgentConfig` (lines 12-23) |
| Phase model resolution | `src/deviate/state/config.py::resolve_phase_model` (lines 136-152) |

## See Also

- [CLI Reference](/reference/cli) — `--agent` flag, layer routing, and `AGENT_TO_BACKEND` summary table
- [`.deviate/config.toml` Schema](/reference/config-toml) — `[agent]` table and the `Literal["opencode", "claude", "droid", "pi"]` constraint
- [Slash Commands](/reference/slash-commands) — inventory of commands installed into each per-agent directory
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — exercises `--agent` and the slash-command installer
- [How-To: run a task via the micro dispatcher](/how-to/run) — exercises `deviate run --agent`
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
