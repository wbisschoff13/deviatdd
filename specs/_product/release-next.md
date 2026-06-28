# Release: Content Capture Subsystem

## Goal
- Ship the Content Capture subsystem that captures every DeviaTDD phase as a durable YAML handover (`FLOW-11`) and synthesizes those handovers into marketing-content drafts in one of five formats (`FLOW-12`), so the agent lineage (Deviate, Scribe, Tome, DeviaTDD) can publish blog posts, X threads, release notes, commit stories, and resume bullets without re-reading raw phase output.
- v1 adds one Python module (`src/deviate/core/handover.py`), one Typer sub-app (`src/deviate/cli/content.py`), one new macro-layer skill (`deviate-content`), five format templates under `src/deviate/prompts/content/`, and a one-sentence Write instruction appended to the terminal contract of fifteen existing skill prompts.

## Constraints
- **YAML files ARE the ledger**. No `specs/narrative.jsonl`, no write-side `HandoverRecord` Pydantic model, no content-hash on write (per `specs/plans/deviate-content.md` lines 13-15). The YAML manifest under `.deviate/content/handovers/` is the durable artifact and is re-emittable from skills if lost.
- **Skill actor writes; runner stays minimal**. The runner's `persist_handover()` helper writes the file only when the actor did not (CLI orchestration path); the post-handler validates and exits (per `specs/plans/deviate-content.md` lines 16-17 and § Persistence flow, lines 64-73).
- **No commit on handover YAMLs**. `.deviate/content/handovers/**` and `.deviate/content/drafts/**` are gitignored runtime state. Git log already captures code/test/spec changes; the YAML is synthesis material, not project source (per `specs/plans/deviate-content.md` lines 17-19).
- **Path convention is governed by `FLOW-02`** (per `specs/_product/architecture.md:213` and `specs/_product/flows/flows-content-capture.md:31`, `:51`). Future epics that need a new `.deviate/` subdirectory root must amend `architecture.md` first.
- **HandoverRecord is read-side only**. Synthesis reads YAMLs via `load_handover_records()`; the runner writes YAMLs via `persist_handover()`. There is no intermediate index, no JSONL, no machine-parseable handoff file (per `specs/plans/deviate-content.md` lines 13-15 and `specs/_product/architecture.md:179`).
- **Anchors are non-fatal**. Absence of a `narrative_anchor:` block on any YAML is non-fatal — synthesis falls back to `phase` + `status` + `files` + git-log metadata (per `specs/plans/deviate-content.md` lines 68-69 and `specs/_product/flows/flows-content-capture.md:56`).
- **Path traversal rejected at the `pathlib` boundary**. Any path that escapes `.deviate/content/handovers/` is rejected by `handover_path()` and `persist_handover()` (per `specs/plans/deviate-content.md` § Risks, lines 162-163).
- **Constitution §1 Append-Only Ledger Protocol — satisfied with note** (per `specs/_product/architecture.md:213`). Content Capture YAMLs are explicitly NOT a ledger; idempotent overwrite-or-skip is the v1 contract.
- **Stack consistency**: `src/deviate/core/handover.py` and `src/deviate/cli/content.py` follow the existing Python 3.13 + Typer stack (per `specs/_product/architecture.md:209`).
- **Cross-cutting surface is bounded**. The 15 modified skill prompts each receive a one-sentence Write instruction in their `<output_format_schemas>` block referencing the canonical `handover_path()` target. No other skill is touched in v1 (per `specs/plans/deviate-content.md` § Modifications, lines 79-87).
- **v1 is single-repo only**. Cross-repo aggregation queries are out of scope (per `specs/plans/deviate-content.md` § Out of scope v1, lines 199-204).
- **No auto-publish**. Synthesis produces drafts only; the developer reviews, edits, and publishes manually (per `specs/plans/deviate-content.md` § Out of scope v1, line 200 and `specs/_product/flows/flows-content-capture.md:78-79`).

## Included Flows
| Flow ID | Name | Notes |
|---|---|---|
| FLOW-11 | Capture Phase Handover | Runner-side helper C8; every DeviaTDD phase post-handler calls `persist_handover()` from `src/deviate/core/handover.py` |
| FLOW-12 | Synthesize Content Digest | CLI sub-app C9 + macro skill `deviate-content` + read-only resource pack C10 under `src/deviate/prompts/content/` |

## Included Work
| Title | Type | Flow Refs | Status |
|---|---|---|---|
| Content Capture Subsystem | ADHOC | [FLOW-11, FLOW-12] | planned |

## Deferred Epics
- `--refine` LLM-driven content refinement flag (per `specs/plans/deviate-content.md` § Out of scope v1, line 201)
- Cross-repo aggregation queries — single-repo only in v1 (per `specs/plans/deviate-content.md` § Out of scope v1, line 202)
- Engagement metrics on published content (per `specs/plans/deviate-content.md` § Out of scope v1, line 203)
- Auto-publish to X / blog — synthesis produces drafts only; human publishes (per `specs/plans/deviate-content.md` § Out of scope v1, line 200)
- `specs/narrative.jsonl` or any other append-only narrative ledger — explicitly rejected (per `specs/plans/deviate-content.md` lines 13-15)
- Write-side persistence Pydantic model for handovers — read-side `HandoverRecord` only in v1 (per `specs/plans/deviate-content.md` line 92)
- Engagement with the existing `tome-*` skills (Diátaxis-quadrant classification of blog content) — orthogonal in v1 (per `specs/plans/deviate-content.md` § Out of scope v1, line 204)
- Per-format sub-skills inside C9 if v1 usage data shows the synthesis template is too large for a single skill prompt

## Acceptance Criteria
- `deviate setup` installs `deviate-content.md` at `.{claude,opencode,factory}/commands/deviate-content.md` (or `.pi/prompts/deviate-content.md` for Pi), and provisions the format-template resource pack at `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md` (per `specs/plans/deviate-content.md` § File changes → New files, lines 90-99 and `specs/_product/architecture.md:38`).
- The Python module `src/deviate/core/handover.py` exposes `handover_path(epic_slug, issue_id, phase, task_id=None) -> Path`, `persist_handover(epic_slug, issue_id, phase, manifest, task_id=None) -> Path`, `load_handover_records(window) -> list[HandoverRecord]`, and a read-side `HandoverRecord` Pydantic model; no write-side persistence model is exported (per `specs/plans/deviate-content.md` § File changes → New files, line 92 and § Persistence flow, lines 64-73).
- `handover_path()` returns `.deviate/content/handovers/<epic_slug>/<issue_id>/<phase>.yaml` for macro handovers and `.deviate/content/handovers/<epic_slug>/<issue_id>/<task_id>/<phase>.yaml` for micro handovers (per `specs/plans/deviate-content.md` § Path convention, lines 44-45).
- `persist_handover()` writes the YAML only when the file is absent; re-invocation with identical content is idempotent and produces no error (per `specs/plans/deviate-content.md` § Task 1, line 116).
- `handover_path()` and `persist_handover()` reject any path that escapes `.deviate/content/handovers/` via `pathlib` and raise a clear diagnostic (per `specs/plans/deviate-content.md` § Risks, lines 162-163).
- The CLI sub-app `src/deviate/cli/content.py` exposes `deviate content --format <blog|x-thread|release-notes|commit-story|resume-bullet> [--window EPIC-X] [--slug S] [--archive]` and `deviate content pre|post` subcommands (per `specs/_product/flows/flows-content-capture.md:43-46` and `specs/plans/deviate-content.md` § File changes → New files, line 94).
- `deviate content --format <unknown>` exits non-zero and lists the five valid formats (per `specs/_product/flows/flows-content-capture.md:58-59`).
- `deviate content --window EPIC-X` filters records to `.deviate/content/handovers/<epic_slug>/**` only; absence of the window flag includes all records in chronological order (per `specs/plans/deviate-content.md` § Task 2, line 145).
- `deviate content --archive EPIC-X` produces `specs/_archives/<epic_slug>-narrative.tar.gz` containing every YAML under that epic; the tar is the only committed-by-default artifact of the Content Capture subsystem (per `specs/plans/deviate-content.md` § Path convention, line 48 and § Task 2, line 146).
- `deviate content --format blog` renders a draft at `.deviate/content/drafts/blog/<slug>.md` whose opening paragraph references at least one `narrative_anchor` from a `judge` record when anchors are present (per `specs/_product/flows/flows-content-capture.md:78` and `specs/plans/deviate-content.md` § Task 2, line 138).
- `deviate content --format x-thread` renders a draft at `.deviate/content/drafts/x-thread/<slug>.md` containing exactly 6 posts sliced from the same anchor pool (per `specs/plans/deviate-content.md` § Task 2, line 140).
- `load_handover_records()` skips malformed YAML with a warning and continues; absence of `narrative_anchor` on any record is non-fatal and synthesis falls back to `phase` + `status` + `files` + git-log metadata (per `specs/_product/flows/flows-content-capture.md:55-56` and `specs/plans/deviate-content.md` lines 68-69).
- Fifteen existing skill prompts — `deviate-red`, `deviate-green`, `deviate-yellow`, `deviate-judge`, `deviate-refactor`, `deviate-execute`, `deviate-e2e`, `deviate-hotfix`, `deviate-prune`, `deviate-review`, `deviate-research`, `deviate-prd`, `deviate-shard`, `deviate-plan`, `deviate-tasks` — each contain a one-sentence Write instruction in their `<output_format_schemas>` block referencing the canonical `handover_path()` target (per `specs/plans/deviate-content.md` § Modifications, lines 79-87).
- `.deviate/.gitignore` excludes `.deviate/content/`; `git ls-files .deviate/content/handovers/` returns no results for any phase that has completed since the gitignore change (per `specs/plans/deviate-content.md` lines 17-19 and § File changes → Modifications, lines 83-87).
- End-to-end smoke: a single DeviaTDD task (RED → GREEN → JUDGE → REFACTOR) produces `.deviate/content/handovers/<epic>/<issue>/<task>/{red,green,judge,refactor}.yaml` with valid YAML, present on disk, and not staged in the git index (per `specs/plans/deviate-content.md` § Verification, line 189).
- The Constitution §1 Append-Only Ledger Protocol note (`specs/_product/architecture.md:213`) is honored: Content Capture YAMLs are explicitly NOT a ledger — runtime state only, idempotent overwrite-or-skip, no append-only guarantee.