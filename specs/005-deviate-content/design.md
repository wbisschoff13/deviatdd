# Content Capture Subsystem — Research Design (HALTED at Constitutional Violation)

**Epic**: 005-deviate-content
**Status**: CONSTITUTIONAL_VIOLATION_RESOLVED — awaiting `/deviate-prd` per operator direction
**Date**: 2026-06-27
**Source Flows**: FLOW-11 (Capture Phase Handover), FLOW-12 (Synthesize Content Digest)

**Resolution Note**: Operator selected option (a) — constitution amendment. `specs/constitution.md` v0.3.0 adds an explicit Tamper Guard exception for `.deviate/feat/**/*.yaml` and `.deviate/content-drafts/**/*.md` (Content Capture runtime state, gitignored, never participating in `git diff` evaluation). The workflow remains halted at this design.md checkpoint. Operator will resume manually with `/deviate-prd` rather than re-running `/deviate-research`; the Alpha/Beta/Gamma fragments below are preserved in full as the canonical architectural analysis for the epic.

---

## Constitutional Violation

[Trigger]: Subagent Gamma's audit of `specs/plans/deviate-content.md` § Persistence flow (lines 64-73) combined with § Modifications (lines 79-87) determined that the "manual path" for handover capture instructs micro-layer skill actors to perform Write tool calls to `.deviate/feat/<epic>/<issue>/[<task>/]<phase>.yaml`. The nine micro-layer skills in the 15-skill modification list (`deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`) would, on first execution that obeys the Write instruction, write to a path outside the Tamper Guard's allow-list and trigger immediate rollback.

[Violating_Decision]: The "Manual path" persistence mode for the nine micro-layer skills in the 15-skill modification list (per `specs/plans/deviate-content.md` § Persistence flow line 65: "Manual path: actor → YAML on stdout + Write tool → .deviate/feat/<epic>/<issue>/<phase>.yaml").

[Violated_Clause]: `specs/constitution.md` §1 Tamper Guard & Micro-Sandboxing, verbatim:

> "Micro-layer LLM execution (Aider) is strictly sandboxed: it is granted write access **only** to files matching `src/**/*.py`. All `tests/`, `specs/`, and configuration files are strictly read-only during Micro-layer execution. Any mutation outside this allow-list triggers an immediate rollback."

`.deviate/feat/**/*.yaml` matches the implementation's `_is_config_file` predicate (any path whose parts include `.deviate` is treated as a configuration file and protected during GREEN/YELLOW contexts — see `src/deviate/core/tamper.py:55-58`). Even though gitignored files may not appear in `git diff --name-only` at runtime (the Tamper Guard's actual detection mechanism), the constitution's literal text grants micro-layer actors write access only to `src/**/*.py` and treats `.deviate/**` as configuration. A Write tool call from a micro actor to `.deviate/feat/**/*.yaml` is a mutation outside the allow-list as written.

[Rejected_Alternative]: The architectural argument at `specs/_product/architecture.md` §8.1 cross-check ("Satisfied. The 15 modified skill prompts operate at the LLM-mediated prompt layer (no Python code change in their hot paths); C8 is a pure-Python helper invoked from phase post-handlers.") does NOT address the manual path because, per the plan's own Persistence flow (line 65), the post-handler on the manual path only "validates, exits (no git ops)" — it does NOT call C8. The Write tool call is made directly by the LLM, and the constitution's sandbox fires rollback (literal text; implementation nuance noted but does not amend the constitutional rule).

[Required_Action]: ONE of the following three resolutions MUST be chosen BEFORE Task 1 GREEN phase runs:

| Option | Description | Reversibility | Blast Radius | Selected |
|---|---|---|---|---|
| **(a) Constitution Amendment** | Add an explicit exception to `specs/constitution.md` §1 Tamper Guard clause: ".deviate/feat/**/*.yaml and .deviate/content-drafts/**/*.md are gitignored runtime state owned by the skill actor's Write tool; they are NOT subject to source-tree rollback during micro-layer execution." Record with version bump 0.2.0 → 0.3.0. | Medium (constitution is append-only; amendment is permanent) | High (sets precedent for future gitignored-runtime-state in Tamper Guard) | **YES — applied 2026-06-27** |
| **(b) Plan Revision** | Split the 15-skill instruction into two per-layer forms: micro-layer skills (the 9 listed above) get CLI-path-only instruction ("After tests fail, the runner's stdout parser captures your manifest; do not use any tools."); macro-layer skills (`deviate-research`, `deviate-prd`, `deviate-shard`) and orchestration skills (`deviate-plan`, `deviate-tasks`, `deviate-execute`, `deviate-review`) retain the Write tool instruction. | High (plan edit before any code committed) | Low (skill prompts only; C8 unchanged) | No |
| **(c) Runtime Mechanism** | C8 MUST be invoked even on the manual path. The Write tool call is intercepted by a sandbox-extension hook in `src/deviate/cli/macro.py` post-handlers that pre-creates the target directory with restricted permissions and writes the YAML via Python rather than via the actor's Write tool. This requires adding `approved_mods` entries to `TamperGuard.check()` calls in micro-layer post-handlers so the path is explicitly allowlisted at evaluation time. | Medium (new plumbing in `src/deviate/cli/macro.py`) | Medium (touches micro-layer post-handlers) | No |

[Halt_Condition]: The post-script `deviate research post` is NOT invoked. The workflow terminates at this step. `data-model.md` is NOT written because there is no approved design to model. The human operator MUST select option (a), (b), or (c) — or rerun `/deviate-explore` with a modified problem statement that excludes the manual path for micro-layer skills. **Status**: option (a) selected and applied; post-script remains NOT invoked per skill invariant. Operator resumes manually with `/deviate-prd`.

---

## Summary

Subagents Alpha, Beta, and Gamma were dispatched in parallel against the explore.md context. Alpha produced a 5-decision Options Matrix with Single Option Dominance applied to all five rows (each `(a)` option satisfies all constraints from `specs/_product/release-next.md` and is concretely anchored in `specs/plans/deviate-content.md`). Beta materialized the 10 pre-specified entities from `specs/_product/domain-model.md` into concrete Pydantic 2.x schemas and surfaced eight field-level gaps requiring HITL resolution. Gamma's adversarial audit surfaced **one Violation** (Tamper Guard), **four Tensions** (Append-Only Ledger spirit, Coverage target, Tamper Guard scope ambiguity on prompt files, Judge phase omission from Definition of Done), and **ten Aligned clauses**, plus seven Contrarian Viewpoints and a seventeen-row Risk Register.

Per the deviate-research skill's CRITICAL INVARIANT #2 (Agent-Level Constitutional Violation Gate), the Violation halts the workflow. The fragments below are preserved in full for human review.

---

## Recommended Architecture (Subagent Alpha)

[Summary]: A single Python module `src/deviate/core/handover.py` exposes `handover_path()`, `persist_handover()`, `load_handover_records()`, and a read-side `HandoverRecord` Pydantic model. A single Typer sub-app `src/deviate/cli/content.py` exposes `deviate content --format <blog|x-thread|release-notes|commit-story|resume-bullet> [--window EPIC-X] [--slug S] [--archive]` plus `deviate content pre|post`. One new macro-layer skill `src/deviate/prompts/skills/deviate-content/SKILL.md` and five read-only format templates under `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md` complete the synthesis surface. The 15 existing skills receive a one-sentence Write instruction appended to their `<output_format_schemas>` block — runner stays minimal, actor writes.

[Module_Surface]:

*New modules (5 + 9 test files):*
- `src/deviate/core/handover.py` — `handover_path()`, `persist_handover()`, `load_handover_records()`, read-side `HandoverRecord` (per `specs/plans/deviate-content.md:92`)
- `src/deviate/cli/content.py` — `deviate content pre|post` + `--format/--window/--slug/--archive` flags (per `specs/_product/flows/flows-content-capture.md:43-46`)
- `src/deviate/prompts/skills/deviate-content/SKILL.md` — macro-layer synthesis skill
- `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md` — 5 format templates (per `specs/plans/deviate-content.md:97-99`)
- 9 new pytest tests under `tests/test_handover/` (4) and `tests/test_content/` (5) per `specs/plans/deviate-content.md:104-112`

*Modified (16):*
- 15 SKILL.md files: `deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`, `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks` (per `specs/plans/deviate-content.md:79-87`)
- `.deviate/.gitignore` — add `/feat/` and `/content-drafts/` (per `specs/plans/deviate-content.md:83-86`)

*No modification:* `src/deviate/core/agent.py` (the existing `HandoverManifest` schema with `extra="allow"` at `src/deviate/core/agent.py:21` is already forward-compatible); `src/deviate/cli/macro.py` (post-handler integration is per-phase, not a single edit); `src/deviate/cli/__init__.py` (single `cli.add_typer(content_app, name="content")` line addition at lines 594-619 pattern).

[Rationale]: Anchored to constitution quotes (`specs/constitution.md` v0.2.0 — tech stack standards, architectural principles), explore.md FILE_REGISTRY rows (HandoverManifest at `src/deviate/core/agent.py:21`; pre/post Typer pattern at `src/deviate/cli/macro.py:195-275`; no new dependencies per Verified Dependencies block), and the product-layer artifacts at `specs/_product/architecture.md:130-201`, `specs/_product/flows/flows-content-capture.md:31,:51`, `specs/_product/release-next.md` Acceptance Criteria 1-15. The Single Option Dominance Rule applies to all five architectural decisions because each `(a)` option satisfies every binding constraint from `specs/_product/release-next.md` and is concretely anchored in the plan and architecture documents.

## Options Matrix (Subagent Alpha)

| # | Decision | Option | Complexity | Testability | Constitutional Alignment | Reversibility | Blast Radius | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Path convention encoding | (a) Slug-based `.deviate/feat/<epic_slug>/<issue_id>/[<task_id>/]<phase>.yaml` | Low | High | **Aligned** w/ `architecture.md:143` | High | Local | **Selected** |
| 1 | Path convention | (b) Literal raw string | Low | Medium | Conflict w/ `architecture.md:144` | Medium | Local | **Rejected** |
| 1 | Path convention | (c) Hybrid literal/slugged | Medium | Medium | Conflict w/ `architecture.md:143-146` | Low | Local | **Rejected** |
| 2 | Handover schema evolution | (a) Extend existing `HandoverManifest` (`src/deviate/core/agent.py:21`) | Low | High | Partial conflict — mixes stdout contract with on-disk YAML | Medium | Medium | **Rejected** |
| 2 | Handover schema | (b) Separate read-side `HandoverRecord` Pydantic in `src/deviate/core/handover.py`; on-disk YAML uses `extra="allow"` | Low | High | **Aligned** w/ `plans/deviate-content.md:92` | High | Local | **Selected** |
| 3 | Synthesis approach | (a) Template-only (Jinja-style `{{ }}` substitution) | Low | High | **Aligned** w/ `architecture.md:177` | High | Low | **Selected** |
| 3 | Synthesis approach | (b) LLM-driven (Qwen3.7-Plus renders markdown) | High | Low | Conflict — adds tier-3 invocation outside 3-layer pipeline | Low | High | **Rejected** |
| 3 | Synthesis approach | (c) Hybrid template + `--refine` | Medium | Medium | Conflict with v1 scope (`plans/deviate-content.md:201`) | Medium | Medium | **Rejected (deferred)** |
| 4 | Anchor persistence | (a) Per-phase typed field map (12 phases × 2-3 named fields) | Medium | High | **Aligned** w/ `plans/deviate-content.md:52-67` | Medium | Medium | **Selected** |
| 4 | Anchor persistence | (b) Free-form dict | Low | Medium | Conflict — degrades `test_blog_format` | High | Low | **Rejected** |
| 5 | Cross-cutting touch strategy | (a) 15 one-sentence appends to `<output_format_schemas>` | Low | High | **Aligned** w/ `architecture.md:281-283` | High | Low | **Selected** |
| 5 | Cross-cutting touch strategy | (b) Wrapper skill absorbs Write responsibility | Medium | Medium | Conflict — inverts actor-writes contract | Low | High | **Rejected** |
| 5 | Cross-cutting touch strategy | (c) CLI flag `--capture-yaml` post-handler | Medium | Medium | Conflict — actor loses agency; anchors become empty | High | Medium | **Rejected** |

**Single Option Dominance Rule applied** to all five decisions.

## Rejected Options (Subagent Alpha)

- **Write-side `HandoverRecord` Pydantic model + content-hash on write.** Rejected per `specs/plans/deviate-content.md:13-15`.
- **`specs/narrative.jsonl` append-only narrative ledger.** Rejected per `specs/plans/deviate-content.md:13-15` and `specs/_product/release-next.md` Deferred Epics.
- **Auto-publish to X / blog.** Rejected per `specs/plans/deviate-content.md:200` and `specs/_product/flows/flows-content-capture.md:78-79`.
- **Cross-repo aggregation.** Rejected per `specs/plans/deviate-content.md:202` and `specs/_product/release-next.md` Constraint 11.
- **LLM-driven content refinement.** Rejected per `specs/plans/deviate-content.md:201` and `specs/_product/release-next.md` Deferred Epics.
- **Tight `HandoverManifest` schema coupling.** Rejected per Option Matrix row 2 (a).
- **Wrapper skill.** Rejected per `specs/plans/deviate-content.md:16-17` (actor-writes rule).
- **Engagement with `tome-*` skills.** Rejected per `specs/plans/deviate-content.md:204`.
- **Append-only git index for `.deviate/feat/`.** Rejected (gitignored; git log cannot capture YAML state).
- **Hot-reload of format templates via file watcher.** Rejected as over-engineering for v1.

## Design Trade-Offs (Subagent Alpha)

| Decision | Trade-off | Why This Side |
|---|---|---|
| YAML manifest as runtime state vs append-only ledger | Idempotent overwrite-or-skip is simpler but loses audit-trail property. | "YAML files ARE the ledger. ... Re-emittable from skills if lost." (`plans/deviate-content.md:13-15`). Also `architecture.md:213`. Git log is the audit trail. |
| Skill actor writes via Write tool vs runner writes from stdout | Actor-authored YAMLs carry richer narrative anchors but create error class where actor forgets the Write call. | "Skill actor writes; runner stays minimal" (`plans/deviate-content.md:16-17`). `HandoverArtifactMissing` is raised with canonical path. |
| Static template prompts vs LLM-rendered drafts | Templates are deterministic and testable but cannot flex; LLM-rendered drafts require snapshot tests + new model tier. | "LLM-driven content refinement — template-based v1; `--refine` flag possible later" (`plans/deviate-content.md:201`). |
| 15 one-sentence skill edits vs wrapper skill vs CLI flag | 15 small edits have low per-edit risk but cross-cut prompt surface; wrapper centralizes but inverts contract; CLI flag keeps prompts clean but loses anchor richness. | "The 15 modified skill prompts... each receive a one-sentence Write instruction" (`architecture.md:281-283`). |
| Separate read-side `HandoverRecord` vs extending `HandoverManifest` | Extending keeps single schema source-of-truth but couples two contracts. | `HandoverRecord` is read-side-only per `plans/deviate-content.md:92` and `domain-model.md` HandoverRecord. Existing `HandoverManifest` at `core/agent.py:21` uses `extra="allow"` for forward-compat. |
| Phase-specific typed anchor fields vs free-form dict | Per-phase typed fields let synthesis reference known anchor names reliably but require 12-phase × 2-3 schema; free-form degrades `test_blog_format` quality gate. | "Synthesis uses anchors as raw material; absence is non-fatal — synthesis falls back to `phase` + `status` + `files` + git-log metadata" (`plans/deviate-content.md:68-69`). |
| Path hierarchy inherited from FLOW-02 vs new top-level roots | Reusing `.deviate/feat/...` keeps governance centralized but constrains future epics to amend `architecture.md` first. | "FLOW-02 (Architecture) governs the path-convention decisions this flow inherits" (`flows-content-capture.md:31`). |
| C8 as pure-Python helper vs LLM-invoked skill | Python helper is deterministic but cannot author narrative anchors; LLM skill composes at write-time but adds model invocation. | "C8 — Handover Capture (Runner) — (none — internal helper)" (`architecture.md:43`). Narrative authoring is the skill actor's job. |
| `.deviate/.gitignore` extension vs root `.gitignore` | Per-directory `/feat/` matches existing local convention; root-level would leak rule into target repos. | `plans/deviate-content.md:83-86` and `release-next.md` Acceptance Criterion 14. |
| Synthesis as Typer sub-app vs slash-command-only | Typer sub-app is deterministic and CI-runnable (bats E2E possible); slash-command-only couples to agent platform. | "CLI sub-app `src/deviate/cli/content.py` exposes `deviate content ...`" (`release-next.md` Acceptance Criterion 6). |

## Contrarian Viewpoints (Subagent Gamma)

- **CV-1**: "YAML files ARE the ledger" is a single point of failure. Re-emit produces a *different* YAML on each invocation; no SHA-256 content-hash; corruption undetectable. Counter-design: thin `handover-checksums.jsonl` or re-introduce `specs/narrative.jsonl` as one-line pointer index.
- **CV-2**: 15-skill cross-cutting Write instruction is inconsistent by construction. Plan does not specify manual-path vs CLI-path per skill. Counter-design: spell out per-layer instructions; eliminate the constitutional violation simultaneously.
- **CV-3**: Idempotent overwrite on path collision hides divergent re-runs. "Git log diff catches divergence" claim is wrong because YAMLs are gitignored. Counter-design: content-hash check in `load_handover_records()`.
- **CV-4**: Single-repo v1 means the cross-repo user has zero path forward. Plan rejects cross-repo but provides no migration path. Counter-design: insert `<repo_slug>` into path convention now.
- **CV-5**: No commit + no JSONL means "what did the agent decide on date X?" is unanswerable. Counter-design: maintain thin `narrative-index.jsonl` with pointer + SHA-256.
- **CV-6**: Path convention is governed by FLOW-02 but FLOW-02 is the very document being audited. Counter-design: add §10 "Path Convention Authority" to `architecture.md`.
- **CV-7**: Anchor field name phase-specific map will drift the moment a new phase is added. Counter-design: codify `ANCHOR_FIELDS_BY_PHASE` dict in `src/deviate/core/handover.py`.

## Risk Register (Subagent Gamma)

| Risk ID | Risk | Likelihood | Impact | Mitigation | Owner | Source Anchor |
|---|---|---|---|---|---|---|
| R-01 | Tamper Guard rollback during micro-skill execution (Constitutional Violation above) | High | High | Resolve CV-2 before GREEN: option (a) constitution amendment, (b) plan revision, (c) runtime mechanism | Task 1 implementer | `plans/deviate-content.md:65` + `constitution.md:25` |
| R-02 | Disk corruption destroys handovers mid-epic | Medium | High | Add SHA-256 checksums in thin index or commit YAMLs | Content Capture maintainer | `plans/deviate-content.md:13-15` |
| R-03 | LLM actor forgets Write call (manual path only; CLI path loses manifest if stdout empty) | Medium | Medium | Mandatory stdout `<handover_emit>` block; `deviate handover doctor` subcommand | Skill author per 15 skills | `plans/deviate-content.md:160-161` |
| R-04 | LLM actor writes malformed YAML | Medium | Low | `validate_artifact()` from `core/validation.py:51` in `load_handover_records()` | core/handover.py author | `plans/deviate-content.md:162` |
| R-05 | LLM actor writes to wrong path (post-handler retries indefinitely) | Medium | Medium | Provide path via `handover_path()` return injected into prompt | core/handover.py + skill author | `plans/deviate-content.md:163` |
| R-06 | Path traversal via epic_slug/issue_id | Low | High | Strict slug regex `^[a-z0-9][a-z0-9-]{0,62}$`; adversarial test `test_path_traversal_rejected` | core/handover.py author | `plans/deviate-content.md:163-164` |
| R-07 | Cross-repo aggregation impossible in v1 | High | Medium | Insert `<repo_slug>` into path convention now (CV-4) | Content Capture maintainer | `plans/deviate-content.md:201` |
| R-08 | Path collisions between phases within a task (re-run after rollback) | Medium | Medium | Add `created_at` to YAML body; `load_handover_records()` keeps latest | core/handover.py author | `plans/deviate-content.md:166` |
| R-09 | Anchor field name drift across prompts | High | High | Codify as Pydantic dict in core/handover.py (CV-7) | core/handover.py author | `plans/deviate-content.md:52-67` |
| R-10 | Synthesis drift between two repos that copy YAMLs | Medium | Medium | Add SHA-256 to YAML body and check on `load_handover_records()` | core/handover.py author | `plans/deviate-content.md:17-19` |
| R-11 | Coverage drops below 80% after Content Capture | Medium | Medium | Run `mise run check --cov` before GREEN; add coverage assertion to CI | Task 1 + Task 2 implementer | `constitution.md:43-48` |
| R-12 | HITL Gate 3 doesn't review synthesis drafts (PII/secrets land in `.deviate/content-drafts/`) | Low | Medium | `validate_artifact()` secrets-detected rule; block `--archive` if secrets found | core/handover.py + cli/content.py author | `constitution.md:51-52` + `architecture.md:222` |
| R-13 | `specs/_archives/<epic>-narrative.tar.gz` is committed-by-default — secrets into git history forever | Medium | High | Require `--archive --force`; `deviate content redact --epic <X>` dry-run preview | cli/content.py author | `plans/deviate-content.md:48` + `constitution.md` Git Isolation |
| R-14 | No machine-parseable handoff between C8 and C9; YAML schema drift invisible | Medium | High | JSON Schema at `specs/_product/schemas/handover.schema.json` + validate in `load_handover_records()` | core/handover.py author | `architecture.md:174-176` |
| R-15 | 15 modified skill prompts each add instruction to `<output_format_schemas>` — single point of maintenance | High | Medium | Move YAML terminal contract to shared prompt-fragment file referenced by all 15 skills | Skill authors for all 15 | `plans/deviate-content.md:79-87` |
| R-16 | FLOW-02 circular authority | Low (current), persistent | Medium | Add §10 "Path Convention Authority" to architecture.md (CV-6) | architecture.md author | `architecture.md:280` |
| R-17 | Template drift between C9 and C10 (placeholder `{{ records }}` literal if record structure changes) | Medium | High | Jinja2 with `StrictUndefined` so missing variables raise (R-17 dependency note: pyproject.toml does not declare jinja2 — `explore.md:48-50` flags; resolve before GREEN) | core/synthesis.py author | `architecture.md:239` + `explore.md:48-50` |

## Constitutional Alignment Audit (Subagent Gamma)

| Constitutional Clause | Architectural Decision | Alignment | Notes |
|---|---|---|---|
| §1 Three-Layer Architecture | Content Capture adds a post-handler step to every phase; C9 is a new macro-layer skill | **Aligned** | No new layer; no gate skipped. |
| §1 Append-Only Ledger Protocol | YAMLs are "idempotent overwrite-or-skip, not append"; explicitly NOT a ledger | **Tension** | Constitution scopes protocol to `issues.jsonl`/`tasks.jsonl`. Architecture §8.1 acknowledges "satisfied with note." Trade-off documented but has real consequences (CV-1, CV-5, R-02). |
| §1 Git Isolation Principle | `.deviate/feat/**` gitignored; no commits for handover YAMLs | **Aligned** | Gitignored runtime writes are consistent with the principle. |
| §1 Tamper Guard & Micro-Sandboxing | Manual path requires micro-layer actor to Write to `.deviate/feat/**/*.yaml` (NOT `src/**/*.py`) | **VIOLATION** | See Constitutional Violation block at top of this document. |
| §1 HITL Gates | No new gate; synthesis output is human-reviewed; auto-publish out of scope v1 | **Aligned** | Gate 3 covers committed artifact (`specs/_archives/<epic>-narrative.tar.gz`); R-12 secondary concern. |
| §1 Session Continuity | No new LLM invocations; same session continues through handover emission | **Aligned** | YAML emitted at phase boundaries by same session. |
| §1 Model Tiering | Synthesis is template-based (no LLM invocation); C8 is pure Python | **Aligned** | No new model routing decisions. |
| §1 Config-Driven Model Routing | No new phase added to routing table | **Aligned** | 15 modified skills use existing model assignments. |
| §3 Coverage target ≥80% | 9 new tests; existing coverage unknown post-additions | **Tension** | R-11 — `mise run check --cov` before GREEN. |
| §3 RED must fail with `AssertionError`/`NotImplementedError` | Task 1 RED tests assert file presence, valid YAML, gitignore status | **Aligned** | Acceptance criteria testable. |
| §3 GREEN; Tamper Guard resets unauthorized test edits | GREEN edits skill prompts (`src/deviate/prompts/skills/...`); are prompts "configuration files"? | **Tension** | Tamper Guard's read-only list is ambiguous about prompt files; recommend explicit clarification before GREEN. |
| §3 REFACTOR regression gate | REFACTOR extracts path constant, centralizes macro/micro detection, reuses `_git_env()` | **Aligned** | Regression gate re-runs the same 4+5 tests. |
| §4 Branch Strategy | Content Capture derives from epic per `architecture.md` §9 | **Aligned** | Branch strategy applies; synthesis on existing epic branch. |
| §4 Commit Convention | Plan produces commits per phase boundary | **Aligned** | Standard. |
| §5 Definition of Done | Plan doesn't address Judge phase execution | **Tension** | Definition of Done requires Judge pass; Plan § Task decomposition lists only 2 tasks (Capture + Synthesis). Either add Task 3 (Judge) or declare Judge-exempt with rationale. |

**Summary**: 1 Violation, 4 Tensions, 10 Aligned clauses.

## Pending HITL Decisions

<!-- HITL_DECISIONS -->
<!-- The pre-existing design decisions are zero because the workflow HALTED at the Constitutional Violation before the standard HITL table could be populated. The single open decision is which resolution option (a), (b), or (c) the human operator selects. -->

| Decision ID | Question | Context | Impact | Recommended Resolution | Status |
|---|---|---|---|---|---|
| `HITL-001` | Which resolution option (a/b/c) should be applied to the Tamper Guard & Micro-Sandboxing Violation? | Subagent Gamma's audit found that the "Manual path" persistence mode for the 9 micro-layer skills violates `specs/constitution.md` §1 Tamper Guard. Three resolutions exist: (a) constitution amendment, (b) plan revision, (c) runtime mechanism. | If unresolved, GREEN phase will trigger immediate Tamper Guard rollback on first micro-skill execution; entire Content Capture epic derails. | Option (a) — Constitution Amendment: explicit exception added to `specs/constitution.md` v0.3.0 §1 Tamper Guard for `.deviate/feat/**/*.yaml` and `.deviate/content-drafts/**/*.md` (Content Capture gitignored runtime state). | `RESOLVED` |

**Gate Rule**: The `deviate prd pre` command will halt on any row with Status `PENDING`. `HITL-001` is now `RESOLVED`. No further decisions block PRD generation; the operator may invoke `/deviate-prd` directly.

## Field-Level Gaps Surfaced (Subagent Beta — for Resolution after Violation)

1. **`created_at` semantics on `PhaseHandover`** — actor-emitted vs runner-stamped. Recommendation: runner-stamped.
2. **`HandoverRecord.source_path` / `.mtime`** — listed as "derived" because `domain-model.md` does not formally declare them; required by Task 2 RED test #1 chronological-order assertion.
3. **`EpicWindow.issue_id` cross-field validator** — derived from path nesting (issue ⇒ epic). Not stated explicitly.
4. **`ContentDraft.byte_count` source** — `domain-model.md` lists it; recommendation: post-write `Path.stat().st_size`.
5. **`NarrativeAnchor` extra-field handling** — corpus treats anchor fields as closed 12-phase map but does not forbid additional keys. Make explicit (`extra="allow"` precedent at `core/agent.py:32`).
6. **`FormatTemplate.placeholders` ordering and required-vs-optional** — `architecture.md:196-198` lists four placeholders as a set; not specified which required. Recommendation: all four required; `records` defaults to `[]`.
7. **YAML serialization style** — corpus does not mandate `yaml.safe_dump(..., sort_keys=False)` vs default. Recommendation: `sort_keys=False`.
8. **`ContentArchive.handover_count` vs `tarball_size` reconciliation** — both listed; no corpus text states what consistency check is required at write time.

## Source Registry

| ID | Type | Source / Path (Strictly Relative to Repo Root) | Relevance Note |
|---|---|---|---|
| SRC-01 | Explore_MD | `specs/explore/deviate-content.md` | Authoritative empirical input; FILE_REGISTRY + Architectural Baselines. |
| SRC-02 | Constitution | `specs/constitution.md` (v0.2.0) | Authoritative governance; §1 Tamper Guard clause cited in violation. |
| SRC-03 | Plan | `specs/plans/deviate-content.md` | User-supplied scope; Persistence flow lines 64-73 cited in violation. |
| SRC-04 | Product_Architecture | `specs/_product/architecture.md` (319 lines) | C8/C9/C10 components, §3.5-§3.7, §4.4-§4.6, §6.1 dependency graph, §8.1 cross-check. |
| SRC-05 | Product_Flow | `specs/_product/flows/flows-content-capture.md` | FLOW-11 and FLOW-12 full schema. |
| SRC-06 | Product_Flow | `specs/_product/flows/index.md` | Canonical flow catalog; FLOW-11 and FLOW-12 verified present. |
| SRC-07 | Product_DomainModel | `specs/_product/domain-model.md` | 10 Content Capture entities pre-specified. |
| SRC-08 | Product_Release | `specs/_product/release-next.md` | 12 constraints + 15 acceptance criteria. |
| SRC-09 | Codebase_File | `src/deviate/core/agent.py:21-32` | `HandoverManifest` with `extra="allow"`; forward-compatible precedent. |
| SRC-10 | Codebase_File | `src/deviate/core/tamper.py` | Implementation of Tamper Guard; `_is_config_file` treats `.deviate/**` as protected during GREEN/YELLOW. |
| SRC-11 | Codebase_File | `src/deviate/cli/macro.py:195-275` | Pre/post Typer sub-app pattern. |
| SRC-12 | Codebase_File | `src/deviate/cli/__init__.py:594-619` | 23 sub-apps registered; `cli.add_typer(...)` pattern. |
| SRC-13 | Codebase_File | `tests/conftest.py` | `_git_env()` and `tmp_git_repo` fixture for git isolation. |
| SRC-14 | Manifest | `pyproject.toml` | `requires-python = ">=3.13"`; `pydantic>=2.0`, `pyyaml>=6.0.3`, `typer>=0.12`, `rich>=13.0` already declared; jinja2 NOT declared. |
| SRC-15 | Config | `.deviate/.gitignore` | Currently excludes `session.json`, `artifacts/`, `prompts.log`, `reports/`, `rollback.jsonl`, `logs/`; needs `/feat/` and `/content-drafts/` extension. |

## Status Summary

| Metric | Value |
|---|---|
| STATUS | CONSTITUTIONAL_VIOLATION_RESOLVED |
| FEATURE_SLUG | 005-deviate-content |
| EPIC_ID | 005-deviate-content |
| GIT_BRANCH | main |
| SPEC_TARGET_DESIGN | specs/005-deviate-content/design.md (this file) |
| SPEC_TARGET_DATAMODEL | NOT WRITTEN (workflow halted at violation; Alpha/Beta fragments preserved in this design.md for human review) |
| CONSTITUTION_VERSION | 0.3.0 (Tamper Guard exception applied) |
| NEXT_ACTION | Operator invokes `/deviate-prd` manually per `specs/_product/release-next.md` constraints. `deviate research post` is NOT invoked per skill invariant. |
