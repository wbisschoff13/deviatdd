# DeviaTDD Framework Migration & Endpoint Architecture Blueprint

This document details the transition from legacy Spec-Driven Development (SDD) scripts and `.rgr/` directory structures to a unified python CLI binary called `deviate`. This architecture abstracts system shell utilities into programmatically enforced CLI commands, introduces a deterministic prefix-invariant document hierarchy within `.deviate/`, and explicitly charts prompt ownership throughout the macroscopic development lifecycle.

---

## Part 1: Unified CLI Endpoints (`deviate`)

The `deviate` command-line application decouples the execution environments (Claude Code, Factory Droid) from raw machine scripts. It consolidates runtime context gathering, structural static analysis, configuration discovery, task state mutations, and the micro-sandbox test loop into an atomic, platform-agnostic engine.

### 1. Environment & Context Discovery Primitives

#### `deviate context`

* **Legacy Mapping:** `get-spec-context.sh`
* **Description:** Performs an ascending directory crawl starting at the active working directory to find a root `.deviate/config.toml` file. It automatically discovers the current working git branch name, parses it to derive the active feature slug, computes absolute paths to files, and formats all discovered environment data into structured key-value maps.
* **Input Parameters:** * `--json` (Optional flag: outputs raw serialized data for direct machine injection)
* `--quiet` (Optional flag: silences verbose diagnostic output stream)


* **Output Example (`--json`):**
```json
{
  "project_root": "/workspace/project",
  "git_branch": "feature/auth-jwt-refresh",
  "feature_slug": "auth-jwt-refresh",
  "specs_directory": "/workspace/project/specs/auth-jwt-refresh",
  "constitution_path": "/workspace/project/specs/constitution.md"
}

```



#### `deviate ast parse <path>`

* **Legacy Mapping:** `sdd-parse-ast.sh`
* **Description:** Reads source code files or directory trees down a targeted file path and generates a non-evaluated, compile-safe interface representation. It extracts public modules, package imports, declared classes, public/private methods, variable signatures, and type annotations. This provides structural bounds verification without executing foreign code blocks.
* **Input Parameters:**
* `<path>` (Required target positional argument)
* `--format [json|markdown]` (Defaults to json)



#### `deviate test-config`

* **Legacy Mapping:** `get-test-config.sh`
* **Description:** Queries the current project `.deviate/config.toml` file to resolve operational defaults for the local ecosystem runtime execution block. It yields test commands, isolation arguments, runtime timeout windows, and explicit test marker filter flags.
* **Output Format:** Plaintext environmental strings or a JSON map matching system execution environments.

---

### 2. Workspace & Lifecycle Operations

#### `deviate init`

* **Legacy Mapping:** New programmatic replacement for project bootstrap.
* **Description:** Initializes a standard project-level DeviaTDD compliance framework. It builds out a baseline `.deviate/` dot directory, establishes a default global tracking layer, injects project-wide rules inside `specs/constitution.md`, and safely deploys client configuration hooks (e.g., `.claudecode.json` or `.factory/commands/`) containing the interface definitions for interactive macro flows.

#### `deviate feature create <title-or-issue-id>`

* **Legacy Mapping:** `create-new-feature.sh`, `assign-next-issue.sh`
* **Description:** Consumes a raw system ticket description or numeric string parameter, strips volatile non-alphanumeric text nodes, and transforms it into a URL-friendly lowercase string layout (`feature-slug`). It switches the local working tree over to a clean, isolated git branch or worktree, initializes the feature subdirectory framework inside `specs/{FEATURE_SLUG}/`, and marks that specific slug as the active workspace target within `.deviate/session.json`.
* **Input Parameters:**
* `<title-or-issue-id>` (Positional string match argument)



#### `deviate feature sync`

* **Legacy Mapping:** New programmatic context maintenance routine.
* **Description:** Automatically rebases the current feature branch against the project's upstream default integration branch (`main`/`master`), evaluates file trees for merge conflicts inside the `specs/` layout, and warns if structural interface changes invalidate current active technical plans.

---

### 3. Task & Tracking Mutations

#### `deviate tasks parse`

* **Legacy Mapping:** `manage-tasks.sh` (structural validations)
* **Description:** Scans `specs/{FEATURE_SLUG}/tasks.md` and applies a strict schema validator. It validates that all task nodes contain compliant tracking indicators, valid structural cross-reference links matching elements in `spec.md` or `plan.md`, and that no broken markdown annotations are present.
* **Returns:** Exit code `0` on validation pass. Exit code `1` with localized file diagnostics on failure.

#### `deviate tasks list`

* **Legacy Mapping:** Custom system dashboard visualizations.
* **Description:** Reads the parsing tree of the feature's active `tasks.md` file and converts it into a tabular summary of current, completed, pending, or blocked tasks.

#### `deviate tasks update <task-id> <status>`

* **Legacy Mapping:** `manage-tasks.sh` (state updates)
* **Description:** Updates state tokens on specific task check-boxes in `tasks.md`.
* **Security & Governance Constraint:** This endpoint enforces programmatic access restrictions. An executive agent running inside an interactive chat layout **cannot** manually advance a task status checkbox directly to completed (`[X]`). If an agent attempts to mutate a status identifier to finished, this endpoint rejects the disk write unless the request is cryptographically signed or directly spawned by the trusted internal `deviate run` micro-sandbox automated loop engine.
* **Input Parameters:**
* `<task-id>` (Target sequence hash index)
* `<status>` (`[ ]` / `[wip]` / `[blocked]`)



---

### 4. Micro-Sandbox Execution Loops & VCS Gates

#### `deviate run <task-id>`

* **Legacy Mapping:** Integrated RGR core runtime framework.
* **Description:** Triggers the deterministic, automated execution cycle for a singular decomposed task node. It traps the probabilistic agent substrate within a rigid state machine cycle (`IDLE` -> `RED` -> `GREEN` -> `REFACTOR` -> `JUDGE` -> `IDLE`). It handles file tamper guards, monitors the file system, executes test runner parameters retrieved from `deviate test-config`, applies Train Gate resets on assertion compilation breaks, and auto-commits the diff tree on verified loop steps.
* **Input Parameters:**
* `<task-id>` (Positional sequence hash target identifier)
* `--profile <name>` (Overrides default runtime engine constraints, e.g., `fast`, `secure`)



#### `deviate run --all`

* **Legacy Mapping:** Automated multi-step orchestration.
* **Description:** Sequences and triggers the sequential resolution of all unblocked, incomplete items defined inside the target feature matrix until it hits a task block or error condition.

#### `deviate commit --stage <phase>`

* **Legacy Mapping:** `git-commit.sh`
* **Description:** Enforces pre-commit invariants before finalizing a git change tracking step. It ensures that modified file boundaries match allowed code paths, validates that no files inside the `specs/` root folder have been changed by an execution agent, sets standardized prefixes matching the current execution phase, and commits the code.
* **Input Parameters:**
* `--stage [RED|GREEN|REFACTOR|E2E]`



---

## Part 2: Document Architecture & Prompt Ownership

To enforce inference path consistency and maximize KV caching efficiency, files are split into cross-project constraints and feature buckets. Volatile data arrays, state history flags, and configuration profiles are hosted cleanly within the `.deviate/` metadata directory.

### 1. File Tree Blueprint

```text
.deviate/
├── config.toml               # Test parameters, target models, environment execution configurations
├── session.json              # State tracker file mapping active branch and lock metrics
└── prompts.log               # Append-only execution record storing runtime loop diagnostic trails
specs/
├── constitution.md           # Absolute project invariants and architectural constraints
└── {FEATURE_SLUG}/           # Isolated target directory bucket for macroscopic features
    ├── explore.md            # Technical exploration diary and options analysis
    ├── prd.md                # System-level product requirement documents
    ├── spec.md               # Pure functional contract ("What & Why" system bounds)
    ├── plan.md               # Technical execution design layout ("How" structural blueprint)
    └── tasks.md              # Strictly managed tracking checkpoint checklist matrix

```

---

### 2. Prompt Matrix & File Generation Lifecycle

Macroscopic commands represent user-facing conversational routines registered as interactive slash commands inside client execution configurations during the `deviate init` process.

| Client Command Trigger | Responsible Persona Role | Targets Created / Mutated | Internal CLI Endpoints Executed |
| --- | --- | --- | --- |
| `/explore` | Technical Researcher | `specs/{FEATURE_SLUG}/explore.md` | `deviate feature create`, `deviate context` |
| `/prd` | Product Owner Proxy | `specs/{FEATURE_SLUG}/prd.md` | `deviate context` |
| `/specify` | Systems Architect | `specs/{FEATURE_SLUG}/spec.md` | `deviate ast parse` |
| `/plan` | Technical Lead | `specs/{FEATURE_SLUG}/plan.md` | `deviate test-config` |
| `/tasks` | Decomposition Parser | `specs/{FEATURE_SLUG}/tasks.md` | `deviate tasks parse` |

#### 1. Command Definition: `/explore`

* **Objective:** Explores technical constraints and establishes project branch architecture.
* **Action Logic:**
1. Spawns the feature directory layout and sets up working git states by running:
```bash
deviate feature create "auth logging overhaul"

```


2. Resolves global project environment mappings by calling:
```bash
deviate context --json

```


3. Evaluates library dependencies, reviews legacy code bottlenecks, documents system limits, and builds the architectural options analysis trade-off matrix inside `explore.md`.



#### 2. Command Definition: `/prd`

* **Objective:** Transforms technical exploration metrics or raw system tickets into immutable user requirements.
* **Action Logic:**
1. Requests environment parameters:
```bash
deviate context --json

```


2. Evaluates the conclusions set within `explore.md`.
3. Produces a detailed requirements layout inside `prd.md`, specifying structural user goals, performance constraints, user behavior limits, and validation parameters.



#### 3. Command Definition: `/specify`

* **Objective:** Converts product goals into absolute system interfaces.
* **Action Logic:**
1. Scans the codebase to discover module configurations and API definitions by calling:
```bash
deviate ast parse ./src/core/auth

```


2. Compiles functional interfaces, schema objects, route patterns, and system edge cases into `spec.md`, defining the architectural boundary contract.



#### 4. Command Definition: `/plan`

* **Objective:** Designs the implementation and verification layout.
* **Action Logic:**
1. Collects system runtime execution targets:
```bash
deviate test-config

```


2. Maps out targeted file locations, mock boundaries, data mock fixtures, and unit/integration design expectations inside `plan.md`.



#### 5. Command Definition: `/tasks`

* **Objective:** Decomposes technical design documents into sequential test steps.
* **Action Logic:**
1. Generates an incremental series of small, testable tasks where every entry links an explicit functional contract item to a distinct test verification assertion.
2. Asserts the structural integrity of the newly produced file before completing by calling:
```bash
deviate tasks parse

```





Once the macroscopic loops finalize `tasks.md` inside the feature directory, control shifts from the interactive conversation space back to the developer's local terminal. The developer passes task tracking indices over to the automated local execution runner loop:

```bash
deviate run task-001

```

This structural division keeps project directories clean, guarantees reproducible prompt execution flows, and traps untrusted code changes within a protected, programmatically validated micro-sandbox test loop.
