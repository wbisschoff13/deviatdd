## FLOW-11 Capture Phase Handover

- Actor: DeviaTDD
- Domain: Content Capture
- Status: Draft

### Problem / job to be done
- Convert ephemeral phase output (LLM stdout, skill artifacts, git log) into a durable, queryable YAML handover at the end of every DeviaTDD phase, so downstream synthesis has raw material to turn into blog posts, X threads, release notes, and resume bullets later.

### Trigger
- End of any DeviaTDD phase (pre or post) — the runner's `persist_handover()` helper fires automatically from the phase post-handler.
- Source: `specs/plans/deviate-content.md` § Persistence flow — "actor → YAML on stdout + Write tool → .deviate/feat/<epic>/<issue>/<phase>.yaml" and "actor → YAML on stdout → AgentBackend parses → post command writes file".

### Preconditions
- An active epic/issue/task chain is in scope (a phase is part of an existing chain).
- The phase belongs to the canonical 12-phase set (`explore`, `research`, `prd`, `shard`, `plan`, `tasks`, `red`, `green`, `yellow`, `judge`, `refactor`, `e2e`) — see `specs/plans/deviate-content.md` § Narrative anchor field.
- The skill actor MAY or MAY NOT include a `narrative_anchor:` block; absence is non-fatal (backward-compatible).
- `.deviate/.gitignore` excludes `/feat/` and `/content-drafts/`.

### Happy path (primary steps)
1. A DeviaTDD phase (e.g. `judge`) completes and its post-handler runs.
2. The skill actor emits a YAML manifest — either via the Write tool to the canonical path (manual path) or via stdout (CLI path).
3. The runner calls `persist_handover()` from `src/deviate/core/handover.py`, which writes to `.deviate/feat/<epic_slug>/<issue_id>/[<task_id>/]<phase>.yaml`.
4. The YAML contains at minimum `phase`, `status`, `files`, and (optionally) a `narrative_anchor:` block whose field names are phase-specific per `specs/plans/deviate-content.md` § Narrative anchor field.
5. The file lands on disk; no git commit, no ledger append — runtime state only.
6. The handover is now available as raw material for `FLOW-12` synthesis.

### Alternate / error paths
- LLM actor forgets the Write call on the manual path → `HandoverArtifactMissing` raised with the canonical path so the actor knows exactly what to write; CLI path never raises this (runner writes from captured stdout).
- LLM actor writes malformed YAML → `yaml.safe_load` in `load_handover_records()` skips with a warning; synthesis degrades gracefully.
- LLM actor writes to a wrong path on the CLI path → post-handler validates path matches the expected `feat/<epic>/<issue>/[<task>/]<phase>.yaml` pattern and rejects with a clear diagnostic.
- Path traversal attempt → `pathlib` everywhere; any path escaping `.deviate/feat/` is rejected (see `specs/plans/deviate-content.md` § Risks).
- Actor re-runs with identical content → idempotent write test catches this; divergent content is a real failure surfaced by `git log` diff (not by the YAML layer).

### Success State
- `.deviate/feat/<epic_slug>/<issue_id>/[<task_id>/]<phase>.yaml` exists, is valid YAML, is gitignored, and is not staged in the git index.
- `narrative_anchor` fields are preserved verbatim if present.
- No commit, no ledger append — runtime state only.

### Metrics / Signals
- Number of handover YAMLs per epic tracks the number of phases run; gaps are visible to a human reviewer.
- `narrative_anchor` field presence rate per phase becomes a quality signal for downstream synthesis.
- Cross-reference: `FLOW-12` reads every handover YAML as its primary input.
- Cross-reference: `FLOW-02` (Architecture) governs the path-convention decisions this flow inherits (`.deviate/feat/...` and `.deviate/content-drafts/...`).

## FLOW-12 Synthesize Content Digest

- Actor: Developer
- Domain: Content Capture
- Status: Draft

### Problem / job to be done
- Aggregate every phase-handover YAML for a chosen window (epic, issue, or all) and render a digestable draft in a chosen format (blog, X thread, release notes, commit story, resume bullet) so I can publish marketing content for Deviate / Scribe / Tome / DeviaTDD without re-reading raw phase output.

### Trigger
- Developer runs the `deviate content` CLI subcommand, e.g. `deviate content --format blog --window EPIC-X --slug my-post` or `deviate content pre` / `post` per `src/deviate/cli/content.py`.
- Optional flags: `--format`, `--window`, `--slug`, `--archive` (see `specs/plans/deviate-content.md` § New files).
- Equivalent slash command `/deviate-content` in the developer's agent of choice.

### Preconditions
- At least one handover YAML exists under `.deviate/feat/**/*.yaml` for the chosen window (or globally if no `--window` is set).
- The 5 format templates exist at `src/deviate/prompts/content/{blog,x-thread,release-notes,commit-story,resume-bullet}.md`.
- `narrative_anchor:` blocks MAY be absent on some YAMLs; synthesis falls back to `phase` + `status` + `files` + `git log` metadata.

### Happy path (primary steps)
1. Developer runs `deviate content --format <blog|x-thread|release-notes|commit-story|resume-bullet> [--window EPIC-X] [--slug S]`.
2. CLI calls `load_handover_records()` from `src/deviate/core/handover.py` to gather all matching YAMLs in chronological order.
3. For each record, the synthesis layer extracts the `narrative_anchor` (if present) keyed by the phase-specific field names from `specs/plans/deviate-content.md` § Narrative anchor field.
4. The chosen format template renders the digest — e.g. blog intro references the `judge.verdict_story` anchor; X thread is sliced into 6 posts from the same anchors.
5. Draft lands at `.deviate/content-drafts/<format>/<slug>.md` (gitignored, not committed).
6. Developer reviews, edits, and publishes manually (auto-publish is explicitly out of scope v1).
7. Optional: `--archive EPIC-X` tars the YAMLs into `specs/_archives/<epic_slug>-narrative.tar.gz` — the only committed-by-default artifact of the content capture system.

### Alternate / error paths
- No YAMLs under the chosen window → CLI exits non-zero with a diagnostic pointing at the window filter; no draft is written.
- No `narrative_anchor` present on any record → synthesis falls back to `phase` + `status` + `files` + `git log`; draft is structurally valid but less narrative-rich.
- Unknown `--format` value → CLI lists the 5 valid formats and exits non-zero.
- `--archive` invoked but no YAMLs under the epic → tar is not written; CLI exits non-zero.
- Path collision on the draft file → CLI refuses to overwrite without an explicit `--force` flag (default: refuse and suggest `--slug`).

### Success State
- A draft exists at `.deviate/content-drafts/<format>/<slug>.md` and is gitignored.
- The draft's opening paragraph references at least one `narrative_anchor` from the chosen window (when anchors are present) — verifiable by the `test_blog_format` and `test_x_thread_format` acceptance tests in `specs/plans/deviate-content.md` § Task 2.
- Human publishing is the next step (out of scope for this flow).

### Metrics / Signals
- Number of drafts per epic tracks synthesis frequency; the gap between last handover and first draft indicates synthesis latency.
- `narrative_anchor` presence rate at synthesis time feeds back to FLOW-11's quality signal — low rates trigger a reminder to update skill actor prompts.
- Cross-reference: `FLOW-11` is the sole producer of this flow's input data.
- Cross-reference: `FLOW-03` (Release) treats synthesis drafts as evidence of release-grade work — release notes drafts are one of the five supported formats.
- Cross-reference: `FLOW-10` (Tome Setup) is unrelated to v1 but the docs site could host published drafts in a future integration.
