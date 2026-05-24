# DeviaTDD: Dual Engine Verification Infrastructure for Agentic Test-Driven Development
## Core Architecture, Lifecycle, and Engineering Specification

---

## 1. Architectural Overview & Philosophy
The architecture operates as a hierarchical lifecycle that shifts from human-driven macroscopic scoping to machine-orchestrated, deterministic microscopic execution loops. It is founded on the principle that Large Language Models (LLMs) are probabilistic, optimization-seeking actors that require structured infrastructure containment rather than implicit alignment trust.

```plaintext
[ MACRO LAYER: Scoping ]  ──> Explore ──> PRD ──> Shard
                                                    │
                                                    ▼
[ MESO LAYER: Contracts ] ──> Specify ──> Plan ──> Context ──> Tasks
                                                                 │
                                                                 ▼
[ MICRO LAYER: TDD Loop ] ──> Red ──> Green ──> Judge/Train ──> Refactor
                                │  ▲
                                ▼  │
                     [ YELLOW: Amend Gate ]
```

---

## 1.5 Non-Goals: What DeviaTDD Is Not

To maintain strict operational focus and establish explicit boundaries of responsibility, DeviaTDD defines the following items as out-of-scope:

* **Not an Agent Substrate Optimizer:** This framework does not attempt to solve the fundamental reasoning, planning, or context-handling limitations of underlying LLM models. If an execution agent aggressively deviates from its instructions, hallucinates runtime workarounds, or behaves erratically, it is categorized as a failure of model capability rather than an infrastructural flaw.
* **Not a Kernel-Level Sandbox Engine:** DeviaTDD does not implement operating system-level virtualization, container runtimes, or syscall write blocking to actively intercept filesystem manipulation during execution. Instead, it relies on deterministic Git-ledger audits and target-path diff monitoring to passively catch, reject, and roll back invalid agent states.
* **Not a Cost-Optimized Prototyping Utility:** Agentic software verification with multi-stage evaluation loops is inherently token-expensive. DeviaTDD does not prioritize absolute token reduction at the expense of governance. Every validation cycle is treated as a necessary investment for maintaining long-term code integrity.
* **Not an Autonomous, Closed-Loop Software Factory:** This framework completely rejects the premise of unsupervised, self-validating AI development systems. DeviaTDD is explicitly anchored on structured Human-in-the-Loop (HITL) specification boundaries and contract alignment gates.

---

## 2. Hierarchical Architectural Layers

### 2.1 The Macro Layer: Feature Scoping
Breaks a business goal down into standard development project containers.
* **Explore:** Research phase to isolate tech stacks and architectural guidelines.
* **PRD:** Translates research into a clear, feature-wide requirement set.
* **Shard:** Breaks down the PRD into standalone technical issue files (GitHub Issues).

### 2.2 The Meso Layer: Issue Engineering
Creates formal contracts for an issue via CLI slash commands.
* **Specify (`/spec:core:specify`):** Generates a structured functional contract (`spec.md`).
* **Plan (`/spec:core:plan`):** Decomposes the specification into a concrete test plan layout (`plan.md`).
* **Context (`/spec:core:context`):** Synchronizes dependencies and historical constitution constraints.
* **Tasks (`/spec:core:tasks`):** Generates the trackable execution blueprint (`tasks.md`) with explicit requirement-to-test mapping tags.

### 2.3 The Micro Layer: The Automated Sandbox (Python CLI)
The executor agent targets a line item in `tasks.md` and is trapped inside a strict state machine governed by Git, deterministic parsing, and defensive operational safeguards.

* **RED (The Contract):**
    * **Action:** The agent writes a unit/integration test.
    * **Verification:** The Python runner executes `pytest --json-report`. It parses the JSON to verify the failure is due to missing implementation (`AssertionError`, `NotImplementedError`) and not a syntax crash.
    * **State Lock:** `git add . && git commit -m "test: [TASK-ID] Red phase complete"`.
* **GREEN (The Execution):**
    * **Action:** The agent iterates on production code to pass the test.
    * **Tamper Guard:** Before evaluating the test suite, the CLI runs `git checkout HEAD -- <test_target_file>` to revert any unauthorized modifications the agent made to the test file. (See Section 8.2 for downstream scope auditing).
    * **Timeout Guard:** The runner enforces a hard timeout (e.g., `--timeout=10`) to kill infinite loops.
    * **State Lock:** Upon a valid Green pass, `git add . && git commit -m "feat: [TASK-ID] Green phase complete"`.
* **YELLOW (The Amendment Protocol - Conditional):**
    * **Action:** If the agent realizes during Green that the Red test is architecturally flawed, it cannot secretly alter it. It must output a `<propose_test_amendment>` block.
    * **Process:** The CLI pauses the Green phase and sends the original test, proposed test, and `spec.md` to an isolated Yellow Judge.
    * **If Approved:** The CLI overwrites the test, locks the new state (`git commit -m "test(amend): ..."`), and resumes Green.
    * **If Rejected:** The CLI rejects the proposal, updates `<judge_feedback>`, and forces the agent back to Green under original constraints.
* **JUDGE / TRAIN (The Compliance Gate):**
    * **The Judge:** The CLI evaluates `git diff HEAD~1 HEAD` (only the implementation) against `spec.md` for invariant/security violations. This judge operates in a clean, zero-shared-history session to break recursive subjectivity.
    * **The Train (Ephemeral Rollback):** If rejected, the CLI safely resets without destroying task progress:
        1. Read `tasks.md` into memory.
        2. Rollback via `git reset --hard HEAD~1` (wipes bad implementation, preserves Red test).
        3. Synthesize a destructive update (replace old failure with new context) to the `<judge_feedback>` tag in memory.
        4. Write the memory state back to disk, routing the agent back to Green.
* **REFACTOR (The Polish Gate):**
    * **Action:** If the Judge accepts the work, the workspace unlocks for an isolated run to polish readability.
    * **Regression Gate:** Post-refactor, the CLI re-runs the test suite. If the tests fail (agent broke code), the CLI safely discards the refactor (`git reset --hard`) and successfully completes the task using the verified Green commit.

---

## 3. Mapping of Architectural Fulfillment

This closed-loop lifecycle converts high-level human intent into strict machine-level invariants. The framework satisfies core development methodologies as follows:

### 3.1 Spec-Driven Development (SDD)
* **How it is fulfilled:** Executed directly via the Macro Layer and Meso Layer.
* **Mechanisms:** The workflow prohibits "vibe coding" or jumping straight into implementation. The framework enforces an artifact-centric approach where a feature must be systematically defined via research, Product Requirement Documents (PRDs), and issue sharding. Slash commands like `/spec:core:specify` and `/spec:core:plan` lock down the functional intent (`spec.md`) and technical approach (`plan.md`) before a single line of feature code can legally be written.

### 3.2 Test-Driven Development (TDD)
* **How it is fulfilled:** Executed via the Micro Layer: Automated Sandbox.
* **Mechanisms:** This layer implements a pure, unyielding RED-GREEN-REFACTOR loop. The Python CLI enforces that the agent first writes a unit or integration test. It then parses the test runner's JSON output (`pytest --json-report`) to programmatically verify that the test failed due to a missing implementation rather than a syntax crash. The code cannot move forward until a successful Green implementation is verified and locked using atomic Git commits at every step boundary.

### 3.3 Test-Driven Agentic Development (TDAD)
* **How it is fulfilled:** Executed via defensive safeguards embedded in the Micro Layer Sandbox.
* **Mechanisms:** Standard TDD assuming human developers falls short with LLM agents, which are prone to bypassing tests, creating infinite loops, or rewriting assertions to pass falsely. This architecture addresses TDAD directly by adding a Tamper Guard (automatically running `git checkout HEAD -- <test_target_file>` to revert unauthorized test edits) and hard timeout limits. It isolates agent behavior to keep the model strictly trapped within the bounds of deterministic software verification.

### 3.4 Acceptance Test-Driven Development (ATDD)
* **How it is fulfilled:** Achieved through bidirectional requirement traceability and the Meso/Micro Layer transition.
* **Mechanisms:** During the Meso phase, `/spec:core:tasks` translates high-level customer requirements, user stories, and acceptance criteria into explicit target mapping tags inside `tasks.md`. In the Micro phase, the Judge Gate evaluates the collective task execution delta directly against the overarching functional constraints of `spec.md`. This guarantees that passing unit tests mathematically equal a passed business acceptance spec.

### 3.5 Evaluation-Driven Development (EDD)
* **How it is fulfilled:** Realized via the Yellow Amend Gate and the Judge/Train Compliance Gate.
* **Mechanisms:** This architecture shifts validation from basic functional checks to prompt optimization and alignment validation. If the execution agent attempts to bend architectural constraints, the isolated Judge evaluates the `git diff` against code-level invariants. When a violation occurs, the Train Gate initiates an ephemeral rollback (`git reset --hard HEAD~1`), writes diagnostic adjustments to the `<judge_feedback>` tag, and feeds that fresh context back into the agent's prompt context. This treats the agent's context window as an iteratively trained parameter optimized for perfect execution compliance.

---

## 4. Core State Machine Engine

The execution state transitions must follow a strict non-bypassable sequence. Backward paths are structurally impossible unless triggered by the programmatic Yellow Amendment or Train Rollback protocols.

```
   ┌─────────┐      /spec:core:specify     ┌───────────┐
   │  IDLE   │ ──────────────────────────> │ SPECIFIED │
   └─────────┘                             └───────────┘
        ▲                                        │
        │                                        │ /spec:core:plan
        │                                        ▼
        │   ┌──────────────┐  /spec:core:tasks ┌───────────┐
        └── │ TASKS_READY  │ <──────────────── │  PLANNED  │
            └──────────────┘                   └───────────┘
                   │
                   │ rgr run [TASK_ID]
                   ▼
            ┌──────────────┐
            │  PHASE_RED   │ ──(Test Failure Verified)──┐
            └──────────────┘                            │
                   ▲                                    │
                   │ (Invalid Red/Syntax Error)         ▼
                   └───────────────────────────── ┌───────────┐
                                                  │ PHASE_GREEN│ <──────────┐
                                                  └───────────┘            │
                                                        │                  │
                                           Proposed     │    Judge         │ Train
                                           Amendment    │  Violation       │ Rollback
                                                        ▼                  │
                                                  ┌───────────┐            │
                                                  │ PHASE_AMEND│           │
                                                  └───────────┘ ───────────┘
                                                        │
                                           Approved     │
                                           Amendment    ▼
                                                  ┌───────────┐
                                                  │PHASE_JUDGE│
                                                  └───────────┘
                                                        │
                                                Passed  │
                                                Judge   ▼
                                                  ┌───────────┐
                                                  │ PHASE_REFA│
                                                  └───────────┘
                                                        │
                                                        │ Regression check
                                                        ▼
                                                  ┌───────────┐
                                                  │ TASK_DONE │
                                                  └───────────┘
```

---

## 5. Phase Prompts & System Context Injection Boundaries

Agents are bound into specialized operational scopes by context restrictions. Open-ended instructions are forbidden.

### 5.1 Meso Layer Phase Prompts
* **`/spec:core:specify` Context:** Issue Data + Raw Architectural Guidelines.
    * *System Directives:* Analyze raw input requirements. Synthesize the deterministic functional specification (`spec.md`). Express logic entirely in business behavior boundaries, edge states, and data models. Exclude engineering syntax or syntax paradigms.
* **`/spec:core:plan` Context:** `spec.md` + Codebase Layout Map.
    * *System Directives:* Process the locked boundaries of `spec.md`. Draft a structured implementation roadmap (`plan.md`) describing test boundaries, mock definitions, and code location hooks. Do not generate code.
* **`/spec:core:tasks` Context:** `spec.md` + `plan.md`.
    * *System Directives:* Decompose the roadmap into discrete, line-item execution steps within `tasks.md`. Every line item must be assigned a unique tracking identifier and map cleanly to an acceptance criterion in `spec.md`.

### 5.2 Micro Layer Sandbox Prompts
* **`PHASE_RED` System Prompt:**
    ```text
    You are running in DeviaTDD PHASE_RED. Your execution block is write-locked to the test directory for [TASK_ID].
    
    INVARIANTS:
    1. You may only modify or create code files within the designated test paths.
    2. Do not write, patch, or amend any production/business logic directories.
    3. The test code must fail gracefully via AssertionError or NotImplementedError.
    4. Code introducing syntax crashes, import failures, or compile faults will be rejected by the runtime evaluator.
    ```
* **`PHASE_GREEN` System Prompt:**
    ```text
    You are running in DeviaTDD PHASE_GREEN. Your objective is to pass the test block validated during the RED phase.
    
    INVARIANTS:
    1. You may not edit any test files. The Tamper Guard automatically resets any mutations to tests.
    2. Write the clean, optimal production logic required to pass the test assertions.
    3. If you encounter an un-passable design flaw in the test structure, you must immediately halt and declare a structural modification request inside a `<propose_test_amendment>` block.
    ```
* **`PHASE_AMEND` (Yellow Judge) System Prompt:**
    ```text
    You are the isolated Yellow Gate Auditor. Review the active spec.md, the original failing test structure, and the agent's amendment block request.
    
    Determine if the revision fixes an invalid test assumption or if the agent is trying to escape strict constraints. Output exclusively <status>APPROVED</status> or <status>REJECTED</status> with structured technical analysis.
    ```
* **`PHASE_JUDGE` (Compliance Gate) System Prompt:**
    ```text
    You are the Compliance Gate Judge. Analyze the production `git diff` for [TASK-ID] against the rules in spec.md.
    
    Verify that no undocumented assumptions, security holes, or structural drift were introduced. If valid, output <verdict>PASS</verdict>. If a violation is present, output <verdict>FAIL</verdict> and include explicit corrections for the execution agent.
    ```

---

## 6. Human-in-the-Loop (HITL) Checkpoint Gates

The framework prevents total autonomy drift by enforcing non-bypassable verification steps where a human supervisor must unlock the transition.

```
[Macro Outputs] ──>  ( GATE 1: Blueprint Approval )  ──> [Meso Layer Unlocks]
                                  │
                                  ▼
[Meso Tasks]   ──>  ( GATE 2: Contract Sign-Off )   ──> [Micro Loop Executes]
                                  │
                                  ▼
[Micro Success] ──>  ( GATE 3: Final Merge Audit )   ──> [Production Deployment]
```

* **Gate 1: Blueprint Approval (Macro-to-Meso Boundary)**
    * *Trigger:* Triggered when the initial Research and PRD manifests are generated.
    * *Action:* Human reviews core architectural selections and tech stacks. Meso layer execution remains locked until an approval flag is written.
* **Gate 2: Contract Sign-Off (Meso-to-Micro Boundary)**
    * *Trigger:* Triggered when `tasks.md` and `spec.md` are completely finalized.
    * *Question Budget Rule:* The agent can prompt the user with targeted clarity questions (max 4 per interaction) to resolve functional ambiguity before locking.
    * *Action:* Human signs off on the requirement tags. This is required before `rgr run [TASK_ID]` will execute.
* **Gate 3: Final Merge Audit (Micro-to-Idle Boundary)**
    * *Trigger:* Triggered when all items in `tasks.md` achieve a `TASK_DONE` state.
    * *Action:* Human evaluates the full atomic Git commit history, total testing metrics, and approves merging the feature branch into main.

---

## 7. Multi-Framework Testing Abstraction

DeviaTDD standardizes framework outputs into its state engine using a unified driver specification.

| Testing Framework | CLI Invocation Strategy | Success Validation | Error Parse Pattern | Tamper Guard Reset Path |
| :--- | :--- | :--- | :--- | :--- |
| **Python / pytest** | `pytest --json-report` | `exit_code == 0` | Inspect JSON for `outcome == "failed"` matching an explicit `AssertionError` / `NotImplementedError`. | `git checkout HEAD -- tests/` |
| **Node.js / Jest** | `jest --json` | `success == true` | Inspect JSON for failed assertions; ensure zero runtime or module import failures. | `git checkout HEAD -- __tests__/` |
| **Go / testing** | `go test -json` | `Action == "pass"` | Parse output stream lines for `Action == "fail"` with explicit testing log assertions. | `git checkout HEAD -- *_test.go` |

---

## 8. Core Architectural Invariants & Guardrails

The orchestrator must maintain and enforce these six structural constraints across all operations:

1. **The Git Isolation Principle:** Every isolated task loop must be executed on a clean git branch or worktree environment. Commits must be made automatically at each phase boundary (`test: [TASK-ID]`, `feat: [TASK-ID]`).
2. **The Test Reversion & Scope Audit Law (Tamper Guard Upgrade):** When entering or running the `GREEN` execution phase, the testing directories must be programmatically forced back to their post-`RED` commit status via a hard checkout hook. To prevent optimization-seeking agents from circumventing execution parameters, the host CLI executes a passive `git diff` audit prior to processing any `GREEN` phase evaluation. If changes are detected outside the designated implementation targets (e.g., configurations, environment components, shared mocks, or parent infrastructure paths), the transaction is immediately invalidated, rolled back, and thrown as an execution error.
3. **State Immobility:** Agents cannot edit task progress indicators within `tasks.md`. Status fields are read-only to agents and are modified exclusively by the host CLI runner upon passing test and judge requirements.
4. **Deterministic Test Failure Check:** For a `RED` phase to be valid, the test must crash explicitly due to missing code logic (assertions). Runtime engine issues, bad imports, typos, or script failures are caught and handled as execution errors, returning the file to the agent without committing.
5. **Memory Preservation via Train Gates:** When the code fails a compliance check, the workspace is safely reset to the last valid commit via a hard reset (`git reset --hard HEAD~1`) to remove code rot. However, the generated failure logs must be preserved and injected directly into the agent's context window. The agent's contextual understanding must expand systematically even when bad files are dropped.
6. **The Elastic Governance Rule:** The operational overhead and token consumption of the micro-execution loop can be scaled dynamically using project-level Execution Profiles configured in `.rgr/config.toml`. While the baseline state machine path remains unyielding, specific semantic phases—such as the independent Judge Phase, automated Refactoring routines, or long-running Train loops—can be scaled back, bypassed, or attached to higher/lower model thresholds depending on the target task's explicit risk or temperature tier (e.g., `--profile fast` versus `--profile secure`).
