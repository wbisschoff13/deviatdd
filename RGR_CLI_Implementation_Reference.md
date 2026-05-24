# RGR CLI - TDD Orchestrator Command Reference

## Overview

RGR (Red-Green-Refactor) is a Python CLI tool that orchestrates TDD cycles via agent subprocesses (Claude/Droid). It manages task workflows, phase transitions, session persistence, and human-in-the-loop (HITL) checkpoints.

**Project**: `/home/werner-wsl/Development/tools/rgr`
**Language**: Python 3.10+
**Key Dependencies**: pydantic>=2.0, typer>=0.12, rich>=13.0
**Entry Point**: `rgr = "rgr.cli:app"`

---

## TABLE OF CONTENTS

1. [Architecture Overview](#architecture-overview)
2. [Data Models](#data-models)
3. [CLI Commands](#cli-commands)
4. [CLI Helper Functions](#cli-helper-functions)
5. [Session Management](#session-management)
6. [TDD State Machine](#tdd-state-machine)
7. [Agent Executor](#agent-executor)
8. [Human-in-the-Loop (HITL)](#human-in-the-loop-hitl)
9. [Test Verification](#test-verification)
10. [Task Parser](#task-parser)
11. [Configuration](#configuration)
12. [Interrupt Handling](#interrupt-handling)
13. [Dashboard Rendering](#dashboard-rendering)
14. [Error Handling](#error-handling)
15. [File Paths and Locations](#file-paths-and-locations)
16. [Testing](#testing)
17. [Command-Line Interface Summary](#command-line-interface-summary)
18. [Constants](#constants)
19. [Integration with SDD Commands](#integration-with-sdd-commands)
20. [Workflow Examples](#workflow-examples)

---

## Architecture Overview

```
src/rgr/
├── __init__.py
├── cli.py              # Typer CLI application
├── models.py          # Pydantic data models
├── orchestrator.py     # TddStateMachine, AgentExecutor
├── session.py          # SessionManager
├── hitl.py             # HitlManager
├── test_verifier.py    # Verifier for test execution
├── parser.py           # Task parsing
├── agents.py          # Agent detection
├── dashboard.py       # Rich table rendering
└── config.py          # Configuration loading
```

### Core Components

1. **SessionManager**: Persists session state across TDD phases via `.tdd-session.json`
2. **TddStateMachine**: Enforces valid TDD phase transitions (IDLE→RED→GREEN→REFACTOR→E2E→IDLE)
3. **AgentExecutor**: Spawns agent subprocesses (Claude/Droid) with prompt management
4. **HitlManager**: Handles pause/resume decisions when agent requires human input
5. **Verifier**: Executes test suites and verifies DoD compliance

---

## Data Models

### TaskStatus (Enum)
```python
class TaskStatus(str, Enum):
    PENDING = "PENDING"       # [ ] unchecked
    IN_PROGRESS = "IN_PROGRESS"  # [/] green done
    COMPLETED = "COMPLETED"   # [x] complete
```

### RiskLevel (Enum)
```python
class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
```

### EffortLevel (Enum)
```python
class EffortLevel(str, Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"
```

### ExecutionMode (Enum)
```python
class ExecutionMode(str, Enum):
    TDD = "TDD"           # Full Red-Green-Refactor cycle
    IMMEDIATE = "IMMEDIATE" # Direct execution without test-first
```

### AgentType (Enum)
```python
class AgentType(str, Enum):
    CLAUDE = "CLAUDE"
    DROID = "DROID"
    AUTO = "AUTO"  # Defaults to CLAUDE
```

### Phase (Enum)
```python
class Phase(str, Enum):
    IDLE = "IDLE"
    RED = "RED"
    GREEN = "GREEN"
    REFACTOR = "REFACTOR"
    E2E = "E2E"
```

### PhaseOutcome (Enum)
```python
class PhaseOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    HITL_REQUIRED = "HITL_REQUIRED"
    INVALID_TRANSITION = "INVALID_TRANSITION"
```

### HitlDecision (Enum)
```python
class HitlDecision(str, Enum):
    CONTINUE = "CONTINUE"
    RETRY = "RETRY"
    ABORT = "ABORT"
    ENTER_COMMAND = "ENTER_COMMAND"
```

### SessionState (Enum)
```python
class SessionState(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
```

### Task Model
```python
class Task(BaseModel):
    task_id: str              # T<NNN> format (e.g., "T001")
    description: str          # Task description text
    status: TaskStatus        # Current task status
    checkbox_line: int        # Line number in tasks.md
    raw_checkbox: str         # Original checkbox string
    risk_level: Optional[RiskLevel]
    effort: Optional[EffortLevel]
    execution_mode: Optional[ExecutionMode]
    tdd_required: bool        # Whether TDD cycle is required
    
    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        # Must match T<NNN> format where NNN is 001-999
        if not _TASK_ID_PATTERN.match(v):
            raise ValueError("task_id must match format T<NNN>")
        return v
```

### Session Model
```python
class Session(BaseModel):
    session_id: uuid.UUID
    agent: AgentType
    current_task_id: str      # T<NNN> format
    current_phase: Phase
    state: SessionState
    created_at: datetime
    updated_at: datetime
    last_error: Optional[str]
    red_output: Optional[str]   # RED phase output for GREEN context
    green_output: Optional[str] # GREEN phase output for REFACTOR context
```

### ExecutionConfig Model
```python
class ExecutionConfig(BaseModel):
    test_command: str         # e.g., "uv run pytest -n auto"
    test_root: str            # e.g., "tests"
    test_extension: str       # e.g., "_test.py"
    timeout_seconds: int = 300
```

### SpecContext Model
```python
class SpecContext(BaseModel):
    branch_name: str
    feature_slug: str
    spec_dir: str
    worktree_path: Optional[str]
    project_root: Path
```

### VerificationResult Model
```python
class VerificationResult(BaseModel):
    phase: Phase
    exit_code: Optional[int]
    verification_status: VerificationStatus
    execution_time_seconds: float
    timestamp: datetime
    session_id: uuid.UUID
```

### DodCheckResult Model
```python
class DodCheckResult(BaseModel):
    code_implemented: bool
    tests_passing: bool
    coverage_met: bool        # Coverage >= 80%
    lint_passing: bool        # Ruff/mypy checks
    documentation_updated: bool
    overall_pass: bool
```

### VerificationStatus Enum
```python
class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CRASH = "CRASH"
    TIMEOUT = "TIMEOUT"
```

### PhaseLog Model
```python
class PhaseLog(BaseModel):
    """Record of a single phase execution with agent output."""

    log_id: uuid.UUID
    task_id: str              # T<NNN> format
    phase: Phase
    outcome: PhaseOutcome
    agent_output: str         # Raw output from agent subprocess
    session_id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime]

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        if not _TASK_ID_PATTERN.match(v):
            raise ValueError("task_id must match format T<NNN>")
        return v
```

### PhaseResult Model
```python
class PhaseResult(BaseModel):
    """Result of a phase execution."""

    outcome: PhaseOutcome
    session_id: uuid.UUID
    agent_output: str = ""
```

### TaskCompletionState Model
```python
class TaskCompletionState(BaseModel):
    """State representing task completion status from tasks.md."""

    total_tasks: int
    completed_tasks: int
    all_complete: bool
    task_ids: List[str]
```

### TasksFile Model
```python
class TasksFile(BaseModel):
    """Represents the tasks.md file and its tasks."""

    file_path: Path
    tasks: List[Task]
    last_modified: datetime
```

### AgentStatus Model
```python
class AgentStatus(BaseModel):
    """Status of an available agent."""

    agent_type: AgentType
    available: bool
    version: Optional[str]
    path: Optional[str]
```

### AgentDetectionResult Model
```python
class AgentDetectionResult(BaseModel):
    """Result of agent detection."""

    agents: List[AgentStatus]
    recommended_agent: Optional[AgentType]
    can_proceed: bool
```

---

## CLI Commands

### `rgr` (default - dashboard)
```
rgr [--file|-f <tasks_file>] [--config|-c <config_path>]
```
Displays tasks from tasks.md in a Rich table dashboard. Auto-detects tasks file if not provided.

**Flow**:
1. Auto-detect tasks file via `_discover_tasks_file()`
2. Check agent availability via `detect_agents()`
3. Validate tasks.md format
4. Render dashboard via `dashboard.render_dashboard()`

### `rgr dashboard`
```
rgr dashboard [--file|-f <tasks_file>] [--config|-c <config_path>]
```
Explicit dashboard command.

### `rgr run [TASK_ID]`
```
rgr run [TASK_ID] [--tasks-file|-f <file>] [--dry-run] [--all|-a] [--verbose|-v]
```
Run TDD cycle for a task (or all pending tasks with `--all`).

**Single Task Mode**:
1. Check prerequisites (agent, file existence, valid format)
2. Find target task (`_find_target_task`)
3. Route based on `tdd_required`:
   - TDD required → `_run_tdd_cycle()`
   - Direct execution → Execute via agent prompt

**All Tasks Mode** (`--all`):
1. Get all pending/in-progress tasks
2. Execute sequentially
3. Stop on first failure

### `rgr e2e`
```
rgr e2e [--tasks-file|-f <file>] [--dry-run]
```
Run E2E phase after all tasks complete.

**Preconditions**:
- All tasks in tasks.md must be marked complete `[x]`
- Checks via `check_all_tasks_completed()`

**Flow**:
1. Verify all tasks complete
2. Execute E2E phase via `TddStateMachine.execute_e2e_phase()`
3. Verify Definition of Done compliance
4. Commit after successful E2E

### `rgr validate`
```
rgr validate [--file|-f <tasks_file>]
```
Validate tasks.md file format. Returns JSON with validation results.

**Output**:
```json
{
  "valid": true|false,
  "errors": [
    {"line_number": 1, "error_type": "TASK_PARSE_ERROR", "message": "...", "context": "..."}
  ],
  "task_count": 42
}
```

Exit code 1 if validation fails.

### `rgr check-agents`
```
rgr check-agents [--preferred|-p <AGENT>]
```
Check available agents (claude, droid) on system.

**Output**:
```json
{
  "agents": [
    {"agent_type": "CLAUDE", "available": true, "version": "1.0", "path": "/usr/bin/claude"}
  ],
  "recommended_agent": "CLAUDE",
  "can_proceed": true
}
```

Exit code 1 if no agents available.

### `rgr config show`
```
rgr config show
```
Display current effective configuration.

**Output**:
```
┌─────────────────┬───────────────────────────────────┬──────────┐
│ Setting         │ Value                             │ Source  │
├─────────────────┼───────────────────────────────────┼──────────┤
│ agent_preference│ AUTO                              │ builtin │
│ tasks_file      │ tasks.md                          │ builtin │
│ config_source   │ BUILTIN                           │          │
└─────────────────┴───────────────────────────────────┴──────────┘
```

### `rgr config export`
```
rgr config export [--output|-o <file>] [--user] [--project]
```
Export default configuration template.

---

## CLI Helper Functions

The CLI module (`cli.py`) contains numerous helper functions that support command execution:

### Agent Configuration Helpers

```python
def _get_agent_from_config(project_root: Optional[Path] = None) -> AgentType:
    """Load config and return agent_preference. Defaults to CLAUDE if config fails."""

def _get_agent_command(project_root: Optional[Path] = None) -> str:
    """Load config and return agent_command. Defaults to 'claude' if config fails."""
```

### Tasks File Discovery

```python
def _discover_tasks_file(default_path: str = "tasks.md") -> str:
    """Auto-discover tasks.md path using get-spec-context.sh script.

    Discovery Flow:
    1. Run $HOME/.config/ai/spec/scripts/get-spec-context.sh --json
    2. Extract 'spec_dir' and 'spec_dir_exists'
    3. Check for {spec_dir}/tasks.md
    4. Fall back to {spec_dir}/plan.md if tasks.md doesn't exist
    5. Fall back to default_path

    Returns:
        Path to tasks.md (may be relative or absolute)
    """
```

### Task Validation Helpers

```python
def _validate_tasks_file(tasks_file: str) -> dict:
    """Validate a tasks file and return result dict.

    Returns:
        Dict with valid, errors, and task_count fields.
        Continues parsing even when errors are encountered.
    """

def _validate_task_id(task_id: str, line_num: int) -> str:
    """Validate task ID matches T<NNN> format where NNN is 001-999.
    Raises TaskParseError if invalid."""

def _map_checkbox_to_status(checkbox: str) -> TaskStatus:
    """Map checkbox string to TaskStatus enum."""

def _build_tasks_from_validation(validation_result: dict, tasks_file: str) -> List[Task]:
    """Build Task objects from validation result for dashboard rendering."""
```

### Prerequisites Checking

```python
def _check_cli_prerequisites(tasks_file: str) -> List[Task]:
    """Check all CLI prerequisites and return parsed tasks.

    Performs fail-fast checks for:
    - Agent availability
    - Tasks file existence
    - Tasks file validity

    Returns:
        List of parsed Task objects

    Raises:
        typer.Exit: If any prerequisite check fails
    """
```

### Task Selection Helpers

```python
def _find_target_task(tasks: List[Task], task_id: Optional[str]) -> Task:
    """Find the target task to run.

    Args:
        tasks: List of available tasks
        task_id: Specific task ID to run, or None to find first pending

    Returns:
        The target Task to run

    Raises:
        TaskNotFoundError: If task_id not found
        TaskAlreadyCompletedError: If task already completed
        NoPendingTasksError: If no pending tasks available
    """
```

### Output Callbacks

```python
def _stream_output_callback(output: str) -> None:
    """Callback for streaming agent output to console.

    Handles JSON output from Claude agent by extracting and formatting
    the result field. Replaces escaped newlines with actual newlines.
    """

def _silent_callback(output: str) -> None:
    """Silent callback - does nothing (used when verbose=False)."""
```

### Task Status Helpers

```python
def _mark_task_status(tasks_file: str, task_id: str, status: str) -> None:
    """Mark a task with a specific status in tasks.md.

    Args:
        tasks_file: Path to tasks.md
        task_id: Task ID to mark
        status: Status to set:
          - "[\\]" (red complete)
          - "[/]" (green done)
          - "[x]" (completed)
    """

def _mark_task_completed(tasks_file: str, task_id: str) -> None:
    """Mark a task as completed ([x]) in tasks.md.

    Args:
        tasks_file: Path to tasks.md
        task_id: Task ID to mark as completed
    """
```

### Git Helpers

```python
def _get_git_head() -> Optional[str]:
    """Get current git HEAD commit hash.

    Returns:
        The git HEAD commit hash, or None if not in a git repo
    """

def _run_commit_after_phase(
    phase: str,
    task_id: str,
    agent: AgentType,
    before_commit: Optional[str] = None,
    executor: Optional[Any] = None,
) -> bool:
    """Run /tools-commit after a phase completes if no commit was made.

    Args:
        phase: The phase name (red, green, refactor, execute, e2e)
        task_id: The task ID
        agent: The agent type (CLAUDE or DROID)
        before_commit: The git commit hash before the phase ran
        executor: Optional AgentExecutor for building prompts

    Returns:
        True if commit succeeded or was skipped, False if commit failed
    """
```

### TDD Cycle Execution

```python
def _run_tdd_cycle(
    task_id: str,
    session_manager: SessionManager,
    executor: AgentExecutor,
    output_callback: Optional[Callable[[str], None]] = None,
    tasks_file: str = "tasks.md",
    session: Optional[Session] = None,
    verbose: bool = False,
    task_status: TaskStatus = TaskStatus.PENDING,
) -> bool:
    """Execute the full TDD cycle for a task.

    Args:
        task_id: The task ID to execute
        session_manager: Session manager instance
        executor: Agent executor instance
        output_callback: Optional callback for streaming output
        tasks_file: Path to tasks.md
        session: Optional existing session (for continuation)
        verbose: Whether to show verbose output
        task_status: Current task status (determines resume point)

    Returns:
        True if cycle completed successfully, False otherwise

    Raises:
        TaskAbortError: If user aborts during execution

    Phase Skip Logic:
        - PENDING: Start from RED
        - IN_PROGRESS: Continue from GREEN (RED already done)
        - COMPLETED: Skip to REFACTOR
    """

def _execute_phase(
    phase: Phase,
    session: Session,
    executor: AgentExecutor,
    output_callback: Optional[Callable[[str], None]] = None,
    max_retries: int = 3,
    retry_count: int = 0,
    session_manager: Optional[SessionManager] = None,
    tasks_file: Optional[str] = None,
    task_id: Optional[str] = None,
    verbose: bool = False,
) -> bool:
    """Execute a single TDD phase.

    Args:
        phase: The phase to execute
        session: The current session
        executor: Agent executor instance
        output_callback: Callback for streaming output
        max_retries: Maximum retry attempts (default 3)
        retry_count: Current retry attempt number
        session_manager: Session manager (for HITL)
        tasks_file: Path to tasks.md (for status updates)
        task_id: Task ID (for status updates)
        verbose: Whether to show verbose output

    Returns:
        True if phase completed successfully, False otherwise
    """
```

### Multi-Task Execution

```python
def _run_all_tasks(
    pending_tasks: List[Task],
    tasks_file: str,
    dry_run: bool,
    verbose: bool = False,
) -> None:
    """Execute all pending/in-progress tasks sequentially.

    Stops on first failure and reports summary at end.

    Args:
        pending_tasks: List of tasks to execute
        tasks_file: Path to tasks.md
        dry_run: If True, show what would run without executing
        verbose: Whether to show verbose output
    """

def _run_single_task(
    target_task: Task,
    tasks_file: str,
    dry_run: bool,
    verbose: bool = False,
) -> None:
    """Execute a single task (either TDD or direct execution).

    Routes based on task.tdd_required:
    - TDD required: Calls _run_tdd_cycle()
    - Direct execution: Calls AgentExecutor.execute_prompt()
    """
```

### Interrupt Handling Helpers

```python
def _setup_interrupt_handler(phase: Phase) -> None:
    """Set up interrupt handler before a phase runs.

    Initializes:
    - _interrupt_flag[0] = False
    - _interrupted_count = 0
    - _interrupted_phase = phase
    - Saves original SIGINT handler
    """

def _cleanup_interrupt_handler() -> None:
    """Restore original interrupt handler after phase completes."""

def _get_interrupt_choice() -> str:
    """Prompt user for choice after Ctrl+C: 1=retry, 2=exit."""

def _restart_phase(
    session: Session,
    phase: Phase,
    executor: AgentExecutor,
    output_callback: Optional[Callable],
    task_id: str,
) -> bool:
    """Restart the current phase from a clean state (after Ctrl+C).

    Uses git reset --hard to revert to previous phase's commit,
    then re-executes the phase.

    Reset Map:
        - GREEN → RED commit
        - REFACTOR → GREEN commit
        - E2E → REFACTOR commit
        - RED: Cannot restart (no previous commit)

    Returns:
        True if retry succeeded, False otherwise
    """
```

### Custom Exceptions

```python
class TaskNotFoundError(Exception):
    """Raised when specified task ID not found."""
    def __init__(self, task_id: str):
        self.task_id = task_id

class TaskAlreadyCompletedError(Exception):
    """Raised when attempting to run completed task."""
    def __init__(self, task_id: str):
        self.task_id = task_id

class NoPendingTasksError(Exception):
    """Raised when no pending tasks are available."""
    pass

class TaskAbortError(Exception):
    """Raised when task explicitly aborted by user."""
    def __init__(self, task_id: str):
        self.task_id = task_id
```

---

## Session Management

### SessionManager Class

```python
class SessionManager:
    def __init__(self, session_file: Path = Path(".tdd-session.json")):
        self.session_file = session_file

    def create_session(self, agent: AgentType, task_id: str) -> Session:
        """Create new session with generated UUID."""
        now = datetime.now(timezone.utc)
        return Session(
            session_id=uuid.uuid4(),
            agent=agent,
            current_task_id=task_id,
            current_phase=Phase.IDLE,
            state=SessionState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def load_session(self) -> Optional[Session]:
        """Load session from file. Returns None if file doesn't exist, invalid JSON, or state is COMPLETED/FAILED."""

    def save_session(self, session: Session) -> None:
        """Save session to .tdd-session.json"""

    def update_phase(self, session: Session, phase: Phase) -> Session:
        """Update current phase and timestamp."""

    def complete_session(self, session: Session) -> Session:
        """Mark session as completed."""

    def fail_session(self, session: Session, error: str) -> Session:
        """Mark session as failed."""
```

### Session Persistence

- **File**: `.tdd-session.json` in project root
- **Format**: JSON via Pydantic `model_dump_json()`
- **States**: ACTIVE, PAUSED, COMPLETED, FAILED

---

## TDD State Machine

### Valid Phase Transitions

```python
_VALID_TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.IDLE: {Phase.RED},        # Start TDD cycle
    Phase.RED: {Phase.GREEN},      # RED → GREEN
    Phase.GREEN: {Phase.REFACTOR},  # GREEN → REFACTOR
    Phase.REFACTOR: {Phase.E2E, Phase.IDLE},  # REFACTOR → E2E or back to IDLE
    Phase.E2E: {Phase.IDLE},        # E2E completes cycle
}
```

### TddStateMachine Class

```python
class TddStateMachine:
    def __init__(
        self,
        session_manager: SessionManager,
        agent_executor: AgentExecutor,
        hitl_manager: HitlManager,
        verifier: Verifier,
    ):
        self.session_manager = session_manager
        self.agent_executor = agent_executor
        self.hitl_manager = hitl_manager
        self.verifier = verifier

    def validate_transition(self, from_phase: Phase, to_phase: Phase) -> bool:
        """Validate a phase transition. Returns True if allowed, False otherwise."""

    def get_current_phase(self, session: Session) -> Phase:
        """Get the current phase of the state machine."""

    async def execute_red_phase(
        self,
        session: Session,
        sync_to_tasks: bool = False,
        tasks_file: str = "tasks.md",
        skip_validation: bool = False,
    ) -> PhaseResult:

    async def execute_green_phase(
        self,
        session: Session,
        sync_to_tasks: bool = False,
        tasks_file: str = "tasks.md",
        skip_validation: bool = False,
    ) -> PhaseResult:

    async def execute_refactor_phase(
        self,
        session: Session,
        sync_to_tasks: bool = False,
        tasks_file: str = "tasks.md",
        skip_validation: bool = False,
    ) -> PhaseResult:

    async def execute_e2e_phase(
        self,
        session: Session,
        sync_to_tasks: bool = False,
        tasks_file: str = "tasks.md",
        skip_validation: bool = False,
    ) -> PhaseResult:

    async def verify_red_phase(self, session: Session) -> VerificationResult:
        """Verify RED phase - expects tests to FAIL (exit code 1)."""

    async def verify_green_phase(self, session: Session) -> VerificationResult:
        """Verify GREEN phase - expects tests to PASS (exit code 0)."""

    async def verify_refactor_phase(self, session: Session) -> VerificationResult:
        """Verify REFACTOR phase - expects tests to PASS (exit code 0)."""

    def pause_on_agent_error(self, session: Session, error_message: str) -> None:
        """Pause session when agent returns an error."""

    def pause_on_verification_failure(
        self, session: Session, phase: Phase, verification_result: Any
    ) -> None:
        """Pause session when verification fails in GREEN or REFACTOR phase."""

    async def resume_with_retry(self, session: Session, testing: bool = False) -> PhaseResult:
        """Resume a paused session by retrying the current phase."""

    def resume_with_abort(self, session: Session) -> None:
        """Resume a paused session by aborting."""
```

### check_all_tasks_completed Function

```python
def check_all_tasks_completed(tasks_file: str) -> TaskCompletionState:
    """Check if all tasks in tasks.md are completed.

    Args:
        tasks_file: Path to the tasks.md file

    Returns:
        TaskCompletionState with completion status and task IDs
    """
```

### TaskBudgetGuard

Prevents infinite task generation loops during GREEN phase:

```python
MAX_TASKS_PER_GREEN_PHASE = 5

class TaskBudgetGuard:
    @staticmethod
    def get_pending_task_count(tasks_path: str) -> int:
        """Count pending tasks in tasks.md"""

    @staticmethod
    def validate_task_invariants(
        tasks_path: str,
        active_task_id: str,
        initial_pending_count: int,
    ) -> tuple[bool, str]:
        """Validate after GREEN phase:
        1. No more than MAX_TASKS_PER_GREEN_PHASE new tasks added
        2. Active task not marked complete by agent during GREEN
        """
```

---

## Agent Executor

### AgentExecutor Class

```python
class AgentExecutor:
    # Prompt file paths per phase
    PROMPT_FILES: dict = {
        Phase.RED: "spec-tdd-red.md",
        Phase.GREEN: "spec-tdd-green.md",
        Phase.REFACTOR: "spec-tdd-refactor.md",
        Phase.E2E: "spec-tdd-e2e.md",
    }
    EXECUTE_PROMPT_FILE: str = "spec-execute.md"
    COMMIT_PROMPT_FILE: str = "tools-commit.md"

    # Phase command slugs - base format without separator
    # Droid uses dashes: /spec-tdd-{phase}
    # Claude uses colons: /spec:tdd:{phase}
    PHASE_COMMANDS: dict = {
        Phase.RED: "tdd-red",
        Phase.GREEN: "tdd-green",
        Phase.REFACTOR: "tdd-refactor",
        Phase.E2E: "tdd-e2e",
        Phase.IDLE: "tdd-red",
    }

    PHASE_COMMANDS_CLAUDE: dict = {
        Phase.RED: "tdd:red",
        Phase.GREEN: "tdd:green",
        Phase.REFACTOR: "tdd:refactor",
        Phase.E2E: "tdd:e2e",
        Phase.IDLE: "tdd:red",
    }

    def __init__(
        self,
        session_manager: Any,
        project_root: Optional[Path] = None,
        agent_command: str = "claude",
    ):
        self.session_manager = session_manager
        self.project_root = project_root or Path.cwd()
        self.agent_command = agent_command  # e.g., "claude", "droid", etc.
        self.test_verifier = Verifier(
            test_config=self._discover_test_config(),
            spec_context=self._discover_spec_context(),
        )

    def _discover_test_config(self) -> ExecutionConfig:
        """Discover test configuration using get-test-config.sh script.

        Fallback defaults if script fails:
            test_command: "uv run pytest -n auto"
            test_root: "tests"
            test_extension: "_test.py"
            timeout_seconds: 300
        """

    def _discover_spec_context(self) -> SpecContext:
        """Discover spec context using get-spec-context.sh script.

        Fallback defaults if script fails:
            branch_name: "unknown"
            feature_slug: "unknown"
            spec_dir: "specs"
            worktree_path: None
            project_root: self.project_root
        """

    def _load_prompt(self, filename: str) -> Optional[str]:
        """Load prompt content from file. Checks multiple locations:
        - ~/.factory/commands/
        - ~/.codex/prompts/
        """

    def _substitute_prompt_vars(
        self,
        prompt: str,
        task_id: str,
        arguments: Optional[str] = None,
        previous_output: Optional[str] = None,
    ) -> str:
        """Substitute {TASK_ID}, $ARGUMENTS, {ARGUMENTS} placeholders.
        Appends previous phase context if provided."""

    def _build_prompt(
        self,
        session: Session,
        phase: Phase,
        agent: AgentType = AgentType.CLAUDE,
        previous_output: Optional[str] = None,
    ) -> str:
        """Build prompt for Claude/Droid. Loads from file or falls back to slash commands."""

    def _build_execute_prompt(
        self,
        task_id: str,
        agent: AgentType = AgentType.CLAUDE,
        arguments: Optional[str] = None,
    ) -> str:
        """Build prompt for direct execution (no TDD). Uses EXECUTE_PROMPT_FILE."""

    def _build_commit_prompt(self, commit_message: str) -> str:
        """Build prompt for commit workflow. Uses COMMIT_PROMPT_FILE."""

    def _build_agent_command(
        self,
        session: Session,
        phase: Phase,
        previous_output: Optional[str] = None,
    ) -> tuple:
        """Build agent command based on agent type.

        Returns tuple of (command, use_shell):
        - Droid: shell with heredoc (`droid exec -o json --auto medium -- << 'EOF' ... EOF`)
        - Claude: `claude -p --output-format json [--resume <session_id>] <prompt>`

        Session ID is used for Claude when not in IDLE phase for continuous conversation.
        """

    async def execute_phase(
        self,
        session: Session,
        phase: Phase,
        output_callback: Optional[Callable] = None,
        previous_output: Optional[str] = None,
    ) -> PhaseResult:
        """Execute TDD phase via agent subprocess.

        Handles:
        - Non-zero exit codes (triggers HITL)
        - Permission errors (retries once with medium auto)
        - Session ID extraction (retries on failure)
        - Output streaming via callback
        """

    async def execute_prompt(
        self,
        session: Session,
        prompt: str,
        output_callback: Optional[Callable] = None,
    ) -> PhaseResult:
        """Execute custom prompt via agent subprocess.

        Used for:
        - Direct execution (no TDD)
        - Custom commands via HITL ENTER_COMMAND option
        """

    def _extract_session_id(self, output: str) -> Optional[uuid.UUID]:
        """Extract session_id from agent output. JSON parsing first, regex fallback."""

    def _is_permission_error(self, output: str) -> bool:
        """Check if output indicates insufficient permission error."""

    def _create_result(
        self,
        outcome: PhaseOutcome,
        session: Session,
        agent_output: str,
    ) -> PhaseResult:
        """Create a PhaseResult with the given parameters."""
```

### Agent Detection

```python
def detect_agents(preferred_agent: AgentType = AgentType.AUTO) -> AgentDetectionResult:
    """Detect available agents (claude, droid) on system."""

def _get_recommended_agent(agents: List[AgentStatus], preferred: AgentType) -> Optional[AgentType]:
    """Determine which agent to recommend based on preference and availability."""
```

### Agent Command Selection

```python
# In cli.py, helper functions for agent config:
def _get_agent_from_config(project_root: Optional[Path] = None) -> AgentType:
    """Load config and return agent_preference. Defaults to CLAUDE."""

def _get_agent_command(project_root: Optional[Path] = None) -> str:
    """Load config and return agent_command. Defaults to 'claude'."""
```

---

## Human-in-the-Loop (HITL)

### HitlManager Class

```python
class HitlManager:
    def __init__(self, session_manager: Optional[SessionManager]):
        self.session_manager = session_manager

    def pause_session(self, session: Session, error_message: str) -> None:
        """Pause session and capture error message. Sets state to PAUSED, last_error to error_message."""

    def detect_hitl_trigger(
        self,
        phase: Phase,
        phase_outcome: PhaseOutcome,
        error_message: Optional[str],
    ) -> Optional[str]:
        """Detect trigger type: 'agent_error', 'verification_failure', 'user_input_request'."""

    def get_trigger_reason(self, phase: Phase, agent_output: str) -> str:
        """Generate human-readable reason for HITL trigger."""

    def prompt_user_options(
        self,
        session: Session,
        testing: bool = False,
        allow_continue: bool = True,
    ) -> HitlDecision:
        """Prompt user with options. Returns CONTINUE, RETRY, or ABORT."""

    def prompt_user_options_advanced(
        self,
        session: Session,
        trigger_reason: Optional[str] = None,
        testing: bool = False,
    ) -> tuple[HitlDecision, Optional[str]]:
        """Advanced prompt with ENTER_COMMAND option.
        Returns (decision, custom_command) where custom_command is None unless decision is ENTER_COMMAND."""

    def resume_session(self, session: Session, decision: HitlDecision) -> None:
        """Resume paused session based on user's decision.
        - ABORT: Sets state to FAILED
        - CONTINUE/RETRY: Sets state to ACTIVE, clears last_error"""
```

### HITL Trigger Scenarios

1. **Agent Error**: Agent returns non-zero exit code or crashes
2. **Session ID Extraction Failure**: Cannot extract session_id from agent output (soft failure)
3. **Permission Error**: Agent reports insufficient permissions
4. **Verification Failure**: Test results don't match expectations

### HITL Decision Flow

```
Agent returns HITL_REQUIRED
        │
        ▼
┌───────────────────┐
│ Pause session     │
│ Capture error    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Get trigger reason│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Prompt user      │
│ (advanced menu)  │
└────────┬──────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    ▼         ▼         ▼          ▼
 CONTINUE   RETRY   ENTER_COMMAND  ABORT
    │         │         │          │
    ▼         ▼         ▼          ▼
 Resume    Retry    Custom     Fail session
 (ACTIVE)  phase    prompt     (FAILED)
```

---

## Test Verification

### Verifier Class

```python
class Verifier:
    def __init__(self, test_config: ExecutionConfig, spec_context: SpecContext):
        self.test_config = test_config
        self.spec_context = spec_context

    def _map_exit_code_to_status(self, exit_code: int, phase: Phase) -> VerificationStatus:
        """Map exit code to verification status:
        - RED: expects exit 1 (tests fail)
        - GREEN/REFACTOR: expects exit 0 (tests pass)
        - Exit codes 2-5 indicate CRASH
        """

    async def verify_test_results(self, phase: Phase, session_id: uuid.UUID) -> VerificationResult:
        """Execute test suite and verify results for given phase."""

    async def verify_dod_compliance(self, session_id: uuid.UUID) -> DodCheckResult:
        """Verify Definition of Done:
        - code_implemented: src/ directory exists with .py files
        - tests_passing: test suite passes
        - coverage_met: coverage >= 80%
        - lint_passing: ruff + mypy pass
        - documentation_updated: docs/ exists or README.md exists
        """
```

### Exit Code Semantics

```python
# pytest conventions
EXIT_CODES = {
    0: "All tests passed",
    1: "Some tests failed",
    2: "Interrupted by user",
    3: "Internal error",
    4: "Usage error",
    5: "No tests collected",
}
# -1: Sentinel for TIMEOUT or CRASH (command not found)
```

---

## Task Parser

### Parsing Pattern

```python
_TASK_LINE_PATTERN = re.compile(
    r"^-\s*(\[[ x/\\]\])\s*\[([^\]]+)\]\s*(.+)$", re.IGNORECASE | re.MULTILINE
)
_METADATA_PATTERN = re.compile(r"\{([^:}]+):\s*([^}]+)\}")
```

### Task ID Validation

```python
def _validate_task_id(task_id: str, line_num: int) -> str:
    """Must be T<NNN> format where NNN is 001-999. T000 not allowed."""
```

### Metadata Extraction

```python
def extract_task_metadata(description: str) -> Tuple[Optional[RiskLevel], Optional[EffortLevel], Optional[ExecutionMode]]:
    """Extract {risk: high}, {effort: M}, {execution_mode: TDD} from description."""

def extract_execution_mode_from_block(task_block: str) -> Optional[ExecutionMode]:
    """Extract [Execution_Mode]: TDD from indented lines."""

def extract_risk_level_from_block(task_block: str) -> Optional[RiskLevel]:
    """Extract [Risk_Level]: high from indented lines."""

def extract_effort_from_block(task_block: str) -> Optional[EffortLevel]:
    """Extract [Effort]: M from indented lines."""
```

### TDD Required Determination

```python
def determine_tdd_required(
    risk_level: Optional[RiskLevel],
    effort: Optional[EffortLevel],
    execution_mode: Optional[ExecutionMode] = None,
) -> bool:
    """Priority:
    1. Execution_Mode field (highest): IMMEDIATE → no TDD, TDD → TDD required
    2. Risk-based fallback: HIGH/MEDIUM → TDD required, LOW/NONE → no TDD
    3. Default: TDD required (conservative)
    """
```

### parse_tasks Function

```python
def parse_tasks(tasks_file: str) -> TasksFile:
    """Parse tasks.md file and extract tasks with status.
    
    Returns TasksFile with list of Task objects.
    Raises: FileNotFoundError, PermissionError, UnicodeDecodeError, TaskParseError
    """
```

### update_task_status Function

```python
def update_task_status(tasks_file: str, task_id: str, status: TaskStatus) -> None:
    """Update task's status in tasks.md file.
    
    Raises: FileNotFoundError if file doesn't exist
            ValueError if task_id not found
    """
```

---

## Configuration

### Config Model

```python
class Config(BaseModel):
    agent_preference: AgentType = Field(default=AgentType.AUTO)
    config_source: ConfigSource  # PROJECT, USER, or BUILTIN
    project_root: Path
    tasks_file: Path
    agent_command: str = "claude"
```

### ConfigSource Enum

```python
class ConfigSource(str, Enum):
    PROJECT = "PROJECT"
    USER = "USER"
    BUILTIN = "BUILTIN"
```

### Hierarchical Precedence

```python
def load_config(project_root: Path) -> Config:
    """Load configuration with precedence: PROJECT > USER > BUILTIN
    
    1. Project config: .rgr/config.toml in project root
    2. User config: ~/.config/rgr/config.toml
    3. Builtin defaults
    """
```

### Config File Format (TOML)

```toml
# RGR Configuration
# Place in .rgr/config.toml (project) or ~/.config/rgr/config.toml (user)

# Agent preference: CLAUDE, DROID, or AUTO (default: AUTO)
# agent_preference = "AUTO"

# Path to tasks file (default: tasks.md)
# tasks_file = "tasks.md"
```

### E2EPhaseConfig Model

```python
class E2EPhaseConfig(BaseModel):
    """Configuration for E2E phase execution."""

    prompt_template: str = Field(
        default=".chezmoitemplates/prompts/spec/tdd/e2e.md",
        description="Path to E2E prompt template",
    )
    verification_timeout: int = Field(
        default=300, ge=0,
        description="Timeout for E2E verification in seconds",
    )
    skip_coverage_check: bool = Field(
        default=False,
        description="Whether to skip coverage verification",
    )
    skip_lint_check: bool = Field(
        default=False,
        description="Whether to skip lint verification",
    )
```

### load_config Function

```python
def load_config(project_root: Path) -> Config:
    """Load configuration with precedence: PROJECT > USER > BUILTIN.

    Args:
        project_root: Path to the project root directory

    Returns:
        Config model with loaded configuration

    Precedence:
    1. Project config: .rgr/config.toml in project root
    2. User config: ~/.config/rgr/config.toml
    3. Builtin defaults
    """
```

---

## Interrupt Handling

### Global Interrupt State

```python
_interrupt_flag = [False]
_interrupted_count = 0
_interrupted_phase: Optional[Phase] = None
_original_sigint_handler: Any = None
```

### Signal Handler

```python
def _signal_handler(signum, frame):
    """Handle Ctrl+C during phase execution.
    - First Ctrl+C: Set flag, prompt for choice
    - Second Ctrl+C: Force exit (130)
    """
```

### Interrupt Flow

```
Ctrl+C received
       │
       ▼
_set_interrupt_flag(true)
_increment_interrupted_count
       │
       ▼
count >= 2? ──YES──→ Force exit (130)
       │
      NO
       │
       ▼
Show menu:
  [1] Retry current phase
  [2] Exit
       │
       ▼
User choice
  1 → _restart_phase() (git reset + re-run)
  2 → Exit
```

### _restart_phase Function

```python
def _restart_phase(
    session: Session,
    phase: Phase,
    executor: AgentExecutor,
    output_callback: Optional[Callable],
    task_id: str,
) -> bool:
    """Restart current phase from clean state.
    
    Uses git reset --hard to revert to previous phase's commit,
    then re-executes the phase.
    
    Reset map:
    - GREEN → RED commit
    - REFACTOR → GREEN commit
    - E2E → REFACTOR commit
    """
```

---

## Workflow Examples

### Single Task TDD Cycle

```bash
# 1. Show dashboard
rgr

# 2. Run TDD for specific task
rgr run T001 --verbose

# 3. Run E2E after all tasks complete
rgr e2e
```

### Continuous Mode

```bash
# Run all pending tasks sequentially
rgr run --all

# Dry run to see what would execute
rgr run --dry-run
```

### Validate and Debug

```bash
# Validate tasks.md format
rgr validate --file tasks.md

# Check agent availability
rgr check-agents --preferred CLAUDE

# Show configuration
rgr config show
```

### Interrupt and Resume

```bash
# During phase execution, press Ctrl+C
# Choose:
#   [1] Retry current phase (git reset + re-run)
#   [2] Exit

# Later, resume from where stopped
rgr run  # picks up next pending task
```

### Direct Execution (No TDD)

```bash
# Tasks with execution_mode=IMMEDIATE or low risk are executed directly
rgr run T042  # direct execution, no Red→Green→Refactor
```

---

## CLI Auto-Discovery

### _discover_tasks_file Function

```python
def _discover_tasks_file(default_path: str = "tasks.md") -> str:
    """Auto-discover tasks.md path using get-spec-context.sh script.
    
    Attempts to find tasks file in spec directory when running in a worktree.
    Falls back to default_path if auto-detection fails.
    """
```

### Discovery Flow

1. Run `$HOME/.config/ai/spec/scripts/get-spec-context.sh --json`
2. Extract `spec_dir` and `spec_dir_exists`
3. Check for `{spec_dir}/tasks.md`
4. Fall back to `{spec_dir}/plan.md` if tasks.md doesn't exist
5. Fall back to `default_path`

---

## Dashboard Rendering

### render_dashboard Function

```python
def render_dashboard(tasks: List[Task]) -> str:
    """Render tasks as Rich table.
    
    Columns: Task ID, Status (with bracket notation), Description
    Status formatting:
    - PENDING → "[ ] Pending"
    - IN_PROGRESS → "[/] In Progress"
    - COMPLETED → "[x] Completed"
    """
```

---

## Error Handling

### Custom Exceptions

```python
class TaskNotFoundError(Exception):
    """Raised when specified task ID not found."""
    def __init__(self, task_id: str):
        self.task_id = task_id

class TaskAlreadyCompletedError(Exception):
    """Raised when attempting to run completed task."""
    def __init__(self, task_id: str):
        self.task_id = task_id

class NoPendingTasksError(Exception):
    """Raised when no pending tasks available."""

class TaskAbortError(Exception):
    """Raised when task explicitly aborted by user."""
    def __init__(self, task_id: str):
        self.task_id = task_id
```

### Fail-Fast Checks

1. **Agent Availability**: `detect_agents()` must return `can_proceed=true`
2. **Tasks File Existence**: File must exist and be readable
3. **Tasks File Validity**: Must pass `_validate_tasks_file()`

---

## File Paths and Locations

### Project Structure

```
rgr/
├── pyproject.toml
├── src/rgr/
│   ├── __init__.py
│   ├── cli.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── session.py
│   ├── hitl.py
│   ├── test_verifier.py
│   ├── parser.py
│   ├── agents.py
│   ├── dashboard.py
│   └── config.py
├── .tdd-session.json          # Session persistence
├── tasks.md                 # Task list (user-provided)
├── specs/                   # Spec directory (worktree)
├── .rgr/
│   ├── config.toml         # Project config
│   └── prompts.log         # Prompt debug log
├── scripts/                 # Helper scripts
│   ├── get-spec-context.sh
│   └── get-test-config.sh
└── contracts/               # API contracts
```

### Key Paths

| Path | Purpose |
|------|---------|
| `.tdd-session.json` | Session state persistence |
| `tasks.md` | Task list file |
| `.rgr/config.toml` | Project configuration |
| `.rgr/prompts.log` | Prompt debugging log |
| `specs/constitution.md` | Project constitution |

---

## Testing

### Test Markers

```toml
[tool.pytest.ini_options]
markers = [
    "e2e: marks tests that run real agent subprocesses",
    "slow: marks tests as slow",
    "skip_agent_mock: skip mock_detect_agents autouse fixture",
]
```

### Running Tests

```bash
# All tests
uv run pytest

# Skip e2e tests
uv run pytest -m "not e2e"

# With coverage
uv run pytest --cov=rgr --cov-fail-under=80

# Parallel
uv run pytest -n auto
```

---

## Command-Line Interface Summary

| Command | Description |
|---------|-------------|
| `rgr` | Show dashboard (default) |
| `rgr dashboard` | Display tasks table |
| `rgr run [TASK_ID]` | Run TDD cycle |
| `rgr run --all` | Run all pending tasks |
| `rgr e2e` | Run E2E phase |
| `rgr validate` | Validate tasks.md format |
| `rgr check-agents` | Check available agents |
| `rgr config show` | Show configuration |
| `rgr config export` | Export config template |

---

## Constants

```python
# Validation
_TASK_ID_PATTERN = re.compile(r"^T\d{3}$")
_VALID_CHECKBOXES = ("[ ]", "[/]", "[x]", "[\\]")

# Task generation guardrails
MAX_TASKS_PER_GREEN_PHASE = 5

# Agent commands
PHASE_COMMANDS = {
    Phase.RED: "tdd-red",
    Phase.GREEN: "tdd-green",
    Phase.REFACTOR: "tdd-refactor",
    Phase.E2E: "tdd-e2e",
}

PHASE_COMMANDS_CLAUDE = {
    Phase.RED: "tdd:red",
    Phase.GREEN: "tdd:green",
    Phase.REFACTOR: "tdd:refactor",
    Phase.E2E: "tdd:e2e",
}
```

---

## Integration with SDD Commands

RGR CLI is designed to work with the SDD command framework:

1. **Phase Prompts**: AgentExecutor loads phase prompts from `$HOME/.factory/commands/`
2. **Spec Context**: Uses `get-spec-context.sh` to discover spec directory
3. **Task Management**: Uses `manage-tasks.sh` for task status updates
4. **Test Config**: Uses `get-test-config.sh` for test configuration

### Handoff Manifest Format

Each phase outputs a structured manifest for the next phase:

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

---

This document contains all implementation details for the RGR TDD Orchestrator CLI. Use this as a complete reference for understanding and modifying the codebase.
