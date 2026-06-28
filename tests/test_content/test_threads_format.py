"""Tests for FLOW-12 threads-format synthesis (Slice B).

Verifies the Threads format template shipped at
``src/deviate/prompts/content/threads.md``.

Per the build-in-public research, Threads is a distinct platform from X:
long-form narrative tolerance (paragraphs of 200-500 chars), visual
support for code-snippet screenshots from the AST parser output, lower
saturation for technical content than X.

The Threads template follows the Problem → Attempt → Result → Insight →
Open Question narrative arc, with mandatory numbers in the Result
section and a question-driven closer for reply engagement.
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


def _seed_judge_handover(repo: Path, *, verdict_text: str) -> None:
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
    yaml_text = (
        "phase: judge\n"
        "status: PASS\n"
        "task_id: T-001\n"
        "files: []\n"
        "narrative_anchor:\n"
        f"  verdict_story: {verdict_text}\n"
        '  invariant_protected: "FLOW-11 capture path is gitignored runtime state"\n'
    )
    target.write_text(yaml_text, encoding="utf-8")


class TestThreadsFormatSynthesis:
    """Slice B — Threads format renders and surfaces the narrative arc."""

    def test_threads_draft_written_to_canonical_path(self, tmp_git_repo: Path) -> None:
        """`--format threads` writes the draft at .deviate/content/drafts/threads/<slug>.md."""
        _seed_judge_handover(
            tmp_git_repo,
            verdict_text="Threads draft path check: 1 paragraph, 1 conclusion.",
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "threads",
                    "--slug",
                    "threads-1",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"deviate content --format threads exited {result.exit_code}. stdout={result.stdout}"
        )
        draft = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "threads"
            / "threads-1.md"
        )
        assert draft.is_file(), f"Draft not written at {draft}"

    def test_threads_intro_references_verdict_story(self, tmp_git_repo: Path) -> None:
        """Threads draft TL;DR blockquote references the seeded verdict_story."""
        verdict = "Threads TL;DR surfaces the lead anchor verbatim."
        _seed_judge_handover(tmp_git_repo, verdict_text=verdict)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "threads",
                    "--slug",
                    "threads-verdict",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        draft = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "threads"
            / "threads-verdict.md"
        )
        body = draft.read_text(encoding="utf-8")
        assert verdict in body, (
            f"verdict_story not present in threads draft. body[:400]={body[:400]!r}"
        )

    def test_threads_contains_signature_narrative_arc(self, tmp_git_repo: Path) -> None:
        """Threads draft carries the 5-section narrative arc (TL;DR / What I tried /
        Result / Insight / Open question).

        Per the research, Threads tolerates long-form narrative and rewards
        posts that end on a question (drives reply engagement).
        """
        _seed_judge_handover(
            tmp_git_repo,
            verdict_text="Narrative-arc check: 5 sections, end on a question.",
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "threads",
                    "--slug",
                    "threads-arc",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, result.stdout
        draft = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "threads"
            / "threads-arc.md"
        )
        body = draft.read_text(encoding="utf-8")
        for section in ("TL;DR", "What I tried", "Result", "Insight", "Open question"):
            assert section in body, (
                f"threads draft missing narrative section '{section}'. "
                f"body[:400]={body[:400]!r}"
            )

    def test_threads_template_uses_canonical_placeholders(self) -> None:
        """Threads template uses the canonical placeholder contract."""
        from deviate.core.synthesis import load_template

        template = load_template("threads")
        for placeholder in ("{{title}}", "{{verdict_story}}", "{{phase_summary}}"):
            assert placeholder in template, (
                f"threads template missing canonical placeholder '{placeholder}'"
            )
