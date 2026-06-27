---
title: "Content Capture Subsystem — YAML Phase Handover Persistence (FLOW-11) and Synthesis (FLOW-12)"
labels: [enhancement, adhoc, vertical-slice, content-capture, handover, synthesis]
blocked_by: []
coordinates_with: []
issue_id: ISS-ADH-012
flow_refs: [FLOW-11, FLOW-12]
---

## System Topology Mapping
- **Epic Target Domain**: `specs/_product/` (Content Capture artifacts already present: `architecture.md` C8/C9/C10, `flows/flows-content-capture.md` FLOW-11/FLOW-12, `release-next.md` 16 acceptance criteria)
- **Local Issue File**: `specs/adhoc/issues/012-deviate-content.md`
- **Primary Architectural Workstations**:
  - `src/deviate/core/handover.py` — NEW: helper module exposing `handover_path()`, `persist_handover()`, `load_handover_records()`, and read-side `HandoverRecord` Pydantic model (no write-side persistence model per `specs/plans/deviate-content.md:92`)
  - `src/deviate/cli/content.py` — NEW: Typer sub-app with `pre|post` commands plus `--format`, `--window`, `--slug`, `--archive` flags (per `specs/_product/flows/flows-content-capture.md:43-46`)
  - `src/deviate/prompts/skills/deviate-content/SKILL.md` — NEW: macro-layer synthesis skill (matches existing `deviate-*` shape, follows `deviate-constitution` frontmatter schema)
  - `src/deviate/prompts/content/blog.md` — NEW: blog format template
  - `src/deviate/prompts/content/x-thread.md` — NEW: X-thread format template
  - `src/deviate/prompts/content/release-notes.md` — NEW: release-notes format template
  - `src/deviate/prompts/content/commit-story.md` — NEW: commit-story format template
  - `src/deviate/prompts/content/resume-bullet.md` — NEW: resume-bullet format template
  - `.deviate/.gitignore` — extend with `/feat/` and `/content-drafts/` entries (currently excludes `session.json`, `artifacts/`, `prompts.log`, `reports/`, `rollback.jsonl`, `logs/`)
  - `src/deviate/cli/__init__.py:594-619` — extend the 23-entry `cli.add_typer(...)` block with `cli.add_typer(content_app, name="content")` (registration line only; no existing code modified)
  - 15 existing SKILL.md files — append a one-sentence Write instruction to the `<output_format_schemas>` block (or equivalent terminal-contract section) of each: `deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`, `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks`
  - `tests/test_handover/test_path_resolution.py` — NEW: macro/micro path shape tests
  - `tests/test_handover/test_persist_manual_path.py` — NEW: actor Write → file present + valid YAML + not in git index
  - `tests/test_handover/test_persist_cli_path.py` — NEW: actor stdout → runner writes file from captured manifest
  - `tests/test_handover/test_idempotent_write.py` — NEW: double write identical content → single file, no errors
  - `tests/test_content/test_load_records.py` — NEW: fixture YAML directory → chronological list
  - `tests/test_content/test_blog_format.py` — NEW: fixture with `verdict_story` anchor → draft opens referencing it
  - `tests/test_content/test_x_thread_format.py` — NEW: anchor pool → 6-post thread
  - `tests/test_content/test_window_filter.py` — NEW: `--window EPIC-X` filters to that epic only
  - `tests/test_content/test_archive_flag.py` — NEW: `--archive EPIC-X` produces `specs/_archives/<epic>-narrative.tar.gz`
- **Upstream Evidence**:
  - `specs/explore/deviate-content.md` — Source explore scan (Status: SUCCESS, Complexity: High, Files Likely Modified: 17 + 8 new)
  - `specs/plans/deviate-content.md` — 207-line plan declaring Context, Design (path convention, narrative anchor field, persistence flow), 15-skill File changes, 2-task decomposition, Risks, Out-of-scope v1
  - `specs/_product/release-next.md` — 16 acceptance criteria for the Content Capture release (lines 39-54)
  - `specs/_product/architecture.md` — Components C8 (Handover Capture, FLOW-11), C9 (Content Synthesis, FLOW-12), C10 (Format Template Pack, FLOW-12) at lines 42-44; integration contracts §3.5-§3.7 lines 129-179; example YAML with `narrative_anchor:` at line 224
  - `specs/_product/flows/flows-content-capture.md` — FLOW-11 (Capture Phase Handover) and FLOW-12 (Synthesize Content Digest) with full Actor/Domain/Status/Problem/Trigger/Preconditions/Happy Path/Alternate/Success State shape
  - `specs/_product/flows/index.md` — 12-flow catalog with FLOW-11 and FLOW-12 marked Draft under Content Capture domain
  - `src/deviate/core/agent.py:21-32` — Existing `HandoverManifest` Pydantic schema with `model_config = {"extra": "allow"}` (forward-compatible with `narrative_anchor:` block)
  - `src/deviate/cli/macro.py:195-275` — Established pre/post dual Typer sub-app pattern (`explore_app` + `@explore_app.command("pre")` + `@explore_app.command("post")`)
  - `src/deviate/cli/_common.py` — Shared CLI utilities (`console`, `with_json_quiet` decorator) imported by the new `cli/content.py`
  - `tests/conftest.py` — `_git_env()` (strips `GIT_*` env vars) and `tmp_git_repo` fixture reused by all 9 new tests
  - `specs/adhoc/prd.md` §`FR-ADHOC-012` — Appended functional requirement with AC-ADHOC-012-01 through AC-ADHOC-012-16

## The Problem Contract
The Content Capture subsystem is the durable, queryable phase-output layer that lets a developer turn ephemeral DeviaTDD phase output (LLM stdout, skill artifacts, git log) into marketing-content drafts — blog posts, X threads, release notes, commit stories, resume bullets — without re-reading raw phase output. The release plan at `specs/_product/release-next.md` mandates FLOW-11 (per-phase YAML handover persistence at `.deviate/feat/<epic>/<issue>/[<task>/]<phase>.yaml`) and FLOW-12 (synthesis CLI sub-app + macro skill + 5 format templates) as the single in-flight release slice. v1 deliberately rejects three abstractions: (1) `specs/narrative.jsonl` or any append-only narrative ledger (per `specs/plans/deviate-content.md:13-15` — "YAML files ARE the ledger"); (2) a write-side `HandoverRecord` Pydantic model (read-side only, per `specs/plans/deviate-content.md:92`); (3) git commits on handover YAMLs (`.deviate/feat/**` and `.deviate/content-drafts/**` are gitignored runtime state, per `specs/plans/deviate-content.md:17-19`). The skill actor writes via Write tool to the canonical path (manual path) or via stdout (CLI path where the runner parses and writes); absence of `narrative_anchor:` on any YAML is non-fatal and synthesis falls back to `phase` + `status` + `files` + git-log metadata. The runner's `persist_handover()` helper is the single integration point called from each phase post-handler and is gated by an idempotent overwrite-or-skip contract — re-invocation with identical content is a no-op, divergent content is a real failure surfaced by git log diff (not by the YAML layer). The `deviate-content` macro skill plus 5 format templates form the FLOW-12 surface; each format template is a static Markdown file under `src/deviate/prompts/content/` loaded by the synthesis layer. The single coherent release slice is "capture + synthesize" — all four new Python files (`src/deviate/core/handover.py`, `src/deviate/cli/content.py`, the synthesis helper), the new macro skill, the 5 format templates, the 15 one-sentence skill-prompt appends, the `.gitignore` extension, and the 9 new pytest tests ship together.

## Scope Boundaries
### Hard Inclusions
- Create `src/deviate/core/handover.py` exporting `handover_path(epic_slug, issue_id, phase, task_id=None) -> Path`, `persist_handover(epic_slug, issue_id, phase, manifest, task_id=None) -> Path`, `load_handover_records(window) -> list[HandoverRecord]`, and a read-side `HandoverRecord` Pydantic model. `handover_path()` returns `.deviate/feat/<epic_slug>/<issue_id>/<phase>.yaml` for macro and `.deviate/feat/<epic_slug>/<issue_id>/<task_id>/<phase>.yaml` for micro. `persist_handover()` writes the YAML only when the file is absent (idempotent overwrite-or-skip). Both `handover_path()` and `persist_handover()` reject any path escaping `.deviate/feat/` via `pathlib` and raise `PathTraversalError` (or equivalent diagnostic). `load_handover_records(window)` skips malformed YAMLs with a stderr warning and returns valid records in chronological order. Source: `specs/_product/architecture.md:42,129-179` + `specs/plans/deviate-content.md:92`.
- Create `src/deviate/cli/content.py` as a Typer sub-app `content_app = typer.Typer(no_args_is_help=True, help="Content Capture commands")` with `@content_app.command("pre")` and `@content_app.command("post")` plus the optional flags `--format <blog|x-thread|release-notes|commit-story|resume-bullet>`, `--window EPIC-X`, `--slug S`, `--archive EPIC-X`. Register it via `cli.add_typer(content_app, name="content")` in `src/deviate/cli/__init__.py` (extending the 23-entry `cli.add_typer(...)` block at lines 594-619 — registration line only). Source: `specs/_product/flows/flows-content-capture.md:43-46` + `specs/plans/deviate-content.md:94`.
- Create `src/deviate/prompts/skills/deviate-content/SKILL.md` with canonical frontmatter (`name: deviate-content`, `description:` describing FLOW-12 synthesis behavior, `category: deviatdd-macro-layer`, `version: 1.0.0`, `aliases: [/deviate-content, spec:deviate-content]`). Body inlines the 5 supported formats (blog, x-thread, release-notes, commit-story, resume-bullet), the synthesis contract (loads handovers via `load_handover_records()`, renders via the format template, writes draft to `.deviate/content-drafts/<format>/<slug>.md`), and the anchor-fallback rule (absence of `narrative_anchor:` on any record → fall back to `phase` + `status` + `files` + git-log metadata). Source: `specs/_product/architecture.md:42-44` + `specs/_product/flows/flows-content-capture.md:1-79`.
- Create 5 format templates at `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md`. Each template is a static Markdown file with `{{ }}`-style placeholders (or equivalent string-substitution markers) consumed by the synthesis helper. The blog template references at least one `narrative_anchor` from the `judge` phase (`verdict_story`); the x-thread template slices the anchor pool into exactly 6 posts of ≤ 280 characters each. Source: `specs/_product/architecture.md:44` + `specs/plans/deviate-content.md:90-99,138,140`.
- Extend `.deviate/.gitignore` with the entries `/feat/` and `/content-drafts/`. The file currently excludes `session.json`, `artifacts/`, `prompts.log`, `reports/`, `rollback.jsonl`, `logs/`; the additions are append-only. Source: `specs/plans/deviate-content.md:17-19,83-87`.
- Append a one-sentence Write instruction to the `<output_format_schemas>` block (or equivalent terminal-contract section) of each of the 15 listed skills: `deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`, `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks`. The instruction references the canonical `handover_path()` target (e.g. "After emitting the YAML manifest, call the Write tool to persist it at `.deviate/feat/<epic>/<issue>/[<task>/]<phase>.yaml`."). The instruction is append-only — no existing content modified. Source: `specs/plans/deviate-content.md:79-87`.
- Add 9 new pytest tests under `tests/test_handover/` (4 tests) and `tests/test_content/` (5 tests), matching the task decomposition at `specs/plans/deviate-content.md:104-150`: `test_path_resolution`, `test_persist_manual_path`, `test_persist_cli_path`, `test_idempotent_write`, `test_load_records`, `test_blog_format`, `test_x_thread_format`, `test_window_filter`, `test_archive_flag`. All 9 tests use the `tmp_git_repo` fixture and `_git_env()` helper from `tests/conftest.py`; tests that exercise CLI commands which internally call `_run_pytest` MUST mock `deviate.cli.micro._run_pytest` per the AGENTS.md mandate.
- Verify end-to-end: a single DeviaTDD task (RED → GREEN → JUDGE → REFACTOR) running against a temp git repo produces `.deviate/feat/<epic>/<issue>/<task>/{red,green,judge,refactor}.yaml`, all four files parse as valid YAML, present on disk, and NOT staged in the git index (verified via `git ls-files --error-unmatch`).

### Defensive Exclusions
- Do NOT create `specs/narrative.jsonl` or any append-only narrative ledger. v1 explicitly rejects this abstraction per `specs/plans/deviate-content.md:13-15`. The YAML manifest under `.deviate/feat/` is the durable artifact and is re-emittable from skills if lost.
- Do NOT export a write-side `HandoverRecord` Pydantic model from `src/deviate/core/handover.py`. The model is read-side only, used by `load_handover_records()` to deserialize YAMLs into structured records for synthesis. The write path is a raw `yaml.safe_dump` from the actor's manifest string. Source: `specs/plans/deviate-content.md:92`.
- Do NOT commit any handover YAML or content draft to git. `.deviate/feat/**` and `.deviate/content-drafts/**` are gitignored runtime state per `specs/plans/deviate-content.md:17-19`. The only committed-by-default artifact is `specs/_archives/<epic_slug>-narrative.tar.gz` when `--archive` is invoked.
- Do NOT add `jinja2` to `pyproject.toml`. The synthesis layer uses plain string `.format()` substitution (or equivalent Python stdlib mechanism) for the 5 format templates — no Jinja2 dependency. If a future iteration requires Jinja2, that is a separate dependency-addition issue.
- Do NOT add a `deviate content run` or any direct execution subcommand. v1 exposes `pre|post` only — the `pre|post` pattern matches `src/deviate/cli/macro.py:195-275` and is the established convention.
- Do NOT auto-publish synthesis drafts to X / blog / release notes / etc. Synthesis produces drafts only; the developer reviews, edits, and publishes manually per `specs/_product/flows/flows-content-capture.md:78-79` and `specs/plans/deviate-content.md:200`.
- Do NOT implement cross-repo aggregation queries. v1 is single-repo only per `specs/plans/deviate-content.md:202`.
- Do NOT add engagement metrics on published content. Out of scope v1 per `specs/plans/deviate-content.md:203`.
- Do NOT implement an LLM-driven content refinement `--refine` flag. Template-based v1 only; `--refine` is a future iteration per `specs/plans/deviate-content.md:201`.
- Do NOT engage with the existing `tome-*` skills (Diátaxis-quadrant classification of blog content). Orthogonal in v1 per `specs/plans/deviate-content.md:204`.
- Do NOT modify `src/deviate/cli/__init__.py` beyond the single `cli.add_typer(content_app, name="content")` registration line. The existing 23-entry `cli.add_typer(...)` block at lines 594-619 grows to 24 entries; no existing code is touched.
- Do NOT modify `src/deviate/core/agent.py:21-32` (the existing `HandoverManifest` schema). Its `model_config = {"extra": "allow"}` is already forward-compatible with the optional `narrative_anchor:` block — no schema change needed.
- Do NOT modify `_VALID_PHASES` (`src/deviate/state/config.py:21-39`) or `_PHASE_ORDER` (`src/deviate/cli/macro.py:747`). Content Capture does not introduce a new DeviaTDD phase; it instruments existing phases with a Write instruction in their skill prompts.
- Do NOT bump the constitution. `specs/constitution.md` remains at v0.2.0; the Append-Only Ledger Protocol note acknowledging Content Capture YAMLs as runtime-state-not-ledger is already recorded at `specs/_product/architecture.md:213`.
- Do NOT modify `specs/DeviaTDD-api.md` or `specs/DeviaTDD-architecture.md`. Product-layer artifacts (`architecture.md`, `flows-content-capture.md`, `release-next.md`) are the source of truth for Content Capture; framework-level architecture docs remain unchanged in v1.
- Do NOT modify the 15 SKILL.md files beyond the one-sentence Write instruction append. No body content of any existing skill is rewritten, restructured, or expanded. The append must be idempotent — re-running the implementation must not duplicate the instruction.

## Upstream Requirement Tracing
- **Requirements Tokens**: `FR-ADHOC-012`
- **Acceptance Criteria Tokens**: `AC-ADHOC-012-01` through `AC-ADHOC-012-16`
- **Data Model Entities** (read-side only): `HandoverRecord` (Pydantic model with `epic_slug`, `issue_id`, `task_id`, `phase`, `status`, `files`, `narrative_anchor: dict | None`, `timestamp`) per `specs/plans/deviate-content.md:92` and `specs/_product/architecture.md:179`
- **Spec Source Anchors**:
  - `specs/_product/release-next.md:39-54` — 16 acceptance criteria for the Content Capture release (mapped 1:1 to AC-ADHOC-012-01 through AC-ADHOC-012-16)
  - `specs/plans/deviate-content.md` — 207-line plan: Context (3 simplifications, lines 5-15), Design (path convention lines 42-49, narrative anchor field lines 52-69, persistence flow lines 64-73), 15-skill Modifications lines 79-87, New files lines 90-99, 2-task decomposition lines 104-150, Risks lines 159-167, Out-of-scope v1 lines 199-204
  - `specs/_product/architecture.md:42-44` — Components C8, C9, C10 declaration
  - `specs/_product/architecture.md:129-179` — §3.5-§3.7 integration contracts
  - `specs/_product/architecture.md:213` — Constitution note acknowledging YAMLs are explicitly NOT a ledger
  - `specs/_product/architecture.md:224` — Example YAML with `narrative_anchor:` block
  - `specs/_product/flows/flows-content-capture.md:1-79` — FLOW-11 + FLOW-12 full happy/alternate paths
  - `src/deviate/core/agent.py:21-32` — Existing `HandoverManifest` with `extra="allow"`
  - `src/deviate/cli/macro.py:195-275` — Established pre/post dual Typer sub-app pattern
  - `src/deviate/cli/__init__.py:594-619` — 23-entry `cli.add_typer(...)` block to extend
  - `tests/conftest.py` — `_git_env()` + `tmp_git_repo` fixture

## User Stories Ledger
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

- **US-012-01**: As a developer running a DeviaTDD phase (e.g. `judge`), I want the skill actor to persist a YAML handover at `.deviate/feat/<epic>/<issue>/[<task>/]<phase>.yaml` via the Write tool so the phase output is durable and queryable for later synthesis, without re-reading the raw LLM stdout. *(Ref: FR-ADHOC-012, FLOW-11)*
- **US-012-02**: As a developer running `deviate explore` (or any macro phase), I want the macro handover to land at `.deviate/feat/<epic>/<issue>/<phase>.yaml` (no task_id segment) so the macro-layer trace is distinguishable from micro-layer task traces. *(Ref: FR-ADHOC-012, FLOW-11, AC-ADHOC-012-03)*
- **US-012-03**: As a developer running a DeviaTDD micro task (RED → GREEN → JUDGE → REFACTOR), I want each phase's handover to land at `.deviate/feat/<epic>/<issue>/<task>/<phase>.yaml` so the per-task trace is recoverable for resume bullets and commit stories. *(Ref: FR-ADHOC-012, FLOW-11, AC-ADHOC-012-03)*
- **US-012-04**: As a developer who re-runs a phase (or runs `deviate <phase> post` twice), I want the second call to be a no-op when the content is identical so accidental re-emission does not overwrite or duplicate the handover. *(Ref: FR-ADHOC-012, FLOW-11, AC-ADHOC-012-04)*
- **US-012-05**: As a security-conscious developer, I want `handover_path()` and `persist_handover()` to reject any path that escapes `.deviate/feat/` so a malicious or buggy actor cannot write YAMLs to `.git/`, `/etc/passwd`, or any other path outside the workspace. *(Ref: FR-ADHOC-012, FLOW-11, AC-ADHOC-012-05)*
- **US-012-06**: As a developer who wants to publish a blog post from a recently merged epic, I want `deviate content --format blog --slug my-post --window EPIC-X` to render a draft at `.deviate/content-drafts/blog/my-post.md` whose opening paragraph references at least one `narrative_anchor` from a `judge` record so I have raw material to edit before publishing. *(Ref: FR-ADHOC-012, FLOW-12, AC-ADHOC-012-10)*
- **US-012-07**: As a developer promoting a release, I want `deviate content --format x-thread --slug thread-1` to slice the same anchor pool into exactly 6 posts (≤ 280 chars each) at `.deviate/content-drafts/x-thread/thread-1.md` so I can paste them directly into X / Twitter without further slicing. *(Ref: FR-ADHOC-012, FLOW-12, AC-ADHOC-012-11)*
- **US-012-08**: As a developer with a large epic containing 40+ handovers, I want `deviate content --window EPIC-X` to filter records to that epic only and `absence-of-window` to include all records so I can choose epic-scoped or repository-wide synthesis. *(Ref: FR-ADHOC-012, FLOW-12, AC-ADHOC-012-08)*
- **US-012-09**: As a developer finishing an epic, I want `deviate content --archive EPIC-X` to produce `specs/_archives/EPIC-X-narrative.tar.gz` containing every YAML under that epic so the only committed-by-default artifact of the system is durable in git history. *(Ref: FR-ADHOC-012, FLOW-12, AC-ADHOC-012-09)*
- **US-012-10**: As a developer encountering a malformed YAML in `.deviate/feat/`, I want `load_handover_records()` to skip it with a stderr warning and continue so a single corrupt file does not block synthesis across the entire repository. *(Ref: FR-ADHOC-012, FLOW-12, AC-ADHOC-012-12)*
- **US-012-11**: As a DeviaTDD maintainer reviewing a PR that adds a new phase skill, I want the 15 existing phase-related skills to each carry a one-sentence Write instruction referencing the canonical `handover_path()` target so the cross-cutting capture surface is uniform across all phases — and no other skill is touched. *(Ref: FR-ADHOC-012, FLOW-11, AC-ADHOC-012-13)*
- **US-012-12**: As a developer who wants to keep `.deviate/feat/` and `.deviate/content-drafts/` out of git, I want `.deviate/.gitignore` to exclude `/feat/` and `/content-drafts/` so `git ls-files .deviate/feat/` returns empty after any phase completes. *(Ref: FR-ADHOC-012, FLOW-11, AC-ADHOC-012-14)*

## ATDD Acceptance Criteria
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

**Scenario 012-01**: `handover_path()` returns macro and micro paths correctly
**Given** the path convention at `specs/plans/deviate-content.md:44-45` and `specs/_product/architecture.md:179`
**When** `handover_path("EPIC-X", "ISS-001", "explore")` and `handover_path("EPIC-X", "ISS-001", "red", task_id="T-001")` are called
**Then** the macro result equals `Path(".deviate/feat/EPIC-X/ISS-001/explore.yaml")` and the micro result equals `Path(".deviate/feat/EPIC-X/ISS-001/T-001/red.yaml")` — verifying AC-ADHOC-012-03.

**Scenario 012-02**: `persist_handover()` writes YAML on manual path
**Given** an actor-emitted manifest string and an empty `.deviate/feat/` in a temp git repo
**When** `persist_handover("EPIC-X", "ISS-001", "red", manifest_yaml, task_id="T-001")` is called from a simulated skill Write tool
**Then** `.deviate/feat/EPIC-X/ISS-001/T-001/red.yaml` exists, parses as valid YAML via `yaml.safe_load`, contains the expected fields, and `git ls-files --error-unmatch .deviate/feat/EPIC-X/ISS-001/T-001/red.yaml` returns non-zero (not staged) — verifying AC-ADHOC-012-02, AC-ADHOC-012-04, AC-ADHOC-012-15.

**Scenario 012-03**: `persist_handover()` writes YAML on CLI path from captured stdout
**Given** an actor that emits YAML to stdout (no Write tool call) and a captured manifest string in the CLI context
**When** `persist_handover()` is invoked with the captured manifest
**Then** the file lands at the canonical `.deviate/feat/...` path, parses as valid YAML, and the test exits 0 — verifying AC-ADHOC-012-02.

**Scenario 012-04**: Double write with identical content is idempotent
**Given** `persist_handover()` is called once with manifest M for `(EPIC-X, ISS-001, red, T-001)`
**When** it is called a second time with the same manifest M and same coordinates
**Then** only one file exists, both calls return the same `Path`, and no exception is raised — verifying AC-ADHOC-012-04.

**Scenario 012-05**: Path traversal rejected
**Given** a path that escapes `.deviate/feat/` (e.g. `../etc/passwd`, `/tmp/foo`, a symlink pointing outside the workspace)
**When** `handover_path("..", "ISS-001", "red")` or `handover_path(epic_slug="EPIC-X", issue_id="ISS-001", phase="red")` with `task_id="../../etc/passwd"` is called, OR a manifest is written to a symlinked path escaping `.deviate/feat/`
**Then** `PathTraversalError` (or equivalent diagnostic exception) is raised before any filesystem write — verifying AC-ADHOC-012-05.

**Scenario 012-06**: `deviate content` sub-app advertises expected subcommands and flags
**Given** the new Typer sub-app at `src/deviate/cli/content.py`
**When** `deviate content --help` runs (with `runner.invoke` against the CLI runner)
**Then** the help text shows `pre|post` subcommands and the optional flags `--format`, `--window`, `--slug`, `--archive` — verifying AC-ADHOC-012-06.

**Scenario 012-07**: Unknown `--format` value exits non-zero with diagnostic
**Given** `deviate content --format bogus`
**When** the command runs
**Then** exit code is non-zero, stderr lists the 5 valid format values (`blog`, `x-thread`, `release-notes`, `commit-story`, `resume-bullet`), and no draft file is created under `.deviate/content-drafts/` — verifying AC-ADHOC-012-07.

**Scenario 012-08**: `--window EPIC-X` filters records to that epic only
**Given** fixture YAMLs under `.deviate/feat/EPIC-A/**`, `.deviate/feat/EPIC-B/**`, and `.deviate/feat/EPIC-X/**`
**When** `load_handover_records(window="EPIC-X")` is called
**Then** the returned list contains only records under `.deviate/feat/EPIC-X/**`; absence of `window` returns all records in chronological order — verifying AC-ADHOC-012-08.

**Scenario 012-09**: `--archive EPIC-X` produces tarball at canonical path
**Given** fixture YAMLs under `.deviate/feat/EPIC-X/**`
**When** `deviate content --archive EPIC-X` runs
**Then** `specs/_archives/EPIC-X-narrative.tar.gz` exists, contains every YAML under that epic, and is the only committed-by-default artifact — verifying AC-ADHOC-012-09.

**Scenario 012-10**: Blog format draft references `verdict_story` anchor
**Given** fixture YAMLs including a `judge` record with a `narrative_anchor.verdict_story` field
**When** `deviate content --format blog --slug my-post` runs against the fixture window
**Then** `.deviate/content-drafts/blog/my-post.md` is written, parses as valid Markdown, and its opening paragraph contains the `verdict_story` text — verifying AC-ADHOC-012-10.

**Scenario 012-11**: X-thread format draft contains exactly 6 posts
**Given** fixture YAMLs with anchor fields across multiple phases
**When** `deviate content --format x-thread --slug thread-1` runs
**Then** `.deviate/content-drafts/x-thread/thread-1.md` contains exactly 6 posts, each ≤ 280 characters, sliced from the anchor pool — verifying AC-ADHOC-012-11.

**Scenario 012-12**: Malformed YAML skipped with warning
**Given** a fixture directory containing one valid YAML and one malformed YAML (e.g. unclosed string)
**When** `load_handover_records()` runs against the fixture
**Then** the malformed record is skipped, a warning is logged to stderr (captured via `capsys`), and the returned list contains the valid records only — verifying AC-ADHOC-012-12.

**Scenario 012-13**: 15 existing skill prompts carry the Write instruction
**Given** the canonical skill list at `specs/plans/deviate-content.md:79-87` (`deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`, `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks`)
**When** each `src/deviate/prompts/skills/<name>/SKILL.md` is read post-implementation
**Then** each contains a one-sentence Write instruction referencing the canonical `handover_path()` target (e.g. "After emitting the YAML manifest, call Write to persist it at `.deviate/feat/<epic>/<issue>/[<task>/]<phase>.yaml`."); a unit test (`tests/test_handover/test_skill_prompts.py` or appended to an existing test file) iterates over the 15 names and asserts the instruction is present in each — verifying AC-ADHOC-012-13.

**Scenario 012-14**: `.deviate/.gitignore` excludes `/feat/` and `/content-drafts/`
**Given** the existing `.deviate/.gitignore`
**When** the file is read post-implementation
**Then** it contains the entries `/feat/` and `/content-drafts/`; a unit test (`tests/test_handover/test_gitignore.py` or appended to existing test file) asserts both entries are present — verifying AC-ADHOC-012-14.

**Scenario 012-15**: End-to-end TDD task produces 4 YAMLs not staged in git
**Given** a temp git repo with `deviate setup` complete and the `tmp_git_repo` fixture initialized
**When** a simulated RED → GREEN → JUDGE → REFACTOR sequence runs against fixture epic `EPIC-X`, issue `ISS-001`, task `T-001`
**Then** `.deviate/feat/EPIC-X/ISS-001/T-001/{red,green,judge,refactor}.yaml` all exist, parse as valid YAML, and `git ls-files --error-unmatch` returns non-zero for each — verifying AC-ADHOC-012-15.

**Scenario 012-16**: Constitution note honored — no `specs/narrative.jsonl` exists
**Given** the Constitution §1 Append-Only Ledger Protocol note at `specs/_product/architecture.md:213` explicitly stating Content Capture YAMLs are NOT a ledger
**When** `git ls-files specs/narrative.jsonl` runs post-implementation
**Then** no such file is tracked (or any other append-only narrative ledger variant); `.deviate/.gitignore` is confirmed to exclude `/feat/` and `/content-drafts/` (idempotent with Scenario 012-14); a unit test (`tests/test_handover/test_no_narrative_ledger.py` or equivalent) asserts `not (specs / "narrative.jsonl").exists()` — verifying AC-ADHOC-012-16.

## Edge Cases and Boundaries
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

- **Missing `narrative_anchor:` block**: A YAML manifest from a phase whose skill has not yet been updated (or whose actor omitted the block) must still load cleanly. `HandoverRecord.narrative_anchor` defaults to `None`; `load_handover_records()` returns the record; `synthesize_draft()` falls back to `phase` + `status` + `files` + git-log metadata. Per `specs/plans/deviate-content.md:68-69` and `specs/_product/flows/flows-content-capture.md:56`.
- **All records missing `narrative_anchor:`**: Synthesis still produces a structurally valid draft but with reduced narrative richness. The x-thread format may produce fewer than 6 posts if the anchor pool is too small; behavior is documented in the synthesis helper's docstring, not in user-facing error messages.
- **Empty `.deviate/feat/` directory**: `load_handover_records()` returns an empty list; synthesis CLI exits non-zero with a diagnostic pointing at the window filter per `specs/_product/flows/flows-content-capture.md:58`. No draft is written.
- **Path collision on draft file**: `deviate content --format blog --slug my-post` invoked twice with the same slug → CLI refuses to overwrite without explicit `--force` flag (default: refuse + suggest alternate `--slug`). Per `specs/_product/flows/flows-content-capture.md:64`.
- **Unknown format value**: `deviate content --format bogus` exits non-zero with a diagnostic listing the 5 valid format values. Per `specs/_product/flows/flows-content-capture.md:59` and AC-ADHOC-012-07.
- **`--archive` with no YAMLs under the epic**: CLI exits non-zero; tar is NOT written. Per `specs/_product/flows/flows-content-capture.md:61`.
- **`task_id` containing path traversal characters**: `handover_path()` with `task_id="../../etc/passwd"` raises `PathTraversalError` before constructing the path. Per AC-ADHOC-012-05.
- **YAML with non-string scalar fields**: `HandoverRecord` uses Pydantic with `extra="allow"` to forward-compatibly accept unknown fields. The schema does NOT enforce strict type checking on every field — synthesis tolerates missing or extra keys.
- **YAML with multiple documents (--- separator)**: `yaml.safe_load_all` is used; each document becomes a separate `HandoverRecord`. A `---` separator in the middle of a single manifest is treated as a multi-document stream.
- **`.deviate/feat/` directory missing**: `persist_handover()` creates parent directories via `pathlib.Path.parent.mkdir(parents=True, exist_ok=True)`. `load_handover_records()` returns an empty list when the root directory does not exist.
- **Symlinks inside `.deviate/feat/`**: `pathlib.Path.resolve(strict=False)` is used; if the resolved path escapes `.deviate/feat/`, the path-traversal guard rejects the write. This protects against an attacker creating a symlink in `.deviate/feat/` pointing to `/etc/passwd`.
- **Re-running the implementation against an updated 15-skill list**: The append operation must be idempotent. If a Write instruction is already present in a skill, the implementation must detect it and skip rather than appending a duplicate. Use a deterministic marker (e.g., the literal string "handover_path()") to detect presence.
- **Cross-platform path separators**: `pathlib.Path` is used throughout, which normalizes to `/` on POSIX and `\` on Windows. The `pathlib.PurePosixPath` invariant must hold when comparing canonical paths in tests.
- **YAML emission encoding**: `persist_handover()` writes YAML using `yaml.safe_dump` with `default_flow_style=False` and `allow_unicode=True`. UTF-8 encoding is the default.
- **Concurrent writes**: v1 does not implement file locking. If two phases race to write the same `(epic, issue, phase, task)` tuple, last-writer-wins. Phase uniqueness within a task in DeviaTDD's existing model makes this race impossible in practice.
- **`deviate content` invoked outside a DeviaTDD workspace**: The CLI exits non-zero with a diagnostic stating `.deviate/` is missing; the developer should `deviate init` first. Mirrors the existing behavior of `deviate init` checks elsewhere.

## Performance Constraints
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

- **L_max (single `handover_path()` call)**: ≤ 1ms (pure `pathlib` string manipulation, no I/O)
- **L_max (single `persist_handover()` call)**: ≤ 10ms (filesystem write + `pathlib` parent directory creation in worst case)
- **L_max (`load_handover_records(window=None)` on a 200-YAML repo)**: ≤ 100ms (sequential `yaml.safe_load` + glob)
- **L_max (single `deviate content --format blog` synthesis)**: ≤ 200ms (load records + template render + markdown write)
- **L_max (single `deviate content --archive EPIC-X` tarball)**: ≤ 500ms (Python stdlib `tarfile.open(mode="w:gz")`)
- **Throughput**: Full test suite (`mise run test`) including 9 new tests remains < 18s per AGENTS.md mandate. New tests: 4 in `tests/test_handover/` + 5 in `tests/test_content/` = 9 tests, each expected < 1s (filesystem-bound, no LLM calls).
- **Lint budget**: `mise run lint` reports zero ruff violations on the new modules and tests. Python modules at `src/deviate/core/handover.py` and `src/deviate/cli/content.py` are ruff-scanned; SKILL.md files are Markdown and not ruff-scanned.
- **Format-check budget**: `mise run format-check` reports zero violations on the new Python modules.
- **File size**: `src/deviate/core/handover.py` ≤ 200 lines; `src/deviate/cli/content.py` ≤ 250 lines; each format template ≤ 50 lines; `src/deviate/prompts/skills/deviate-content/SKILL.md` ≤ 150 lines (matches the existing deviate-constitution skill at ~215 lines or shorter — synthesis is template-driven, not deeply reasoned).
- **Idempotency cost**: Re-running `persist_handover()` on an existing file completes in ≤ 5ms (file existence check + early return, no YAML re-parse).
- **15-skill append cost**: Appending one sentence to each of 15 SKILL.md files completes in ≤ 200ms (sequential file appends).
- **Cold `deviate content --help` cost**: ≤ 100ms (Typer sub-app registration + help rendering).

## Multi-Tiered Verification Targets
- **Unit Sandbox Targets**:
  - `tests/test_handover/test_path_resolution.py::test_macro_path_shape` — `handover_path("EPIC-X", "ISS-001", "explore")` returns expected path
  - `tests/test_handover/test_path_resolution.py::test_micro_path_shape` — `handover_path("EPIC-X", "ISS-001", "red", task_id="T-001")` returns expected path
  - `tests/test_handover/test_persist_manual_path.py::test_manual_write_creates_file` — actor Write → file present, valid YAML, not in git index
  - `tests/test_handover/test_persist_cli_path.py::test_cli_path_writes_from_stdout` — actor stdout → runner writes file from captured manifest
  - `tests/test_handover/test_idempotent_write.py::test_double_write_identical_content` — second call is no-op
  - `tests/test_content/test_load_records.py::test_load_records_chronological_order` — fixture directory → list in chronological order
  - `tests/test_content/test_blog_format.py::test_blog_intro_references_verdict_story` — fixture with `verdict_story` anchor → draft opens referencing it
  - `tests/test_content/test_x_thread_format.py::test_x_thread_has_six_posts` — anchor pool → 6-post thread, each ≤ 280 chars
  - `tests/test_content/test_window_filter.py::test_window_filters_to_epic_only` — `--window EPIC-X` returns only that epic's records
  - `tests/test_content/test_archive_flag.py::test_archive_produces_tarball` — `--archive EPIC-X` produces `specs/_archives/<epic>-narrative.tar.gz`
- **Integration Sandbox Targets**:
  - End-to-end smoke test (added under `tests/test_integration/` or as a new `tests/test_handover/test_e2e_smoke.py`): simulated RED → GREEN → JUDGE → REFACTOR task produces 4 YAMLs at `.deviate/feat/<epic>/<issue>/<task>/{red,green,judge,refactor}.yaml`, all parse as valid YAML, none staged in git
  - CLI integration: `runner.invoke(cli, ["content", "--help"])` returns expected help text; `runner.invoke(cli, ["content", "--format", "bogus"])` exits non-zero with diagnostic
  - Gitignore integration: `tests/test_handover/test_gitignore.py` (or appended to existing test file) asserts `.deviate/.gitignore` contains `/feat/` and `/content-drafts/` entries post-implementation
  - Skill prompt integration: `tests/test_handover/test_skill_prompts.py` (or appended to existing test file) iterates over the 15 named skills and asserts each contains the Write instruction

## Demonstration Path
```bash
# 1. Verify the new Python module exports the expected API
uv run python -c "
from src.deviate.core.handover import handover_path, persist_handover, load_handover_records, HandoverRecord
macro = handover_path('EPIC-X', 'ISS-001', 'explore')
micro = handover_path('EPIC-X', 'ISS-001', 'red', task_id='T-001')
print(f'[OK] macro: {macro}')
print(f'[OK] micro: {micro}')
assert str(macro) == '.deviate/feat/EPIC-X/ISS-001/explore.yaml'
assert str(micro) == '.deviate/feat/EPIC-X/ISS-001/T-001/red.yaml'
"

# 2. Verify the new CLI sub-app is registered
uv run python -c "
from src.deviate.cli import cli
import click.testing
runner = click.testing.CliRunner()
result = runner.invoke(cli, ['content', '--help'])
assert result.exit_code == 0
assert 'pre' in result.output and 'post' in result.output
assert '--format' in result.output and '--window' in result.output
assert '--slug' in result.output and '--archive' in result.output
print('[OK] deviate content --help advertises pre|post + 4 flags')
"

# 3. Verify the new macro skill template + 5 format templates exist
ls src/deviate/prompts/skills/deviate-content/SKILL.md \
   src/deviate/prompts/content/blog.md \
   src/deviate/prompts/content/x-thread.md \
   src/deviate/prompts/content/release-notes.md \
   src/deviate/prompts/content/commit-story.md \
   src/deviate/prompts/content/resume-bullet.md

# 4. Verify the 15 existing skill prompts carry the Write instruction
for skill in deviate-red deviate-green deviate-yellow deviate-judge deviate-refactor \
             deviate-execute deviate-e2e deviate-hotfix deviate-prune deviate-review \
             deviate-research deviate-prd deviate-shard deviate-plan deviate-tasks; do
  grep -q "handover_path()" "src/deviate/prompts/skills/$skill/SKILL.md" || \
    (echo "[FAIL] $skill missing handover_path() reference" && exit 1)
done
echo "[OK] all 15 skills carry the Write instruction"

# 5. Verify .deviate/.gitignore excludes /feat/ and /content-drafts/
grep -q "^/feat/$" .deviate/.gitignore && \
grep -q "^/content-drafts/$" .deviate/.gitignore && \
echo "[OK] .deviate/.gitignore excludes /feat/ and /content-drafts/"

# 6. Run the 9 new unit tests
mise run test tests/test_handover/ tests/test_content/ -v

# 7. Run the full test suite + lint + format-check
mise run test
mise run lint
mise run format-check
mise run check

# 8. End-to-end smoke: simulate a TDD task and verify the 4 YAMLs land
tmpdir=$(mktemp -d)
cd "$tmpdir"
git init -q && git config user.email "test@test" && git config user.name "Test"
mkdir -p .deviate/feat
# Simulate the 4 phase handovers via persist_handover
uv run --project /Users/werner/Projects/tools/deviatdd python -c "
from src.deviate.core.handover import persist_handover
for phase in ['red', 'green', 'judge', 'refactor']:
    manifest = f'phase: {phase}\nstatus: success\nfiles: []\n'
    persist_handover('EPIC-X', 'ISS-001', phase, manifest, task_id='T-001')
"
ls .deviate/feat/EPIC-X/ISS-001/T-001/
# Verify not staged in git
! git ls-files --error-unmatch .deviate/feat/EPIC-X/ISS-001/T-001/red.yaml 2>/dev/null && \
  echo "[OK] 4 YAMLs present and not staged in git"

# 9. Test synthesis end-to-end
uv run --project /Users/werner/Projects/tools/deviatdd deviate content --format blog --slug my-post --window EPIC-X
test -f .deviate/content-drafts/blog/my-post.md && echo "[OK] blog draft written"

# 10. Test archive
uv run --project /Users/werner/Projects/tools/deviatdd deviate content --archive EPIC-X
test -f specs/_archives/EPIC-X-narrative.tar.gz && echo "[OK] tarball written"
```
