# Implementation Tasks: `feat/adhoc/012-deviate-content`

> Source issue: `specs/adhoc/issues/012-deviate-content.md` (ISS-ADH-012)
> Source plan: `specs/plans/deviate-content.md`
> Release trace: `specs/_product/release-next.md` AC-ADHOC-012-01 through AC-ADHOC-012-16
> v1 product-layer scope: FLOW-11 (per-phase YAML handover capture) + FLOW-12 (synthesis CLI + 5 format templates)

## Phase 1: FLOW-11 Capture Helper Module (C8 Handover Capture)
**Goal**: Author `src/deviate/core/handover.py` as the runner-side helper exposing `handover_path()`, `persist_handover()`, `load_handover_records()`, and the read-side `HandoverRecord` Pydantic model. Extend `.deviate/.gitignore` to exclude the runtime-state surface. Ships the single integration point every DeviaTDD phase post-handler will call to durably persist YAML handovers at `.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml` — the C8 component of the architecture.

### Tasks

- TSK-012-01: FLOW-11 capture helper + path/persistence/idempotency tests
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Sociable_Unit
  - **Verification**: `mise run test tests/test_handover/ -v`
  - **Estimated Time**: 75 minutes
  - **Flow References**: `[FLOW-11, FLOW-12]`
  - **Files**:
    - `src/deviate/core/handover.py` (NEW)
    - `tests/test_handover/test_path_resolution.py` (NEW)
    - `tests/test_handover/test_persist_manual_path.py` (NEW)
    - `tests/test_handover/test_persist_cli_path.py` (NEW)
    - `tests/test_handover/test_idempotent_write.py` (NEW)
    - `.deviate/.gitignore` (EXTEND — append `.deviate/content/`)
  - **Rationale**: US-012-01 through US-012-05 + US-012-12 require the FLOW-11 capture helper to exist with the canonical path convention from `specs/_product/architecture.md:179` (macro: `.deviate/content/handovers/<epic>/<issue>/<phase>.yaml`; micro: `.deviate/content/handovers/<epic>/<issue>/<task>/<phase>.yaml`). US-012-04 mandates idempotent overwrite-or-skip semantics (`specs/plans/deviate-content.md:64-73`); US-012-05 mandates path-traversal rejection before any filesystem write. The existing `HandoverManifest` at `src/deviate/core/agent.py:21-32` carries `model_config = {"extra": "allow"}` and is forward-compatible with the optional `narrative_anchor:` block — `handover.py` reuses that pattern via a read-side `HandoverRecord` Pydantic model without modifying `agent.py` per Defensive Exclusion. Serves FLOW-11 Steps 1-4 (Trigger → Manual/CLI Path → Persistence → Idempotency).
  - **Details**:
    - **Red**: Write 4 failing tests under `tests/test_handover/` (matching `specs/plans/deviate-content.md:108-118`). (a) `test_path_resolution`: asserts `handover_path("EPIC-X", "ISS-001", "explore") == Path(".deviate/content/handovers/EPIC-X/ISS-001/explore.yaml")` (macro case) and `handover_path("EPIC-X", "ISS-001", "red", task_id="T-001") == Path(".deviate/content/handovers/EPIC-X/ISS-001/T-001/red.yaml")` (micro case); also asserts `handover_path("..", "ISS-001", "red")` raises `PathTraversalError` via `Path.resolve(strict=False)`. (b) `test_persist_manual_path`: invokes `persist_handover("EPIC-X", "ISS-001", "red", manifest_yaml, task_id="T-001")` against `tmp_git_repo`, asserts the file exists, `yaml.safe_load` round-trips, and `git ls-files --error-unmatch` returns non-zero (not staged per `AC-ADHOC-012-15`). (c) `test_persist_cli_path`: invokes `persist_handover()` from a stub CLI context with a captured stdout manifest string, asserts the canonical file lands and parses. (d) `test_idempotent_write`: calls `persist_handover()` twice with identical content, asserts one file exists, no exception, both calls return the same `Path`. Tests use `tmp_git_repo` + `_git_env()` from `tests/conftest.py`.
    - **Green**: Create `src/deviate/core/handover.py` exporting four public symbols: (1) `handover_path(epic_slug, issue_id, phase, task_id=None) -> Path` — returns the canonical path via a `_HANDOVER_ROOT = Path(".deviate") / "content" / "handovers"` constant, sets `task_id` segment when present; resolves via `Path.resolve(strict=False)` and validates the resolved path is rooted under `_HANDOVER_ROOT.resolve()` (raises `PathTraversalError` otherwise). (2) `persist_handover(epic_slug, issue_id, phase, manifest, task_id=None) -> Path` — `Path.mkdir(parents=True, exist_ok=True)`, early-returns existing path on `Path.exists()` (idempotency), else `yaml.safe_dump(manifest, default_flow_style=False, allow_unicode=True)`. (3) `load_handover_records(window=None) -> list[HandoverRecord]` — globs `.deviate/content/handovers/**/*.yaml`, parses via `yaml.safe_load`, skips malformed entries with `print(f"warning: skip {path}: {e}", file=sys.stderr)` (captured by `capsys` in tests), returns chronologically ordered records. (4) `HandoverRecord(BaseModel)` with `epic_slug`, `issue_id`, `task_id`, `phase`, `status`, `files: list[str]`, `narrative_anchor: dict[str, Any] | None`, `timestamp`, and `model_config = {"extra": "allow"}` matching `src/deviate/core/agent.py:21-32`. Append two lines (`.deviate/content/`) to `.deviate/.gitignore`.
    - **Refactor**: Extract `_HANDOVER_ROOT` as a module-level `Path` constant; centralize macro/micro detection by presence of `task_id` in a single `_segments(task_id)` helper; reuse `_git_env()` patterns from `tests/conftest.py` (do not redefine locally); ensure `PathTraversalError` carries the rejected path string in its message for diagnosability.
    - **Edge Cases**: Path traversal via `..` in `epic_slug`/`issue_id`/`task_id`/`phase` rejected at `handover_path()` time (BEFORE mkdir); idempotent re-write returns the existing `Path` without re-parsing YAML; malformed YAML in `load_handover_records()` is logged to stderr and skipped (not raised) per `AC-ADHOC-012-12`; `task_id=None` produces the macro path shape (no `task_id` segment).
    - **Acceptance**: `pytest tests/test_handover/ -v` passes 4/4; `.deviate/.gitignore` contains both `.deviate/content/`; `git ls-files --error-unmatch .deviate/content/handovers/EPIC-X/ISS-001/T-001/red.yaml` returns non-zero inside a `tmp_git_repo` fixture; `mise run lint` reports zero ruff violations on `src/deviate/core/handover.py`; module line count ≤ 200.

---

## Phase 2: FLOW-12 Synthesis CLI + Macro Skill + 5 Format Templates (C9 + C10)
**Goal**: Ship the synthesis CLI sub-app `deviate content` plus the `deviate-content` macro skill plus 5 format templates (`blog`, `x-thread`, `release-notes`, `commit-story`, `resume-bullet`). Loads `HandoverRecord`s via the FLOW-11 helper, renders via the format template, writes draft to `.deviate/content/drafts/<format>/<slug>.md`; archive flag writes `specs/_archives/<epic>-narrative.tar.gz`. C9 (Synthesis) + C10 (Format Template Pack).

### Tasks

- TSK-012-02: FLOW-12 synthesis CLI + deviate-content skill + 5 format templates + 5 tests
  - **Judge Feedback**: Three of four blocking issues from the prior JUDGE feedback were correctly addressed; one was not.
    - **Judge Feedback**: 
    - **Judge Feedback**: ADDRESSED:
    - **Judge Feedback**: - Blocking #1 — `src/deviate/cli/content.py` split into 4 modules (90-line CLI + 140-line synthesis + 121-line renderers + 127-line yaml-loader); the CLI surface is well within the ≤150-line budget. ✓
    - **Judge Feedback**: - Blocking #3 — `tests/test_content/test_cli_help.py` (4 tests in `TestContentCliHelp`) and `tests/test_content/test_unknown_format.py` (3 tests in `TestUnknownFormatRejection`) added, verifying Scenario 012-06 and Scenario 012-07. ✓
    - **Judge Feedback**: - Blocking #4 — No linter-silencing `_ = ...` lines at the bottom of `content.py`; no dead `_list_template_formats` function; `re` import correctly located in `synthesis.py` only. ✓
    - **Judge Feedback**: - Secondary — `_split_into_x_thread()` honors the documented phase-priority ordering (red → green → judge → refactor → teaser → CTA) via the `_PHASE_PRIORITY` sort key. ✓
    - **Judge Feedback**: - Secondary — The 15 SKILL.md appends are one-sentence with appropriate Markdown formatting (single sentence, no heading, minimal blank-line padding for readability). ✓
    - **Judge Feedback**: 
    - **Judge Feedback**: NOT ADDRESSED — Blocking #2 (lenient YAML parser):
    - **Judge Feedback**: The lenient YAML parser was not reverted. Instead, it was relocated to a brand-new module `src/deviate/core/synthesis_yaml.py` (127 lines). The module's docstring explicitly acknowledges the contradiction with Scenario 012-12 but proceeds anyway. `synthesize_draft()` calls `load_records_lenient()` as its default read path:
    - **Judge Feedback**: 
    - **Judge Feedback**:     # src/deviate/core/synthesis.py:84
    - **Judge Feedback**:     records = load_records_lenient(window=window, repo=base)
    - **Judge Feedback**: 
    - **Judge Feedback**: Why the relocation does NOT satisfy the prior feedback:
    - **Judge Feedback**: 1. The prior feedback explicitly required: "Restore the original TSK-012-01 behavior: `yaml.safe_load` + skip + stderr warning on `yaml.YAMLError`."
    - **Judge Feedback**: 2. Scenario 012-12 mandates: "the malformed record is skipped with a warning logged to stderr" — not fixed.
    - **Judge Feedback**: 3. The spec's "YAML files ARE the ledger" simplicity principle at `specs/plans/deviate-content.md:13-15` is violated by a separate fixer module that introduces scope creep into FLOW-12.
    - **Judge Feedback**: 4. The lenient parser is structurally the same code as the prior attempt's `_lenient_yaml_fallback()` — same regex pattern (`^(\s+)([a-zA-Z_]\w*)\s*:\s+(.+)$`), same `yaml.YAMLError` catch, same in-place fix-and-retry logic.
    - **Judge Feedback**: 
    - **Judge Feedback**: NEXT GREEN ATTEMPT MUST:
    - **Judge Feedback**: 1. Delete `src/deviate/core/synthesis_yaml.py` entirely (the whole file, not just the helpers).
    - **Judge Feedback**: 2. In `src/deviate/core/synthesis.py`, change `from deviate.core.synthesis_yaml import load_records_lenient` to use the already-imported `load_handover_records` from `deviate.core.handover`. If `load_handover_records` is not currently imported in `synthesis.py`, add the import.
    - **Judge Feedback**: 3. In `synthesize_draft()`, change `records = load_records_lenient(window=window, repo=base)` to `records = load_handover_records(window=window, repo=base)`.
    - **Judge Feedback**: 4. Run `mise run test tests/test_content/ -v` and confirm all 24 synthesis tests still pass — every YAML fixture in the new tests is well-formed and parses cleanly under `yaml.safe_load`.
    - **Judge Feedback**: 5. Run `mise run lint` to confirm no F401 unused-import warnings remain.
    - **Judge Feedback**: 6. Verify `handover.py` is byte-equal to its TSK-012-01 state: `git diff src/deviate/core/handover.py` against the TSK-012-01 commit should show zero changes.
    - **Judge Feedback**: 7. Verify the synthesis integration tests (`test_blog_format`, `test_x_thread_format`, `test_window_filter`, `test_archive_flag`) still pass — the CLI surface is unchanged, only the read-path beneath `synthesize_draft()` is being tightened.
    - **Judge Feedback**: 
    - **Judge Feedback**: Do NOT introduce any alternative lenient parsing mechanism in the next attempt. If a real-world YAML genuinely needs lenient parsing, file it as a separate bug per the prior feedback's guidance.
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Integration
  - **Verification**: `mise run test tests/test_content/ -v && mise run lint && uv run --project /Users/werner/Projects/tools/deviatdd python -c "import yaml,pathlib; t=pathlib.Path('src/deviate/prompts/skills/deviate-content/SKILL.md').read_text(); fm=yaml.safe_load(t.split('---',2)[1]); assert fm['name']=='deviate-content'; assert fm['category']=='deviatdd-macro-layer'; assert fm['version']=='1.0.0'; assert '/deviate-content' in fm['aliases']; print('OK')"`
  - **Estimated Time**: 90 minutes
  - **Flow References**: `[FLOW-11, FLOW-12]`
  - **Files**:
    - `src/deviate/cli/content.py` (NEW)
    - `src/deviate/cli/__init__.py` (EXTEND — append one `cli.add_typer(content_app, name="content")` line at line ~706 region)
    - `src/deviate/prompts/skills/deviate-content/SKILL.md` (NEW)
    - `src/deviate/prompts/content/blog.md` (NEW)
    - `src/deviate/prompts/content/x-thread.md` (NEW)
    - `src/deviate/prompts/content/release-notes.md` (NEW)
    - `src/deviate/prompts/content/commit-story.md` (NEW)
    - `src/deviate/prompts/content/resume-bullet.md` (NEW)
    - `src/deviate/core/handover.py` (EXTEND — add `synthesize_draft(records, format, slug) -> Path` and `archive_epic(epic_slug) -> Path`)
    - `tests/test_content/test_load_records.py` (NEW)
    - `tests/test_content/test_blog_format.py` (NEW)
    - `tests/test_content/test_x_thread_format.py` (NEW)
    - `tests/test_content/test_window_filter.py` (NEW)
    - `tests/test_content/test_archive_flag.py` (NEW)
  - **Rationale**: US-012-06 through US-012-10 require the FLOW-12 synthesis surface — `deviate content --format <5 formats> --window EPIC-X --slug S --archive EPIC-X` — to load records via the Phase-1 helper, extract anchors per phase-specific field names (`specs/plans/deviate-content.md:52-67`), render via the format template using `str.format()` (NO Jinja2 per Defensive Exclusion), and write drafts to `.deviate/content/drafts/<format>/<slug>.md`. The 5 format templates are the C10 Format Template Pack; the `deviate-content` macro skill is the FLOW-12 driver discovered by `discover_skills()` at `src/deviate/core/skills.py:20-26`. AC-ADHOC-012-06 through AC-ADHOC-012-12 + AC-ADHOC-012-16. Serves FLOW-12 Steps 1-6 (Load → Extract → Render → Write → Archive) plus the FLOW-11 read-back path.
  - **Details**:
    - **Red**: Write 5 failing tests under `tests/test_content/`. (a) `test_load_records`: seed `tmp_git_repo/.deviate/content/handovers/EPIC-X/ISS-001/{red,green,judge,refactor}.yaml`, call `load_handover_records()`, assert chronologically ordered list with `len == 4` and that `judge` record carries `narrative_anchor.verdict_story` (per `AC-ADHOC-012-08`). (b) `test_blog_format`: seed fixture with `judge` record whose `narrative_anchor.verdict_story = "Test verdict story sentence."`, invoke `runner.invoke(cli, ["content", "--format", "blog", "--slug", "my-post", "--window", "EPIC-X"])`, assert exit 0, file at `.deviate/content/drafts/blog/my-post.md` exists, and opening paragraph contains the `verdict_story` text (per `AC-ADHOC-012-10`). (c) `test_x_thread_format`: invoke `--format x-thread --slug thread-1`, assert file at `.deviate/content/drafts/x-thread/thread-1.md` contains exactly 6 posts, each ≤ 280 characters (per `AC-ADHOC-012-11`). (d) `test_window_filter`: seed YAMLs across `EPIC-A`, `EPIC-B`, `EPIC-X`, invoke `--window EPIC-X`, assert only `EPIC-X` records surface in the synthesized draft; absence of `--window` includes all records (per `AC-ADHOC-012-08`). (e) `test_archive_flag`: invoke `--archive EPIC-X`, assert `specs/_archives/EPIC-X-narrative.tar.gz` exists, opens via `tarfile.open(mode="r:gz")`, and contains every YAML under `.deviate/content/handovers/EPIC-X/` (per `AC-ADHOC-012-09`). Tests use `runner.invoke(cli, ["content", ...])` pattern from `tests/test_cli/test_adhoc.py`; mock `deviate.cli.micro._run_pytest` per AGENTS.md performance mandate.
    - **Green**: Create `src/deviate/cli/content.py` with `content_app = typer.Typer(no_args_is_help=True, help="Content Capture commands")` exposing `@content_app.command("pre")` (thin shell — pre-context setup, no-op in v1 per macro.py pattern at lines 195-275), `@content_app.command("post")` (thin shell — persistence is automatic via `persist_handover()` from the runner), and a `@content_app.callback(invoke_without_command=True)` named-flag surface accepting `--format` (constrained to `("blog", "x-thread", "release-notes", "commit-story", "resume-bullet")` — unknown values exit non-zero with diagnostic listing the 5 valid values per `AC-ADHOC-012-07`), `--window <epic_slug>` (optional filter per `AC-ADHOC-012-08`), `--slug <name>` (default `<format>-<timestamp>`), `--archive <epic_slug>` (optional; replaces draft-write with tarball write per `AC-ADHOC-012-09`). Register via single line `cli.add_typer(content_app, name="content")` appended to the existing 23-entry block at `src/deviate/cli/__init__.py:706` region. Extend `src/deviate/core/handover.py` with `synthesize_draft(records, format, slug) -> Path` (loads template from `src/deviate/prompts/content/<format>.md` via `importlib.resources.files("deviate.prompts")`, substitutes `{{ epic_slug }}`/`{{ slug }}`/`{{ format }}`/`{{ records }}` via `str.format()`, writes to `.deviate/content/drafts/<format>/<slug>.md`) and `archive_epic(epic_slug) -> Path` (uses `tarfile.open(mode="w:gz")` to bundle every YAML under `.deviate/content/handovers/<epic_slug>/**` into `specs/_archives/<epic_slug>-narrative.tar.gz`). Create `src/deviate/prompts/skills/deviate-content/SKILL.md` with canonical frontmatter (`name: deviate-content`, `description: <FLOW-12 synthesis line>`, `category: deviatdd-macro-layer`, `version: 1.0.0`, `aliases: [/deviate-content, spec:deviate-content, content]`); body inlines the 5 supported formats, the synthesis contract (load via `load_handover_records(window)`, render via `src/deviate/prompts/content/<format>.md`, write to `.deviate/content/drafts/<format>/<slug>.md`), and the anchor-fallback rule (absence of `narrative_anchor:` → fall back to `phase` + `status` + `files`). Create 5 format templates under `src/deviate/prompts/content/`: `blog.md` (long-form post referencing `verdict_story` anchor in intro per `specs/_product/flows/flows-content-capture.md:78`), `x-thread.md` (exactly 6 posts ≤ 280 chars sliced from anchor pool), `release-notes.md`, `commit-story.md`, `resume-bullet.md`; each ≤ 50 lines.
    - **Refactor**: Extract format rendering into per-format functions `_render_<format>(records) -> str`; extract anchor extraction into `extract_anchor(phase, record) -> dict | None` helper; ensure consistent error messages across all 5 format templates (each template references `{{ records }}` exactly once); keep `synthesize_draft()` and `archive_epic()` in `handover.py` if line count stays ≤ 200, else extract to `src/deviate/core/synthesis.py` per `specs/plans/deviate-content.md:144`.
    - **Edge Cases**: Empty `.deviate/content/handovers/` → synthesis CLI exits non-zero with diagnostic pointing at `--window` filter (per `specs/_product/flows/flows-content-capture.md:58`); anchor-pool too small for x-thread → emit fewer than 6 posts and document in helper docstring; unknown `--format` value → exit non-zero with diagnostic listing the 5 valid values; `--archive` writes `specs/_archives/` parent dirs via `Path.mkdir(parents=True, exist_ok=True)`; `str.format()` substitution on template content (no Jinja2 import anywhere per Defensive Exclusion); if module line count exceeds 200, extract to `src/deviate/core/synthesis.py` and import from `content.py`.
    - **Acceptance**: `pytest tests/test_content/ -v` passes 5/5; `runner.invoke(cli, ["content", "--help"])` shows `pre|post` and 4 flags; `runner.invoke(cli, ["content", "--format", "bogus"])` exits non-zero with diagnostic listing the 5 valid formats; `src/deviate/cli/__init__.py` has exactly one new line (`cli.add_typer(content_app, name="content")`) appended at line ~707; `deviate-content/SKILL.md` frontmatter parses cleanly with the expected fields; full suite `mise run test` remains < 18s per AGENTS.md mandate; `handover.py` line count ≤ 200.
  - **Dependency**: TSK-012-01

---

## Phase 3: 15-Skill Write Instruction Cross-Cut (FLOW-11 actor wiring)
**Goal**: Append a single idempotent Write instruction to each of the 15 listed skill prompts so the LLM actor uniformly emits the per-phase YAML handover via the canonical `handover_path()` target. No body content of any existing skill is rewritten, restructured, or expanded — pure append-only with idempotency guard.

### Tasks

- TSK-012-03: Append one-sentence Write instruction to 15 skill prompts + skill prompt validation test
  - **Type**: Feature_Batch
  - **Mode**: TDD
  - **Test Strategy**: Solitary_Unit
  - **Verification**: `mise run test tests/test_handover/test_skill_prompts.py -v && mise run test tests/test_handover/test_gitignore.py -v`
  - **Estimated Time**: 60 minutes
  - **Flow References**: `[FLOW-11, FLOW-12]`
  - **Files**:
    - `src/deviate/prompts/skills/deviate-red/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-green/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-yellow/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-judge/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-refactor/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-execute/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-e2e/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-hotfix/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-prune/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-review/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-research/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-prd/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-shard/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-plan/SKILL.md` (APPEND-ONLY)
    - `src/deviate/prompts/skills/deviate-tasks/SKILL.md` (APPEND-ONLY)
    - `tests/test_handover/test_skill_prompts.py` (NEW)
    - `tests/test_handover/test_gitignore.py` (NEW)
  - **Rationale**: US-012-11 mandates uniform FLOW-11 capture across all 15 phase-related skills so a phase running for any epic/issue/task emits its YAML handover via the canonical `handover_path()` target — without this cross-cut, only the manual path via Write tool is guaranteed; the CLI path (stdout only) relies on the actor remembering the Write call. The instruction is APPEND-ONLY per Defensive Exclusion — no existing body is rewritten, restructured, or expanded — and idempotent via detection of the literal marker "handover_path()" already present (re-runs do not duplicate the sentence). AC-ADHOC-012-13 (15 skills carry the instruction) + AC-ADHOC-012-14 (.gitignore excludes both runtime-state dirs).
  - **Details**:
    - **Red**: Write `tests/test_handover/test_skill_prompts.py` with a constant `_HANDOVER_WRITE_SKILLS = ("deviate-red", "deviate-green", "deviate-yellow", "deviate-judge", "deviate-refactor", "deviate-execute", "deviate-e2e", "deviate-hotfix", "deviate-prune", "deviate-review", "deviate-research", "deviate-prd", "deviate-shard", "deviate-plan", "deviate-tasks")` (15 entries) and a `test_skill_prompts_carry_handover_write_instruction` test that iterates the tuple, reads each `src/deviate/prompts/skills/<name>/SKILL.md`, and asserts the literal marker `"handover_path()"` appears in the body (case-sensitive substring). Also write `tests/test_handover/test_gitignore.py` asserting `.deviate/.gitignore` contains both `.deviate/content/` lines (per `AC-ADHOC-012-14`); reuse the test pattern from `tests/test_cli/test_init.py` for reading root config files.
    - **Green**: For each of the 15 SKILL.md files, run a small inline Python script (or `edit` call): read the file, check whether the literal marker `"handover_path()"` is already present in the body; if absent, append a single sentence at the end of the file (just before the trailing newline if present). The sentence text (defined as a single `HANDOVER_WRITE_INSTRUCTION` constant for uniform application): `"After emitting the YAML manifest, call the Write tool to persist it at \`.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml\` per the FLOW-11 capture contract at \`src/deviate/core/handover.py:handover_path()\`."` Use the exact same constant string for all 15 files to prevent drift. Append `.deviate/content/` to `.deviate/.gitignore` (already done in TSK-012-01, this task only asserts the file content via the test).
    - **Refactor**: Centralize the instruction text as `HANDOVER_WRITE_INSTRUCTION` constant in a small helper module if drift risk emerges across re-runs; the append operation is mechanical — apply it identically to all 15 files; do NOT modify any body content of any existing skill beyond this single trailing line.
    - **Edge Cases**: Idempotency — re-running the append must NOT duplicate the instruction; the marker detection (`"handover_path()" in body`) is the only guard. The `deviate-explore` skill emits `explore.md` as its primary artifact (not a YAML manifest) and is NOT in the 15-skill list per `specs/plans/deviate-content.md:79-87` — do NOT append to it. Do NOT modify `tome-*` skills (orthogonal per Defensive Exclusion). Do NOT modify `deviate-flows/SKILL.md` (existing in-progress modification per AGENTS.md §in-progress discipline).
    - **Acceptance**: All 15 SKILL.md files contain the literal marker `"handover_path()"` in their body; no body content of any existing skill is rewritten beyond the single trailing sentence; the append is idempotent (re-running the operation does not duplicate the instruction); `pytest tests/test_handover/test_skill_prompts.py -v` passes; `pytest tests/test_handover/test_gitignore.py -v` passes; full suite `mise run test` remains < 18s; `mise run lint` reports zero ruff violations on the new test files.
  - **Dependency**: TSK-012-01

---

## Implementation Strategy
**Execution Order**:
1. Phase 1 (`TSK-012-01`) → Phase 2 (`TSK-012-02`) → Phase 3 (`TSK-012-03`)

Phases 2 and 3 both depend on Phase 1: Phase 2 imports `persist_handover` / `load_handover_records` / `HandoverRecord` from `handover.py`; Phase 3 references `handover_path()` in the appended instruction text. Phase 3 is independent of Phase 2 (it only modifies skill prompts, no Python code).

**Critical Dependency Chains**:
- `TSK-012-02` MUST follow `TSK-012-01` (synthesis CLI imports the capture helper).
- `TSK-012-03` MUST follow `TSK-012-01` (the appended sentence references `handover_path()` which only exists after Phase 1 ships).

**Risk Hotspots**:
- **Path traversal via `..` in slug/issue/task fields** (High impact, Low likelihood): `handover_path()` MUST call `Path.resolve(strict=False)` and validate the resolved path is rooted under `_HANDOVER_ROOT.resolve()` BEFORE any `mkdir` call. The Phase 1 `test_path_resolution` RED test asserts the rejection on `task_id="../../etc/passwd"`; the GREEN implementation must guard against ALL of `epic_slug`, `issue_id`, `phase`, and `task_id` containing traversal sequences. Per `specs/plans/deviate-content.md:159-167`.
- **15-skill append duplication on re-run** (Low impact, Medium likelihood): The idempotency guard is detection of the literal marker `"handover_path()"` in the file body BEFORE append. The Phase 3 `test_skill_prompts.py` test asserts the marker is present exactly once (count == 1) — accidental double-append fails the test. Per `specs/plans/deviate-content.md:166` + Defensive Exclusion §"no body content of any existing skill is rewritten, restructured, or expanded".
- **Cli registration regression** (High impact, Low likelihood): `cli.add_typer(content_app, name="content")` MUST be the SOLE modification to `src/deviate/cli/__init__.py`. No existing line touched. The existing `cli.add_typer(...)` block at lines 683-706 grows from 23 to 24 entries. `git diff src/deviate/cli/__init__.py` MUST show exactly one new line.
- **Jinja2 dependency creep** (High impact, Medium likelihood): The synthesis helper uses `str.format()` substitution ONLY. No Jinja2 import anywhere — if a future iteration requires Jinja2, that is a separate dependency-addition issue per Defensive Exclusion. Templates use `{{ key }}` placeholders compatible with `str.format_map()`.
- **`.deviate/.gitignore` regression** (Low impact, Low likelihood): The gitignore extension is append-only; the file grows from 6 to 8 lines. No existing entry touched. The Phase 1 RED test and Phase 3 `test_gitignore.py` both assert both new lines are present.
- **`synthesize_draft()` over 200-line `handover.py` boundary** (Medium impact, Low likelihood): If `handover.py` exceeds 200 lines after `synthesize_draft()` + `archive_epic()` are added, extract to `src/deviate/core/synthesis.py` per `specs/plans/deviate-content.md:144` and re-export from `handover.py` for backward-compatible imports. The synthesis module's `load_handover_records` and `HandoverRecord` references remain valid since both stay in `handover.py`.
- **Defensive Exclusion §"modify cli/__init__.py beyond one line"**: The Phase 2 RED test reads `cli/__init__.py` before GREEN implementation to snapshot the exact 23-entry block; the GREEN implementation appends exactly one `cli.add_typer(content_app, name="content")` line; the Phase 2 verification re-reads the file to assert only one new line was added.

**Merge Conflict Boundaries**:
- Files touched by multiple phases: `.deviate/.gitignore` is touched by `TSK-012-01` (append two lines) and asserted by `TSK-012-03` (test). Sequential execution (Phase 1 → Phase 3) avoids any merge conflict — Phase 1 lands the gitignore change, Phase 3 only validates it.
- `src/deviate/core/handover.py` is touched by `TSK-012-01` (creation) and `TSK-012-02` (extension with `synthesize_draft()` + `archive_epic()`). Sequential execution avoids any merge conflict — Phase 1 ships the helper, Phase 2 extends it.
- The 15 SKILL.md files in Phase 3 are mutually exclusive — no two phases touch the same skill.
- The 5 format templates + `deviate-content` skill + `content.py` are unique to Phase 2.

**Commits**:
- One commit per phase (three commits total) following the conventional commit format:
  - `feat(TSK-012-01): add handover capture helper + 4 tests + gitignore extension (FLOW-11)`
  - `feat(TSK-012-02): add deviate content CLI + deviate-content skill + 5 format templates + 5 tests (FLOW-12)`
  - `feat(TSK-012-03): append handover write instruction to 15 phase skills + validation test`
- Commits land on the existing `feat/adhoc/012-deviate-content` worktree branch (per the orchestrator's worktree setup).

---

## Universal Test Constraints (ALL TASKS)

- **Git Isolation Mandatory**: Any test that invokes git operations MUST operate on a temporary directory initialized as a fresh git repo. Tests MUST NOT run git commands within the real repository's working tree.
- **Implementation Pattern**: Use the shared `tmp_git_repo` fixture from `tests/conftest.py`. Pass `repo=tmp_git_repo` (or operate via the fixture's bound directory) to all git-interacting functions. Never reference `Path.cwd()`, `os.getcwd()`, or the real repo root in tests.
- **`_git_env()` Reuse**: Import `_git_env` from `tests.conftest` (do not redefine locally) and pass `env=_git_env()` to every `subprocess.run` call that invokes `git`. The helper strips `GIT_*` env vars to prevent parent-repo config leak.
- **`_run_pytest` Mock Mandate**: Tests that invoke CLI commands which internally call `_run_pytest` MUST mock `deviate.cli.micro._run_pytest` with `subprocess.CompletedProcess(args=[], returncode=0, stdout="...", stderr="")`. Full suite must remain < 18s.

## Universal API Design Constraint (ALL CORE MODULES)

Every git-interacting function in core modules MUST accept an optional `repo_path: Path | None = None` parameter. When `None`, default to `Path.cwd()`.

**This issue**: `src/deviate/core/handover.py` does NOT directly invoke git — git discipline is enforced by the test surface (`git ls-files --error-unmatch`) and by the `.deviate/.gitignore` exclusion. `persist_handover()` writes YAML only; no git interaction. The path-traversal guard uses `Path.resolve(strict=False)` + root-prefix check, no git.

## Universal Skill Frontmatter Invariant (NEW deviate-content SKILL.md)

The single new `src/deviate/prompts/skills/deviate-content/SKILL.md` MUST declare the frontmatter in this exact field order, matching the reference at `src/deviate/prompts/skills/deviate-constitution/SKILL.md:1-11`:

```yaml
---
name: deviate-content
description: <single-line description of FLOW-12 synthesis behavior>
category: deviatdd-macro-layer
version: 1.0.0
aliases:
  - /deviate-content
  - spec:deviate-content
  - content
---
```

- `name` MUST equal `deviate-content`.
- `description` MUST be a single-line string (no `\n` characters).
- `category` MUST equal `deviatdd-macro-layer`.
- `version` MUST equal `1.0.0`.
- `aliases` MUST be a flat YAML list (not inline `[...]` syntax) including the slash-command form (`/deviate-content`).

## Performance Targets (Recap)

- `handover.py` module line count ≤ 200 (extract to `synthesis.py` if exceeded).
- `content.py` module line count ≤ 250.
- `deviate-content/SKILL.md` body ≤ 150 lines.
- Each of the 5 format templates ≤ 50 lines.
- `handover_path()` and `persist_handover()` combined ≤ 5ms per call (filesystem-bound).
- `load_handover_records()` ≤ 100ms for 200 YAMLs (per Performance Constraint at `specs/plans/deviate-content.md:106`).
- Full test suite `mise run test` ≤ 18s.
- `mise run lint` reports zero ruff violations on `src/deviate/core/handover.py` and `src/deviate/cli/content.py`.

## Ledger Discipline Notes

- `tasks.jsonl` is append-only: each state transition (RED → GREEN → JUDGE → COMPLETED) is a separate appended line per `specs/constitution.md:1` Append-Only Ledger Protocol. Existing lines are NEVER mutated.
- `created_at` timestamps may repeat for transitions batched within the same execution run. Strictly monotonic per-task `created_at` is NOT a ledger invariant; downstream consumers pick the latest appended line per `id`.
- `specs/issues.jsonl` follows the same rule. Multiple entries for the same `issue_id` are valid; canonical state is derived by sequential parsing, last-wins.
- `flow_refs: [FLOW-11, FLOW-12]` from the issue frontmatter propagates verbatim to every emitted task via the `**Flow References**` field. Downstream micro phases (red, green, refactor, judge) MUST restate these flow references before writing code and assert the implementation serves them per Universal Invariant §8.
