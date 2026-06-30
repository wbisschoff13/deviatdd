---
title: "Scaffold a feature workspace"
description: "Run `deviate feature create <title>` to derive a slug, create the `feat/<slug>` branch, scaffold `specs/<slug>/`, and reset the session — the greenfield entry point before `/deviate-explore` runs."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-002-003
---

# Scaffold a feature workspace

This how-to covers `deviate feature create` — the macro-layer workspace scaffolding command registered at `src/deviate/cli/__init__.py:795` as `cli.add_typer(feature_app, name="feature")` and implemented at `src/deviate/cli/feature.py::create` (line 79). The command consumes a freeform feature title, derives a URL-friendly kebab-case slug (`_derive_slug`, line 15), scaffolds the feature directory at `specs/<slug>/` (`_create_feature_directory`, line 22), creates the git branch `feat/<slug>` via Graphite (`gt create -am`) or plain git (`git branch`) depending on `.deviate/config.toml`'s `graphite` setting, and resets `.deviate/session.json` to defaults (`SessionState()` at line 92). There is no dedicated `/deviate-feature` slash command — the CLI is the primary action. The command is most often invoked *implicitly* by `/deviate-explore`, `/deviate-specify`, and `/deviate-plan` (each calls `deviate feature create` as phase step 1 per `specs/DeviaTDD-api.md:277`); this how-to is for the operator who wants to scaffold the workspace manually — typically when starting a new epic on the trunk or when the implicit invocation is missing the slug you want.

## Prerequisites

- **A clean working tree on the base branch (`main` or `master`)** — `deviate feature create` creates the `feat/<slug>` branch from the current HEAD. With plain git (`graphite = false`), `_create_feature_branch` (`src/deviate/cli/feature.py:71-76`) calls `git branch <name>` which does NOT switch branches — you stay on your previous branch. Any uncommitted edits on that branch will become invisible after `git checkout feat/<slug>` even though they still exist. Stash or commit before invoking.
- **A DeviaTDD workspace bootstrapped** — `.deviate/config.toml` must exist (created by `deviate setup`). The command reads `graphite` from `.deviate/config.toml` via `resolve_graphite_config()` (`src/deviate/state/config.py:171`) to decide between `gt create -am` and `git branch`. If `.deviate/` is missing, see [Bootstrap a DeviaTDD workspace](/how-to/setup).
- **An initialized repo with a `specs/` directory** — `_create_feature_directory` creates `specs/<slug>/` but assumes `specs/` already exists at the repo root. If not, run `deviate init` first (see [Initialize a repo with DeviaTDD conventions](/how-to/init)).
- **Optional: Graphite CLI on `PATH` when `graphite = true`** — the command shells out to `gt create -am`. When `graphite` is unset (default) or `false`, the command uses `git branch <slug>` instead and requires no extra tools.
- **A feature title (1–12 words)** — the source text for slug derivation. `_derive_slug()` lowercases, replaces any non-`[a-z0-9]` run with `-`, and strips leading/trailing hyphens. Pass `--slug <slug>` to override the derivation when your title contains diacritics, em-dashes, CJK characters, or brand names that would produce surprising slugs.

## Steps

### 1. Verify the working tree is clean and on the base branch

Before invoking, confirm you are on `main` (or `master`) and the tree is clean. The branch is anchored to the current HEAD — if you are mid-feature on another `feat/<other>` branch, the new `feat/<slug>` will fork from that feature, not from `main`, which is rarely what you want.

```bash
# On the base branch (not a feat/* branch)
git rev-parse --abbrev-ref HEAD | grep -E '^(main|master)$'

# Clean working tree (no staged or unstaged edits)
test -z "$(git status --porcelain)"

# Working tree's HEAD anchor (record this — the new branch forks from here)
git rev-parse HEAD
```

If any of these fail, finish or stash the in-flight work first. Branching from the wrong base is the most common cause of "where did my commits go?" surprises after `deviate feature create`.

### 2. Run `deviate feature create` with the feature title

In your shell, run the CLI with the feature title as the positional argument. This is the primary action for this how-to — there is no `/deviate-feature` slash command, so the CLI is the only entry point.

```bash
deviate feature create "Auth overhaul — OAuth + JWT rotation"
```

The command runs to completion in under a second and produces no stdout output on success (no JSON contract, no banner). Three side effects land in order (`src/deviate/cli/feature.py:84-94`):

1. `specs/<slug>/` directory created (e.g. `specs/auth-overhaul-oauth-jwt-rotation/`).
2. `feat/<slug>` branch created (without checkout, unless Graphite).
3. `.deviate/session.json` written with default `SessionState()` (`current_phase: IDLE`, `active_issue_id: null`).

For tighter slug control, pass `--slug` explicitly:

```bash
deviate feature create --slug auth-overhaul "Auth overhaul — OAuth + JWT rotation"
```

The `--slug` flag is useful when your title contains characters that would produce surprising slugs (em-dashes, CJK, diacritics, brand names with capitals).

### 3. Switch to the new branch (plain git only)

When `.deviate/config.toml` has `graphite = false` (default), `_create_feature_branch` (`src/deviate/cli/feature.py:71-76`) calls `git branch <name>` which creates the branch without checking it out. You remain on your previous branch. Switch manually before any further work:

```bash
git checkout feat/auth-overhaul-oauth-jwt-rotation
```

When `graphite = true`, `_create_feature_branch` (lines 48-55) calls `gt create -am <name>` which creates, checks out, and commits in one step. Skip this step — `git rev-parse --abbrev-ref HEAD` will already report `feat/<slug>`.

### 4. Verify the three side effects landed

Confirm the directory, the branch, and the session file all exist with the expected contents. This is the verification step — every troubleshooting entry below surfaces here first.

```bash
# 1. Feature directory exists at specs/<slug>/
ls -d specs/auth-overhaul-oauth-jwt-rotation/

# 2. Branch exists locally
git rev-parse --verify feat/auth-overhaul-oauth-jwt-rotation

# 3. Session file was written and reset to defaults
python -c "import json; s=json.load(open('.deviate/session.json')); print('phase:', s['current_phase'], '| issue:', s.get('active_issue_id'))"

# 4. Branch HEAD matches the anchor from step 1 (the branch was forked from there)
git rev-parse feat/auth-overhaul-oauth-jwt-rotation
```

Expected: directory exists, branch exists, `current_phase: IDLE` and `active_issue_id: None`, branch HEAD matches the anchor from step 1. If any of these is missing or wrong, see troubleshooting below.

### 5. Move to the next phase

The feature workspace is now ready for content. Continue with one of:

- [Run the /deviate-explore phase](/how-to/explore) — the natural next macro phase; its step 1 detects the existing workspace and skips a second `feature create`.
- [Run the /deviate-research phase](/how-to/research) — if exploration is already done and you have a design in mind, or if you are resuming an existing epic with a known design.

## Troubleshooting

### Command exits 0 but no `specs/<slug>/` directory was created

`_create_feature_directory` (`src/deviate/cli/feature.py:22`) calls `mkdir(parents=True, exist_ok=True)` — this should never fail silently. Check whether the slug derivation produced an empty string (your title stripped down to nothing after `_derive_slug`'s lower-case-and-replace pass).

**Fix**: Pass `--slug <slug>` explicitly with a non-empty slug. Titles consisting entirely of punctuation, em-dashes, or non-Latin characters can derive to `""` after `re.sub(r"[^a-z0-9]+", "-", slug).strip("-")`.

### Command exits 1 with `GRAPHITE_NOT_FOUND`

You have `graphite = true` in `.deviate/config.toml` but `gt` is not on `PATH`. `_create_feature_branch` (`src/deviate/cli/feature.py:57-61`) catches the `FileNotFoundError` and prints the banner with a link to <https://graphite.dev/docs/cli>.

**Fix**: Either (a) install Graphite from <https://graphite.dev/docs/cli> and re-run, or (b) set `graphite = false` in `.deviate/config.toml` and re-run — the command will use plain `git branch` instead.

### Command exits 1 with `GRAPHITE_FAILED <stderr detail>`

Graphite is installed but `gt create -am <slug>` exited non-zero. Common causes: the slug contains characters Graphite rejects, the repo's trunk branch is renamed, or you have unstaged changes that Graphite refuses to commit.

**Fix**: Inspect the stderr detail printed before the banner. Most often the fix is `git status` to clean up unstaged changes, or `--slug` to pass a Graphite-safe slug (lowercase, alphanumeric, hyphens only).

### `git branch <slug>` is a silent no-op when the branch already exists

`_create_feature_branch` (`src/deviate/cli/feature.py:37-44`) calls `git rev-parse --verify --quiet <branch_name>` first; if it returns 0, the function returns immediately without creating a branch. The directory and session file are still written — so a re-run after a partial prior invocation can leave the directory present but the branch pointing elsewhere.

**Fix**: Verify before re-running with `git rev-parse --verify feat/<slug>`. If the branch exists from a prior partial run, decide whether to `git branch -D feat/<slug>` and re-run, or `git checkout feat/<slug>` to resume the prior workspace.

### `.deviate/session.json` was reset to defaults (`IDLE`, no active issue)

This is the command's actual behavior — `create()` (`src/deviate/cli/feature.py:92-94`) instantiates `SessionState()` with no parameters, which resets `current_phase` to `IDLE` and `active_issue_id` to `None`. If you had an in-flight issue tracked in the session, that issue is no longer anchored.

**Fix**: Re-anchor the session by running the relevant next phase — e.g. `deviate meso run --issue ISS-NNN-NNN` to restore `active_issue_id`. The session reset is intentional (the new workspace starts fresh) but is undocumented outside this source line; treat it as expected behavior, not a regression.

### Working tree had uncommitted edits and they appear to vanish after switching branches

`_create_feature_branch` does not switch branches on the plain-git path. If you stashed nothing and you had edits on `main`, they are still on `main` when you `git checkout feat/<slug>` — but you no longer see them in the working tree. They reappear when you `git checkout main` again.

**Fix**: This is not data loss — it is the standard git detached-worktree surprise. Switch back to `main` to recover, commit or stash, then return to `feat/<slug>`. The how-to's step 1 (verify clean tree before invoking) prevents this scenario entirely.

## Next Steps

- [Run the /deviate-explore phase](/how-to/explore) — the natural next macro phase; its step 1 detects the existing workspace and writes `specs/<slug>/explore.md` without re-scaffolding.
- [Initialize a repo with DeviaTDD conventions](/how-to/init) — prerequisite if `specs/` does not exist yet; `deviate feature create` assumes `specs/` is already scaffolded.
- [Bootstrap a DeviaTDD workspace](/how-to/setup) — prerequisite if `.deviate/config.toml` does not exist; the command reads `graphite` from there to choose between `gt create -am` and `git branch`.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for every `deviate-*` slash command; note that `deviate-feature` is intentionally absent because the command has no dedicated prompt template (operators invoke `deviate feature create` directly).
- [Reference: Macro run](/reference/macro-run) — the `--target <slug>` flag pattern that downstream macro phases use to point at the workspace this command created.