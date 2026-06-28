# DeviaTDD Product Domain Model

**Last Updated**: 2026-06-27
**Source**:
  - `specs/_product/architecture.md` §3.1–§3.4 (Tome Subsystem, FLOW-04..FLOW-10)
  - `specs/_product/architecture.md` §3.5–§3.7 (Content Capture Subsystem, FLOW-11..FLOW-12)
  - `specs/plans/deviate-content.md` § Path convention and § File changes

---

## Entities

### Commit
- **Attributes**: `sha`, `message`, `changed_files[]`, `changed_tests[]`, `merged_diff` (or `branch_diff` for merge-base mode)
- **Relationships**:
  - has many `Capability` (1..n) — what changes the commit introduces that may need docs
  - input to `ClassificationReport`

### ClassificationReport
- **Attributes**: `change_summary`, `capabilities[]` (Capability list), `no_touch_list[]` (file paths), `mode` (commit | sha | merge-base | working-tree), `target_sha`
- **Relationships**:
  - produced by C1 (Tome Classifier)
  - consumed by C2-C5 (writers, via human handoff)
  - consumed by C6 (verifier, for boundary reconciliation)

### Capability
- **Attributes**: `capability` (string), `evidence` (string), `audience` (user | operator | contributor | internal), `doc_type` (DocType), `action` (Action), `target_file` (path), `confidence` (0.0-1.0)
- **Relationships**:
  - belongs to one `ClassificationReport`
  - routes to one writer (C2-C5) based on `doc_type`

### DocType (enum)
- **Values**: `tutorial`, `how-to`, `reference`, `explanation`
- **Cardinality**: 1:1 with writer components C2-C5

### Action (enum)
- **Values**: `create`, `update`, `no-change`, `human-review`, `setup-required`
- **Semantics**:
  - `create` / `update` → triggers a writer (C2-C5)
  - `no-change` → no writer runs; C6 also skipped
  - `human-review` → human reviews before any writer runs
  - `setup-required` → C7 must run before C1 can proceed

### DocPage
- **Attributes**: `path` (relative to `apps/docs/src/content/docs/`), `frontmatter` (TomeFrontmatter), `content` (markdown body), `last_verified_at`, `verified_sha`, `related_issues[]`
- **Relationships**:
  - lives in one `StarlightQuadrant`
  - produced/updated by exactly one writer (C2-C5) based on `doc_type`

### TomeFrontmatter
- **Attributes**: `title`, `description`, `doc_type` (DocType), `status` (draft | reviewed), `last_verified_at` (date), `verified_sha`, `related_issues[]`
- **Relationships**:
  - embedded in every `DocPage`
  - schema declared in two places: C7's `content.config.ts` (Starlight-side) and inline in C2-C5 prompts (LLM-side)

### VerificationReport
- **Attributes**: `pass_items[]`, `fail_items[]`, `boundary_violations[]`, `recommended_files[]`
- **Relationships**:
  - produced by C6 (Tome Verifier)
  - consumed by humans (no auto-routing to writers)

### StarlightQuadrant (enum)
- **Values**: `tutorials`, `how-to`, `reference`, `explanation`
- **Cardinality**: 1:1 with writer components C2-C5
- **Ownership**: directory path under `apps/docs/src/content/docs/<quadrant>/`

## Content Capture Entities (FLOW-11, FLOW-12)

### PhaseHandover
- **Attributes**: `phase` (Phase), `status` (HandoverStatus), `files[]` (relative paths), `narrative_anchor?` (NarrativeAnchor), `epic_slug`, `issue_id`, `task_id?`, `created_at`
- **Persistence**: YAML file at `.deviate/content/handovers/<epic_slug>/<issue_id>/[<task_id>/]<phase>.yaml` (per `specs/plans/deviate-content.md` § Path convention, lines 45-46). Gitignored.
- **Relationships**:
  - belongs to one Epic (by `epic_slug`)
  - belongs to one Issue (by `issue_id`)
  - optionally belongs to one Task (by `task_id`)
  - emitted by exactly one Phase post-handler (per `specs/plans/deviate-content.md` § Persistence flow, lines 64-73)
  - consumed by `load_handover_records()` for `FLOW-12`

### Phase (enum)
- **Values**: `explore`, `research`, `prd`, `shard`, `plan`, `tasks`, `red`, `green`, `yellow`, `judge`, `refactor`, `e2e` — the canonical 12-phase set (per `specs/_product/flows/flows-content-capture.md:12-13`)
- **Cardinality**: 1:1 with `PhaseHandover`

### HandoverStatus (enum)
- **Values**: `ok`, `warning`, `error`
- **Semantics**: reflects the post-handler outcome; `error` triggers `FLOW-11` success-state failure but does NOT halt synthesis (`FLOW-12` proceeds with whatever handovers are present)

### NarrativeAnchor
- **Attributes**: phase-specific field map (e.g., for `judge`: `invariant_protected`, `verdict_story`; for `prd`: `user_promise`, `non_goal`, `success_metric`). See full field map at `specs/plans/deviate-content.md` § Narrative anchor field, lines 52-67.
- **Optionality**: absence is non-fatal — backward-compatible with skills that have not yet been updated (per `specs/plans/deviate-content.md` § Persistence flow, line 17 and § Context, lines 13-15)
- **Relationships**:
  - embedded 0..1 per `PhaseHandover`
  - consumed by `ContentDraft` for intro-paragraph reference (per `specs/_product/flows/flows-content-capture.md:78`)
  - tracked as a quality signal for synthesis latency feedback

### HandoverRecord (read-side)
- **Attributes**: same as `PhaseHandover` (parsed from YAML via `yaml.safe_load`)
- **Cardinality**: 1:1 with `PhaseHandover`
- **Module**: Pydantic model in `src/deviate/core/handover.py` (per `specs/plans/deviate-content.md` § File changes → New files, line 91). Read-side only — there is no write-side persistence model; the YAML file IS the durable artifact.

### EpicWindow (filter)
- **Attributes**: `epic_slug?` (optional), `issue_id?` (optional)
- **Semantics**: restricts `load_handover_records()` to a path prefix. `EpicWindow(epic_slug="X")` matches `.deviate/content/handovers/X/**`. Empty window matches all records.

### ContentDraft
- **Attributes**: `format` (FormatKind), `slug`, `path` (`.deviate/content/drafts/<format>/<slug>.md`), `epic_slug?`, `narrative_anchors_referenced[]` (field names actually used), `created_at`, `byte_count`
- **Persistence**: markdown file under `.deviate/content/drafts/<format>/<slug>.md` (per `specs/plans/deviate-content.md` § Path convention, line 47). Gitignored.
- **Relationships**:
  - produced by C9 (Content Synthesis) from one or more `PhaseHandover` for one `EpicWindow`
  - rendered by exactly one `FormatTemplate` from C10
  - consumed by humans (no auto-publish, per `specs/plans/deviate-content.md` § Out of scope v1, line 200)

### FormatKind (enum)
- **Values**: `blog`, `x-thread`, `release-notes`, `commit-story`, `resume-bullet`
- **Cardinality**: 1:1 with the 5 templates in C10 (per `specs/plans/deviate-content.md` § File changes → New files, lines 95-99)
- **Semantics**: `--format` flag value on `deviate content` CLI; unknown values cause the CLI to list the 5 valid formats and exit non-zero (per `specs/_product/flows/flows-content-capture.md:58-59`)

### FormatTemplate (resource)
- **Attributes**: `kind` (FormatKind), `path` (`src/deviate/prompts/content/<kind>.md`), `placeholders[]` (`epic_slug`, `slug`, `format`, `records`)
- **Relationships**:
  - static read-only resource (per `specs/_product/architecture.md` §3.7 C10 detail)
  - consumed by C9 only; C8 does not read templates

### ContentArchive
- **Attributes**: `epic_slug`, `path` (`specs/_archives/<epic_slug>-narrative.tar.gz`), `tarball_size` (bytes), `handover_count`, `created_at`
- **Persistence**: tarball at `specs/_archives/<epic_slug>-narrative.tar.gz` (per `specs/plans/deviate-content.md` § Path convention, line 48). Committed-by-default when `--archive` is invoked — the only committed artifact of Content Capture.
- **Relationships**:
  - contains N `PhaseHandover` YAMLs for one `epic_slug`
  - produced by C9 with `--archive` flag (per `specs/plans/deviate-content.md` § Task 2, line 146)
  - optional — not produced unless `--archive` is explicitly invoked

## Entity-Relationship Summary

```
Commit ──1..n──> Capability ──1──> DocType ──1──> Writer (C2-C5) ──1──> DocPage
                       │
                       └──> Action ──> routes to writer | halts C1 | no-op

ClassificationReport ──1──> Capability[]  (transient)
DocPage ──1──> TomeFrontmatter
DocPage ──1──> StarlightQuadrant
VerificationReport (transient, output of C6)


Phase (post-handler) ──1──> PhaseHandover ──0..1──> NarrativeAnchor
                              │
                              ├──> epic_slug ──> Epic ──0..1──> ContentArchive
                              └──> consumed by ──> EpicWindow ──> load_handover_records()
                                                                        │
                                                                        ▼
                                                              ContentDraft ──1──> FormatTemplate ──1──> FormatKind
```

## Delta from Prior Version

### Tome subsystem delta (2026-06-26)
- **Added**: `Commit`, `ClassificationReport`, `Capability`, `DocType`, `Action`, `DocPage`, `TomeFrontmatter`, `VerificationReport`, `StarlightQuadrant` — 9 entities introduced by the Tome subsystem.

### Content Capture subsystem delta (2026-06-27)
- **Added**: `PhaseHandover`, `Phase`, `HandoverStatus`, `NarrativeAnchor`, `HandoverRecord`, `EpicWindow`, `ContentDraft`, `FormatKind`, `FormatTemplate`, `ContentArchive` — 10 new entities introduced by the Content Capture subsystem.
- **Removed**: none.
- **Modified**: none (no Tome entity touched by Content Capture — orthogonal subsystems).
- **Cumulative total entity count**: 19.

`[yellow]DOMAIN_MODEL_DELTA[/]` — 10 new entities added by FLOW-11/FLOW-12; flagged for HITL Gate 1 review per architecture-skill invariant 5. Cross-epic impact: the 15 modified skill prompts (`deviate-red`, `deviate-green`, etc.) gain a `PhaseHandover` emission contract; this is a structural change to the terminal contract of each modified skill.
