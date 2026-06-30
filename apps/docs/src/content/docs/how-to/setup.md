---
title: "Bootstrap a DeviaTDD workspace"
description: "Run `deviate setup` to scaffold `.deviate/`, install the slash-command library, and seed the append-only ledger merge rules."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-001
  - ISS-ADH-010
  - ISS-ADH-011
---

# Bootstrap a DeviaTDD workspace

This how-to covers `deviate setup` — the one-time workspace bootstrap that scaffolds `.deviate/config.toml`, installs the full slash-command library into every supported agent platform directory, provisions a placeholder `specs/constitution.md`, and seeds the union-merge rules in the root `.gitattributes` that make `specs/issues.jsonl` concurrent-branch safe. After this command runs, every `/deviate-*` and `/tome-*` slash command is available in the agent prompt palette and the operator can move on to [Initialize a repo with DeviaTDD conventions](/how-to/init) (if the project is brand-new) or jump straight into the [first-run tutorial](/tutorials/starter-first-run).

## Prerequisites

- **Python 3.13** — `deviate` targets `>=3.13` per `pyproject.toml:5`. The fastest way to get a working Python is [mise](https://mise.jdx.dev/) with the `[env] python = "3.13"` block already shipped in `mise.toml`.
- **`uv`** — used to install the `deviate` package as an editable tool. Install via `mise use uv@latest` or `pipx install uv`.
- **An agent platform installed and on `PATH`** — pick exactly one of: `factory` (Droid IDE, defaults backend), `claude` (Claude Code), `opencode` (OpenCode CLI), or `pi` (Pi coding agent). The slash-command library is installed into *all four* directories regardless of which one you pick, but `[agent].backend` is set to your choice and that value drives meso/micro dispatch.
- **A git-initialized working directory** — `deviate setup` mutates `.gitattributes` and `.gitignore` at the repo root. Running it outside a git repo is supported but the merge-rule seeding has no effect.
- **`libref` (optional)** — if `libref` is on `PATH` (or you pass `--libref`), the scaffolded `.deviate/config.toml` gets `use_libref = true` and the operator can use offline library lookups during the macro layer.

## Steps

### 1. Install the `deviate` CLI as an editable tool

From the project root, install the package so the `deviate` command resolves on `PATH`. The mise task wraps this for you.

```bash
mise run install-tool
# equivalent to: uv tool install --editable .
```

Verify the install by printing the version:

```bash
deviate --version
```

Expected output: `deviate 2.0.0` (or whatever the current `pyproject.toml` `version` field resolves to).

### 2. Choose your agent platform

Pick exactly one. The choice is persisted to `[agent].backend` in `.deviate/config.toml` and consumed by the meso/micro layers when they dispatch a model invocation. If you skip the flag, `deviate setup` will interactively prompt you in a TTY and abort with `NO_AGENT_SELECTED` in non-interactive shells.

```bash
# Common cases — pick one:
deviate setup --agent factory    # Factory Droid IDE
deviate setup --agent claude     # Claude Code
deviate setup --agent opencode   # OpenCode CLI
deviate setup --agent pi         # Pi coding agent
```

If you're on the deviatdd repo itself (or any project where `~/.claude/skills/` already has a `deviate` global install), pass `--agent-export-mode local` to keep the scaffolded config project-scoped:

```bash
deviate setup --agent pi --agent-export-mode local
```

### 3. Run the bootstrap

`deviate setup` is idempotent — re-running it on a configured workspace does not duplicate `.gitignore` entries, does not rewrite the `constitution.md` you populated during `/research`, and merges `--graphite` / `--libref` flag toggles surgically into an existing `.deviate/config.toml`. The full invocation:

```bash
deviate setup --agent pi
```

Expected console output (truncated):

```
Initializing deviate workspace...
  CREATE  config.toml
  CREATE  session.json
  CREATE  .gitignore
  INSTALL 32 commands → claude
  INSTALL 32 commands → opencode
  INSTALL 32 commands → factory
  INSTALL 32 commands → pi
  CREATE  .gitignore with 4 agent entries
  CREATE  .gitattributes with union-merge rules
```

### 4. Verify the scaffold

Confirm the bootstrap landed correctly. The slash-command library is installed into all four agent directories regardless of the `--agent` choice, so you should see populated directories in each.

```bash
# Config exists and has the backend you chose
cat .deviate/config.toml

# All four agent directories have slash commands
ls .claude/commands/ | head -5
ls .opencode/commands/ | head -5
ls .factory/commands/ | head -5
ls .pi/prompts/ | head -5

# Constitution placeholder is in place
test -f specs/constitution.md && echo "OK"

# Root .gitattributes has the union-merge rules
grep "merge=union" .gitattributes
```

If you picked `--agent pi`, you should also see `[agent] backend = "pi"` in `.deviate/config.toml`. If you picked `--agent factory`, the value is `droid` (the underlying backend binary that the Factory Droid IDE wraps).

### 5. Open your agent platform and confirm the palette

Launch the agent you chose in step 2 — for example, run `pi` in the project root, or open the Factory Droid IDE in this directory. Every `/deviate-*` and `/tome-*` slash command should appear in the prompt palette. If the palette is empty, see the **Troubleshooting** section.

## Troubleshooting

### `NO_AGENT_SELECTED` error on a CI runner or scripted invocation

`deviate setup` aborts with `NO_AGENT_SELECTED` when the session is non-interactive (no TTY) and no `--agent` flag was passed. Fix by passing the flag explicitly — never rely on the interactive prompt in automation.

```bash
deviate setup --agent pi    # or factory, claude, opencode
```

### Slash commands not appearing in the agent's prompt palette

Two common causes. First, the agent platform may have cached the old directory tree — restart the agent process and reload the command palette. Second, the agent platform convention may differ — Factory, Claude, and OpenCode discover commands from `.<agent>/commands/`, but Pi uses `.<agent>/prompts/`. Confirm the right directory was populated for your agent:

```bash
ls .pi/prompts/    # for --agent pi
ls .claude/commands/    # for --agent claude
```

If the directory is empty, re-run `deviate setup` — installation is idempotent and will re-populate any agent directory whose commands went missing.

### `Invalid agent '<name>'. Must be one of: factory, droid, claude, opencode, pi`

`--agent` only accepts the five canonical choices. `droid` is the underlying backend binary, and `factory` is the Droid IDE that wraps it — they map to the same `.factory/commands/` directory. If you want a custom agent backend, edit `.deviate/config.toml` directly after running setup; the meso/micro layer will read whatever value you set in `[agent].backend`.

### Setup ran but `.deviate/config.toml` was not created

The config file is only written when the file does not exist AND `--graphite` / `--libref` are not passed (in that case the existing config is updated surgically, not recreated). If your file is missing, check that the working directory is writable and that no `umask` is preventing `.deviate/` from being created. Then re-run with the `--libref` flag — that flag forces a config merge even on an existing file, and the resulting error message will tell you why the write failed.

### `.gitattributes` was created but `merge=union` is not taking effect

`merge=union` is a git driver that requires a clean rebase or merge to take effect. If you ran `deviate setup` after the branch was already in the middle of a merge, the rules are in the file but git has already chosen a different driver. Abort the merge (`git merge --abort`), then `git pull` — git will pick up the new attributes on the next merge.

## Next Steps

- [Initialize a repo with DeviaTDD conventions](/how-to/init) — next task if this is a brand-new repository; scaffolds `mise.toml` and the `specs/` tree.
- [First-run tutorial](/tutorials/starter-first-run) — guided walk through `deviate setup` → first slash command → first TDD task; use this if you want context before continuing.
- [Reference: `deviate` CLI flags](/reference/cli#deviate-setup) — every flag on the `deviate setup` command, including `--agent-export-mode`, `--graphite`, and `--libref`.
- [Reference: agent backends](/reference/agent-backends) — the `factory`/`droid`/`claude`/`opencode`/`pi` mapping and per-agent command-directory convention.
- [Reference: starter config](/reference/starter-config) — the canonical `.deviate/config.toml`, `.gitignore`, and `.gitattributes` shapes that `deviate setup` produces.
- [Explanation: starter architecture](/explanation/starter-architecture) — design rationale for what `deviate setup` scaffolds and why the append-only ledger merge rules matter.
