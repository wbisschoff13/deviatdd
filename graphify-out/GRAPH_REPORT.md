# Graph Report - aether  (2026-06-10)

## Corpus Check
- 165 files · ~155,227 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1479 nodes · 2271 edges · 64 communities (55 shown, 9 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 396 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a5c2006f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Vector Index Metadata|Vector Index Metadata]]
- [[_COMMUNITY_Project Root & Documentation|Project Root & Documentation]]
- [[_COMMUNITY_Core Utility Functions|Core Utility Functions]]
- [[_COMMUNITY_Micro Layer TDD Sandbox|Micro Layer TDD Sandbox]]
- [[_COMMUNITY_Session & Config State|Session & Config State]]
- [[_COMMUNITY_Meso Layer Specification|Meso Layer Specification]]
- [[_COMMUNITY_Init Scaffold & Governance|Init Scaffold & Governance]]
- [[_COMMUNITY_Core Contract & Issues|Core Contract & Issues]]
- [[_COMMUNITY_DeviaTDD Architecture Specs|DeviaTDD Architecture Specs]]
- [[_COMMUNITY_Validation Engine|Validation Engine]]
- [[_COMMUNITY_Deviate Workflow Skills|Deviate Workflow Skills]]
- [[_COMMUNITY_Git Worktree Management|Git Worktree Management]]
- [[_COMMUNITY_DeviaTDD Workflow Phases|DeviaTDD Workflow Phases]]
- [[_COMMUNITY_ISS-001 CLI Bootstrap|ISS-001 CLI Bootstrap]]
- [[_COMMUNITY_Constitution Governance|Constitution Governance]]
- [[_COMMUNITY_Init Integration Tests|Init Integration Tests]]
- [[_COMMUNITY_Specify Command Tests|Specify Command Tests]]
- [[_COMMUNITY_Git Commit Module|Git Commit Module]]
- [[_COMMUNITY_Manifest T001 Migration|Manifest T001 Migration]]
- [[_COMMUNITY_Manifest T002 Migration|Manifest T002 Migration]]
- [[_COMMUNITY_Manifest T004 Migration|Manifest T004 Migration]]
- [[_COMMUNITY_Bash Parity Tests|Bash Parity Tests]]
- [[_COMMUNITY_Git Repo Detection|Git Repo Detection]]
- [[_COMMUNITY_Macro Contract Tests|Macro Contract Tests]]
- [[_COMMUNITY_Task Run Command Tests|Task Run Command Tests]]
- [[_COMMUNITY_Meso Contract Tests|Meso Contract Tests]]
- [[_COMMUNITY_Init Export Cycle Tests|Init Export Cycle Tests]]
- [[_COMMUNITY_Pydantic Data Models|Pydantic Data Models]]
- [[_COMMUNITY_PRD Extraction Module|PRD Extraction Module]]
- [[_COMMUNITY_Task Decomposition Skills|Task Decomposition Skills]]
- [[_COMMUNITY_Init Command Tests|Init Command Tests]]
- [[_COMMUNITY_Explore Command Tests|Explore Command Tests]]
- [[_COMMUNITY_PRD Command Tests|PRD Command Tests]]
- [[_COMMUNITY_CLI Architecture Migration|CLI Architecture Migration]]
- [[_COMMUNITY_Research Command Tests|Research Command Tests]]
- [[_COMMUNITY_Shard Command Tests|Shard Command Tests]]
- [[_COMMUNITY_ISS-007 Backward Compat|ISS-007 Backward Compat]]
- [[_COMMUNITY_Test Fixtures|Test Fixtures]]
- [[_COMMUNITY_Streaming Pipeline Monitor|Streaming Pipeline Monitor]]
- [[_COMMUNITY_OpenCode Plugin Config|OpenCode Plugin Config]]
- [[_COMMUNITY_Plugin Package Config|Plugin Package Config]]
- [[_COMMUNITY_Codebase Index Config|Codebase Index Config]]
- [[_COMMUNITY_Workstation Mapping|Workstation Mapping]]
- [[_COMMUNITY_Definition of Done|Definition of Done]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]

## God Nodes (most connected - your core abstractions)
1. `id_to_key` - 500 edges
2. `chdir()` - 81 edges
3. `SessionState` - 61 edges
4. `IssueRecord` - 39 edges
5. `TaskRecord` - 21 edges
6. `TransitionViolationError` - 20 edges
7. `datetime` - 19 edges
8. `Path` - 18 edges
9. `resolve_issue_record()` - 18 edges
10. `_specify_pre()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `TestDeviateConfig` --uses--> `TransitionViolationError`  [INFERRED]
  tests/test_state/test_config.py → src/deviate/state/config.py
- `TestSessionState` --uses--> `TransitionViolationError`  [INFERRED]
  tests/test_state/test_config.py → src/deviate/state/config.py
- `TestDualModePhaseOrdering` --uses--> `TransitionViolationError`  [INFERRED]
  tests/test_state/test_session.py → src/deviate/state/config.py
- `TestFilesystemDivergence` --uses--> `TransitionViolationError`  [INFERRED]
  tests/test_state/test_session.py → src/deviate/state/config.py
- `TestSessionPersistence` --uses--> `TransitionViolationError`  [INFERRED]
  tests/test_state/test_session.py → src/deviate/state/config.py

## Import Cycles
- 1-file cycle: `src/deviate/state/ledger.py -> src/deviate/state/ledger.py`

## Hyperedges (group relationships)
- **TDD Micro-Cycle (Red → Green → Judge → Refactor)** — agents_red_phase, agents_green_phase, agents_judge_phase, agents_refactor_phase [EXTRACTED 1.00]
- **HITL Gate System (3 Human-in-the-Loop Approval Gates)** — agents_hitl_gate_1, agents_hitl_gate_2, agents_hitl_gate_3 [EXTRACTED 1.00]
- **Full DeviaTDD Pipeline DAG** — agents_explore_phase, agents_research_phase, agents_prd_phase, agents_shard_phase, agents_specify_phase, agents_tasks_phase, agents_red_phase, agents_green_phase, agents_refactor_phase, agents_e2e_phase [EXTRACTED 1.00]
- **DeviaTDD Three-Layer Architecture** — deviatdd_macro_meso_micro_architecture, deviatdd_rgr_tdd_cycle, deviatdd_gherkin_acceptance_criteria, deviatdd_constitutional_governance, deviatdd_hitl_gates, deviatdd_vertical_slicing, deviatdd_pre_post_script_pattern, deviatdd_sociable_unit_testing, deviatdd_jsonl_issue_ledger [INFERRED 0.85]
- **ISS-001 Init Implementation Cycle (PR-003/005/007 + Spec + Tasks)** — pr_descriptions_feat_001_deviate_cli_python_003_meso_layer_specification_task_decomposition, pr_descriptions_feat_001_deviate_cli_python_005_cli_architecture_realignment_skill_integration, pr_descriptions_feat_001_deviate_cli_python_007_macro_meso_parity_backward_compatibility, 001_cli_initialization_governance_provisioning_spec, 001_cli_initialization_governance_provisioning_tasks [EXTRACTED 1.00]
- **001-deviate-cli-python Epic Issue Collection** — issues_iss001, issues_iss002, issues_iss003, issues_iss004, issues_iss005, issues_iss006, issues_iss007, issues_iss008, issues_iss009 [EXTRACTED 1.00]
- **DeviaTDD Three-Layer Architecture** — macro_layer, meso_layer, micro_layer, domain_driven_subapps [EXTRACTED 1.00]
- **DeviaTDD Three-Layer Architecture** — specs_deviatdd_architecture_macro_layer, specs_deviatdd_architecture_meso_layer, specs_deviatdd_architecture_micro_layer [EXTRACTED 1.00]
- **DeviaTDD Macro Layer Pipeline Skills** — deviate_explore_skill_skill, deviate_research_skill_skill, deviate_prd_skill_skill, deviate_shard_skill_skill [INFERRED 0.95]
- **DeviaTDD Micro Layer TDD Cycle Skills** — deviate_red_skill_skill, deviate_refactor_skill_skill, deviate_e2e_skill_skill, deviate_prune_skill_skill [INFERRED 0.95]
- **DeviaTDD Pipeline** — deviate_tasks_skill_deviate_tasks, deviate_triage_skill_deviate_triage [INFERRED 0.85]

## Communities (64 total, 9 thin omitted)

### Community 0 - "Vector Index Metadata"
Cohesion: 0.00
Nodes (500): id_to_key, 1, 1001, 1006, 1007, 1008, 1009, 1011 (+492 more)

### Community 1 - "Project Root & Documentation"
Cohesion: 0.01
Nodes (138): /Users/werner/Development/tools/aether/CLAUDE.md, /Users/werner/Development/tools/aether/findings.md, /Users/werner/Development/tools/aether/mise.toml, /Users/werner/Development/tools/aether/pr_descriptions/feat-001-deviate-cli-python-001-cli-initialization-governance-provisioning-pr-11.md, /Users/werner/Development/tools/aether/pr_descriptions/feat-001-deviate-cli-python-003-meso-layer-specification-task-decomposition.md, /Users/werner/Development/tools/aether/pr_descriptions/feat-001-deviate-cli-python-005-cli-architecture-realignment-skill-integration.md, /Users/werner/Development/tools/aether/pr_descriptions/feat-001-deviate-cli-python-007-macro-meso-parity-backward-compatibility.md, /Users/werner/Development/tools/aether/prompts/deviate-adhoc/SKILL.md (+130 more)

### Community 2 - "Core Utility Functions"
Cohesion: 0.10
Nodes (47): _extract_epic_num(), _halt(), _handle_transition_error(), _load_manifest(), Extract the leading numeric prefix from an epic slug.      ``001-deviate-cli-boo, Ensure .githooks/ is configured as hooks path if the directory exists., _run_pre_commit_hooks(), _validate_constitution() (+39 more)

### Community 3 - "Micro Layer TDD Sandbox"
Cohesion: 0.05
Nodes (32): Path, append_issue_record(), append_issue_transition(), _append_record(), append_task_record(), append_task_transition(), _append_with_compound_key(), IssueRecord (+24 more)

### Community 4 - "Session & Config State"
Cohesion: 0.18
Nodes (6): Path, SessionState, _find_source_for(), reconstruct_from_worktree(), SessionState, validate_filesystem_state()

### Community 5 - "Meso Layer Specification"
Cohesion: 0.13
Nodes (42): _extract_issue_num(), _handle_missing_dot_dir(), Extract the numeric suffix from an issue ID.      ``ISS-006`` → ``006``, ``TSK-0, _derive_pr_metadata(), _emit_contract(), _find_spec_md(), _is_issue_completed(), _load_session() (+34 more)

### Community 6 - "Init Scaffold & Governance"
Cohesion: 0.07
Nodes (31): BaseModel, _apply_governance(), _dict_to_toml(), _ensure_dir(), _ensure_gitignore(), _get_agent_skill_dir(), init(), _install_skills_to_agents() (+23 more)

### Community 7 - "Core Contract & Issues"
Cohesion: 0.08
Nodes (22): emit_contract(), load_contract(), claim_issue(), is_issue_completed(), read_issue_body(), resolve_issue(), _resolve_ledger(), datetime (+14 more)

### Community 8 - "DeviaTDD Architecture Specs"
Cohesion: 0.06
Nodes (35): ISS-002 Macro-Layer State & Ledger Management Spec, ISS-002 Implementation Tasks, ISS-003 Meso-Layer Spec, ISS-003 Implementation Tasks, ISS-005 CLI Architecture Realignment & Skill Integration Spec, ISS-005 Implementation Tasks, Append-Only Ledger Protocol, DeviaTDD Three-Layer Architecture (+27 more)

### Community 9 - "Validation Engine"
Cohesion: 0.09
Nodes (12): extract_section_body(), validate_artifact(), validate_gherkin_syntax(), validate_sections(), validate_task_id(), validate_yaml_frontmatter(), TestExtractSectionBody, TestValidateGherkinSyntax (+4 more)

### Community 10 - "Deviate Workflow Skills"
Cohesion: 0.08
Nodes (30): deviate-adhoc Skill, deviate-constitution Skill, deviate-context Skill, deviate-e2e Skill, deviate-execute Skill, deviate-explore Skill, deviate-hotfix Skill, deviate-pr Skill (+22 more)

### Community 11 - "Git Worktree Management"
Cohesion: 0.15
Nodes (17): branch_exists_on_remote(), create_worktree(), detect_remote(), detect_worktree(), find_worktree_for_branch(), Return the worktree path for an existing branch, or None., Remove a worktree and its local branch (best-effort, no-op on failure)., Return the default git remote name, preferring ``origin``. (+9 more)

### Community 12 - "DeviaTDD Workflow Phases"
Cohesion: 0.12
Nodes (24): Ad-Hoc Fast Path, DeviaTDD Spec-Driven Development Workflow, E2E Phase: End-to-End Verification, Explore Phase, GREEN Phase: Implementation, HITL Gate 1: Design Approval, HITL Gate 2: Spec Approval, HITL Gate 3: Merge Approval (+16 more)

### Community 13 - "ISS-001 CLI Bootstrap"
Cohesion: 0.16
Nodes (17): ISS-001 Init: CLI Initialization & Governance Provisioning Spec, ISS-001 Init: Task Decomposition (T001-T004), Bash-to-Python Migration (8K-Line Bash Removal), Constitutional Governance (specs/constitution.md), Macro-Meso JSON Contract Field Parity, Gherkin Given/When/Then Acceptance Criteria, Human-in-the-Loop Approval Gates (1/2/3), Idempotent Governance Provisioning (+9 more)

### Community 14 - "Constitution Governance"
Cohesion: 0.22
Nodes (8): extract_commands(), resolve_constitution(), validate_constitution(), Path, TestExtractCommands, TestResolveConstitution, TestValidateConstitution, Path

### Community 15 - "Init Integration Tests"
Cohesion: 0.18
Nodes (10): MonkeyPatch, US-006-INIT Scenario 4: contract handoff defaults to .deviate/session.json., T007: Wire agent detection, skill installation, and contract handoff into deviat, US-005-SKILLS Scenario 2: SKILL.md copied to detected agent paths., US-005-SKILLS Scenario 3: skip when content matches., US-005-SKILLS Scenario 4: overwrite when content differs., US-006-INIT Scenario 1: auto-detect agents from cwd directories., US-006-INIT Scenario 2: --agent flag overrides auto-detection. (+2 more)

### Community 16 - "Specify Command Tests"
Cohesion: 0.34
Nodes (6): _make_issue_record(), TestSpecifyCommand, TestSpecifyPreSubcommand, _write_ledger(), IssueRecord, Path

### Community 17 - "Git Commit Module"
Cohesion: 0.21
Nodes (9): commit_artifact(), stage_and_commit(), Path, TestCommitArtifact, TestStageAndCommit, _git_env(), Path, tmp_git_repo() (+1 more)

### Community 18 - "Manifest T001 Migration"
Cohesion: 0.14
Nodes (13): commit_body, commit_subject, files_modified, reasoning, approach, key_decisions, task_id, validation (+5 more)

### Community 19 - "Manifest T002 Migration"
Cohesion: 0.14
Nodes (13): commit_body, commit_subject, files_modified, reasoning, approach, key_decisions, task_id, validation (+5 more)

### Community 20 - "Manifest T004 Migration"
Cohesion: 0.14
Nodes (13): commit_body, commit_subject, files_modified, reasoning, approach, key_decisions, task_id, validation (+5 more)

### Community 21 - "Bash Parity Tests"
Cohesion: 0.37
Nodes (10): CompletedProcess, _find_bash_scripts(), _git_env(), _init_git_repo(), _install_deviate(), _parse_json_contract(), _run_bash(), _run_python() (+2 more)

### Community 22 - "Git Repo Detection"
Cohesion: 0.27
Nodes (6): find_repo_root(), gather_git_state(), Path, TestFindRepoRoot, TestGatherGitState, Path

### Community 23 - "Macro Contract Tests"
Cohesion: 0.46
Nodes (3): _git_env(), TestMacroContracts, Path

### Community 24 - "Task Run Command Tests"
Cohesion: 0.11
Nodes (18): DeviaTDD Phase Architecture, ⚡ Fast-Lane Execution Contract, Fast-Path, 🔐 Git Commit Authority (MANDATORY), graphify, HITL Gates, Macro Layer — Feature Scoping, Meso Layer — Issue Engineering (+10 more)

### Community 25 - "Meso Contract Tests"
Cohesion: 0.47
Nodes (3): _git_env(), TestMesoContracts, Path

### Community 26 - "Init Export Cycle Tests"
Cohesion: 0.23
Nodes (5): TestInitCommand, chdir(), TestFullInitCycle, Path, Path

### Community 27 - "Pydantic Data Models"
Cohesion: 0.22
Nodes (10): Data Model Document, Architecture Design Document, Exploration Report, Product Requirements Document, AgentConfig Pydantic Model, DeviateConfig Pydantic Model (TOML), IssueRecord Pydantic Model (JSONL), SessionState Pydantic Model (JSON) (+2 more)

### Community 28 - "PRD Extraction Module"
Cohesion: 0.28
Nodes (4): extract_prd_requirements(), Path, TestExtractPrdRequirements, Path

### Community 29 - "Task Decomposition Skills"
Cohesion: 0.25
Nodes (9): Autonomous R-G-R Mandate, Deviate Tasks Skill, Execution Mode Decision Tree, Specify → Tasks → TDD Pipeline, Workflow Classification Schema, Decision Matrix, Decision Predicates, Deviate Triage Skill (+1 more)

### Community 30 - "Init Command Tests"
Cohesion: 0.31
Nodes (16): _append_status_transition(), _dispatch_task(), _find_all_pending_tasks(), _find_task_record(), Run dispatcher: route task by execution_mode to TDD cycle or execute phase., Append a status-transition entry for a task.      Creates a new TaskRecord with, _read_ledger_records(), _resolve_issue_number() (+8 more)

### Community 33 - "CLI Architecture Migration"
Cohesion: 0.29
Nodes (7): CLI Architecture Migration Plan, Core Contract Module (deviate/core/contract.py), Core Ledger Module (deviate/core/ledger.py), Core Skills Module (deviate/core/skills.py), Core Worktree Module (deviate/core/worktree.py), IssueRecord Model Mismatch with JSONL Schema, Malformed JSON in issues.jsonl Line 10

### Community 36 - "ISS-007 Backward Compat"
Cohesion: 0.33
Nodes (6): ISS-007 Macro/Meso Parity & Backward Compatibility Spec, ISS-007 Implementation Tasks, Content Validation Engine for Post-Commands, Contract Field Parity with Bash Originals, FR-007 Macro/Meso Parity & Backward Compatibility, ISS-007 Macro/Meso Parity & Backward Compatibility

### Community 37 - "Test Fixtures"
Cohesion: 0.13
Nodes (4): TestDualModePhaseOrdering, TestTaskIdNormalization, TestTransitionViolations, TestValidTransitions

### Community 38 - "Streaming Pipeline Monitor"
Cohesion: 0.67
Nodes (3): FR-ADHOC-001: Streaming Pipeline Monitor, ISS-011: Streaming Pipeline Monitor, OrchestrationMonitor

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (5): TestExplorePre, TestPrdPost, TestResearchPre, TestShardPost, Path

### Community 60 - "Community 60"
Cohesion: 0.27
Nodes (6): _git_env(), TestPrRun, TestSpecifyPost, TestSpecifyPre, TestTasksPre, Path

### Community 61 - "Community 61"
Cohesion: 0.21
Nodes (4): TestFilesystemDivergence, TestSessionPersistence, TestSessionReconstruction, Path

### Community 62 - "Community 62"
Cohesion: 0.47
Nodes (5): _make_issue_record(), TestTasksCommand, _write_ledger(), IssueRecord, Path

### Community 63 - "Community 63"
Cohesion: 0.57
Nodes (3): scaffold_artifacts(), TestMacroFullCycle, Path

## Knowledge Gaps
- **753 isolated node(s):** `$schema`, `plugin`, `⚙️ Project Execution Contract (MANDATORY)`, `🧠 State & Authority Model (MANDATORY)`, `⚡ Fast-Lane Execution Contract` (+748 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SessionState` connect `Session & Config State` to `PRD Command Tests`, `Core Utility Functions`, `Micro Layer TDD Sandbox`, `Research Command Tests`, `Meso Layer Specification`, `Init Scaffold & Governance`, `Shard Command Tests`, `Test Fixtures`, `Core Contract & Issues`, `Explore Command Tests`, `Specify Command Tests`, `Community 59`, `Community 60`, `Community 61`, `Community 62`, `Community 63`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `IssueRecord` connect `Micro Layer TDD Sandbox` to `Core Utility Functions`, `Meso Layer Specification`, `Init Scaffold & Governance`, `Core Contract & Issues`, `Specify Command Tests`, `Community 60`, `Community 62`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 72 inferred relationships involving `chdir()` (e.g. with `.test_init_appends_governance_to_nonexistent_file()` and `.test_init_creates_constitution()`) actually correct?**
  _`chdir()` has 72 INFERRED edges - model-reasoned connections that need verification._
- **Are the 50 inferred relationships involving `SessionState` (e.g. with `Match` and `Path`) actually correct?**
  _`SessionState` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `IssueRecord` (e.g. with `Path` and `SessionState`) actually correct?**
  _`IssueRecord` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `TaskRecord` (e.g. with `Console` and `IssueRecord`) actually correct?**
  _`TaskRecord` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `⚙️ Project Execution Contract (MANDATORY)` to the rest of the system?**
  _807 weakly-connected nodes found - possible documentation gaps or missing edges._