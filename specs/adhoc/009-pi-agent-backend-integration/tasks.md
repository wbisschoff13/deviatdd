# Implementation Tasks: `feat/adhoc/009-pi-agent-backend-integration`

## Phase 1: Core Backend Contract
**Goal**: Register Pi as a first-class backend — widen Pydantic model validation, extend the command registry, add per-backend model-flag dispatch, implement error handling for missing binary, build test fixtures, and verify YAML manifest extraction for Pi-shaped output.

### Tasks

- TSK-009-01: Register Pi backend in config model, command registry, model-flag dispatch, error handling, and test fixtures
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `mise run test tests/core/test_agent.py -v`
  - **Estimated Time**: 90 minutes
  - **Files**:
    - `src/deviate/state/config.py`
    - `src/deviate/core/agent.py`
    - `tests/core/test_agent.py`
  - **Rationale**: Widen `AgentConfig.backend` Literal to `"pi"` so Pydantic validation accepts the new backend (US-009-01, AC-009-08). Extend `BACKEND_COMMANDS` with `"pi": "pi -p"` so the subprocess dispatch resolves the correct binary (AC-009-07). Add `MODEL_FLAGS` per-backend map so Pi print mode does not receive `--model` (it rejects it; model routing goes through `settings.json`) — addresses US-009-02, AC-009-01. Handle `FileNotFoundError` for missing `pi` binary with `AgentBinaryNotFoundError` (edge case §Pi binary missing). Add `StubPiBackend` fixture mirroring `StubAgentBackend` for downstream test isolation (AC-009-09 multi-target). Verify Pi-shaped YAML output parses through the existing `_YAML_BLOCK_RE` / `_YAML_HANDOVER_MARKER_RE` pipeline.
  - **Details**:
    - **Red**: In `tests/core/test_agent.py`, write `test_agent_config_literal_accepts_pi` — construct `AgentConfig(backend="pi")` and assert `model_dump()["backend"] == "pi"`. Write `test_agent_config_literal_rejects_unknown` — construct `AgentConfig(backend="unknown")` and assert `ValidationError`. Write `test_pi_backend_subprocess_contract` — patch `subprocess.Popen`, call `AgentBackend(AgentConfig(backend="pi")).invoke(prompt="...")`, assert spawned `cmd[0]` is `"pi"` and `cmd[1]` is `"-p"`, prompt piped via `stdin`. Write `test_pi_backend_model_flag_not_injected` — patch `subprocess.Popen`, call `invoke()` with `model="some-model"` on pi backend, assert `"--model"` not in spawned `cmd`. Write `test_pi_backend_missing_binary` — patch `subprocess.Popen` to raise `FileNotFoundError`, assert `AgentBinaryNotFoundError` raised. Write `test_pi_backend_yaml_extraction` — feed Pi-shaped stdout (fenced YAML block + `<handover_manifest>` tag) through `AgentBackend.parse_output()`, assert `HandoverManifest` parses. Write `test_stub_pi_backend_yields_canonical_manifest` — instantiate `StubPiBackend`, invoke, assert returned `HandoverManifest.phase == "RED"` and `status == "success"`.
    - **Green**: In `src/deviate/state/config.py:14`, widen Literal to `Literal["opencode", "claude", "droid", "pi"]`. Add `pi_rpc: bool = Field(default=False, description="Opt-in RPC mode for Pi — spawns pi --mode rpc --no-session instead of pi -p")`. In `src/deviate/core/agent.py:60`, add `"pi": "pi -p"` to `BACKEND_COMMANDS`. Add module-level `MODEL_FLAGS: dict[str, list[str] | None] = {"pi": None, "opencode": ["--model"], "droid": ["--model"]}`. In `invoke()` at line 291, replace `if model is not None and backend_name != "claude":` with a `MODEL_FLAGS.get(backend_name)` lookup — if `MODEL_FLAGS[backend_name]` is `None`, skip `--model` injection; if it is a list, use its first element as the flag. In `invoke()` at line 305-306, the `FileNotFoundError` catch for `subprocess.Popen` already wraps to `AgentBinaryNotFoundError` — verify it triggers for `pi`. Add `StubPiBackend(StubAgentBackend)` class returning `HandoverManifest(phase="RED", status="success")`.
    - **Refactor**: Ensure `MODEL_FLAGS.get(backend_name, ["--model"])` default preserves existing behavior for unrecognized backends. Verify `StubPiBackend` reuses `StubAgentBackend.__init__` via `super()`. Add inline `# type: ignore` comment on `Literal` violation if `invoke()` backend Literal widening creates type-check gap (the `invoke()` signature uses a Literal that predates pi; the actual backend routing is dynamic via `BACKEND_COMMANDS`).
    - **Edge Cases**: `pi` binary not on PATH → `AgentBinaryNotFoundError` with install instructions. `MODEL_FLAGS[unknown_backend]` → default `["--model"]` for backward compatibility. Pi YAML output with extra frontmatter fields → `HandoverManifest.model_config = {"extra": "allow"}` handles it. `StubPiBackend` invoked without `StubAgentBackend._invoked` flag → inherits from parent.
    - **Acceptance**: `mise run test tests/core/test_agent.py -v` exits 0. All tests: literal accept, literal reject, subprocess contract, model flag not injected, missing binary, YAML extraction, stub backend — pass. `AgentConfig(backend="pi")` round-trips through `model_dump()`/`model_validate()`. `BACKEND_COMMANDS["pi"]` resolves to `"pi -p"`.

---

## Phase 2: Agent Selection Build & Init Flow Integration
**Goal**: Expose Pi in user-facing agent selection (AGENT_CHOICES, AGENT_TO_BACKEND) and wire the `deviate init` flow to create Pi skill symlinks and settings.json when `agent.backend = "pi"`.

### Tasks

- TSK-009-02: Add Pi to agent selection constants and implement `deviate init` Pi-specific setup: skill symlinks and settings.json generation
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `mise run test tests/cli/test_init.py -v`
  - **Estimated Time**: 90 minutes
  - **Files**:
    - `src/deviate/cli/__init__.py`
    - `tests/cli/test_init.py`
  - **Rationale**: Extend `AGENT_CHOICES` and `AGENT_TO_BACKEND` to include `"pi"` so users can select it via `--agent pi` and the backend dispatch maps correctly (US-009-01, AC-009-05). Implement `_setup_pi_skills(workdir)` in the init flow so Pi discovers DeviaTDD's 20 skill directories natively via symlinks under `~/.pi/agent/skills/` (US-009-04, AC-009-02). Implement `_generate_pi_settings(workdir, config_path)` so the `[models]` section of `.deviate/config.toml` maps onto `~/.pi/agent/settings.json` for Pi's provider/model routing (US-009-02, AC-009-03). Enforce idempotency across re-runs and preserve user-managed settings keys (edge cases §Settings.json merge, §Skill directory already exists).
  - **Details**:
    - **Red**: In `tests/cli/test_init.py`, write `test_agent_choices_includes_pi` — assert `"pi" in AGENT_CHOICES`. Write `test_agent_to_backend_maps_pi` — assert `AGENT_TO_BACKEND["pi"] == "pi"`. Write `test_init_creates_pi_skill_symlinks` — mock `Path.home()` to a `tmp_path`, run `deviate init --agent pi --no-interactive`, assert 20 symlinks under `.pi/agent/skills/`, each `readlink` resolves to `src/deviate/prompts/skills/<name>`. Write `test_init_generates_pi_settings_json` — mock `Path.home()`, provide `.deviate/config.toml` with `[models]\ndefault = "anthropic/claude-sonnet-4-5"`, run init, assert `~/.pi/agent/settings.json` contains `{"provider": "anthropic", "model": "claude-sonnet-4-5", "skillPaths": [...]}`. Write `test_init_idempotent_pi_setup` — run init twice, assert no duplicate symlinks, settings.json unchanged, no errors. Write `test_init_preserves_user_managed_settings_keys` — pre-populate settings.json with `{"custom_key": "val"}`, run init, assert `custom_key` preserved, DeviaTDD keys added/updated. Write `test_init_pi_skill_symlinks_skip_existing_directories` — pre-create `~/.pi/agent/skills/deviate-explore` as a real directory, run init, assert SKIP logged, directory untouched.
    - **Green**: In `src/deviate/cli/__init__.py:44`, extend `AGENT_CHOICES` with `"pi"`. In line 49-54, add `"pi": "pi"` to `AGENT_TO_BACKEND`. In `_get_agent_skill_dir` (line 508), add `if agent_name == "pi": return Path.home() / ".pi" / "agent" / "skills"`. Add `_setup_pi_skills(workdir: Path) -> None` helper: iterate `discover_skills()` from `deviate.core.skills`, for each create `Path.home() / ".pi" / "agent" / "skills" / f"deviate-{skill_name}"` symlink pointing to the absolute `src/deviate/prompts/skills/<skill_name>` directory. Create parent dirs with `mkdir(parents=True, exist_ok=True)`. Skip if target exists as a real directory (not symlink) — log `[yellow]SKIP[/]`. Add `_generate_pi_settings(workdir: Path, config_path: Path) -> None` helper: read `[models]` from `config_path` via `tomllib`, resolve `default` model, split `provider/model` from `provider/model_id` format, write `~/.pi/agent/settings.json` with `provider`, `model`, `skillPaths` (list with one entry: absolute path to `src/deviate/prompts/skills`). On re-run, parse existing settings.json, merge DeviaTDD-managed keys (`provider`, `model`, `skillPaths`), preserve all other keys. Write only if content differs. Call both helpers from the init flow when `agent.backend == "pi"`.
    - **Refactor**: Extract `_split_provider_model(model_str: str) -> tuple[str, str]` helper for the `provider/model_id` → `(provider, model)` split. Use `console.print` with Rich markup consistent with existing `SKIP`/`CREATE`/`INSTALL` log lines. Ensure symlink targets are absolute via `pathlib.Path.resolve()`.
    - **Edge Cases**: `~/.pi/agent/` directory missing → `mkdir(parents=True, exist_ok=True)`. Symlink target missing (skill directory deleted) → Pi logs warning on discovery; `deviate init` re-creates on subsequent runs. Settings.json merge with non-DeviaTDD keys → preserve, only write `provider`, `model`, `skillPaths`. `provider/model_id` split on `"/"` with no slash → treat full string as `model`, `provider = ""`. Concurrent init runs → `fcntl.flock` on settings.json write (like existing ledger writer). Cross-platform symlink on Windows → `OSError` surfaced with clear error.
    - **Acceptance**: `mise run test tests/cli/test_init.py -v` exits 0. All 7 Pi init tests pass. `AGENT_CHOICES` contains `"pi"`. `AGENT_TO_BACKEND["pi"] == "pi"`. 20 symlinks created with correct targets. settings.json mirrors `[models]` config. Idempotent re-runs succeed. User-managed settings keys survive.

---

## Phase 3: RPC Mode Dispatch (Opt-In)
**Goal**: Enable opt-in RPC mode (`pi --mode rpc --no-session`) via `agent.pi_rpc = true` config key — spawn JSONL-over-stdin/stdout client, parse streaming events, and extract the handover manifest from `agent_end`.

### Tasks

- TSK-009-03: Implement RPC mode dispatch when `pi_rpc = true` — spawn `pi --mode rpc --no-session`, send JSONL prompt, parse stream, extract manifest from `agent_end`
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `mise run test tests/core/test_agent.py::test_pi_rpc_mode_opt_in -v`
  - **Estimated Time**: 60 minutes
  - **Files**:
    - `src/deviate/core/agent.py`
    - `tests/core/test_agent.py`
  - **Rationale**: When `agent.pi_rpc = true`, DeviaTDD must spawn Pi in RPC mode instead of print mode. RPC mode uses JSONL-over-stdin/stdout for streaming events including `agent_start`, `message_update`, and `agent_end` (the source of truth for the handover manifest). This addresses US-009-05 and AC-009-10. RPC mode also enables per-phase model swaps via Pi's `set_model` RPC command and captures `get_session_stats` for cost observability (TSK-009-04).
  - **Details**:
    - **Red**: In `tests/core/test_agent.py`, write `test_pi_rpc_mode_opt_in` — construct `AgentConfig(backend="pi", pi_rpc=True)`, patch `subprocess.Popen`, call `invoke(prompt="...")`, assert spawned `cmd` is `["pi", "--mode", "rpc", "--no-session"]`. Feed a mock RPC event stream via `stdout` (`agent_start`, `message_update`, `agent_end` with handover manifest payload), assert `HandoverManifest` extracted correctly.
    - **Green**: In `src/deviate/core/agent.py`, in `invoke()` after resolving `backend_name == "pi"` and `cmd = ["pi", "-p"]`, add branch: if `self.config.pi_rpc` is `True`, set `cmd = ["pi", "--mode", "rpc", "--no-session"]`. Implement `_invoke_rpc(proc, prompt, timeout, backend_name)` that writes `{"type": "prompt", "content": "<prompt>"}\n` to stdin, reads JSONL from stdout line-by-line, parses `agent_start`, `message_update` (stream to `output_callback` if present), and `agent_end` — extract `message.content` text, pass to `self.parse_output()`. On timeout, raise `AgentTimeoutError` with partial stdout collected so far. On non-zero exit, raise `AgentSubprocessError`. On JSONL parse error for a single malformed line, log warning via `console.print` and skip.
    - **Refactor**: Extract JSONL line reading into a generator helper `_read_jsonl_lines(stream)` yielding `(line_str, parsed_dict)`. Reuse existing `parse_output()` for manifest extraction from `agent_end` message content. Ensure `_invoke_rpc` signature matches the existing blocking/streaming dispatch pattern in `invoke()`.
    - **Edge Cases**: JSONL malformed line → log warning, skip, continue. Missing `agent_end` event → treat last `message_update` text as output, attempt manifest extraction. Pi RPC mode process exits non-zero → `AgentSubprocessError` with stderr surfaced. `pi_rpc = true` but Pi binary only supports print mode (< v0.80.0) → `AgentSubprocessError` with Pi's error message. Prompt contains JSON-special characters → JSON-escaped via `json.dumps()` before embedding in `{"content": ...}`.
    - **Acceptance**: `test_pi_rpc_mode_opt_in` passes. `agent.pi_rpc = true` spawns `["pi", "--mode", "rpc", "--no-session"]` instead of `["pi", "-p"]`. JSONL event stream parsed correctly. `HandoverManifest` extracted from `agent_end` payload.

---

## Phase 4: Token Observability — pi.session_stats
**Goal**: Capture Pi's token statistics (tokens.input, output, cacheRead, cacheWrite) from agent output and append a `pi.session_stats` JSON block to `prompts.log` AGENT_RESULT events when the backend is Pi.

### Tasks

- TSK-009-04: Extract `pi.session_stats` from Pi agent output and enrich prompts.log AGENT_RESULT entries
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `mise run test tests/core/test_agent.py::test_pi_session_stats_logged -v`
  - **Estimated Time**: 60 minutes
  - **Files**:
    - `src/deviate/cli/micro.py`
    - `tests/core/test_agent.py`
  - **Rationale**: Pi emits token stats (via `--print-tokens` in print mode, or `get_session_stats` / `agent_end` event in RPC mode) with fields `tokens.input`, `tokens.output`, `tokens.cacheRead`, `tokens.cacheWrite`. Capturing these into `prompts.log` AGENT_RESULT events enables cost observability and cache-hit ratio computation (US-009-03, AC-009-04). Stats must be non-null when present in Pi output; absent stats log a warning but do not fail.
  - **Details**:
    - **Red**: In `tests/core/test_agent.py`, write `test_pi_session_stats_logged` — patch `subprocess.Popen` to return Pi-shaped stdout containing a token-stats footer block (`tokens.input: 1234\n`, `tokens.output: 567\n`, `tokens.cacheRead: 890\n`, `tokens.cacheWrite: 45\n`), wrap in a test that exercises `_extract_pi_session_stats(stdout)` → assert dict has all four keys with correct int values. Then test the full logging path — call through `_invoke_agent(backend_name="pi")` (mock AgentBackend.invoke to return manifest + raw lines containing stats), assert `_log_run("AGENT_RESULT", ...)` receives `pi_session_stats` kwarg.
    - **Green**: In `src/deviate/cli/micro.py`, add `_extract_pi_session_stats(stdout: str) -> dict[str, int] | None` helper that scans stdout for token lines matching pattern `tokens\.(input|output|cacheRead|cacheWrite):\s*(\d+)`. Returns dict with camelCase keys or `None` if no stats found. Integrate into `_invoke_agent()` after `manifest = backend.invoke(...)`: if `backend_name == "pi"`, extract stats from `raw_lines` joined output, pass as `pi_session_stats=<dict>` or `pi_session_stats=None` to `_log_run("AGENT_RESULT", ...)`. Update the `_log_run("AGENT_RESULT", ...)` call at line 336-343 to include `pi_session_stats=pi_stats` keyword (the `**kwargs` log call already supports arbitrary keys). If stats absent, log a `[yellow]WARN[/]` via `c.print` but do not fail.
    - **Refactor**: Ensure `_extract_pi_session_stats` handles both `tokens.input:` and `tokens:\n  input:` formats (Pi may emit as YAML-like or key-value). Use a single regex `tokens\.\s*(input|output|cacheRead|cacheWrite)\s*:?\s*(\d+)` for robustness. In `_invoke_agent`, move the `raw_lines` collection to always capture stdout (not just via `collecting_handler`), so stats extraction can access full output even when `_invoke_blocking` path is used.
    - **Edge Cases**: Token stats absent from Pi output → `_extract_pi_session_stats` returns `None`, log `[yellow]WARN[/] no session stats`, no `pi.session_stats` block in log entry. Partial stats (only input/output, no cache fields) → return only present fields, log warning for missing. Malformed number values → skip that field, log warning. Non-Pi backend → `_extract_pi_session_stats` not called. RPC mode stats from `agent_end` event differ in format → regex accommodates both `key: value` and JSON formats.
    - **Acceptance**: `test_pi_session_stats_logged` passes with all four stats fields non-null when present in output. `prompts.log` AGENT_RESULT entry for Pi backend contains `pi.session_stats` sub-object. Absent stats log warning but do not fail.

---

## Phase 5: Spec Documentation
**Goal**: Document Pi backend in the authoritative spec files — backend selection matrix, model-flag dispatch difference, skill symlink strategy, settings.json generation, RPC mode opt-in, and token stats logging.

### Tasks

- TSK-009-05: Document Pi backend in DeviaTDD-api.md and DeviaTDD-architecture.md
  - **Type**: Config
  - **Mode**: IMMEDIATE
  - **Verification**: Manual review of `specs/DeviaTDD-api.md` and `specs/DeviaTDD-architecture.md` for Pi backend documentation
  - **Estimated Time**: 45 minutes
  - **Files**:
    - `specs/DeviaTDD-api.md`
    - `specs/DeviaTDD-architecture.md`
  - **Rationale**: Per Spec Alignment mandate, any change to backend architecture must be reflected in both authoritative spec documents. The backend selection matrix in `DeviaTDD-api.md` must include Pi with print mode + opt-in RPC mode. The `DeviaTDD-architecture.md` §Backend Architecture section must document Pi-specific customizations: skill symlink strategy, settings.json generation for model routing (vs `--model` flag injection for opencode/droid), RPC mode opt-in, and `pi.session_stats` logging.
  - **Details**:
    - **Implementation**: In `specs/DeviaTDD-api.md`, add a Pi row to the backend selection matrix table with columns: Backend name (`pi`), CLI command (`pi -p`), Model flag (`N/A — routes via ~/.pi/agent/settings.json`), RPC mode (`pi --mode rpc --no-session`, opt-in via `agent.pi_rpc = true`), Token stats (`pi.session_stats` in prompts.log). In `specs/DeviaTDD-architecture.md`, under a new or existing §Backend Architecture section, add a subsection for Pi documenting: (1) skill symlink strategy at init — `~/.pi/agent/skills/` symlinks to `src/deviate/prompts/skills/`, (2) settings.json generation from `[models]` config, (3) model-flag dispatch difference — Pi does not accept `--model`, routes through settings.json instead, (4) RPC mode as opt-in for streaming JSONL events, (5) token stats capture into `pi.session_stats`, (6) defensive exclusions: no binary bundling, no macro layer support yet, no sub-agent delegation.
    - **Edge Cases**: None — pure documentation task.
    - **Acceptance**: Both spec files contain Pi backend entries. Backend selection matrix includes pi row. Architecture doc covers skill symlinks, settings.json, model routing, RPC mode, and token stats. Documentation is consistent with the implementation in TSK-009-01 through TSK-009-04.
  - **Dependency**: TSK-009-01

---

## Phase 6: End-to-End Integration Verification
**Goal**: Verify the full `deviate init` + Pi export cycle completes within performance constraints and the init-to-agent pipeline works end-to-end for the Pi backend.

### Tasks

- TSK-009-06: E2E integration test for Pi init + export cycle
  - **Type**: Infra_Batch
  - **Mode**: TDD
  - **Test Strategy**: Integration
  - **Verification**: `mise run test tests/cli/test_init_export_cycle.py -v`
  - **Estimated Time**: 45 minutes
  - **Files**:
    - `tests/cli/test_init_export_cycle.py`
  - **Rationale**: The existing `test_init_export_cycle.py` verifies init + agent export for opencode/claude/droid. Pi must be included in this integration test to confirm the full pipeline — config creation, skill symlinks, settings.json generation, agent export — completes within the L_max ≤ 500ms init constraint. Addresses the Integration Sandbox Target from the spec's Multi-Tiered Verification Targets.
  - **Details**:
    - **Red**: In `tests/cli/test_init_export_cycle.py`, write `test_init_export_pi_backend` — run `deviate init --agent pi --no-interactive` in a `tmp_path` workspace, assert `.deviate/config.toml` contains `backend = "pi"`, assert skill symlinks created under mocked `~/.pi/agent/skills/`, assert settings.json exists with correct provider/model, assert init completes in < 500ms. Mock `Path.home()` to tmp_path to isolate from real filesystem.
    - **Green**: No production code changes — the test verifies the existing `deviate init` flow with Pi backend after TSK-009-02 is implemented. If test fails, revisit TSK-009-02 for missing init flow integration.
    - **Refactor**: Ensure test uses the same `Path.home()` mock pattern as TSK-009-02 tests. Use `time.perf_counter()` for performance assertion.
    - **Edge Cases**: Pi binary not on PATH (CI environments) → the init flow doesn't invoke Pi, so this should not block the test. Symlink creation on macOS/Linux (POSIX) → test passes. Symlink creation on Windows → may require admin/Developer Mode; document as known limitation.
    - **Acceptance**: `test_init_export_pi_backend` passes. Init completes in < 500ms. Config.toml reflects `backend = "pi"`. Symlinks and settings.json present and correct.
  - **Dependency**: TSK-009-02

---

## Implementation Strategy
**Execution Order**:
1. Phase 1 → Phase 2 → Phase 5 (docs after init flow) → Phase 3 → Phase 4 → Phase 6
2. Phase 5 (docs) can run in parallel with Phase 3 and Phase 4 after Phase 1 completes

**Critical Dependency Chains**:
- TSK-009-01 must precede TSK-009-02 (init flow needs `AgentConfig` to accept `"pi"`)
- TSK-009-01 must precede TSK-009-03 (RPC mode extends `invoke()` from core)
- TSK-009-01 must precede TSK-009-04 (token stats hooks into agent invocation path)
- TSK-009-02 must precede TSK-009-06 (E2E test requires Pi init flow)

**Risk Hotspots**:
- `MODEL_FLAGS` per-backend map: default `["--model"]` must remain for all existing backends; `None` for Pi must skip injection without breaking `opencode`/`droid`/`stub`. Test with `test_pi_backend_model_flag_not_injected` and regression-test with existing `test_command_with_model`.
- Settings.json merge logic: non-DeviaTDD keys must survive re-runs. Test with `test_init_preserves_user_managed_settings_keys` and idempotency test.
- Cross-platform symlink: `pathlib.Path.symlink_to()` may fail on Windows without Developer Mode. Surface clear error, do not crash.
- RPC mode JSONL parsing: malformed lines must not crash the agent loop. Test with malformed JSONL line.

**Merge Conflict Boundaries**:
- `src/deviate/core/agent.py`: touched by TSK-009-01 and TSK-009-03
- `src/deviate/state/config.py`: touched by TSK-009-01 only
- `src/deviate/cli/__init__.py`: touched by TSK-009-02 only
- `src/deviate/cli/micro.py`: touched by TSK-009-04 only
- `tests/core/test_agent.py`: touched by TSK-009-01, TSK-009-03, TSK-009-04
- `tests/cli/test_init.py`: touched by TSK-009-02 only
- `tests/cli/test_init_export_cycle.py`: touched by TSK-009-06 only
- `specs/DeviaTDD-api.md`: touched by TSK-009-05 only
- `specs/DeviaTDD-architecture.md`: touched by TSK-009-05 only

---

## Universal Test Constraints (ALL TASKS)

- **Git Isolation Mandatory**: Any test that invokes git operations MUST operate on a temporary directory initialized as a fresh git repo. Tests MUST NOT run git commands within the real repository's working tree.
- **Implementation Pattern**: Use a shared `tmp_git_repo` fixture from `tests/conftest.py`. Pass `repo=tmp_git_repo` to all git-interacting functions. Never reference `Path.cwd()` or the real repo root.
- **Rationale**: Prevent accidental commits, branch creation, or state mutation in the actual project repo during test execution.
- **Test Performance**: Never call `_run_pytest()` (in `src/deviate/cli/micro.py`) in tests. Mock `deviate.cli.micro._run_pytest` with an appropriate `subprocess.CompletedProcess` return value if tests invoke CLI commands that call `_run_pytest`.
- **Agent Mocking**: All Pi agent invocation tests (TSK-009-01, TSK-009-03, TSK-009-04) MUST mock `subprocess.Popen` — do NOT require the `pi` binary on the test runner's PATH.

## Universal API Design Constraint (ALL CORE MODULES)

Every git-interacting function in core modules MUST accept an optional `repo_path: Path | None = None` parameter. When `None`, default to `Path.cwd()`.
