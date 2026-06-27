"""Tests for the canonical handover path convention (FLOW-11).

Verifies Scenario 012-01 (macro/micro path shape) and Scenario 012-05
(path traversal rejected) from ``specs/adhoc/issues/012-deviate-content.md``.

Path convention (per ``specs/_product/architecture.md:179`` and
``specs/plans/deviate-content.md:44-45``):

* macro:  ``.deviate/feat/<epic_slug>/<issue_id>/<phase>.yaml``
* micro:  ``.deviate/feat/<epic_slug>/<issue_id>/<task_id>/<phase>.yaml``

Path traversal via ``..`` segments, absolute paths, or symlink escape is
rejected by raising ``PathTraversalError`` before any filesystem write.
"""

from __future__ import annotations

import pytest

from deviate.core.handover import PathTraversalError, handover_path


class TestMacroPathShape:
    """AC-ADHOC-012-03 — macro path is ``.deviate/feat/<epic>/<issue>/<phase>.yaml``."""

    def test_macro_path_for_explore_phase(self, tmp_path):
        result = handover_path("EPIC-X", "ISS-001", "explore", repo=tmp_path)
        assert (
            result
            == tmp_path / ".deviate" / "feat" / "EPIC-X" / "ISS-001" / "explore.yaml"
        )

    def test_macro_path_for_research_phase(self, tmp_path):
        result = handover_path("EPIC-X", "ISS-001", "research", repo=tmp_path)
        assert (
            result
            == tmp_path / ".deviate" / "feat" / "EPIC-X" / "ISS-001" / "research.yaml"
        )

    def test_macro_path_for_prd_phase(self, tmp_path):
        result = handover_path("EPIC-X", "ISS-001", "prd", repo=tmp_path)
        assert (
            result == tmp_path / ".deviate" / "feat" / "EPIC-X" / "ISS-001" / "prd.yaml"
        )

    def test_macro_path_for_shard_phase(self, tmp_path):
        result = handover_path("EPIC-X", "ISS-001", "shard", repo=tmp_path)
        assert (
            result
            == tmp_path / ".deviate" / "feat" / "EPIC-X" / "ISS-001" / "shard.yaml"
        )

    def test_macro_path_returns_pathlib_path(self, tmp_path):
        from pathlib import Path

        result = handover_path("EPIC-X", "ISS-001", "explore", repo=tmp_path)
        assert isinstance(result, Path)


class TestMicroPathShape:
    """AC-ADHOC-012-03 — micro path includes ``<task_id>`` segment."""

    def test_micro_path_for_red_phase(self, tmp_path):
        result = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-001", repo=tmp_path
        )
        assert result == (
            tmp_path / ".deviate" / "feat" / "EPIC-X" / "ISS-001" / "T-001" / "red.yaml"
        )

    def test_micro_path_for_green_phase(self, tmp_path):
        result = handover_path(
            "EPIC-X", "ISS-001", "green", task_id="T-001", repo=tmp_path
        )
        assert result == (
            tmp_path
            / ".deviate"
            / "feat"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "green.yaml"
        )

    def test_micro_path_for_judge_phase(self, tmp_path):
        result = handover_path(
            "EPIC-X", "ISS-001", "judge", task_id="T-001", repo=tmp_path
        )
        assert result == (
            tmp_path
            / ".deviate"
            / "feat"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "judge.yaml"
        )

    def test_micro_path_for_refactor_phase(self, tmp_path):
        result = handover_path(
            "EPIC-X", "ISS-001", "refactor", task_id="T-001", repo=tmp_path
        )
        assert result == (
            tmp_path
            / ".deviate"
            / "feat"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "refactor.yaml"
        )

    def test_micro_path_distinguishes_tasks(self, tmp_path):
        """Different task_ids under the same issue must produce distinct paths."""
        path_a = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-001", repo=tmp_path
        )
        path_b = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-002", repo=tmp_path
        )
        assert path_a != path_b

    def test_micro_path_includes_task_segment_in_chain(self, tmp_path):
        """The micro path MUST have exactly one task_id segment between issue and phase."""
        result = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-001", repo=tmp_path
        )
        parts = result.parts
        # last part is the phase YAML file; segment before it is the task_id
        assert parts[-2] == "T-001"
        assert parts[-1] == "red.yaml"


class TestMacroMicroDistinguishability:
    """Macro (no task_id) and micro (with task_id) must produce different paths."""

    def test_macro_and_micro_paths_differ_for_same_phase(self, tmp_path):
        macro = handover_path("EPIC-X", "ISS-001", "red", repo=tmp_path)
        micro = handover_path(
            "EPIC-X", "ISS-001", "red", task_id="T-001", repo=tmp_path
        )
        assert macro != micro

    def test_macro_path_has_no_task_segment(self, tmp_path):
        macro = handover_path("EPIC-X", "ISS-001", "red", repo=tmp_path)
        # macro path: .../ISS-001/red.yaml — no T-* segment between
        assert "T-" not in macro.parts[-2]


class TestPathTraversalRejection:
    """AC-ADHOC-012-05 — path traversal attempts are rejected before any write.

    Tests assert ``PathTraversalError`` is raised specifically. Stub modules
    that raise ``NotImplementedError`` (or any other exception) MUST fail
    these tests — the spec mandates a dedicated diagnostic exception so
    callers can distinguish path-traversal errors from generic failures.
    """

    def test_parent_dir_segment_in_epic_rejected(self, tmp_path):
        with pytest.raises(PathTraversalError):
            handover_path("..", "ISS-001", "red", repo=tmp_path)

    def test_parent_dir_segment_in_issue_rejected(self, tmp_path):
        with pytest.raises(PathTraversalError):
            handover_path("EPIC-X", "..", "red", repo=tmp_path)

    def test_parent_dir_segment_in_task_id_rejected(self, tmp_path):
        with pytest.raises(PathTraversalError):
            handover_path(
                "EPIC-X", "ISS-001", "red", task_id="../../etc/passwd", repo=tmp_path
            )

    def test_absolute_path_in_task_id_rejected(self, tmp_path):
        with pytest.raises(PathTraversalError):
            handover_path(
                "EPIC-X", "ISS-001", "red", task_id="/etc/passwd", repo=tmp_path
            )

    def test_path_traversal_does_not_create_files(self, tmp_path):
        """A rejected path must not produce any file under the repo."""
        with pytest.raises(PathTraversalError):
            handover_path("..", "ISS-001", "red", repo=tmp_path)
        # No file should have been written anywhere
        assert list(tmp_path.rglob("*.yaml")) == []


class TestHandoverPathModuleSurface:
    """The handover module must export the documented public API."""

    def test_handover_path_is_callable(self, tmp_path):
        assert callable(handover_path)

    def test_module_exports_persist_handover(self):
        from deviate.core.handover import persist_handover

        assert callable(persist_handover)

    def test_module_exports_load_handover_records(self):
        from deviate.core.handover import load_handover_records

        assert callable(load_handover_records)

    def test_module_exports_handover_record_model(self):
        from deviate.core.handover import HandoverRecord

        # Read-side Pydantic model — instantiation must accept the documented fields.
        record = HandoverRecord(
            epic_slug="EPIC-X",
            issue_id="ISS-001",
            task_id="T-001",
            phase="red",
            status="PASS",
            files=["src/foo.py"],
        )
        assert record.epic_slug == "EPIC-X"
        assert record.phase == "red"
