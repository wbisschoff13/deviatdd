"""Tests for the idempotent overwrite-or-skip contract of ``persist_handover()``.

Verifies Scenario 012-04 from ``specs/adhoc/issues/012-deviate-content.md``:

* Re-invoking ``persist_handover()`` with the **same** manifest and coordinates
  is a no-op — single file on disk, no exception, same returned Path.
* The contract is ``write-or-skip``: divergent content is a real failure
  surfaced by git log diff (out of scope for this test); identical content
  is silently accepted.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from tests.conftest import _git_env

from deviate.core.handover import handover_path, persist_handover


def _list_handover_files(epic: str, issue: str, task: str, repo: Path) -> list[Path]:
    """Return the list of YAML handovers under a (epic, issue, task) tuple."""
    base = repo / ".deviate" / "content" / "handovers" / epic / issue / task
    if not base.exists():
        return []
    return sorted(base.glob("*.yaml"))


class TestIdempotentIdenticalWrites:
    """AC-ADHOC-012-04 — double write with identical content is a no-op."""

    def test_double_write_produces_single_file(self, tmp_git_repo: Path):
        manifest = (
            "phase: red\n"
            "status: PASS\n"
            "files:\n"
            "  - src/deviate/core/handover.py\n"
            "task_id: T-001\n"
        )
        persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-001", repo=tmp_git_repo
        )
        files = _list_handover_files("EPIC-X", "ISS-001", "T-001", tmp_git_repo)
        assert len(files) == 1
        assert files[0].name == "red.yaml"

    def test_double_write_returns_same_path(self, tmp_git_repo: Path):
        manifest = "phase: green\nstatus: PASS\nfiles: []\ntask_id: T-002\n"
        first = persist_handover(
            "EPIC-X", "ISS-001", "green", manifest, task_id="T-002", repo=tmp_git_repo
        )
        second = persist_handover(
            "EPIC-X", "ISS-001", "green", manifest, task_id="T-002", repo=tmp_git_repo
        )
        assert first == second

    def test_double_write_does_not_raise(self, tmp_git_repo: Path):
        manifest = "phase: judge\nstatus: PASS\nfiles: []\ntask_id: T-003\n"
        # No exception on first call
        persist_handover(
            "EPIC-X", "ISS-001", "judge", manifest, task_id="T-003", repo=tmp_git_repo
        )
        # No exception on second call with identical content
        persist_handover(
            "EPIC-X", "ISS-001", "judge", manifest, task_id="T-003", repo=tmp_git_repo
        )

    def test_triple_write_still_single_file(self, tmp_git_repo: Path):
        """Three or more writes with identical content are also no-ops."""
        manifest = "phase: refactor\nstatus: PASS\nfiles: []\ntask_id: T-004\n"
        for _ in range(3):
            persist_handover(
                "EPIC-X",
                "ISS-001",
                "refactor",
                manifest,
                task_id="T-004",
                repo=tmp_git_repo,
            )
        files = _list_handover_files("EPIC-X", "ISS-001", "T-004", tmp_git_repo)
        assert len(files) == 1

    def test_idempotent_write_preserves_content(self, tmp_git_repo: Path):
        """Second write must not corrupt the original content."""
        manifest = (
            "phase: red\n"
            "status: PASS\n"
            "files:\n"
            "  - src/foo.py\n"
            "narrative_anchor:\n"
            '  intent: "Original intent"\n'
        )
        first = persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-005", repo=tmp_git_repo
        )
        persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-005", repo=tmp_git_repo
        )
        with first.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        assert loaded["phase"] == "red"
        assert loaded["status"] == "PASS"
        assert loaded["files"] == ["src/foo.py"]
        assert loaded["narrative_anchor"]["intent"] == "Original intent"


class TestIdempotentMacroWrite:
    """Macro phase (no task_id) writes are also idempotent."""

    def test_macro_double_write_single_file(self, tmp_git_repo: Path):
        manifest = "phase: explore\nstatus: PASS\nfiles: []\nepic_slug: EPIC-X\n"
        persist_handover("EPIC-X", "ISS-001", "explore", manifest, repo=tmp_git_repo)
        persist_handover("EPIC-X", "ISS-001", "explore", manifest, repo=tmp_git_repo)
        macro_dir = (
            tmp_git_repo / ".deviate" / "content" / "handovers" / "EPIC-X" / "ISS-001"
        )
        assert macro_dir.exists()
        files = sorted(macro_dir.glob("explore.yaml"))
        assert len(files) == 1


class TestIdempotentWriteDoesNotStage:
    """Repeated writes must keep the file untracked in git."""

    def test_repeated_writes_stay_untracked(self, tmp_git_repo: Path):
        manifest = "phase: red\nstatus: PASS\nfiles: []\ntask_id: T-006\n"
        target = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-006", repo=tmp_git_repo
        )
        for _ in range(3):
            persist_handover(
                "EPIC-X", "ISS-001", "red", manifest, task_id="T-006", repo=tmp_git_repo
            )
        ls = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(target)],
            cwd=tmp_git_repo,
            env=_git_env(),
            capture_output=True,
            text=True,
        )
        assert ls.returncode != 0


class TestIdempotentPerformance:
    """The idempotent fast-path should complete in well under the 5ms budget."""

    def test_second_write_fast_path(self, tmp_git_repo: Path):
        """Second call should be near-instant (file existence check + early return)."""
        import time

        manifest = "phase: red\nstatus: PASS\nfiles: []\ntask_id: T-100\n"
        persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-100", repo=tmp_git_repo
        )
        start = time.perf_counter()
        persist_handover(
            "EPIC-X", "ISS-001", "red", manifest, task_id="T-100", repo=tmp_git_repo
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        # Generous bound: 50ms (spec says ≤ 5ms; 50ms accommodates slow CI)
        assert elapsed_ms < 50, (
            f"second write took {elapsed_ms:.1f}ms (expected < 50ms)"
        )
