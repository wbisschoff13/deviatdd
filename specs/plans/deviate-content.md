# Deviate Content — Plan

**Status**: Temporary plan, awaiting elevation to a tracked issue.
**Goal**: Capture DeviaTDD phase work as durable, queryable artifacts and synthesize them into blog posts / X threads / release notes / resume bullets for marketing Deviate, Scribe, Tome, and DeviaTDD itself.

---

## Context

The user is building a new agent in the Deviate / Scribe / Tome lineage with DeviaTDD and wants per-phase logs that can later be turned into resume-site blog content and X threads. The plan captures that without pre-building aggregation infrastructure we don't yet have query patterns for.

Three simplifications drove the final shape of this plan (each is a real cut, not just renaming):

1. **YAML files ARE the ledger.** No `specs/narrative.jsonl`, no persistence-layer `HandoverRecord` Pydantic model, no content-hash on write. The YAML manifest under `.deviate/content/handovers/` is the durable artifact. Re-emittable from skills if lost.
2. **Skill actor writes; runner stays minimal.** One-sentence prompt addition per skill. Runner post command writes the file only if the actor didn't (CLI orchestration path).
3. **No commit on handover YAMLs.** Gitignored runtime state. Git log already captures code/test/spec changes; the YAML is synthesis material, not project source.

---

## Design

### Path convention

| Layer | Path |
|---|---|
| Macro handover | `.deviate/content/handovers/<epic_slug>/<issue_id>/<phase>.yaml` |
| Micro handover | `.deviate/content/handovers/<epic_slug>/<issue_id>/<task_id>/<phase>.yaml` |
| Synthesis drafts | `.deviate/content/drafts/<format>/<slug>.md` |
| Archive (opt-in, committed) | `specs/_archives/<epic_slug>-narrative.tar.gz` |

All `.deviate/content/handovers/**` and `.deviate/content/drafts/**` are gitignored. The archive path is the only committed-by-default artifact (only when `--archive` is invoked).

### Narrative anchor field

Each skill's YAML terminal contract gets an optional `narrative_anchor:` block. The runner treats absence as "no anchor for this phase" — backward-compatible with skills that haven't been updated yet.

| Phase | Anchor fields |
|---|---|
| `deviate-explore` | `problem`, `boundary_clarified`, `surprise` |
| `deviate-research` | `decision`, `alternative_rejected`, `risk` |
| `deviate-prd` | `user_promise`, `non_goal`, `success_metric` |
| `deviate-shard` | `slice_reasoning`, `dependency_insight` |
| `deviate-plan` | `approach_choice`, `risk_acknowledged` |
| `deviate-tasks` | `parallelization_note` |
| `deviate-red` | `assumption_frozen`, `interesting_failure_mode` |
| `deviate-green` | `implementation_decision`, `alternative_considered` |
| `deviate-yellow` | `spec_drift`, `new_rule` |
| `deviate-judge` | `invariant_protected`, `verdict_story` |
| `deviate-refactor` | `smell_removed`, `naming_lesson` |
| `deviate-e2e` | `acceptance_proof`, `user_facing_observation` |
| `deviate-constitution` | `principle`, `enforcement_scope`, `exception_boundary` |
| `deviate-flows` | `user_role`, `trigger`, `success_signal` |
| `deviate-architecture` | `component`, `integration_contract`, `classification` |
| `deviate-release` | `release_goal`, `included_flows`, `deferred_work` |

Synthesis uses anchors as raw material; absence is non-fatal — synthesis falls back to `phase` + `status` + `files` + git-log metadata.

### Persistence flow

```
Manual path:    actor → YAML on stdout + Write tool → .deviate/content/handovers/<epic>/<issue>/<phase>.yaml
                                                  → post command: validates, exits (no git ops)

CLI path:       actor → YAML on stdout → AgentBackend parses → post command writes file
                                                  → post command: validates, exits (no git ops)

Either path:    .deviate/content/handovers/** is gitignored. No commit, no ledger append.
```

The runner's `persist_handover()` helper is a single function called from each phase post handler. It only writes if the file isn't already there (CLI path) and never touches git.

---

## File changes

### Modifications

**15 skills** get one-sentence Write instruction appended to `<output_format_schemas>`:

- Micro / orchestration: `deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`
- Macro: `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks`

(Full audit in Task 1 — any skill whose terminal contract is a YAML manifest gets the instruction; macro skills that emit a primary artifact like `explore.md` or `design.md` get the anchor block too but the Write instruction is optional since the primary artifact already lands on disk.)

**`.deviate/.gitignore`** — add:
```
.deviate/content/
```

### New files

- `src/deviate/prompts/skills/deviate-content/SKILL.md` — synthesis skill (macro layer)
- `src/deviate/core/handover.py` — `handover_path()`, `persist_handover()`, `load_handover_records()`, `HandoverRecord` (read-side model only)
- `src/deviate/cli/content.py` — `deviate content pre|post` (with `--format`, `--window`, `--slug`, `--archive` flags)
- `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md` — format templates
- `tests/test_handover/test_path_resolution.py`
- `tests/test_handover/test_persist_manual_path.py`
- `tests/test_handover/test_persist_cli_path.py`
- `tests/test_handover/test_idempotent_write.py`
- `tests/test_content/test_load_records.py`
- `tests/test_content/test_blog_format.py`
- `tests/test_content/test_x_thread_format.py`
- `tests/test_content/test_window_filter.py`
- `tests/test_content/test_archive_flag.py`

---

## Task decomposition (2 tasks)

### Task 1: Capture — skill Write instructions + runner helper

**RED** — 4 tests:
1. `test_path_resolution`: macro and micro cases resolve to expected `.deviate/content/handovers/...` paths.
2. `test_persist_manual_path`: simulate skill actor writing YAML via Write tool to canonical path; assert file present, valid YAML, NOT in git index.
3. `test_persist_cli_path`: simulate CLI orchestration path where actor emits only to stdout; assert `persist_handover()` writes the file from the captured manifest.
4. `test_idempotent_write`: actor writes twice with identical content; assert single file, no errors.

**GREEN**:
- Implement `src/deviate/core/handover.py` with `handover_path()`, `persist_handover()`, `load_handover_records()`, read-side `HandoverRecord` Pydantic model.
- Update `.deviate/.gitignore` to exclude `.deviate/content/`.
- Audit the 24-skill list and add the one-sentence Write instruction to the 15 listed above.

**REFACTOR**:
- Extract path pattern into a single constant.
- Centralize macro/micro detection by presence of `task_id`.
- Reuse existing git-isolation patterns from `tests/conftest.py`.

**Acceptance**:
- 4 tests pass.
- Modified skills still pass skill-shape validation (no regressions in existing tests).
- Smoke test: run `deviate explore pre ...` + simulated actor + `deviate explore post ...` → `.deviate/content/handovers/<epic>/<issue>/explore.yaml` exists, is valid YAML, is not staged in git.

### Task 2: Synthesis — `deviate content` skill

**RED** — 5 tests:
1. `test_load_records`: given a fixture directory of YAML files (one per phase across one epic), assert `load_handover_records()` returns the expected list in chronological order.
2. `test_blog_format`: given fixture YAMLs (including a `verdict_story` anchor from a judge phase), assert `--format blog` produces a draft whose intro paragraph references that anchor.
3. `test_x_thread_format`: assert `--format x-thread` produces a 6-post thread sliced from the same anchors.
4. `test_window_filter`: assert `--window EPIC-X` only includes YAMLs under that epic.
5. `test_archive_flag`: assert `--archive EPIC-X` produces `specs/_archives/<epic>-narrative.tar.gz` containing all YAMLs under that epic.

**GREEN**:
- Create `src/deviate/prompts/skills/deviate-content/SKILL.md` (macro layer, follows existing `deviate-*` shape).
- Implement synthesis in `src/deviate/core/handover.py` (or new `core/synthesis.py`) — `synthesize_draft(records, format) -> str`.
- Create 5 format templates in `src/deviate/prompts/content/`.
- Implement `src/deviate/cli/content.py` with `pre` / `post` subcommands.

**REFACTOR**:
- Extract format rendering into pluggable template functions.
- Extract anchor extraction into a separate utility (`extract_anchor(phase, record) -> dict | None`).
- Consistent error messages across all format templates.

**Acceptance**:
- 5 tests pass.
- End-to-end smoke: run `deviate explore` + `deviate research` + `deviate shard` + red/green/judge/refactor against a fixture epic → `deviate content --format blog --window <epic>` produces a draft whose opening paragraph references the judge's `verdict_story` anchor.

---

## Risks

| Risk | Mitigation |
|---|---|
| LLM actor forgets Write call | Post command checks `handover_path.exists()`; raises `HandoverArtifactMissing` with the canonical path so the actor knows exactly what to do. |
| LLM actor writes malformed YAML | `yaml.safe_load` in `load_handover_records()` skips with warning; CLI post path validates schema before accepting. |
| LLM actor writes to wrong path | CLI post validates path matches expected pattern. |
| Path traversal | `pathlib` everywhere; reject any path that escapes `.deviate/content/handovers/`. |
| Cross-repo aggregation queries | Out of scope v1. Re-evaluate when query patterns emerge. |
| Path collisions (same task, multiple phases) | Impossible — phase is unique within a task in DeviaTDD's existing model. |
| Actor writes stale content from a re-run | Idempotent re-write test catches this for identical content; divergent content is a real failure surfaced by git log diff. |

---

## Verification

- `mise run test` — full suite, including new `test_handover/` and `test_content/`.
- `mise run test-e2e` — bats E2E test running a 1-task pipeline and verifying `.deviate/content/handovers/<epic>/<issue>/<task>/red.yaml` exists.
- Manual smoke against the resume-site epic the user is about to start.

---

## Out of scope (v1)

- Auto-publish to X / blog — synthesis produces drafts only; human publishes.
- LLM-driven content refinement — template-based v1; `--refine` flag possible later.
- Cross-repo aggregation — single-repo only.
- `specs/narrative.jsonl` or any other append-only ledger for narrative events.
- Engagement metrics on published content.
- Engagement with the existing `tome-*` skills — orthogonal; can integrate later if blog content needs Diátaxis-quadrant classification.
