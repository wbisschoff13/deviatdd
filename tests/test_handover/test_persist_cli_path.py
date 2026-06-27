"""Tests for the CLI-path persistence contract (FLOW-11, CLI path).

Verifies Scenario 012-03 from ``specs/adhoc/issues/012-deviate-content.md``:

* Skill actor emits YAML to stdout only (no Write tool call).
* The CLI orchestrator parses the actor's stdout and calls
  ``persist_handover()`` with the captured manifest string.
* The function writes the file at the canonical path and exits cleanly.

The test exercises the same ``persist_handover()`` entry point that the
orchestrator would invoke after capturing the manifest from stdout.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from tests.conftest import _git_env

from deviate.core.handover import PathTraversalError, handover_path, persist_handover


class TestCliPathWritesFromCapturedStdout:
    """AC-ADHOC-012-02 — CLI path: file is written from the captured manifest."""

    def test_cli_path_writes_file_from_stdout_capture(self, tmp_git_repo: Path):
        # Simulate the actor's stdout (a YAML document as a string).
        captured_stdout = (
            "phase: red\n"
            "status: PASS\n"
            "files:\n"
            "  - tests/test_handover/test_persist_cli_path.py\n"
            "task_id: T-007\n"
            'rationale: "Captured via CLI runner after actor stdout emit"\n'
        )
        result = persist_handover(
            "EPIC-X",
            "ISS-001",
            "red",
            captured_stdout,
            task_id="T-007",
            repo=tmp_git_repo,
        )
        assert result.exists()
        with result.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        assert loaded["phase"] == "red"
        assert loaded["status"] == "PASS"
        assert loaded["task_id"] == "T-007"

    def test_cli_path_matches_canonical_handover_path(self, tmp_git_repo: Path):
        captured_stdout = "phase: green\nstatus: PASS\nfiles: []\ntask_id: T-008\n"
        result = persist_handover(
            "EPIC-X",
            "ISS-001",
            "green",
            captured_stdout,
            task_id="T-008",
            repo=tmp_git_repo,
        )
        expected = handover_path(
            "EPIC-X", "ISS-001", "green", task_id="T-008", repo=tmp_git_repo
        )
        assert result == expected

    def test_cli_path_writes_macro_handover(self, tmp_git_repo: Path):
        """CLI path for a macro phase (no task_id) lands at the macro path."""
        captured_stdout = (
            "phase: explore\n"
            "status: PASS\n"
            "files: []\n"
            "epic_slug: EPIC-X\n"
            "issue_id: ISS-001\n"
        )
        result = persist_handover(
            "EPIC-X", "ISS-001", "explore", captured_stdout, repo=tmp_git_repo
        )
        assert result.exists()
        # No task segment in the chain
        assert result.parent.name != "T-XXX"

    def test_cli_path_preserves_unicode_in_manifest(self, tmp_git_repo: Path):
        captured_stdout = (
            "phase: red\n"
            "status: PASS\n"
            "files: []\n"
            'rationale: "Café résumé naïve — 测试"\n'
        )
        result = persist_handover(
            "EPIC-X",
            "ISS-001",
            "red",
            captured_stdout,
            task_id="T-009",
            repo=tmp_git_repo,
        )
        content = result.read_text(encoding="utf-8")
        assert "Café" in content
        assert "测试" in content

    def test_cli_path_file_not_in_git_index(self, tmp_git_repo: Path):
        captured_stdout = "phase: red\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-X",
            "ISS-001",
            "red",
            captured_stdout,
            task_id="T-010",
            repo=tmp_git_repo,
        )
        ls = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(result)],
            cwd=tmp_git_repo,
            env=_git_env(),
            capture_output=True,
            text=True,
        )
        assert ls.returncode != 0


class TestCliPathAcceptsDictManifest:
    """Some CLI paths may pass a dict (after JSON/YAML parse) — accept either."""

    def test_cli_path_accepts_string_manifest(self, tmp_git_repo: Path):
        """The primary contract: manifest is a YAML string (raw actor stdout)."""
        result = persist_handover(
            "EPIC-X",
            "ISS-001",
            "red",
            "phase: red\nstatus: PASS\nfiles: []\n",
            task_id="T-011",
            repo=tmp_git_repo,
        )
        assert result.exists()
        with result.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        assert loaded["phase"] == "red"


class TestCliPathValidation:
    """The CLI path must reject path-traversal attempts the same way.

    Tests assert ``PathTraversalError`` is raised specifically. Stub modules
    that raise ``NotImplementedError`` MUST fail these tests.
    """

    def test_cli_path_rejects_traversal_in_task_id(self, tmp_git_repo: Path):
        with pytest.raises(PathTraversalError):
            persist_handover(
                "EPIC-X",
                "ISS-001",
                "red",
                "phase: red\nstatus: PASS\nfiles: []\n",
                task_id="../../etc/passwd",
                repo=tmp_git_repo,
            )

    def test_cli_path_rejects_traversal_in_epic(self, tmp_git_repo: Path):
        with pytest.raises(PathTraversalError):
            persist_handover(
                "..",
                "ISS-001",
                "red",
                "phase: red\nstatus: PASS\nfiles: []\n",
                repo=tmp_git_repo,
            )
