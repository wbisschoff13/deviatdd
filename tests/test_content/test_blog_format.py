"""Tests for FLOW-12 blog-format synthesis.

Verifies Scenario 012-10 from ``specs/adhoc/issues/012-deviate-content.md``:

**Scenario 012-10**: Blog format draft references ``verdict_story`` anchor
**Given** fixture YAMLs including a ``judge`` record with a
``narrative_anchor.verdict_story`` field
**When** ``deviate content --format blog --slug my-post`` runs against the
fixture window
**Then** ``.deviate/content-drafts/blog/my-post.md`` is written, parses as
valid Markdown, and its opening paragraph contains the ``verdict_story``
text — verifying AC-ADHOC-012-10.

These tests use ``runner.invoke(cli, [...])`` to exercise the full public
CLI surface — the same surface a developer invokes from the terminal.
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


class TestBlogFormatSynthesis:
    """AC-ADHOC-012-10 — blog draft references the judge's ``verdict_story`` anchor."""

    def test_blog_format_draft_written_to_canonical_path(self, tmp_git_repo: Path):
        """`deviate content --format blog --slug my-post --window EPIC-X` writes the
        draft at .deviate/content-drafts/blog/my-post.md.
        """
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
            / "feat"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "judge.yaml"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(judge_yaml, encoding="utf-8")

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--slug",
                    "my-post",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"deviate content --format blog exited {result.exit_code}. stdout={result.stdout}"
        )
        draft = tmp_git_repo / ".deviate" / "content-drafts" / "blog" / "my-post.md"
        assert draft.is_file(), f"Draft not written at {draft}"

    def test_blog_format_intro_references_verdict_story(self, tmp_git_repo: Path):
        """The blog draft's opening paragraph contains the judge verdict_story text."""
        verdict_text = "We hardened the path-traversal surface end-to-end."
        judge_yaml = (
            "phase: judge\n"
            "status: PASS\n"
            "task_id: T-001\n"
            "files: []\n"
            "narrative_anchor:\n"
            f"  verdict_story: {verdict_text}\n"
        )
        target = (
            tmp_git_repo
            / ".deviate"
            / "feat"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "judge.yaml"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(judge_yaml, encoding="utf-8")

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--slug",
                    "verdict-post",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        draft = (
            tmp_git_repo / ".deviate" / "content-drafts" / "blog" / "verdict-post.md"
        )
        body = draft.read_text(encoding="utf-8")
        assert verdict_text in body, (
            f"verdict_story not present in blog draft. body[:400]={body[:400]!r}"
        )

    def test_blog_format_draft_parses_as_markdown(self, tmp_git_repo: Path):
        """The synthesized draft is a valid Markdown file (parses without exception
        and contains a markdown heading marker).
        """
        judge_yaml = (
            "phase: judge\n"
            "status: PASS\n"
            "task_id: T-001\n"
            "files: []\n"
            "narrative_anchor:\n"
            "  verdict_story: Another test verdict.\n"
        )
        target = (
            tmp_git_repo
            / ".deviate"
            / "feat"
            / "EPIC-X"
            / "ISS-001"
            / "T-001"
            / "judge.yaml"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(judge_yaml, encoding="utf-8")

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "blog",
                    "--slug",
                    "md-post",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        draft = tmp_git_repo / ".deviate" / "content-drafts" / "blog" / "md-post.md"
        body = draft.read_text(encoding="utf-8")
        assert body.startswith("#"), (
            f"Blog draft does not start with a markdown heading. body[:80]={body[:80]!r}"
        )
