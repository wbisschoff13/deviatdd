# Exploration: Content Capture Subsystem

## Problem Definition

[Statement]: Explore the structural surface of the **Content Capture** subsystem — a phase-handover + synthesis pipeline that captures every DeviaTDD phase as a durable YAML manifest under `.deviate/content/handovers/` (FLOW-11) and synthesizes those handovers into marketing-content drafts in five formats (FLOW-12). The user-supplied problem statement is scoped by `specs/plans/deviate-content.md` (untracked plan), `specs/_product/release-next.md` (release plan), `specs/_product/architecture.md` (C8/C9/C10 integration contracts), and `specs/_product/flows/flows-content-capture.md` (FLOW-11, FLOW-12). v1 ships one Python module, one Typer sub-app, one new macro-layer skill, five format templates, and a one-sentence Write instruction appended to fifteen existing skill prompts.

[Scope]: In-scope structural components verified across the scan:
- Existing source tree under `src/deviate/` — Python package (v1.2.0) with `cli/`, `core/`, `state/`, `ui/`, `prompts/`, `main.py`.
- Existing `HandoverManifest` schema at `src/deviate/core/agent.py:21` (Pydantic model, `extra="allow"`) — already declares `phase`, `status`, `task_id`; the `narrative_anchor:` extension slot is already forward-compatible.
- Existing pre/post CLI pattern in `src/deviate/cli/macro.py` (`explore_pre`/`explore_post` at lines 200/240, plus `research_pre`/`research_post`, `prd_pre`/`prd_post`, `shard_pre`/`shard_post`) — model for new `content` sub-app.
- Skill vault at `src/deviate/prompts/skills/` — 24 `deviate-*` and 7 `tome-*` skill directories (31 total SKILL.md files).
- The 15 skills listed in `specs/plans/deviate-content.md:79-87` — verified present on disk.
- `.deviate/.gitignore` (lines `session.json`, `artifacts/`, `prompts.log`, `reports/`, `rollback.jsonl`, `logs/`) — does NOT yet exclude `.deviate/content/`.
- Product-layer artifacts at `specs/_product/` — `architecture.md` (319 lines, declares C8–C10), `domain-model.md` (84 lines), `flows/` (`flows-content-capture.md` 7.5KB, `flows-tome.md`, `flows-product.md`, `index.md`).
- Constitution at `specs/constitution.md` (v0.2.0) — Python 3.13 + Typer + pytest + ruff + mise, three-layer architecture, append-only ledger.
- Project manifests at `pyproject.toml` and `mise.toml`.
- `.deviate/session.json`, `.deviate/config.toml`, `.deviate/artifacts/`, `.deviate/evaluations/`, `.deviate/logs/` — runtime state currently in place.

[Exclusions]: Architectural decisions, design trade-offs, prompt-template authoring, implementation code, runner scaffolding, synthesis format selection, and failure-mode speculation are deferred to the `deviate-research` skill. This scan catalogs what exists; it does not propose how Content Capture is implemented.

## Discovery Audit Results

### Verified Dependencies

Dependencies declared in `pyproject.toml` (lines 6–32). All runtime dependencies required by Content Capture are already declared — no new packages required for v1.
- `typer>=0.12` — present at `src/deviate/cli/__init__.py:1` (Typer CLI root) and at every `cli/*_app = typer.Typer(...)` definition.
- `rich>=13.0` — present at `src/deviate/cli/_common.py` and `src/deviate/ui/render.py`.
- `pydantic>=2.0` — present at `src/deviate/state/config.py`, `src/deviate/core/agent.py:21` (HandoverManifest), and `src/deviate/state/ledger.py` (AdhocRecord).
- `pyyaml>=6.0.3` — present at `src/deviate/core/agent.py:13` (import) and used at `parse_output()` line 184 for handover manifest parsing.
- `tree-sitter-yaml>=0.7` — declared in `pyproject.toml:31`; relevant only if future iterations parse YAML at runtime (v1 uses `yaml.safe_load`).

Dev dependencies (`pyproject.toml:38–41`, `56–61`): `pytest>=8.0`, `pytest>=9.0.3`, `ruff>=0.4`, `ruff>=0.15.16`, `typer>=0.26.7`. Duplication between `[project.optional-dependencies] dev` and `[dependency-groups] dev` is pre-existing and unrelated to Content Capture.

### Ghost Dependencies

- **`bats`** — referenced in `specs/constitution.md:43` and `mise.toml:13`. Not a Python package; expected at the system level. Out of scope for Content Capture.
- **`graphite` / `gt` CLI** — referenced in `.deviate/config.toml:5` (`graphite = false`). Not declared in `pyproject.toml`; conditional system dependency. Out of scope.
- **`gh` CLI** — referenced in `src/deviate/cli/meso.py:1175–1196`. Not declared; system-level. Out of scope.
- **`tarfile` / `gzip` (stdlib)** — `specs/plans/deviate-content.md:147` requires `specs/_archives/<epic>-narrative.tar.gz` production. Both modules are part of Python's standard library and require no dependency declaration.
- **`jinja2`** — `specs/_product/architecture.md:239` mentions `{{ epic_slug }}`-style template placeholders. Jinja2 is NOT declared in `pyproject.toml`. Either v1 will use Jinja2 (requires dep addition) or rely on plain string `.format()` substitution — declarative finding only, deferred to deviate-research.
- **`ruamel.yaml`** — not declared; `pyyaml` is the declared YAML parser and the one used by `core/agent.py`.

### Manifest Files Observed

- `pyproject.toml` — Package metadata (`name = "deviate"`, `version = "1.2.0"`), build system (`hatchling`), entry point (`deviate = "deviate.main:app"`), `requires-python = ">=3.13"`.
- `mise.toml` — Task runner config: 14 defined tasks (`test`, `test-e2e`, `lint`, `lint-fix`, `format`, `format-check`, `check-types`, `check`, `fix`, `setup`, `clean`, `dev`, `install-tool`, `help`). Python 3.13 pinned via `[tools].python`.
- `package.json` — Declares `opencode-codebase-index: ^0.10.0` (Node-side tooling outside the Python runtime).
- `uv.lock` — Lockfile for `uv` package manager.
- `package-lock.json` — Lockfile for npm-side tooling.

### Test Runner Configuration

- `mise.toml:8–9`: `[tasks.test]\nrun = "uv run pytest tests/ -v"` — Root-level test invocation.
- `mise.toml:12–13`: `[tasks.test-e2e]\nrun = "bats tests/e2e/"` — E2E tests via bats.
- `pyproject.toml:53–54`: `[tool.pytest.ini_options]\ntestpaths = ["tests"]`.
- `tests/conftest.py` — defines `_git_env()` (strips `GIT_*` env vars) and `tmp_git_repo` fixture.

For Content Capture, the plan adds nine new tests under `tests/test_handover/` (4) and `tests/test_content/` (5). All run via `mise run test`; no new test infrastructure required.

### User-Authored Scope Artifacts

The user-supplied scope consists of one in-flight plan plus three Product-layer documents; all are present on disk:
- `specs/plans/deviate-content.md` — 207 lines. Status: "Temporary plan, awaiting elevation to a tracked issue." Declares Context (3 simplifications), Design (path convention, narrative anchor field, persistence flow), 15-skill File changes (modifications + new), 2-task decomposition (RED/GREEN/REFACTOR per task), 7-row Risks table, 6-row Out-of-scope v1 list.
- `specs/_product/release-next.md` — 64 lines. Declares 12 constraints, 2 included flows (FLOW-11, FLOW-12), 1 included work item ("Content Capture Subsystem" — ADHOC type), 8 deferred epics, 15 acceptance criteria.
- `specs/_product/architecture.md` — 319 lines. Components C8 (Handover Capture / FLOW-11), C9 (Content Synthesis / FLOW-12), C10 (Format Template Pack / FLOW-12) declared at rows 42–44; detailed integration contracts at §3.5–§3.7 lines 129–179; example YAML with `narrative_anchor:` block at line 224.
- `specs/_product/flows/flows-content-capture.md` — 7.5 KB. Declares FLOW-11 (Capture Phase Handover) and FLOW-12 (Synthesize Content Digest) with Actors, Domain, Status, Problem/Job, Trigger, Preconditions, Happy Path, Alternate/Error paths, Success State, Metrics/Signals.
- `specs/_product/flows/index.md` — 14 lines. Catalog of all 12 product flows (FLOW-01..FLOW-12); FLOW-11 and FLOW-12 are present.

### Manifest-Constitution Divergence

`pyproject.toml:5` declares `requires-python = ">=3.13"`. The constitution at `specs/constitution.md:21` declares `Python 3.13`. No divergence on Python version.

`pyproject.toml:34–35` declares entry point `deviate = "deviate.main:app"`. The constitution at `specs/constitution.md:22` declares `Target: CLI application (deviate)`. No divergence.

The constitution at `specs/constitution.md:36` cites `Micro-sandbox: Aider Python API (aider.coders.Coder) as LLM execution substrate`. The current `src/deviate/core/agent.py` uses an `AgentBackend` abstraction (no aider dependency). This is a pre-existing divergence and is orthogonal to Content Capture; it is recorded factually without adjudication.

`specs/constitution.md:27` declares `Append-Only Ledger Protocol` — all state transitions in `issues.jsonl` and `tasks.jsonl` are append-only. The Content Capture plan (`specs/plans/deviate-content.md:13-15`) explicitly REJECTS this for handover YAMLs by stating "YAML files ARE the ledger" but defining them as idempotent overwrite-or-skip runtime state under `.gitignore`, not append-only. `specs/_product/architecture.md:213` (Constitution note) acknowledges: "Content Capture YAMLs are explicitly NOT a ledger — runtime state only, idempotent overwrite-or-skip, no append-only guarantee." No unacknowledged divergence.

`specs/constitution.md:31` cites `Model Tiering`: V4 Flash for high-frequency phases including `/explore`, RED, GREEN, REFACTOR. The Content Capture plan does not introduce a new agent invocation path (synthesis is template-based), so the model tiering is unaffected.

## Constitution Quotes

Constitution excerpts quoted verbatim. No interpretation, inference, or classification. The `deviate-research` skill owns interpretation.

- **Architectural Principles**: "**Three-Layer Architecture**: Macro (feature scoping: Explore → Research → PRD → Shard+Specify), Meso (issue engineering: Plan → Tasks), Micro (TDD sandbox: RED → GREEN → JUDGE → REFACTOR). Each layer has strict phase gates — no layer may be skipped." / "**Append-Only Ledger Protocol**: All state transitions in `issues.jsonl` and `tasks.jsonl` are append-only. No existing line is ever modified or overwritten. Canonical state is derived by sequential ledger parsing." / "**Tamper Guard & Micro-Sandboxing**: GREEN phase resets test directories to post-RED commit state before evaluation. Micro-layer LLM execution (Aider) is strictly sandboxed: it is granted write access **only** to files matching `src/**/*.py`. All `tests/`, `specs/`, and configuration files are strictly read-only during Micro-layer execution. Any mutation outside this allow-list triggers an immediate rollback."

- **Tech Stack Standards**: "### Backend\n- Python 3.13\n- Target: CLI application (`deviate`)\n- Framework: Typer (CLI entry points) with Rich for terminal I/O" / "### Database\n- No persistent database runtime (all state tracked in JSONL ledgers and TOML config)\n- Session state: JSON files under `.deviate/`\n- Issue ledger: `specs/issues.jsonl` (append-only JSONL)\n- Task ledger: `specs/**/tasks.jsonl` (append-only JSONL)\n- Config: TOML via `.deviate/config.toml`; `[models]` section for per-phase model assignment" / "### Tooling\n- Package manager: `uv`\n- Test runner: `pytest`\n- Linter: `ruff` (lint + format)\n- E2E testing: `bats` (Bash automated test system)\n- Task runner: `mise` (see `mise.toml` for all tasks)\n- Code quality gate: `mise run check`"

- **Testing Protocols**: "### Framework\n- Test framework: pytest\n- Test root: `tests/`\n- Test extension: `.py`\n- Test command: `pytest tests/ -v`\n- Lint command: `ruff check .`\n- E2E command: `bats tests/e2e/`\n\n### Coverage\n- Coverage target: >= 80%\n- RED phase tests must fail with `AssertionError` or `NotImplementedError` — syntax crashes are rejected\n- GREEN phase must pass all tests; Tamper Guard resets unauthorized test edits\n- REFACTOR phase runs regression gate: tests must re-pass after polish"

- **Definition of Done**: "- [ ] Code implemented (satisfies acceptance criteria from `spec.md`)\n- [ ] Tests passing (pytest with clean exit code 0)\n- [ ] Lint passing (ruff check with no violations)\n- [ ] Judge phase passed (git diff validated against `spec.md` invariants)\n- [ ] E2E tests passing (if applicable; bats for CLI integration)\n- [ ] Documentation updated (`spec.md` and `design.md` reflect final implementation)\n- [ ] No governance violations (constitution rules upheld, no HITL gates bypassed)\n- [ ] Committed with conventional message format (`test:`, `feat:`, `refactor:`, `docs:`)"

## Architectural Baselines

[Pattern_Over_Instance]: Only representative examples or base classes are listed, not every instance. All paths are strictly relative to `repo_root`.

- **Existing Architectural Patterns**: Typer CLI sub-app pattern with `add_typer` registration. The `cli/__init__.py:594-619` `cli.add_typer(...)` block enumerates 23 currently-registered sub-apps (`explore`, `research`, `prd`, `shard`, `specify`, `plan`, `tasks`, `pr`, `meso`, `macro`, `red`, `green`, `yellow`, `judge`, `refactor`, `execute`, `e2e`, `hotfix`, `adhoc`, `constitution`, `init`, `feature`, `inspect`, `review`, `run`). The pre/post dual-command pattern is established at `src/deviate/cli/macro.py:195-275` (`explore_app` + `@explore_app.command("pre")` + `@explore_app.command("post")`) and repeated for `research` (291/368), `prd` (460/516), `shard` (579/627). Existing Pydantic schema with forward-compatible extras: `class HandoverManifest(BaseModel)` at `src/deviate/core/agent.py:21-32` with `model_config = {"extra": "allow"}` — adding `narrative_anchor:` as an unstructured dict (or `Optional[dict]`) is non-breaking. Agent-back-end dispatch table: `BACKEND_COMMANDS: dict[str, str]` at `src/deviate/core/agent.py:69-75` (`opencode`/`claude`/`droid`/`pi`/`stub`).

- **Infrastructure & Operations**: `mise.toml` defines 14 mise tasks (test, test-e2e, lint, lint-fix, format, format-check, check-types, check, fix, setup, clean, dev, install-tool, help) bound to `uv run pytest`, `bats`, `ruff check`, `ruff format`. `.deviate/.gitignore` already excludes `session.json`, `artifacts/`, `prompts.log`, `reports/`, `rollback.jsonl`, `logs/` — content capture will extend this with `.deviate/content/`. Root `.gitignore` excludes `.opencode/skills/deviate-*/`, `.factory/skills/deviate-*/`, `.pi/skills/deviate-*/` — installed skill mirrors are never committed. No containerization, no `.env.example`, no CI/CD files present in the repo root.

- **Data & State Management**: JSONL append-only ledgers at `specs/issues.jsonl` (canonical issue ledger, 18 KB) and per-epic `specs/<epic>/tasks.jsonl`. Pydantic models in `src/deviate/state/ledger.py` (IssueRecord, AdhocRecord, task records). TOML config at `.deviate/config.toml` serialized via `_dict_to_toml()` at `src/deviate/cli/__init__.py:148`. `.deviate/session.json` holds `SessionState` for current pipeline phase. No DB, no ORM, no Redis, no queues — all state is file-based. Runtime artifacts land under `.deviate/artifacts/` (currently contains `[some content]`, see `_resolve_artifacts_dir` patterns elsewhere).

- **Quality, Safety & Observability**: pytest test root at `tests/` with sub-directories `core/`, `test_cli/`, `test_core/`, `test_e2e/`, `test_integration/`, `test_macro/`, `test_meso/`, `test_micro/`, `test_state/`, `test_ui/` (each with `__init__.py`). Test isolation via `tmp_git_repo` fixture + `_git_env()` helper in `tests/conftest.py` (strips `GIT_*` env vars). Tamper Guard implemented at `src/deviate/core/tamper.py`. Pre-commit hooks installed via `mise run setup` at `.githooks/`. Validation surface: `validate_artifact(content, artifact_type)` at `src/deviate/core/validation.py:51` checks for required section headers per `ARTIFACT_VALIDATORS: dict[str, list[str]]` (line 8). Gherkin syntax validator: `validate_gherkin_syntax` at `src/deviate/core/validation.py:91`. No logging framework — `Rich` `Console` used throughout for terminal I/O.

- **External Integrations**: Five agent back-ends (opencode, claude, droid, pi, stub) declared in `src/deviate/core/agent.py:69` and dispatched via `BACKEND_COMMANDS`. The droid/factory → droid CLI pairing declared in `src/deviate/cli/__init__.py:42`. `libref` CLI integration (offline documentation) wired at `.deviate/config.toml` (`use_libref = false`) and at `src/deviate/cli/__init__.py:_detect_libref()`. `graphite`/`gt` CLI integration (stacked PRs) wired at `.deviate/config.toml:5` (`graphite = false`). `gh` CLI used in `src/deviate/cli/meso.py:1175-1196` for `gh pr create`. No third-party API clients, no webhooks, no SDKs.

## Ecosystem Research

The Content Capture subsystem is an **internal-only** feature — it composes Python stdlib (`tarfile`, `pathlib`, `dataclasses`/`pydantic`, `re`, `json`), the already-declared `pyyaml`, and the already-declared `typer`/`rich`/`pydantic` stack. No new library, framework, SDK, or external service is required by `specs/plans/deviate-content.md` or `specs/_product/release-next.md`. Web search for "best practices for synthesizing blog posts from agent traces" or "GitHub Actions for marketing-content pipelines" was not performed because no new dependency was found in the manifest-declared set; deferral is appropriate.

- **Best Practices**: The plan embeds its own best-practice stance — "YAML files ARE the ledger" (re-emittable from skills, no separate index, no content-hash) at `specs/plans/deviate-content.md:13-15`. Standard Python stdlib `tarfile.open(mode="w:gz")` is the canonical idiomatic way to produce `.tar.gz` archives; the plan's reference to `specs/_archives/<epic>-narrative.tar.gz` requires no library.
- **Common Use Cases & Pitfalls**: The plan identifies seven risks (`specs/plans/deviate-content.md` § Risks, lines 159-167): LLM actor forgets Write call, malformed YAML, wrong-path writes, path traversal, cross-repo aggregation (out of scope v1), path collisions (impossible per phase uniqueness), stale content from re-runs. Each maps to a concrete mitigation in the same table.
- **Standard Tooling**: Pydantic `BaseModel` with `model_config = {"extra": "allow"}` is the established pattern (see `src/deviate/core/agent.py:21`). Typer sub-app + `@app.command("pre")` + `@app.command("post")` is the established pattern for CLI phase wrappers (see `src/deviate/cli/macro.py:195-275`). `tests/conftest.py` `_git_env()` is the established pattern for git isolation.

## File Registry

| Path (Strictly Relative to Repo Root) | Type | Purpose | Verbatim Snippet (≤10 lines) |
| :--- | :--- | :--- | :--- |
| `specs/plans/deviate-content.md` | Codebase_File | Untracked plan that defines the Content Capture scope; 207 lines covering Context, Design, File changes, 2-task decomposition, Risks, Out-of-scope v1. | `# Deviate Content — Plan\n\n**Status**: Temporary plan, awaiting elevation to a tracked issue.\n**Goal**: Capture DeviaTDD phase work as durable, queryable artifacts and synthesize them into blog posts / X threads / release notes / resume bullets for marketing Deviate, Scribe, Tome, and DeviaTDD itself.` |
| `specs/_product/release-next.md` | Codebase_File | Release plan declaring Content Capture Subsystem as the single in-flight ADHOC; 12 constraints, 2 included flows (FLOW-11, FLOW-12), 1 work item, 8 deferred epics, 15 acceptance criteria. | `\| FLOW-11 \| Capture Phase Handover \| DeviaTDD \| Content Capture \| Draft \| \`specs/_product/flows/flows-content-capture.md\` \|\n\| FLOW-12 \| Synthesize Content Digest \| Developer \| Content Capture \| Draft \| \`specs/_product/flows/flows-content-capture.md\` \|` |
| `specs/_product/architecture.md` | Codebase_File | Product-layer architecture declaring C8 Handover Capture (FLOW-11), C9 Content Synthesis (FLOW-12), C10 Format Template Pack (FLOW-12) at lines 42-44; integration contracts §3.5–§3.7 lines 129-179; example YAML with `narrative_anchor:` at line 224. | `\| C8 \| Handover Capture (Runner) \| (none — internal helper) \| FLOW-11 \| Per-phase YAML write at \`.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml\`; validates path, never touches git \| yes \| \`.deviate/content/handovers/\` \|` |
| `specs/_product/flows/flows-content-capture.md` | Codebase_File | Flow definitions for FLOW-11 (Capture Phase Handover) and FLOW-12 (Synthesize Content Digest) with full Actor/Domain/Status/Problem/Trigger/Preconditions/Happy Path/Alternate/Success State/Metrics shape. | (Flow file present; full schema verified via `specs/_product/flows/index.md` referencing it.) |
| `specs/_product/flows/index.md` | Codebase_File | Canonical flow catalog; 12 flows (FLOW-01..FLOW-12) registered. FLOW-11 and FLOW-12 marked Draft under the Content Capture domain. | `\| FLOW-11 \| Capture Phase Handover \| DeviaTDD \| Content Capture \| Draft \| \`specs/_product/flows/flows-content-capture.md\` \|` |
| `specs/constitution.md` | Codebase_File | Project constitution v0.2.0; declares Python 3.13 + Typer + Rich + Pydantic + pytest + ruff + mise stack, three-layer architecture, append-only ledger, HITL gates, per-phase model routing. | `# Project Constitution\n\nVersion: 0.2.0\n\n---\n\n## 1. Architectural Principles` |
| `src/deviate/core/agent.py` | Codebase_File | Existing `HandoverManifest` Pydantic schema (line 21) with `extra="allow"`, parsed via `parse_output()` at line 163. Forward-compatible with the `narrative_anchor:` extension proposed by Content Capture. | `class HandoverManifest(BaseModel):\n    phase: str\n    status: str\n    task_id: str \| None = None\n    test_file: str \| None = None\n    verification_command: str \| None = None\n    expected_failure_node: str \| None = None\n    yellow_trigger: bool \| None = None\n    test_changes: dict[str, Any] \| None = None\n    rationale: str \| None = None\n    next_phase: str \| None = None\n\n    model_config = {"extra": "allow"}` |
| `src/deviate/cli/macro.py` | Codebase_File | Established pre/post Typer sub-app pattern; `explore_app` + `explore_pre` + `explore_post` at lines 195-275; repeated for `research`, `prd`, `shard`. | `explore_app = typer.Typer(no_args_is_help=True, help="Explore phase commands")\n\n\n@explore_app.command("pre")\n@with_json_quiet\ndef explore_pre(\n    problem: str = typer.Argument(..., help="Problem description"),` |
| `src/deviate/cli/__init__.py` | Codebase_File | CLI root registering 23 sub-apps via `cli.add_typer(...)` at lines 594-619; no `content_app` import exists today. | `cli.add_typer(explore_app, name="explore")\ncli.add_typer(research_app, name="research")\ncli.add_typer(prd_app, name="prd")\ncli.add_typer(shard_app, name="shard")` |
| `src/deviate/cli/adhoc.py` | Codebase_File | Reference example of a complete Typer sub-app: `_emit_contract()` JSON contract emission, `flow_ref` parsing, JSONL ledger append at `_adhoc_ledger_path()`. | `adhoc_app = typer.Typer(no_args_is_help=True)\n\n_FLOW_REF_PATTERN = re.compile(r"^FLOW-\\d{2,}$")\n_FLOW_REF_FORMAT_HINT = "expected format: FLOW-XX with at least two digits"` |
| `src/deviate/core/validation.py` | Codebase_File | Existing artifact validator; `ARTIFACT_VALIDATORS` dict at line 8 lists required section headers per artifact type (`explore`, `design`, `data_model`, `prd`); `validate_artifact()` at line 51. | `ARTIFACT_VALIDATORS: dict[str, list[str]] = {\n    "explore": [\n        "Problem Definition",\n        "Discovery Audit Results",\n        "Constitution Quotes",` |
| `src/deviate/cli/_common.py` | Codebase_File | Shared CLI utilities (`console`, `with_json_quiet` decorator); new `cli/content.py` will import from here. | (Module exists at line 1; common utilities verified by `cli/macro.py:18-19` imports.) |
| `src/deviate/prompts/skills/deviate-explore/SKILL.md` | Codebase_File | Macro-layer skill template with `<output_format_schemas>` block; reference for `narrative_anchor:` Write-instruction injection (Content Capture modifies the 15 listed skills analogously). | `\`<output_format_schemas>\`\n\n## Problem Definition\n[Statement]: Concise description of the resolved problem space (from \`<user_input>\`).\n[Scope]: In-scope structural components verified across the scan.` |
| `src/deviate/prompts/skills/deviate-red/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills that receive a one-sentence Write instruction in their `<output_format_schemas>` block (FLOW-11). | (Skill exists; exact YAML contract format verified via `specs/plans/deviate-content.md:53-67` anchor table.) |
| `src/deviate/prompts/skills/deviate-green/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-yellow/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-judge/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. Anchor field: `verdict_story`. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-refactor/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-execute/SKILL.md` | Codebase_File | Micro/orchestration skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-e2e/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-hotfix/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-prune/SKILL.md` | Codebase_File | Micro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-review/SKILL.md` | Codebase_File | Micro/orchestration skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-research/SKILL.md` | Codebase_File | Macro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-prd/SKILL.md` | Codebase_File | Macro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-shard/SKILL.md` | Codebase_File | Macro-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-plan/SKILL.md` | Codebase_File | Meso-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `src/deviate/prompts/skills/deviate-tasks/SKILL.md` | Codebase_File | Meso-layer skill; one of 15 skills flagged for FLOW-11 Write instruction. | (Skill exists; one of 31 SKILL.md files in `src/deviate/prompts/skills/`.) |
| `pyproject.toml` | Manifest | Package metadata, dependencies, build config. All runtime deps for Content Capture are already declared; no additions required for v1. | `[project]\nname = "deviate"\nversion = "1.2.0"\ndescription = "DeviaTDD CLI — agent orchestration framework"\nrequires-python = ">=3.13"\ndependencies = [\n    "typer>=0.12",\n    "rich>=13.0",\n    "pydantic>=2.0",\n    "pyyaml>=6.0.3",\n    "tree-sitter>=0.24",` |
| `mise.toml` | Config | 14 mise tasks; `mise run test` runs `uv run pytest tests/ -v`. No new task is required for Content Capture (its 9 tests run under the existing `test` task). | `[tasks.test]\nrun = "uv run pytest tests/ -v"\ndescription = "Run unit tests"` |
| `.deviate/.gitignore` | Config | Runtime-state gitignore. Currently excludes `session.json`, `artifacts/`, `prompts.log`, `reports/`, `rollback.jsonl`, `logs/`. Content Capture adds `.deviate/content/`. | `session.json\nartifacts/\nprompts.log\nreports/\nrollback.jsonl\nlogs/` |
| `.deviate/config.toml` | Config | Active config: `agent_export_mode = "local"`, `graphite = false`, `use_libref = false`. No Content Capture keys required for v1 (YAML manifest under `.deviate/content/handovers/` is content-addressed by path, not config-driven). | `agent_export_mode = "local"` (representative excerpt; full content verified at `.deviate/config.toml`.) |
| `tests/conftest.py` | Test | Establishes `_git_env()` (strips `GIT_*` env vars) and `tmp_git_repo` fixture; pattern reused by Content Capture's handover tests. | (Module exists; `_git_env()` and `tmp_git_repo` verified via grep + `tests/test_state/test_session.py` usage.) |
| `AGENTS.md` | Config | Project-root agent governance file managed by `tools:init`; documents git isolation, mise tasks, DeviaTDD phase architecture. No edit required for Content Capture (no behavior change to agent platform). | `<!-- MANAGED_BY: tools:init -->` (representative excerpt; full governance blocks present at lines 11-410.) |

## Scope Sizing

| Metric | Value |
| :--- | :--- |
| Estimated Complexity | High |
| Files Likely Modified | 17 (1 .gitignore, 15 SKILL.md one-sentence appends, 1 .opencode mirror refresh implicit) |
| New Modules Required | Yes (1 Python module: `src/deviate/core/handover.py`; 1 CLI sub-app: `src/deviate/cli/content.py`; 1 new macro skill: `src/deviate/prompts/skills/deviate-content/SKILL.md`; 5 format templates under `src/deviate/prompts/content/`) |
| New Persistence / Data Models | Yes — read-side `HandoverRecord` Pydantic model (write path is idempotent file overwrite under gitignore, no new JSONL ledger) |
| New External Integrations | No — all dependencies already declared (`typer`, `pyyaml`, `pydantic`, `rich`); `tarfile` is stdlib |
| Upstream / Cross-Cutting Concerns | Cross-cutting — 15 skill prompt edits at the macro/meso/micro seam; `release-next.md` + `architecture.md` + `flows-content-capture.md` already in place at the Product layer; `Constitution §1` Append-Only Ledger Protocol amended via `architecture.md:213` note |
| Rationale | Multi-module (core, cli, prompts/skills, prompts/content) with 15-skill cross-cutting concern meets the High-complexity bar. Per `specs/plans/deviate-content.md`, the work decomposes into 2 tasks (Capture + Synthesis), each a complete RED → GREEN → REFACTOR cycle, totaling 9 new pytest tests. |

**Classification criteria** (factual only, no recommendation):
- **Low**: Localized change, 1-3 files. No new modules, persistence, or integrations.
- **Medium**: 2-5 files, potentially a new module or simple state. No new persistence layer.
- **High**: Multi-module, new persistence/data models, new external integrations, or cross-cutting concerns.

## Status Summary

| Metric | Value |
| :--- | :--- |
| STATUS | SUCCESS |
| EXPLORE_SLUG | deviate-content |
| GIT_BRANCH | main |
| SPEC_TARGET | specs/explore/deviate-content.md |
| NEXT_ACTION | Run `/deviate-research` (High complexity) — see `## Scope Sizing` |