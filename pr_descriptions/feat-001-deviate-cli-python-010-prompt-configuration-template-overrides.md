Prompt templates were locked inside the installed package tree — invisible, non-obvious, and overwritten on every upgrade. This change bootstraps user-editable prompt overrides in `.deviate/prompts/`, establishes an override-first resolution chain with package default fallback, replaces the nested skill installation system with flat command files, and adds `--refresh-prompts` for safe reset with optional backup.

- Prompt resolution: `resolve_prompt()`, `resolve_command()`, and `interpolate()` with override-first resolution, silent fallback, and `${PLACEHOLDER}` variable interpolation
- Template migration: Replaced nested `src/deviate/prompts/skills/` (18 SKILL.md directories) with flat `.md` files in `commands/`; created 11 auto-phase prompt templates in `auto/`
- Init scaffolding: `deviate init` now bootstraps `.deviate/prompts/{auto,commands}/` from package defaults, idempotent on re-run, with `--refresh-prompts` flag for overwrite (with optional timestamped backup)
- Command installation: Rewrote `skills.py` to install flat `.md` command files to `.opencode/commands/` instead of nested SKILL.md to `.opencode/skills/`, resolving through the override chain
- E2E coverage: Full integration tests for override resolution, fallback, agent installation, interpolation, and refresh cycles
