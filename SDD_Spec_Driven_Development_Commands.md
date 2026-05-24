# SPEC-DRIVEN DEVELOPMENT (SDD) - COMPLETE COMMAND REFERENCE

## Overview

This document synthesizes ALL Spec-Driven Development commands and workflows. SDD is a comprehensive framework for orchestrating agent-driven development with TDD cycles, human-in-the-loop checkpoints, and spec-first methodology.

**Project**: This framework powers the RGR CLI (`/home/werner-wsl/Development/tools/rgr`) which orchestrates TDD cycles via agent subprocesses (Claude/Droid).

**Key Scripts Location**: `$HOME/.config/ai/spec/scripts/`

---

## TABLE OF CONTENTS

1. [Slash Command Reference](#slash-command-reference)
2. [Required Scripts](#required-scripts)
3. [Helper Scripts](#helper-scripts)
4. [Templates](#templates)
5. [Constitution Management](#specconstitution---project-constitution-maintenance)
6. [Core Specification](#speccorespecify---core-specification-engine)
7. [Technical Planning](#speccoreplan---technical-implementation-planning)
8. [Task Decomposition](#speccoretasks---task-decomposition)
9. [Context Synchronization](#speccorecontext---agent-context-synchronization)
10. [Triage Classification](#spectriage---rigor-classification)
11. [Cycle Router](#speccycle---intelligent-phase-router)
12. [Direct Execution](#specexecute---direct-task-execution)
13. [TDD Red Phase](#spectddred---red-phase)
14. [TDD Green Phase](#spectddgreen---green-phase)
15. [TDD Refactor Phase](#spectddrefactor---refactor-phase)
16. [TDD E2E Phase](#spectdde2e---e2e-testing)
17. [PRD Generation](#specfullprd---product-requirements-document)
18. [Phase Handover Flow](#phase-handover-flow)
19. [Constraints](#constraints)

---

## SLASH COMMAND REFERENCE

### Command Notation

SDD uses **colon notation** for all slash commands (e.g., `/spec:cycle`, `/spec:core:plan`). This aligns with Factory Droid's slash command registration pattern.

### Available Commands

| Command | Purpose |
|---------|---------|
| `/spec:constitution` | Initialize/update project constitution |
| `/spec:core:specify` | Define functional specification from issue |
| `/spec:core:plan` | Create technical implementation plan |
| `/spec:core:tasks` | Decompose plan into executable tasks |
| `/spec:core:context` | Sync context to agent files |
| `/spec:triage` | Classify workflow rigor level |
| `/spec:cycle` | Route to appropriate TDD phase |
| `/spec:execute` | Direct task execution (no TDD) |
| `/spec:tdd:red` | Red phase (write failing tests) |
| `/spec:tdd:green` | Green phase (implement to pass) |
| `/spec:tdd:refactor` | Refactor phase (cleanup) |
| `/spec:tdd:e2e` | End-to-end testing |
| `/spec:full:prd` | Generate product requirements doc |

### Aliases

| Alias | Expands To |
|-------|------------|
| `/c` | `/spec:cycle` |
| `/ca` | `/spec:cycle --auto` |
| `/x` | `/spec:execute` |
| `/xa` | `/spec:execute --auto` |
| `/xd` | `/spec:execute --dry-run` |

### Slash Command Registration

Factory Droid automatically discovers slash commands from:
1. `$HOME/.factory/commands/` - Custom command definitions
2. Built-in commands loaded from agent prompt templates

Commands are invoked by typing `/spec:` followed by the command name. The agent recognizes these patterns and routes to the appropriate handler.

---

## REQUIRED SCRIPTS

All required scripts MUST be located at `$HOME/.config/ai/spec/scripts/`. If any are missing, **STOP immediately** and report error.

### Core Scripts (Required)

| Script | Purpose |
|--------|---------|
| `get-spec-context.sh` | Resolve current spec context (branch, spec dir, worktree) |
| `assign-next-issue.sh` | Find and assign next available GitHub issue |
| `create-new-feature.sh` | Create feature branch with optional worktree |
| `manage-tasks.sh` | Manage task status in tasks.md |
| `get-test-config.sh` | Resolve test configuration from constitution |
| `sdd-parse-ast.sh` | Parse AST for symbol collection |

### get-spec-context.sh

```bash
# Usage
get-spec-context.sh [--json|--quiet|--strict]

# Output (KEY=VALUE format):
BRANCH_NAME="feature-auth"
FEATURE_SLUG="001-tdd-orchestrator"
SPEC_DIR="specs/001-tdd-orchestrator/045-native-context-gathering"
SPEC_DIR_EXISTS="true"
WORKTREE_ROOT="/home/user/project"
WORKTREE_DETECTED="true"
CONSTITUTION_EXISTS="true"
CONSTITUTION_TEST_COMMAND="uv run pytest"
PROJECT_TYPE="python"
BASE_BRANCH="main"
CHANGED_FILES="src/cli.py,tests/test_cli.py"
```

### assign-next-issue.sh

```bash
# Usage
assign-next-issue.sh [--dry-run|--assign-to <user>]

# Output for assigned issue:
ASSIGNED_ISSUE: 42
ASSIGNED_TO: username
ISSUE_URL: https://github.com/owner/repo/issues/42
ISSUE_TITLE: Implement feature X
```

### create-new-feature.sh

```bash
# Usage
create-new-feature.sh "feature description" [--create-worktree] [--feature-slug <slug>] [--issue-id <number>]

# Output:
BRANCH_NAME: 045-native-context-gathering
FEATURE_DESCRIPTION: Native context gathering
REPO_ROOT: /home/user/project
FEATURE_SLUG: 002-rust-tui-rgr-orchestrator
WORKTREE_PATH: .worktrees/045-native-context-gathering
SPECS_DIR: specs/002-rust-tui-rgr-orchestrator/045-native-context-gathering
```

### manage-tasks.sh

```bash
# Commands
manage-tasks.sh get-active [TASKS_FILE]   # Get first in-progress task
manage-tasks.sh get-next [TASKS_FILE]      # Get first pending task
manage-tasks.sh set-state <TASK_ID> <STATE> # Set task state (progress|done)
manage-tasks.sh get-phase-status <PHASE>   # Get phase completion status
manage-tasks.sh set-e2e-status <PHASE> <done|reset>  # Set E2E status
```

### get-test-config.sh

```bash
# Usage
get-test-config.sh [--json|--quiet]

# Output:
TEST_ROOT: tests
TEST_EXT: _test.py
TEST_COMMAND: uv run pytest -n auto
LINT_COMMAND: ruff check .
PROJECT_TYPE: python
```

### sdd-parse-ast.sh

```bash
# Usage
sdd-parse-ast.sh <file_path>

# Output (JSON):
{"file": "src/cli.py", "language": "python", "symbols": ["main", "cli", "parse_args"]}
```

---

## HELPER SCRIPTS

Additional scripts available at `$HOME/.config/ai/spec/scripts/`:

### git-commit.sh

Centralized git commit execution with safety checks.

```bash
# Commands
git-commit.sh --validate          # Check if repo is ready for commit
git-commit.sh --scan              # Scan staged files for sensitive patterns
git-commit.sh --commit "msg" file1...  # Stage and commit files
git-commit.sh --commit --no-verify "msg"  # Bypass hooks (for TDD Red phase)
git-commit.sh --context [--json]  # Output git context for AI

# Sensitive file patterns blocked:
# \.env$, \.pem$, \.p12$, \.npmrc$, id_rsa$, \.key$, etc.

# Output format (--context):
BRANCH_NAME: feature-auth
COMMIT_HASH: abc1234
IS_DIRTY: true
STAGED_FILES: src/cli.py,tests/test_cli.py
STAGED_COUNT: 2
SENSITIVE_FILES: none
SENSITIVE_COUNT: 0
CAN_COMMIT: true
```

**TDD Workflow Usage**: During Red phase when tests intentionally fail, use `--no-verify` to bypass pre-commit hooks:
```bash
git-commit.sh --commit --no-verify "test(T001): add failing tests"
```

### pr-review-threads.sh

Manage PR review threads.

```bash
# Commands
pr-review-threads.sh --unresolved     # Fetch all unresolved threads
pr-review-threads.sh --resolve 1      # Resolve thread ID 1
pr-review-threads.sh --resolve 1,2,3  # Resolve multiple threads

# Output for --unresolved:
THREAD_INDEX: 42
THREAD_ID: PRRT_kwDO...
AUTHOR: reviewer
PATH: src/cli.py
LINE: 123
---
BODY_START
Comment text here
BODY_END
```

### create_issues.sh

Batch create issues from a template.

```bash
# Usage documented in script help
create_issues.sh --help
```

---

## TEMPLATES

Template files are located at `$HOME/.config/ai/spec/templates/`:

| Template | Purpose |
|----------|---------|
| `spec-template.md` | Functional specification template |
| `plan-template.md` | Technical implementation plan template |
| `tasks-template.md` | Task decomposition template |
| `pr-template.md` | Pull request description template |
| `commit-template.md` | Commit message template |

### Template Usage

Templates are used automatically by the corresponding `/spec:*` commands:
- `/spec:core:specify` → uses `spec-template.md`
- `/spec:core:plan` → uses `plan-template.md`
- `/spec:core:tasks` → uses `tasks-template.md`

---

## [SPEC:CONSTITUTION] - Project Constitution Maintenance

### Purpose
Initialize or update `specs/constitution.md` as the authoritative governance artifact defining architectural standards, stack constraints, testing mandates, and completion criteria.

### Execution Sequence

**STEP 1 - Extract User Constraints**: Extract explicit Constraints, Demands, and Expectations from USER_INPUT.

**STEP 2 - Load Existing Constitution**: If `specs/constitution.md` exists, parse `[CONSTITUTION_VERSION]` and extract principles. If missing, initialize version as `0.1.0`.

**STEP 3 - Analyze Project State**: Scan project state sources (`package.json`, `mix.exs`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `terraform/`, CI configs) to detect:
- Frameworks
- Databases
- Infrastructure tooling
- Testing frameworks
- Deployment patterns

**STEP 4 - Resolve Governance Model**: Merge User_Derived_Principles, Existing_Constitution_State, and Detected_Project_Standards using precedence rules.

**STEP 5 - Determine Version Increment**:
- `[MAJOR]`: Removal or redefinition of governance principles
- `[MINOR]`: New section or materially expanded rule
- `[PATCH]`: Clarification, wording, or non-semantic refinement

**STEP 6 - Render Constitution**: Produce `specs/constitution.md` using the required template.

### Required Output Template

```markdown
# Project Constitution

[CONSTITUTION_VERSION]: X.Y.Z

---

## [1_ARCHITECTURAL_PRINCIPLES]
- Immutable governance rules

## [2_TECH_STACK_STANDARDS]
### [2_1_BACKEND]
### [2_2_FRONTEND]
### [2_3_DATABASE]
### [2_4_INFRASTRUCTURE]
### [2_5_TOOLING]

## [3_TESTING_PROTOCOLS]
### [3_1_FRAMEWORK]
- `TEST_FRAMEWORK`: <exunit|jest|pytest|...>
- `TEST_ROOT`: <test|tests>
- `TEST_EXT`: <_test.exs|.test.ts|...>
- `TEST_COMMAND`: <mix test|pytest|...>
- `LINT_COMMAND`: <mix credo|ruff check|...>

### [3_2_COVERAGE]
- Coverage thresholds

## [4_DEFINITION_OF_DONE]
- [ ] Code implemented
- [ ] Tests passing
- [ ] Coverage requirements met
- [ ] Documentation updated
- [ ] No governance violations

## [5_VERSION_HISTORY]
- X.Y.Z — Change description

## [SEMANTIC_ANCHORS]
- `CONSTITUTION_VERSION`
- Section identifiers: `[1_ARCHITECTURAL_PRINCIPLES]`, `[2_TECH_STACK_STANDARDS]`, etc.
- File paths, framework names, CLI commands
```

### Pre-requisites
- Required scripts at `$HOME/.config/ai/spec/scripts/`: `get-spec-context.sh`, `assign-next-issue.sh`, `create-new-feature.sh`
- If scripts NOT found, STOP immediately and report

### Edge Case Handling
- **EMPTY_USER_INPUT**: Use existing constitution and project state; if both absent, generate minimal defaults
- **MISSING_PROJECT_STATE**: Do not infer technologies; retain existing standards or defaults
- **MALFORMED_EXISTING_CONSTITUTION**: Preserve version if detectable; reconstruct from valid fragments; increment `[PATCH]`
- **CONFLICTING_CONSTRAINTS**: Apply `[SOURCE_PRECEDENCE_RULES]`
- **EXTREMELY_LONG_INPUT**: Process fully without truncation

---

## [SPEC:CORE:SPECIFY] - Core Specification Engine

### Purpose
Define the functional contract ("The What and Why") for a specific feature or fix. Produces a validated specification while preserving invariant anchors and excluding implementation logic.

### Pipeline
Resolve issue → Draft spec → Create branch + worktree → Write spec.md → Self-validate → HITL review → Commit → Hand off to `/spec:core:plan`

### Execution Sequence

**PHASE_0_PREFLIGHT**:
1. Run `$HOME/.config/ai/spec/scripts/get-spec-context.sh --quiet`
2. Evaluate conditions:
   - If `BRANCH_NAME` is "main", "master", or "HEAD" (detached)
   - OR if `WORKTREE_DETECTED` is "false"
3. If conditions true, STOP and present warning
4. Ask user to create feature branch with worktree

**PHASE_0_ISSUE_INTEGRATION**:
1. Run `$HOME/.config/ai/spec/scripts/get-spec-context.sh --quiet --strict`
2. Run `$HOME/.config/ai/spec/scripts/assign-next-issue.sh` if no explicit issue
3. Fetch issue content via `gh issue view <NUMBER> --json body,title`
4. Extract attachment URLs from issue body (GitHub-hosted attachments)
5. Extract FEATURE_SLUG from issue body (`**Feature_Slug**: <slug>` or `[Feature_Slug]: <slug>`)
6. Check for `coordinates_with` and confirm alignment

**PHASE_A_SPEC_DRAFTING**:
1. Extract Requirements: Identify user stories, acceptance criteria, success metrics
2. Define Intent: Formulate problem statement and functional goals
3. Validate Boundary: Ensure NO technical stack or implementation details
4. Detect Ambiguity: If > 5 ambiguities exist, pause and ask for clarification
5. Document Anti-Goals: Explicitly list what this feature does NOT include
6. Enumerate Project Structure: List ALL files that will be touched, with purpose
7. Create Traceability Matrix: Map each user story to its primary files

**PHASE_B_BRANCH_AND_ENVIRONMENT**:
1. Run `$HOME/.config/ai/spec/scripts/create-new-feature.sh` with `--create-worktree --feature-slug {FEATURE_SLUG} --issue-id {ISSUE_NUMBER}`
2. Read `specs/constitution.md` and check for functional conflicts
3. Confirm `{BRANCH_NAME}` and `{SPECS_DIR}` exist
4. Run `mise setup` to install tool versions
5. Download attachments to branch directory

**PHASE_C_VALIDATION_AND_COMMIT**:
1. Checklist Validation: Ensure all required `spec.md` sections present and non-technical
2. Stage and commit

### HITL_GATE_1_BLUEPRINT
After generating `spec.md`, present:
1. Blueprint Context: Summary of problem, stories, constraints
2. Anti-Goals: Explicitly list what we are NOT doing
3. Single Point of Failure: Critical data/API relationship
4. AskUser: 3-5 specific questions about boundaries and trade-offs

### Output Contract

Return structured Markdown with sections:
- `[PROBLEM_STATEMENT]`
- `[USER_STORIES]` with `[STORY_<ID>]`, Actor, Action, Outcome, `[Acceptance_Criteria]`
- `[SUCCESS_METRICS]` with `[METRIC_<ID>]`
- `[CONSTRAINTS]` with `[CONSTRAINT_<ID>]`
- `[RATIONALE]`
- `[ATTACHMENTS]`
- `[ANTI_GOALS]`
- `[PROJECT_STRUCTURE]` with file paths and purposes
- `[TRACEABILITY_MATRIX]` mapping stories to files

### Status Values
- `STATUS: SUCCESS`
- `STATUS: ISSUE_BLOCKED`
- `STATUS: NEEDS_CLARIFICATION`

---

## [SPEC:CORE:PLAN] - Technical Implementation Planning

### Purpose
Translate functional intent into a constitution-grounded technical implementation strategy. Produces research.md, data-model.md, API contracts, plan.md, and quickstart.md.

### Execution Sequence

**STEP_0_PREFLIGHT**: Same preflight checks as specify

**STEP_1_RESEARCH_AND_CONTEXT_INGESTION**:
1. Read `specs/constitution.md` for architectural patterns
2. Read `{SPEC_DIR}/spec.md` for functional requirements
3. Run AST parser to collect existing function/interface definitions:
   ```bash
   mkdir -p {SPEC_DIR}/.ast_inventory
   git diff --name-only "$BASE_COMMIT" HEAD -- '*.py' '*.ex' '*.exs' '*.js' '*.jsx' '*.ts' '*.tsx' '*.rs' '*.cpp' '*.cc' '*.cs' 2>/dev/null | while read -r file; do
     if [ -f "$file" ]; then
       "$HOME/.config/ai/spec/scripts/sdd-parse-ast.sh" "$file" >> "{SPEC_DIR}/.ast_inventory/$(basename "$file").json" 2>/dev/null || true
     fi
   done
   ```
4. Search codebase for existing patterns and reusable components
5. Perform investigative research for third-party libraries or external APIs
6. Record findings in `{SPEC_DIR}/research.md`

**STEP_2_DATA_MODEL_DESIGN**:
1. Define all new or modified data structures, schemas, database migrations
2. Identify relationships between entities
3. Document in `{SPEC_DIR}/data-model.md`

**STEP_3_CONTRACT_SPECIFICATION**:
1. If feature involves APIs (REST, GraphQL, Internal), define contracts
2. Create or update files in `/contracts/` directory
3. Ensure contracts are language-agnostic or strictly typed if stack requires

**STEP_4_IMPLEMENTATION_STRATEGY**:
1. Break down feature into sequential, logical **Phases**
2. For each phase, define:
   - **Phase_ID**: `Phase_1`, `Phase_2`, etc.
   - **Goal**: High-level objective
   - **Execution_Mode**: `TDD` or `IMMEDIATE`
   - **Workstation_Context**: Files that share logical capability
   - **Files_Touched**: Project-relative paths to be created or modified
   - **Verification**: Deterministic command to prove completion
   - **Phase_Dependency**: (Optional) Which phase must complete first

**STEP_4B_TRACEABILITY_ENFORCEMENT**:
1. Read spec.md PROJECT_STRUCTURE section and extract all files
2. Cross-reference against PHASES Files_Touched:
   - Every file in `[PROJECT_STRUCTURE]` MUST appear in at least one phase
   - Every file in `[Files_Touched]` MUST appear in `[PROJECT_STRUCTURE]`
3. Read spec.md TRACEABILITY_MATRIX and verify story-file distribution
4. Phase_Goal to Files_Touched alignment: Every noun in `[Phase_Goal]` must be a file in that phase's `[Files_Touched]`
5. Anti-Goals boundary check: Verify no anti-goal files appear in any phase

**STEP_5_ARTIFACT_GENERATION**:
1. Create `{SPEC_DIR}/plan.md` using project template
2. Populate plan with results from previous steps
3. Create or update `quickstart.md` if feature requires setup changes

**STEP_6_TASK_INITIALIZATION**: Inform user to run `/spec:core:tasks` next

---

## [SPEC:CORE:TASKS] - Task Decomposition

### Purpose
Decompose approved technical plan into **Autonomous R-G-R Units** (Vertical Tasks, 30-90 min). Each task is a deterministic instruction for an agent to perform a complete Red-Green-Refactor cycle.

### R-G-R Mandate
- **Red**: Every task starts by writing a failing test (Sociable/Integration)
- **Green**: Implement minimum code to pass the test
- **Refactor**: Clean up code to match idioms and `specs/constitution.md`
- **Verification-is-Done**: A task is ONLY done when its `Verification` command passes

### Granularity Rules

**1. "Slice over Step" Rule**:
- ❌ **Reject (Atomic)**: "Update DB schema", "Add field to DTO"
- ✅ **Accept (Slice)**: "Extend 'User Profile' model and DTO with 'Social Links' (Schema, Types, Validation)"

**2. "30-90 Minute" Rule**:
- If task takes < 30 min → **Merge** with neighbor in dependency chain
- If task takes > 90 min → **Split** only if split maintains verticality

**3. "Ambiguity Resolution" Rule**:
- Create separate tasks per capability
- Add explicit `Dependency` field to downstream tasks

### Task Structure Constraints

Every task MUST contain:
- **Task_ID**: `T{NNN}` (zero-padded, sequential)
- **Task_Type**: `Feature_Batch | Infra_Batch | Domain_Batch | Bugfix | Migration | Config`
- **Execution_Mode**: `TDD | IMMEDIATE` (default: `TDD`)
- **Test_Strategy**: `Sociable_Unit | Integration | Solitary_Unit` (required if Execution_Mode is TDD)
- **Description**: High-density objective
- **Verification**: Deterministic CLI Command
- **Estimated_Time**: 30-90 minutes
- **Files_Touched**: List of absolute or project-relative paths (minimum 2 files)
- **Task_Details**: 4-8 detailed bullet points with explicit R-G-R breakdown:
  - **[RED]**: Specific test file, test cases, assertions
  - **[GREEN]**: Exact functions/methods to implement, signatures, logic
  - **[REFACTOR]**: Code quality improvements, pattern alignment
  - **[EDGE_CASES]**: Error handling, boundary conditions
  - **[ACCEPTANCE]**: Concrete "done" criteria beyond test passing
- **Dependency**: (Optional) `T{NNN}` if requires another task
- **Risk_Level**: (Optional) `none | low | medium | high`
- **Effort**: (Optional) `S | M | L`

### Output Formats

**JSON Output** (`tasks.json`):
```json
[
  {
    "id": "T001",
    "description": "Implement JWT token service with RS256 signing",
    "status": "PENDING",
    "risk_level": "medium",
    "effort": "M",
    "execution_mode": "TDD",
    "tdd_required": true
  }
]
```

**Markdown Output** (`tasks.md`):
```markdown
# Implementation Tasks: {BRANCH_NAME}

## [PHASE_1]: <Feature Slice Name>
[Phase_Goal]: <capability delivered>

### [TASKS]
- [ ] [T001] <Description>
  - [Task_Type]: Feature_Batch
  - [Execution_Mode]: TDD
  - [Test_Strategy]: Sociable_Unit
  - [Verification]: <command>
  - [Estimated_Time]: 60 minutes
  - [Risk_Level]: medium
  - [Effort]: M
  - [Files_Touched]:
    - path/to/file1.ts
    - path/to/file2.ts
  - [Task_Details]:
    - [RED] Write failing test: `<test_name>()` with assertion...
    - [GREEN] Implement `<function_name>(<params>): <return_type>`...
```

---

## [SPEC:CORE:CONTEXT] - Agent Context Synchronization

### Purpose
Synchronize technical execution context from `{SPEC_DIR}/plan.md` into `CLAUDE.md`, `AGENTS.md`, and `.github/agents/copilot-instructions.md` for agent-wide consistency.

### Execution Sequence

**STEP_0_CONTEXT_HANDOFF_CHECK**: Look for handoff from `/spec:core:plan` in conversation history

**STEP_1_ENVIRONMENT_RESOLUTION**: Execute `$HOME/.config/ai/spec/scripts/get-spec-context.sh --quiet --strict`

**STEP_1B_PARSE_AND_VALIDATE_CONTEXT**:
1. Extract structured fields from `{SPEC_DIR}/plan.md`
2. Apply USER_INPUT overrides if provided
3. Merge with constitution (plan.md values highest, constitution fills gaps)
4. Validate against merged constraints

**STEP_1C_MULTILINGUAL_DETECTION**: Detect if project is multi-lingual/monorepo:
- If DETECTED_LANGS contains 2+ languages → `MULTILANG_MODE=append`
- If DETECTED_LANGS contains 1 language → `MULTILANG_MODE=replace`

**STEP_2_GENERATE_CANONICAL_BLOCK**:
```markdown
## Technical Execution Context

[Language]: <value>
[Dependencies]: <value_1>, <value_2>
[Storage]: <value>
[Testing]: <value>
[Target_Platform]: <value>
[Project_Type]: <value>
[Performance_Goals]: <value>
[Constraints]: <value>
[Scale]: <value>
[Build]: <value>
[Test]: <value>
[Lint]: <value>
[Runtime]: <value>
[Structure]: <value>
```

**STEP_3_TARGET_FILE_DISCOVERY**: Process files in deterministic order:
- `CLAUDE.md`
- `AGENTS.md` (symlink to CLAUDE.md)
- `.github/agents/copilot-instructions.md`

**STEP_4_BLOCK_REPLACEMENT_ALGORITHM**:
- Detect existing block by exact header match: `## Technical Execution Context`
- Block boundaries: Start at header, end at next `##` or EOF
- Cases: Single match → Replace; No match → Append at EOF; Multiple matches → CONTEXT_WRITE_FAILURE

---

## [SPEC:TRIAGE] - Rigor Classification

### Purpose
Analyze USER_INPUT and PROJECT_CONTEXT to determine minimum rigor workflow classification: `FULL | CORE | TDD | NONE`.

### Decision Predicates

- **A1_MULTI_SYSTEM_IMPACT**: TRUE if change affects multiple bounded contexts, subsystems, or integration points
- **A2_NEW_INFRASTRUCTURE**: TRUE if change requires new infrastructure, environment changes, database migrations, or external integrations
- **A3_ARCHITECTURAL_AMBIGUITY**: TRUE if functional or technical ambiguity prevents immediate implementation
- **A4_PRODUCTION_RISK**: TRUE if change impacts production-critical paths
- **A5_LOCALIZED_LOGIC**: TRUE if change is confined to a single function/module with clearly defined inputs/outputs
- **A6_TRIVIAL_SCOPE**: TRUE if task is CRUD, formatting, documentation tweak, or simple script with near-zero misinterpretation risk

### Classification Rules (Priority Order)

1. IF A1_MULTI_SYSTEM_IMPACT = TRUE OR A2_NEW_INFRASTRUCTURE = TRUE → **CLASSIFICATION = "FULL"**

2. ELSE IF A4_PRODUCTION_RISK = TRUE OR A3_ARCHITECTURAL_AMBIGUITY = TRUE → **CLASSIFICATION = "CORE"**

3. ELSE IF A5_LOCALIZED_LOGIC = TRUE AND A3_ARCHITECTURAL_AMBIGUITY = FALSE → **CLASSIFICATION = "TDD"**

4. ELSE IF A6_TRIVIAL_SCOPE = TRUE → **CLASSIFICATION = "NONE"**

5. ELSE → **CLASSIFICATION = "CORE"**

### Output Contract (JSON only)

```json
{
  "[CLASSIFICATION]": "FULL | CORE | TDD | NONE",
  "[JUSTIFICATION]": "1–2 sentence rationale grounded in decision predicates",
  "[SIGNALS]": {
    "[A1_MULTI_SYSTEM_IMPACT]": true | false,
    "[A2_NEW_INFRASTRUCTURE]": true | false,
    "[A3_ARCHITECTURAL_AMBIGUITY]": true | false,
    "[A4_PRODUCTION_RISK]": true | false,
    "[A5_LOCALIZED_LOGIC]": true | false,
    "[A6_TRIVIAL_SCOPE]": true | false
  },
  "[CONSTITUTIONAL_CONSTRAINTS_DETECTED]": [],
  "[MISSING_INPUTS]": [],
  "[SEMANTIC_ANCHORS]": {
    "[CONSTITUTION_PATH]": "specs/constitution.md",
    "[DECISION_PREDICATES]": ["A1", "A2", "A3", "A4", "A5", "A6"],
    "[CLASSIFICATION_VALUES]": ["FULL", "CORE", "TDD", "NONE"]
  }
}
```

---

## [SPEC:CYCLE] - Intelligent Phase Router

### Purpose
Determine current workflow state and route to appropriate next phase: Direct execution, TDD Red, TDD Green, or TDD Refactor.

### Routing Logic

**STEP_1_CHECK_EXPLICIT_HANDOVER**: Parse USER_INPUT for `[HANDOVER_MANIFEST]` YAML block

**STEP_2_CHECK_CONVERSATION_HISTORY**: Scan for previous phase output with `[HANDOVER_MANIFEST]`

**STEP_3_CHECK_TASK_STATUS**: Query task management:
```bash
$HOME/.config/ai/spec/scripts/manage-tasks.sh get-active
```

**STEP_4_ROUTE_BY_PHASE**:

| Previous Phase | Route To | Rationale |
|---------------|----------|-----------|
| `RED` | `/spec:tdd:green` | Tests written, implement code |
| `GREEN` | `/spec:tdd:refactor` | Tests pass, clean up code |
| `REFACTOR` | Check E2E status | Task complete, check E2E |
| `DIRECT` | Check E2E status | Direct execution complete |
| None (new task) | Check complexity | Determine execution mode |

**STEP_5_COMPLEXITY_CHECK**:

| Complexity Score | Execution Mode | Route To |
|------------------|----------------|----------|
| ≤ 3 | DIRECT | `/spec:execute` |
| > 3 | TDD | `/spec:tdd:red` |

**Complexity Factors**:
- Files to touch: +1 to +3
- Dependencies: +0 to +2
- API/DB changes: +2
- Security related: +2
- Tests exist: -1
- Trivial task type: -2

### Output Contract

```markdown
# Cycle: Routing Decision

## [STATE_ANALYSIS]
```yaml
handover_source: {explicit|conversation|task_status|none}
previous_phase: {RED|GREEN|REFACTOR|DIRECT|null}
task_id: {TASK_ID}
task_status: {in_progress|pending|complete}
complexity_score: {SCORE}
```

## [ROUTING_DECISION]
[Target]: {/spec:execute|/spec:tdd:red|/spec:tdd:green|/spec:tdd:refactor|/spec:tdd:e2e}
[Reason]: {REASONING}

## [NEXT_ACTION]
Execute: `{COMMAND}`
```

### Continuous Mode (`--auto`)

```
┌─────────────────────────────────────┐
│         /spec:cycle --auto          │
└─────────────────┬───────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Route to Phase │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Execute Phase  │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Phase Complete │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ More Tasks?    │
         └────────┬───────┘
                  │
         ┌────────┴────────┐
        YES               NO
         │                 │
         ▼                 ▼
    ┌─────────┐      ┌───────────┐
    │ Cycle   │      │  Report   │
    │ Again   │      │  Complete │
    └─────────┘      └───────────┘
```

---

## [SPEC:EXECUTE] - Direct Task Execution

### Purpose
Execute a task directly without TDD cycle. Use for:
- Low complexity tasks (complexity ≤ 3)
- Trivial changes (typos, comments, config)
- Documentation updates
- Simple refactors with existing test coverage

### Pre-requisites
- Required scripts at `$HOME/.config/ai/spec/scripts/`: `get-spec-context.sh`, `manage-tasks.sh`
- For TDD tasks, use `/spec:cycle` instead

### Execution Sequence

**STEP_0_FLAG_PARSING**:
| Flag | Variable | Effect |
|------|----------|--------|
| `--auto` | `CONTINUOUS_MODE=true` | After task completion, start next task |
| `--dry-run` | `DRY_RUN=true` | Display execution plan without modifying |
| `<TASK_ID>` | `EXPLICIT_TASK={TASK_ID}` | Execute specific task |

**STEP_1_WORKFLOW_DISCOVERY**:
```bash
# Priority 1: Spec mode (worktree with specs/)
# Priority 2: TM mode (.task-master exists)
# Priority 3: Plan mode (thoughts/plans exists)
```

**STEP_2_TASK_DISCOVERY**:
- Use explicit task if provided
- First check for in-progress task via `manage-tasks.sh get-active`
- Else get next via `manage-tasks.sh get-next`

**STEP_3_DIRECT_IMPLEMENTATION**:
1. Load task details from `{SPEC_DIR}/tasks.md`
2. Implement changes directly
3. Run quick validation
4. If validation passes → Proceed to STEP_4_AUTO_COMMIT

**STEP_4_AUTO_COMMIT** (MANDATORY):
1. Mark task complete in `{SPEC_DIR}/tasks.md`
2. Stage files: `git add -u`, then `git add {SPEC_DIR}/*.md specs/`
3. Run precommit hooks and verify no files change
4. Update .gitignore if needed
5. Commit with message:
   ```
   feat({TASK_ID}): {TASK_TITLE}
   
   Mode: DIRECT
   - Implemented changes directly without TDD cycle
   - Validation passed
   ```

### Output Contract (NO PROSE - structured manifest only)

```markdown
# Execute: {TASK_ID}

Status: COMPLETE
Mode: DIRECT
Workflow: {WORKFLOW}

## [EXECUTION_MANIFEST]
```yaml
execution_id: {TIMESTAMP}
task_id: {TASK_ID}
task_title: {TASK_TITLE}
workflow: {WORKFLOW}
spec_dir: {SPEC_DIR}
execution_mode: DIRECT
files_modified:
  - path: {FILE_PATH}
    action: created|modified
    purpose: {PURPOSE}
validation:
  lint: {PASS|FAIL|SKIP}
  typecheck: {PASS|FAIL|SKIP}
  tests: {PASS|FAIL|SKIP}
  command: "{VALIDATION_COMMAND}"
time_elapsed: "{DURATION}"
reasoning:
  approach: "{APPROACH_SUMMARY}"
  key_decisions:
    - decision: "{DECISION_1}"
      rationale: "{RATIONALE}"
commit:
  sha: "{COMMIT_SHA}"
  message: "feat({TASK_ID}): {TASK_TITLE}"
next_action: {CONTINUE | WAIT_FOR_USER}
```
```

---

## [SPEC:TDD:RED] - Red Phase

### Purpose
Execute the Red phase of the TDD cycle by generating failing automated tests that define the Source of Truth for `{TASK_ID}`.

### R-G-R Execution Model
Each task (30-90 min) undergoes ONE complete R-G-R cycle:
- Select ONE task → Red (write failing test) → Green → Refactor → Mark task complete → Select next task

### Mocking Guidelines

**When NOT to Use Mocks**:
1. Internal Sibling Functions/Classes: Never mock a function within your application boundary
2. Domain Logic & Pure Functions: Math, parsing, data transformation
3. Data Transfer Objects (DTOs) & Models: Never mock data structures
4. The ORM or Database Client: Use in-memory or containerized databases

**When TO Use Mocks**:
1. Third-Party APIs: Payment gateways, email providers, external microservices
2. Non-Deterministic Outputs: System time, randomness
3. Destructive/Expensive Operations: Code that wipes a server, charges credit card

### Input Handling

**Task Inference Rule**:
1. First check for in-progress tasks via `$HOME/.config/ai/spec/scripts/manage-tasks.sh get-active`
2. If no in-progress, get next via `$HOME/.config/ai/spec/scripts/manage-tasks.sh get-next`
3. NEVER ask user which task to run

**NO_TASKS_REMAINING**: If both scripts return empty:
```markdown
# TDD Red Phase: Cycle Complete

## [STATUS]
[Value]: NO_TASKS_REMAINING

## [PHASE_COMPLETION]
[Message]: All tasks in `tasks.md` are marked as complete.
```

### Execution Sequence

**STEP_0_CONTEXT_FROM_CONVERSATION**: Extract active task from conversation history

**STEP_1_TASK_ISOLATION**:
1. Use `{TASK_ID}` to extract task description from `tasks.md`
2. Map to corresponding architectural requirement in `spec.md`
3. Identify all dependencies (DTOs, Services, Models)

**STEP_2_TEST_GENERATION**:
1. Create/Update Test File following project naming conventions
2. Write Failing Test Case:
   - **Arrange**: Initialize real objects (DTOs/Models)
   - **Act**: Invoke the primary function/method
   - **Assert**: Define expected outcome
3. Ensure Failure: Test MUST fail because implementation does not exist

**STEP_5_UPDATE_TASK_STATUS**:
```bash
$HOME/.config/ai/spec/scripts/manage-tasks.sh set-state {TASK_ID} progress
```

**STEP_7_AUTO_COMMIT** (MANDATORY):
1. Run verification command to ensure tests fail
2. Stage all relevant files
3. Run precommit hooks
4. Commit with message:
   ```
   test({TASK_ID}): add failing tests
   
   Phase: RED
   - Generated failing test cases
   - Tests define expected behavior (Source of Truth)
   - Implementation pending (Green phase)
   ```

### Output Contract (NO PROSE - structured manifest only)

```markdown
# TDD Red: {TASK_ID}

Status: TEST_WRITTEN (failing)
Test: `path/to/test_file.ext`

## [HANDOVER_MANIFEST]
```yaml
phase: RED
task_id: {TASK_ID}
spec_dir: {SPEC_DIR}
files:
  - path: path/to/test_file.ext
    action: created|modified
    purpose: Test file for {TASK_ID}
test:
  command: "{VERIFICATION_COMMAND}"
  status: FAIL
  expected_error: "{EXACT_ERROR_MESSAGE}"
  assertions:
    - "{ASSERTION_1}"
    - "{ASSERTION_2}"
  setup:
    - "{SETUP_STEP_1}"
constraints:
  - "{CONSTRAINT_1}"
  - "{CONSTRAINT_2}"
reasoning:
  approach: "{TEST_STRATEGY}"
  key_decisions:
    - decision: "{DECISION_1}"
      rationale: "{WHY_THIS_TEST_STRUCTURE}"
  edge_cases_covered:
    - "{EDGE_CASE_1}"
dependencies:
  - "{DTO/MODEL/SERVICE_REQUIRED}"
commit:
  sha: "{COMMIT_SHA}"
  message: "test({TASK_ID}): add failing tests"
previous_phase: red
next_phase: /spec:tdd:green
```
```

---

## [SPEC:TDD:GREEN] - Green Phase

### Purpose
Execute the Green phase by implementing minimal code to make tests pass. Handles TWO scenarios:
1. **Implementation gaps**: Implement minimal code to satisfy correct test expectations
2. **Test faults**: Fix tests that contain errors (typos, wrong function calls, incorrect assertions)

### IT IS OKAY TO MODIFY TESTS when:
- Test calls function that doesn't match implementation's actual API
- Test expects function name/signature that differs from data-model or contracts
- Test has typos in function names, variable names, or assertions
- Test uses incorrect mock setup that doesn't align with contract
- Test asserts on wrong output structure compared to data-model
- Test setup is fundamentally flawed

### Pre-requisites
- Required scripts at `$HOME/.config/ai/spec/scripts/`: `get-spec-context.sh`, `manage-tasks.sh`

### Execution Sequence

**STEP_0_CONTEXT_FROM_CONVERSATION**: Extract `{TASK_ID}` and `{VERIFICATION_COMMAND}` from previous `/spec:tdd:red` output

**STEP_1_FALLBACK_CONTEXT** (if handover fails):
1. Run `$HOME/.config/ai/spec/scripts/get-spec-context.sh --quiet --strict`
2. Run `$HOME/.config/ai/spec/scripts/manage-tasks.sh get-active` to find in-progress task
3. Set `Source: Fallback`

**STEP_2_CONTRACT_LOADING** (ALWAYS executed):
1. Read `specs/constitution.md`
2. Read `{SPEC_DIR}/prd.md`
3. Read `{SPEC_DIR}/spec.md`
4. Read `{SPEC_DIR}/data-model.md`
5. Read any relevant contracts in `/contracts/` or `{SPEC_DIR}/contracts/`

**STEP_3_IMPLEMENT_FROM_HANDOVER**:
1. Read the test file to understand exact expectations
2. Implement minimal code to satisfy `test.assertions`
3. Respect all constraints from `constraints` list
4. Use dependencies listed in `dependencies` if needed

**Implementation Rules**:
- Write ONLY code required to satisfy test assertions
- Do NOT run tests during this step
- If test has syntax errors (Test Fault), fix them in the test file

**STEP_4_VERIFY_GREEN_STATE**:
```bash
{VERIFICATION_COMMAND}
```
Expected: All tests pass

**STEP_5_UPDATE_TASK_STATUS**:
```bash
$HOME/.config/ai/spec/scripts/manage-tasks.sh set-state {TASK_ID} progress
```

**STEP_6_AUTO_COMMIT** (MANDATORY):
1. Run verification command
2. Stage all files (including `tasks.md` explicitly after manage-tasks.sh modified it)
3. Run precommit hooks
4. Commit with message:
   ```
   feat({TASK_ID}): implement feature
   
   Phase: GREEN
   - Implemented minimal code to pass all tests
   - Test assertions satisfied
   - Ready for refactoring
   ```

### Task Modification Rules
If uncovering unexpected dependencies or requirements:
- Append new items to bottom of task list: `- [ ] T<ID>: <Description>`
- **Strictly prohibited**: Rewriting, deleting, or altering existing tasks
- If requirement introduces deep architectural changes → flag blocked and STOP

### Output Contract (NO PROSE)

```markdown
# TDD Green: {TASK_ID}

Status: IMPLEMENTATION_COMPLETE (tests pass)
Scenario: [Implementation Gap | Test Fault | Both]

## [HANDOVER_MANIFEST]
```yaml
phase: GREEN
task_id: {TASK_ID}
spec_dir: {SPEC_DIR}
files:
  - path: path/to/source_file.ext
    action: created|modified
    purpose: {PURPOSE}
  - path: path/to/test_file.ext
    action: modified|unchanged
    purpose: {PURPOSE_IF_MODIFIED}
test:
  command: "{VERIFICATION_COMMAND}"
  status: PASS
  assertions:
    - "{ASSERTION_1}"
    - "{ASSERTION_2}"
  output: "{TRUNCATED_TEST_OUTPUT}"
constraints_inherited:
  - "{CONSTRAINT_FROM_RED}"
constraints_new:
  - "{NEW_CONSTRAINT_DISCOVERED}"
reasoning:
  approach: "{APPROACH_SUMMARY}"
  key_decisions:
    - decision: "{DECISION_1}"
      rationale: "{WHY_THIS_APPROACH}"
  alternatives_considered:
    - "{ALTERNATIVE_1}: {WHY_REJECTED}"
technical_debt:
  - "{DEBT_1}"
commit:
  sha: "{COMMIT_SHA}"
  message: "feat({TASK_ID}): implement feature"
previous_phase: /spec:tdd:red
next_phase: /spec:tdd:refactor
```
```

---

## [SPEC:TDD:REFACTOR] - Refactor Phase

### Purpose
Execute the Refactor phase while preserving externally observable behavior. Ensure structural improvement, architectural alignment, and test invariance.

### Pre-requisites
- Required script at `$HOME/.config/ai/spec/scripts/`: `get-spec-context.sh`
- **Tests Passing**: All tests for `{TASK_ID}` MUST be passing (Green state confirmed)

### Refactor Strategy

**STEP_1_IDENTIFY_CODE_SMELLS**:
- **Duplication**: Repeated logic or data structures
- **Complexity**: Deep nesting, large functions (>30 lines), high cyclomatic complexity
- **Contract Violations**: Deviations from data-model.md or constitution.md
- **Naming**: Obscure or inconsistent naming
- **Coupling**: Unnecessary dependencies or tight coupling to internals

**STEP_2_APPLY_REFACTORING_PATTERNS**:
- **Extract Function/Method**: Breakdown large logical blocks
- **Rename Variable/Function**: Improve semantic clarity
- **Move Function/Logic**: Align with functional core/imperative shell or Repo pattern
- **Replace Conditional with Polymorphism**: (If appropriate)
- **Consolidate Duplicate Fragments**: Centralize shared logic

### Quality Indicators
1. **Behavior Invariance**: All existing tests pass without modification
2. **Readability**: Code intent is clear without comments
3. **SNR Maximization**: Low filler, high logical density
4. **Architectural Fidelity**: Matches project's established patterns

### Execution Sequence

**STEP_0_CONTEXT_FROM_CONVERSATION**: Extract from `/spec:tdd:green` output

**STEP_2_CONTRACT_LOADING** (ALWAYS):
1. Read `specs/constitution.md`
2. Read `{SPEC_DIR}/spec.md`
3. Read `{SPEC_DIR}/data-model.md`

**STEP_3_ANALYZE_GREEN_IMPLEMENTATION**:
1. Cross-reference `technical_debt` from manifest with code
2. Identify additional smells not captured in debt list
3. Prioritize refactoring based on architectural impact

**STEP_4_EXECUTE_REFACTOR**:
- You may modify application code, but MUST NOT modify tests
- If a test fails after refactor, refactor has introduced a regression

**STEP_5_VERIFY_INVARIANCE**:
```bash
{VERIFICATION_COMMAND}
```

**STEP_6_MARK_TASK_COMPLETE**:
```bash
$HOME/.config/ai/spec/scripts/manage-tasks.sh set-state {TASK_ID} done
```

**STEP_7_AUTO_COMMIT** (MANDATORY):
1. Run verification command
2. Stage all files (including `tasks.md` explicitly)
3. Run precommit hooks
4. Commit with message:
   ```
   refactor({TASK_ID}): improve structure
   
   Phase: REFACTOR
   - Applied structural improvements while preserving behavior
   - All tests pass (behavior invariance verified)
   - Task marked complete in tasks.md
   ```

### Output Contract (NO PROSE)

```markdown
# TDD Refactor: {TASK_ID}

Status: TASK_COMPLETE
Task: {TASK_ID} marked `[x]` in tasks.md

## [HANDOVER_MANIFEST]
```yaml
phase: REFACTOR
task_id: {TASK_ID}
spec_dir: {SPEC_DIR}
task_status: COMPLETE
files:
  - path: path/to/source_file.ext
    action: modified
    purpose: {REFACTOR_PURPOSE}
refactoring:
  smells_addressed:
    - "{SMELL_1}"
    - "{SMELL_2}"
  patterns_applied:
    - "{PATTERN_1}"
    - "{PATTERN_2}"
test:
  command: "{VERIFICATION_COMMAND}"
  status: PASS
  output: "{TRUNCATED_TEST_OUTPUT}"
constraints_preserved:
  - "{ALL_CONSTRAINTS_MAINTAINED}"
reasoning:
  approach: "{REFACTORING_APPROACH}"
  key_decisions:
    - decision: "{DECISION_1}"
      rationale: "{WHY_THIS_PATTERN}"
artifacts:
  - "{FUNCTIONS_ADDED_OR_MODIFIED}"
commit:
  sha: "{COMMIT_SHA}"
  message: "refactor({TASK_ID}): improve structure"
previous_phase: /spec:tdd:green
next_phase: /spec:cycle  # Route back to cycle for next task
```
```

---

## [SPEC:TDD:E2E] - End-to-End Testing

### Purpose
Execute end-to-end (E2E) testing after ALL phases complete to verify the feature meets user intent.

### E2E vs Integration Distinction
- **Integration**: Tests how several internal components interact. May use in-memory DBs or virtualized file systems. Focuses on **Internal Contracts**
- **E2E**: Tests the *entire* system as a "Black Box" from user's perspective. Uses production-like environment. Focuses on **User Intent**

### E2E Strategy by Project Type

**CLI Projects**:
- Exit Code Rigor: Assert specific exit codes (0 for success, 1 for validation error, 127 for command not found)
- Stream Capture: Verify stdout/stderr
- Black Box Binaries: Mock external tools by placing "fake" versions in temporary PATH
- Golden File Testing: Compare complex outputs against "reference" files

**Web Projects**:
- High-Value Happy Paths: Focus on "Money Maker" paths
- Critical Failure Paths: Test catastrophically wrong scenarios
- Environment Isolation: Use isolated temporary directories, dedicated test databases
- Stable Selectors: Use `data-testid` instead of CSS classes

**API Projects**:
- HTTP Workflows: Full request/response cycles
- Auth Flows: Login, token refresh
- External APIs: Real third-party calls

### Execution Sequence

**STEP_1_CONTEXT_LOADING**:
```bash
$HOME/.config/ai/spec/scripts/get-spec-context.sh --quiet --strict
```

**STEP_1A_FETCH_GIT_DIFF**:
```bash
BASE_BRANCH=$(git branch --list main >/dev/null 2>&1 && echo "main" || echo "master")
GIT_DIFF=$(git diff $BASE_BRANCH...HEAD --stat 2>/dev/null)
CHANGED_FILES=$(git diff $BASE_BRANCH...HEAD --name-only 2>/dev/null)
```

**STEP_1B_DETECT_PROJECT_TYPE**:
| Project Type | E2E Approach |
|--------------|--------------|
| CLI | Shell subprocess, BATS tests |
| Web | Playwright/Cypress browser automation |
| API | HTTP client workflows, contract tests |
| Library | Skip E2E |

**STEP_2_ALL_PHASES_COMPLETION_VERIFICATION**: Verify all phases have all tasks complete `[x]`

**STEP_3_EXTRACT_INTEGRATION_POINTS**: Extract from `{SPEC_DIR}/plan.md` and `{SPEC_DIR}/data-model.md`:
- Service Boundaries
- Data Flows
- External APIs
- Database Operations
- API Endpoints

**STEP_3A_RESOLVE_E2E_TEST_CONFIG**:
```bash
$HOME/.config/ai/spec/scripts/get-test-config.sh
```

**STEP_3C_ANALYZE_TASKS_FOR_E2E**: Parse tasks.md for:
- Tasks requiring E2E tests (explicit markers)
- User workflow tasks requiring E2E coverage
- Phase identifiers and task descriptions

**STEP_3D_ANALYZE_CHANGES_FOR_E2E_UPDATES**: Compare changed files against existing E2E test files

**STEP_5_CHECK_EXISTING_AND_GENERATE**:
- For E2E tests requiring updates: Update test assertions, inputs, expected outputs
- For new E2E tests: Create new file with appropriate format

**STEP_6_VERIFY_UNIT_TESTS_STILL_PASS**: Execute unit test command from constitution

**STEP_7_VERIFY_PRECONDITIONS**:
- Unit Tests: Must pass
- Integration Tests: Should have been run in `/spec:tdd:integration` phase
- E2E Tooling: Check availability based on `{E2E_STRATEGY}`

**STEP_8_EXECUTE_E2E_TESTS**: Execute based on E2E_STRATEGY

**STEP_9_VALIDATION_AND_COMMIT**: If tests pass, commit with message:
```
test({PHASE_ID}): add/update E2E tests
```

### Output Contract

```markdown
# E2E Testing Report: {PHASE_ID}

## [PHASE_ID]
[Value]: <phase_id>
[Branch]: {BRANCH_NAME}
[Project_Type]: <CLI|Web|API|Library>
[E2E_Strategy]: <CLI|Web|API|Skip>

## [PHASE_COMPLETION_STATUS]
[Total_Tasks]: <count>
[Completed_Tasks]: <count>
[E2E_Run]: YES|NO

## [CHANGES_ANALYSIS]
[Base_Branch]: <main|master>
[Changed_Files]: <count>
[Files_Requiring_E2E_Update]: <count>

## [E2E_TEST_COVERAGE]
### [CLI_Coverage] (if applicable)
- Command execution: YES|NO
- stdin/stdout/stderr: YES|NO
- Exit codes: YES|NO
- File system operations: YES|NO
- Environment variables: YES|NO

## [TEST_MATRIX]
| Test ID | Category | Scope | Status | Type |
|---------|----------|-------|--------|------|
| [E2E_<ID>] | CLI/Web/API | <scope> | PASS|FAIL | NEW|UPDATE |

## [E2E_TESTS_REQUIRING_UPDATES]
| Test File | Changed Source | Update Reason |
|-----------|---------------|---------------|
| <test_path> | <source_file> | <reason> |

## [GENERATED_TEST_FILES]
### [TEST_FILE_<N>]
[Path]: <path>
[Type]: CLI E2E | Web E2E | API E2E
[Action]: CREATED | UPDATED
[Coverage]: <e2e_categories_covered>

## [EXECUTION_RESULTS]
[Unit_Tests]: PASS | FAIL
[E2E_Tests]: PASS | FAIL | SKIPPED
[E2E_Tooling]: <BATS|Playwright|Cypress|pytest|other|NONE>

## [COMMIT]
[Message]: test({PHASE_ID}): add/update E2E tests
[Status]: Committed | Pending | Skipped
```

---

## [SPEC:FULL:PRD] - Product Requirements Document

### Purpose
Transform research and constraints into deterministic, implementation-agnostic `specs/{FEATURE_SLUG}/prd.md` defining: What is being built, Why it is being built, Measurable success criteria, Explicit functional boundaries.

### Execution Sequence

**STEP_1_CONTEXT_VALIDATION**:
1. Read `specs/{FEATURE_SLUG}/explore.md`
2. Read `specs/constitution.md`
3. Produce:
   - `Context_Summary`
   - `Identified_Functional_Gaps`
   - `Constraint_Extract` (Importing all `[CONST_<ID>]` from both inputs)
   - `Decision_Ledger` (Importing `[Selected_Option]` and `[Residual_Risks]` from explore.md)
   - `Clarification_Log_Extract` (ALL questions from `[CLARIFICATION_LOG]` section)

**STEP_2_BLOCKING_DECISIONS_CHECK** (CRITICAL):
1. Extract all questions from explore.md's `[CLARIFICATION_LOG]` section
2. Identify questions with `[Status]: Blocking`
3. If ANY blocking questions exist, **DO NOT PROCEED** until user provides answers
4. Use AskUser tool to present each blocking question as multi-choice with context

**STEP_3_EXPLORE_UNCERTAINTY_RESOLUTION**:
1. Extract ALL non-blocking open questions, assumptions, residual risks from explore.md
2. For each uncertainty, determine if it impacts PRD's functional completeness
3. Present impactful uncertainties as multi-choice questions via AskUser

**STEP_4_FUNCTIONAL_SYNTHESIS**: Construct `specs/{FEATURE_SLUG}/prd.md`

### PRD Structure

```markdown
# Product Requirements Document

## [PROJECT_VISION]
[Problem_Statement]: <description>
[Target_Outcome]: <description>
[Success_Metrics]:
- [METRIC_<ID>]: <measurable_indicator>

---

## [USER_STORIES]
### [US_<NNN>]
As a [user type],
I want to [action],
So that [benefit].
[Inherited_Constraints]: <list specific CONST_<ID> or RISK_<ID>>

---

## [ACCEPTANCE_CRITERIA]
### [AC_<NNN>] — References: [US_<NNN>]
GIVEN [initial state]
WHEN [action occurs]
THEN [observable result]
AND [constraint CONST_<ID> is satisfied]

---

## [DATA_MODEL_CONTRACT]

### [INTERNAL_ENTITIES]
#### [ENTITY_<NAME>]
[Purpose]: <business role>
[Attributes]:
- <attribute_name>: <semantic_type> — <description>
[Relationships]:
- <cardinality> [ENTITY_<OTHER>]: <description>
[Lifecycle]:
- [Created_When]: <condition>
- [Mutated_When]: <condition>
- [Deleted_When]: <condition or "never">
[Owned_By]: <user_type or system_component>

### [EXTERNAL_ENTITIES]
- [ENTITY_<NAME>]: <source_system> — <how referenced>

### [BOUNDARY_CONTRACTS]
- [BOUNDARY_<ID>]: <data exchanged> — Direction: <in/out/bidirectional> — Invariants: <constraints>

### [OPERATIONS]
#### [OPERATION_<ID>]: <operation_name>
[Input_Entities]: <list>
[Output_Entities]: <list>
[Preconditions]: <list>
[Postconditions]: <list>

### [DATA_FLOW]
- [OPERATION_<ID>]: [ENTITY_<A>] → [ENTITY_<B>] — <description>

### [DATA_CONSTRAINTS]
- [DC_<ID>]: <uniqueness, referential integrity, or lifecycle dependency rule>

---

## [CONSTRAINTS_AND_INVARIANTS]
[Functional_Boundaries]:
- [CONST_<ID>]: <boundary>
[Exclusions]:
- <excluded_scope>

---

## [RESOLVED_CLARIFICATIONS]
- [Q_<ID>]: <question> → <answer>

---

## [DEFINITION_OF_DONE]
- [ ] All User Stories mapped to Acceptance Criteria
- [ ] All constraints preserved
- [ ] All open questions resolved or documented
- [ ] No implementation details present
- [ ] All entities referenced by at least one User Story
- [ ] All operations covered by at least one Acceptance Criterion

---

## [BLOCKING_ISSUES]
(Include only if applicable)
- [BLOCK_<ID>]: <description>

---

## [SEMANTIC_ANCHORS]
- `specs/{FEATURE_SLUG}/prd.md`
- All `[US_<NNN>]` identifiers
- All `[AC_<NNN>]` identifiers
- All `[ENTITY_<NAME>]` identifiers
- All `[OPERATION_<ID>]` identifiers
```

### HITL_GATE_1_BLUEPRINT

After generating PRD, calculate question budget:
```
QUESTION_BUDGET = 2 + (entities - 2) / 3 + (stories - 3) / 5
Cap at MIN(QUESTION_BUDGET, 12)
```

Present questions grouped by domain (max 4 questions per AskUser call):
- Entity relationship questions
- Constraint satisfaction questions
- Scope clarity questions

### Strict Functional Scope
- **MUST HAVE ZERO AMBIGUITY**
- Exclude syntactic implementation details
- **MUST PRESERVE architectural mandates** defined in explore.md's `[Selected_Option]`
- Focus strictly on functional intent, behavioral requirements, system boundaries

---

## [PHASE_HANDOVER_FLOW]

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   /cycle    │────▶│  /tdd:red   │────▶│  /tdd:green │────▶│/tdd:refactor│
│  (detects   │     │ (outputs    │     │ (outputs    │     │ (outputs    │
│   new task) │     │  RED        │     │  GREEN      │     │  REFACTOR   │
│             │     │  manifest)  │     │  manifest)  │     │  manifest)  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
       ┌───────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   /cycle    │
│  (detects   │
│   complete,  │
│  next task)  │
└─────────────┘
```

### Handover Manifest Format

Each phase outputs a structured manifest for the next phase. The manifest is embedded in the phase's structured output as:

```yaml
## [HANDOVER_MANIFEST]
```yaml
phase: RED|GREEN|REFACTOR
task_id: T001
spec_dir: specs/001-feature
files:
  - path: path/to/file.ext
    action: created|modified
test:
  command: "uv run pytest tests/"
  status: PASS|FAIL
constraints:
  - CONST_01
reasoning:
  approach: approach description
  key_decisions:
    - decision: decision text
      rationale: rationale text
```
```

---

## [CONSTRAINTS]

- NEVER output prose - structured output only
- ALWAYS use bracketed headers `[SECTION_NAME]`
- ALWAYS preserve semantic anchors for stories, metrics, entities
- ALWAYS verify blocking dependencies before drafting
- NEVER include technical implementation in spec content
- ALWAYS verify fail-fast prerequisites before execution
- NEVER skip phases in TDD cycle (always Red → Green → Refactor)
- ALWAYS check for handover before falling back to task status
- PRESERVE handover manifests exactly when passing between phases
- STOP on any execution failure in `--auto` mode
- NEVER create commits (delegate to phase commands or ask user)

---

## [INTEGRATION WITH RGR CLI]

The RGR CLI (`/home/werner-wsl/Development/tools/rgr`) is a Python CLI tool that orchestrates TDD cycles via agent subprocesses. It integrates with this SDD framework:

### RGR Command Mapping

| RGR Command | SDD Equivalent |
|-------------|----------------|
| `rgr run T001` | `/spec:cycle` with explicit task |
| `rgr run --all` | `/spec:cycle --auto` |
| `rgr e2e` | `/spec:tdd:e2e` |

### RGR Phase Prompts

RGR loads phase prompts from:
- `$HOME/.factory/commands/` - Command definitions for agent
- Fallback to slash commands if prompt files not found

### RGR Session Management

RGR persists session state in `.tdd-session.json` and uses:
- `get-spec-context.sh` for spec context discovery
- `manage-tasks.sh` for task status updates
- `get-test-config.sh` for test configuration

### RGR State Machine

RGR enforces valid TDD phase transitions:
```
IDLE → RED → GREEN → REFACTOR → E2E → IDLE
```

---

## [FILE STRUCTURE REFERENCE]

### Scripts Directory (`$HOME/.config/ai/spec/scripts/`)

```
scripts/
├── get-spec-context.sh      # Required - Context resolution
├── assign-next-issue.sh      # Required - GitHub issue assignment
├── create-new-feature.sh     # Required - Branch/worktree creation
├── manage-tasks.sh           # Required - Task status management
├── get-test-config.sh       # Required - Test config resolution
├── sdd-parse-ast.sh         # Required - AST parsing
├── git-commit.sh             # Helper - Git operations with safety
├── pr-review-threads.sh       # Helper - PR review thread management
└── create_issues.sh          # Helper - Batch issue creation
```

### Templates Directory (`$HOME/.config/ai/spec/templates/`)

```
templates/
├── spec-template.md          # Functional specification
├── plan-template.md          # Technical implementation plan
├── tasks-template.md         # Task decomposition
├── pr-template.md            # Pull request description
└── commit-template.md        # Commit message
```

### Spec Directory Structure

```
specs/
├── constitution.md           # Project constitution
└── {FEATURE_SLUG}/
    ├── spec.md              # Functional specification
    ├── research.md          # Research findings
    ├── data-model.md        # Data model design
    ├── plan.md              # Implementation plan
    ├── tasks.md             # Task list
    ├── quickstart.md        # Setup instructions (optional)
    └── contracts/           # API contracts (optional)
        └── *.md
```

---

## [SEMANTIC ANCHORS]

All SDD commands use consistent semantic anchors for traceability:

### Task Identifiers
- Format: `T{NNN}` (e.g., `T001`, `T042`, `T123`)
- Zero-padded, 001-999 range

### Phase Identifiers
- `RED`, `GREEN`, `REFACTOR`, `E2E`

### Story Identifiers
- Format: `STORY_{ID}` (e.g., `STORY_001`)

### Metric Identifiers
- Format: `METRIC_{ID}` (e.g., `METRIC_001`)

### Constraint Identifiers
- Format: `CONST_{ID}` (e.g., `CONST_001`)

### Entity Identifiers
- Format: `ENTITY_{NAME}` (e.g., `ENTITY_USER`)

### Operation Identifiers
- Format: `OPERATION_{ID}` (e.g., `OPERATION_001`)

---

**Document Version**: 1.0.0
**Last Updated**: 2026-05-22
**Scripts Location**: `$HOME/.config/ai/spec/scripts/`
**Templates Location**: `$HOME/.config/ai/spec/templates/`
