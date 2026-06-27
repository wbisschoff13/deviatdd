"""Tests for AC-ADHOC-012-14: ``.deviate/.gitignore`` excludes runtime-state dirs.

Scenario 012-14 from ``specs/adhoc/issues/012-deviate-content.md`` —
``.deviate/.gitignore`` excludes both ``/feat/`` (handover persistence
surface per FLOW-11) and ``/content-drafts/`` (synthesis output per
FLOW-12) so neither participates in ``git diff`` evaluation. The
gitignore is the gate that keeps Content Capture out of the append-only
ledger protocol (per ``specs/_product/architecture.md:213``).

Per ``specs/adhoc/issues/012-deviate-content.md`` Edge Cases and
Boundaries: "``.deviate/feat/`` directory missing: ``persist_handover()``
creates parent directories via ``pathlib.Path.parent.mkdir(parents=True,
exist_ok=True)``." The gitignore entries are the inverse guarantee —
the directories may exist on disk but never in git.

The gitignore lives at ``<workdir>/.deviate/.gitignore`` — inside the
``.deviate/`` directory itself, so the entries use *paths relative to
that directory*: ``/feat/`` excludes ``.deviate/feat/`` and
``/content-drafts/`` excludes ``.deviate/content-drafts/``.
"""

from __future__ import annotations

from pathlib import Path


# Canonical gitignore location — the file lives INSIDE .deviate/, so
# its entries are paths relative to that directory.
_GITIGNORE_PATH = Path(".deviate") / ".gitignore"

# Canonical entries per ``specs/plans/deviate-content.md:17-19``.
# Each must appear as an exact line (no prefix characters, anchored
# at start-of-line).
_RUNTIME_STATE_ENTRIES: tuple[str, ...] = (
    "/feat/",
    "/content-drafts/",
)

# Original 6 entries authored by ``_ensure_gitignore`` at
# ``src/deviate/cli/__init__.py:539`` — preserved to guard against
# regressions where a future implementation drops them.
_LEGACY_ENTRIES: tuple[str, ...] = (
    "session.json",
    "artifacts/",
    "prompts.log",
    "reports/",
    "rollback.jsonl",
    "logs/",
)


def _read_gitignore_lines() -> list[str]:
    """Return the gitignore file's lines, skipping the trailing newline split."""
    text = _GITIGNORE_PATH.read_text(encoding="utf-8")
    # Split on \n and drop the trailing empty line from the final \n.
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines


class TestDotDeviateGitignoreRuntimeState:
    """AC-ADHOC-012-14 — the gitignore excludes both runtime-state dirs."""

    def test_gitignore_file_exists(self) -> None:
        """``.deviate/.gitignore`` is a file on disk in the worktree."""
        assert _GITIGNORE_PATH.exists(), (
            f"Missing gitignore at {_GITIGNORE_PATH} — Content Capture "
            "subsystem requires it to be in place from TSK-012-01 onward."
        )
        assert _GITIGNORE_PATH.is_file(), (
            f"{_GITIGNORE_PATH} exists but is not a regular file"
        )

    def test_gitignore_excludes_feat_directory(self) -> None:
        """The gitignore contains the ``/feat/`` entry as an exact line."""
        lines = _read_gitignore_lines()
        assert "/feat/" in lines, (
            f"Expected '/feat/' as an exact line in {_GITIGNORE_PATH}; got: {lines}"
        )

    def test_gitignore_excludes_content_drafts_directory(self) -> None:
        """The gitignore contains the ``/content-drafts/`` entry as an exact line."""
        lines = _read_gitignore_lines()
        assert "/content-drafts/" in lines, (
            f"Expected '/content-drafts/' as an exact line in {_GITIGNORE_PATH}; "
            f"got: {lines}"
        )

    def test_gitignore_carries_both_runtime_state_entries(self) -> None:
        """Both ``/feat/`` and ``/content-drafts/`` are present simultaneously."""
        lines = _read_gitignore_lines()
        missing = [entry for entry in _RUNTIME_STATE_ENTRIES if entry not in lines]
        assert not missing, (
            f"Missing runtime-state entries in {_GITIGNORE_PATH}: {missing}. "
            "Both '/feat/' (FLOW-11 handover persistence) and '/content-drafts/' "
            "(FLOW-12 synthesis drafts) must be excluded from git tracking."
        )


class TestDotDeviateGitignoreIdempotency:
    """The runtime-state entries appear exactly once each (idempotent append)."""

    def test_feat_entry_appears_exactly_once(self) -> None:
        lines = _read_gitignore_lines()
        count = lines.count("/feat/")
        assert count == 1, (
            f"Expected '/feat/' to appear exactly once in {_GITIGNORE_PATH}; "
            f"got {count} occurrences. Duplicates indicate a non-idempotent "
            "append operation."
        )

    def test_content_drafts_entry_appears_exactly_once(self) -> None:
        lines = _read_gitignore_lines()
        count = lines.count("/content-drafts/")
        assert count == 1, (
            f"Expected '/content-drafts/' to appear exactly once in "
            f"{_GITIGNORE_PATH}; got {count} occurrences."
        )


class TestDotDeviateGitignoreNonRegressions:
    """Pre-existing gitignore entries are preserved alongside the new ones."""

    def test_legacy_entries_are_still_present(self) -> None:
        """The 6 original entries authored by ``_ensure_gitignore`` remain."""
        lines = _read_gitignore_lines()
        missing = [entry for entry in _LEGACY_ENTRIES if entry not in lines]
        assert not missing, (
            f"Legacy gitignore entries missing from {_GITIGNORE_PATH}: "
            f"{missing}. The Content Capture append must not displace the "
            "6 baseline entries authored by _ensure_gitignore."
        )

    def test_gitignore_has_at_least_eight_entries(self) -> None:
        """6 legacy + 2 runtime-state = at least 8 lines."""
        lines = _read_gitignore_lines()
        assert len(lines) >= 8, (
            f"Expected {_GITIGNORE_PATH} to have at least 8 entries "
            f"(6 legacy + 2 runtime-state); got {len(lines)}: {lines}"
        )


class TestDotDeviateGitignoreFunctionalBehavior:
    """Functional verification — the entries actually keep dirs out of git.

    These tests operate on isolated temp dirs to satisfy the AGENTS.md
    Git Isolation Principle (no git commands inside the real project
    repo). Each test seeds a temp git repo with a hand-written
    ``.deviate/.gitignore`` mirroring the canonical file, then asserts
    that ``git check-ignore`` reports the runtime-state dirs as ignored.
    """

    def test_feat_directory_is_ignored_in_git(self, tmp_path: Path) -> None:
        """A file under ``.deviate/feat/`` reports as git-ignored."""
        import subprocess

        from tests.conftest import _git_env

        repo = tmp_path
        deviate_dir = repo / ".deviate"
        deviate_dir.mkdir(parents=True)
        (deviate_dir / ".gitignore").write_text(
            "\n".join(_LEGACY_ENTRIES + _RUNTIME_STATE_ENTRIES) + "\n",
            encoding="utf-8",
        )
        # Seed an actual file under the runtime-state path.
        feat_file = deviate_dir / "feat" / "EPIC-X" / "ISS-001" / "red.yaml"
        feat_file.parent.mkdir(parents=True)
        feat_file.write_text("phase: red\n", encoding="utf-8")

        subprocess.run(
            ["git", "init", "-q"],
            cwd=repo,
            env=_git_env(),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test"],
            cwd=repo,
            env=_git_env(),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            env=_git_env(),
            check=True,
        )
        # ``git check-ignore -v <path>`` prints the matching pattern +
        # exits 0 when the path IS ignored; exits 1 when not ignored.
        # Use the *gitignore-relative* form because the gitignore is
        # at .deviate/.gitignore (not the repo root).
        result = subprocess.run(
            ["git", "check-ignore", "-v", ".deviate/feat/EPIC-X/ISS-001/red.yaml"],
            cwd=repo,
            env=_git_env(),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected .deviate/feat/EPIC-X/ISS-001/red.yaml to be "
            f"git-ignored; got exit {result.returncode}. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    def test_content_drafts_directory_is_ignored_in_git(self, tmp_path: Path) -> None:
        """A file under ``.deviate/content-drafts/`` reports as git-ignored."""
        import subprocess

        from tests.conftest import _git_env

        repo = tmp_path
        deviate_dir = repo / ".deviate"
        deviate_dir.mkdir(parents=True)
        (deviate_dir / ".gitignore").write_text(
            "\n".join(_LEGACY_ENTRIES + _RUNTIME_STATE_ENTRIES) + "\n",
            encoding="utf-8",
        )
        draft_file = deviate_dir / "content-drafts" / "blog" / "my-post.md"
        draft_file.parent.mkdir(parents=True)
        draft_file.write_text("# draft\n", encoding="utf-8")

        subprocess.run(
            ["git", "init", "-q"],
            cwd=repo,
            env=_git_env(),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test"],
            cwd=repo,
            env=_git_env(),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            env=_git_env(),
            check=True,
        )
        result = subprocess.run(
            [
                "git",
                "check-ignore",
                "-v",
                ".deviate/content-drafts/blog/my-post.md",
            ],
            cwd=repo,
            env=_git_env(),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected .deviate/content-drafts/blog/my-post.md to be "
            f"git-ignored; got exit {result.returncode}. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
