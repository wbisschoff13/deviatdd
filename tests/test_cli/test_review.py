from __future__ import annotations

import json
import subprocess
from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli
from tests.conftest import _git_env

runner = CliRunner()


class TestReviewPreCore:
    """RED-phase tests for TSK-004-02: pre command core — contract emission, git diff, constitution path resolution."""

    def test_review_pre_emits_contract(self, tmp_git_repo: Path) -> None:
        """UT-01: deviate review pre emits valid JSON contract with all required keys."""
        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["review", "pre"])

        assert result.exit_code == 0
        contract = json.loads(result.stdout)
        assert isinstance(contract, dict)
        assert "status" in contract
        assert "diff" in contract
        assert "constitution_path" in contract
        assert "prd_path" in contract
        assert "base_branch" in contract
        assert "report_exists" in contract
        assert "timestamp" in contract
        assert contract["status"] == "READY"

    def test_review_pre_finds_constitution(self, tmp_git_repo: Path) -> None:
        """UT-02: Contract constitution_path points to resolved absolute path of specs/constitution.md."""
        specs_dir = tmp_git_repo / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        const_path = specs_dir / "constitution.md"
        const_path.write_text("# Test Constitution\n", encoding="utf-8")

        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["review", "pre"])

        assert result.exit_code == 0
        contract = json.loads(result.stdout)
        resolved = str(const_path.resolve())
        assert contract["constitution_path"] == resolved

    def test_review_pre_diff_against_main(self, tmp_git_repo: Path) -> None:
        """UT-06: diff field contains unified diff of changes against merge-base with main."""
        subprocess.run(
            ["git", "branch", "-m", "main"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )
        (tmp_git_repo / "existing.txt").write_text("original\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "existing.txt"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "base content"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )

        subprocess.run(
            ["git", "checkout", "-b", "feature-branch"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )
        (tmp_git_repo / "new.txt").write_text("new content\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "new.txt"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "add new file"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["review", "pre"])

        assert result.exit_code == 0
        contract = json.loads(result.stdout)
        assert contract["diff"], (
            "Expected non-empty diff when branch has changes vs main"
        )
        assert "new.txt" in contract["diff"]

    def test_review_pre_empty_diff(self, tmp_git_repo: Path) -> None:
        """UT-07: Contract emitted with empty diff string when no changes vs main."""
        subprocess.run(
            ["git", "branch", "-m", "main"],
            cwd=tmp_git_repo,
            env=_git_env(),
            check=True,
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["review", "pre"])

        assert result.exit_code == 0
        contract = json.loads(result.stdout)
        assert contract["diff"] == ""
