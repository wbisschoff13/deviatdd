"""Tests for FLOW-12 epic-scoped window filtering.

Verifies Scenario 012-08 from ``specs/adhoc/issues/012-deviate-content.md``:

**Scenario 012-08**: ``--window EPIC-X`` filters records to that epic only
**Given** fixture YAMLs under ``.deviate/feat/EPIC-A/**``,
``.deviate/feat/EPIC-B/**``, and ``.deviate/feat/EPIC-X/**``
**When** ``load_handover_records(window="EPIC-X")`` is called
**Then** the returned list contains only records under
``.deviate/feat/EPIC-X/**``; absence of ``window`` returns all records
in chronological order — verifying AC-ADHOC-012-08.

Both the API layer (``load_handover_records(window=...)``) and the CLI
layer (``deviate content --window EPIC-X``) are exercised. The CLI test
also verifies that EPIC-A and EPIC-B anchors do NOT leak into the
EPIC-X-scoped draft.
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli
from deviate.core.handover import load_handover_records

runner = CliRunner()


def _seed_yaml(repo: Path, epic: str, issue: str, phase: str, anchor_text: str) -> Path:
    """Seed a single YAML handover under .deviate/feat/<epic>/<issue>/<task>/<phase>.yaml.

    Returns the written path.
    """
    target = repo / ".deviate" / "feat" / epic / issue / "T-001" / f"{phase}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    yaml_text = (
        f"phase: {phase}\n"
        "status: PASS\n"
        "task_id: T-001\n"
        "files: []\n"
        "narrative_anchor:\n"
        f"  story: {anchor_text}\n"
    )
    target.write_text(yaml_text, encoding="utf-8")
    return target


class TestWindowFilterAPI:
    """AC-ADHOC-012-08 — ``load_handover_records(window=...)`` filters by epic."""

    def test_load_records_window_filters_to_epic_only(self, tmp_git_repo: Path):
        """load_handover_records(window='EPIC-X') returns only EPIC-X records."""
        for epic in ("EPIC-A", "EPIC-B", "EPIC-X"):
            for phase in ("red", "green"):
                _seed_yaml(tmp_git_repo, epic, "ISS-001", phase, f"{epic} anchor")

        records = load_handover_records(window="EPIC-X", repo=tmp_git_repo)

        epics = [r.epic_slug for r in records]
        assert all(epic == "EPIC-X" for epic in epics), (
            f"Expected only EPIC-X records, got epics={epics}"
        )
        assert len(records) == 2  # one red + one green under EPIC-X

    def test_load_records_without_window_returns_all(self, tmp_git_repo: Path):
        """load_handover_records() with no window returns all records across epics."""
        for epic in ("EPIC-A", "EPIC-B", "EPIC-X"):
            for phase in ("red", "green"):
                _seed_yaml(tmp_git_repo, epic, "ISS-001", phase, f"{epic} anchor")

        records = load_handover_records(repo=tmp_git_repo)

        epics = {r.epic_slug for r in records}
        assert epics == {"EPIC-A", "EPIC-B", "EPIC-X"}
        assert len(records) == 6


class TestWindowFilterCLI:
    """AC-ADHOC-012-08 — CLI ``--window`` flag scopes synthesis to that epic."""

    def test_cli_window_filters_synthesis_to_epic_only(self, tmp_git_repo: Path):
        """`deviate content --format blog --window EPIC-X` synthesizes a draft that
        references only EPIC-X anchors — EPIC-A / EPIC-B anchors are absent.
        """
        epic_x_anchor = "EPIC-X unique anchor that MUST appear in EPIC-X draft."
        epic_a_anchor = "EPIC-A unique anchor that must NOT appear in EPIC-X draft."
        epic_b_anchor = "EPIC-B unique anchor that must NOT appear in EPIC-X draft."

        verdicts = {
            "EPIC-A": epic_a_anchor,
            "EPIC-B": epic_b_anchor,
            "EPIC-X": epic_x_anchor,
        }
        for epic, verdict in verdicts.items():
            target = (
                tmp_git_repo
                / ".deviate"
                / "feat"
                / epic
                / "ISS-001"
                / "T-001"
                / "judge.yaml"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            yaml_text = (
                "phase: judge\n"
                "status: PASS\n"
                "task_id: T-001\n"
                "files: []\n"
                "narrative_anchor:\n"
                f"  verdict_story: {verdict}\n"
            )
            target.write_text(yaml_text, encoding="utf-8")

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--slug",
                    "windowed-post",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"deviate content --window EPIC-X exited {result.exit_code}. stdout={result.stdout}"
        )
        draft = (
            tmp_git_repo / ".deviate" / "content-drafts" / "blog" / "windowed-post.md"
        )
        assert draft.is_file()
        body = draft.read_text(encoding="utf-8")
        assert epic_x_anchor in body, (
            f"EPIC-X unique anchor missing from windowed draft. body[:400]={body[:400]!r}"
        )
        assert epic_a_anchor not in body, (
            "EPIC-A leaked into EPIC-X-scoped draft — --window filter not honored."
        )
        assert epic_b_anchor not in body, (
            "EPIC-B leaked into EPIC-X-scoped draft — --window filter not honored."
        )

    def test_cli_without_window_includes_all_epics(self, tmp_git_repo: Path):
        """Without --window, the synthesis includes anchors from every epic in the repo."""
        epic_a_anchor = "EPIC-A wide-window anchor."
        epic_b_anchor = "EPIC-B wide-window anchor."

        verdicts = {
            "EPIC-A": epic_a_anchor,
            "EPIC-B": epic_b_anchor,
        }
        for epic, verdict in verdicts.items():
            target = (
                tmp_git_repo
                / ".deviate"
                / "feat"
                / epic
                / "ISS-001"
                / "T-001"
                / "judge.yaml"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            yaml_text = (
                "phase: judge\n"
                "status: PASS\n"
                "task_id: T-001\n"
                "files: []\n"
                "narrative_anchor:\n"
                f"  verdict_story: {verdict}\n"
            )
            target.write_text(yaml_text, encoding="utf-8")

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                ["content", "--format", "blog", "--slug", "wide-post"],
            )

        assert result.exit_code == 0, result.stdout
        draft = tmp_git_repo / ".deviate" / "content-drafts" / "blog" / "wide-post.md"
        body = draft.read_text(encoding="utf-8")
        assert epic_a_anchor in body, (
            f"EPIC-A wide-window anchor missing from unfiltered draft. body[:400]={body[:400]!r}"
        )
        assert epic_b_anchor in body
