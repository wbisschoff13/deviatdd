from __future__ import annotations

import json
import os
import subprocess
from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli


def _git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


runner = CliRunner()


class TestContextPre:
    """US-001: Workspace Discovery and ContextContract Emission."""

    def test_context_pre_emits_contract(self, tmp_path: Path):
        """Scenario 1: Valid workspace emits READY contract with all fields."""
        (tmp_path / ".deviate").mkdir(parents=True)
        (tmp_path / ".deviate" / "config.toml").write_text('profile = "default"\n')
        (tmp_path / "specs").mkdir()
        with chdir(tmp_path):
            result = runner.invoke(cli, ["context", "pre"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["status"] == "READY"
        assert isinstance(data["repo_root"], str)
        assert isinstance(data["deviate_path"], str) or data["deviate_path"] is None
        assert isinstance(data["specs_path"], str) or data["specs_path"] is None
        assert isinstance(data["specs_issues"], list)
        assert isinstance(data["timestamp"], str)

    def test_context_pre_missing_deviate(self, tmp_path: Path):
        """Scenario 2: Missing .deviate/ returns FAILURE with diagnostic."""
        with chdir(tmp_path):
            result = runner.invoke(cli, ["context", "pre"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["status"] == "FAILURE"
        assert isinstance(data["diagnostic"], str)
        assert len(data["diagnostic"]) > 0


class TestContextPost:
    """US-002/US-003/US-004: Governance Upsert, Symlink, Stale Refs, Commit."""

    def test_context_post_updates_governance(self, tmp_git_repo: Path):
        """Scenario US-002-01: Valid manifest updates CLAUDE.md governance block."""
        (tmp_git_repo / ".deviate").mkdir(parents=True)
        (tmp_git_repo / ".deviate" / "config.toml").write_text('profile = "default"\n')
        (tmp_git_repo / "specs").mkdir()
        claude = tmp_git_repo / "CLAUDE.md"
        claude.write_text(
            "# Project\n\n"
            "## Technical Execution Context\n"
            "Status: INIT\n"
            "Tasks=Pending\n\n"
            "## Other Section\n"
            "Keep me.\n"
        )
        (tmp_git_repo / "AGENTS.md").write_text("# AGENTS\n")
        with chdir(tmp_git_repo):
            pre_result = runner.invoke(cli, ["context", "pre"])
            manifest_path = tmp_git_repo / "manifest.json"
            manifest_path.write_text(pre_result.stdout)
            result = runner.invoke(cli, ["context", "post", str(manifest_path)])
        assert result.exit_code == 0, result.output
        updated = claude.read_text()
        assert "## Technical Execution Context" in updated
        assert "Status: INIT" not in updated
        assert "Tasks=Pending" not in updated
        assert "## Other Section" in updated
        assert "Keep me." in updated
        assert "# Project" in updated

    def test_context_post_symlink_enforcement(self, tmp_git_repo: Path):
        """Scenario US-003-01: AGENTS.md created as symlink to CLAUDE.md."""
        (tmp_git_repo / ".deviate").mkdir(parents=True)
        (tmp_git_repo / ".deviate" / "config.toml").write_text('profile = "default"\n')
        claude_content = (
            "# CLAUDE Governance\n## Technical Execution Context\nTasks=Test\n"
        )
        (tmp_git_repo / "CLAUDE.md").write_text(claude_content)
        agents = tmp_git_repo / "AGENTS.md"
        assert not agents.exists()
        manifest_path = tmp_git_repo / "manifest.json"
        with chdir(tmp_git_repo):
            pre_result = runner.invoke(cli, ["context", "pre"])
            manifest_path.write_text(pre_result.stdout)
            result = runner.invoke(cli, ["context", "post", str(manifest_path)])
        assert result.exit_code == 0, result.output
        assert agents.is_symlink()
        assert agents.readlink() == tmp_git_repo / "CLAUDE.md"

    def test_context_post_stale_refs(self, tmp_git_repo: Path):
        """Scenario US-004-01: Stale patterns removed from AGENTS.md."""
        (tmp_git_repo / ".deviate").mkdir(parents=True)
        (tmp_git_repo / ".deviate" / "config.toml").write_text('profile = "default"\n')
        (tmp_git_repo / "CLAUDE.md").write_text("# CLAUDE\n")
        agents_content = (
            "# AGENTS\n\n"
            "Some valid content.\n\n"
            "rgr run\n"
            "manage-tasks.sh\n"
            "sdd-parse-ast.sh\n"
            "get-test-config.sh\n"
            ".rgr/\n\n"
            "More valid content.\n"
        )
        (tmp_git_repo / "AGENTS.md").write_text(agents_content)
        manifest_path = tmp_git_repo / "manifest.json"
        with chdir(tmp_git_repo):
            pre_result = runner.invoke(cli, ["context", "pre"])
            manifest_path.write_text(pre_result.stdout)
            result = runner.invoke(cli, ["context", "post", str(manifest_path)])
        assert result.exit_code == 0, result.output
        updated = (tmp_git_repo / "AGENTS.md").read_text()
        lines = updated.splitlines()
        assert "rgr run" not in lines
        assert "manage-tasks.sh" not in lines
        assert "sdd-parse-ast.sh" not in lines
        assert "get-test-config.sh" not in lines
        assert ".rgr/" not in lines
        assert "Some valid content." in lines
        assert "More valid content." in lines

    def test_context_post_stages_files(self, tmp_git_repo: Path):
        """Scenario US-002-01: Context post stages CLAUDE.md and AGENTS.md."""
        (tmp_git_repo / ".deviate").mkdir(parents=True)
        (tmp_git_repo / ".deviate" / "config.toml").write_text('profile = "default"\n')
        (tmp_git_repo / "specs").mkdir()
        (tmp_git_repo / "CLAUDE.md").write_text(
            "# Project\n\n"
            "## Technical Execution Context\n"
            "Tasks=Old\n\n"
            "## Keep\n"
            "Preserved.\n"
        )
        manifest_path = tmp_git_repo / "manifest.json"
        with chdir(tmp_git_repo):
            pre_result = runner.invoke(cli, ["context", "pre"])
            manifest_path.write_text(pre_result.stdout)
            result = runner.invoke(cli, ["context", "post", str(manifest_path)])
        assert result.exit_code == 0, result.output
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=tmp_git_repo,
            env=_git_env(),
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = staged.stdout.strip().splitlines()
        assert "CLAUDE.md" in staged_files
        assert "AGENTS.md" in staged_files


class TestContextCombined:
    """Single `deviate context` command — pre + post in one shot."""

    def test_context_combined_updates_governance_and_stages(self, tmp_git_repo: Path):
        """Running `deviate context` scans workspace, updates files, and stages."""
        (tmp_git_repo / ".deviate").mkdir(parents=True)
        (tmp_git_repo / ".deviate" / "config.toml").write_text('profile = "default"\n')
        (tmp_git_repo / "specs").mkdir()
        claude = tmp_git_repo / "CLAUDE.md"
        claude.write_text(
            "# Project\n\n"
            "## Technical Execution Context\n"
            "Tasks=Old\n\n"
            "## Other Section\n"
            "Keep me.\n"
        )
        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["context"])
        assert result.exit_code == 0, result.output
        updated = claude.read_text()
        assert "## Technical Execution Context" in updated
        assert "Tasks=Old" not in updated
        assert "## Other Section" in updated
        agents = tmp_git_repo / "AGENTS.md"
        assert agents.is_symlink()
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=tmp_git_repo,
            env=_git_env(),
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = staged.stdout.strip().splitlines()
        assert "CLAUDE.md" in staged_files
        assert "AGENTS.md" in staged_files

    def test_context_combined_missing_deviate_exits_nonzero(self, tmp_path: Path):
        """Missing .deviate/ emits failure and exits non-zero."""
        with chdir(tmp_path):
            result = runner.invoke(cli, ["context"])
        assert result.exit_code == 1, result.output
        assert "CONTEXT_FAILURE" in result.output
