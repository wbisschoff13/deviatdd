## Review Report: feat/002-deviatdd-gap-analysis/003-fast-path-commands

### Positive Patterns

- **`ComplexityGate.classify()` with `_stub` parameter** (`src/deviate/core/complexity.py:770-781`): Using the stub parameter for deterministic testing without mocking is a clean testability pattern. It mirrors the design doc's recommendation for testable core modules.
- **`AdhocRecord` Pydantic model** (`src/deviate/state/ledger.py:790-797`): Type-safe, `extra="forbid"`, defaults set correctly. Matches existing `IssueRecord`/`TaskRecord` conventions perfectly.
- **`_classify_expression_returns` refactor** (`src/deviate/cli/micro.py:1552-1572`): Extracting the old inline monolithic `_is_return_type_mismatch` into a focused classifier with specific error messages is a clear readability improvement.

### Critical Issues

#### C-001: `adhoc post` violates Append-Only Protocol (Constitution §Append-Only Ledger)

- **File**: `src/deviate/cli/adhoc.py:106-108`
- **Category**: Constitution | **Severity**: Critical | **Confidence**: High
- **Problem**: The `post` command read the entire ledger into memory, mutated one record, and rewrote the entire file. This violated the constitution's Append-Only Protocol: "No existing line is ever modified or overwritten."
- **Evidence**: The function previously rewrote all records via `ledger_path.open("w", ...)`.
- **Remediation**: Changed to append-only: `post` now creates a copy of the found record, transitions it to COMPLETED, and appends a new JSONL line. `_read_adhoc_ledger` was changed from returning a list to a dict keyed by `issue_id` (last-wins for canonical state).
- **Status**: ✅ FIXED

#### C-002: `_specify_pre` feature creation didn't create git branch (Spec US-007)

- **File**: `src/deviate/cli/meso.py:450-461`
- **Category**: PRD | **Severity**: High | **Confidence**: High
- **Problem**: `US-007-FeatureCreateScaffold` requires "a git branch `feat/{SLUG}` is created" but `_specify_pre()` auto-creation code only created the directory and session — it did NOT create the git branch.
- **Remediation**: Added `_create_feature_branch(slug, repo_root)` call after directory creation, matching `feature create` behavior.
- **Status**: ✅ FIXED

#### C-003: `_RETURN_TYPE_MAP` was dead code after refactor (Clean Code)

- **File**: `src/deviate/cli/micro.py:1540-1549`
- **Category**: CleanCode | **Severity**: Medium | **Confidence**: High
- **Problem**: After the refactor that replaced `_is_return_type_mismatch` with `_classify_expression_returns`, the `_RETURN_TYPE_MAP` dict was defined but never referenced anywhere.
- **Remediation**: Removed the orphaned `_RETURN_TYPE_MAP` dict.
- **Status**: ✅ FIXED

### Suggestions

#### S-001: `feature.py` should use shared `console` from `_common.py`

- **File**: `src/deviate/cli/feature.py:8,13`
- **Category**: Idiomacy | **Severity**: Low
- **Current**: Creates its own `Console()` instance (missing Rich theme, different from shared instance)
- **Recommended**: `from deviate.cli._common import console` (like `adhoc.py` does)
- **Rationale**: The project pattern is to use the shared `console` from `_common.py` for consistent styling. `adhoc.py` does this correctly.

#### S-002: `_derive_slug` has redundant f-string

- **File**: `src/deviate/cli/feature.py:21`
- **Category**: Pragmatism | **Severity**: Low
- **Current**: `return f"{slug}"` (unnecessary f-string wrapping a local variable)
- **Recommended**: `return slug`
- **Rationale**: The f-string adds zero value and is a minor code smell.

#### S-003: `_adhoc_ledger_path()` hardcodes `Path.cwd()` with no parameter for test injection

- **File**: `src/deviate/cli/adhoc.py:16-17`
- **Category**: Pragmatism | **Severity**: Medium
- **Current**: `return Path.cwd() / "specs" / "adhoc.jsonl"` — forces tests to use `chdir()`
- **Recommended**: Accept optional `repo_path` parameter, defaulting to `Path.cwd()`
- **Rationale**: The design doc says "Every git-interacting function must accept an optional `repo_path: Path | None = None` parameter." Tests currently use fragile `chdir(tmp_path)` instead.

#### S-004: `feature.py` creates `SessionState` without setting fields

- **File**: `src/deviate/cli/feature.py:59-61`
- **Category**: Pragmatism | **Severity**: Medium
- **Current**: Creates `SessionState()` with all defaults (empty issue_id, no phase) and saves it
- **Recommended**: Set `current_phase` and `active_issue_id` on the session to reflect the newly created feature workspace
- **Rationale**: The spec says "the session is updated with the new feature context." A default session doesn't convey context.

### Opportunities

#### O-001: `adhoc pre` uses timestamp-based issue IDs — risk of collision

- **File**: `src/deviate/cli/adhoc.py:60-61`
- **Current**: `f"adhoc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"`
- **Potential Improvement**: Use `uuid.uuid4()` or `secrets.token_hex(8)` for guaranteed uniqueness
- **Expected Benefit**: Eliminates collision risk when multiple adhoc tasks are created in the same second

### Compliance Matrix

| Domain | Status | Summary of Findings |
|--------|--------|--------------------|
| Security | ✅ | No injection, auth, or data exposure issues |
| Pragmatism | ⚠️ | Redundant f-string, missing repo_path parameter pattern in adhoc.py |
| Idiomacy | ⚠️ | `feature.py` uses own `Console()` instead of shared instance; tests use `chdir()` pattern |
| Clean Code | ✅ | `_RETURN_TYPE_MAP` removed (was dead code) |
| Constitution | ✅ | Append-Only Protocol violation in `adhoc post` fixed |
| PRD | ✅ | Missing branch creation in `_specify_pre` fixed |

### Quick Fix Summary

| Priority | Category | File | Lines | Issue | Effort |
|----------|----------|------|-------|-------|--------|
| 1 | Constitution | `src/deviate/cli/adhoc.py` | 106-108 | Append-only violation in `post` — **FIXED** | Low |
| 2 | PRD | `src/deviate/cli/meso.py` | 450-461 | `_specify_pre` missing branch creation — **FIXED** | Low |
| 3 | CleanCode | `src/deviate/cli/micro.py` | 1540-1549 | Remove dead `_RETURN_TYPE_MAP` — **FIXED** | Low |
| 4 | Idiomacy | `src/deviate/cli/feature.py` | 8,13 | Use shared `console` import (unfixed) | Low |
| 5 | Pragmatism | `src/deviate/cli/feature.py` | 21 | Remove redundant f-string (unfixed) | Low |
| 6 | Pragmatism | `src/deviate/cli/adhoc.py` | 16-17 | Add `repo_path` parameter to `_adhoc_ledger_path` (unfixed) | Low |
| 7 | Pragmatism | `src/deviate/cli/feature.py` | 59-61 | Set session context fields (unfixed) | Low |

### Files Changed (18 files, +965/−27)

| File | Changes | Issues Found (Remaining) | Note |
|------|---------|-------------------------|------|
| `.githooks/pre-commit` | +5 | 0 | Git isolation env fix in hook |
| `CLAUDE.md` | +6/−2 | 0 | Docs: git isolation with `_git_env` |
| `specs/.../spec.md` | +188 | 0 | New: spec document (governance) |
| `specs/.../tasks.jsonl` | +16 | 0 | New: task state ledger |
| `specs/.../tasks.md` | +149 | 0 | New: task decomposition |
| `specs/issues.jsonl` | +1 | 0 | New: ISS-002-003 issue |
| `src/deviate/cli/__init__.py` | +4 | 0 | Register adhoc + feature apps |
| `src/deviate/cli/adhoc.py` | +111 | S-003, O-001 | Append-only violation **FIXED** |
| `src/deviate/cli/feature.py` | +61 | S-001, S-002, S-004 | New: feature create |
| `src/deviate/cli/meso.py` | +30/−1 | 0 | Missing branch creation **FIXED** |
| `src/deviate/cli/micro.py` | +50/−37 | 0 | Dead `_RETURN_TYPE_MAP` **REMOVED** |
| `src/deviate/core/complexity.py` | +36 | 0 | New: ComplexityGate |
| `src/deviate/state/ledger.py` | +10 | 0 | New: AdhocRecord model |
| `tests/test_cli/test_adhoc.py` | +98 | 0 | Tests for adhoc commands |
| `tests/test_cli/test_feature.py` | +67 | 0 | Tests for feature create |
| `tests/test_cli/test_meso.py` | +49 | 0 | Test for specify pre |
| `tests/test_core/test_complexity.py` | +32 | 0 | Tests for ComplexityGate |
| `tests/test_state/test_ledger.py` | +79 | 0 | Tests for AdhocRecord |

### Overall Assessment

- **Code Quality**: Good (3 structural issues fixed, 4 low-priority suggestions remain)
- **Readability**: High (well-organized diff, good test coverage, clean refactoring)
- **Maintainability**: High (fixes aligned with constitution and design doc patterns)

## Fix Instructions

Each entry is an independent fix. Apply in priority order.

### FIX-001: Append-Only Protocol — adhoc post
- **File**: `src/deviate/cli/adhoc.py`
- **Severity**: Critical | Confidence: High
- **Change**: Changed `_read_adhoc_ledger` from `list[dict]` to `dict[str, dict]` keyed by `issue_id` (last-wins dedup). Changed `post` to copy found record, transition to COMPLETED, and **append** new line instead of rewriting the file.
- **Current**: `with ledger_path.open("w", ...)` + linear list search
- **Expected**: `with ledger_path.open("a", ...)` + `records.get(issue_id)` dict lookup

### FIX-002: Missing branch creation in _specify_pre
- **File**: `src/deviate/cli/meso.py`
- **Line**: 452
- **Severity**: High | Confidence: High
- **Change**: Added `_create_feature_branch(slug, repo_root)` after `spec_dir.mkdir(parents=True, exist_ok=True)` in the auto-create section. Imported `_create_feature_branch` from `deviate.cli.feature`.
- **Current**: Only created directory, no branch
- **Expected**: Directory + branch created (matching `feature create` behavior)

### FIX-003: Remove dead _RETURN_TYPE_MAP
- **File**: `src/deviate/cli/micro.py`
- **Line**: 1540-1549
- **Severity**: Medium | Confidence: High
- **Change**: Removed the orphaned `_RETURN_TYPE_MAP` dict that was only referenced by the deleted `_is_return_type_mismatch` function.
- **Current**: Dead code block present
- **Expected**: Removed entirely
