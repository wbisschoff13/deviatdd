# FEATURE_SPECIFICATION: specs/001-deviate-cli-python/010-prompt-configuration-template-overrides/spec.md

## SYSTEM_TOPOLOGY_MAPPING

- **Epic Domain**: `001-deviate-cli-python`
- **Epic Slug**: `001-deviate-cli-python`
- **Issue ID**: `ISS-010`
- **Issue Slug**: `010-prompt-configuration-template-overrides`
- **Workstation Paths**:
  - `src/deviate/cli/__init__.py` — `deviate init` extended with prompt scaffolding + `--refresh-prompts` flag
  - `src/deviate/core/prompts.py` — Prompt resolution layer: `resolve_prompt()`, `resolve_skill()`, `interpolate()`, `list_overrides()`, `list_defaults()`
  - `src/deviate/core/skills.py` — Skill installation updated to resolve from `.deviate/prompts/` first
  - `.deviate/prompts/` — User-editable prompt template overrides (created by `deviate init`)
  - `.deviate/prompts/auto/` — Slim automated prompt overrides
  - `.deviate/prompts/skills/` — Manual SKILL.md overrides
  - `src/deviate/prompts/` — Package defaults (read-only reference)
  - `tests/test_core/test_prompts.py`
  - `tests/test_cli/test_init.py` — Extended for prompt scaffolding assertions
  - `tests/test_integration/test_prompt_overrides.py`
- **Upstream Requirement Traceability**: `FR-010` (Prompt Configuration & User-Editable Template Overrides)

## THE_PROBLEM_CONTRACT

Developers customizing the DeviaTDD workflow need user-visible, editable prompt templates in `.deviate/prompts/` that override package defaults. Currently, prompt templates live exclusively inside the installed `src/deviate/prompts/` package tree — invisible, non-obvious, and overwritten on every package upgrade. This forces developers to either fork the package or accept opaque behavior.

The feature must:
1. Bootstrap `.deviate/prompts/auto/` and `.deviate/prompts/skills/` on `deviate init` by copying from package defaults.
2. Never overwrite user customizations unless `--refresh-prompts --force` is explicitly passed.
3. Provide a resolution chain: `.deviate/prompts/` override → package default fallback.
4. Support `${PLACEHOLDER}` variable interpolation with per-phase re-resolution of static variables.
5. Propagate user overrides to agent skill directories on next `deviate init`.
6. Integrate with automated pipelines so prompt edits take effect immediately.

## SCOPE_BOUNDARIES

### Hard Inclusions

1. **Prompt scaffolding in `deviate init`**:
   - Creates `.deviate/prompts/auto/` with all slim automated templates copied from `src/deviate/prompts/auto/`
   - Creates `.deviate/prompts/skills/` with all manual SKILL.md templates copied from `src/deviate/prompts/skills/`
   - Idempotent: skips if `.deviate/prompts/` already exists, with console message
   - `--refresh-prompts` flag: prompts user `"Back up existing overrides? [y/N]"` before overwriting
   - Requires `--force` to proceed with overwrite after backup prompt

2. **Prompt resolution layer** (`src/deviate/core/prompts.py`):
   - `resolve_prompt(name: str) -> str` — resolves template via `.deviate/prompts/auto/` override → `src/deviate/prompts/auto/` package default fallback
   - `resolve_skill(name: str) -> str` — resolves SKILL.md via `.deviate/prompts/skills/` override → `src/deviate/prompts/skills/` package default fallback
   - Missing override files: silent fallback to package default (no warning)
   - `interpolate(template: str, variables: dict) -> str` — resolves `${PLACEHOLDER}` variables
   - `list_overrides() -> list[str]` — enumerates templates that currently have user overrides
   - `list_defaults() -> list[str]` — enumerates templates currently on package defaults
   - Static variables (`${CONSTITUTION}`, `${CLAUDE_MD}`, `${REPO_ROOT}`): re-resolved per phase (no explicit cache; relies on model-based caching optimization via constitution placement after prompt, before dynamic variables)

3. **Skill installation integration** (`src/deviate/core/skills.py`):
   - `install_skill()` updated to call `resolve_skill()` instead of reading directly from `src/deviate/prompts/skills/`
   - User edits to `.deviate/prompts/skills/` propagate to agent directories on next `deviate init`

4. **Automated pipeline integration**:
   - All slim prompt builds call `resolve_prompt("auto/<phase>.md")` instead of reading from `src/deviate/prompts/auto/` directly
   - User edits to `.deviate/prompts/auto/` take effect immediately in next phase execution

5. **CLI updates** (`src/deviate/cli/__init__.py`):
   - `--refresh-prompts` flag added to `deviate init`
   - Prompt scaffolding step added to init sequence (after dotfiles, before skill installation)
   - Console output reflecting prompt bootstrapping status

### Defensive Exclusions

- Template validation beyond basic file-existence checks (syntax validation deferred to runtime)
- Web-based prompt editor or GUI
- Per-phase prompt diffing or merge conflict resolution — `--refresh-prompts` is a blunt overwrite
- Template versioning or migration — user is responsible for reconciling overrides with upstream template changes
- Dynamic prompt generation from database or API sources
- Symlink or broken-reference detection in `.deviate/prompts/` (unreadable files fall through to package defaults)

## PERFORMANCE_CONSTRAINTS

- `resolve_prompt()` and `resolve_skill()` must complete in L_max <= 10ms per call (single file stat + conditional read)
- `interpolate()` must complete in L_max <= 50ms for a 10-variable template
- `list_overrides()` / `list_defaults()` must complete in L_max <= 50ms (directory walk + existence check)
- Prompt scaffolding in `deviate init` must complete in L_max <= 500ms for ~30 templates
- `--refresh-prompts` must complete in L_max <= 1s including optional backup tar

## MULTI_TIERED_VERIFICATION_TARGETS

| Tier | Target | Command |
|------|--------|---------|
| Unit | `tests/test_core/test_prompts.py` | `pytest tests/test_core/test_prompts.py -v` |
| Integration | `tests/test_cli/test_init.py` (prompt scaffolding) | `pytest tests/test_cli/test_init.py -v -k prompt` |
| Integration | `tests/test_integration/test_prompt_overrides.py` | `pytest tests/test_integration/test_prompt_overrides.py -v` |
| Lint | Full repo | `ruff check .` |
| Type check | Full repo | `mypy src/deviate/` |

## ATDD_ACCEPTANCE_CRITERIA_LEDGER

### US-010-1: Prompt scaffolding creates override directories on `deviate init`

- **Upstream Requirement Traceability**: FR-010

**Given** a clean project directory with no `.deviate/prompts/` directory
**When** `deviate init` is executed
**Then** `.deviate/prompts/auto/` is created with files matching `src/deviate/prompts/auto/`
**And** `.deviate/prompts/skills/` is created with directories matching `src/deviate/prompts/skills/`
**And** each file in `.deviate/prompts/auto/` has identical content to the corresponding package default
**And** each SKILL.md in `.deviate/prompts/skills/` has identical content to the corresponding package default

### US-010-2: Idempotent init skips existing `.deviate/prompts/`

- **Upstream Requirement Traceability**: FR-010

**Given** a project where `.deviate/prompts/` exists and contains user-modified files
**When** `deviate init` is executed (without `--refresh-prompts`)
**Then** no files in `.deviate/prompts/` are modified
**And** a console message is printed: `"prompts/ already exists, skipping (use --refresh-prompts to reset)"`

### US-010-3: Prompt resolution checks override before package default

- **Upstream Requirement Traceability**: FR-010

**Given** `.deviate/prompts/auto/red.md` exists with content `"CUSTOM RED"`
**And** `src/deviate/prompts/auto/red.md` exists with content `"DEFAULT RED"`
**When** `resolve_prompt("auto/red.md")` is called
**Then** the return value is `"CUSTOM RED"`

### US-010-4: Prompt resolution falls back silently for missing overrides

- **Upstream Requirement Traceability**: FR-010

**Given** `.deviate/prompts/auto/` exists but does not contain `red.md`
**And** `src/deviate/prompts/auto/red.md` exists with content `"DEFAULT RED"`
**When** `resolve_prompt("auto/red.md")` is called
**Then** the return value is `"DEFAULT RED"`
**And** no warning or error is emitted

### US-010-5: Placeholder interpolation resolves dynamic variables

- **Upstream Requirement Traceability**: FR-010

**Given** a template string `"Task: ${TASK_DESCRIPTION} (ID: ${TASK_ID})"`
**When** `interpolate()` is called with `variables={"TASK_DESCRIPTION": "Write tests", "TASK_ID": "T001"}`
**Then** the return value is `"Task: Write tests (ID: T001)"`
**And** static variables (`${CONSTITUTION}`, `${CLAUDE_MD}`, `${REPO_ROOT}`) are resolved from current filesystem state

### US-010-6: `--refresh-prompts` prompts for backup before overwrite

- **Upstream Requirement Traceability**: FR-010

**Given** `.deviate/prompts/` exists with user-modified files
**When** `deviate init --refresh-prompts` is executed
**Then** the user is prompted with `"Back up existing overrides? [y/N]"`
**When** the user responds `"y"`
**Then** a backup of `.deviate/prompts/` is created at `.deviate/prompts.bak/<timestamp>/`
**And** `.deviate/prompts/` is overwritten with fresh copies from package defaults
**When** the user responds `"N"` (or defaults)
**Then** `.deviate/prompts/` is overwritten directly without backup
**And** `--force` is not required for the overwrite itself (the backup prompt is the safeguard)

### US-010-7: Skill installation resolves from override chain

- **Upstream Requirement Traceability**: FR-010

**Given** `.deviate/prompts/skills/deviate-red/SKILL.md` exists with content `"CUSTOM SKILL"`
**And** `install_skill("deviate-red", target_dir)` is called
**When** the skill content is written to `target_dir/deviate-red/SKILL.md`
**Then** the written content is `"CUSTOM SKILL"` (not the package default)

### US-010-8: Automated pipeline resolves slim prompts from override chain

- **Upstream Requirement Traceability**: FR-010

**Given** `.deviate/prompts/auto/red.md` contains `"OVERRIDE"` 
**And** the automated pipeline builds a prompt for the RED phase
**When** `resolve_prompt("auto/red.md")` is called by the pipeline
**Then** the returned content is `"OVERRIDE"`

### US-010-9: `list_overrides()` returns only user-customized templates

- **Upstream Requirement Traceability**: FR-010

**Given** `.deviate/prompts/auto/red.md` exists with content different from the package default
**And** `.deviate/prompts/auto/green.md` does not exist
**When** `list_overrides()` is called
**Then** the return value includes `"auto/red.md"`
**And** the return value does not include `"auto/green.md"`

## SYSTEM_STATUS_SUMMARY

| Parameter | Value |
|-----------|-------|
| STATUS | SPECIFIED |
| EPIC_SLUG | 001-deviate-cli-python |
| BRANCH_NAME | feat/001-deviate-cli-python/010-prompt-configuration-template-overrides |
| SPEC_PATH | specs/001-deviate-cli-python/010-prompt-configuration-template-overrides/spec.md |
| ISSUE_ID | ISS-010 |
| NEXT_ACTION | Run `deviate tasks` to decompose spec.md into TDD task units |
