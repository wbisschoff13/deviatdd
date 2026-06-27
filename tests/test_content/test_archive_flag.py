"""Tests for FLOW-12 ``--archive`` epic-scoped tarball production.

Verifies Scenario 012-09 from ``specs/adhoc/issues/012-deviate-content.md``:

**Scenario 012-09**: ``--archive EPIC-X`` produces tarball at canonical path
**Given** fixture YAMLs under ``.deviate/feat/EPIC-X/**``
**When** ``deviate content --archive EPIC-X`` runs
**Then** ``specs/_archives/EPIC-X-narrative.tar.gz`` exists, contains every
YAML under that epic, and is the only committed-by-default artifact —
verifying AC-ADHOC-012-09.

The tarball is the lone durable-by-git artifact of the Content Capture
subsystem (per ``specs/plans/deviate-content.md:17-19``); the YAMLs
themselves remain gitignored runtime state.
"""

from __future__ import annotations

import tarfile
from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


def _seed_yaml(repo: Path, epic: str, issue: str, phase: str) -> Path:
    """Seed a single YAML handover under .deviate/feat/<epic>/<issue>/<task>/<phase>.yaml."""
    path = repo / ".deviate" / "feat" / epic / issue / "T-001" / f"{phase}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml_text = f"phase: {phase}\nstatus: PASS\ntask_id: T-001\nfiles: []\n"
    path.write_text(yaml_text, encoding="utf-8")
    return path


class TestArchiveFlag:
    """AC-ADHOC-012-09 — ``deviate content --archive EPIC-X`` produces a tarball."""

    def test_archive_produces_tarball_at_canonical_path(self, tmp_git_repo: Path):
        """`deviate content --archive EPIC-X` writes specs/_archives/EPIC-X-narrative.tar.gz."""
        for phase in ("red", "green", "judge", "refactor"):
            _seed_yaml(tmp_git_repo, "EPIC-X", "ISS-001", phase)

        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["content", "--archive", "EPIC-X"])

        assert result.exit_code == 0, (
            f"deviate content --archive EPIC-X exited {result.exit_code}. stdout={result.stdout}"
        )
        archive = tmp_git_repo / "specs" / "_archives" / "EPIC-X-narrative.tar.gz"
        assert archive.is_file(), f"Tarball not written at {archive}"

    def test_archive_tarball_contains_every_yaml_under_epic(self, tmp_git_repo: Path):
        """The tarball contains every YAML under .deviate/feat/EPIC-X/."""
        seeded: list[Path] = []
        for phase in ("red", "green", "judge", "refactor"):
            seeded.append(_seed_yaml(tmp_git_repo, "EPIC-X", "ISS-001", phase))
        # Seed another epic's YAML — it MUST NOT appear in the EPIC-X tarball.
        _seed_yaml(tmp_git_repo, "EPIC-OTHER", "ISS-002", "red")

        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["content", "--archive", "EPIC-X"])

        assert result.exit_code == 0, result.stdout
        archive = tmp_git_repo / "specs" / "_archives" / "EPIC-X-narrative.tar.gz"
        assert archive.is_file()

        with tarfile.open(archive, mode="r:gz") as tar:
            members = tar.getnames()

        for path in seeded:
            rel = path.relative_to(tmp_git_repo).as_posix()
            assert rel in members, (
                f"Tarball missing EPIC-X YAML {rel}; members={members}"
            )

        # The other epic's content must not appear under EPIC-X.
        other_rel = (
            (tmp_git_repo / ".deviate" / "feat" / "EPIC-OTHER" / "ISS-002" / "red.yaml")
            .relative_to(tmp_git_repo)
            .as_posix()
        )
        assert other_rel not in members, (
            f"Tarball leaked EPIC-OTHER content: {other_rel} in {members}"
        )

    def test_archive_creates_parent_directories(self, tmp_git_repo: Path):
        """`deviate content --archive EPIC-X` creates specs/_archives/ parent dirs as needed."""
        archive_parent = tmp_git_repo / "specs" / "_archives"
        # Pre-condition: parent does not yet exist.
        assert not archive_parent.exists(), "archive_parent should not exist pre-test"

        for phase in ("red", "green"):
            _seed_yaml(tmp_git_repo, "EPIC-X", "ISS-001", phase)

        with chdir(tmp_git_repo):
            result = runner.invoke(cli, ["content", "--archive", "EPIC-X"])

        assert result.exit_code == 0, result.stdout
        assert archive_parent.is_dir(), "specs/_archives/ parent directory not created"
        archive = archive_parent / "EPIC-X-narrative.tar.gz"
        assert archive.is_file()
