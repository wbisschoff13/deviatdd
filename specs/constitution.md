# Project Constitution

[CONSTITUTION_VERSION]: 0.1.0

---

## [1_ARCHITECTURAL_PRINCIPLES]
- Hierarchical lifecycle enforcement: Macro (Scoping) → Meso (Contracts) → Micro (TDD Loop)
- Human-in-the-Loop (HITL) checkpoint gates at layer transitions
- The Git Isolation Principle: every isolated task loop executes on a clean git branch/worktree; commits auto-generated at phase boundaries
- The Test Reversion & Scope Audit Law (Tamper Guard): GREEN phase triggers `git checkout HEAD -- <test_dir>` to revert unauthorized test mutations; diff audit validates implementation scope
- State Immobility: agents cannot edit task status in `tasks.md`; status fields modified exclusively by CLI runner
- Deterministic Test Failure Check: RED phase valid only when test fails via AssertionError/NotImplementedError, not syntax/runtime errors
- Memory Preservation via Train Gates: failed compliance checks trigger `git reset --hard HEAD~1` with preserved failure logs injected into agent context
- Elastic Governance Rule: execution overhead scaled via project-level profiles in `.deviate/config.toml` (e.g., `--profile fast` vs `--profile secure`)
- Rejection of autonomous closed-loop factory model; explicit HITL anchoring required

---

## [2_TECH_STACK_STANDARDS]

### [2_1_BACKEND]
- Framework: DeviaTDD Python CLI (`deviate`); language-agnostic engine
- Runtime: Python 3.10+ (CLI host), agent runtime language determined by target project

### [2_2_FRONTEND]
- Framework: TBD by project specification
- Note: Frontend components subject to DeviaTDD Micro Layer validation when included in feature scope

### [2_3_DATABASE]
- Database: TBD by project specification
- Note: DeviaTDD enforces database schema contracts via spec.md boundaries

### [2_4_INFRASTRUCTURE]
- Infrastructure: TBD by project specification
- Infrastructure-as-code support: terraform/ (if present)

### [2_5_TOOLING]
- CLI Engine: `deviate` (Python)
- VCS: Git (required for state machine enforcement)
- Test Runners: pytest (Python), jest (Node.js), go test (Go) - via unified driver specification
- Linting: TBD per project (mix credo for Elixir, ruff for Python, eslint for JS)

---

## [3_TESTING_PROTOCOLS]

### [3_1_FRAMEWORK]
- TEST_FRAMEWORK: pytest | jest | go test (unified abstraction)
- TEST_ROOT: tests/ (Python), __tests__/ (Node.js), *_test.go (Go)
- TEST_EXT: _test.py | .test.ts | _test.go
- TEST_COMMAND: pytest --json-report | jest --json | go test -json
- LINT_COMMAND: TBD per project

### [3_2_COVERAGE]
- COVERAGE_THRESHOLD: TBD per project (default: 80%)
- Coverage enforcement: Judge Phase validates coverage meets threshold before TASK_DONE

---

## [4_DEFINITION_OF_DONE]
- [ ] Code implemented per spec.md functional contract
- [ ] Tests passing (RED-GREEN cycle complete)
- [ ] Coverage requirements met
- [ ] Judge Phase verdict: PASS
- [ ] Refactor phase regression check passed
- [ ] Git phase commits generated (test: [TASK-ID], feat: [TASK-ID])
- [ ] No governance violations (Tamper Guard, State Immobility enforced)
- [ ] Documentation updated (spec.md, plan.md, tasks.md)

---

## [5_VERSION_HISTORY]
- 0.1.0 — Initial constitution derived from DeviaTDD-architecture.md and DeviaTDD-api.md

---

## [SEMANTIC_ANCHORS]
- `specs/constitution.md`
- `[CONSTITUTION_VERSION]`
- `[1_ARCHITECTURAL_PRINCIPLES]`
- `[2_TECH_STACK_STANDARDS]`
- `[2_1_BACKEND]`
- `[2_2_FRONTEND]`
- `[2_3_DATABASE]`
- `[2_4_INFRASTRUCTURE]`
- `[2_5_TOOLING]`
- `[3_TESTING_PROTOCOLS]`
- `[3_1_FRAMEWORK]`
- `[3_2_COVERAGE]`
- `[4_DEFINITION_OF_DONE]`
- `[5_VERSION_HISTORY]`
