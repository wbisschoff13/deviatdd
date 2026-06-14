## Review Report: feat/adhoc/002-aider-agent-backend-integration

**Branch**: `feat/adhoc/002-aider-agent-backend-integration`
**Scope**: 43 files changed, 5405 insertions, 59 deletions across 23 commits
**Focus**: Aider backend implementation (ISS-ADH-002) alignment with spec, constitution, and PRD
**Review Date**: 2026-06-14

---

### Positive Patterns

1. **Clean AiderConfig model design** — `src/deviate/state/config.py:11-20`
   - Pydantic model with `extra = "forbid"`, sensible defaults, and `Field(default_factory=...)` for mutable defaults. Follows the established pattern from `AgentConfig` and `DeviateConfig`. TOML round-trip tested.

2. **Comprehensive test coverage for flag variants** — `tests/test_core/test_agent.py:352-460`
   - Each AiderConfig flag (`auto_commits`, `suggest_shell_commands`, `yes_mode`, `model`) has a dedicated test verifying the corresponding CLI flag presence/absence. This is thorough and maintainable.

3. **Post-guard pattern** — `src/deviate/core/agent.py:400-411`
   - The concept of running `mise run test` unconditionally after aider invocation (regardless of aider's self-reported status) is a strong defensive engineering pattern that catches false positives.

---

### Critical Issues

#### CRIT-001: `BACKEND_COMMANDS` not updated — aider unreachable from pipeline dispatch

- **File**: `src/deviate/core/agent.py:69-73`
- **Category**: Constitution | **Severity**: Critical | **Confidence**: High
- **Problem**: The spec (US-001, Hard Inclusions) explicitly requires: "Extend `BACKEND_COMMANDS` map with `'aider': 'aider'`". The current dict only has `opencode`, `claude`, `droid`. The `AiderBackend` class exists as a standalone class but is never registered in the dispatch map. The meso/macro pipelines (`macro.py:1519`, `meso.py:966`) instantiate `AgentBackend()` directly — they will never route to aider even if `config.backend = "aider"`.
- **Evidence**:
  ```python
  BACKEND_COMMANDS: dict[str, str] = {
      "opencode": "opencode run",
      "claude": "claude -p",
      "droid": "droid exec",
  }
  ```
- **Remediation**: Add `"aider": "aider"` to `BACKEND_COMMANDS`. Additionally, the meso/macro `_invoke_agent_phase()` functions must check `config.backend` and instantiate `AiderBackend` when backend is `"aider"`, or `AiderBackend` must inherit from `AgentBackend` so the dispatch is polymorphic.
- **Before**:
  ```python
  BACKEND_COMMANDS: dict[str, str] = {
      "opencode": "opencode run",
      "claude": "claude -p",
      "droid": "droid exec",
  }
  ```
- **After**:
  ```python
  BACKEND_COMMANDS: dict[str, str] = {
      "opencode": "opencode run",
      "claude": "claude -p",
      "droid": "droid exec",
      "aider": "aider",
  }
  ```

#### CRIT-002: `AiderBackend` does not implement `AgentBackend` interface — breaks polymorphism

- **File**: `src/deviate/core/agent.py:293-434`
- **Category**: Constitution / PRD | **Severity**: Critical | **Confidence**: High
- **Problem**: The spec says "AiderBackend implements AgentBackend interface." The class is standalone (no inheritance). `AgentBackend.invoke()` signature is `(prompt, backend, timeout, output_callback) -> HandoverManifest`. `AiderBackend.invoke()` signature is `(prompt) -> HandoverManifest`. The meso/macro pipelines call `backend.invoke(prompt)` on an `AgentBackend` instance — they cannot use `AiderBackend` polymorphically. This means the aider backend is unreachable from automated pipelines.
- **Evidence**:
  ```python
  # AgentBackend.invoke() — full interface
  def invoke(self, prompt: str, backend: ..., timeout: ..., output_callback: ...) -> HandoverManifest:

  # AiderBackend.invoke() — incompatible signature
  def invoke(self, prompt: str) -> HandoverManifest:
  ```
- **Remediation**: Make `AiderBackend` inherit from `AgentBackend` and override `invoke()` with a compatible signature (accepting but ignoring unused params, or using them appropriately). Alternatively, create a factory function `create_backend(config) -> AgentBackend` that returns the right subclass.

#### CRIT-003: Post-guard silently passes when `mise` binary not found

- **File**: `src/deviate/core/agent.py:400-406`
- **Category**: Security / PRD | **Severity**: Critical | **Confidence**: High
- **Problem**: `_run_post_guard()` catches `FileNotFoundError` (mise not installed) and returns the original manifest unchanged. If aider claims "All tests passed" but `mise` is not on PATH, the phase is marked PASS without any actual verification. This defeats the entire purpose of the post-guard (US-005).
- **Evidence**:
  ```python
  def _run_post_guard(self, manifest: HandoverManifest) -> HandoverManifest:
      try:
          guard_result = subprocess.run(
              ["mise", "run", "test"], capture_output=True, text=True
          )
      except FileNotFoundError:
          return manifest  # ← silently passes!
  ```
- **Remediation**: When `mise` is not found, the guard should either raise an error (hard abort) or set `manifest.status = "FAIL"` with `verification_result = "FAIL"` and `error_details = "mise binary not found — post-guard cannot verify"`.
- **Before**:
  ```python
  except FileNotFoundError:
      return manifest
  ```
- **After**:
  ```python
  except FileNotFoundError:
      manifest.status = "FAIL"
      manifest.verification_result = "FAIL"
      manifest.error_details = "mise binary not found — post-guard cannot verify"
      return manifest
  ```

#### CRIT-004: Duplicate ISS-ADH-002 entry in issues.jsonl

- **File**: `specs/issues.jsonl` (lines 1440 and 1442 in diff)
- **Category**: Constitution | **Severity**: Critical | **Confidence**: High
- **Problem**: The append-only ledger has two identical ISS-ADH-002 entries. Constitution §1 states: "All state transitions in `issues.jsonl` and `tasks.jsonl` are append-only. No existing line is ever modified or overwritten." A duplicate entry is not a state transition — it's a data integrity violation that will confuse ledger parsers.
- **Evidence**:
  ```
  {"issue_id":"ISS-ADH-002","type":"feature","title":"Aider Agent Backend Integration","status":"SPECIFIED",...}
  {"issue_id":"ISS-001-008",...}
  {"issue_id":"ISS-ADH-002","type":"feature","title":"Aider Agent Backend Integration","status":"SPECIFIED",...}
  ```
- **Remediation**: Remove the duplicate line. The ledger should have exactly one ISS-ADH-002 entry.

---

### Suggestions

#### SUG-001: Post-guard doesn't populate `verification_result` or `error_details` on failure

- **File**: `src/deviate/core/agent.py:408-411`
- **Category**: PRD | **Severity**: High
- **Current Pattern**: When guard fails, only `manifest.status = "FAIL"` is set.
- **Recommended Pattern**: Also set `manifest.verification_result = "FAIL"` and `manifest.error_details = guard_result.stdout + guard_result.stderr` per US-005 AC-1 ("POST_GUARD_FAILED error including the test output").
- **Rationale**: Downstream consumers (meso/macro pipelines) check `manifest.status` but the spec requires the test output to be surfaced for diagnostics.

#### SUG-002: `AiderBackend.invoke()` hardcodes `Path.cwd()` — not testable without `chdir`

- **File**: `src/deviate/core/agent.py:415`
- **Category**: Idiomacy / Constitution | **Severity**: High
- **Current Pattern**: `repo_root = Path.cwd()` hardcoded in `invoke()`.
- **Recommended Pattern**: Accept `repo_path: Path | None = None` parameter (defaulting to `Path.cwd()`). The constitution's "Universal API Design Constraint" mandates this for all git-interacting functions. Integration tests currently work around this with a `chdir()` context manager.
- **Rationale**: Test isolation principle. The `chdir` workaround in integration tests is fragile and could leak if an exception occurs before the context manager exits.

#### SUG-003: `HandoverManifest` lacks explicit `files_touched`, `verification_result`, `error_details` fields

- **File**: `src/deviate/core/agent.py:19-31`
- **Category**: Clean Code | **Severity**: Medium
- **Current Pattern**: These fields are accepted via `model_config = {"extra": "allow"}` but not declared.
- **Recommended Pattern**: Add explicit optional fields: `files_touched: list[str] | None = None`, `verification_result: str | None = None`, `error_details: str | None = None`.
- **Rationale**: Type safety, IDE support, and discoverability. The AiderBackend relies on these fields heavily but they're invisible in the schema.

#### SUG-004: No streaming output support in `AiderBackend`

- **File**: `src/deviate/core/agent.py:375-398`
- **Category**: Pragmatism | **Severity**: Medium
- **Current Pattern**: `_run_with_retry()` uses `subprocess.run(capture_output=True)` which buffers all output until the process exits.
- **Recommended Pattern**: Use `subprocess.Popen` with line-by-line stdout reading (matching the parent class `_invoke_streaming` pattern) and accept an `output_callback` parameter.
- **Rationale**: The orchestration monitor (ISS-ADH-001) expects real-time `agent_output` events. Aider invocations will show no output until the entire process completes, making the monitor useless for aider runs.

#### SUG-005: `_build_aider_command` passes prompt as CLI argument — OS arg length limits

- **File**: `src/deviate/core/agent.py:306`
- **Category**: Pragmatism | **Severity**: Low
- **Current Pattern**: `args = ["aider", "--message", prompt]` — prompt is a CLI argument.
- **Recommended Pattern**: Consider writing the prompt to a temporary file and using `--message-file` (if aider supports it), or piping via stdin. At minimum, document the limitation.
- **Rationale**: macOS has a 256KB arg limit. With constitution + CLAUDE.md injection, prompts could approach this for large codebases.

#### SUG-006: `_halt` changed from `typer.Exit` to `SystemExit` — inconsistent with rest of CLI

- **File**: `src/deviate/cli/_common.py:98`
- **Category**: Idiomacy | **Severity**: Low
- **Current Pattern**: `raise SystemExit(1)` instead of `raise typer.Exit(code=1)`.
- **Recommended Pattern**: Revert to `typer.Exit(code=1)` or document why `SystemExit` is preferred.
- **Rationale**: `typer.Exit` is the idiomatic way to exit in Typer apps. `SystemExit` bypasses Typer's cleanup and may cause issues with test runners that catch `SystemExit`.

---

### Opportunities

#### OPP-001: Factory pattern for backend selection

- **File**: `src/deviate/core/agent.py`
- **Current Approach**: Callers must know whether to instantiate `AgentBackend` or `AiderBackend` based on config.
- **Potential Improvement**: Add `create_backend(config: AgentConfig) -> AgentBackend` factory that returns the correct class based on `config.backend`.
- **Expected Benefit**: Eliminates the current gap where meso/macro pipelines always use `AgentBackend` regardless of config. Single point of backend selection logic.

#### OPP-002: Explicit `HandoverManifest` subclass for Aider

- **File**: `src/deviate/core/agent.py`
- **Current Approach**: Aider uses the base `HandoverManifest` with extra fields.
- **Potential Improvement**: Define `AiderHandoverManifest(HandoverManifest)` with explicit `files_touched`, `verification_result`, `error_details` fields.
- **Expected Benefit**: Type-safe access to aider-specific manifest fields without relying on `extra = "allow"` dynamic attributes.

---

### Compliance Matrix

| Domain | Status | Summary of Findings |
|--------|--------|---------------------|
| Security | ⚠️ | Post-guard silently passes when `mise` not found (CRIT-003). No secret exposure. |
| Pragmatism | ⚠️ | No streaming output for aider (SUG-004). Prompt as CLI arg has length limits (SUG-005). |
| Idiomacy | ⚠️ | `SystemExit` instead of `typer.Exit` (SUG-006). `Path.cwd()` hardcoded (SUG-002). |
| Clean Code | ✅ | Good test organization, clear class structure. Missing explicit HandoverManifest fields (SUG-003). |
| Constitution | ❌ | `BACKEND_COMMANDS` not updated (CRIT-001). Duplicate ledger entry (CRIT-004). Interface not implemented (CRIT-002). |
| PRD | ❌ | Aider backend unreachable from meso/macro pipelines (CRIT-002). Post-guard doesn't surface test output (SUG-001). |

---

### Quick Fix Summary

| Priority | Category | File | Lines | Issue Description | Effort |
|----------|----------|------|-------|-------------------|--------|
| 1 | Constitution | `src/deviate/core/agent.py` | 69-73 | Add `"aider": "aider"` to `BACKEND_COMMANDS` | Low |
| 2 | Constitution | `src/deviate/core/agent.py` | 293 | Make `AiderBackend` inherit from `AgentBackend` or add factory | Med |
| 3 | Security | `src/deviate/core/agent.py` | 405-406 | Post-guard: fail when `mise` not found instead of silent pass | Low |
| 4 | Constitution | `specs/issues.jsonl` | N/A | Remove duplicate ISS-ADH-002 entry | Low |
| 5 | PRD | `src/deviate/core/agent.py` | 408-411 | Post-guard: set `verification_result` and `error_details` on failure | Low |
| 6 | Idiomacy | `src/deviate/core/agent.py` | 415 | Accept `repo_path` parameter instead of hardcoded `Path.cwd()` | Low |
| 7 | CleanCode | `src/deviate/core/agent.py` | 19-31 | Add explicit `files_touched`, `verification_result`, `error_details` fields to `HandoverManifest` | Low |
| 8 | Idiomacy | `src/deviate/cli/_common.py` | 98 | Revert `SystemExit(1)` to `typer.Exit(code=1)` | Low |

---

### Files Changed (Aider-relevant subset)

| File Path | Total Changes | Issues Found | Brief Note |
|-----------|---------------|--------------|------------|
| `src/deviate/core/agent.py` | +200 | CRIT-001, CRIT-002, CRIT-003, SUG-001 through SUG-005 | Core AiderBackend implementation |
| `src/deviate/state/config.py` | +15 | None | AiderConfig model — clean |
| `tests/test_core/test_agent.py` | +328 | None | Comprehensive test coverage |
| `tests/test_integration/test_aider_backend.py` | +150 | SUG-002 | Integration tests use `chdir` workaround |
| `tests/test_state/test_config.py` | +54 | None | Config validation tests — clean |
| `specs/issues.jsonl` | +3 | CRIT-004 | Duplicate ISS-ADH-002 entry |
| `src/deviate/cli/_common.py` | +1/-1 | SUG-006 | `SystemExit` change |

---

### Overall Assessment

- **Code Quality**: Fair — Core implementation is solid but integration with existing dispatch is broken
- **Readability**: High — Clear class structure, well-organized tests, good naming
- **Maintainability**: Medium — Standalone `AiderBackend` class creates a parallel code path that will drift from `AgentBackend` over time

---

## Fix Instructions

Each entry is an independent fix. Apply in priority order.

### FIX-001: Add aider to BACKEND_COMMANDS
- **File**: `src/deviate/core/agent.py`
- **Line**: 69
- **Severity**: Critical | Confidence: High
- **Change**: Add `"aider": "aider"` entry to the `BACKEND_COMMANDS` dict
- **Current**:
  ```python
  BACKEND_COMMANDS: dict[str, str] = {
      "opencode": "opencode run",
      "claude": "claude -p",
      "droid": "droid exec",
  }
  ```
- **Expected**:
  ```python
  BACKEND_COMMANDS: dict[str, str] = {
      "opencode": "opencode run",
      "claude": "claude -p",
      "droid": "droid exec",
      "aider": "aider",
  }
  ```

### FIX-002: Make AiderBackend inherit from AgentBackend
- **File**: `src/deviate/core/agent.py`
- **Line**: 293
- **Severity**: Critical | Confidence: High
- **Change**: Make `AiderBackend` a subclass of `AgentBackend` so it can be used polymorphically in pipeline code. Override `invoke()` with a compatible signature.
- **Current**:
  ```python
  class AiderBackend:
      def __init__(self, config: AgentConfig | None = None) -> None:
          self.config = config or AgentConfig()
  ```
- **Expected**:
  ```python
  class AiderBackend(AgentBackend):
      def __init__(self, config: AgentConfig | None = None) -> None:
          super().__init__(config)
  ```
  Also update `invoke()` signature to accept (and handle) `output_callback`:
  ```python
  def invoke(
      self,
      prompt: str,
      backend: str | None = None,
      timeout: int | None = None,
      output_callback: OutputCallback | None = None,
  ) -> HandoverManifest:
  ```

### FIX-003: Post-guard must fail when mise not found
- **File**: `src/deviate/core/agent.py`
- **Line**: 405
- **Severity**: Critical | Confidence: High
- **Change**: When `mise` binary is not found, mark manifest as FAIL instead of silently passing
- **Current**:
  ```python
  except FileNotFoundError:
      return manifest
  ```
- **Expected**:
  ```python
  except FileNotFoundError:
      manifest.status = "FAIL"
      manifest.verification_result = "FAIL"
      manifest.error_details = "mise binary not found — post-guard cannot verify"
      return manifest
  ```

### FIX-004: Remove duplicate ISS-ADH-002 from issues.jsonl
- **File**: `specs/issues.jsonl`
- **Line**: Last line (duplicate of an earlier entry)
- **Severity**: Critical | Confidence: High
- **Change**: Remove the last line which is an exact duplicate of the ISS-ADH-002 entry already present. The ledger must have exactly one ISS-ADH-002 entry.
- **Current**: Two identical lines:
  ```
  {"issue_id":"ISS-ADH-002","type":"feature","title":"Aider Agent Backend Integration","status":"SPECIFIED",...}
  ...
  {"issue_id":"ISS-ADH-002","type":"feature","title":"Aider Agent Backend Integration","status":"SPECIFIED",...}
  ```
- **Expected**: One line only.

### FIX-005: Post-guard must populate verification_result and error_details on failure
- **File**: `src/deviate/core/agent.py`
- **Line**: 408
- **Severity**: High | Confidence: High
- **Change**: When post-guard test fails, set `verification_result` and `error_details` on the manifest
- **Current**:
  ```python
  if guard_result.returncode != 0:
      manifest.status = "FAIL"
  ```
- **Expected**:
  ```python
  if guard_result.returncode != 0:
      manifest.status = "FAIL"
      manifest.verification_result = "FAIL"
      manifest.error_details = (
          f"POST_GUARD_FAILED: mise run test exited with code {guard_result.returncode}\n"
          f"{guard_result.stdout}\n{guard_result.stderr}"
      ).strip()
  ```

### FIX-006: Accept repo_path parameter in AiderBackend.invoke()
- **File**: `src/deviate/core/agent.py`
- **Line**: 413
- **Severity**: High | Confidence: High
- **Change**: Add `repo_path` parameter to `invoke()` instead of hardcoding `Path.cwd()`
- **Current**:
  ```python
  def invoke(self, prompt: str) -> HandoverManifest:
      aider_cfg = self.config.aider
      repo_root = Path.cwd()
  ```
- **Expected**:
  ```python
  def invoke(self, prompt: str, ...) -> HandoverManifest:
      aider_cfg = self.config.aider
      repo_root = repo_path or Path.cwd()
  ```

### FIX-007: Add explicit fields to HandoverManifest
- **File**: `src/deviate/core/agent.py`
- **Line**: 19
- **Severity**: Medium | Confidence: High
- **Change**: Add explicit optional fields for aider-specific manifest data
- **Current**:
  ```python
  class HandoverManifest(BaseModel):
      phase: str
      status: str
      task_id: str | None = None
      test_file: str | None = None
      verification_command: str | None = None
      expected_failure_node: str | None = None
      yellow_trigger: bool | None = None
      test_changes: dict[str, Any] | None = None
      rationale: str | None = None
      next_phase: str | None = None
  ```
- **Expected**:
  ```python
  class HandoverManifest(BaseModel):
      phase: str
      status: str
      task_id: str | None = None
      test_file: str | None = None
      verification_command: str | None = None
      expected_failure_node: str | None = None
      yellow_trigger: bool | None = None
      test_changes: dict[str, Any] | None = None
      rationale: str | None = None
      next_phase: str | None = None
      files_touched: list[str] | None = None
      verification_result: str | None = None
      error_details: str | None = None
  ```

### FIX-008: Revert _halt to use typer.Exit
- **File**: `src/deviate/cli/_common.py`
- **Line**: 98
- **Severity**: Low | Confidence: Medium
- **Change**: Revert from `SystemExit(1)` to `typer.Exit(code=1)` for consistency with the rest of the CLI
- **Current**:
  ```python
  raise SystemExit(1)
  ```
- **Expected**:
  ```python
  raise typer.Exit(code=1)
  ```
