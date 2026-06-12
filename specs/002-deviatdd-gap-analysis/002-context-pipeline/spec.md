# FEATURE_SPECIFICATION: specs/002-deviatdd-gap-analysis/002-context-pipeline/spec.md

## SYSTEM_TOPOLOGY_MAPPING

- **Epic Domain**: 002 — DeviaTDD Docs-to-Code Gap Resolution
- **Issue ID**: ISS-002-002
- **Issue Title**: Context Pipeline — Context Pre/Post Commands & AGENTS.md Alignment
- **Issue File**: `specs/002-deviatdd-gap-analysis/issues/002-context-pipeline.md`
- **Branch**: `feat/002-deviatdd-gap-analysis/002-context-pipeline`
- **Workstation Paths**:
  - `src/deviate/cli/context.py` — NEW: `context pre` and `context post` CLI commands (Typer)
  - `src/deviate/core/context.py` — NEW: `resolve_workspace_context()`, `ContextContract` Pydantic model, symlink enforcement, stale reference audit
  - `src/deviate/core/worktree.py` — MODIFY: governance block upsert helpers (`upsert_governance_block`)
  - `src/deviate/cli/macro.py` — MODIFY: auto-trigger `context post` via `--no-context-sync` flag in explore post, research post, prd post, shard post
  - `src/deviate/cli/meso.py` — MODIFY: auto-trigger `context post` via `--no-context-sync` flag in specify post
  - `CLAUDE.md` — MODIFY: `## Technical Execution Context` governance block upsert
  - `AGENTS.md` — MODIFY: symlink enforcement, stale reference removal
- **Upstream PRD**: `specs/002-deviatdd-gap-analysis/prd.md`
- **Blocked By**: `ISS-002-001` (Foundation CLI Infrastructure)

## THE_PROBLEM_CONTRACT

After running `deviate explore post`, the governance blocks in `CLAUDE.md` are stale — the `## Technical Execution Context` section references outdated paths and phase states. The developer must manually determine the current workspace state and update these blocks, which is error-prone and frequently forgotten.

The **Context Pipeline** solves this by providing a pair of commands:

1. **`deviate context pre`** — Crawls the workspace directory, discovers `.deviate/` configuration and `specs/` directory tree, resolves all paths relative to `repo_root`, and emits a `ContextContract` JSON on stdout with status `READY` or `FAILURE`.
2. **`deviate context post <manifest>`** — Reads the `ContextContract` JSON manifest, upserts the `## Technical Execution Context` section in `CLAUDE.md`, enforces `AGENTS.md → CLAUDE.md` symlink (or copy fallback on Windows), audits `AGENTS.md` for stale reference patterns and removes them, then commits the result.

All macro and meso post commands (`explore post`, `research post`, `prd post`, `shard post`, `specify post`) auto-trigger `context post` as a final step unless the operator passes `--no-context-sync`. The sync is best-effort with a soft warning — it never blocks the parent command's commit.

## SCOPE_BOUNDARIES

### Hard Inclusions

- `deviate context pre` — directory crawl, path resolution, `ContextContract` JSON emission
- `deviate context post <manifest>` — manifest read, governance block upsert, symlink enforcement, stale reference removal, git commit
- `ContextContract` Pydantic model with relative path strings and `status` field (`READY` | `FAILURE`)
- Auto-trigger in all macro/meso post commands via `--no-context-sync` flag
- Symlink enforcement: `AGENTS.md → CLAUDE.md` via `ln -sf` (POSIX) or copy fallback (Windows)
- `os.name` guard for symlink operations (POSIX vs Windows branching)
- Stale reference audit: exact-line removal of `rgr run`, `manage-tasks.sh`, `sdd-parse-ast.sh`, `get-test-config.sh`, `.rgr/` patterns from `AGENTS.md`
- Governance block upsert in `CLAUDE.md`: `## Technical Execution Context` section — full replace of the block content while preserving surrounding file structure
- Context sync is best-effort with warning — never a hard gate that blocks post-command commit
- Symlink content comparison: if `AGENTS.md` content matches `CLAUDE.md` and is not already a symlink, replace with symlink; if content differs, leave as-is and warn
- Git commit after `context post` with conventional commit message

### Defensive Exclusions

- NO changes to micro-layer TDD cycle (red/green/refactor), profiles, or cache discipline
- NO changes to session state machine beyond auto-trigger wiring
- NO removal of existing governance block content — only upsert/replace the `## Technical Execution Context` section
- NO changes to `deviate init` or constitution provisioning
- Symlink on Windows uses copy fallback — no `mklink` or admin elevation
- NO changes to `.deviate/config.toml` or session state format
- NO changes to PRD format, issue ledger format, or issue JSON contract schema
- NO automatic symlink creation if `AGENTS.md` content differs from `CLAUDE.md` content

## PERFORMANCE CONSTRAINTS

| Constraint | Target | Context |
|-----------|--------|---------|
| `context pre` execution | L_max <= 200ms | Workspace crawl + path resolution + JSON emission |
| `context post` execution | L_max <= 300ms | File read, governance upsert, symlink, stale audit, commit |
| Combined auto-trigger overhead | L_max <= 500ms | Total added latency to parent post command |
| Stale reference audit | L_max <= 50ms | AGENTS.md line scan + exact-match removal |
| Governance block upsert | L_max <= 100ms | Read CLAUDE.md, replace section, write |

## MULTI_TIERED_VERIFICATION_TARGETS

| Tier | Test File | Test Cases |
|------|-----------|------------|
| Unit — Core | `tests/test_core/test_context.py` | `test_resolve_workspace_context`, `test_context_contract_paths_relative`, `test_context_contract_serialization`, `test_symlink_enforcement_posix`, `test_symlink_enforcement_windows`, `test_stale_reference_removal`, `test_governance_upsert` |
| CLI — Context | `tests/test_cli/test_context.py` | `test_context_pre_emits_contract`, `test_context_pre_missing_deviate`, `test_context_post_updates_governance`, `test_context_post_symlink_enforcement`, `test_context_post_stale_refs`, `test_context_post_commit` |
| CLI — Macro | `tests/test_cli/test_macro.py` | `test_explore_post_auto_triggers_context`, `test_explore_post_no_context_sync` |
| CLI — Meso | `tests/test_cli/test_meso.py` | `test_specify_post_auto_triggers_context`, `test_specify_post_no_context_sync` |
| Integration | `tests/test_integration/test_context_pipeline.py` | `test_full_context_pre_post_cycle`, `test_context_post_symlink_content_match`, `test_context_post_symlink_content_diverge` |

## ATDD_ACCEPTANCE_CRITERIA_LEDGER

### US-001-context-pre: Workspace Discovery and ContextContract Emission

* **Upstream Requirement Traceability**: FR-002

**Scenario 1: Valid workspace with `.deviate/` and `specs/`**
`**Given**` a workspace containing `.deviate/config.toml` and `specs/` directory
`**When**` the user runs `deviate context pre`
`**Then**` the command emits a JSON `ContextContract` on stdout
`**And**` the contract contains `status: READY`
`**And**` all path fields are resolved relative to `repo_root`
`**And**` the contract includes `repo_root`, `deviate_path`, `specs_path`, `specs_issues`, `specs_active_issue`, `timestamp`, and `status`

**Scenario 2: Missing `.deviate/` directory**
`**Given**` a workspace without `.deviate/`
`**When**` the user runs `deviate context pre`
`**Then**` the command emits a JSON `ContextContract` on stdout
`**And**` the contract contains `status: FAILURE`
`**And**` the contract includes a `diagnostic` field explaining the missing `.deviate/` directory

**Scenario 3: Empty workspace (no specs/)**
`**Given**` a workspace with `.deviate/` but no `specs/` directory
`**When**` the user runs `deviate context pre`
`**Then**` the command emits a JSON `ContextContract` with `status: READY`
`**And**` the contract's `specs_path` is `null` and `specs_issues` is an empty array

### US-002-context-post-manifest: Governance Block Upsert and Commit

* **Upstream Requirement Traceability**: FR-002

**Scenario 1: Valid manifest updates CLAUDE.md governance block**
`**Given**` a valid `ContextContract` JSON file at `<manifest>`
`**And**` `CLAUDE.md` contains a `## Technical Execution Context` section with stale content
`**When**` the user runs `deviate context post <manifest>`
`**Then**` the `## Technical Execution Context` block in `CLAUDE.md` is replaced with fresh content from the contract
`**And**` surrounding sections in `CLAUDE.md` are not modified
`**And**` the command runs `git add` and `git commit` on `CLAUDE.md`
`**And**` the commit message follows the format `chore(context): sync governance for <branch_name>`

**Scenario 2: Missing CLAUDE.md**
`**Given**` a valid `ContextContract` JSON file at `<manifest>`
`**And**` `CLAUDE.md` does not exist in the workspace root
`**When**` the user runs `deviate context post <manifest>`
`**Then**` the command prints a warning that `CLAUDE.md` is missing
`**And**` the command does NOT create `CLAUDE.md`
`**And**` the command exits with code 0 (non-blocking)

**Scenario 3: Invalid manifest JSON**
`**Given**` a malformed or non-existent `<manifest>` file path
`**When**` the user runs `deviate context post <manifest>`
`**Then**` the command prints a diagnostic error
`**And**` the command exits with non-zero exit code

### US-003-symlink-enforcement: AGENTS.md/CLAUDE.md Symlink Alignment

* **Upstream Requirement Traceability**: FR-011

**Scenario 1: AGENTS.md does not exist — create symlink**
`**Given**` `AGENTS.md` does not exist in the workspace root
`**And**` `CLAUDE.md` exists with content
`**When**` the user runs `deviate context post <manifest>`
`**Then**` `AGENTS.md` is created as a symbolic link to `CLAUDE.md` (POSIX) or a content copy (Windows)

**Scenario 2: AGENTS.md is already a symlink to CLAUDE.md — no-op**
`**Given**` `AGENTS.md` exists and is already a symbolic link pointing to `CLAUDE.md`
`**When**` the user runs `deviate context post <manifest>`
`**Then**` no change is made to `AGENTS.md`
`**And**` no warning is printed

**Scenario 3: AGENTS.md exists with same content as CLAUDE.md — replace with symlink**
`**Given**` `AGENTS.md` exists as a regular file
`**And**` the content of `AGENTS.md` is byte-identical to `CLAUDE.md`
`**And**` `AGENTS.md` is not a symbolic link
`**When**` the user runs `deviate context post <manifest>`
`**Then**` `AGENTS.md` is replaced with a symbolic link to `CLAUDE.md`

**Scenario 4: AGENTS.md exists with different content — leave as-is, warn**
`**Given**` `AGENTS.md` exists as a regular file
`**And**` the content of `AGENTS.md` differs from `CLAUDE.md`
`**When**` the user runs `deviate context post <manifest>`
`**Then**` `AGENTS.md` is not modified
`**And**` a warning is printed that `AGENTS.md` content diverges from `CLAUDE.md` and manual alignment may be needed

**Scenario 5: Windows copy fallback**
`**Given**` the operating system is Windows (`os.name == 'nt'`)
`**When**` the user runs `deviate context post <manifest>`
`**Then**` the command copies `CLAUDE.md` content to `AGENTS.md` instead of creating a symbolic link
`**And**` no `mklink` or admin elevation is attempted

### US-004-stale-reference-cleanup: Stale Pattern Removal from AGENTS.md

* **Upstream Requirement Traceability**: FR-011

**Scenario 1: Remove exact stale lines**
`**Given**` `AGENTS.md` contains lines matching stale patterns: `rgr run`, `manage-tasks.sh`, `sdd-parse-ast.sh`, `get-test-config.sh`, `.rgr/`
`**When**` the user runs `deviate context post <manifest>`
`**Then**` entire lines that exactly match the stale patterns (after trimming whitespace) are removed from `AGENTS.md`
`**And**` lines that merely contain these patterns as substrings but are not exact matches are preserved

**Scenario 2: No stale references — no-op**
`**Given**` `AGENTS.md` contains no lines matching any stale pattern
`**When**` the user runs `deviate context post <manifest>`
`**Then**` `AGENTS.md` is not modified by the stale reference audit

### US-005-auto-trigger: Macro/Meso Post Auto-Trigger of Context Post

* **Upstream Requirement Traceability**: FR-002

**Scenario 1: explore post auto-triggers context post**
`**Given**` the user runs `deviate explore post` without any `--no-context-sync` flag
`**When**` the explore post command completes its primary work
`**Then**` `context post` is automatically invoked with the latest `ContextContract`
`**And**` if `context post` fails, a warning is printed but the explore post commit proceeds

**Scenario 2: --no-context-sync suppresses auto-trigger**
`**Given**` the user runs `deviate explore post --no-context-sync`
`**When**` the explore post command completes its primary work
`**Then**` `context post` is NOT auto-triggered
`**And**` no warning about skipped context sync is printed

**Scenario 3: specify post auto-triggers context post**
`**Given**` the user runs `deviate specify post` without `--no-context-sync`
`**When**` the specify post command completes its primary work
`**Then**` `context post` is automatically invoked with the latest `ContextContract`

**Scenario 4: Auto-trigger soft-fail does not block parent**
`**Given**` `context post` is auto-triggered and encounters a non-fatal error (e.g., missing AGENTS.md, locked CLAUDE.md)
`**When**` the parent post command's primary work and commit are complete
`**Then**` the parent command exits with code 0
`**And**` a warning about context sync failure is printed to stderr

## SYSTEM_STATUS_SUMMARY

| Variable | Value |
|----------|-------|
| STATUS | READY |
| EPIC_SLUG | 002-deviatdd-gap-analysis |
| BRANCH_NAME | feat/002-deviatdd-gap-analysis/002-context-pipeline |
| SPEC_PATH | specs/002-deviatdd-gap-analysis/002-context-pipeline/spec.md |
| ISSUE_ID | ISS-002-002 |
| NEXT_ACTION | TASKS |
