## Plan Summary

- **Issue**: ISS-ADH-013 — Product-Layer YAML Handover Emission — Extend FLOW-11 to /deviate-constitution, /deviate-flows, /deviate-architecture, /deviate-release
- **Implementation Strategy**: Append the canonical `## Handover Persistence (FLOW-11)` Write instruction to the four Product-layer command files in `src/deviate/prompts/commands/`, extend the `PHASE_COMMANDS` canonical list in `tests/test_handover/test_command_prompts.py` from 15 to 19 entries, document the `.deviate/feat/_product/<skill-name>/<skill-name>.yaml` path convention via a new `## 3.8 Product-layer handover path convention` section in `specs/_product/architecture.md`, add two path-shape tests to `tests/test_handover/test_path_resolution.py`, and extend the narrative-anchor field map in `specs/plans/deviate-content.md` with four Product-layer rows — all without touching `src/deviate/core/handover.py` (sentinel `epic_slug="_product"` invocation reuses the existing function unchanged) and without amending `specs/constitution.md` (the existing Tamper Guard Content Capture exception at `specs/constitution.md:14-18` already covers `.deviate/feat/**/*.yaml` globally per the `**/*.yaml` glob).
- **Estimated Complexity**: Medium
- **Estimated Effort**: 2-4 hours (8 source/spec files touched, no new Python modules, no constitutional amendment, no signature change to `handover_path()`)

## Product Layer Anchors

- **Flow References**: [FLOW-11, FLOW-12]
- **Source**: `specs/adhoc/issues/013-product-layer-yaml-handover.md` (frontmatter field: `flow_refs`)
- **Release Context**: Extend the Content Capture release goal ("Ship the Content Capture subsystem that captures every DeviaTDD phase as a durable YAML handover (`FLOW-11`) and synthesizes those handovers into marketing-content drafts in one of five formats (`FLOW-12`)" at `specs/_product/release-next.md:4`) to cover the four Product-layer skills, so `deviate content` (FLOW-12) can pull phase-specific anchors (`principle`, `user_role`, `component`, `release_goal`) from Product-layer work.
- **Architecture Components Touched**: C8 (Handover Capture / FLOW-11) at `specs/_product/architecture.md:129-150`; C9 (Content Synthesis / FLOW-12) at `specs/_product/architecture.md:151-164`

**Invariant**: Every downstream artifact (`tasks.md`, RED tests, GREEN implementation, JUDGE verdict, E2E coverage, PR description) MUST surface these `Flow References` and verify the change serves them. A change that breaks or silently abandons a named flow MUST fail JUDGE with severity HIGH.

## Workstation Mapping

- **`src/deviate/prompts/commands/deviate-constitution.md`** — Product-layer command for FLOW-04 governance; needs FLOW-11 Write instruction.
  - **Current State**: Contains no `handover_path()` marker (verified: `grep -c "handover_path" src/deviate/prompts/commands/deviate-constitution.md` returns `0`). Existing YAML frontmatter declares `name: deviate-constitution`, `category: deviatdd-macro-layer`, `aliases:` block.
  - **Changes Required**: Append a `## Handover Persistence (FLOW-11)` section in the `<output_format_schemas>` block (matching the canonical reference shape at `src/deviate/prompts/commands/deviate-red.md`) instructing the actor to write `.deviate/feat/_product/constitution/constitution.yaml` via `handover_path("_product", "constitution", "constitution")`.
  - **Integration Surface**: `tests/test_handover/test_command_prompts.py::test_command_instruction_is_idempotent` (auto-asserted via `@pytest.mark.parametrize` over extended `PHASE_COMMANDS`); `src/deviate/core/handover.py::handover_path()` consumes the sentinel `epic_slug="_product"` unchanged.

- **`src/deviate/prompts/commands/deviate-flows.md`** — Product-layer command for FLOW-01 flow authoring; needs FLOW-11 Write instruction.
  - **Current State**: Contains no `handover_path()` marker (verified: `grep -c "handover_path" src/deviate/prompts/commands/deviate-flows.md` returns `0`). Existing frontmatter intact.
  - **Changes Required**: Append the canonical `## Handover Persistence (FLOW-11)` section instructing write to `.deviate/feat/_product/flows/flows.yaml` via `handover_path("_product", "flows", "flows")`.
  - **Integration Surface**: Same as `deviate-constitution.md`. Special note: `specs/plans/deviate-content.md:141` explicitly excluded `deviate-flows` from the original 15-skill append (in-progress modification at the time). That guard is now lifted — this issue is the canonical emission contract for `deviate-flows`.

- **`src/deviate/prompts/commands/deviate-architecture.md`** — Product-layer command for FLOW-02 architecture authoring; needs FLOW-11 Write instruction.
  - **Current State**: Contains no `handover_path()` marker (verified: `grep -c "handover_path" src/deviate/prompts/commands/deviate-architecture.md` returns `0`).
  - **Changes Required**: Append the canonical `## Handover Persistence (FLOW-11)` section instructing write to `.deviate/feat/_product/architecture/architecture.yaml` via `handover_path("_product", "architecture", "architecture")`.
  - **Integration Surface**: Same as above. Note that `deviate-architecture` already classifies changes via `Local / Context-Bridging / Context-Creating` per FLOW-02 Metrics at `specs/_product/flows/flows-product.md:63` — this classification surfaces as a `classification` anchor field for FLOW-12 synthesis (per narrative-anchor field map extension).

- **`src/deviate/prompts/commands/deviate-release.md`** — Product-layer command for FLOW-03 release authoring; needs FLOW-11 Write instruction.
  - **Current State**: Contains no `handover_path()` marker (verified: `grep -c "handover_path" src/deviate/prompts/commands/deviate-release.md` returns `0`).
  - **Changes Required**: Append the canonical `## Handover Persistence (FLOW-11)` section instructing write to `.deviate/feat/_product/release/release.yaml` via `handover_path("_product", "release", "release")`.
  - **Integration Surface**: Same as above. Release-phase handovers carry the highest-leverage synthesis anchors (`release_goal`, `included_flows`, `deferred_work`) — these flow into `deviate content --format release-notes` per `specs/_product/flows/flows-content-capture.md:82`.

- **`tests/test_handover/test_command_prompts.py`** — Canonical 15-command coverage gate; needs extension to 19 entries.
  - **Current State**: Defines `PHASE_COMMANDS: list[str]` at lines 40-58 with 15 entries (10 micro + 5 macro). `TestCommandPromptHandoverCoverage::test_canonical_skill_list_has_exactly_fifteen` at line 217 asserts `len(PHASE_COMMANDS) == 15`. `_MICRO_COMMANDS` (10) and `_MACRO_COMMANDS` (5) lists at lines 60-79. `test_command_instruction_is_idempotent` at line 196 asserts `marker_count == 1` per command via `@pytest.mark.parametrize`.
  - **Changes Required**: Extend `PHASE_COMMANDS` from 15 to 19 entries by appending a new comment block:
    ```
    # Product layer (4 skills)
    "deviate-constitution",
    "deviate-flows",
    "deviate-architecture",
    "deviate-release",
    ```
    Update `test_canonical_skill_list_has_exactly_fifteen` (rename + update assertion to `len(PHASE_COMMANDS) == 19`). The `@pytest.mark.parametrize` loops over `PHASE_COMMANDS` automatically cover the four new entries — no new test logic required. Optionally add a `_PRODUCT_COMMANDS` (4) tuple for symmetry with `_MICRO_COMMANDS` / `_MACRO_COMMANDS`.
  - **Integration Surface**: `src/deviate/core/commands.py::resolve_command(name)` consumes the extended list (one entry per command resolves to the file under `src/deviate/prompts/commands/<name>.md` per `_resolve_commands_root`).

- **`tests/test_handover/test_path_resolution.py`** — Path-shape and traversal-guard coverage; needs two new tests.
  - **Current State**: Defines `TestMacroPathShape` (lines 23-57), `TestMicroPathShape` (lines 60-131), `TestMacroMicroDistinguishability` (lines 134-147), `TestPathTraversalRejection` (lines 150-184), `TestHandoverPathModuleSurface` (lines 187-219). All tests use `handover_path(epic, issue, phase, [task_id=], repo=tmp_path)`.
  - **Changes Required**: Append two new tests (or a new `class TestProductLayerPathShape`):
    - `test_product_layer_path_shape` — asserts `handover_path("_product", "constitution", "constitution", repo=tmp_path)` returns `.deviate/feat/_product/constitution/constitution.yaml` (and analogous for the other 3 Product-layer commands: `flows`, `architecture`, `release`).
    - `test_product_layer_sentinel_passes_traversal_guard` — asserts `handover_path("_product", "..", "constitution", repo=tmp_path)` raises `PathTraversalError` (sentinel must not weaken the existing traversal guard at `src/deviate/core/handover.py:85-92`).
  - **Integration Surface**: `src/deviate/core/handover.py::handover_path()` (lines 60-92) and `_validate_segment()` (lines 45-55) — both consumed unchanged.

- **`specs/_product/architecture.md`** — Cross-epic integration contract; needs new §3.8 documentation row.
  - **Current State**: §3 Components table at lines 31-44 covers C1-C10. §3.5 (C8 / FLOW-11) at lines 129-150 documents the path convention. §3.6 (C9 / FLOW-12) at lines 151-164. §4.4 (Phase post-handler → C8 contract) at lines 215-244. §6.1 (Content Capture subgraph) at lines 297-307. §8.1 (Content Capture Constitution Cross-Check) at lines 333-348. FLOW-02 governance of `.deviate/feat/` root at line 299.
  - **Changes Required**: Append a new `### 3.8 Product-layer handover path convention` section after `### 3.7 C10 — Format Template Pack (FLOW-12)` documenting: (a) Macro handover (Product layer) path is `.deviate/feat/_product/<skill-name>/<skill-name>.yaml`; (b) implementation invokes `handover_path("_product", "<skill-name>", "<skill-name>")` via the sentinel `epic_slug`; (c) underscore-prefix on `_product` distinguishes Product-layer origin from real epic slugs (per-directory-name 1:1 with `specs/_product/`); (d) `.deviate/feat/` remains the single top-level root (FLOW-02 governance at line 299 unchanged); (e) path-traversal guard at `_validate_segment()` and `resolved_target.relative_to(resolved_root)` applies unchanged.
  - **Integration Surface**: `src/deviate/core/handover.py` (path convention reference); cross-epic readers (`specs/_product/flows/flows-content-capture.md` documents `.deviate/feat/_product/**` in subsequent revisions).

- **`specs/plans/deviate-content.md`** — Authoritative Content Capture plan; needs narrative-anchor field map extension.
  - **Current State**: Path convention table at lines 41-48 (Macro/Micro rows). Narrative anchor field map at lines 52-67 (12 rows for Macro/Meso/Micro phases — `deviate-explore` through `deviate-e2e`). Persistence flow diagram at lines 64-73.
  - **Changes Required**: Extend the narrative-anchor field map with 4 Product-layer rows after the existing 12:
    - `deviate-constitution` → `principle`, `enforcement_scope`, `exception_boundary`
    - `deviate-flows` → `user_role`, `trigger`, `success_signal`
    - `deviate-architecture` → `component`, `integration_contract`, `classification` (Local/Context-Bridging/Context-Creating per FLOW-02 Metrics at `specs/_product/flows/flows-product.md:63`)
    - `deviate-release` → `release_goal`, `included_flows`, `deferred_work`
    Per `specs/_product/flows/flows-content-capture.md:55-56`, absence of `narrative_anchor:` on any YAML is non-fatal — these fields are optional.
  - **Integration Surface**: `src/deviate/core/synthesis.py::extract_anchor(phase, record)` (deferred; this issue only extends the field map, not the extraction logic). Future `deviate content` invocations can pull the new fields when present.

## Implementation Strategy

- **Phase 1**: Skill command appends + test list extension
  - **Files**: `src/deviate/prompts/commands/deviate-{constitution,flows,architecture,release}.md` (4 files), `tests/test_handover/test_command_prompts.py` (1 file)
  - **Approach**: For each of the four Product-layer commands, append the canonical `## Handover Persistence (FLOW-11)` section inside the `<output_format_schemas>` block (or as a sibling section if no XML wrapper), matching the reference shape at `src/deviate/prompts/commands/deviate-red.md`. Use the sentinel `epic_slug="_product"` invocation pattern: `handover_path("_product", "<skill-name>", "<skill-name>")`. Concurrently extend `PHASE_COMMANDS` from 15 to 19 entries and rename `test_canonical_skill_list_has_exactly_fifteen` to `test_canonical_skill_list_has_exactly_nineteen` with `len(PHASE_COMMANDS) == 19` assertion. The `@pytest.mark.parametrize` decorators on `test_command_has_write_instruction`, `test_command_references_canonical_handover_path`, `test_command_instruction_lives_in_terminal_contract_section`, `test_command_instruction_is_idempotent`, `test_command_file_resolves_and_exists`, `test_command_keeps_frontmatter_name`, and `test_command_keeps_output_format_schemas_close_tag` automatically cover the four new entries.
  - **Verification**: `grep -c "handover_path()" src/deviate/prompts/commands/deviate-{constitution,flows,architecture,release}.md` returns `1` for each file. `mise run test tests/test_handover/test_command_prompts.py -v` passes 19 iterations of each parameterized test. `mise run test` finishes in < 18s per AGENTS.md performance mandate. `mise run lint` reports zero ruff violations.

- **Phase 2**: Path-convention tests + architecture documentation + narrative-anchor field map
  - **Files**: `tests/test_handover/test_path_resolution.py` (1 file), `specs/_product/architecture.md` (1 file), `specs/plans/deviate-content.md` (1 file)
  - **Approach**: Append `class TestProductLayerPathShape` (or two new test methods) to `tests/test_handover/test_path_resolution.py` validating (a) the four sentinel `handover_path()` calls return the canonical paths, and (b) `handover_path("_product", "..", "constitution")` raises `PathTraversalError`. Concurrently append `### 3.8 Product-layer handover path convention` to `specs/_product/architecture.md` (after `### 3.7 C10`), declaring the path convention, sentinel invocation pattern, and FLOW-02 governance continuity. Concurrently extend the narrative-anchor field map in `specs/plans/deviate-content.md` (12 → 16 rows).
  - **Verification**: `mise run test tests/test_handover/test_path_resolution.py -v` passes all 4 new assertions. `grep -A 20 "Product-layer handover path convention" specs/_product/architecture.md` returns the new section. `grep -cE "^\| (deviate-constitution|deviate-flows|deviate-architecture|deviate-release)" specs/plans/deviate-content.md` returns ≥ 4 matches. End-to-end smoke: simulate the four Product-layer invocations via `persist_handover("_product", "<skill>", "<skill>", manifest)` against a temp git repo; `.deviate/feat/_product/*.yaml` all exist, parse as valid YAML, and `git ls-files --error-unmatch` returns non-zero for each (not staged in git index). `head -20 specs/constitution.md` still reads `Version: 0.3.0` (no amendment).

## Data Flow Analysis

- **Input flow**: A developer runs `/deviate-constitution`, `/deviate-flows`, `/deviate-architecture`, or `/deviate-release` (slash command in any supported agent — claude, opencode, factory, pi). The agent invokes the corresponding command file under `src/deviate/prompts/commands/`. The command file's `<output_format_schemas>` block (extended by this issue to include `## Handover Persistence (FLOW-11)`) instructs the agent to emit a YAML manifest on stdout AND call the Write tool to persist it at the canonical Product-layer path.
- **Transformation**: The agent constructs the manifest with `phase`, `status`, `files`, and optional `narrative_anchor:` blocks (per the anchor field map extended by this issue). The agent invokes `handover_path("_product", "<skill-name>", "<skill-name>")` (sentinel invocation) to compute the canonical path: `.deviate/feat/_product/<skill-name>/<skill-name>.yaml`.
- **Validation**: `src/deviate/core/handover.py::_validate_segment()` (lines 45-55) accepts the underscore-prefixed `_product` sentinel because it is non-empty, stripped, and contains no whitespace, no path separators, no `..`, and is not absolute. The final `resolved_target.relative_to(resolved_root)` check at lines 85-92 guarantees the path stays under `.deviate/feat/` (rejects traversal attempts).
- **Write**: The agent uses the Write tool to persist the YAML at the canonical path. `.deviate/.gitignore` already excludes `/feat/` (per `specs/plans/deviate-content.md:17-19`), so Product-layer YAMLs are gitignored runtime state — no commit, no ledger append.
- **Storage**: `.deviate/feat/_product/{constitution,flows,architecture,release}.yaml` (4 new file paths under the existing `.deviate/feat/` root; no new top-level directory introduced — FLOW-02 governance at `specs/_product/architecture.md:299` unchanged).
- **Output flow (downstream)**: When `deviate content --format <blog|x-thread|release-notes|commit-story|resume-bullet> --window _product` runs, `src/deviate/core/synthesis.py::load_handover_records(window="_product")` returns the four Product-layer records (plus any Macro/Meso/Micro records when no window is specified). FLOW-12 synthesis pulls `narrative_anchor` fields per the extended field map (`principle`, `user_role`, `component`, `release_goal`, etc.) when present; falls back to `phase` + `status` + `files` + git-log metadata when absent (per `specs/_product/flows/flows-content-capture.md:55-56` non-fatal contract).
- **Constitutional surface**: This issue adds zero new contracts; it extends the existing FLOW-11 emission contract (15 → 19 skills), the existing FLOW-11 path convention (4 new Product-layer paths under the existing `.deviate/feat/` root), and the existing FLOW-12 anchor-extraction contract (4 new Product-layer anchor rows). Constitution §1 Tamper Guard Content Capture exception at `specs/constitution.md:14-18` covers `.deviate/feat/**/*.yaml` globally — no amendment needed.

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Explore artifact references stale paths (`src/deviate/prompts/skills/` and `tests/test_handover/test_skill_prompts.py`) that do not match the current repo layout (`src/deviate/prompts/commands/` and `tests/test_handover/test_command_prompts.py`) | Medium | High | Use `git grep` / `find` to verify the actual current paths before editing. The plan.md workstation mapping above documents the corrected paths. Cross-reference `src/deviate/core/commands.py::resolve_command` to confirm the live command location. |
| Sentinel `epic_slug="_product"` collides with a real epic slug chosen by a developer | Medium | Low | Document the reserved-underscore-prefix convention in `specs/_product/architecture.md` §3.8 (epic slugs starting with `_` are reserved for framework use). Add a runtime warning in `deviate explore` if `epic_slug="_product"` is invoked (deferred — out of scope for this issue per `specs/explore/product-layer-yaml.md:13-14`). |
| `deviate-flows` SKILL.md was deliberately excluded from the original 15-skill append per `specs/plans/deviate-content.md:141` ("Do NOT modify `deviate-flows/SKILL.md` (existing in-progress modification per AGENTS.md §in-progress discipline)") | Medium | Low | That guard is documented as a scope guard from FR-ADHOC-012. By FR-ADHOC-013 (this issue) the in-progress modification has concluded; the guard is lifted. The plan's workstation mapping for `deviate-flows.md` confirms the current state is `marker_count == 0` and the change appends the canonical Write instruction. |
| Append operation not idempotent — re-running against an already-instrumented Product-layer command duplicates the Write instruction | High | Low | The existing `test_command_instruction_is_idempotent` parameterized assertion at `tests/test_handover/test_command_prompts.py:196-211` enforces `marker_count == 1`. The reference shape at `src/deviate/prompts/commands/deviate-red.md` documents the canonical sentence — the implementation must check for `## Handover Persistence (FLOW-11)` presence and skip if already present. |
| Path traversal via sentinel (`_product` + `..` segment) bypasses the existing guard | High | Low | The new `test_product_layer_sentinel_passes_traversal_guard` test asserts `handover_path("_product", "..", "constitution")` raises `PathTraversalError`. `_validate_segment()` at `src/deviate/core/handover.py:45-55` rejects `..` in any segment (line 53: `if value in {"..", "."} or value.startswith(".."):`) — the test verifies the sentinel does not weaken this guard. |
| Full test suite exceeds 18s performance budget after the 4 new skill commands × 7 parameterized tests = 28 new assertion executions | Medium | Low | Per `specs/explore/product-layer-yaml.md:227` and issue Scenario 013-10, the assertions are `marker_count == 1`-style string checks, each ≤ 5ms. 28 new assertions × 5ms = 140ms total. New `TestProductLayerPathShape` adds 4 path-shape tests (~50ms each = 200ms) + 1 traversal-guard test (~50ms) = 250ms. Total budget impact: ~390ms — well under the 18s envelope. |
| Narrative anchor field map extension breaks `extract_anchor()` if it expects only the 12 known rows | Medium | Low | Per `specs/_product/flows/flows-content-capture.md:55-56`, absence of `narrative_anchor:` is non-fatal and synthesis falls back to `phase` + `status` + `files` + git-log metadata. The `HandoverRecord` Pydantic model uses `extra="allow"` (`src/deviate/core/handover.py:24-39`) — new anchor fields slot in without schema change. `extract_anchor()` (if it exists) must return `None` for unrecognized fields, not raise. |
| Constitution §1 Tamper Guard exception does not actually cover the new Product-layer paths | High | Very Low | Verified: `specs/constitution.md:14-18` declares "micro-layer skill actors are permitted to write to `.deviate/feat/**/*.yaml`" — the `**/*.yaml` glob recursively matches `.deviate/feat/_product/**/*.yaml`. AC-ADHOC-013-08 asserts this empirically. No amendment required. |
| Implementation regenerates `deviate-flows/SKILL.md` instead of appending (violates scope) | Medium | Low | Implementation must (a) read the file, (b) check for `## Handover Persistence (FLOW-11)` presence, (c) append only when absent. The terminal contract block must remain intact. Verified by `test_command_keeps_output_format_schemas_close_tag` at `tests/test_handover/test_command_prompts.py:262-279`. |
| NO_FLOW_INHERITANCE — issue has no `flow_refs` and no Product-layer mapping could be inferred | Medium | Low | Not applicable. Issue frontmatter carries `flow_refs: [FLOW-11, FLOW-12]` (verbatim at `specs/adhoc/issues/013-product-layer-yaml-handover.md:7`). The `## Product Layer Anchors` section above mirrors these references. |
| PRODUCT_LAYER_ABSENT — `specs/_product/` directory not present | Low | Very Low | Not applicable. `specs/_product/` exists with `architecture.md`, `domain-model.md`, `release-next.md`, `flows/`, `flows/index.md`, `flows/flows-content-capture.md`, `flows/flows-product.md`, `flows/flows-tome.md` — verified by `ls specs/_product/`. |
| `deviate content --window _product` synthesis filter does not match the underscore-prefixed path glob | Medium | Medium | The window-filter logic at `src/deviate/core/synthesis.py::load_handover_records(window)` accepts a string window. The `--window _product` flag must pass the sentinel verbatim. If the filter uses `Path.match()` or `fnmatch.fnmatch()`, the underscore-prefixed path must match `.deviate/feat/_product/**`. Verification deferred to integration testing — the path-shape tests in this issue cover the path-computation surface only. Edge case noted in issue `## Edge Cases and Boundaries`. |

## Integration Points

- **`src/deviate/core/handover.py::handover_path()`** (lines 60-92): Consumes the sentinel `epic_slug="_product"` argument unchanged. Returns `.deviate/feat/_product/<skill-name>/<skill-name>.yaml`. No signature change.
- **`src/deviate/core/handover.py::_validate_segment()`** (lines 45-55): Consumes each path segment (epic_slug, issue_id, phase, task_id). Accepts the underscore-prefixed `_product` sentinel (non-empty, stripped, no whitespace, no path separators, no `..`, not absolute). The traversal guard at line 53 (`if value in {"..", "."} or value.startswith(".."): raise PathTraversalError`) is what `test_product_layer_sentinel_passes_traversal_guard` exercises.
- **`src/deviate/core/commands.py::resolve_command(name)`**: Resolves each of the 4 Product-layer command names (`deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release`) to the file at `src/deviate/prompts/commands/<name>.md` via `_resolve_commands_root()`. The extended `PHASE_COMMANDS` list (15 → 19) is consumed by `tests/test_handover/test_command_prompts.py::resolve_command(name)` calls inside the parameterized test methods.
- **`src/deviate/core/synthesis.py::load_handover_records(window)`**: Reads YAMLs from `.deviate/feat/**` via `Path.rglob`. Future `--window _product` invocations (out of scope for this issue per `specs/explore/product-layer-yaml.md:13-14`) filter to `.deviate/feat/_product/**`. The path-shape contract established by this issue's `### 3.8` documentation row enables downstream synthesis filter extensions.
- **`src/deviate/core/handover.py::HandoverRecord`** (lines 24-39): Pydantic model with `model_config = ConfigDict(extra="allow")` — Product-layer anchor fields (`principle`, `user_role`, `component`, `release_goal`, etc.) slot in without schema change.
- **`tests/test_handover/test_command_prompts.py::PHASE_COMMANDS`**: Extended from 15 to 19 entries. `@pytest.mark.parametrize` decorators on 7 test methods automatically iterate over the extended list, asserting `handover_path()` marker presence, idempotency, terminal-section location, canonical path reference, file existence, frontmatter integrity, and `<output_format_schemas>` close-tag presence — for all 4 new Product-layer commands.
- **`specs/_product/architecture.md::§ 3.5 C8 — Handover Capture (FLOW-11)`** (lines 129-150): The new `### 3.8` section extends this component documentation. C8's path convention at lines 134-138 currently declares only Macro (`<epic>/<issue>/<phase>`) and Micro (`<epic>/<issue>/<task>/<phase>`) shapes — the new §3.8 adds the Product-layer third shape without modifying the existing C8 entry.
- **`specs/plans/deviate-content.md::### Narrative anchor field`** (lines 52-67): The extended 12 → 16 row table becomes the authoritative anchor field map for FLOW-12 synthesis. `src/deviate/core/synthesis.py::extract_anchor(phase, record)` (if/when implemented) reads this map.
- **`specs/constitution.md::§ 1 Tamper Guard Content Capture exception`** (lines 14-18): The `**/*.yaml` glob covers `.deviate/feat/_product/**/*.yaml` recursively — no amendment required. This is asserted by AC-ADHOC-013-08.

## Target File Structure

The following target workstation files have been pre-scanned with structural analysis. Each entry shows the detected language, extracted symbols (functions, classes, interfaces, etc.), and import/include/using blocks. Path notation is corrected from the `specs/explore/product-layer-yaml.md` reference to match the actual current repo layout — the explore artifact's references to `src/deviate/prompts/skills/` and `tests/test_handover/test_skill_prompts.py` are stale (the `refactor(prompts)!: ship commands-only v2.0 layout` commit moved skills to `src/deviate/prompts/commands/` and the test was renamed to `tests/test_handover/test_command_prompts.py`).

### `src/deviate/prompts/commands/deviate-constitution.md` (Language: markdown)
- **Symbols**:
  - entry `## Handover Persistence (FLOW-11)` (TO BE APPENDED — currently absent; reference shape at `src/deviate/prompts/commands/deviate-red.md`)
- **Imports**: (N/A — Markdown command prompt consumed by agent runtime, not imported by Python)
- **Notes**: Currently lacks `handover_path()` marker (`grep -c "handover_path" src/deviate/prompts/commands/deviate-constitution.md` returns `0`). Append the canonical Write instruction inside the `<output_format_schemas>` block (or as a sibling section if no XML wrapper), targeting `.deviate/feat/_product/constitution/constitution.yaml` via sentinel `handover_path("_product", "constitution", "constitution")`.

### `src/deviate/prompts/commands/deviate-flows.md` (Language: markdown)
- **Symbols**:
  - entry `## Handover Persistence (FLOW-11)` (TO BE APPENDED — currently absent; reference shape at `src/deviate/prompts/commands/deviate-red.md`)
- **Imports**: (N/A — Markdown command prompt)
- **Notes**: Currently lacks `handover_path()` marker (`grep -c "handover_path" src/deviate/prompts/commands/deviate-flows.md` returns `0`). Original 15-skill append contract at `specs/plans/deviate-content.md:141` deliberately excluded `deviate-flows` — that guard is lifted by FR-ADHOC-013. Append canonical Write instruction targeting `.deviate/feat/_product/flows/flows.yaml`.

### `src/deviate/prompts/commands/deviate-architecture.md` (Language: markdown)
- **Symbols**:
  - entry `## Handover Persistence (FLOW-11)` (TO BE APPENDED — currently absent)
- **Imports**: (N/A)
- **Notes**: Currently lacks `handover_path()` marker (`grep -c "handover_path" src/deviate/prompts/commands/deviate-architecture.md` returns `0`). Append canonical Write instruction targeting `.deviate/feat/_product/architecture/architecture.yaml`. Note that `deviate-architecture` already classifies changes via `Local / Context-Bridging / Context-Creating` per FLOW-02 Metrics at `specs/_product/flows/flows-product.md:63` — this classification surfaces as a `classification` anchor field for FLOW-12 synthesis.

### `src/deviate/prompts/commands/deviate-release.md` (Language: markdown)
- **Symbols**:
  - entry `## Handover Persistence (FLOW-11)` (TO BE APPENDED — currently absent)
- **Imports**: (N/A)
- **Notes**: Currently lacks `handover_path()` marker (`grep -c "handover_path" src/deviate/prompts/commands/deviate-release.md` returns `0`). Append canonical Write instruction targeting `.deviate/feat/_product/release/release.yaml`. Release-phase handovers carry the highest-leverage synthesis anchors (`release_goal`, `included_flows`, `deferred_work`) — these flow into `deviate content --format release-notes` per `specs/_product/flows/flows-content-capture.md:82`.

### `tests/test_handover/test_command_prompts.py` (Language: python)
- **Symbols**:
  - entry `PHASE_COMMANDS: list[str]` (line 40, 15 entries: 10 micro + 5 macro) — TO BE EXTENDED to 19 entries by appending Product-layer block
  - entry `_MICRO_COMMANDS: list[str]` (line 60, 10 entries)
  - entry `_MACRO_COMMANDS: list[str]` (line 73, 5 entries)
  - function `_extract_terminal_section(text: str) -> str | None` (line 82) — extracts terminal-contract section (XML tags + markdown heading fallback)
  - class `TestCommandPromptHandoverInstruction`
  - function `test_command_has_write_instruction(self, command_name: str) -> None` (line 132, parametrized over `PHASE_COMMANDS`)
  - function `test_command_references_canonical_handover_path(self, command_name: str) -> None` (line 145, parametrized)
  - function `test_command_instruction_lives_in_terminal_contract_section(self, command_name: str) -> None` (line 165, parametrized)
  - function `test_command_instruction_is_idempotent(self, command_name: str) -> None` (line 196, parametrized — asserts `marker_count == 1`)
  - class `TestCommandPromptHandoverCoverage`
  - function `test_canonical_skill_list_has_exactly_fifteen(self) -> None` (line 217 — TO BE RENAMED to `test_canonical_skill_list_has_exactly_nineteen` and assertion updated to `len(PHASE_COMMANDS) == 19`)
  - function `test_canonical_skill_list_has_no_duplicates(self) -> None` (line 222)
  - function `test_micro_layer_covers_ten_skills(self) -> None` (line 227)
  - function `test_macro_layer_covers_five_skills(self) -> None` (line 233)
  - function `test_command_file_resolves_and_exists(self, command_name: str) -> None` (line 240, parametrized)
  - class `TestCommandPromptHandoverNonRegressions`
  - function `test_command_keeps_frontmatter_name(self, command_name: str) -> None` (line 252, parametrized)
  - function `test_command_keeps_output_format_schemas_close_tag(self, command_name: str) -> None` (line 262, parametrized)
- **Imports**:
  - `from __future__ import annotations`
  - `import pytest`
  - `from deviate.core.commands import resolve_command`
- **Notes**: The `@pytest.mark.parametrize("command_name", PHASE_COMMANDS)` decorators on 7 test methods automatically cover the 4 new Product-layer commands once `PHASE_COMMANDS` is extended — zero new test methods required for skill-list coverage.

### `tests/test_handover/test_path_resolution.py` (Language: python)
- **Symbols**:
  - class `TestMacroPathShape`
  - class `TestMicroPathShape`
  - class `TestMacroMicroDistinguishability`
  - class `TestPathTraversalRejection`
  - class `TestHandoverPathModuleSurface`
  - function `test_macro_path_for_explore_phase(self, tmp_path)` (line 26)
  - function `test_macro_path_for_research_phase(self, tmp_path)` (line 33)
  - function `test_macro_path_for_prd_phase(self, tmp_path)` (line 40)
  - function `test_macro_path_for_shard_phase(self, tmp_path)` (line 46)
  - function `test_macro_path_returns_pathlib_path(self, tmp_path)` (line 53)
  - function `test_micro_path_for_red_phase(self, tmp_path)` (line 63)
  - function `test_micro_path_for_green_phase(self, tmp_path)` (line 71)
  - function `test_micro_path_for_judge_phase(self, tmp_path)` (line 85)
  - function `test_micro_path_for_refactor_phase(self, tmp_path)` (line 99)
  - function `test_micro_path_distinguishes_tasks(self, tmp_path)` (line 113)
  - function `test_micro_path_includes_task_segment_in_chain(self, tmp_path)` (line 123)
  - function `test_macro_and_micro_paths_differ_for_same_phase(self, tmp_path)` (line 137)
  - function `test_macro_path_has_no_task_segment(self, tmp_path)` (line 144)
  - function `test_parent_dir_segment_in_epic_rejected(self, tmp_path)` (line 159)
  - function `test_parent_dir_segment_in_issue_rejected(self, tmp_path)` (line 163)
  - function `test_parent_dir_segment_in_task_id_rejected(self, tmp_path)` (line 167)
  - function `test_absolute_path_in_task_id_rejected(self, tmp_path)` (line 173)
  - function `test_path_traversal_does_not_create_files(self, tmp_path)` (line 179)
  - function `test_handover_path_is_callable(self, tmp_path)` (line 190)
  - function `test_module_exports_persist_handover(self)` (line 193)
  - function `test_module_exports_load_handover_records(self)` (line 198)
  - function `test_module_exports_handover_record_model(self)` (line 203)
  - function `test_product_layer_path_shape(self, tmp_path)` (TO BE APPENDED — new test asserting 4 sentinel `handover_path()` calls return canonical paths)
  - function `test_product_layer_sentinel_passes_traversal_guard(self, tmp_path)` (TO BE APPENDED — new test asserting `handover_path("_product", "..", "constitution")` raises `PathTraversalError`)
- **Imports**:
  - `from __future__ import annotations`
  - `import pytest`
  - `from deviate.core.handover import PathTraversalError, handover_path`
- **Notes**: Two new tests to be appended (either as new methods or grouped into a new `class TestProductLayerPathShape`). Both tests use `tmp_path` fixture per existing convention.

### `specs/_product/architecture.md` (Language: markdown)
- **Symbols**:
  - entry `## 3. Components` (line 31) — Components table C1-C10
  - entry `### 3.5 C8 — Handover Capture (FLOW-11)` (line 129) — documents `.deviate/feat/<epic>/<issue>/[<task>/]<phase>.yaml` path convention
  - entry `### 3.6 C9 — Content Synthesis (FLOW-12)` (line 151)
  - entry `### 3.7 C10 — Format Template Pack (FLOW-12)` (line 166)
  - entry `### 3.8 Product-layer handover path convention` (TO BE APPENDED after line 178 — declares the `.deviate/feat/_product/<skill-name>/<skill-name>.yaml` convention, sentinel invocation pattern, FLOW-02 governance continuity, and traversal-guard applicability)
  - entry `## 6.1 Content Capture subgraph` (line 297) — references FLOW-02 governance of `.deviate/feat/` root
  - entry `## 8.1 Content Capture Constitution Cross-Check` (line 333) — satisfies §2 Backend (Python 3.13 + Typer), §2 Database (no persistent database), §2 Infrastructure (Aider micro-sandbox for `src/**/*.py` — Product-layer skills operate at prompt layer), §1 Append-Only Ledger Protocol (satisfied with note: Content Capture YAMLs are NOT a ledger), §1 Three-Layer Architecture (satisfied: Content Capture adds post-handler step, does not introduce new layer)
- **Imports**: (N/A — Markdown)
- **Notes**: §3.8 must declare all five points (a-e) per issue Scenario 013-06 / AC-ADHOC-013-05.

### `specs/plans/deviate-content.md` (Language: markdown)
- **Symbols**:
  - entry `### Persistence flow` (line 64) — manual + CLI path persistence diagram
  - entry `### Path convention` (line 41) — Macro/Micro handover paths (4 rows)
  - entry `### Narrative anchor field` (line 52) — 12-row anchor field map (Macro/Meso/Micro phases only) — TO BE EXTENDED with 4 Product-layer rows
  - entry `### File changes` (line 79) — 15-skill modification list (extension point)
  - entry `## Task decomposition` (line 100) — 2-task breakdown (Capture + Synthesis)
  - entry `## Risks` (line 154) — risk register
  - entry `## Verification` (line 184) — `mise run test`, `mise run test-e2e` validation
  - entry `## Out of scope (v1)` (line 197) — `specs/narrative.jsonl`, engagement metrics, LLM refinement, auto-publish, cross-repo aggregation, tome-* skill integration
- **Imports**: (N/A — Markdown)
- **Notes**: The 4 new Product-layer anchor rows must be appended after the existing 12 rows (lines 52-67). The table is the authoritative anchor field map for FLOW-12 synthesis.

### `src/deviate/core/handover.py` (Language: python)
- **Symbols**:
  - class `PathTraversalError(ValueError)` (line 17) — diagnostic exception for path-escape attempts
  - class `HandoverRecord(BaseModel)` (line 24) — read-side Pydantic model with `extra="allow"`
  - constant `_HANDOVER_ROOT = Path(".deviate") / "feat"` (line 41)
  - constant `_YAML_SUFFIX = ".yaml"` (line 43)
  - function `_validate_segment(label: str, value: str) -> str` (line 45) — rejects segments that could escape `.deviate/feat/`
  - function `handover_path(epic_slug: str, issue_id: str, phase: str, task_id: str | None = None, repo: Path | None = None) -> Path` (line 60) — pure path computation; consumes sentinel `epic_slug="_product"` unchanged
  - function `persist_handover(epic_slug: str, issue_id: str, phase: str, manifest: str, task_id: str | None = None, repo: Path | None = None) -> Path` (line 94) — write-or-skip; idempotent
  - function `load_handover_records(window: ...) -> list[HandoverRecord]` — chronological read
- **Imports**:
  - `from __future__ import annotations`
  - `from pathlib import Path`
  - `from typing import Any`
  - `from pydantic import BaseModel, ConfigDict`
  - `from deviate.core.yaml_repair import safe_load_yaml`
- **Notes**: NO MODIFICATION. The sentinel `epic_slug="_product"` invocation reuses the existing function unchanged. The `_validate_segment()` helper (line 53: `if value in {"..", "."} or value.startswith(".."): raise PathTraversalError`) is what guarantees the sentinel does not weaken the traversal guard — verified by the new `test_product_layer_sentinel_passes_traversal_guard` test.

### `specs/_product/release-next.md` (Language: markdown)
- **Symbols**:
  - entry `# Release: Content Capture Subsystem` (line 1) — current release goal
  - entry `## Goal` (line 3) — ship Content Capture subsystem capturing every DeviaTDD phase as YAML handover (FLOW-11) and synthesizing in 5 formats (FLOW-12)
  - entry `## Constraints` (line 7) — YAML files ARE the ledger; skill actor writes; no commit on handover YAMLs; path convention governed by FLOW-02; HandoverRecord read-side only; anchors non-fatal; path traversal rejected at `pathlib` boundary; stack consistency (Python 3.13 + Typer); cross-cutting surface bounded (15 modified skills in v1); v1 single-repo; no auto-publish
  - entry `## Included Flows` (line 21) — FLOW-11, FLOW-12
  - entry `## Included Work` (line 27) — Content Capture Subsystem / ADHOC / [FLOW-11, FLOW-12] / planned
  - entry `## Deferred Epics` (line 32) — `--refine`, cross-repo aggregation, engagement metrics, auto-publish, `specs/narrative.jsonl`, write-side persistence model, tome-* skill engagement, per-format sub-skills
  - entry `## Acceptance Criteria` (line 42) — 13 AC items
- **Imports**: (N/A — Markdown)
- **Notes**: This release goal is the canonical reference for the FLOW-11 / FLOW-12 surface area. The current AC at `specs/_product/release-next.md:51` ("Fifteen existing skill prompts ... each contain a one-sentence Write instruction ...") extends to 19 entries by this issue. No `release-next.md` modification is required (the AC at line 51 is informational and lists the 15-skill baseline; the 19-skill extension is captured in the new §3.8 documentation row in `specs/_product/architecture.md` instead).

### `specs/constitution.md` (Language: governance)
- **Symbols**:
  - entry `Version: 0.3.0` (line 1) — current version (UNCHANGED by this issue)
  - entry `## 1. Architectural Principles` (line 5) — Three-Layer Architecture (Macro / Meso / Micro); Append-Only Ledger Protocol; Git Isolation Principle; Tamper Guard & Micro-Sandboxing (with Content Capture runtime-state exception at lines 14-18); Human-in-the-Loop (HITL); Session Continuity; Model Tiering; Config-Driven Model Routing
  - entry `## 2. Tech Stack Standards` (line 19) — Python 3.13, Typer CLI, Rich terminal I/O; no frontend, no database, JSONL ledgers + TOML config; Aider micro-sandbox; git version control; uv/pytest/ruff/bats/mise tooling
  - entry `## 3. Testing Protocols` (line 36) — pytest framework, >= 80% coverage, RED phase fails with `AssertionError`/`NotImplementedError`, GREEN phase passes all tests, REFACTOR regression gate
  - entry `## 5. Definition of Done` (line 56) — 8-item DoD checklist
  - entry `## 6. Version History` (line 67) — v0.1.0 (initial), v0.2.0 ([models] config), v0.3.0 (Content Capture exception)
- **Imports**: (N/A — Governance document)
- **Notes**: NO AMENDMENT REQUIRED. The existing Tamper Guard Content Capture exception at lines 14-18 ("micro-layer skill actors are permitted to write to `.deviate/feat/**/*.yaml`") covers `.deviate/feat/_product/**/*.yaml` recursively via the `**/*.yaml` glob. The Three-Layer Architecture definition at line 9 (Macro / Meso / Micro) remains unchanged — the Product layer remains implicit per the existing release policy at `specs/_product/release-next.md:4` ("Minimal cli implementation. Keep it agent-centric"). Version remains `0.3.0`.

### `tests/test_handover/test_path_resolution.py` (Language: python)
- **Symbols**: (see above — existing TestMacroPathShape, TestMicroPathShape, TestMacroMicroDistinguishability, TestPathTraversalRejection, TestHandoverPathModuleSurface classes plus the two new tests)
- **Imports**: (see above)
- **Notes**: Two new test methods appended. No new test files created (per AC-ADHOC-013-10 "the new tests are appended to existing test files (no new test files created)"). The Python file remains ruff-clean.