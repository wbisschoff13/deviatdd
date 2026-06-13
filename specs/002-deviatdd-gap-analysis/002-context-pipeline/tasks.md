# Implementation Tasks: feat/002-deviatdd-gap-analysis/002-context-pipeline

## Phase 1: Core Context Pipeline Logic
**Goal**: Implement core domain logic for workspace context resolution, `ContextContract` model, governance block upsert, symlink enforcement, and stale reference audit.

### Tasks

- [ ] TSK-002-01: Core Context Logic — Model, Resolution, Governance, Symlinks, Stale Audit
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `pytest tests/test_core/test_context.py -v`
  - **Estimated Time**: 90 minutes
  - **Files**:
    - `src/deviate/core/context.py`
    - `src/deviate/core/worktree.py`
    - `tests/test_core/test_context.py`
  - **Rationale**: `context.py` is the NEW central module housing all core domain logic: `ContextContract` Pydantic model (used by both pre/post), `resolve_workspace_context()` (workspace crawl path discovery), symlink enforcement, and stale reference audit — covering US-001 (context-pre), US-002 (governance upsert), US-003 (symlink), US-004 (stale refs) all tracing to FR-002 and FR-011. `worktree.py` gains `upsert_governance_block()` since CLAUDE.md governance editing is a workspace-level operation, aligning with the module's file management role (US-002 SC-01). Tests in `test_context.py` validate every core path.
  - **Details**:
    - **Red**: Write failing tests in `tests/test_core/test_context.py`: `test_resolve_workspace_context_valid` — assert `ContextContract.status == "READY"` and all path fields are relative strings; `test_resolve_workspace_context_missing_deviate` — assert `status == "FAILURE"` with `diagnostic` field; `test_context_contract_paths_relative` — assert `repo_root`, `deviate_path`, `specs_path` are relative; `test_context_contract_serialization` — assert JSON round-trip preserves fields; `test_governance_upsert` — assert `## Technical Execution Context` block is replaced while surrounding sections are preserved; `test_symlink_enforcement_posix` — assert `AGENTS.md` becomes symlink to `CLAUDE.md`; `test_symlink_enforcement_windows` — assert copy fallback when `os.name == 'nt'`; `test_stale_reference_removal` — assert exact-line patterns `rgr run`, `manage-tasks.sh`, `sdd-parse-ast.sh`, `get-test-config.sh`, `.rgr/` are removed
    - **Green**: Implement `class ContextContract(BaseModel)` in `src/deviate/core/context.py` with fields: `status: Literal["READY", "FAILURE"]`, `repo_root: str`, `deviate_path: Optional[str]`, `specs_path: Optional[str]`, `specs_issues: list[str]`, `specs_active_issue: Optional[str]`, `diagnostic: Optional[str]`, `timestamp: str`. Implement `resolve_workspace_context(repo_root: Path) -> ContextContract` that crawls `.deviate/` and `specs/`, resolves paths as relative strings, returns READY or FAILURE. Implement `upsert_governance_block(content: str, block_header: str, fresh_block: str, repo: Path | None = None) -> str` in `worktree.py` that replaces the target section in CLAUDE.md content while preserving surrounding file structure. Implement `enforce_agents_symlink(claude_path: Path, agents_path: Path) -> None` with `os.name` guard, content comparison logic, and copy fallback. Implement `remove_stale_references(content: str, patterns: list[str]) -> str` with exact-line match (trimmed whitespace).
    - **Refactor**: Align `ContextContract` field naming with existing `_emit_contract` and `contract.py` patterns. Use `Path` type consistently. Extract `_read_file_safe()` helper for file-not-found scenarios.
    - **Edge Cases**: Missing `.deveiate/` directory returns FAILURE with diagnostic. Missing `specs/` returns READY with null specs_path. AGENTS.md content-diverge from CLAUDE.md leaves as-is and warns (per HITL decision). AGENTS.md already a symlink — no-op. Empty content lines in stale audit — skip.
    - **Acceptance**: All 8 test cases pass. Core logic covers US-001 SC-01/02/03, US-002 SC-01, US-003 SC-01/02/03/04/05, US-004 SC-01/02. Governance block upsert preserves surrounding sections.

- [x] TSK-002-02: CLI Context Commands (pre, post, combined)
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Integration
  - **Verification**: `pytest tests/test_cli/test_context.py -v`
  - **Estimated Time**: 60 minutes
  - **Dependency**: TSK-002-01
  - **Files**:
    - `src/deviate/cli/context.py`
    - `tests/test_cli/test_context.py`
  - **Rationale**: `context.py` CLI is the NEW user-facing entry point wrapping core logic with Typer argument parsing, JSON contract emission, and error handling. Exposes three entry points: `deviate context` (default — runs scan + apply in one shot), `deviate context pre` (scan-only, emit JSON contract), and `deviate context post <manifest>` (apply from saved manifest). Tests in `test_context.py` validate all three paths.
  - **Details**:
    - **Red**: Write failing CLI tests in `tests/test_cli/test_context.py`: `test_context_pre_emits_contract` — invoke `context pre`, assert JSON on stdout with `status: READY` and all required fields; `test_context_pre_missing_deviate` — invoke in dir without `.deviate/`, assert `status: FAILURE`; `test_context_post_updates_governance` — create manifest via `context pre`, invoke `context post /tmp/manifest`, assert CLAUDE.md `## Technical Execution Context` is updated; `test_context_post_symlink_enforcement` — assert AGENTS.md becomes symlink after context post; `test_context_post_stale_refs` — assert stale patterns removed from AGENTS.md; `test_context_post_commit` — assert git commit with message format `chore(context): sync governance for <branch>`; `test_context_combined_updates_governance_and_commits` — invoke `deviate context` with no subcommand, assert governance updated, symlink created, commit made; `test_context_combined_missing_deviate` — invoke `deviate context` in dir without `.deviate/`, assert non-zero exit with diagnostic
    - **Green**: Implement `context_app = typer.Typer(no_args_is_help=False)` in `src/deviate/cli/context.py` with `context_main()` callback (`invoke_without_command=True`) that runs `resolve_workspace_context()` then `_apply_context()` in one shot, plus `pre()` and `post()` as explicit subcommands. Extract `_apply_context(contract, repo_root)` from `post()` logic so it's shared between the combined command and `post`. `_apply_context` stages files via `git add` (no commit — staged changes are included in the caller's commit). `pre()`: call `resolve_workspace_context()`, print JSON via `json.dumps()`. `post(manifest: Path)`: read manifest file, validate, call `_apply_context()`. Handle `--json` and `--quiet` flags on `pre` via `with_json_quiet` decorator pattern.
    - **Refactor**: Use `_common.py` helpers (`console`, `_halt`) consistently. Match CLI decorator and error-handling patterns from `macro.py` and `meso.py` (Typer exit codes, rich console output).
    - **Edge Cases**: Invalid manifest path → non-zero exit with diagnostic. Missing CLAUDE.md → warning, continues, exits 0. Windows `os.name == 'nt'` → copy fallback, no `mklink`. Empty manifest JSON → non-zero exit. `deviate context` with FAILURE pre-scan exits non-zero before applying.
    - **Acceptance**: All 8 test cases pass. `context pre` emits valid JSON contract. `context post` applies from manifest (stages files, no commit). `deviate context` (combined) does both in one shot (stages files, no commit). Performance: combined < 500ms, `context pre` < 200ms.

## Phase 2: Auto-Trigger Integration
**Goal**: Wire automatic `deviate context` invocation into all macro and meso post commands with a `--no-context-sync` escape hatch.

### Tasks

- [ ] TSK-002-03: Auto-Trigger `deviate context` in Macro/Meso Post Commands
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `pytest tests/test_cli/test_macro.py tests/test_cli/test_meso.py -v`
  - **Estimated Time**: 60 minutes
  - **Dependency**: TSK-002-02
  - **Files**:
    - `src/deviate/cli/macro.py`
    - `src/deviate/cli/meso.py`
    - `tests/test_cli/test_macro.py`
    - `tests/test_cli/test_meso.py`
  - **Rationale**: `macro.py` and `meso.py` are the existing post-command modules that must gain auto-trigger wiring — `explore_post`, `research_post`, `prd_post`, `shard_post` (macro), `specify_post` (meso) — each receiving a `--no-context-sync` flag to suppress the trigger, covering US-005 SC-01/02/03/04 (FR-002). Tests in `test_macro.py` and `test_meso.py` validate auto-trigger behavior, suppression flag, and soft-fail guarantee. The auto-trigger calls `deviate context` (combined command) rather than separate pre/post.
  - **Details**:
    - **Red**: Write failing tests: `test_explore_post_auto_triggers_context` in `test_macro.py` — mock `deviate context`, invoke `explore_post`, assert combined context called; `test_explore_post_no_context_sync` — invoke with `--no-context-sync`, assert context NOT called; `test_specify_post_auto_triggers_context` in `test_meso.py` — same pattern for `specify_post`; `test_context_sync_soft_fail_does_not_block_parent` — mock `deviate context` to raise, assert parent exits 0 with warning on stderr
    - **Green**: Add `no_context_sync: bool = typer.Option(False, "--no-context-sync")` to `explore_post()`, `research_post()`, `prd_post()`, `shard_post()` in `macro.py` and `specify_post()` in `meso.py`. At end of each post (after commit): `if not no_context_sync: _maybe_trigger_context_sync()`. Implement `_maybe_trigger_context_sync() -> None` helper (shared by reference or import) that runs `deviate context` via subprocess, catches `CalledProcessError`, prints `"[yellow]CONTEXT_SYNC_WARN[/] ..."` to stderr, and continues.
    - **Refactor**: Extract `_maybe_trigger_context_sync()` into a shared helper in `_common.py` to avoid duplication across 5 post commands. The helper should accept a `repo: Path | None = None` parameter for test isolation.
    - **Edge Cases**: `deviate context` binary not found → soft warning. Worktree not in sync → soft warning. Workspace scan returns FAILURE → soft warning, parent commit still succeeds. Multiple post commands in sequence → each triggers independently. `--no-context-sync` passed → silent skip, no warning about skipped sync.
    - **Acceptance**: All test cases pass. Every macro/meso post auto-triggers `deviate context`. `--no-context-sync` reliably suppresses trigger. Failed context sync never blocks parent commit (US-005 SC-04).

- [ ] TSK-002-04: Context Pipeline Integration Tests
  - **Type**: Feature_Batch
  - **Mode**: IMMEDIATE
  - **Verification**: `pytest tests/test_integration/test_context_pipeline.py -v`
  - **Estimated Time**: 45 minutes
  - **Dependency**: TSK-002-03
  - **Files**:
    - `tests/test_integration/test_context_pipeline.py`
  - **Rationale**: New integration test file exercising the combined `deviate context` cycle end-to-end, plus phased pre→post, symlink content-match/diverge edge cases, and performance constraints (L_max <= 500ms for combined, <= 200ms for pre). Covers all stories US-001 through US-005 holistically, including HITL decisions on AGENTS.md content comparison and symlink enforcement.
  - **Details**:
    - **Implementation**: Write `tests/test_integration/test_context_pipeline.py` with `tmp_git_repo` fixture: `test_combined_context_cycle` — setup `.deviate/` and `specs/`, run `deviate context` (combined), verify CLAUDE.md `## Technical Execution Context` updated, verify AGENTS.md is symlink, verify CLAUDE.md and AGENTS.md are staged (`git diff --cached`); `test_context_post_symlink_content_match` — write AGENTS.md with same content as CLAUDE.md, run `context post`, verify symlink created; `test_context_post_symlink_content_diverge` — write AGENTS.md with different content, run `context post`, verify no symlink, warning printed; `test_combined_context_performance` — measure `deviate context` execution time, assert < 500ms; `test_context_pre_performance` — measure `context pre` execution time, assert < 200ms
    - **Refactor**: Follow existing integration test patterns (see `test_macro_full_cycle.py`, `test_init_export_cycle.py`). Use `subprocess.run` with `cwd=tmp_git_repo` for CLI invocations. Assert on stdout stderr content.
    - **Acceptance**: All 5 integration tests pass. Combined `deviate context` cycle verified with real filesystem and git operations in isolated temp repo. Performance constraints validated.

---

## Implementation Strategy
**Execution Order**:
1. Phase 1 (TSK-002-01 Core Logic) → Phase 1 (TSK-002-02 CLI Commands) → Phase 2 (TSK-002-03 Auto-Trigger) → Phase 2 (TSK-002-04 Integration Tests)

**Critical Dependency Chains**:
- TSK-002-01 (Core Context Model + Workspace Resolution + Governance/Symlink/Stale) must precede TSK-002-02 (CLI Commands) — the CLI wraps the core logic
- TSK-002-02 (CLI Commands) must precede TSK-002-03 (Auto-Trigger) — auto-trigger invokes `deviate context`
- TSK-002-03 (Auto-Trigger) must precede TSK-002-04 (Integration Tests) — integration tests exercise the full pipeline including auto-trigger

**Risk Hotspots**:
- Symlink `os.name` branching: Windows copy fallback must be tested on CI (mock `os.name == 'nt'` in unit tests; integration tests run on POSIX only)
- AGENTS.md content comparison: Reading file bytes vs string comparison — must use identical read mode as CLAUDE.md
- Auto-trigger subprocess invocation: Must use `repo_path` parameter for test isolation, never `Path.cwd()` in test context
- Performance: Combined `deviate context` at 500ms includes pre-scan + governance update + git commit — may need optimization if commit hooks add latency
- Combined command failure mode: If workspace scan returns FAILURE, the command exits non-zero before applying — auto-trigger must handle non-zero exit as soft warning

**Merge Conflict Boundaries**:
- `macro.py` — Touched by both TSK-002-03 (auto-trigger) and potential parallel ISS tasks; maintain backward-compatible signature
- `meso.py` — Same risk as `macro.py`; both add optional `--no-context-sync` flag and end-of-function trigger
- `worktree.py` — TSK-002-01 adds `upsert_governance_block()`; check no other task in this epic modifies worktree.py

## Universal Test Constraints (ALL TASKS)

- **Git Isolation Mandatory**: Any test that invokes git operations (init, add, commit, branch, worktree, checkout, log, status, push) MUST operate on a temporary directory initialized as a fresh git repo via `tmp_path` (pytest) or `tempfile.TemporaryDirectory`. Tests MUST NOT run git commands within the real repository's working tree.
- **Implementation Pattern**: Use a shared `tmp_git_repo` fixture from `tests/conftest.py` (which calls `git init` inside `tmp_path` and configures a test user). Pass `repo=tmp_git_repo` to all git-interacting functions. Never reference `Path.cwd()` or the real repo root.
- **Rationale**: Prevent accidental commits, branch creation, or state mutation in the actual project repo during test execution. All tests are TDD and run repeatedly; accidental mutations corrupt the development workflow.

## Universal API Design Constraint (ALL CORE MODULES)

Every git-interacting function in core modules MUST accept an optional `repo_path: Path | None = None` parameter. When `None`, default to `Path.cwd()`. This is the **sole enabler** of test isolation — without it, tests must use fragile `chdir` tricks or operate on the real repo.

```python
# DO: accept repo_path, default to cwd
def resolve_workspace_context(repo_root: Path | None = None) -> ContextContract:
    repo_root = repo_root or Path.cwd()

def upsert_governance_block(content: str, repo: Path | None = None) -> str:
    repo = repo or Path.cwd()

# DON'T: hard-code Path.cwd() or rely on ambient working directory
def resolve_workspace_context() -> ContextContract:  # BAD — untestable
    ...
```

**Consequence**: Every per-task Git Isolation block below is a specific instance of this universal constraint. If a task's `Green` section says to implement a function that runs git commands or reads workspace files, that function **must** accept `repo_path`.
