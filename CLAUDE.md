<!-- MANAGED_BY: tools:init -->

## ⚙️ Project Execution Contract (MANDATORY)

- **Repository Type**: single-language (Python)
- **Execution Mode**: TDD (Red-Green-Refactor via deviate cycle)
- **Performance Constraints**: L_max <= 500ms for init, L_max <= 200ms per agent export

## 🧠 State & Authority Model (MANDATORY)

- Primary State Tracker: `git` commits
- Project Constitution: `specs/constitution.md`
- Core Strategy Ledger: `specs/001-deviate-cli-bootstrapping/000-project-bootstrap/plan.md`

## ⚡ Fast-Lane Execution Contract

- Use `mise run <task>` for all task execution
- Deterministic tooling via `.mise.toml`
- Git hooks under `.githooks/`

## 🛠️ Mise Tasks as Execution API

| Task | Purpose |
|------|---------|
| `mise run test` | Run unit tests |
| `mise run test-e2e` | Run E2E tests via bats |
| `mise run lint` | Lint Python |
| `mise run lint-fix` | Apply lint fixes |
| `mise run format` | Format Python |
| `mise run format-check` | Check formatting |
| `mise run check-types` | Type check |
| `mise run fix` | Format + lint fix |
| `mise run check` | All validation checks |
| `mise run setup` | Install deps + hooks |
| `mise run clean` | Remove artifacts |
| `mise run help` | List tasks |

## 🔐 Git Commit Authority (MANDATORY)

- Commit after each verified successful verification loop
- Never use `--no-verify`
- Preserve all semantic anchors

## 🧪 Test Git Isolation (MANDATORY)

Never run git commands against the real repo during tests. Every git
operation in tests MUST target a `tmp_path`-based isolated repo.

- Use the `tmp_git_repo` fixture (created by T002 in `tests/conftest.py`)
- Every `git` subprocess call MUST include `cwd=<tmp_git_repo>` — the `cwd`
  flag is the ONLY thing scoping the command to the temp repo
- Never use `Path.cwd()`, `os.getcwd()`, or the real repo root in tests
- Verify test isolation: `git config user.name` inside the fixture should
  show `Test Runner`, never the real user's name

See `spec.md` §`TEST_ISOLATION_CONSTRAINTS` and `tasks.md` §`Universal
Test Constraints` for full rules.

## ⚡ Test Performance (MANDATORY)

Never call `_run_pytest()` (in `src/deviate/cli/micro.py`) in tests.
Tests that invoke CLI commands which internally call `_run_pytest` (red post,
green post, refactor post) MUST mock `deviate.cli.micro._run_pytest` with an
appropriate `subprocess.CompletedProcess` return value.

Performance target: full suite < 18s. If adding a test via `runner.invoke(cli,
["red", "post"])` and it calls `_run_pytest`, the test will trigger ALL pytest
tests as a subprocess (~5s per invocation). Always mock it.

Example:
```python
@patch("deviate.cli.micro._run_pytest")
def test_something(self, mock_pytest, tmp_git_repo):
    mock_pytest.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="1 passed", stderr=""
    )
```

For refactor_post tests that call `_run_pytest` twice, use `side_effect`:
```python
mock_pytest.side_effect = [
    subprocess.CompletedProcess(args=[], returncode=0, stdout="1 passed", stderr=""),
    subprocess.CompletedProcess(args=[], returncode=0, stdout="1 passed", stderr=""),
]
```

## DeviaTDD Phase Architecture

### Macro Layer — Feature Scoping
- `/explore` → **DeepSeek V4 Flash**: Fast scan of codebase structure, dependencies, and patterns. Outputs `explore.md` (what exists, not what to do).
- `/research` → **Qwen3.7-Plus [Thinking Mode]**: Consumes `explore.md`, performs architectural analysis. Outputs `design.md` (trade-offs, decisions) and `data-model.md` (schemas, relationships).
- `/prd` → **Qwen3.7-Plus [Thinking Mode]**: Translates `design.md` into immutable user requirements and acceptance criteria in `prd.md`.
- `/shard` → **Qwen3.7-Plus [Thinking Mode]**: Breaks PRD into ~5 independent vertical-slice issues (3-10 bounds). Each issue is end-to-end testable.

### Meso Layer — Issue Engineering
- `/specify` → **DeepSeek V4 Pro**: Converts issue data into functional contract `spec.md` (business boundaries, edge cases — no implementation).
- **[HITL Gate 2]**: Human reviews `spec.md` before task decomposition proceeds.
- `/tasks` → **DeepSeek V4 Pro** (same continuous thread as /specify for prefix cache): Decomposes `spec.md` into ~5 TDD-cycle tasks with implementation hints (3-10 bounds). Merged former `/plan` role. Appends terminal `type: "e2e"` task.

### Micro Layer — TDD Sandbox
- **RED** → **DeepSeek V4 Flash**: Write failing test; verified to fail due to missing implementation.
- **GREEN** → **DeepSeek V4 Flash**: Write production code to pass test; tamper guard reverts unauthorized test edits.
- **YELLOW** → **DeepSeek V4 Flash** (conditional): If RED test is flawed, propose amendment for isolated judge approval/rejection.
- **JUDGE** → **DeepSeek V4 Pro**: Isolated compliance gate evaluates `git diff` against `spec.md` for security and structural violations.
- **REFACTOR** → **DeepSeek V4 Flash**: Polish implementation; regression gate re-runs tests, rolls back on failure.

### Fast-Path
- `/adhoc` → **Qwen3.7-Plus [Thinking Mode]**: Compresses Explore + Research + PRD + Shard for low/medium complexity tasks via complexity gate.

### HITL Gates
- **Gate 1**: After `/research`, before `/prd` — human approves design and data model.
- **Gate 2**: After `/specify`, before `/tasks` — human approves functional contract.
- **Gate 3**: After all tasks complete — human approves merge.

### Model Routing Rationale
- **Explorers (low-cost ingestion)**: `/explore`, RED/GREEN/REFACTOR → V4 Flash for high-volume reading and code generation.
- **Architects (premium strategic logic)**: `/research`, `/prd`, `/shard`, `/adhoc` → Qwen3.7-Plus [Thinking Mode] for abstract reasoning and constraint satisfaction.
- **Translators (cached engineering)**: `/specify` + `/tasks` → V4 Pro in single continuous thread for 90%+ prefix cache discount.
- **Compliance gate**: JUDGE → V4 Pro for isolated security and drift verification.

## Python-Only Architecture

All deviate operations are Python-based. Skills live as package resources under
`src/deviate/prompts/skills/<name>/SKILL.md` and are invoked via the `deviate`
CLI (`deviate <subcommand>`) instead of shell scripts. No `.sh` files exist in
the `prompts/` directory. The `mise.toml` file defines all task execution via
`uv run` — no shell script tasks.

## Skill Resolution

When a skill file references `<SKILL_DIR>/<script>.sh`, resolve `<SKILL_DIR>` to
`src/deviate/prompts/skills/<name>/` and use `deviate <subcommand>` instead.

## Prompt Edit Discipline

All skill and prompt template edits MUST target `src/deviate/prompts/`.
The `~/.config/opencode/skills/` directory is a read-only install mirror;
edits there are overwritten on reinstall. Always edit the source tree and commit
through the deviate system.

## Technical Execution Context

Tasks=status: READY, repo_root: , deviate_path: .deviate, specs_path: specs, timestamp: 2026-06-13T15:05:23.081175
