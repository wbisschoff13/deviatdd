from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


@contextmanager
def chdir(path: Path):
    cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


class TestSkillInstallation:
    """T007: Wire agent detection, skill installation, and contract handoff into deviate init."""

    def test_init_installs_skills_to_agent_dirs(self, tmp_path: Path):
        """US-005-SKILLS Scenario 2: SKILL.md copied to detected agent paths."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".opencode").mkdir()
        with chdir(tmp_path):
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "INSTALL" in result.output.upper()

    def test_skill_idempotency_skip_identical(self, tmp_path: Path):
        """US-005-SKILLS Scenario 3: skip when content hash matches."""
        claude_skills = Path.home() / ".claude" / "skills"
        claude_skills.mkdir(parents=True, exist_ok=True)
        src = (
            Path(__file__).resolve().parent.parent.parent
            / "src"
            / "deviate"
            / "prompts"
            / "skills"
        )
        for skill_dir in src.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                target = claude_skills / skill_dir.name / "SKILL.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
        (tmp_path / ".claude").mkdir(exist_ok=True)
        with chdir(tmp_path):
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "SKIP" in result.output

    def test_skill_idempotency_overwrite_stale(self, tmp_path: Path):
        """US-005-SKILLS Scenario 4: overwrite when content differs."""
        claude_skills = Path.home() / ".claude" / "skills"
        claude_skills.mkdir(parents=True, exist_ok=True)
        target = claude_skills / "deviate-specify" / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("STALE CONTENT", encoding="utf-8")
        (tmp_path / ".claude").mkdir(exist_ok=True)
        with chdir(tmp_path):
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            content = target.read_text(encoding="utf-8")
            assert "STALE CONTENT" not in content

    def test_auto_detect_agents_from_cwd(self, tmp_path: Path):
        """US-006-INIT Scenario 1: auto-detect agents from cwd directories."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".opencode").mkdir()
        (tmp_path / ".factory").mkdir()
        from deviate.core import skills as skills_module

        with chdir(tmp_path):
            agents = skills_module.detect_agents()
            assert "opencode" in agents
            assert "claude" in agents
            assert "factory" in agents

    def test_agent_flag_overrides_detection(self, tmp_path: Path):
        """US-006-INIT Scenario 2: --agent flag overrides auto-detection."""
        (tmp_path / ".claude").mkdir()
        with chdir(tmp_path):
            result = runner.invoke(cli, ["init", "--agent", "opencode"])
            assert result.exit_code == 0

    def test_contract_handoff_defaults_to_session_json(self, tmp_path: Path):
        """US-006-INIT Scenario 4: contract handoff defaults to .deviate/session.json."""
        with chdir(tmp_path):
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert (tmp_path / ".deviate" / "session.json").exists()
            gitignore = tmp_path / ".gitignore"
            assert gitignore.exists()
            content = gitignore.read_text(encoding="utf-8")
            assert ".deviate/session.json" in content
