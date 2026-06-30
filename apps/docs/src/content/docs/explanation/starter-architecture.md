---
title: "How the Setup Scaffold Emerges"
description: "Why `deviate setup` writes what it writes: `.deviate/`, the four agent command dirs, and the gitignore/gitattributes seeds — all idempotently."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-001
---

# How the Setup Scaffold Emerges

What does `deviate setup` actually leave behind in a working directory, and why is the shape of that residue the same on every machine it runs on? The answer is a deliberately narrow contract: the operator runs one command, the framework writes a fixed set of files at fixed paths, and re-running the command produces zero diff against committed state. Every other property of the scaffold — the absence of global config, the placeholder constitution, the four-agent installation fan-out, the `merge=union` rules in the root `.gitattributes` — falls out of that one contract.

## Context

DeviaTDD's value sits in three places: the append-only ledgers that record every phase transition, the three HITL gates that cannot be bypassed by flag, and the Tamper Guard that constrains micro-layer writes to `src/**/*.py`. None of those features do anything until the files they depend on exist. A fresh working directory has a `.git/` folder and possibly a `README.md`; it does not yet have `specs/issues.jsonl`, `[agent]` tables, or a constitution the macro layer can populate. The bootstrap is the bridge between "the operator owns a git repo" and "the operator can run `/deviate-explore`."

The natural prior art would be one of two shapes. A global config directory in the user's home — the shape `~/.claude/`, `~/.config/deviate/`, and most CLIs adopt — would mean a single install serves every project, but it also entangles project identity with user identity, and the operator's per-project customizations have nowhere to live. A template repository the operator copies into a fresh project would keep the scaffold version-controllable, but it would silently drift from the live code path: every change to a helper would require a corresponding edit to the seed file, with no enforcement that the two stayed in sync. DeviaTDD takes a third path: the framework owns the bootstrap process end-to-end via a single CLI subcommand, and the contract that command honors is idempotency.

## Rationale

Six decisions stack on top of the idempotency contract, and each one narrows the shape of the workspace.

The first is that *every helper is additive rather than rewriting*. `_scaffold_dotfiles` writes `.deviate/config.toml` only if the file is absent; `_ensure_root_gitignore` and `_ensure_root_gitattributes` parse the existing file, append the missing union-merge rules or command-pattern entries, and preserve user-authored lines verbatim; `_scaffold_constitution` writes a placeholder only when `specs/constitution.md` does not exist. Re-running setup is a no-op against committed state for the same reason `git restore -- <path>` against a clean tree is a no-op: the helpers check existence before writing. This is what lets setup be re-invoked during onboarding of a new agent, after a flag change, and during recovery from a botched experiment without losing user data.

The second is that *the slash-command library is installed into all four supported agent directories regardless of which one the operator chose* via `--agent`. The choice persists into `[agent].backend` in `.deviate/config.toml` and is consumed by the meso and micro layers when they dispatch a model invocation; it does *not* gate which directory receives the install. An operator who picks Claude Code today and Pi tomorrow does not lose `/deviate-*` access on Pi because the command set is in `.pi/prompts/` from setup time. The four targets — `.claude/commands/`, `.opencode/commands/`, `.factory/commands/`, `.pi/prompts/` — are all populated by the same `_install_commands_to_agents` call.

The third is that *workspace config stays at the workdir root, never under `~/`*. `.deviate/config.toml`, `.deviate/session.json`, and `.deviate/artifacts/` are project-owned; the operator's Pi config, Claude settings, and global preferences are explicitly out of scope. The cost is a per-checkout run of `deviate setup` when the operator moves to a new machine, but the benefit is that monorepos and per-project overrides have a stable address space.

The fourth is that *`specs/constitution.md` is a placeholder, not a pre-populated scaffold*. The constitution's content — tech stack standards, testing protocols, the project-specific Definition of Done — only the macro layer's `/research` phase has the codebase context to populate. Setup writes a Version 0.1.0 file with `TBD` markers in five sections and trusts the next phase to fill them in. A setup that probed for the language or guessed the test command would produce a constitution that lies about the project until the macro layer corrects it.

The fifth is that *the root `.gitignore` patterns are path-scoped to `*/commands/` and `*/prompts/`*. A broader `**/deviate-*.md` pattern would silently ignore `src/deviate/prompts/commands/deviate-*.md` — the very files DeviaTDD's own repository uses as its source of truth — and the per-project install of the same library would exclude the development repo's commands. The four explicit patterns cover every supported backend and any future agent that follows the flat-file convention, while leaving the project-internal prompt sources alone.

The sixth is that *the root `.gitattributes` declares `merge=union` for the JSONL ledgers at setup time*. This is the operational seam between this page and a deeper architectural decision: ledgers are append-only, line-oriented, and concurrent-branch safe because git's `merge=union` driver merges them by line, keeping every unique line across branches and emitting no conflict markers. The constants `DEVIATE_GITATTRIBUTES_SEED` in `src/deviate/cli/__init__.py` carry the exact text, and `_ensure_root_gitattributes` provisions them idempotently. Without setup committing those rules, the ledger protocol documented in [Why Append-Only Ledgers](/explanation/append-only-ledger) would silently revert to line-level conflicts at every concurrent merge.

## Mental Model

Picture two regions side by side: the *deviate-owned* scaffold on the left, and the *git-tracked* indicators on the right. The setup command writes the left region once, and the right region is a small footer that lets git treat the left region's append-only ledgers correctly.

```
                deviate setup  (idempotent: re-runs produce 0 diff)
                       │
   ┌───────────────────┼──────────────────────────────┬──────────────────┐
   ▼                   ▼                              ▼                  ▼
 .deviate/         specs/                  .claude/ .opencode/       project root
   config.toml     constitution.md         .factory/   .pi/         .gitignore
   session.json    (TBD placeholder)        commands/   prompts/     .gitattributes
   artifacts/                                                   specs/issues.jsonl
   .gitignore                                                 (merge=union)
```

The framework owns `.deviate/` entirely — every field there is either set by setup or appended by the running CLI; the operator rarely writes into it. The four agent dirs are pure output: setup fills them with the command library and the per-agent runtime ignores them. The gitignore and gitattributes are the only files setup touches that the operator is likely to read by hand, and they are written *for* git rather than *for* the operator — they exist so that a concurrent-branch ledger merge does not produce conflict markers, and so that the agent command files do not pollute the operator's commit history.

## Trade-Offs

What the scaffold earns.

*Reproducibility.* Every operator who runs `deviate setup` lands at the same workspace shape. An how-to that says "open `.deviate/config.toml`" works without platform caveats, because the file exists at that exact path on every machine the framework supports. *Switching cost reduction.* An operator moving from one agent backend to another mid-project does not lose access to the command library, because setup populates every supported agent dir up front and the operator's choice is only which one is *selected*, not which one is *installed*. *Discipline on root-level files.* The scaffold is a forcing function: any feature that needs a new file at the repo root must update `_ensure_root_*` so it lands during setup rather than appearing at random mid-session.

What the scaffold gives up.

*No migration path for older workspaces.* If `.deviate/config.toml` gains a new required field, the helper's idempotent-merge path may not pick it up on existing installations; the operator either runs setup with the relevant `--force` flag, edits the file by hand, or skips the upgrade. Setup also has *no rollback*: once the scaffold files are written, setup does not remove them, and uninstallation is an explicit operator action. And the placeholder constitution means a workspace committed immediately after setup will ship a `specs/constitution.md` that says "TBD" in five places — operators are expected to run `/research` before any meaningful work continues.

Rejected alternatives, named so the trade-off is auditable.

- **A global install surface in `~/.<agent>/`.** Would have unified setup across projects on one machine, but at the cost of coupling user identity to project identity. Two checkouts of the same repo on the same machine would compete for the same command directory, and the operator's `.gitignore` patterns could not reliably distinguish project-owned from user-owned slash commands without additional bookkeeping.
- **A monolithic `deviate init.yaml` template the operator copies.** Would have made the scaffold version-controllable in the framework's own repository, but every helper would have a corresponding copy in the seed file, and the two would silently diverge as the helpers evolved. The review surface for a copy-pasted template is also strictly larger than the review surface for a code path.
- **Interactive prompts during setup to populate the constitution.** Would have produced a richer scaffold out of the box, but would have required setup to know the project's tech stack — exactly the information the macro layer is structured to discover later. Pre-filling fields the macro layer will re-derive is wasted motion, and any incorrect guess has to be undone by the next phase.

## Implications

The scaffold is the foundation that every other phase assumes. The micro-layer agents read `specs/issues.jsonl` and `specs/**/tasks.jsonl`; the verify routine reads `[agent].backend` from `.deviate/config.toml` to dispatch the model; the inspect commands parse the same ledgers to derive canonical state. Setup's hard guarantee is that the canonical file layout is in place before any of those readers run. Its soft guarantee is idempotent updates to that layout when the framework evolves.

A new feature that introduces a new root-level file therefore has to add a corresponding `_ensure_root_*` helper so the new file appears during setup rather than on first invocation of the feature — that is the only mechanism that keeps the canonical layout stable across fresh and existing workspaces.

What becomes easier: reproducibility (fresh clone plus `deviate setup` produces an identical workspace), platform switching (the operator can move between agents without command-library loss), and recovery (re-running setup after a botched experiment is safe because the helpers are additive). What becomes harder: machine migration of an existing `.deviate/` between versions of DeviaTDD — every schema change needs a hand-rolled migration path because setup does not own that surface — and detecting silent manual drift: the verifier does not currently inspect `.deviate/`, so a hand-edited scaffold file is not surfaced as a violation.

## See Also

- [Why Append-Only Ledgers](/explanation/append-only-ledger) — the deeper rationale for the `merge=union` rules this scaffold seeds into `.gitattributes`; this page owns the file-provisioning half, that page owns the data-model half.
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — the operator task that exercises the design described here, including the agent flag, the libref auto-detection, and the idempotency contract in practice.
- [Reference: starter config](/reference/starter-config) — the canonical `.deviate/config.toml`, root `.gitignore`, and root `.gitattributes` shapes written by this scaffold, where the union-merge rules and command-pattern entries are exposed as lookup material.
