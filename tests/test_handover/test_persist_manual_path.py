"""Tests for the manual-path persistence contract (FLOW-11, manual path).

Verifies Scenario 012-02 from ``specs/adhoc/issues/012-deviate-content.md``:

* Skill actor emits YAML on stdout AND uses the Write tool to the canonical
  path. ``persist_handover()`` validates the file exists and exits (does not
  overwrite an existing file with different content).

Properties asserted:

1. The file is created at the canonical ``.deviate/feat/...`` path.
2. The file parses as valid YAML via ``yaml.safe_load``.
3. The file contains the expected fields (phase, status, files, etc.).
4. The file is NOT staged in the git index (``git ls-files --error-unmatch``
   returns non-zero).
5. ``persist_handover()`` returns the canonical ``Path`` for the written file.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from tests.conftest import _git_env

from deviate.core.handover import handover_path, persist_handover


def _git_ls_files(target: Path, repo: Path) -> subprocess.CompletedProcess:
    """Run ``git ls-files --error-unmatch`` against the given path.

    Returns a CompletedProcess with returncode 0 if tracked, non-zero if untracked.
    """
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(target)],
        cwd=repo,
        env=_git_env(),
        capture_output=True,
        text=True,
    )


class TestPersistManualWriteCreatesFile:
    """AC-ADHOC-012-02, AC-ADHOC-012-15 — file is created at canonical path."""

    def test_persist_creates_file_at_canonical_path(self, tmp_git_repo: Path):
        manifest = (
            "phase: red\n"
            "status: PASS\n"
            "files:\n"
            "  - src/deviate/core/handover.py\n"
            "task_id: T-001\n"
        )
        result = persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        assert result.exists()
        assert result == handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-001", repo=tmp_git_repo
        )

    def test_persist_creates_parent_directories(self, tmp_git_repo: Path):
        """persist_handover MUST create nested parent directories as needed."""
        manifest = "phase: red\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-NEW", "ISS-999", "green", manifest, task_id="T-042", repo=tmp_git_repo
        )
        assert result.exists()
        # Parent chain should exist
        assert result.parent.exists()
        assert result.parent.parent.exists()
        assert result.parent.parent.parent.exists()

    def test_persist_returns_pathlib_path(self, tmp_git_repo: Path):
        manifest = "phase: red\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        assert isinstance(result, Path)


class TestPersistWritesValidYaml:
    """AC-ADHOC-012-02 — written content must be valid YAML with expected fields."""

    def test_persisted_yaml_parses_successfully(self, tmp_git_repo: Path):
        manifest = (
            "phase: red\n"
            "status: PASS\n"
            "files:\n"
            "  - src/deviate/core/handover.py\n"
            "task_id: T-001\n"
            "narrative_anchor:\n"
            '  intent: "Establish capture helper for FLOW-11"\n'
        )
        result = persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        with result.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        assert loaded["phase"] == "red"
        assert loaded["status"] == "PASS"
        assert loaded["files"] == ["src/deviate/core/handover.py"]
        assert loaded["task_id"] == "T-001"

    def test_persisted_yaml_preserves_optional_narrative_anchor(
        self, tmp_git_repo: Path
    ):
        """The extra='allow' model accepts the narrative_anchor: block."""
        manifest = (
            "phase: judge\n"
            "status: PASS\n"
            "files: []\n"
            "task_id: T-001\n"
            "narrative_anchor:\n"
            '  verdict_story: "The runner writes a YAML per phase and the helper is idempotent."\n'
        )
        result = persist_handover(
            "EPIC-X", "ISS-001", "judge", manifest, task_id="T-001", repo=tmp_git_repo
        )
        with result.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        assert loaded["narrative_anchor"]["verdict_story"].startswith(
            "The runner writes"
        )

    def test_persisted_macro_yaml_parses(self, tmp_git_repo: Path):
        """Macro path (no task_id) also produces valid YAML."""
        manifest = (
            "phase: explore\n"
            "status: PASS\n"
            "files: []\n"
            "epic_slug: EPIC-X\n"
            "issue_id: ISS-001\n"
        )
        result = persist_handover(
            "EPIC-X", "ISS-001", "explore", manifest, repo=tmp_git_repo
        )
        with result.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        assert loaded["phase"] == "explore"
        assert loaded["status"] == "PASS"


class TestPersistedFileIsGitignored:
    """AC-ADHOC-012-15 — ``.deviate/feat/...`` MUST NOT be tracked by git."""

    def test_persisted_file_not_in_git_index(self, tmp_git_repo: Path):
        manifest = "phase: red\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        # ``git ls-files --error-unmatch`` exits non-zero when the path is untracked.
        ls = _git_ls_files(result, tmp_git_repo)
        assert ls.returncode != 0, (
            f"persisted handover at {result} should not be tracked in git index; "
            f"stdout={ls.stdout!r} stderr={ls.stderr!r}"
        )

    def test_persisted_macro_file_not_in_git_index(self, tmp_git_repo: Path):
        manifest = "phase: explore\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-X", "ISS-001", "explore", manifest, repo=tmp_git_repo
        )
        ls = _git_ls_files(result, tmp_git_repo)
        assert ls.returncode != 0

    def test_persisted_files_absent_from_git_ls_files_output(self, tmp_git_repo: Path):
        """``git ls-files`` of the directory should not list any YAMLs."""
        persist_handover(
            "EPIC-X",
            "ISS-001",
            "red",
            "phase: red\nstatus: PASS\nfiles: []\n",
            task_id="T-001",
            repo=tmp_git_repo,
        )
        persist_handover(
            "EPIC-X",
            "ISS-001",
            "green",
            "phase: green\nstatus: PASS\nfiles: []\n",
            task_id="T-001",
            repo=tmp_git_repo,
        )
        ls = subprocess.run(
            ["git", "ls-files", ".deviate/"],
            cwd=tmp_git_repo,
            env=_git_env(),
            capture_output=True,
            text=True,
            check=True,
        )
        assert ls.stdout.strip() == ""


class TestPersistReturnValue:
    """AC-ADHOC-012-02 — returned Path is the canonical path."""

    def test_returned_path_matches_handover_path(self, tmp_git_repo: Path):
        manifest = "phase: red\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        expected = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-001", repo=tmp_git_repo
        )
        assert result == expected

    def test_returned_path_points_to_existing_file(self, tmp_git_repo: Path):
        manifest = "phase: green\nstatus: PASS\nfiles: []\n"
        result = persist_handover(
            "EPIC-X", "ISS-001", "green", manifest, task_id="T-001", repo=tmp_git_repo
        )
        assert result.exists()
        assert result.is_file()
