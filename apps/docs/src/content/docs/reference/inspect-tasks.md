---
title: "inspect tasks"
description: "Read-only query against the project-root tasks.jsonl ledger — derives current task states via filter_tasks() and renders a Rich table or JSON."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# inspect tasks

Read-only query of the project-root `tasks.jsonl` append-only ledger; derives current task states via `filter_tasks()` and renders either a Rich `Table` or a JSON array.

## Command

| Field | Value |
|---|---|
| Command | `deviate inspect tasks list` |
| Typer group | `tasks_app = typer.Typer(no_args_is_help=True)` |
| Registered as | `cli.add_typer(inspect_app, name="inspect")` (`src/deviate/cli/__init__.py:796`); `inspect_app.add_typer(tasks_app, name="tasks")` (`src/deviate/cli/inspect.py:25`) |
| Source | `src/deviate/cli/inspect.py::tasks_list_command` (line 165) |

The `tasks_app` sub-typer currently exposes one subcommand (`list`). Running `deviate inspect tasks` with no subcommand prints help and exits.

## Flags

| Name | Type | Default | Description |
|---|---|---|---|
| `--status` | `string` | `null` | Filter tasks by exact `status` value (one of the TaskRecord `status` literals) |
| `--json` | `bool` | `false` | Emit a JSON array of task records instead of the Rich table |
| `--quiet` | `bool` | `false` | Suppress all output; intended for pipeline use together with `--json` |

When both `--json` and `--quiet` are absent, the command renders a Rich `Table` titled `Tasks` with columns `ID | Issue ID | Description | Status | Mode`. When `--quiet` is set without `--json`, no output is produced.

## Ledger Location

| Path | Scope |
|---|---|
| `<workdir>/tasks.jsonl` | The file `tasks_list_command` reads; resolved as `Path.cwd() / "tasks.jsonl"` (`src/deviate/cli/inspect.py:147`) |

The command reads the root-level ledger only. Issue-scoped ledgers at `specs/{epic}/issues/{ISSUE_ID}/tasks.jsonl` are not consulted by this surface.

## TaskRecord Schema

Pydantic model validated against every record in `tasks.jsonl` (`src/deviate/state/ledger.py::TaskRecord`, lines 60-86). Extra fields are forbidden (`model_config = {"extra": "forbid"}`); records that fail validation are dropped from the output with a warning.

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `string` | required | Task identifier; must match regex `^TSK-\d{3}-\d{2}$` (`_validate_task_id`) |
| `issue_id` | `string` | required | Owning issue identifier (foreign key into `specs/issues.jsonl`) |
| `description` | `string` | required | One-line task summary (`min_length=1`) |
| `status` | `enum` | `PENDING` | One of `PENDING`, `RED`, `GREEN`, `YELLOW`, `YELLOW_APPROVED`, `YELLOW_REJECTED`, `JUDGE`, `REFACTOR`, `COMPLETED`, `FAILED` |
| `execution_mode` | `enum` | `TDD` | One of `TDD`, `DIRECT`, `EXECUTE`, `E2E`, `IMMEDIATE` |
| `created_at` | `datetime` | UTC now | ISO-8601 timestamp; used by the default sort |

## LedgerFilter Defaults

`filter_tasks(ledger_path, LedgerFilter)` is invoked from `_tasks_list` with these defaults (`src/deviate/cli/inspect.py:148-152` and `src/deviate/state/ledger.py::LedgerFilter`).

| Field | Type | Default | Description |
|---|---|---|---|
| `entity_type` | `enum` | `task` | Discriminator; always `task` for this command |
| `status_filter` | `string` | `null` | Pushed from the `--status` flag |
| `limit` | `int` | `20` | Maximum records returned (must be `> 0`) |
| `offset` | `int` | `0` | Pagination start (must be `>= 0`) |
| `sort_by` | `enum` | `created_at` | One of `created_at`, `timestamp`, `status` |
| `sort_desc` | `bool` | `true` | Reverse-sort by `sort_by` |

## Derived-Status Pipeline

`filter_tasks` reconstructs the canonical task state from the append-only ledger by sequential parsing.

| Step | Source | Behavior |
|---|---|---|
| Read | `_read_ledger_strict` (`src/deviate/state/ledger.py:215`) | Strict JSONL parse; raises `ValueError` on a malformed line |
| Deduplicate | `filter_tasks` (`src/deviate/state/ledger.py:233-241`) | First-seen `id` wins per task; later duplicate entries are skipped |
| Sort | `filter_tasks` (`src/deviate/state/ledger.py:244-248`) | By `sort_by` descending when `sort_desc=true` |
| Paginate | `filter_tasks` (`src/deviate/state/ledger.py:249-251`) | Slices `[offset : offset + limit]` |
| Validate | `filter_tasks` (`src/deviate/state/ledger.py:252-258`) | Each record round-trips through `TaskRecord.model_validate`; invalid records are dropped with a warning |

## Examples

```
deviate inspect tasks list
```

Filter by an exact status literal:

```
deviate inspect tasks list --status RED
```

Pipe the JSON record array into another tool:

```
deviate inspect tasks list --json --quiet | jq '.[] | select(.execution_mode == "E2E")'
```

## See Also

- [How to run /deviate-tasks](/how-to/tasks) — exercises the upstream slash-command phase whose artifact populates `tasks.jsonl`
- [Slash Commands](/reference/slash-commands) — slash-command inventory including `deviate-tasks` (meso-layer producer)
- [Macro Run Pipeline](/reference/macro-run) — meso/macro pipeline context that hands off to the TDD layer
- [Reference: look something up](/reference/intro) — quadrant index