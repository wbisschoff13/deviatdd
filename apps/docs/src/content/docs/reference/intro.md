---
title: "Reference: look something up"
description: "Information-oriented lookups for the DeviaTDD surface — commands, configs, schemas, flags, and defaults."
doc_type: reference
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Reference: look something up

This quadrant is for readers who already know what they're looking for. You have a terminal open or a config file in front of you and you need a fast, factual answer — a flag, a default, a schema field, an alias. The pages here describe surfaces; they do not walk through tasks or build a narrative. Step-by-step operator instructions live under [How-To](/how-to/intro); learning narrative lives under [Tutorials](/tutorials/intro); rationale and trade-offs live under [Explanation](/explanation/intro).

## Reference surfaces

- [CLI Reference](/reference/cli) — Every `deviate` subcommand, flag, layer routing, and exit-code semantics, sourced from `src/deviate/cli/__init__.py:774-799` and the per-module flag definitions.
- [Slash Commands](/reference/slash-commands) — Inventory of all 31 slash commands shipped under `src/deviate/prompts/commands/`, with name, aliases, layer, category, and version for each.
- [Phase State Machine](/reference/phase-state-machine) — The 16 valid `SessionState.current_phase` values, the per-phase artifact map, and the `SessionState` model fields that gate phase transitions.
- [Mise Tasks](/reference/mise-tasks) — Every `[tasks.*]` block in `mise.toml`, with shell invocation, dependency list, and purpose.
- [Starter Config](/reference/starter-config) — The three files written by `deviate setup`: `.deviate/config.toml`, project-root `.gitignore`, and project-root `.gitattributes`.
- [tome-classify Modes](/reference/tome-classify-modes) — Input modes, action enum, gate behaviors, confidence range, and report sections for the Tome C1 classifier.
- [tome-classify Report Schema](/reference/tome-report-schema) — Data schema for the Tome C1 classification report: capability table columns, action enum, status enum, gate precedence, and section structure.
- [Tome List](/reference/tome-list) — Flags, Rich-table vs JSON output, column fields, and row schema for the `deviate tome list` CLI subcommand.
- [Tome Writers](/reference/tome-write) — Reference for the four quadrant-disciplined writer slash commands gated by the report.
## See Also

- [Tutorials: a guided tour](/tutorials/intro)
- [How-To: accomplish a specific task](/how-to/intro)
- [Explanation: understand the why](/explanation/intro)
- [Slash Commands](/reference/slash-commands)
- [CLI Reference](/reference/cli)
