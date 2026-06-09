from __future__ import annotations

from pathlib import Path

from deviate.core.skills import detect_agents, install_command


class TestInstallCommand:
    def test_install_command_resolves_from_override(self, tmp_path: Path):
        target_dir = tmp_path / "target"
        repo_path = tmp_path / "repo"
        override_file = (
            repo_path / ".deviate" / "prompts" / "commands" / "deviate-red.md"
        )
        override_file.parent.mkdir(parents=True)
        override_file.write_text("CUSTOM OVERRIDE")

        result = install_command("deviate-red", target_dir, repo_path=repo_path)

        installed = target_dir / "commands" / "deviate-red.md"
        assert installed.read_text() == "CUSTOM OVERRIDE"
        assert result is True

    def test_install_command_falls_back_to_package(self, tmp_path: Path):
        target_dir = tmp_path / "target"
        repo_path = tmp_path / "repo"
        repo_path.mkdir(parents=True)

        result = install_command("deviate-red", target_dir, repo_path=repo_path)

        installed = target_dir / "commands" / "deviate-red.md"
        assert installed.exists()
        assert result is True

    def test_install_command_skip_when_identical(self, tmp_path: Path):
        target_dir = tmp_path / "target"
        repo_path = tmp_path / "repo"
        repo_path.mkdir(parents=True)

        result1 = install_command("deviate-red", target_dir, repo_path=repo_path)
        assert result1 is True

        result2 = install_command("deviate-red", target_dir, repo_path=repo_path)
        assert result2 is False

    def test_install_command_overwrite_when_stale(self, tmp_path: Path):
        target_dir = tmp_path / "target"
        repo_path = tmp_path / "repo"
        repo_path.mkdir(parents=True)
        stale = target_dir / "commands" / "deviate-red.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("STALE CONTENT")

        result = install_command("deviate-red", target_dir, repo_path=repo_path)

        assert result is True
        assert stale.read_text() != "STALE CONTENT"

    def test_install_command_targets_commands_dir(self, tmp_path: Path):
        target_dir = tmp_path / "target"
        repo_path = tmp_path / "repo"
        repo_path.mkdir(parents=True)

        result = install_command("deviate-red", target_dir, repo_path=repo_path)

        commands_file = target_dir / "commands" / "deviate-red.md"
        skills_file = target_dir / "skills" / "deviate-red" / "SKILL.md"
        assert commands_file.exists()
        assert not skills_file.exists()
        assert result is True


class TestDetectAgents:
    def test_detect_agents_still_works(self, tmp_path: Path):
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".opencode").mkdir()
        (tmp_path / ".factory").mkdir()

        result = detect_agents(tmp_path)

        assert result == ["claude", "factory", "opencode"]
