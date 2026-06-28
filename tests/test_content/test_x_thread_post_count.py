"""Tests for FLOW-12 ``--posts N`` x-thread length control.

Verifies that the ``--posts`` CLI flag controls the number of posts the
x-thread synthesis produces:

**Given** a seeded window of handover YAMLs
**When** ``deviate content --format x-thread --posts N --slug x`` runs
**Then** the rendered draft contains exactly N posts, each ≤ 280 chars.

For ``N > 6`` the synthesis augments its anchor pool with per-record
story lines from the handovers so longer threads draw on real content
rather than only filler.
"""

from __future__ import annotations

import re
from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


def _seed_anchor_pool(repo: Path) -> None:
    """Seed four phases so the post-6 augmentation has story lines to draw on."""
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


def _read_thread(repo: Path, slug: str) -> tuple[str, list[str]]:
    """Return (raw_body, list_of_post_strings_after_split)."""
    body = (
        repo / ".deviate" / "content" / "drafts" / "x-thread" / f"{slug}.md"
    ).read_text(encoding="utf-8")
    parts = re.split(r"(?m)^\s*---\s*$", body)
    posts = [p.strip() for p in parts if p.strip()]
    return body, posts


class TestXThreadPostCount:
    """``--posts N`` controls the rendered thread length."""

    def test_posts_default_is_six(self, tmp_git_repo: Path):
        """Without --posts, the x-thread draft has 6 posts (backwards compat)."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--slug",
                    "default-six",
                ],
            )

        assert result.exit_code == 0, result.stdout
        _, posts = _read_thread(tmp_git_repo, "default-six")
        assert len(posts) == 6

    def test_posts_three_produces_three_posts(self, tmp_git_repo: Path):
        """`--posts 3` produces exactly 3 posts."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--posts",
                    "3",
                    "--slug",
                    "three",
                ],
            )

        assert result.exit_code == 0, result.stdout
        _, posts = _read_thread(tmp_git_repo, "three")
        assert len(posts) == 3, f"expected 3 posts, got {len(posts)}"
        for idx, post in enumerate(posts, start=1):
            assert len(post) <= 280, f"post #{idx} exceeds 280 chars: {post[:60]!r}"

    def test_posts_eight_augments_pool_with_per_record_stories(
        self, tmp_git_repo: Path
    ):
        """`--posts 8` produces 8 posts; post #6 onwards draws on per-record
        story lines (not only filler)."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "x-thread",
                    "--posts",
                    "8",
                    "--slug",
                    "eight",
                ],
            )

        assert result.exit_code == 0, result.stdout
        _, posts = _read_thread(tmp_git_repo, "eight")
        assert len(posts) == 8
        # Posts 7 and 8 should NOT be the boilerplate "Continued thread update" filler;
        # the seeded story lines should appear in the tail of the thread.
        tail = " ".join(posts[6:])
        assert "Continued thread update" not in tail, (
            f"posts 7-8 should draw on per-record stories, not filler. tail={tail!r}"
        )
        # The "Verdict: 4/4 tests green" line is one of the seeded anchors;
        # it should appear somewhere in the augmented tail.
        assert "Verdict" in tail or "Implementation" in tail or "Polish" in tail, (
            f"expected a per-record story line in posts 7-8. tail={tail!r}"
        )

    def test_posts_one_produces_single_post(self, tmp_git_repo: Path):
        """`--posts 1` produces a single post (the verdict)."""
        _seed_anchor_pool(tmp_git_repo)

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
                    "one",
                ],
            )

        assert result.exit_code == 0, result.stdout
        _, posts = _read_thread(tmp_git_repo, "one")
        assert len(posts) == 1

    def test_posts_applies_only_to_x_thread(self, tmp_git_repo: Path):
        """`--posts N` paired with a non-x-thread format is silently ignored;
        the blog draft is written normally and still passes its markdown contract."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--posts",
                    "12",
                    "--slug",
                    "blog-only",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        body = (
            tmp_git_repo / ".deviate" / "content" / "drafts" / "blog" / "blog-only.md"
        ).read_text(encoding="utf-8")
        assert body.startswith("#"), "blog draft must still start with heading"
