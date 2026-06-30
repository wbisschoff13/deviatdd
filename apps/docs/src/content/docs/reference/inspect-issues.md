---
title: "Inspect Issues"
description: "Read-only inspect subcommands that query specs/issues.jsonl and per-issue tasks.jsonl, with --json and --quiet output modes."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Inspect Issues

Read-only queries against `specs/issues.jsonl` and per-issue `tasks.jsonl` for listing issues and tasks, with `--json` and `--quiet` output modes for tooling integration.

## Command Group

| Field | Value |
|---|---|
| Group | `inspect` |
| Source | `src/deviate/cli/inspect.py` |
| Registered as | `cli.add_typer(inspect_app, name="inspect")` (`src/deviate/cli/__init__.py:796`) |
| Sub-groups | `inspect issues`, `inspect tasks` |
| Typer container | `inspect_app = typer.Typer(no_args_is_help=True)` |

## Subcommands

| Path | Source function | Purpose |
|---|---|---|
| `inspect issues list` | `src/deviate/cli/inspect.py::issues_list_command` | List entries from `specs/issues.jsonl`, deduplicated by `issue_id` |
| `inspect tasks list` | `src/deviate/cli/inspect.py::tasks_list_command` | List entries from the active epic's `tasks.jsonl` via `filter_tasks` |

## `inspect issues list` Flags

| Name | Type | Default | Description |
|---|---|---|---|
| `--type` | `string` | `null` | Filter by issue `type` (e.g., `feature`, `hotfix`, `adhoc`) |
| `--status` | `enum` | `null` | Filter by issue status from the `IssueRecord` literals |
| `--json` | `bool` | `false` | Emit the result set as a JSON array on stdout |
| `--quiet` | `bool` | `false` | Suppress non-JSON output (Rich table) |

## `inspect tasks list` Flags

| Name | Type | Default | Description |
|---|---|---|---|
| `--status` | `enum` | `null` | Filter by task status from the `TaskRecord` literals |
| `--json` | `bool` | `false` | Emit the result set as a JSON array on stdout |
| `--quiet` | `bool` | `false` | Suppress non-JSON output (Rich table) |

## Issue Output Schema

When `--json` is set, `inspect issues list` emits a JSON array where each entry carries the following fields.

| Field | Type | Always present | Description |
|---|---|---|---|
| `issue_id` | `string` | yes | Stable ledger identifier, e.g., `ISS-001-003` |
| `type` | `string` | yes | Issue type label; free-form string (`feature`, `hotfix`, `adhoc`) |
| `title` | `string` | yes | Human-readable title from the ledger record |
| `status` | `enum` | yes | One of `DRAFT`, `BACKLOG`, `SPECIFIED`, `SHARDED`, `COMPLETED` |
| `source_file` | `string` | yes | Path to the issue spec file, relative to repo root |
| `blocked_by` | `list[string]` | yes | `issue_id` values this issue is sequentially blocked by |
| `coordinates_with` | `list[string]` | yes | `issue_id` values this issue laterally coordinates with |
| `orphan_claim` | `bool \| null` | yes | Tri-state claim flag; see Orphan Claim Logic |

## Task Output Schema

When `--json` is set, `inspect tasks list` emits a JSON array where each entry carries the following fields.

| Field | Type | Always present | Description |
|---|---|---|---|
| `id` | `string` | yes | Task identifier matching `^TSK-\d{3}-\d{2}$` |
| `issue_id` | `string` | yes | Owning issue `issue_id` |
| `description` | `string` | yes | Single-line description of the task |
| `status` | `enum` | yes | One of `PENDING`, `RED`, `GREEN`, `YELLOW`, `YELLOW_APPROVED`, `YELLOW_REJECTED`, `JUDGE`, `REFACTOR`, `COMPLETED`, `FAILED` |
| `execution_mode` | `enum` | yes | One of `TDD`, `DIRECT`, `EXECUTE`, `E2E`, `IMMEDIATE` |

## Orphan Claim Logic

`orphan_claim` is computed only for `SPECIFIED` issues by `_check_orphan_claim` and resolved against the configured remote via `git ls-remote --heads <remote> <branch>`.

| Condition | `orphan_claim` value | Rich table marker |
|---|---|---|
| Remote branch missing | `true` | `🟡 ORPHAN_CLAIM` |
| Remote branch present | `false` | _(empty)_ |
| `subprocess.TimeoutExpired`, `OSError`, non-zero `git` exit | `null` | _(empty)_ |
| Issue status is not `SPECIFIED`, or `source_file` is empty | `null` | _(empty)_ |

`inspect tasks list` does not surface an `orphan_claim` field.

## Source-of-Truth

| Attribute | Location |
|---|---|
| Typer app | `src/deviate/cli/inspect.py::inspect_app` |
| Issue sub-typer | `inspect_app.add_typer(issues_app, name="issues")` |
| Task sub-typer | `inspect_app.add_typer(tasks_app, name="tasks")` |
| Issue ledger read | `src/deviate/state/ledger.py::_read_ledger_strict` |
| Issue schema | `src/deviate/state/ledger.py::IssueRecord` |
| Task schema | `src/deviate/state/ledger.py::TaskRecord` |
| Tasks filtering | `src/deviate/state/ledger.py::filter_tasks` |
| Deduplication | `src/deviate/cli/inspect.py::_deduplicate_issues` |

## Examples

List every issue as a JSON array:

```
deviate inspect issues list --json
```

Filter issues by status and emit JSON:

```
deviate inspect issues list --status SPECIFIED --json
```

Inspect tasks for the active epic:

```
deviate inspect tasks list --json
```

Combine `--json` and `--quiet` to drop the Rich table and emit only JSON on stdout:

```
deviate inspect issues list --json --quiet
```

## See Also

- [Slash Commands](/reference/slash-commands) — the per-phase slash commands that emit entries consumed by `inspect`
- [Macro Run Pipeline](/reference/macro-run) — automated macro-layer pipeline that produces the ledger entries `inspect` queries
- [Reference: look something up](/reference/intro) — quadrant index
