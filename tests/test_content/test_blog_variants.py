"""Tests for FLOW-12 blog-variant synthesis (Slice B).

Verifies the three research-backed blog format variants shipped under
``src/deviate/prompts/content/``:

* ``blog-saha`` — 5-section Saha et al. 2026 reflective template
  (Project → Issue → Codebase → Challenges → Solution + Takeaway).
  Resume-grade voice. Use for process retrospectives.
* ``blog-devrel`` — 4-section DevRel Bridge 2024 tutorial template
  (Intro → Background → Main Content → Conclusion + Takeaway).
  Stripe / Cloudflare engineering blog voice. Use for capability launches.
* ``blog-narrative`` — Problem → Attempt → Failure → Pivot → Insight → CTA
  framework-essay template. Use for decision-rationale essays.

All three variants share the same placeholder contract as ``blog.md``:
``{{title}}``, ``{{verdict_story}}``, ``{{phase_summary}}``,
``{{invariant_protected}}``. The synthesis layer substitutes them via
``str.replace`` (``src/deviate/core/synthesis.py::render_template``).

Each variant test:
1. Asserts the format value is accepted by ``--format`` (no error / draft written).
2. Asserts the rendered draft references the seeded ``verdict_story`` text.
3. Asserts the rendered draft contains the variant's signature section headings.
"""

from __future__ import annotations

from contextlib import chdir
from pathlib import Path

import pytest
from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


_BLOG_VARIANT_FORMATS: list[tuple[str, tuple[str, ...]]] = [
    (
        "blog-saha",
        # Saha 2026 5-section template headings.
        (
            "About the project",
            "The issue",
            "Codebase overview",
            "Challenges",
            "Solution",
        ),
    ),
    (
        "blog-devrel",
        # DevRel Bridge 2024 4-section template headings.
        ("Introduction", "Background", "Main Content", "Conclusion"),
    ),
    (
        "blog-narrative",
        # Narrative arc: Problem → Attempt → Failure → Pivot → Insight → CTA.
        ("Problem", "Attempt", "Failure", "Pivot", "Insight", "CTA"),
    ),
]


def _seed_judge_handover(repo: Path, *, verdict_text: str) -> None:
    """Seed a single ``judge`` YAML handover under EPIC-X/ISS-001/T-001."""
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
        '  invariant_protected: "path-traversal guard at .deviate/content/handovers/"\n'
    )
    target.write_text(yaml_text, encoding="utf-8")


@pytest.mark.parametrize(("format_name", "expected_headings"), _BLOG_VARIANT_FORMATS)
class TestBlogVariantSynthesis:
    """Slice B — each blog variant loads, renders, and surfaces its signature sections."""

    def test_variant_draft_written_to_canonical_path(
        self, tmp_git_repo: Path, format_name: str, expected_headings: tuple[str, ...]
    ) -> None:
        """`--format <variant>` writes the draft at .deviate/content/drafts/<variant>/<slug>.md."""
        verdict = (
            f"We shipped the {format_name} variant for the build-in-public playbook."
        )
        _seed_judge_handover(tmp_git_repo, verdict_text=verdict)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    format_name,
                    "--slug",
                    f"{format_name}-post",
                    "--window",
                    "EPIC-X",
                ],
            )

        assert result.exit_code == 0, (
            f"deviate content --format {format_name} exited {result.exit_code}. "
            f"stdout={result.stdout}"
        )
        draft = (
            tmp_git_repo
            / ".deviate"
            / "content"
            / "drafts"
            / format_name
            / f"{format_name}-post.md"
        )
        assert draft.is_file(), f"Draft not written at {draft}"

    def test_variant_intro_references_verdict_story(
        self, tmp_git_repo: Path, format_name: str, expected_headings: tuple[str, ...]
    ) -> None:
        """The variant draft contains the seeded ``verdict_story`` text."""
        verdict = f"Saha-meets-DevRel: {format_name} surfaces the lead anchor verbatim."
        _seed_judge_handover(tmp_git_repo, verdict_text=verdict)

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    format_name,
                    "--slug",
                    f"{format_name}-verdict",
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
            / format_name
            / f"{format_name}-verdict.md"
        )
        body = draft.read_text(encoding="utf-8")
        assert verdict in body, (
            f"verdict_story not present in {format_name} draft. "
            f"body[:400]={body[:400]!r}"
        )

    def test_variant_contains_signature_section_headings(
        self, tmp_git_repo: Path, format_name: str, expected_headings: tuple[str, ...]
    ) -> None:
        """The variant draft carries its signature section headings (per the research template)."""
        _seed_judge_handover(
            tmp_git_repo,
            verdict_text=f"Signature-heading check for {format_name}.",
        )

        with chdir(tmp_git_repo):
            result = runner.invoke(
                cli,
                [
                    "content",
                    "--format",
                    format_name,
                    "--slug",
                    f"{format_name}-sections",
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
            / format_name
            / f"{format_name}-sections.md"
        )
        body = draft.read_text(encoding="utf-8")
        for heading in expected_headings:
            assert heading in body, (
                f"{format_name} draft missing signature section heading "
                f"'{heading}'. body[:400]={body[:400]!r}"
            )


class TestBlogVariantTemplateSchema:
    """Schema-level contract: each blog-variant template exists and uses the canonical placeholders."""

    @pytest.mark.parametrize(("format_name", "_expected"), _BLOG_VARIANT_FORMATS)
    def test_variant_template_file_exists(
        self, format_name: str, _expected: tuple[str, ...]
    ) -> None:
        """Each variant has a template file at ``src/deviate/prompts/content/<format>.md``."""
        import importlib.resources

        from deviate.prompts import content as content_pkg

        path = importlib.resources.files(content_pkg).joinpath(f"{format_name}.md")
        assert path.is_file(), f"Template file not found: {path}"

    @pytest.mark.parametrize(("format_name", "_expected"), _BLOG_VARIANT_FORMATS)
    def test_variant_template_uses_canonical_placeholders(
        self, format_name: str, _expected: tuple[str, ...]
    ) -> None:
        """Each variant template uses the canonical {{title}} / {{verdict_story}} placeholders."""
        from deviate.core.synthesis import load_template

        template = load_template(format_name)
        for placeholder in ("{{title}}", "{{verdict_story}}"):
            assert placeholder in template, (
                f"{format_name} template missing canonical placeholder '{placeholder}'"
            )
