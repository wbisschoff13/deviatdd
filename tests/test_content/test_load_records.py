"""Tests for FLOW-12 record loading — chronological handover enumeration.

Verifies Scenario 012-08 (window filter at the API layer) and the
chronological-ordering contract of ``load_handover_records()`` from
``specs/adhoc/issues/012-deviate-content.md``.

The function returns ``HandoverRecord`` objects in the order they were
written to disk (mtime) — *not* lexicographic path order — because the
synthesis layer needs the DeviaTDD micro-cycle phase order
(red → green → judge → refactor) to be deterministic and meaningful.
"""

from __future__ import annotations

import time
from pathlib import Path

from deviate.core.handover import HandoverRecord, load_handover_records


def _seed_handover(repo: Path, phase: str) -> Path:
    """Write a single handover YAML and return its canonical path."""
    target = (
        repo
        / ".deviate"
        / "content"
        / "handovers"
        / "EPIC-X"
        / "ISS-001"
        / "T-001"
        / f"{phase}.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"phase: {phase}\nstatus: PASS\ntask_id: T-001\nfiles: []\n",
        encoding="utf-8",
    )
    return target


class TestLoadHandoverRecordsChronological:
    """AC-ADHOC-012-08 / Scenario 012-08 — chronological ordering contract."""

    def test_load_records_returns_four_records(self, tmp_git_repo: Path):
        """Given a fixture directory of 4 phase YAMLs, load_handover_records() returns 4 records."""
        for phase in ("red", "green", "judge", "refactor"):
            _seed_handover(tmp_git_repo, phase)
            # Touch each one distinctly so mtimes differ even on coarse-grained FS.
            time.sleep(0.01)

        records = load_handover_records(repo=tmp_git_repo)

        assert len(records) == 4
        assert all(isinstance(r, HandoverRecord) for r in records)

    def test_load_records_chronological_order(self, tmp_git_repo: Path):
        """Records are returned in DeviaTDD micro-cycle chronological order:
        red → green → judge → refactor — not lexicographic path order.
        """
        # Seed in scrambled file-write order to prove the loader sorts by mtime,
        # not by phase name (lexicographic order would be green → judge → red → refactor).
        for phase in ("judge", "red", "refactor", "green"):
            _seed_handover(tmp_git_repo, phase)
            time.sleep(0.01)

        records = load_handover_records(repo=tmp_git_repo)

        phases = [r.phase for r in records]
        assert phases == ["judge", "red", "refactor", "green"], (
            f"Expected chronological DeviaTDD phase order, got {phases}. "
            "load_handover_records() must NOT return lexicographic path order."
        )

    def test_load_records_preserves_narrative_anchor(self, tmp_git_repo: Path):
        """A judge record carrying narrative_anchor.verdict_story round-trips through load."""
        judge_yaml = (
            "phase: judge\n"
            "status: PASS\n"
            "task_id: T-001\n"
            "files:\n"
            "  - src/deviate/core/handover.py\n"
            "narrative_anchor:\n"
            "  invariant_protected: spec.md path-traversal guard\n"
            "  verdict_story: We hardened the path-traversal surface end-to-end.\n"
        )
        target = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "handovers"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "judge.yaml"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(judge_yaml, encoding="utf-8")

        records = load_handover_records(repo=tmp_git_repo)

        assert len(records) == 1
        judge = records[0]
        assert judge.narrative_anchor is not None
        assert judge.narrative_anchor["verdict_story"] == (
            "We hardened the path-traversal surface end-to-end."
        )
        assert judge.narrative_anchor["invariant_protected"] == (
            "spec.md path-traversal guard"
        )

    def test_load_records_chronological_without_window_arg(self, tmp_git_repo: Path):
        """load_handover_records() (no window) returns all records in chronological order
        across the repository. Seeded phases are written in scrambled order to prove
        that the loader sorts by mtime, not by phase name.
        """
        write_order = ["refactor", "green", "judge", "red"]
        for phase in write_order:
            _seed_handover(tmp_git_repo, phase)
            time.sleep(0.01)

        records = load_handover_records(repo=tmp_git_repo)

        phases = [r.phase for r in records]
        assert phases == write_order
