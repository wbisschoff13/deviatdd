"""Tests for FLOW-12 ``--posts N`` range validation.

Verifies the ``--posts`` flag rejects out-of-range values with a clear
diagnostic and a non-zero exit code:

- ``--posts 0`` is rejected (must be ≥ 1)
- ``--posts 51`` is rejected (must be ≤ 50)
- ``--posts 50`` is accepted (boundary)
- ``--posts 1`` is accepted (boundary)
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


def _seed_minimal_anchor(repo: Path) -> None:
    """Seed one minimal judge anchor so the synthesis has at least one record."""
    target = (
        repo
        / ".deviate"
        / "content"
        / "handovers"
        / "EPIC-X"
        / "ISS-001"
        / "T-001"
        / "judge.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "phase: judge\nstatus: PASS\ntask_id: T-001\nfiles: []\n"
        "narrative_anchor:\n  verdict_story: Test verdict story.\n",
        encoding="utf-8",
    )


class TestPostsValidation:
    """``--posts`` rejects out-of-range values."""

    def test_posts_zero_is_rejected(self, tmp_git_repo: Path):
        """`--posts 0` exits non-zero with diagnostic; no draft written."""
        _seed_minimal_anchor(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--posts",
                    "0",
                    "--slug",
                    "zero",
                ],
            )

        assert result.exit_code != 0, (
            f"expected non-zero exit for --posts 0, got {result.exit_code}. "
            f"stdout={result.stdout}"
        )
        assert "1..50" in result.stdout or "posts" in result.stdout.lower(), (
            f"diagnostic should mention range. stdout={result.stdout!r}"
        )
        bad = tmp_git_repo / ".deviate" / "content" / "drafts" / "x-thread" / "zero.md"
        assert not bad.exists(), "no draft must be written when validation fails"

    def test_posts_fifty_one_is_rejected(self, tmp_git_repo: Path):
        """`--posts 51` exits non-zero with diagnostic; no draft written."""
        _seed_minimal_anchor(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--posts",
                    "51",
                    "--slug",
                    "fifty-one",
                ],
            )

        assert result.exit_code != 0, (
            f"expected non-zero exit for --posts 51, got {result.exit_code}. "
            f"stdout={result.stdout}"
        )
        assert "1..50" in result.stdout, (
            f"diagnostic should mention range. stdout={result.stdout!r}"
        )

    def test_posts_one_is_accepted(self, tmp_git_repo: Path):
        """`--posts 1` (lower boundary) is accepted."""
        _seed_minimal_anchor(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--posts",
                    "1",
                    "--slug",
                    "boundary-low",
                ],
            )

        assert result.exit_code == 0, (
            f"--posts 1 should be accepted, got exit {result.exit_code}. "
            f"stdout={result.stdout}"
        )

    def test_posts_fifty_is_accepted(self, tmp_git_repo: Path):
        """`--posts 50` (upper boundary) is accepted."""
        _seed_minimal_anchor(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--posts",
                    "50",
                    "--slug",
                    "boundary-high",
                ],
            )

        assert result.exit_code == 0, (
            f"--posts 50 should be accepted, got exit {result.exit_code}. "
            f"stdout={result.stdout}"
        )
