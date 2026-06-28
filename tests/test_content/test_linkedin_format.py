"""Tests for FLOW-12 linkedin-format synthesis (Slice B).

Verifies the LinkedIn format template shipped at
``src/deviate/prompts/content/linkedin.md``.

Per the build-in-public research, LinkedIn is the resume-discoverability
cross-post channel: the personal website is the central brand asset and
LinkedIn provides the inbound audience that the website otherwise lacks.
The LinkedIn voice is first-person, career-relevant, and ends on a
question to drive comments in the first hour (LinkedIn's algorithm
rewards early-engagement).
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
        '  invariant_protected: "LinkedIn surfaces career-relevant framing"\n'
    )
    target.write_text(yaml_text, encoding="utf-8")


class TestLinkedInFormatSynthesis:
    """Slice B — LinkedIn format renders and surfaces the resume-grade frame."""

    def test_linkedin_draft_written_to_canonical_path(self, tmp_git_repo: Path) -> None:
        """`--format linkedin` writes the draft at .deviate/content/drafts/linkedin/<slug>.md."""
        _seed_judge_handover(
            tmp_git_repo,
            verdict_text="LinkedIn draft path check: 4 sections, ~200 words.",
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "linkedin",
                    "--slug",
                    "linkedin-1",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"deviate content --format linkedin exited {result.exit_code}. "
            f"stdout={result.stdout}"
        )
        draft = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / "linkedin"
            / "linkedin-1.md"
        )
        assert draft.is_file(), f"Draft not written at {draft}"

    def test_linkedin_intro_references_verdict_story(self, tmp_git_repo: Path) -> None:
        """LinkedIn draft \"What I shipped\" blockquote references the seeded verdict_story."""
        verdict = "LinkedIn surfaces the lead anchor in the first section."
        _seed_judge_handover(tmp_git_repo, verdict_text=verdict)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "linkedin",
                    "--slug",
                    "linkedin-verdict",
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
            / "linkedin"
            / "linkedin-verdict.md"
        )
        body = draft.read_text(encoding="utf-8")
        assert verdict in body, (
            f"verdict_story not present in linkedin draft. body[:400]={body[:400]!r}"
        )

    def test_linkedin_contains_signature_sections(self, tmp_git_repo: Path) -> None:
        """LinkedIn draft carries the 4-section resume-grade frame.

        Per the research, the LinkedIn voice is:
        - \"What I shipped\" — outcome-led opener (2-3 sentences)
        - \"Why it matters for builders\" — career or workflow framing
        - \"The technical bit\" — brief technical walkthrough
        - \"Open to builders\" — question-driven closer for comments
        """
        _seed_judge_handover(
            tmp_git_repo,
            verdict_text="Section check: outcome / why / technical / open.",
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    "linkedin",
                    "--slug",
                    "linkedin-sections",
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
            / "linkedin"
            / "linkedin-sections.md"
        )
        body = draft.read_text(encoding="utf-8")
        for section in (
            "What I shipped",
            "Why it matters for builders",
            "The technical bit",
            "Open to builders",
        ):
            assert section in body, (
                f"linkedin draft missing signature section '{section}'. "
                f"body[:400]={body[:400]!r}"
            )

    def test_linkedin_template_uses_canonical_placeholders(self) -> None:
        """LinkedIn template uses the canonical placeholder contract."""
        from deviate.core.synthesis import load_template

        template = load_template("linkedin")
        for placeholder in ("{{title}}", "{{verdict_story}}"):
            assert placeholder in template, (
                f"linkedin template missing canonical placeholder '{placeholder}'"
            )
