---
title: "Tome List"
description: "Reference for the `deviate tome list` CLI subcommand — flags, Rich-table vs JSON output, column fields, and row schema for listing /tome-classify report rows."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Tome List

The `deviate tome list --from-report <path>` subcommand reads a `/tome-classify` markdown report, parses its capability table, and prints the rows either as a Rich table (default) or as a JSON array (`--json`).

## Command

| Field | Value |
|---|---|
| Command | `deviate tome list` |
| Source | `src/deviate/cli/tome.py::list_command` |
| Registered as | `cli.add_typer(tome_app, name="tome")` then `tome_app.command("list")` (`src/deviate/cli/__init__.py:799`) |
| Typer group | `tome_app = typer.Typer(no_args_is_help=True)` |
| Predecessor | `/tome-classify` (Tome C1) — emits the markdown report this command parses via `parse_classification_report` |

The command is read-only: it does not invoke any writer slash command, dispatch any agent backend, or write to `target_file`.

## Flags

| Name | Type | Default | Description |
|---|---|---|---|
| `--from-report` | `path` | _(required)_ | Path to a `/tome-classify` markdown report file (must exist and be readable) |
| `--json` | `bool` | `false` | Emit a JSON array of row records on stdout instead of a Rich table |

`--from-report` is validated by Typer (`exists=True, readable=True`); a missing or unreadable file aborts the command with Typer's standard error before any row parsing occurs.

## Rich Table Output

When `--json` is omitted, the command builds a `rich.table.Table` titled `Classification Report — <report-name> (<n> rows)` and renders it via the global Rich `Console`. Each capability row becomes one rendered table row.

| Column | Source field | Style | Description |
|---|---|---|---|
| `Capability` | `row.capability` | `cyan` | Truncated to 60 characters with a trailing `…` when over the limit (per `_format_capability(capability, 60)`) |
| `DocType` | `row.doc_type` | `magenta` | One of `tutorial` \| `how-to` \| `reference` \| `explanation` |
| `Action` | `row.action` | `green` (when `create`) \| `yellow` (when `update`) \| `dim` (when `no-change`) \| `red` (when `human-review` or `setup-required`) \| `white` (fallback) | Color of the action label is determined by the `_print_table` action-style map |
| `Confidence` | `row.confidence` | right-aligned | Floating-point confidence rendered as `{row.confidence:.2f}` |
| `Target` | `row.target_file` | _(default)_ | The literal `target_file` from the report; rendered as `—` when null (i.e., `setup-required` rows) |

The `Confidence` cell is right-aligned via `justify="right"`; `Capability` is `no_wrap=False` so long capability descriptions wrap inside the cell rather than clip the row.

## JSON Output Schema

When `--json` is set, the command emits a JSON array (pretty-printed with `indent=2`) on stdout via `typer.echo`. Each element carries the seven fields below; the object key order matches the declaration in `list_command` so that downstream tooling can rely on positional parsing.

| Field | Type | Always present | Description |
|---|---|---|---|
| `capability` | `string` | yes | User-facing capability description from the report's `capability` column |
| `evidence` | `string` | yes | Verbatim file paths and/or commit messages from the report's `evidence` column |
| `audience` | `string` | yes | Audience literal from the report's `audience` column |
| `doc_type` | `string` | yes | Quadrant literal from the report's `doc_type` column |
| `action` | `string` | yes | Action literal from the report's `action` column |
| `target_file` | `string \| null` | yes | Target path from the report's `target_file` column; `null` when the row carries `setup-required` |
| `confidence` | `number` | yes | Floating-point confidence in `[0.0, 1.0]`; rendered as the parsed `float` value (not rounded) |

`parse_classification_report` skips malformed rows silently; rows that cannot be parsed (wrong column count, unparseable confidence) are dropped before `deviate tome list` sees them. The JSON array therefore only contains rows that passed parser validation.

## Action Style Map

The color applied to the `Action` cell in the Rich-table output is resolved by the `_print_table` action-style map. Default fall-through uses `white`.

| Action | Color |
|---|---|
| `create` | `green` |
| `update` | `yellow` |
| `no-change` | `dim` |
| `human-review` | `red` |
| `setup-required` | `red` |
| _(any other value)_ | `white` |

## Row Source Schema

The rows consumed by this command are produced by `parse_classification_report` (`src/deviate/tome/parser.py::parse_classification_report`) into `CapabilityRow` instances. The dataclass (`src/deviate/tome/parser.py:34-49`) declares the seven fields below; the same fields are surfaced by `--json`.

| Field | Type | Description |
|---|---|---|
| `capability` | `str` | User-facing capability description |
| `evidence` | `str` | Verbatim file paths and/or commit messages |
| `audience` | `str` | One of `developer` \| `operator` \| `end-user` \| `contributor`; comma-separated when multiple |
| `doc_type` | `str` | One of `tutorial` \| `how-to` \| `reference` \| `explanation` |
| `action` | `str` | One of `create` \| `update` \| `no-change` \| `human-review` \| `setup-required` |
| `target_file` | `str` | Normalized target path; literal `null` cell becomes empty string, then rendered as `—` in the table |
| `confidence` | `float` | Closed `[0.0, 1.0]`; default `0.0` if the cell fails `_parse_confidence` |

## Source-of-Truth

| Attribute | Location |
|---|---|
| Command definition | `src/deviate/cli/tome.py::list_command` (`@tome_app.command("list")`) |
| Typer app | `src/deviate/cli/tome.py::tome_app` (`typer.Typer(no_args_is_help=True)`) |
| Mounting | `cli.add_typer(tome_app, name="tome")` in `src/deviate/cli/__init__.py` |
| Row parser | `src/deviate/tome/parser.py::parse_classification_report` |
| Row dataclass | `src/deviate/tome/parser.py::CapabilityRow` |
| Confidence parser | `src/deviate/tome/parser.py::_parse_confidence` |
| Target normalizer | `src/deviate/tome/parser.py::_normalize_target_file` |

## Examples

List the rows of a report as a Rich table:

```
deviate tome list --from-report tome-report.md
```

Emit the same rows as a JSON array (suitable for piping into `jq` or a downstream dashboard):

```
deviate tome list --from-report tome-report.md --json
```

## See Also

- [CLI Reference](/reference/cli) — every `deviate` subcommand, including `deviate tome` and the `tome list` flag reference at the CLI level
- [tome-classify Report Schema](/reference/tome-report-schema) — the seven-column capability table this command parses
- [tome-classify Modes](/reference/tome-classify-modes) — input modes that produce the report consumed by `tome list`
- [Tome Writers](/reference/tome-write) — the writer slash commands dispatched by `deviate tome write` against the rows listed here
- [Slash Commands](/reference/slash-commands) — inventory of all shipped slash commands including `tome-classify`
- [Reference intro](/reference/intro) — navigation map for the reference quadrant
