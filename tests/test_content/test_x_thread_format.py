"""Tests for FLOW-12 x-thread-format synthesis.

Verifies Scenario 012-11 from ``specs/adhoc/issues/012-deviate-content.md``:

**Scenario 012-11**: X-thread format draft contains exactly 6 posts
**Given** fixture YAMLs with anchor fields across multiple phases
**When** ``deviate content --format x-thread --slug thread-1`` runs
**Then** ``.deviate/content-drafts/x-thread/thread-1.md`` contains exactly
6 posts, each ≤ 280 characters, sliced from the anchor pool — verifying
AC-ADHOC-012-11.

Posts are separated by ``---`` lines in the draft body. The splitting
helper is local to this test module because the production code does not
need to export it — the public contract is "exactly 6 posts, each ≤ 280".
"""

from __future__ import annotations

import re
from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


_POST_SEP = re.compile(r"(?m)^\s*---\s*$")


def _split_x_thread_posts(body: str) -> list[str]:
    """Split an x-thread draft into its 6 posts. Posts are separated by `---` lines."""
    parts = _POST_SEP.split(body)
    return [p.strip() for p in parts]


def _seed_anchor_pool(repo: Path) -> dict[str, str]:
    """Seed four phases of ``judge`` narrative anchors under ``EPIC-X/ISS-001/T-001``.

    Returns the dict of phase → anchor so the test can assert that the
    synthesized thread slices from this pool.
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
            / "feat"
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
        )
        target.write_text(yaml_text, encoding="utf-8")
    return anchors


class TestXThreadFormatSynthesis:
    """AC-ADHOC-012-11 — x-thread draft has exactly 6 posts ≤ 280 chars each."""

    def test_x_thread_draft_written_to_canonical_path(self, tmp_git_repo: Path):
        """`deviate content --format x-thread --slug thread-1` writes the draft at
        .deviate/content-drafts/x-thread/thread-1.md.
        """
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                ["content", "--format", "x-thread", "--slug", "thread-1"],
            )

        assert result.exit_code == 0, (
            f"deviate content --format x-thread exited {result.exit_code}. stdout={result.stdout}"
        )
        draft = (
            tmp_git_repo / ".deviate" / "content-drafts" / "x-thread" / "thread-1.md"
        )
        assert draft.is_file(), f"Draft not written at {draft}"

    def test_x_thread_has_exactly_six_posts(self, tmp_git_repo: Path):
        """The x-thread draft contains exactly 6 posts separated by `---` markers."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                ["content", "--format", "x-thread", "--slug", "thread-six"],
            )

        assert result.exit_code == 0, result.stdout
        draft = (
            tmp_git_repo / ".deviate" / "content-drafts" / "x-thread" / "thread-six.md"
        )
        body = draft.read_text(encoding="utf-8")
        posts = _split_x_thread_posts(body)
        # Filter out empty leading/trailing artifacts from leading/trailing separators.
        posts = [p for p in posts if p]
        assert len(posts) == 6, (
            f"x-thread must contain exactly 6 posts, got {len(posts)}"
        )

    def test_x_thread_each_post_under_280_chars(self, tmp_git_repo: Path):
        """Each post in the x-thread is ≤ 280 characters (X / Twitter limit)."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                ["content", "--format", "x-thread", "--slug", "thread-len"],
            )

        assert result.exit_code == 0, result.stdout
        draft = (
            tmp_git_repo / ".deviate" / "content-drafts" / "x-thread" / "thread-len.md"
        )
        body = draft.read_text(encoding="utf-8")
        posts = [p for p in _split_x_thread_posts(body) if p]
        assert len(posts) == 6, (
            f"x-thread must contain exactly 6 posts, got {len(posts)}"
        )
        for idx, post in enumerate(posts, start=1):
            assert len(post) <= 280, (
                f"x-thread post #{idx} (len={len(post)}) exceeds 280 chars ({post[:60]!r}...)"
            )
