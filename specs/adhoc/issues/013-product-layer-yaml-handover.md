---
title: "Product-Layer YAML Handover Emission — Extend FLOW-11 to /deviate-constitution, /deviate-flows, /deviate-architecture, /deviate-release"
labels: [enhancement, adhoc, vertical-slice, content-capture, product-layer, handover]
blocked_by: []
coordinates_with: []
issue_id: ISS-ADH-013
flow_refs: [FLOW-11, FLOW-12]
---

## System Topology Mapping
- **Epic Target Domain**: `specs/adhoc/` + Product-layer skill directories under `src/deviate/prompts/skills/`
- **Local Issue File**: `specs/adhoc/issues/013-product-layer-yaml-handover.md`
- **Primary Architectural Workstations**:
  - `src/deviate/prompts/skills/deviate-constitution/SKILL.md` — MODIFY: append one-sentence FLOW-11 Write instruction to `## Handover Persistence (FLOW-11)` terminal-contract section, referencing the canonical target `.deviate/content/handovers/_product/constitution/constitution.yaml`. Implementation calls `handover_path("_product", "constitution", "constitution")` via the sentinel `epic_slug` argument. Source: `specs/explore/product-layer-yaml.md:135-141`.
  - `src/deviate/prompts/skills/deviate-flows/SKILL.md` — MODIFY: same append shape, canonical target `.deviate/content/handovers/_product/flows/flows.yaml`; sentinel call `handover_path("_product", "flows", "flows")`.
  - `src/deviate/prompts/skills/deviate-architecture/SKILL.md` — MODIFY: same append shape, canonical target `.deviate/content/handovers/_product/architecture/architecture.yaml`; sentinel call `handover_path("_product", "architecture", "architecture")`.
  - `src/deviate/prompts/skills/deviate-release/SKILL.md` — MODIFY: same append shape, canonical target `.deviate/content/handovers/_product/release/release.yaml`; sentinel call `handover_path("_product", "release", "release")`.
  - `tests/test_handover/test_skill_prompts.py` — MODIFY: extend `PHASE_SKILLS` list at lines 28-50 from 15 to 19 entries by appending a `# Product layer (4 skills)` comment block with `deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release`. The existing `@pytest.mark.parametrize` loop at line 161-171 (`test_skill_instruction_is_idempotent`) automatically iterates over the extended list — no new test logic required.
  - `tests/test_handover/test_path_resolution.py` — MODIFY: append two new tests `test_product_layer_path_shape` (asserts the four sentinel `handover_path()` calls return canonical paths) and `test_product_layer_sentinel_passes_traversal_guard` (asserts `handover_path("_product", "..", "constitution")` raises `PathTraversalError`).
  - `specs/_product/architecture.md` — MODIFY: append new §3.8 "Product-layer handover path convention" section documenting the `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml` path, the sentinel `epic_slug="_product"` invocation pattern, the underscore-prefix distinction, and the unchanged FLOW-02 governance.
  - `specs/plans/deviate-content.md` — MODIFY: extend narrative-anchor field map at lines 52-67 with 4 Product-layer rows (constitution → `principle`, `enforcement_scope`, `exception_boundary`; flows → `user_role`, `trigger`, `success_signal`; architecture → `component`, `integration_contract`, `classification`; release → `release_goal`, `included_flows`, `deferred_work`).
- **Upstream Evidence**:
  - `specs/explore/product-layer-yaml.md` — Source explore scan (Status: SUCCESS, Complexity: Medium, Files Likely Modified: 8 categories, 8-12 source/spec files)
  - `specs/explore/product-layer-yaml.md:1-9` — Problem definition (extend FLOW-11 to Product-layer skills so FLOW-12 can aggregate across all phases/layers)
  - `specs/explore/product-layer-yaml.md:135-141` — Reference example (`deviate-red/SKILL.md` append shape)
  - `specs/explore/product-layer-yaml.md:144-150` — Canonical 15-skill coverage gate
  - `specs/explore/product-layer-yaml.md:158-164` — Idempotency assertion (`test_skill_instruction_is_idempotent`)
  - `specs/_product/flows/flows-content-capture.md:31,51` — FLOW-11 path-convention governance (`.deviate/content/handovers/<epic_slug>/<issue_id>/[<task_id>/]<phase>.yaml`)
  - `specs/_product/architecture.md:213` — FLOW-02 governance of `.deviate/content/handovers/` root
  - `specs/_product/release-next.md:51` — Existing AC for the 15-skill append (extended to 19 by this issue)
  - `specs/plans/deviate-content.md:79-87` — 15-skill modification list (extension point)
  - `specs/plans/deviate-content.md:52-67` — Narrative-anchor field map (extension point, 12 rows for Macro/Meso/Micro)
  - `src/deviate/core/handover.py:41` — `_HANDOVER_ROOT = Path(".deviate") / "content" / "handovers"`
  - `src/deviate/core/handover.py:45-55` — `_validate_segment()` helper (accepts underscore-prefixed sentinels)
  - `src/deviate/core/handover.py:59-89` — `handover_path()` body enforcing the path convention
  - `src/deviate/core/handover.py:24-39` — `HandoverRecord` Pydantic model with `extra="allow"` (forward-compatible with new anchor fields)
  - `tests/test_handover/test_skill_prompts.py:28-50` — `PHASE_SKILLS` canonical list (extension point)
  - `tests/test_handover/test_skill_prompts.py:161-171` — `test_skill_instruction_is_idempotent` parameterized assertion
  - `src/deviate/prompts/skills/deviate-red/SKILL.md` — Reference shape for the FLOW-11 append
  - `src/deviate/prompts/skills/deviate-research/SKILL.md:385` — Macro-skill reference shape
  - `src/deviate/prompts/skills/deviate-prd/SKILL.md:121` — PRD-skill reference shape
  - `src/deviate/prompts/skills/deviate-plan/SKILL.md:133` — Plan-skill reference shape
  - `specs/constitution.md:14-18` — Tamper Guard Content Capture exception (already covers `.deviate/content/handovers/**/*.yaml` — implicitly covers Product-layer paths)
  - `specs/_product/flows/flows-product.md:1-94` — FLOW-01/02/03 definitions (anchor field design context)
  - `specs/_product/flows/flows-content-capture.md:55-56` — Anchor non-fatal fallback contract
  - `specs/adhoc/prd.md` §`FR-ADHOC-013` — Appended functional requirement with AC-ADHOC-013-01 through AC-ADHOC-013-10
  - `specs/adhoc/012-deviate-content/plan.md:79-87` — Prior 15-skill append contract (extension baseline)

## The Problem Contract
The Content Capture subsystem (FLOW-11 / FLOW-12) captures every DeviaTDD phase as a durable YAML handover so `deviate content` (FLOW-12) can aggregate phase output into marketing-content drafts in five formats (blog, X-thread, release-notes, commit-story, resume-bullet). Per FR-ADHOC-012 (`specs/adhoc/prd.md`), the canonical 15-skill emission contract at `tests/test_handover/test_skill_prompts.py::PHASE_SKILLS` covers every Macro, Meso, and Micro layer skill — but leaves the four Product-layer skills (`deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release`) un-instrumented. This means `deviate content --format blog --slug my-post` (and the other four formats) currently cannot aggregate Product-layer phase output, even though Product-layer work — `/deviate-flows` writing `specs/_product/flows/flows-<domain>.md`, `/deviate-architecture` writing `specs/_product/architecture.md` and `specs/_product/domain-model.md`, `/deviate-release` writing `specs/_product/release-next.md`, `/deviate-constitution` writing `specs/constitution.md` — produces the highest-leverage narrative material for content drafts: release-goal descriptions, architectural decisions, flow definitions, governance exceptions. The single coherent vertical slice is: (a) append the canonical one-sentence `handover_path()` Write instruction to the four Product-layer SKILL.md files (mechanical, mirrors the `deviate-red/SKILL.md` reference shape verbatim), (b) extend the `PHASE_SKILLS` canonical list from 15 to 19 entries so the existing parameterized idempotency assertion automatically covers the four new skills, (c) define and document the Product-layer path convention `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml` in `specs/_product/architecture.md` §3.8 (concrete proposal: sentinel `epic_slug="_product"` invocation pattern, no `handover_path()` signature change), (d) extend the narrative-anchor field map with 4 Product-layer rows so FLOW-12 synthesis can pull phase-specific anchors (`principle`, `user_role`, `component`, `release_goal`, etc.) when present, and (e) add 2 path-convention unit tests to `tests/test_handover/test_path_resolution.py` validating the sentinel pattern. The Constitution §1 Tamper Guard exception at `specs/constitution.md:14-18` already covers `.deviate/content/handovers/**/*.yaml` globally, so no constitutional amendment is required and the Three-Layer Architecture definition (Macro / Meso / Micro) remains unchanged.

## Scope Boundaries
### Hard Inclusions
- Append a one-sentence FLOW-11 Write instruction to each of the four Product-layer SKILL.md files, matching the canonical reference shape at `src/deviate/prompts/skills/deviate-red/SKILL.md` exactly:
  ````
  ## Handover Persistence (FLOW-11)

  After emitting the YAML manifest, call the Write tool to persist it at `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml` via `deviate.core.handover.handover_path()` (FLOW-11 capture).
  ````
  Where `<skill-name> ∈ {constitution, flows, architecture, release}`. Implementation calls `handover_path("_product", "<skill-name>", "<skill-name>")` via the sentinel `epic_slug` argument. Source: `specs/explore/product-layer-yaml.md:135-141` + `tests/test_handover/test_skill_prompts.py:161-171`.
- Extend the canonical `PHASE_SKILLS` list at `tests/test_handover/test_skill_prompts.py:28-50` from 15 to 19 entries by appending a `# Product layer (4 skills)` comment block with `deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release`. The existing `test_skill_instruction_is_idempotent` parameterized assertion at lines 161-171 automatically covers the four new entries (it iterates over `PHASE_SKILLS` via `@pytest.mark.parametrize`). Source: `specs/explore/product-layer-yaml.md:144-150`.
- Append 2 new unit tests to `tests/test_handover/test_path_resolution.py`:
  - `test_product_layer_path_shape` — asserts `handover_path("_product", "constitution", "constitution")` returns `.deviate/content/handovers/_product/constitution/constitution.yaml` (and analogous for the other 3 Product-layer skills). The `_validate_segment()` helper at `src/deviate/core/handover.py:45-55` accepts the underscore-prefixed sentinel because it is non-empty, stripped, and contains no whitespace.
  - `test_product_layer_sentinel_passes_traversal_guard` — asserts `handover_path("_product", "..", "constitution")` raises `PathTraversalError` (or equivalent diagnostic). This confirms the sentinel does not weaken the existing traversal guard at lines 85-92.
- Add a new §3.8 "Product-layer handover path convention" section to `specs/_product/architecture.md` documenting:
  - Macro handover (Product layer): `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml`
  - Implementation uses `handover_path("_product", "<skill-name>", "<skill-name>")` with the underscore-prefixed sentinel `epic_slug` to signal Product-layer origin
  - Underscore prefix distinguishes the Product-layer root from real epic slugs; the sentinel `_product` matches the directory name `specs/_product/` for one-to-one traceability
  - Path traversal guard at `_validate_segment()` and `resolved_target.relative_to(resolved_root)` (lines 45-55, 85-92) applies unchanged; the sentinel `_product` passes the existing validation surface
  - `.deviate/content/handovers/` remains the single top-level root (FLOW-02 governance at `specs/_product/architecture.md:213` unchanged); no amendment to the architecture root is needed — only the addition of the §3.8 documentation row
- Extend the narrative-anchor field map at `specs/plans/deviate-content.md:52-67` with 4 Product-layer rows:
  - `deviate-constitution` → `principle`, `enforcement_scope`, `exception_boundary`
  - `deviate-flows` → `user_role`, `trigger`, `success_signal`
  - `deviate-architecture` → `component`, `integration_contract`, `classification` (Local/Context-Bridging/Context-Creating per FLOW-02 Metrics at `specs/_product/flows/flows-product.md:63`)
  - `deviate-release` → `release_goal`, `included_flows`, `deferred_work`
  These fields are optional; absence on any YAML is non-fatal per the existing fallback at `specs/_product/flows/flows-content-capture.md:55-56`.
- Verify end-to-end: after a simulated four-skill invocation sequence (`/deviate-constitution` → `/deviate-flows` → `/deviate-architecture` → `/deviate-release`) against a temp git repo, `.deviate/content/handovers/_product/{constitution,flows,architecture,release}.yaml` all exist, parse as valid YAML, and are NOT staged in the git index (verified via `git ls-files --error-unmatch`).

### Defensive Exclusions
- Do NOT modify `src/deviate/core/handover.py` signature or body. The `handover_path()` function is reused unchanged via sentinel `epic_slug="_product"` arguments. Any signature extension (e.g., adding `product_layer: bool = False` flag, or accepting `None` epic_slug) is deferred to a follow-up issue if research demands it.
- Do NOT modify `_HANDOVER_ROOT` (`src/deviate/core/handover.py:41`). The existing `.deviate/content/handovers/` root covers the new Product-layer subdirectory by virtue of path depth; no `_HANDOVER_ROOT` change is needed.
- Do NOT introduce a new top-level directory under `.deviate/` (e.g., `.deviate/product-handover/`). Per `specs/_product/architecture.md:213`, "FLOW-02 (Architecture) governs the path conventions (`.deviate/content/handovers/` and `.deviate/content/drafts/`) inherited by FLOW-11 and FLOW-12 ... This subgraph cannot introduce new top-level directory roots without amending this architecture document." The new Product-layer paths nest under the existing `.deviate/content/handovers/` root, so no amendment to the architecture root is needed — only the addition of the §3.8 documentation row.
- Do NOT amend `specs/constitution.md`. The existing Tamper Guard Content Capture exception at `specs/constitution.md:14-18` covers `.deviate/content/handovers/**/*.yaml` globally; Product-layer YAMLs are gitignored runtime state under the same path root. The Constitution's "Three-Layer Architecture" definition (line 9) remains Macro / Meso / Micro — the Product layer remains implicit per the existing release policy at `specs/_product/release-next.md` ("Minimal cli implementation. Keep it agent-centric"). The Version line remains at `0.3.0`.
- Do NOT regenerate `specs/_product/flows/flows-product.md`, `specs/_product/architecture.md` (architecture body), `specs/_product/release-next.md`, or `specs/_product/domain-model.md`. Only the §3.8 documentation row is appended to `architecture.md`; the other Product-layer artifacts remain untouched.
- Do NOT modify the existing 15-skill SKILL.md appends shipped per FR-ADHOC-012. They are already in production; this issue extends only the four Product-layer skills.
- Do NOT introduce LLM-driven content refinement for Product-layer handovers. v1 uses the same `narrative_anchor:` block shape as the 15 existing skills (optional, non-fatal absence, fallback to `phase` + `status` + `files` + git-log metadata per `specs/_product/flows/flows-content-capture.md:55-56`).
- Do NOT add new tests that exercise `deviate content` synthesis against Product-layer YAMLs in this issue. The `tests/test_content/` suite already covers synthesis shape (5 format templates, anchor referencing, window filter, archive); the new Product-layer paths are caught by the existing fixture loader via the `window=None` chronological branch. End-to-end synthesis validation is deferred to the next Content Capture release iteration.
- Do NOT bundle the architecture/constitution amendment or `_HANDOVER_ROOT` extension into this issue. Per the explore exclusions at `specs/explore/product-layer-yaml.md:13-14`, "Architectural decisions, design trade-offs, risk analysis, naming of any new product-layer anchor fields, decisions about whether to amend `handover_path()` to accept a `None` epic/issue, whether to introduce a new `_product/` subdirectory under `.deviate/content/handovers/`, narrative_anchor field design for product-layer phases, synthesis-layer changes for product-layer outputs, and failure-mode speculation — all deferred to the `deviate-research` skill." This ad-hoc issue ships the minimal vertical slice (one path convention via sentinel, one documentation row, four SKILL.md appends, one test-list extension, 2 path-convention tests) without attempting to canonicalize the architectural decisions reserved for research.

## Upstream Requirement Tracing
- **Requirements Tokens**: `FR-ADHOC-013`
- **Acceptance Criteria Tokens**: `AC-ADHOC-013-01` through `AC-ADHOC-013-10`
- **Data Model Entities**: None new — `HandoverRecord` Pydantic model at `src/deviate/core/handover.py:24-39` already supports `extra="allow"` and `narrative_anchor: dict[str, Any] | None`; Product-layer anchor fields slot in without schema changes. `IssueRecord.flow_refs` field at `src/deviate/state/ledger.py:35` already exists (added per FR-ADHOC-010).
- **Spec Source Anchors**:
  - `specs/explore/product-layer-yaml.md:1-9` — Problem definition (extend FLOW-11 pattern to Product-layer skills)
  - `specs/explore/product-layer-yaml.md:135-141` — Reference example (`deviate-red/SKILL.md` append shape)
  - `specs/explore/product-layer-yaml.md:144-150` — Canonical 15-skill coverage gate
  - `specs/explore/product-layer-yaml.md:158-164` — Idempotency assertion
  - `specs/explore/product-layer-yaml.md:13-14` — Deferral of architectural decisions to `deviate-research`
  - `specs/_product/flows/flows-content-capture.md:31,51` — FLOW-11 path-convention governance
  - `specs/_product/flows/flows-content-capture.md:55-56` — Anchor non-fatal fallback contract
  - `specs/_product/architecture.md:213` — FLOW-02 governance of `.deviate/content/handovers/` root
  - `specs/_product/release-next.md:51` — Existing AC for the 15-skill append (extended to 19 by this issue)
  - `specs/_product/flows/flows-product.md:63` — FLOW-02 classification metric (Local/Context-Bridging/Context-Creating)
  - `specs/plans/deviate-content.md:79-87` — 15-skill modification list (extension point)
  - `specs/plans/deviate-content.md:52-67` — Narrative-anchor field map (extension point)
  - `src/deviate/core/handover.py:41` — `_HANDOVER_ROOT = Path(".deviate") / "content" / "handovers"`
  - `src/deviate/core/handover.py:45-55` — `_validate_segment()` helper
  - `src/deviate/core/handover.py:59-89` — `handover_path()` body
  - `src/deviate/core/handover.py:85-92` — `resolved_target.relative_to(resolved_root)` traversal guard
  - `src/deviate/core/handover.py:24-39` — `HandoverRecord` Pydantic model with `extra="allow"`
  - `tests/test_handover/test_skill_prompts.py:28-50` — `PHASE_SKILLS` canonical list
  - `tests/test_handover/test_skill_prompts.py:161-171` — `test_skill_instruction_is_idempotent`
  - `src/deviate/prompts/skills/deviate-red/SKILL.md` — Reference shape for the FLOW-11 append
  - `specs/constitution.md:14-18` — Tamper Guard Content Capture exception (covers Product-layer paths)
  - `specs/constitution.md:9` — Three-Layer Architecture definition (unchanged)

## User Stories Ledger
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

- **US-013-01**: As a developer who runs `/deviate-flows` to author a new product flow under `specs/_product/flows/flows-<domain>.md`, I want the skill actor to emit a durable YAML handover at `.deviate/content/handovers/_product/flows/flows.yaml` via `handover_path("_product", "flows", "flows")` so the FLOW-12 synthesis (`deviate content --format blog`) can pull a `user_role` / `trigger` / `success_signal` anchor from my flow authoring and surface it as content draft material. *(Ref: FR-ADHOC-013, FLOW-11, FLOW-12, FLOW-01)*
- **US-013-02**: As a developer who runs `/deviate-architecture` to update `specs/_product/architecture.md`, I want the skill actor to emit a YAML handover at `.deviate/content/handovers/_product/architecture/architecture.yaml` so FLOW-12 can pull a `component` / `integration_contract` / `classification` anchor when drafting release-notes or commit-story content from my architecture work. *(Ref: FR-ADHOC-013, FLOW-11, FLOW-12, FLOW-02)*
- **US-013-03**: As a developer who runs `/deviate-release` to update `specs/_product/release-next.md`, I want the skill actor to emit a YAML handover at `.deviate/content/handovers/_product/release/release.yaml` so FLOW-12 can pull a `release_goal` / `included_flows` / `deferred_work` anchor — the single most valuable synthesis input across the entire Content Capture subsystem. *(Ref: FR-ADHOC-013, FLOW-11, FLOW-12, FLOW-03)*
- **US-013-04**: As a developer who runs `/deviate-constitution` to update `specs/constitution.md`, I want the skill actor to emit a YAML handover at `.deviate/content/handovers/_product/constitution/constitution.yaml` so FLOW-12 can pull a `principle` / `enforcement_scope` / `exception_boundary` anchor when drafting blog posts about governance changes. *(Ref: FR-ADHOC-013, FLOW-11, FLOW-12)*
- **US-013-05**: As a DeviaTDD maintainer running `mise run test tests/test_handover/ -v`, I want the canonical 15-skill assertion to extend to 19 entries so any future regression that removes the FLOW-11 Write instruction from a Product-layer skill is caught by `test_skill_instruction_is_idempotent` exactly the same way a regression on a Macro/Meso/Micro skill is caught today. *(Ref: FR-ADHOC-013, FLOW-11)*
- **US-013-06**: As a developer invoking `deviate content --format blog --window _product`, I want the synthesis loader to return the four Product-layer records (`constitution.yaml`, `flows.yaml`, `architecture.yaml`, `release.yaml`) alongside any Macro/Meso/Micro records so the resulting blog draft references the full vertical (constitution → flows → architecture → release → epics). *(Ref: FR-ADHOC-013, FLOW-12)*
- **US-013-07**: As a security-conscious developer, I want `handover_path("_product", "..", "constitution")` to raise `PathTraversalError` so the Product-layer paths cannot escape `.deviate/content/handovers/` even via the sentinel epic_slug. *(Ref: FR-ADHOC-013, FLOW-11)*
- **US-013-08**: As a developer re-running the four Product-layer skills in sequence (e.g., `/deviate-constitution` → `/deviate-flows` → `/deviate-architecture` → `/deviate-release` to bootstrap a new product layer), I want each handover to land at its canonical Product-layer path and re-emission to be a no-op (idempotent overwrite-or-skip per `specs/plans/deviate-content.md:116`) so accidental re-runs do not duplicate or corrupt the YAMLs. *(Ref: FR-ADHOC-013, FLOW-11)*

## ATDD Acceptance Criteria
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

**Scenario 013-01**: `deviate-constitution` SKILL.md carries the FLOW-11 Write instruction (idempotent)
**Given** the canonical reference shape at `src/deviate/prompts/skills/deviate-red/SKILL.md` and the idempotency assertion at `tests/test_handover/test_skill_prompts.py:161-171`
**When** `src/deviate/prompts/skills/deviate-constitution/SKILL.md` is read post-implementation
**Then** it contains the literal string `handover_path()` exactly once (marker_count == 1 per `test_skill_instruction_is_idempotent`); the surrounding section is titled `## Handover Persistence (FLOW-11)`; the canonical target referenced in the instruction is `.deviate/content/handovers/_product/constitution/constitution.yaml` — verifying AC-ADHOC-013-01.

**Scenario 013-02**: `deviate-flows`, `deviate-architecture`, `deviate-release` SKILL.md files carry the Write instruction (idempotent)
**Given** the same reference shape and idempotency assertion
**When** the other three Product-layer SKILL.md files are read
**Then** each contains `handover_path()` exactly once, with the canonical target `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml` for `<skill-name> ∈ {flows, architecture, release}`; the parameterized `@pytest.mark.parametrize` loop at `tests/test_handover/test_skill_prompts.py:161-171` automatically iterates over the extended `PHASE_SKILLS` list and asserts the marker count — verifying AC-ADHOC-013-02.

**Scenario 013-03**: `PHASE_SKILLS` canonical list extends from 15 to 19 entries
**Given** the existing list at `tests/test_handover/test_skill_prompts.py:28-50` (15 entries)
**When** the list is read post-implementation
**Then** it contains exactly 19 entries: the original 15 plus `deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release` appended in a `# Product layer (4 skills)` comment block; the existing `@pytest.mark.parametrize` loop at line 161-171 automatically iterates over the extended list — verifying AC-ADHOC-013-03.

**Scenario 013-04**: `handover_path()` accepts the sentinel `epic_slug="_product"` and returns the canonical Product-layer path
**Given** the sentinel approach (no `handover_path()` signature change)
**When** `handover_path("_product", "constitution", "constitution")`, `handover_path("_product", "flows", "flows")`, `handover_path("_product", "architecture", "architecture")`, and `handover_path("_product", "release", "release")` are called
**Then** the four results equal `.deviate/content/handovers/_product/constitution/constitution.yaml`, `.deviate/content/handovers/_product/flows/flows.yaml`, `.deviate/content/handovers/_product/architecture/architecture.yaml`, and `.deviate/content/handovers/_product/release/release.yaml` respectively; the path-traversal guard at `_validate_segment()` (`src/deviate/core/handover.py:45-55`) accepts the underscore-prefixed sentinel because it is non-empty, stripped, and contains no whitespace — verifying AC-ADHOC-013-04.

**Scenario 013-05**: Path traversal guard rejects escaped sentinel invocation
**Given** the new unit test `test_product_layer_sentinel_passes_traversal_guard` appended to `tests/test_handover/test_path_resolution.py`
**When** `handover_path("_product", "..", "constitution")` is called with `issue_id=".."`
**Then** `PathTraversalError` (or equivalent diagnostic) is raised before any filesystem write; the underscore-prefix sentinel does not weaken the existing traversal guard at `src/deviate/core/handover.py:85-92` (`resolved_target.relative_to(resolved_root)`) — verifying AC-ADHOC-013-05.

**Scenario 013-06**: `specs/_product/architecture.md` §3.8 documents the Product-layer path convention
**Given** the new §3.8 section to be appended post-implementation
**When** `grep -A 20 "Product-layer handover path convention" specs/_product/architecture.md` runs
**Then** the section explicitly declares: (a) Macro handover (Product layer) path is `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml`; (b) the implementation invokes `handover_path("_product", "<skill-name>", "<skill-name>")` via the sentinel `epic_slug`; (c) the underscore-prefix on `_product` distinguishes Product-layer origin from real epic slugs; (d) `.deviate/content/handovers/` remains the single top-level root (FLOW-02 governance at `specs/_product/architecture.md:213` unchanged); (e) path-traversal guard applies unchanged — verifying AC-ADHOC-013-06.

**Scenario 013-07**: Narrative-anchor field map extends with 4 Product-layer rows
**Given** the existing map at `specs/plans/deviate-content.md:52-67` (12 rows for Macro/Meso/Micro phases)
**When** the table is read post-implementation
**Then** it contains 4 additional rows for `deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release` with the proposed anchor fields: constitution → `principle`, `enforcement_scope`, `exception_boundary`; flows → `user_role`, `trigger`, `success_signal`; architecture → `component`, `integration_contract`, `classification`; release → `release_goal`, `included_flows`, `deferred_work` — verifying AC-ADHOC-013-07.

**Scenario 013-08**: Constitution §1 Tamper Guard exception covers Product-layer paths (no amendment required)
**Given** the existing exception at `specs/constitution.md:14-18` covering `.deviate/content/handovers/**/*.yaml`
**When** `head -20 specs/constitution.md | grep -A 5 "Exception"` is read post-implementation
**Then** the exception text remains unchanged; `Version: 0.3.0` line is preserved; `.deviate/content/handovers/_product/**` is implicitly covered by the `**/*.yaml` glob; Three-Layer Architecture definition at line 9 remains Macro / Meso / Micro; no constitutional amendment is required — verifying AC-ADHOC-013-08.

**Scenario 013-09**: End-to-end Product-layer bootstrap emits 4 handovers not staged in git
**Given** a temp git repo with `deviate setup` complete and `.deviate/.gitignore` containing `.deviate/content/`
**When** a simulated sequence of `/deviate-constitution`, `/deviate-flows`, `/deviate-architecture`, `/deviate-release` runs against fixture product-layer content
**Then** `.deviate/content/handovers/_product/{constitution,flows,architecture,release}.yaml` all exist, parse as valid YAML, are present on disk, and `git ls-files --error-unmatch` returns non-zero for each (not staged in git index); the existing `.deviate/content/` gitignore entry covers the new `_product/` subdirectory without modification — verifying AC-ADHOC-013-09.

**Scenario 013-10**: Test suite remains < 18s and lint passes
**Given** the new tests are appended to existing test files (no new test files created) and the SKILL.md appends are Markdown
**When** `mise run test` and `mise run lint` complete post-implementation
**Then** the full suite finishes in < 18s (per AGENTS.md performance mandate); ruff reports zero violations on the modified Python files (`tests/test_handover/test_skill_prompts.py` and `tests/test_handover/test_path_resolution.py`); the four SKILL.md appends and the `architecture.md` / `deviate-content.md` Markdown modifications are not ruff-scanned — verifying AC-ADHOC-013-10.

## Edge Cases and Boundaries
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

- **Sentinel `_product` rejected by `_validate_segment()`**: If the existing validation at `src/deviate/core/handover.py:45-55` rejects underscore-prefixed segments (unlikely given the current surface treats `epic_slug` as an opaque path component), the implementation falls back to a different sentinel (e.g., `epic_slug="product"` without the underscore — slightly less distinct from real epic slugs but functionally equivalent). The path verification at Scenario 013-04 catches this case at test time, and the developer picks the first viable sentinel.
- **Product-layer skill invoked outside a DeviaTDD workspace**: The skill actor still emits the YAML; the runtime guard at `handover_path()` raises `PathTraversalError` if `.deviate/content/handovers/` does not exist and parent-directory creation fails. Same failure mode as the existing 15 skills — no new error surface.
- **Re-running the implementation against an already-instrumented Product-layer skill**: The append operation must be idempotent. If a Write instruction is already present in a skill, the implementation must detect it and skip rather than appending a duplicate. The `test_skill_instruction_is_idempotent` assertion (`marker_count == 1`) catches accidental duplication at test time.
- **Conflict between underscore-prefix sentinel and a real epic slug `_product`**: If a user names an actual epic `_product`, the path collision would cause handovers to overwrite. The implementation documents this edge case in the architecture §3.8 section (epic slugs starting with `_` are reserved for framework use) and emits a warning if `deviate explore` is invoked with `epic_slug="_product"`. This is a documentation-only guard — runtime validation is out of scope for this issue.
- **Narrative anchor fields absent on Product-layer YAMLs**: Per the existing fallback at `specs/_product/flows/flows-content-capture.md:55-56`, absence of `narrative_anchor:` is non-fatal and synthesis falls back to `phase` + `status` + `files` + git-log metadata. The proposed anchor fields (`principle`, `user_role`, `component`, `release_goal`, etc.) are optional, not required.
- **Flow Refs parsing for Product-layer flows**: The `_FLOW_REF_PATTERN` at `src/deviate/cli/adhoc.py:13` is `^FLOW-\d{2,}$`. The four Product-layer flows (FLOW-01, FLOW-02, FLOW-03) match this pattern. The 4 Product-layer skills themselves are NOT flows — they implement flows. An issue emitted from `/deviate-constitution` carries `flow_refs: []` because constitution is governance, not a user-visible flow. This is consistent with the existing convention at `ISS-ADH-010` where `flow_refs` is empty for zero-flow enabling slices per the Vertical Slice Mandate.
- **`deviate content --window _product` filter**: The synthesis loader at `src/deviate/core/synthesis.py::load_handover_records(window)` accepts a string window filter. The `--window _product` flag must pass the sentinel verbatim to the loader; the loader must accept the underscore-prefixed filter and match the `.deviate/content/handovers/_product/**` path glob. This is a minor extension to the existing window-filter logic — verified by Scenario 013-06 in the demonstration path (synthesis test).
- **`flow_refs` field on Product-layer handover YAMLs**: Product-layer handovers MAY include `flow_refs: [FLOW-01, FLOW-02, FLOW-03]` in their YAML manifest (the skill actor can populate it from the Product-layer flow being modified). The `HandoverRecord` Pydantic model already supports `extra="allow"` so the field slots in without schema change.
- **Concurrent Product-layer skill invocations**: If a developer runs `/deviate-flows` and `/deviate-architecture` concurrently, the two writes target distinct paths (`.deviate/content/handovers/_product/flows/flows.yaml` vs `.deviate/content/handovers/_product/architecture/architecture.yaml`) and do not collide. v1 does not implement file locking; the existing race-condition behavior applies unchanged.
- **`.deviate/.gitignore` covers Product-layer paths**: The existing `.deviate/content/` entry covers all paths under `.deviate/content/handovers/`, including the new `.deviate/content/handovers/_product/` subdirectory. No `.gitignore` change is required.
- **Missing `.deviate/content/handovers/` directory at first invocation**: `persist_handover()` creates parent directories via `pathlib.Path.parent.mkdir(parents=True, exist_ok=True)` per the existing behavior at FR-ADHOC-012 Edge Cases and Boundaries. The first `/deviate-constitution` invocation materializes the full path tree including `.deviate/content/handovers/_product/constitution/`.
- **Cross-platform path separators**: `pathlib.Path` is used throughout. The `pathlib.PurePosixPath` invariant must hold when comparing canonical paths in tests.

## Performance Constraints
<!-- Canonical format reference: src/deviate/prompts/skills/deviate-shard/SKILL.md -->

- **L_max (single `handover_path()` call with sentinel epic_slug)**: ≤ 1ms (pure `pathlib` string manipulation, no I/O)
- **L_max (single `persist_handover()` call to `.deviate/content/handovers/_product/...`)**: ≤ 10ms (filesystem write + parent directory creation in worst case)
- **L_max (`load_handover_records(window="_product")` against a fixture tree)**: ≤ 100ms (sequential `yaml.safe_load` + glob)
- **L_max (single `deviate content --format blog --window _product` synthesis)**: ≤ 200ms (load records + template render + markdown write)
- **Throughput**: Full test suite (`mise run test`) remains < 18s per AGENTS.md mandate. New assertions: 1 parameterized assertion in existing `tests/test_handover/test_skill_prompts.py` (auto-covers the 4 new skills via `@pytest.mark.parametrize`, adds ~5ms total) + 2 path-convention tests in `tests/test_handover/test_path_resolution.py` (~50ms each). Total: ≤ 5 new assertions, all expected < 100ms each.
- **Lint budget**: `mise run lint` (ruff check) reports zero violations on the modified Python files (`tests/test_handover/test_skill_prompts.py` and `tests/test_handover/test_path_resolution.py`). The SKILL.md appends are Markdown and not ruff-scanned. The `architecture.md` and `deviate-content.md` modifications are Markdown.
- **Format-check budget**: `mise run format-check` reports zero violations on the modified Python files.
- **File size**: Each Product-layer SKILL.md append is one section (3 lines + blank) — ~30 bytes added per file. Total addition across 4 files: ~120 bytes. `architecture.md` §3.8 addition: ≤ 30 lines. `deviate-content.md` table extension: 4 rows, ≤ 10 lines.
- **Idempotency cost**: Re-running `persist_handover()` on an existing Product-layer YAML completes in ≤ 5ms (file existence check + early return, no YAML re-parse). The append operation on the four SKILL.md files is idempotent: re-running the implementation against an already-instrumented skill detects the existing `handover_path()` marker and skips.
- **`discover_skills()` enumeration of 23 skills (4 Product-layer pre-existing per FR-ADHOC-010)**: unchanged, ≤ 5ms (no new skill directories added in this issue).

## Multi-Tiered Verification Targets
- **Unit Sandbox Targets**:
  - `tests/test_handover/test_skill_prompts.py::test_skill_instruction_is_idempotent[deviate-constitution]` — auto-asserted by extending `PHASE_SKILLS` from 15 to 19 entries; `@pytest.mark.parametrize` loop catches missing or duplicated `handover_path()` marker.
  - `tests/test_handover/test_skill_prompts.py::test_skill_instruction_is_idempotent[deviate-flows]` — same parameterized assertion
  - `tests/test_handover/test_skill_prompts.py::test_skill_instruction_is_idempotent[deviate-architecture]` — same parameterized assertion
  - `tests/test_handover/test_skill_prompts.py::test_skill_instruction_is_idempotent[deviate-release]` — same parameterized assertion
  - `tests/test_handover/test_skill_prompts.py::test_skill_instruction_in_terminal_section[deviate-constitution]` (and analogous for the other 3 skills) — auto-asserted via the existing parameterized loop (verifies the marker is in the `## Handover Persistence (FLOW-11)` section, not arbitrarily placed)
  - `tests/test_handover/test_path_resolution.py::test_product_layer_path_shape` — NEW: asserts `handover_path("_product", "constitution", "constitution")` returns `.deviate/content/handovers/_product/constitution/constitution.yaml` (and analogous for the other 3 Product-layer skills)
  - `tests/test_handover/test_path_resolution.py::test_product_layer_sentinel_passes_traversal_guard` — NEW: asserts `handover_path("_product", "..", "constitution")` raises `PathTraversalError` (sentinel must not weaken the traversal guard)
- **Integration Sandbox Targets**:
  - End-to-end Product-layer bootstrap (manual or scripted): four skill invocations produce 4 handovers at `.deviate/content/handovers/_product/{constitution,flows,architecture,release}.yaml`, all parse as valid YAML, none staged in git
  - Constitution untouched: `head -5 specs/constitution.md` still reads `Version: 0.3.0` (no version bump)
  - Architecture.md §3.8 row present: `grep -A 5 "Product-layer handover path convention" specs/_product/architecture.md` returns the new section
  - Narrative-anchor field map extension: `grep -E "^\| (deviate-constitution|deviate-flows|deviate-architecture|deviate-release)" specs/plans/deviate-content.md` returns 4+ matches in the anchor table

## Demonstration Path
```bash
# 1. Verify the 4 Product-layer SKILL.md files carry the FLOW-11 marker (idempotency: exactly once each)
for skill in deviate-constitution deviate-flows deviate-architecture deviate-release; do
  count=$(grep -c "handover_path()" "src/deviate/prompts/skills/$skill/SKILL.md")
  if [ "$count" -eq 1 ]; then
    echo "[OK] $skill carries handover_path() marker exactly once"
  else
    echo "[FAIL] $skill has $count occurrences of handover_path() (expected 1)"
    exit 1
  fi
done

# 2. Verify the canonical PHASE_SKILLS list extends to 19 entries
uv run python -c "
import re, pathlib
text = pathlib.Path('tests/test_handover/test_skill_prompts.py').read_text()
matches = re.findall(r'^\s*\"(deviate-[a-z]+)\"', text, flags=re.MULTILINE)
print(f'[OK] PHASE_SKILLS list contains {len(matches)} entries')
assert len(matches) == 19, f'expected 19 entries, got {len(matches)}'
expected_new = {'deviate-constitution', 'deviate-flows', 'deviate-architecture', 'deviate-release'}
assert expected_new.issubset(set(matches)), f'missing Product-layer skills: {expected_new - set(matches)}'
print('[OK] all 4 Product-layer skills present in PHASE_SKILLS')
"

# 3. Verify the sentinel path convention via Python REPL
uv run python -c "
from src.deviate.core.handover import handover_path
expected_paths = {
    ('_product', 'constitution', 'constitution'): '.deviate/content/handovers/_product/constitution/constitution.yaml',
    ('_product', 'flows', 'flows'): '.deviate/content/handovers/_product/flows/flows.yaml',
    ('_product', 'architecture', 'architecture'): '.deviate/content/handovers/_product/architecture/architecture.yaml',
    ('_product', 'release', 'release'): '.deviate/content/handovers/_product/release/release.yaml',
}
for (epic, issue, phase), expected in expected_paths.items():
    actual = str(handover_path(epic, issue, phase))
    assert actual == expected, f'{actual} != {expected}'
    print(f'[OK] {epic}/{issue}/{phase} -> {actual}')
"

# 4. Verify path traversal guard applies to sentinel epic_slug
uv run python -c "
from src.deviate.core.handover import handover_path
try:
    handover_path('_product', '..', 'constitution')
    print('[FAIL] path traversal was not rejected')
    exit(1)
except Exception as e:
    print(f'[OK] path traversal rejected: {type(e).__name__}: {e}')
"

# 5. Verify architecture.md §3.8 documents the new path convention
grep -A 10 "Product-layer handover path convention" specs/_product/architecture.md

# 6. Verify narrative-anchor field map extends with 4 Product-layer rows
grep -cE "^\| (deviate-constitution|deviate-flows|deviate-architecture|deviate-release)" specs/plans/deviate-content.md
# Expected: 4 rows

# 7. Verify Constitution §1 Tamper Guard exception covers Product-layer paths (no amendment needed)
head -20 specs/constitution.md | grep -A 5 "Exception (Content Capture"

# 8. Run the unit tests
mise run test tests/test_handover/test_skill_prompts.py -v
mise run test tests/test_handover/test_path_resolution.py::test_product_layer_path_shape -v
mise run test tests/test_handover/test_path_resolution.py::test_product_layer_sentinel_passes_traversal_guard -v

# 9. Run the full test suite + lint + format-check
mise run test
mise run lint
mise run format-check
mise run check

# 10. End-to-end smoke: simulate 4 Product-layer skill invocations
tmpdir=$(mktemp -d)
cd "$tmpdir"
git init -q && git config user.email "test@test" && git config user.name "Test"
mkdir -p .deviate/content/handovers
# Simulate the 4 Product-layer handovers via persist_handover with sentinel epic_slug
uv run --project /Users/werner/Projects/tools/deviatdd python -c "
from src.deviate.core.handover import persist_handover
for skill in ['constitution', 'flows', 'architecture', 'release']:
    manifest = f'phase: {skill}\nstatus: success\nfiles: []\nnarrative_anchor:\n  principle: example\n'
    persist_handover('_product', skill, skill, manifest)
"
ls .deviate/content/handovers/_product/
# Verify not staged in git
for f in .deviate/content/handovers/_product/*.yaml; do
  ! git ls-files --error-unmatch "$f" 2>/dev/null && \
    echo "[OK] $(basename $f) present and not staged in git"
done

# 11. Verify .deviate/.gitignore covers the Product-layer paths (no change needed)
grep -q "^.deviate/content/$" .deviate/.gitignore && echo "[OK] .deviate/content/ gitignore entry covers Product-layer paths"
```