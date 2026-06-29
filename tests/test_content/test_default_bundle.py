"""Tests for FLOW-12 default-format bundle.

Verifies that ``deviate content`` invoked without ``--format`` renders the
**build-in-public default bundle**: ``blog``, ``x-thread``, and ``threads``
drafts from the same handover window in one invocation.

**Given** a seeded window of handover YAMLs
**When** ``deviate content --slug my-post --window EPIC-X`` runs with NO
``--format`` flag
**Then** three drafts land at the canonical paths:
- ``.deviate/content/drafts/blog/my-post.md``
- ``.deviate/content/drafts/x-thread/my-post.md``
- ``.deviate/content/drafts/threads/my-post.md``

This is the headline behavior of the ``/deviate-content`` slash command:
the developer runs one command and gets a content bundle ready for review
across blog, X, and Threads surfaces without having to remember which
``--format`` value triggers which template.

The explicit ``--format`` override path stays intact — passing
``--format blog`` alone writes only the blog draft, matching the
repeatable-flag contract established for multi-format synthesis.
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


def _seed_anchor_pool(repo: Path) -> None:
    """Seed four phases of ``judge`` narrative anchors under ``EPIC-X/ISS-001/T-001``.

    Mirrors the fixture used by ``test_multi_format.py`` so the default
    bundle case exercises the same anchor pool that single-format tests
    use. The blog draft picks up ``judge.verdict_story``; the x-thread
    draft draws on the four story lines; the Threads draft surfaces the
    same lead anchor in its TL;DR.
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


class TestDefaultBundleSynthesis:
    """Default ``deviate content`` (no ``--format``) emits the bundle."""

    def test_no_format_flag_writes_all_three_default_drafts(
        self, tmp_git_repo: Path
    ) -> None:
        """Omitting ``--format`` renders blog + x-thread + threads in one call."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--slug",
                    "default-bundle",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"default-bundle exited {result.exit_code}. stdout={result.stdout}"
        )

        for sub in ("blog", "x-thread", "threads"):
            path = (
                tmp_git_repo
                / ".deviate"
                / "content"
                / "drafts"
                / sub
                / "default-bundle.md"
            )
            assert path.is_file(), f"{sub} draft missing at {path}"

    def test_default_bundle_blog_starts_with_heading(self, tmp_git_repo: Path) -> None:
        """The default bundle's blog draft still satisfies the
        ``body.startswith('#')`` markdown-heading contract."""
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--slug",
                    "default-blog-md",
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
            / "blog"
            / "default-blog-md.md"
        ).read_text(encoding="utf-8")
        assert body.startswith("#"), (
            f"Default-bundle blog draft does not start with heading. "
            f"body[:80]={body[:80]!r}"
        )

    def test_default_bundle_x_thread_has_six_posts(self, tmp_git_repo: Path) -> None:
        """The default bundle's x-thread draft has 6 posts (the default)."""
        import re

        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--slug",
                    "default-six",
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
            / "default-six.md"
        ).read_text(encoding="utf-8")
        parts = re.split(r"(?m)^\s*---\s*$", body)
        posts = [p.strip() for p in parts if p.strip()]
        assert len(posts) == 6, (
            f"Default-bundle x-thread post count should be 6, got {len(posts)}"
        )

    def test_explicit_single_format_override_still_works(
        self, tmp_git_repo: Path
    ) -> None:
        """Passing ``--format blog`` alone writes ONLY the blog draft.

        Confirms the explicit-format override path is unchanged: the
        default bundle applies only when ``--format`` is omitted, and any
        explicit value (single or repeated) replaces the default set.
        """
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--slug",
                    "override-blog",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout

        blog = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "blog"
            / "override-blog.md"
        )
        thread = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "x-thread"
            / "override-blog.md"
        )
        threads_draft = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "threads"
            / "override-blog.md"
        )
        assert blog.is_file(), f"Blog draft not written at {blog}"
        assert not thread.exists(), (
            "x-thread draft must NOT be written when --format blog is the only "
            f"format passed (default bundle must not apply). Found {thread}"
        )
        assert not threads_draft.exists(), (
            "Threads draft must NOT be written when --format blog is the only "
            f"format passed. Found {threads_draft}"
        )

    def test_explicit_format_appends_to_default(self, tmp_git_repo: Path) -> None:
        """Passing ``--format`` AFTER relying on the default is a no-op for
        the default set — explicit values fully replace the default.

        This pins the semantics: defaults are a fallback for "no flag
        passed", NOT a hidden base that explicit flags add to. Power
        users wanting ``blog + release-notes`` (without x-thread or
        threads) write ``--format blog --format release-notes`` explicitly.
        """
        _seed_anchor_pool(tmp_git_repo)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--format",
                    "release-notes",
                    "--slug",
                    "replace-default",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout

        for sub, expected in (
            ("blog", True),
            ("release-notes", True),
            ("x-thread", False),
            ("threads", False),
        ):
            path = (
                tmp_git_repo
                / ".deviate"
                / "content"
                / "drafts"
                / sub
                / "replace-default.md"
            )
            if expected:
                assert path.is_file(), f"{sub} draft missing at {path}"
            else:
                assert not path.exists(), (
                    f"{sub} draft must NOT be written when explicit --format "
                    f"replaces default. Found {path}"
                )
