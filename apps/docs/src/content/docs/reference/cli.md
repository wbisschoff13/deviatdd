---
title: "CLI Reference"
description: "Every `deviate` subcommand, flag, layer routing, and exit-code semantics, sourced from `src/deviate/cli/__init__.py:774-799` and the per-module flag definitions."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-001
  - ISS-001-002
  - ISS-001-003
  - ISS-001-004
---

# CLI Reference

Every subcommand exposed by the `deviate` entry point, its flags, layer routing, and exit-code semantics — the surface a developer or operator consults while a terminal is open.

## Top-Level Command

| Field | Value |
|---|---|
| Binary | `deviate` |
| Entry point | `src/deviate/cli/__init__.py::cli` (`typer.Typer(no_args_is_help=True)`) |
| Callback | `main()` at `src/deviate/cli/__init__.py:69-78` |
| Subcommand registration | `cli.add_typer(...)` and `cli.command(...)` at `src/deviate/cli/__init__.py:774-799` |

| Flag | Type | Default | Description |
|---|---|---|---|
| `--version` | `bool` | `false` | Print the installed `deviate` version from `importlib.metadata.version("deviate")` and exit |

## Subcommand Index

22 subcommands ship in `8daa502`. The `Layer` column maps each command to the layer model documented in `specs/DeviaTDD-api.md` Part 1.

| Subcommand | Layer | Group | Source |
|---|---|---|---|
| `deviate setup` | Bootstrap | flat | `src/deviate/cli/__init__.py::setup` |
| `deviate init` | Bootstrap | Typer | `src/deviate/cli/init.py::init_app` |
| `deviate constitution` | Bootstrap | Typer | `src/deviate/cli/constitution.py::constitution_app` |
| `deviate explore` | Macro | Typer | `src/deviate/cli/macro.py::explore_app` |
| `deviate research` | Macro | Typer | `src/deviate/cli/macro.py::research_app` |
| `deviate prd` | Macro | Typer | `src/deviate/cli/macro.py::prd_app` |
| `deviate shard` | Macro | Typer | `src/deviate/cli/macro.py::shard_app` |
| `deviate feature` | Macro | Typer | `src/deviate/cli/feature.py::feature_app` |
| `deviate adhoc` | Macro | Typer | `src/deviate/cli/adhoc.py::adhoc_app` |
| `deviate specify` | Meso | flat | `src/deviate/cli/meso.py::specify` |
| `deviate plan` | Meso | flat | `src/deviate/cli/meso.py::plan` |
| `deviate tasks` | Meso | flat | `src/deviate/cli/meso.py::tasks` |
| `deviate pr` | Meso | flat | `src/deviate/cli/meso.py::pr` |
| `deviate meso` | Meso | Typer | `src/deviate/cli/meso.py::meso_app` |
| `deviate red` | Micro | Typer | `src/deviate/cli/micro.py::red_app` |
| `deviate green` | Micro | Typer | `src/deviate/cli/micro.py::green_app` |
| `deviate yellow` | Micro | Typer | `src/deviate/cli/micro.py::yellow_app` |
| `deviate judge` | Micro | Typer | `src/deviate/cli/micro.py::judge_app` |
| `deviate refactor` | Micro | Typer | `src/deviate/cli/micro.py::refactor_app` |
| `deviate execute` | Micro | Typer | `src/deviate/cli/micro.py::execute_app` |
| `deviate e2e` | Micro | Typer | `src/deviate/cli/micro.py::e2e_app` |
| `deviate hotfix` | Micro | Typer | `src/deviate/cli/micro.py::hotfix_app` |
| `deviate run` | Micro dispatcher | flat | `src/deviate/cli/micro.py::run_command` |
| `deviate inspect` | Inspection | Typer | `src/deviate/cli/inspect.py::inspect_app` |
| `deviate review` | Gate 3 | Typer | `src/deviate/cli/review.py::review_app` |
| `deviate tome` | Tome | Typer | `src/deviate/cli/tome.py::tome_app` |

## Bootstrap & Governance

### `deviate setup`

Flat alias for `deviate init` (legacy entry point at `src/deviate/cli/__init__.py:587-655`). Idempotent: re-running never duplicates rules.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--agent-export-mode` | `enum` | `local` | Agent export mode; `local` writes to `<workdir>/.<agent>/commands/`, `global` writes to `~/.claude/` |
| `--graphite` | `bool` | `false` | Enable Graphite CLI integration; merges `graphite = true` into `config.toml` and installs the Graphite governance block |
| `--libref` | `bool` | `false` | Force-enable `libref` CLI integration; merges `use_libref = true` into `config.toml`; overrides PATH detection |
| `--agent` | `enum` | `null` | Override auto-detected agent platform; one of `factory`, `droid`, `claude`, `opencode`, `pi` |

| Output token | Trigger |
|---|---|
| `NO_AGENT_SELECTED` | `--agent` omitted in non-interactive session with no persisted `[agent].backend` |

### `deviate init`

Typer sub-group registered via `cli.add_typer(init_app, name="init")`.

| Path | Source function | Purpose |
|---|---|---|
| `deviate init pre` | `src/deviate/cli/init.py::pre` | Detect project type, scaffold DeviaTDD structure, emit JSON contract |
| `deviate init post` | `src/deviate/cli/init.py::post` | Validate artifacts, stage for commit, emit status JSON |

`init pre` and `init post` accept no positional args or flags beyond Typer's built-ins.

### `deviate constitution`

Typer sub-group for `specs/constitution.md` governance.

| Path | Source function | Flag / Arg | Type | Default | Description |
|---|---|---|---|---|---|
| `deviate constitution generate` | `constitution.py::generate` | `--force` | `bool` | `false` | Overwrite existing `constitution.md` |
| `deviate constitution pre` | `constitution.py::pre` | _(none)_ | | | Validate `constitution.md`, extract commands, emit JSON |
| `deviate constitution post <manifest>` | `constitution.py::post` | `<manifest>` | `path` | _(required)_ | Path to manifest JSON; commit on success |

| Output token | Trigger |
|---|---|
| `FAILURE` | Missing file, validation failure, or missing `## TESTING_PROTOCOLS` section |

## Macro Layer

All macro `pre` commands are decorated with `@with_json_quiet` from `src/deviate/cli/_common.py` and therefore auto-expose `--json` and `--quiet`.

### `deviate explore`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate explore pre` | `<problem>` | `string` | _(required)_ | Problem description |
| `deviate explore pre` | `--slug` | `string` | `null` | Explicit explore slug override |
| `deviate explore post` | `--slug` | `string` | `null` | Explore slug to validate |
| `deviate explore post` | `--force` | `bool` | `false` | Bypass phase validation |

### `deviate research`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate research pre` | `--slug` | `string` | `null` | Explore slug; auto-discovers latest from `specs/explore/` if omitted |
| `deviate research post` | `--epic` | `string` | `null` | Epic slug (e.g., `003-prompt-optimization`) |
| `deviate research post` | `--force` | `bool` | `false` | Bypass phase validation |

### `deviate prd`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate prd pre` | `--epic` | `string` | `null` | Epic slug; auto-discovers latest if omitted |
| `deviate prd pre` | `--dry-run` | `bool` | `false` | Preview contract without side effects |
| `deviate prd post` | `<manifest>` | `path` | _(required)_ | Path to PRD manifest JSON |
| `deviate prd post` | `--force` | `bool` | `false` | Bypass phase validation |

### `deviate shard`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate shard pre` | `--epic` | `string` | `null` | Epic slug; auto-discovers latest if omitted |
| `deviate shard pre` | `--dry-run` | `bool` | `false` | Preview contract without side effects |
| `deviate shard post` | `<manifest>` | `path` | _(required)_ | Path to shard manifest JSON |
| `deviate shard post` | `--epic` | `string` | `null` | Override epic slug from manifest |
| `deviate shard post` | `--force` | `bool` | `false` | Bypass phase validation |

### `deviate feature`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate feature create` | `<title>` | `string` | _(required)_ | Feature title; kebab-case slug is derived automatically |
| `deviate feature create` | `--slug` | `string` | `null` | Explicit slug override (bypasses derivation) |

| Output token | Trigger |
|---|---|
| `GRAPHITE_NOT_FOUND` | `gt` binary missing on PATH (when `graphite = true`) |
| `GRAPHITE_FAILED` | `gt create` exits non-zero |

### `deviate adhoc`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate adhoc pre` | `<description>` | `string` | _(required)_ | Task description; classified via `ComplexityGate` |
| `deviate adhoc pre` | `--skip-gates` | `bool` | `false` | Skip `COMPLEXITY_GATE_REJECTION` for HIGH complexity tasks |
| `deviate adhoc pre` | `--flow-ref` | `string` | `null` | Comma-separated `FLOW-XX` IDs (matches `^FLOW-\d{2,}$`) |
| `deviate adhoc post` | `<issue-id>` | `string` | _(required)_ | Issue/manifest ID to mark complete |

| Output token | Trigger |
|---|---|
| `COMPLEXITY_GATE_REJECTION` | HIGH complexity without `--skip-gates` |
| `INVALID_FLOW_REF` | `--flow-ref` token does not match `^FLOW-\d{2,}$` |
| `MANIFEST_NOT_FOUND` | `issue_id` not present in `specs/adhoc.jsonl` |

## Meso Layer

All meso `pre` commands are decorated with `@with_json_quiet` from `src/deviate/cli/_common.py` and auto-expose `--json` and `--quiet`.

### `deviate specify`

Legacy flat command (Specify absorbed into Shard; use `deviate shard pre/post` for new work).

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate specify <issue-id>` | `<issue-id>` | `string` | _(required)_ | Issue ID, or literal `pre` / `post` |
| `deviate specify <issue-id>` | `--force` | `bool` | `false` | Bypass push failure |
| `deviate specify <issue-id>` | `--dry-run` | `bool` | `false` | Resolve issue and emit contract; no worktree, no claim |
| `deviate specify <issue-id>` | `--issue` | `string` | `null` | Issue ID for the `pre` subcommand (overrides positional) |

### `deviate plan`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate plan <issue-id>` | `<issue-id>` | `string` | _(required)_ | Issue ID, or literal `pre` / `post` |
| `deviate plan <issue-id>` | `--force` | `bool` | `false` | Bypass push / validation guards |
| `deviate plan <issue-id>` | `--dry-run` | `bool` | `false` | Preview without side effects |
| `deviate plan <issue-id>` | `--issue` | `string` | `null` | Issue ID override for `pre` |

### `deviate tasks`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate tasks <issue-id>` | `<issue-id>` | `string` | _(required)_ | Issue ID, or literal `pre` / `post` |
| `deviate tasks <issue-id>` | `--force` | `bool` | `false` | Bypass validation |
| `deviate tasks <issue-id>` | `--dry-run` | `bool` | `false` | Preview without side effects |
| `deviate tasks <issue-id>` | `--issue-id` | `string` | `null` | Issue ID override for `post` |

### `deviate pr`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate pr <action>` | `<action>` | `string` | _(required)_ | Action literal: `pre` (validate) or `run` (create PR) |
| `deviate pr run` | `--body-file` | `path` | _(required for `run`)_ | Path to PR body file |
| `deviate pr run` | `--merge` | `bool` | `false` | Merge immediately after PR creation |
| `deviate pr run` | `--auto-merge` | `bool` | `false` | Enable GitHub auto-merge |

| Output token | Trigger |
|---|---|
| `MISSING_BODY_FILE` | `--body-file` omitted from `deviate pr run` |
| `UNKNOWN_ACTION` | `<action>` not in `{pre, run}` |

### `deviate meso run`

Automated meso pipeline: claim → plan → tasks → IDLE.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--issue` | `string` | `null` | Target issue ID; defaults to next unblocked `BACKLOG` issue |
| `--dry-run` | `bool` | `false` | Emit slim prompt only; no claim, no worktree, no agent call, no commits |
| `--force` | `bool` | `false` | Bypass `blocked_by` dependency check |
| `--quiet` / `--verbose` | `bool` | `true` | Suppress non-essential output (default: quiet) |

## Micro Layer

### `deviate red`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate red pre` | `--task` / `-t` | `string` | `null` | Task ID (`TNNN` or `TSK-NNN-NN`) |
| `deviate red post` | _(none)_ | | | Run `pytest -v`; verify failure is `ASSERTION_FAILURE` |

### `deviate green`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate green pre` | `--task` / `-t` | `string` | `null` | Task ID |
| `deviate green post` | _(none)_ | | | Verify `pytest -v` returns 0; run `TamperGuard` in `GREEN_IMPLEMENTATION` context |

### `deviate yellow`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate yellow pre` | `--task` / `-t` | `string` | `null` | Task ID |
| `deviate yellow post` | `--approved` | `bool` | `false` | Approve `<propose_test_amendment>` block; commit and force session to `GREEN` |
| `deviate yellow post` | `--rejected` | `bool` | `false` | Reject amendments; `git restore .`; force session to `GREEN` |

### `deviate judge`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate judge pre` | _(none)_ | | | Detect phase changes, scan `spec.md` for protected modules, emit JSON verdict |

### `deviate refactor`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate refactor pre` | `--task` / `-t` | `string` | `null` | Task ID |
| `deviate refactor post` | _(none)_ | | | Verify GREEN transition exists; run AST return-type check; rollback on regression |

### `deviate execute`

`execute pre` skips the RED phase — direct execution mode for `DIRECT` / `IMMEDIATE`-typed tasks.

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate execute pre` | `--task` / `-t` | `string` | `null` | Task ID |
| `deviate execute post` | `<task_id>` | `string` | `null` | Task ID; auto-discovered from session if empty |
| `deviate execute post` | `<subject>` | `string` | `""` | Commit subject; auto-generated from task ID if empty |
| `deviate execute post` | `<body>` | `string` | `null` | Optional commit body |

### `deviate e2e`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate e2e pre` | _(none)_ | | | Halt if any task across all ledgers is not `COMPLETED` |
| `deviate e2e post` | `<manifest>` | `string` | `null` | Optional manifest JSON path |

### `deviate hotfix`

| Path | Arg / Flag | Type | Default | Description |
|---|---|---|---|---|
| `deviate hotfix pre` | `--task` / `-t` | `string` | `null` | Task ID |
| `deviate hotfix post` | `<manifest>` | `string` | `null` | Optional manifest JSON path |

### `deviate run`

Top-level dispatcher that routes tasks by `execution_mode` (TDD cycle or direct execute).

| Arg / Flag | Type | Default | Description |
|---|---|---|---|
| `<task-id>` | `string` | `null` | Task ID (`TNNN` or `TSK-NNN-NN`); auto-selects next PENDING when omitted |
| `--all` | `bool` | `false` | Run all PENDING tasks for the active issue sequentially |
| `--profile` | `enum` | `full` | Execution profile: `full` (RED + GREEN + JUDGE + REFACTOR), `fast` (RED + GREEN), `secure` (RED + GREEN + JUDGE) |
| `--no-judge` | `bool` | `null` | Skip JUDGE phase (composable profile override) |
| `--no-refactor` | `bool` | `null` | Skip REFACTOR phase (composable profile override) |
| `--agent` | `string` | `null` | Override agent backend; falls back to `[agent].backend` in `.deviate/config.toml` |
| `--json` | `bool` | `false` | Emit JSONL events (`task_started`, `phase_change`, `task_completed`, `task_failed`, `pipeline_halted`, `pipeline_complete`) |
| `--dry-run` | `bool` | `false` | Print resolved task(s) and exit without dispatching |
| `--verbose` | `bool` | `false` | Print debug diagnostics |

| Output token | Trigger |
|---|---|
| `PhaseFailedError` | Exhaustion of `max_train_attempts = 3` (TDD) or `max_judge_attempts = 3` (execute) |
| Exit `1` | `deviate run --all` halted on first failed task |

## Inspection

### `deviate inspect`

Typer sub-group registered via `cli.add_typer(inspect_app, name="inspect")`. Two sub-groups: `inspect issues` and `inspect tasks`. See [Inspect Issues](/reference/inspect-issues) for the complete flag and output-schema table.

## Review (HITL Gate 3)

### `deviate review pre`

Lightweight PR/merge review at Gate 3. No flag other than the standard.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--base` | `string` | `main` | Base branch for merge-base computation |
| `--branch` | `string` | `null` | Target branch; defaults to `HEAD` for a self-contained review |

## Tome Subsystem

### `deviate tome`

Typer sub-group registered via `cli.add_typer(tome_app, name="tome")`.

#### `deviate tome write`

Fan-out writer invocations across the rows of a `/tome-classify` report.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--from-report` | `path` | _(required)_ | Path to a `/tome-classify` markdown report (must exist) |
| `--workers` / `-w` | `int` | `4` | Parallel writer invocations (range 1-32) |
| `--timeout` / `-t` | `int` | `600` | Per-writer timeout in seconds (minimum 10) |
| `--backend` | `enum` | `null` | Override agent backend (`opencode` / `droid` / `claude` / `pi`); falls back to `.deviate/config.toml [agent].backend`, then `opencode` |
| `--actions` | `string` | `create,update` | Comma-separated actions to process |
| `--no-resume` | `bool` | `false` | Re-run rows whose target file already exists (default: skip existing) |
| `--log` | `path` | `.deviate/tome-batch.log` | Per-row log file path; empty string disables logging |
| `--dry-run` | `bool` | `false` | Print the dispatch plan and exit without dispatching |

| Output token | Trigger |
|---|---|
| Exit `1` | One or more dispatched rows returned non-DONE status |

#### `deviate tome list`

Print the rows of a `/tome-classify` report as a Rich table or JSON array.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--from-report` | `path` | _(required)_ | Path to a `/tome-classify` markdown report (must exist) |
| `--json` | `bool` | `false` | Emit a JSON array of row records instead of a Rich table |

## Common Flags

Flags injected by the `@with_json_quiet` decorator in `src/deviate/cli/_common.py` and shared across macro and meso `pre` commands.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--json` | `bool` | `false` | Capture stdout, serialize the command's return value as JSON, print only JSON |
| `--quiet` | `bool` | `false` | Suppress non-JSON stdout while preserving stderr |
| `--force` | `bool` | `false` | Bypass phase validation or pre-flight guards (per-command semantics) |
| `--dry-run` | `bool` | `false` | Preview contract / dispatch plan without side effects |

`--json` and `--quiet` are orthogonal: `--json --quiet` emits JSON on stdout and errors on stderr. The decorator only applies to functions that are wrapped with `@with_json_quiet` — listed in the **Macro Layer** and **Meso Layer** subcommand tables above.

## Agent Backend Selection

`--agent` resolves via the `AGENT_TO_BACKEND` map in `src/deviate/cli/__init__.py:51-57`.

| User-facing name | Backend binary | Notes |
|---|---|---|
| `factory` | `droid` | Factory Droid IDE; commands dir `.factory/commands/` |
| `droid` | `droid` | Underlying binary both `factory` and `droid` dispatch to |
| `claude` | `claude` | Print mode, `--permission-mode auto`; `--model` may be ignored |
| `opencode` | `opencode` | Default backend when none persisted |
| `pi` | `pi` | Native slash-command discovery via `<workdir>/.pi/prompts/` |

## Exit Codes

| Code | Meaning | Source |
|---|---|---|
| `0` | Success — phase artifact validated and committed, or contract emitted | all `pre`/`post`/`run` paths |
| `1` | Failure — validation error, missing artifact, missing manifest, `NO_AGENT_SELECTED`, `MISSING_BODY_FILE`, agent non-zero exit | `typer.Exit(code=1)` calls (40+ sites) |
| `78` | `EX_CONFIG` — internal configuration error | `src/deviate/cli/micro.py:2449` |
| `130` | `SIGINT` — interrupted by the user | `src/deviate/cli/micro.py:2295` |

Failure exits are surfaced as `[red]<TOKEN>: <message>[/]` on stderr via Rich before the `typer.Exit(code=1)` raise. See [Macro Run Pipeline](/reference/macro-run) for the halt-token pattern applied across macro layers.

## Layer Routing

| Layer | Phases | CLI subcommands | Source module |
|---|---|---|---|
| Bootstrap | Governance | `setup`, `init`, `constitution` | `src/deviate/cli/__init__.py`, `init.py`, `constitution.py` |
| Macro | Feature scoping | `explore`, `research`, `prd`, `shard`, `feature`, `adhoc` | `src/deviate/cli/macro.py`, `feature.py`, `adhoc.py` |
| Meso | Issue engineering | `specify`, `plan`, `tasks`, `pr`, `meso` | `src/deviate/cli/meso.py` |
| Micro | TDD sandbox | `red`, `green`, `yellow`, `judge`, `refactor`, `execute`, `e2e`, `hotfix`, `run` | `src/deviate/cli/micro.py` |
| Inspection | Read-only queries | `inspect` | `src/deviate/cli/inspect.py` |
| Gate 3 | Review | `review` | `src/deviate/cli/review.py` |
| Tome | Docs fan-out | `tome` | `src/deviate/cli/tome.py` |

## Examples

Bootstrap a fresh workspace with the Factory backend and Graphite enabled:

```
deviate setup --agent factory --graphite
```

Run the full macro pipeline against a feature bucket:

```
deviate macro run --target auth-jwt
```

Dispatch a single micro task through the `fast` profile (RED + GREEN only):

```
deviate run TSK-001-03 --profile fast --agent opencode
```

Fan out `/tome-write-*` invocations across a classification report with 8 parallel writers:

```
deviate tome write --from-report tome-report.md --workers 8 --backend opencode
```

List every issue in JSON form:

```
deviate inspect issues list --json
```

## See Also

- [Slash Commands](/reference/slash-commands) — inventory of the per-phase slash commands installed by `deviate setup`
- [Macro Run Pipeline](/reference/macro-run) — automated macro-layer pipeline (`explore → research → prd → shard`)
- [Inspect Issues](/reference/inspect-issues) — complete flag and output schema for `deviate inspect`
- [How to bootstrap a DeviaTDD workspace](/how-to/setup) — exercises `deviate setup` and `deviate init`
- [How to run a task via the micro dispatcher](/how-to/run) — exercises `deviate run` and the TDD cycle
- [How to run /deviate-explore](/how-to/explore) — first macro phase
- [How to run /deviate-plan](/how-to/plan) — meso bridge from shard to tasks
- [How to run /deviate-red](/how-to/red) — RED phase mechanics
- [How to run /deviate-execute](/how-to/execute) — direct execute mode (no RED)
- [How to run the /deviate-judge phase](/how-to/judge) — compliance evaluation
- [Reference: look something up](/reference/intro) — quadrant index