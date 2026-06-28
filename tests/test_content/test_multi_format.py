"""Tests for FLOW-12 multi-format synthesis.

Verifies that a single ``deviate content`` invocation can render more than
one format from the same window of handovers:

**Given** a seeded window of handover YAMLs
**When** ``deviate content --format blog --format x-thread --slug my-post`` runs
**Then** both ``.deviate/content/drafts/blog/my-post.md`` and
``.deviate/content/drafts/x-thread/my-post.md`` are written, each
independently valid (blog passes its verdict_story contract; x-thread
has exactly 6 posts since --posts is at its default).
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


def _seed_anchor_pool(repo: Path) -> None:
    """Seed four phases of ``judge`` narrative anchors under ``EPIC-X/ISS-001/T-001``.

    Mirrors the fixture used by ``test_x_thread_format.py`` so the multi-
    format case exercises the same anchor pool that single-format tests
    use. The blog draft will pick up the ``judge.verdict_story`` field;
    the x-thread draft will draw on the four story lines.
    """
    anchors = {
        "red": "Frozen assumption: handover_path() must guard against .. traversal.",
        "green": "Implementation: pathlib with strict=False resolve check + early return.",
        "judge": "Verdict: 4/4 tests green, no spec violations, FLOW-11 contract honored.",
        "refactor": "Polish: extracted _HANDOVER_ROOT constant, deduplicated helper.",
    }
    for phase, anchor in anchors.items():
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
        yaml_text = (
            f"phase: {phase}\n"
            "status: PASS\n"
            "task_id: T-001\n"
            "files: []\n"
            "narrative_anchor:\n"
            f"  story: {anchor}\n"
            f"  verdict_story: {anchor}\n"
        )
        target.write_text(yaml_text, encoding="utf-8")


class TestMultiFormatSynthesis:
    """Multi-format ``--format`` flag writes one draft per format."""

    def test_blog_and_x_thread_written_from_single_invocation(self, tmp_git_repo: Path):
        """`--format blog --format x-thread` writes both drafts in one call."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--format",
                    "x-thread",
                    "--slug",
                    "combo",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"deviate content multi-format exited {result.exit_code}. "
            f"stdout={result.stdout}"
        )

        blog = tmp_git_repo / ".deviate" / "content" / "drafts" / "blog" / "combo.md"
        thread = (
            tmp_git_repo / ".deviate" / "content" / "drafts" / "x-thread" / "combo.md"
        )
        assert blog.is_file(), f"Blog draft not written at {blog}"
        assert thread.is_file(), f"X-thread draft not written at {thread}"

    def test_multi_format_blog_starts_with_heading(self, tmp_git_repo: Path):
        """The blog draft from multi-format invocation still satisfies the
        ``body.startswith('#')`` markdown-heading contract."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--format",
                    "x-thread",
                    "--slug",
                    "combo-md",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        body = (
            tmp_git_repo / ".deviate" / "content" / "drafts" / "blog" / "combo-md.md"
        ).read_text(encoding="utf-8")
        assert body.startswith("#"), (
            f"Multi-format blog draft does not start with heading. "
            f"body[:80]={body[:80]!r}"
        )

    def test_multi_format_x_thread_has_six_posts_by_default(self, tmp_git_repo: Path):
        """The x-thread draft from multi-format invocation still has 6 posts
        when --posts is left at its default."""
        import re

        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--format",
                    "x-thread",
                    "--slug",
                    "combo-six",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        body = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "x-thread"
            / "combo-six.md"
        ).read_text(encoding="utf-8")
        parts = re.split(r"(?m)^\s*---\s*$", body)
        posts = [p.strip() for p in parts if p.strip()]
        assert len(posts) == 6, (
            f"Multi-format x-thread default count should be 6, got {len(posts)}"
        )

    def test_three_formats_in_one_invocation(self, tmp_git_repo: Path):
        """Passing --format three times writes three drafts in one call."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--format",
                    "x-thread",
                    "--format",
                    "release-notes",
                    "--slug",
                    "trio",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"three-format exited {result.exit_code}. stdout={result.stdout}"
        )
        for sub in ("blog", "x-thread", "release-notes"):
            path = tmp_git_repo / ".deviate" / "content" / "drafts" / sub / "trio.md"
            assert path.is_file(), f"{sub} draft missing at {path}"

    def test_unknown_format_in_list_rejects_invocation(self, tmp_git_repo: Path):
        """If any --format value is unknown, the whole invocation exits non-zero
        and no drafts are written."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--format",
                    "nonsense",
                    "--slug",
                    "bad",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code != 0, (
            f"expected non-zero exit on unknown format, got {result.exit_code}. "
            f"stdout={result.stdout}"
        )
        bad_blog = tmp_git_repo / ".deviate" / "content" / "drafts" / "blog" / "bad.md"
        assert not bad_blog.exists(), (
            "Blog draft must not be written when validation fails partway"
        )
