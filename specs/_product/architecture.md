# DeviaTDD Product Architecture — Tome & Content Capture Subsystems

**Classification**: Context-Creating
  - Tome subsystem (2026-06-26): introduced 7 new components and 1 new output surface (`apps/docs/`)
  - Content Capture subsystem (2026-06-27): introduces 3 new components, 1 new Python module (`core/handover.py`), 1 new CLI sub-app (`cli/content.py`), and cross-cuts 15 existing skill prompts with a one-sentence Write instruction
**Last Updated**: 2026-06-27
**Source Flows**:
  - `specs/_product/flows/flows-tome.md` (FLOW-04..FLOW-10)
  - `specs/_product/flows/flows-content-capture.md` (FLOW-11..FLOW-12)

---

## 1. Scope

This document covers two Product-level subsystems, each spanning multiple epics:

1. **Tome** — a manual post-merge documentation curator for Starlight docs sites. It classifies a commit (or a branch-level diff) against the four Diátaxis quadrants, then runs only the writer skills the classifier selects. The verifier performs a wider cross-doc pass after writers complete. Covered by FLOW-04..FLOW-10.

2. **Content Capture** — a phase-handover + synthesis pipeline. Every DeviaTDD phase emits a YAML handover manifest at the end of its post-handler (`FLOW-11`); the `deviate content` CLI then aggregates handovers and renders a marketing-content draft in one of five formats (`FLOW-12`). Covered by FLOW-11 and FLOW-12.

Per-epic concerns belong in `specs/issues/`.

## 2. Out of Scope (Cross-Cutting)

- **Tome is prompt-only in v1**. Each Tome skill lives as a static `SKILL.md` text file under `src/deviate/prompts/skills/tome-*/`. No Python runtime is added in this iteration. DeviaTDD's own tech stack (Python 3.13 + Typer) is unchanged.
- **Tome output is decoupled from DeviaTDD's runtime stack**. Skill outputs (Starlight sites, `apps/docs/`, `content.config.ts`, `.astro` files) live in *target repos* that consume the skills, not in DeviaTDD's repo.
- **No shared contracts module**. Each skill inlines the schemas it needs. There is no `tome/contracts.py` or equivalent.
- **No JUDGE pattern**. The verifier (FLOW-09) emits a human-readable report. There is no `<judge_feedback>` auto-routing, no machine-parseable feedback, and no automated re-run of writers.
- **No `deviate tome <phase>` CLI surface in v1**. A future iteration may introduce a Typer sub-app under `src/deviate/cli/tome.py` for the phases that prove to need deterministic enforcement (likely C7 setup + path/frontmatter validation for C2-C5). v1 ships pure-prompt and gathers usage data first.

## 3. Components

| ID | Component | Skill | Flow | Responsibility | Self-verify | Writes to |
|---|---|---|---|---|---|---|
| C1 | Tome Classifier | `tome-classify` | FLOW-04 | Ingest commit/branch evidence; emit classification report | n/a (read-only) | nothing |
| C2 | Tome Writer — Tutorial | `tome-write-tutorial` | FLOW-05 | Produce one `tutorials/*.md` | yes | `apps/docs/src/content/docs/tutorials/` |
| C3 | Tome Writer — How-To | `tome-write-how-to` | FLOW-06 | Produce one `how-to/*.md` | yes | `apps/docs/src/content/docs/how-to/` |
| C4 | Tome Writer — Reference | `tome-write-reference` | FLOW-07 | Produce one `reference/*.md` | yes | `apps/docs/src/content/docs/reference/` |
| C5 | Tome Writer — Explanation | `tome-write-explanation` | FLOW-08 | Produce one `explanation/*.md` | yes | `apps/docs/src/content/docs/explanation/` |
| C6 | Tome Verifier | `tome-verify-docs` | FLOW-09 | Cross-doc pass: factual accuracy, path correctness, no cross-type contamination, valid Starlight location | n/a (read-only report) | nothing |
| C7 | Tome Setup | `tome-setup` | FLOW-10 | Idempotent bootstrap of `apps/docs/`, four quadrant dirs, `content.config.ts`, optional starter set | n/a | `apps/docs/` (in target repo) |
| C8 | Handover Capture (Runner) | (none — internal helper) | FLOW-11 | Per-phase YAML write at `.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml`; validates path, never touches git | yes | `.deviate/content/handovers/` |
| C9 | Content Synthesis | `deviate-content` | FLOW-12 | Aggregate handovers for a window; render draft in chosen format; optional archive tarball | n/a | `.deviate/content/drafts/`, `specs/_archives/` |
| C10 | Format Template Pack | (resource — 5 prompt templates) | FLOW-12 | Format-specific markdown templates consumed by C9 (blog, x-thread, release-notes, commit-story, resume-bullet) | n/a | `src/deviate/prompts/content/` |

### 3.1 C1 — Tome Classifier (FLOW-04)

- **Skill path**: `src/deviate/prompts/skills/tome-classify/SKILL.md`
- **Input modes**:
  - default (no args) → HEAD~1 (previous commit)
  - `/tome-classify <sha>` → specific commit
  - `/tome-classify --merge-base` → `git diff $(git merge-base HEAD main)..HEAD` of current branch
  - `/tome-classify --working-tree` → uncommitted/staged changes
- **Inputs (per mode)**: commit SHA or branch diff, commit message(s), changed files, changed tests, optional `specs/` artifacts (issues, tasks, flows), existing `apps/docs/src/content/docs/` tree.
- **Outputs**: A classification report containing:
  1. brief change summary
  2. capability table (capability, evidence, audience, doc_type, action, target_file, confidence)
  3. no-touch list
- **Action enum** (inlined in C1 prompt): `create`, `update`, `no-change`, `human-review`, `setup-required`.
- **Gate behavior**:
  - All changes internal-only → `no-change`; downstream writers and C6 are skipped.
  - Classifier uncertain → `human-review`; writers blocked until human confirms.
  - `apps/docs/` absent → `setup-required`; classifier halts and points at C7.
  - Target file collides with existing page in wrong quadrant → `human-review` with collision flagged.
  - Merge-base diff → branch-level classification covering all commits since divergence from main; capability table is scoped to the cumulative change set.
- **Flow ref**: FLOW-04.

### 3.2 C2-C5 — Tome Writers (FLOW-05..FLOW-08)

- **Skill paths**:
  - C2: `src/deviate/prompts/skills/tome-write-tutorial/SKILL.md`
  - C3: `src/deviate/prompts/skills/tome-write-how-to/SKILL.md`
  - C4: `src/deviate/prompts/skills/tome-write-reference/SKILL.md`
  - C5: `src/deviate/prompts/skills/tome-write-explanation/SKILL.md`
- **Strict quadrant rule**: Each writer is confined to its own Diátaxis quadrant directory. C2 → `tutorials/`, C3 → `how-to/`, C4 → `reference/`, C5 → `explanation/`. A writer that needs to touch a different quadrant must flag back to C1 for re-classification.
- **Per-writer self-verify** (built into each prompt, not a separate output):
  - target file path is in the writer's quadrant
  - frontmatter is valid Tome schema (`title`, `description`, `doc_type`, `status`, `last_verified_at`, `verified_sha`, `related_issues`)
  - content stays in the writer's doc_type register (e.g., C2 does not produce step-by-step instructions, C6 territory)
  - existing valid content is preserved where possible
- **Frontmatter schema** (inlined in each writer prompt):
  ```yaml
  ---
  title: ...
  description: ...
  doc_type: tutorial | how-to | reference | explanation
  status: draft | reviewed
  last_verified_at: YYYY-MM-DD
  verified_sha: abc1234
  related_issues:
    - ISS-123
  ---
  ```
- **Out-of-scope for writers**: `index.md`, `_meta/`, `content.config.ts`, `package.json`, `astro.config.mjs`. These are C7's territory or out of scope.
- **Flow refs**: FLOW-05, FLOW-06, FLOW-07, FLOW-08.

### 3.3 C6 — Tome Verifier (FLOW-09)

- **Skill path**: `src/deviate/prompts/skills/tome-verify-docs/SKILL.md`
- **Trigger**: Developer runs `/tome-verify-docs` after at least one writer (C2-C5) has produced an updated file.
- **Cross-doc checks** (system-level, not single-doc):
  - Factual consistency: each updated doc's claims match the commit diff, changed tests, and `specs/` artifacts.
  - Path correctness: each updated file lives in the quadrant its `doc_type` claims.
  - Command/config/API accuracy: examples in updated docs match current code.
  - No cross-type contamination: tutorial content inside a how-to, etc.
  - Valid Starlight location: file is under `apps/docs/src/content/docs/<quadrant>/`.
- **Output format**: Human-readable markdown report with:
  - PASS items
  - FAIL items
  - Boundary violations
  - Recommended files to commit
- **No auto-routing**: Verifier does not call back to writers. Human reads the report, manually re-runs the relevant writer with updated evidence if needed.
- **Flow ref**: FLOW-09.

### 3.4 C7 — Tome Setup (FLOW-10)

- **Skill path**: `src/deviate/prompts/skills/tome-setup/SKILL.md`
- **Trigger**: Developer runs `/tome-setup` once per repo; subsequent runs are idempotent.
- **Inputs**: confirmation that the repo accepts a Starlight app under `apps/docs/` (or developer confirms override).
- **Scaffold**:
  1. `apps/docs/` with Starlight
  2. Four quadrant dirs under `apps/docs/src/content/docs/` (tutorials, how-to, reference, explanation) + `index.md` + `_meta/`
  3. `src/content.config.ts` extending `docsSchema()` with Tome frontmatter fields (`doc_type`, `status`, `last_verified_at`, `verified_sha`, `related_issues`)
  4. Optional starter set (one architecture explanation, one config reference, one first-task how-to, one first-run tutorial) — controlled by an opt-out flag
- **Idempotency**: Re-runs produce zero diff against committed state. Missing quadrant dirs are added; existing files are preserved.
- **Precondition for C1**: C1 refuses to propose target files until C7 has produced `apps/docs/`. Classifier emits `setup-required` action and halts.
- **Flow ref**: FLOW-10.

### 3.5 C8 — Handover Capture (FLOW-11)

- **Module path**: `src/deviate/core/handover.py` (Python, not a skill — invoked from phase post-handlers, never via LLM)
- **Public API** (per `specs/plans/deviate-content.md` § File changes → New files, lines 88-95):
  - `handover_path(epic_slug, issue_id, task_id=None, phase) -> Path` — pure path computation
  - `persist_handover(epic_slug, issue_id, phase, manifest, task_id=None) -> Path` — write-or-skip; idempotent
  - `load_handover_records(window: EpicWindow) -> list[HandoverRecord]` — chronological read
  - `HandoverRecord` — read-side Pydantic model (no write-side persistence model; YAML is the durable artifact per `specs/plans/deviate-content.md` lines 13-15)
- **Path convention** (per `specs/plans/deviate-content.md` § Path convention, lines 44-49):
  - Macro handover: `.deviate/content/handovers/<epic_slug>/<issue_id>/<phase>.yaml`
  - Micro handover: `.deviate/content/handovers/<epic_slug>/<issue_id>/<task_id>/<phase>.yaml`
- **Trigger**: end of any DeviaTDD phase post-handler — called automatically, not by the user (per `specs/_product/flows/flows-content-capture.md:8-10`).
- **Dual input modes** (per `specs/plans/deviate-content.md` § Persistence flow, lines 64-73):
  - Manual path: skill actor emits YAML on stdout AND uses the Write tool to the canonical path; `persist_handover()` validates the file exists and exits (does not overwrite)
  - CLI path: skill actor emits YAML on stdout only; `AgentBackend` parses stdout and `persist_handover()` writes the file
- **Git discipline**: writes to `.deviate/content/handovers/**` which is gitignored (per `specs/plans/deviate-content.md` lines 17-19 and § File changes → Modifications, lines 83-87). No commit, no ledger append. Path traversal is rejected via `pathlib` (per `specs/plans/deviate-content.md` § Risks, lines 162-163).
- **Error surfaces** (per `specs/_product/flows/flows-content-capture.md:32-38`):
  - `HandoverArtifactMissing` — manual path: actor forgot the Write call; raised with canonical path
  - malformed YAML → `load_handover_records()` skips with warning
  - wrong path on CLI path → post-handler rejects with diagnostic
- **Flow ref**: FLOW-11.

### 3.6 C9 — Content Synthesis (FLOW-12)

- **Skill path**: `src/deviate/prompts/skills/deviate-content/SKILL.md` (macro layer)
- **CLI sub-app**: `src/deviate/cli/content.py` (per `specs/plans/deviate-content.md` § File changes → New files, line 94)
- **CLI surface** (per `specs/_product/flows/flows-content-capture.md:43-46` and `specs/plans/deviate-content.md` § File changes → New files, line 94):
  - `deviate content --format <blog|x-thread|release-notes|commit-story|resume-bullet> [--window EPIC-X] [--slug S] [--archive]`
  - `deviate content pre` / `deviate content post` subcommands
- **Aggregation strategy**: `load_handover_records(window)` from C8 gathers YAMLs in chronological order; C9 extracts `narrative_anchor` keyed by phase-specific field names (per `specs/_product/flows/flows-content-capture.md:50-52` and `specs/plans/deviate-content.md` § Narrative anchor field, lines 52-67).
- **Output paths** (per `specs/plans/deviate-content.md` § Path convention, lines 46-49):
  - Drafts: `.deviate/content/drafts/<format>/<slug>.md` (gitignored)
  - Archive: `specs/_archives/<epic_slug>-narrative.tar.gz` (committed-by-default only when `--archive` invoked)
- **Format dispatch**: C9 reads `format` flag and routes to the matching template from C10. Refusal on collision: existing draft file → CLI exits non-zero with `--force` suggestion (per `specs/_product/flows/flows-content-capture.md:60`).
- **Anchor fallback**: when no `narrative_anchor` block is present on any record, synthesis falls back to `phase` + `status` + `files` + `git log` metadata (per `specs/plans/deviate-content.md` lines 68-69).
- **Flow ref**: FLOW-12.

### 3.7 C10 — Format Template Pack (FLOW-12)

- **Resource location**: `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md` (per `specs/plans/deviate-content.md` § File changes → New files, lines 95-99)
- **Five format templates**, each a static markdown prompt with Jinja-style `{{ }}` placeholders for `epic_slug`, `slug`, `format`, and `records[]`:
  - `blog.md` — long-form post; intro must reference at least one `verdict_story` anchor when present (per `specs/_product/flows/flows-content-capture.md:78`)
  - `x-thread.md` — 6-post thread sliced from the same anchor pool
  - `release-notes.md` — per-release changelog draft (cross-referenced with `FLOW-03` per `specs/_product/flows/flows-content-capture.md:82`)
  - `commit-story.md` — per-commit narrative
  - `resume-bullet.md` — single accomplishment bullet
- **Consumed by**: C9 only. C8 does not read templates.
- **Validation surface**: the `test_blog_format` and `test_x_thread_format` acceptance tests assert that the intro paragraph of the rendered draft references a `narrative_anchor` field (per `specs/plans/deviate-content.md` § Task 2, lines 138-141).
- **Out of scope for v1**: auto-publish to X / blog; LLM-driven content refinement (`--refine` deferred); cross-repo aggregation; engagement metrics (per `specs/plans/deviate-content.md` § Out of scope v1, lines 199-204).
- **Flow ref**: FLOW-12.

### 3.8 Product-layer handover path convention

- **Macro handover (Product layer)**: `.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml`. The four Product-layer commands (`deviate-constitution`, `deviate-flows`, `deviate-architecture`, `deviate-release`) emit to this nested path so FLOW-12 (`deviate content`) can aggregate Product-layer output alongside Macro/Meso/Micro handovers.
- **Sentinel invocation**: Implementation calls `handover_path("_product", "<skill-name>", "<skill-name>")` from `src/deviate/core/handover.py`. The underscore-prefixed sentinel `epic_slug="_product"` is accepted by the existing `_validate_segment()` helper because it is non-empty, stripped, and contains no whitespace or path separators. No `handover_path()` signature change is required.
- **Underscore prefix distinction**: The leading underscore on `_product` reserves the segment for framework-internal use, distinguishing the Product-layer root from real epic slugs (`deviate-content`, `deviate-cli`, etc.). The sentinel `_product` mirrors the directory name `specs/_product/` for one-to-one traceability. Real epic slugs starting with `_` are reserved for framework-internal sentinels; a future revision may add a `[yellow]RESERVED_SENTINEL[/]` warning in `deviate explore` when invoked with `epic_slug="_product"` (out of scope for AC-ADHOC-013).
- **Path traversal guard unchanged**: The validation surface at `src/deviate/core/handover.py::_validate_segment` and the defense-in-depth check `resolved_target.relative_to(resolved_root)` (lines 85-92) continue to reject `..`, absolute paths, and whitespace. The sentinel `_product` passes the validation surface; the parameter-shape attack `handover_path("_product", "..", "constitution")` is rejected before any filesystem write.
- **Single top-level root preserved**: `.deviate/content/handovers/` remains the only top-level handover root (FLOW-02 governance unchanged). The new `_product/` subdirectory nests under `.deviate/content/handovers/` and does not introduce a new top-level directory; no architectural amendment to the FLOW-02 root is required.
- **Flow ref**: FLOW-11.

## 4. Integration Contracts

### 4.1 C1 → C2-C5 contract

- **Form**: Classification report (inlined markdown in C1's output, consumed by humans who then run the relevant C2-C5 skill).
- **Schema** (inlined in both C1 and each C2-C5 prompt):
  ```markdown
  # Classification Report — <sha-or-mode>

  ## Summary
  <one-paragraph change summary>

  ## Capabilities
  | capability | evidence | audience | doc_type | action | target_file | confidence |
  |------------|----------|----------|----------|--------|-------------|------------|
  | ...        | ...      | ...      | ...      | ...    | ...         | ...        |

  ## No-Touch List
  - <files that must not be modified>
  ```
- **DocType values**: `tutorial`, `how-to`, `reference`, `explanation`.
- **Action values**: `create`, `update`, `no-change`, `human-review`, `setup-required`.

### 4.2 C2-C5 → C6 contract

- **Form**: Updated files at the path declared in C1's `target_file` column, with valid Tome frontmatter.
- **No machine-parseable handoff**: C2-C5 emit markdown; C6 reads markdown. No structured metadata file is shared.

### 4.3 C7 → C1 contract

- **Form**: C1 reads the existence of `apps/docs/src/content/docs/` to decide whether to emit `setup-required` or proceed.
- **Tome frontmatter schema is declared in two places**: C7's `content.config.ts` (Starlight-side) and inline in C2-C5 prompts (LLM-side). Both must agree; drift between them is a verifier (C6) finding.

### 4.4 Phase post-handler → C8 contract

- **Form**: Every DeviaTDD phase post-handler calls `persist_handover()` from `src/deviate/core/handover.py` (per `specs/plans/deviate-content.md` § Persistence flow, lines 64-73). The skill actor is responsible for either:
  - **Manual path**: emitting YAML on stdout AND using the Write tool to the canonical path (`handover_path()` returns the target); post-handler validates the file exists.
  - **CLI path**: emitting YAML on stdout only; `AgentBackend` parses stdout and calls `persist_handover()` which writes the file.
- **Schema** (inlined in the terminal contract of every modified skill prompt — see `specs/plans/deviate-content.md` § Modifications, lines 79-87 for the 15-skill list):
  ```yaml
  phase: <phase-name>
  status: ok | warning | error
  files:
    - <relative-path>
  narrative_anchor:
    <phase-specific-field>: <text>   # optional; field names per deviate-content.md § Narrative anchor field
  ```
- **Anchor field map** (per `specs/plans/deviate-content.md` § Narrative anchor field, lines 52-67) — 12 phases, each with 2-3 named anchor fields (e.g., `judge` → `invariant_protected`, `verdict_story`; `prd` → `user_promise`, `non_goal`, `success_metric`).
- **Boundary rule**: `pathlib` everywhere; any path escaping `.deviate/content/handovers/` is rejected (per `specs/plans/deviate-content.md` § Risks, lines 162-163).

### 4.5 C8 → C9 contract

- **Form**: C9 reads via `load_handover_records(window)` which returns a chronological list of `HandoverRecord` Pydantic models parsed from the YAMLs in `.deviate/content/handovers/**/*.yaml` (per `specs/_product/flows/flows-content-capture.md:50` and `specs/plans/deviate-content.md` line 95).
- **No machine-parseable handoff file**: handovers are themselves the contract. C9 reads YAMLs; C8 writes YAMLs. There is no intermediate index or `narrative.jsonl` (per `specs/plans/deviate-content.md` § Context, lines 13-15 — the YAML manifest is the ledger).
- **Window filter**: `--window EPIC-X` restricts records to `.deviate/content/handovers/<epic_slug>/**`; absence of `--window` means all records (per `specs/plans/deviate-content.md` § Task 2, line 145).

### 4.6 C9 → C10 contract

- **Form**: C9 dispatches to one of the 5 templates in `src/deviate/prompts/content/` based on the `--format` flag. Unknown `--format` value → CLI lists the 5 valid formats and exits non-zero (per `specs/_product/flows/flows-content-capture.md:58-59`).
- **Template surface**: each template is a static markdown file with `{{ epic_slug }}`, `{{ slug }}`, `{{ format }}`, and `{{ records }}` placeholders. C9 fills them and writes to `.deviate/content/drafts/<format>/<slug>.md` (per `specs/plans/deviate-content.md` § Path convention, line 47).
- **Archive side-channel**: `--archive EPIC-X` writes `specs/_archives/<epic_slug>-narrative.tar.gz` containing every YAML under that epic (per `specs/plans/deviate-content.md` § Path convention, line 48 and § Task 2, line 146).

## 5. Data Ownership Boundaries

| Owner | Owns | Reads | Writes |
|---|---|---|---|
| C1 | Classification report (transient) | commit, diff, `specs/`, `apps/docs/src/content/docs/` (read-only) | nothing |
| C2 | `apps/docs/src/content/docs/tutorials/*.md` | commit, classification report | `tutorials/` |
| C3 | `apps/docs/src/content/docs/how-to/*.md` | commit, classification report | `how-to/` |
| C4 | `apps/docs/src/content/docs/reference/*.md` | commit, classification report | `reference/` |
| C5 | `apps/docs/src/content/docs/explanation/*.md` | commit, classification report | `explanation/` |
| C6 | Verification report (transient) | updated docs, commit, classification report | nothing |
| C7 | `apps/docs/` (scaffold, content config, starter set) | target repo state | `apps/docs/` |
| C8 | `.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml` | phase post-handler manifest (stdout or Write tool) | `.deviate/content/handovers/` |
| C9 | `.deviate/content/drafts/<format>/<slug>.md`, `specs/_archives/<epic>-narrative.tar.gz` | `.deviate/content/handovers/**/*.yaml` via `load_handover_records()` | `.deviate/content/drafts/`, `specs/_archives/` |
| C10 | `src/deviate/prompts/content/<format>.md` (read-only resource) | n/a (static) | `src/deviate/prompts/content/` (initial provisioning only) |

**Quadrant directory is the structural seam for Tome**: C2-C5 must not write outside their assigned quadrant. C7 is the only writer of `content.config.ts`, `index.md`, and `_meta/`. C1 and C6 are read-only.

**Path hierarchy is the structural seam for Content Capture**: C8 owns `.deviate/content/handovers/**`; C9 owns `.deviate/content/drafts/**` and `specs/_archives/**`. C10 is a static read-only resource consumed by C9. C8 and C9 never write outside their declared path roots; path traversal is rejected at the `pathlib` boundary.

## 6. Dependency Graph

```
FLOW-10 (C7 Setup) ──── gates ────> FLOW-04 (C1 Classify)
                                       │
                                       ├──> FLOW-05 (C2 Write Tutorial)
                                       ├──> FLOW-06 (C3 Write How-To)
                                       ├──> FLOW-07 (C4 Write Reference)
                                       └──> FLOW-08 (C5 Write Explanation)
                                                          │
                                                          └──> FLOW-09 (C6 Verify)
```

- **C7 is the only prerequisite for C1**. Until C7 has produced `apps/docs/`, C1 emits `setup-required` and halts.
- **C1 is the only prerequisite for C2-C5**. Each writer runs only when C1's capability table contains a row with that writer's `doc_type` and a `create` or `update` action.
- **C2-C5 are independent of each other** — no cross-writer coordination.
- **C6 runs only after at least one of C2-C5 has produced a file**. C6 is not blocking on the full set of writers; the developer can verify after each writer or after the whole set.
- **No CLI execution layer in v1**. All work is LLM-mediated through the skill prompts. A `deviate tome <phase>` CLI surface is deferred to a future iteration once v1 usage data shows which phases need deterministic enforcement.

### 6.1 Content Capture subgraph

```
ALL 12 phase post-handlers ──> C8 (Handover Capture)
                                       │
                                       ▼ writes
                              .deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml
                                       │
                                       ▼ reads
                                       C9 (Content Synthesis) ──reads templates──> C10 (Format Template Pack)
                                       │
                                       ├──> .deviate/content/drafts/<format>/<slug>.md
                                       └──> specs/_archives/<epic>-narrative.tar.gz  (--archive only)
```

- **Every DeviaTDD phase post-handler calls C8**. The 15 modified skill prompts (`deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`, `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks`) emit the YAML manifest; the post-handler routes it through C8 (per `specs/plans/deviate-content.md` § Modifications, lines 79-87).
- **C9 depends on C8's outputs only** — no direct dependency on any phase. C9 is decoupled from the phase pipeline; it is a downstream consumer.
- **C10 is a leaf resource** — consumed by C9, no dependencies.
- **C9's archive path is the only committed-by-default artifact** of Content Capture (per `specs/plans/deviate-content.md` § Context, lines 17-19). All handover YAMLs and drafts are gitignored runtime state.
- **`FLOW-02` (Architecture) governs the path conventions** (`.deviate/content/handovers/` and `.deviate/content/drafts/`) inherited by FLOW-11 and FLOW-12 (per `specs/_product/flows/flows-content-capture.md:31` and `:51`). This subgraph cannot introduce new top-level directory roots without amending this architecture document.

## 7. Flow Traceability

| Component | Flow IDs |
|---|---|
| C1 | FLOW-04 |
| C2 | FLOW-05 |
| C3 | FLOW-06 |
| C4 | FLOW-07 |
| C5 | FLOW-08 |
| C6 | FLOW-09 |
| C7 | FLOW-10 |
| C8 | FLOW-11 |
| C9 | FLOW-12 |
| C10 | FLOW-12 |

| Flow ID | Component |
|---|---|
| FLOW-04 | C1 |
| FLOW-05 | C2 |
| FLOW-06 | C3 |
| FLOW-07 | C4 |
| FLOW-08 | C5 |
| FLOW-09 | C6 |
| FLOW-10 | C7 |
| FLOW-11 | C8 |
| FLOW-12 | C9, C10 |

No orphans. Every flow maps to at least one component; every component maps to at least one flow.

## 8. Constitution Cross-Check

- §2 Frontend (None, CLI-only) — **Satisfied**. Tome skills are markdown prompts in `src/deviate/prompts/skills/`. No web/GUI runtime is added to DeviaTDD itself.
- §2 Backend (Python 3.13, Typer) — **Satisfied**. No new Python modules or runtime code.
- §2 Tech stack standards — **Satisfied**. No `package.json`, `astro.config.mjs`, or Node toolchain is added to DeviaTDD's repo. Skill *output* may include these files in target repos; that is out of scope for this constitution.
- §1 Architectural principles — **Satisfied**. Tome operates purely at the prompt layer, layered on top of DeviaTDD's three-layer architecture without modifying it.

No `[red]CONSTITUTION_CONFLICT[/]`. No amendment required.

### 8.1 Content Capture Constitution Cross-Check

- §2 Frontend (None, CLI-only) — **Satisfied**. C9's CLI surface (`deviate content`) is Typer-based; no web/GUI runtime is introduced.
- §2 Backend (Python 3.13, Typer) — **Satisfied**. `src/deviate/core/handover.py` and `src/deviate/cli/content.py` follow the existing Python 3.13 + Typer stack.
- §2 Database (No persistent database runtime; session state under `.deviate/`) — **Satisfied**. `.deviate/content/handovers/` and `.deviate/content/drafts/` are session-state directories under `.deviate/`, consistent with the existing `.deviate/` convention.
- §2 Infrastructure (Aider micro-sandbox for `src/**/*.py`) — **Satisfied**. The 15 modified skill prompts operate at the LLM-mediated prompt layer (no Python code change in their hot paths); C8 is a pure-Python helper invoked from phase post-handlers.
- §1 Append-Only Ledger Protocol — **Satisfied with note**. The Constitution states "All state transitions in `issues.jsonl` and `tasks.jsonl` are append-only." The Content Capture YAMLs are NOT a ledger — they are gitignored runtime state, by explicit design (per `specs/plans/deviate-content.md` § Context, lines 13-15). No append-only guarantee is offered or required for these files; `persist_handover()` is idempotent overwrite-or-skip, not append.
- §1 Three-Layer Architecture — **Satisfied**. Content Capture adds a post-handler step to each phase but does not introduce a new layer or skip a gate.

No `[red]CONSTITUTION_CONFLICT[/]`. No amendment required.

## 9. Cross-Layer Signal

Downstream `deviate shard` invocations will emit `flow_refs:` for any issue derived from this architecture, keyed to the component→flow map in §7. Two epics will derive their issue sets from this document:

- **Tome Subsystem epic** — derives from FLOW-04..FLOW-10 plus the architectural seams in §4.1–§4.3 and §5.
- **Content Capture epic** — derives from FLOW-11..FLOW-12 plus the seams in §4.4–§4.6 and §6.1. The cross-cutting touch on the 15 modified skills means the Content Capture epic's `flow_refs:` will also include `FLOW-11` on every issue derived from any other epic whose TDD task runs through those skills, since each micro-task now emits a handover YAML.

The path-convention decisions (`.deviate/content/handovers/`, `.deviate/content/drafts/`, `specs/_archives/`) made here are inherited by `FLOW-11` and `FLOW-12` per the cross-reference at `specs/_product/flows/flows-content-capture.md:31` and `:51`. Any future epic that needs a new `.deviate/` subdirectory root must amend this architecture document first.
