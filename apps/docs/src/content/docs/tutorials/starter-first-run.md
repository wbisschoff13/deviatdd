---
title: "Your first DeviaTDD session"
description: "Walk through `deviate setup`, open the agent platform, run `/deviate-init`, then trigger `/deviate-explore` to land your first exploration task end-to-end."
doc_type: tutorial
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-001
  - ISS-ADH-010
  - ISS-ADH-011
---

# Your first DeviaTDD session

By the end of this tutorial you will have bootstrapped a DeviaTDD workspace with `deviate setup`, opened the agent platform you chose, confirmed the slash-command library is wired up, run one slash command for the first time, and triggered your first macro-layer task — an exploration scan that writes `specs/explore/<slug>.md` to disk. Every creative step is a slash command; your hands stay on the keyboard only to read state and verify the agent's work.

You do not write any code in this tutorial — the agent does the operational work.

## Prerequisites

Before you start, make sure your workstation has DeviaTDD installed and a git repo to work in:

- **DeviaTDD installed** — `deviate --version` must print a version (currently `deviate 2.0.0`). If it does not, follow Step 1 of [Bootstrap a DeviaTDD workspace](/how-to/setup): install the `deviate` package as an editable tool with `mise run install-tool` (or `uv tool install --editable .`).
- **An agent platform installed** — pick exactly one of: `pi` (Pi coding agent), `claude` (Claude Code), `factory`/`droid` (Factory Droid IDE), or `opencode` (OpenCode CLI). Setup installs the slash-command library into every supported agent directory regardless of which one you pick; the `--agent` flag only sets the `[agent].backend` value consumed by the meso/micro layers.
- **A git-initialized working directory** — any repo works, including one you just `git init`'d inside. The repo does not need a `README.md` or any commits yet; the bootstrap is happy with an empty tree.

## Step 1 — Run `deviate setup`

Open a terminal at the repo root and run the bootstrap. The `--agent` flag selects which agent the meso/micro layers dispatch to; the slash-command library is mirrored into every supported agent directory regardless.

```bash
deviate setup --agent pi
```

Substitute `pi` for `claude`, `factory`, or `opencode` if you have a different agent.

> Why this exists: `deviate setup` is the one-time workspace bootstrap. It writes `.deviate/config.toml`, mirrors the slash-command library into `.pi/prompts/` (and `.claude/commands/`, `.factory/commands/`, `.opencode/commands/`), seeds a placeholder `specs/constitution.md`, and writes the union-merge rules into the root `.gitattributes`. After this one command, every `/deviate-*` and `/tome-*` slash command becomes available in your agent's prompt palette. The full source for this command lives at `src/deviate/cli/__init__.py:587-659`.

Expected result (output is truncated for readability — the important lines are the `INSTALL` rows):

```
Initializing deviate workspace...
  CREATE  config.toml
  CREATE  session.json
INSTALL <N> commands → pi
INSTALL <N> commands → claude
INSTALL <N> commands → opencode
INSTALL <N> commands → factory
  CREATE  .gitignore with 4 agent entries
  CREATE  .gitattributes with union-merge rules
```

If you see `NO_AGENT_SELECTED`, your shell is non-interactive and you forgot the `--agent` flag. Re-run with the flag explicitly.

## Step 2 — Verify the slash library landed (verification action)

Confirm Step 1 actually wrote the prompt files. The directory depends on the agent you picked.

```bash
ls .pi/prompts/ | head -5
```

Substitute `.pi/prompts/` for `.claude/commands/`, `.factory/commands/`, or `.opencode/commands/` if you picked a different agent. Expected result:

```
deviate-adhoc.md
deviate-architecture.md
deviate-constitution.md
deviate-e2e.md
deviate-execute.md
```

If the directory is empty, re-run `deviate setup --agent <name>`. Setup is idempotent — re-running never duplicates files.

## Step 3 — Open your agent and check the prompt palette

Launch the agent you chose in Step 1. For Pi, that means running `pi` from the project root:

```bash
pi
```

Inside the agent, type `/` and look at the slash-command palette. You should see the full `/deviate-*` family (init, explore, research, prd, shard, plan, tasks, red, green, yellow, judge, refactor, e2e, pr, ...) and the `/tome-*` family (classify, setup, verify-docs, write-tutorial, write-how-to, write-reference, write-explanation).

If the palette is empty, your agent platform may have cached the old directory tree — quit the agent and reopen it. For Pi specifically, no `~/.pi/agent/` writes happen during setup; if Pi's palette is empty after reopen, double-check that `.pi/prompts/` is populated (Step 2) and that you launched Pi from the project root, not a sibling directory.

## Step 4 — Run your first slash command: `/deviate-init`

For a brand-new repo (no `mise.toml` yet, no `specs/` directory), the natural first slash command is `/deviate-init`. Type this in the agent prompt box and submit:

```text
/deviate-init
```

> Why this is your "first slash command": init scaffolds the project-level conventions DeviaTDD needs to do anything else — a `mise.toml` whose `test` task exits 0 even with no tests written yet (the **zero-test-pass invariant** that the RED phase relies on), a `specs/` directory with `constitution.md` and an empty append-only `specs/issues.jsonl` ledger, and the union-merge rules in `.gitattributes`. For an existing repo that already has these, `/deviate-init` is a no-op — it detects the existing artifacts, skips the writes, and returns SUCCESS.

Expected result (the slash command runs the pre/post scripts and emits a JSON contract on stdout):

```json
{
  "phase": "deviate-init",
  "status": "READY",
  "project_type": "python",
  "artifacts_created": ["mise.toml", "specs/", "specs/issues.jsonl", "specs/constitution.md", ".gitattributes"],
  "mise_available": true
}
```

`project_type` is auto-detected from `mix.exs`, `pyproject.toml`, `package.json`, `Cargo.toml`, or `go.mod`. An unrecognised repo scaffolds as `unknown` with `test = "echo 'No test framework' || true"` and init still succeeds. If `project_type` is `unknown`, you may want to edit `mise.toml` afterward to wire your real test runner.

## Step 5 — Trigger your first task: `/deviate-explore`

The first concrete task DeviaTDD knows how to do is "explore a feature" — a read-only structural scan of one feature bucket that writes an `explore.md` summary to disk. In your agent prompt box:

```text
/deviate-explore my-first-feature
```

Substitute `my-first-feature` with a kebab-case slug describing one feature you want to characterize (`user-auth`, `billing-webhook`, `cli-typer-setup`, ...). The slash command is fully autonomous and zero-touch: it runs the pre/post scripts, dispatches two read-only subagents (a codebase scanner and an ecosystem researcher), and writes the markdown file. You do not call any subagent by hand.

> Why this is your "first task": explore is the macro-layer phase that produces `specs/explore/<slug>.md`, the input to downstream phases (`/deviate-research` for High complexity, `/deviate-adhoc` for Low/Medium complexity). Without an explore pass, those phases have nothing to consume. This is the smallest end-to-end unit of work the system can do — read-only, autonomous, zero-touch — and the "feel-completion" moment of this tutorial.

Expected result (the slash command writes `specs/explore/my-first-feature.md` and emits the Status Summary table):

```
STATUS: SUCCESS
EXPLORE_SLUG: my-first-feature
GIT_BRANCH: <your current branch>
SPEC_TARGET: specs/explore/my-first-feature.md
NEXT_ACTION: Run `/deviate-adhoc` (Low/Medium complexity) or `/deviate-research` (High complexity) — see `## Scope Sizing` in the explore.md artifact
```

You can open `specs/explore/my-first-feature.md` in any editor — it is a static markdown document that catalogs what exists in the codebase, with a `## Scope Sizing` table near the bottom that classifies the feature as Low / Medium / High complexity.

## Verification

Confirm the whole end-to-end flow by inspecting the four artifacts the tutorial produced:

```bash
# Step 1: setup wrote the config
ls .deviate/config.toml

# Step 1: setup installed the slash library (substitute your agent's directory)
ls .pi/prompts/deviate-init.md

# Step 4: init scaffolded governance
ls specs/constitution.md

# Step 5: explore produced a feature brief
ls specs/explore/*.md
```

Each command should print a real path. If any path is missing, walk back through the matching step above.

To prove the test pipeline is wired up end-to-end, also run a test pass:

```bash
mise run test
```

Expected result: on a freshly-initialized repo with no tasks yet, `mise run test` exits 0 with `no tests ran` or `0 tests collected`. That is the **zero-test-pass invariant** — it confirms the micro layer can dispatch a failing test in a future tutorial and have the runner pick it up cleanly.

## Next Steps

- [Your first RED → GREEN → REFACTOR cycle](/tutorials/first-red-green) — once your project is initialized and you have an `explore.md` and (eventually) a `tasks.jsonl` with one PENDING row, this tutorial walks one task through the TDD micro loop end-to-end.
- [Tutorials: a guided tour](/tutorials/intro) — back to the tutorial quadrant's navigation map.
- [How to bootstrap a workspace](/how-to/setup) — the operator reference for `deviate setup`, including troubleshooting and non-TTY invocation patterns.
- [Reference: slash commands](/reference/slash-commands) — every `/deviate-*` and `/tome-*` slash command shipped, indexed by layer (macro / meso / micro / tome).
