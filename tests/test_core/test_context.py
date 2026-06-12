from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from deviate.core.context import (
    ContextContract,
    enforce_agents_symlink,
    remove_stale_references,
    resolve_workspace_context,
)
from deviate.core.worktree import upsert_governance_block


class TestResolveWorkspaceContext:
    def test_valid_workspace_returns_ready(self, tmp_path: Path):
        (tmp_path / ".deviate").mkdir(parents=True)
        (tmp_path / ".deviate" / "config.toml").write_text('profile = "default"\n')
        (tmp_path / "specs").mkdir()
        contract = resolve_workspace_context(repo_root=tmp_path)
        assert contract.status == "READY"
        assert contract.repo_root == ""
        assert contract.deviate_path == ".deviate"
        assert contract.specs_path == "specs"
        assert contract.specs_active_issue is None
        assert contract.diagnostic is None
        assert isinstance(contract.timestamp, str)
        assert len(contract.timestamp) > 0

    def test_missing_deviate_returns_failure(self, tmp_path: Path):
        contract = resolve_workspace_context(repo_root=tmp_path)
        assert contract.status == "FAILURE"
        assert contract.diagnostic is not None
        assert "deviate" in contract.diagnostic.lower()

    def test_missing_specs_returns_ready_with_null_specs(self, tmp_path: Path):
        (tmp_path / ".deviate").mkdir(parents=True)
        (tmp_path / ".deviate" / "config.toml").write_text("")
        contract = resolve_workspace_context(repo_root=tmp_path)
        assert contract.status == "READY"
        assert contract.specs_path is None
        assert contract.specs_issues == []

    def test_paths_are_relative(self, tmp_path: Path):
        (tmp_path / ".deviate").mkdir(parents=True)
        (tmp_path / ".deviate" / "config.toml").write_text("")
        (tmp_path / "specs").mkdir()
        contract = resolve_workspace_context(repo_root=tmp_path)
        assert contract.repo_root == ""
        assert not contract.deviate_path.startswith("/")
        assert ".." not in contract.deviate_path

    def test_discovers_specs_issues(self, tmp_path: Path):
        (tmp_path / ".deviate").mkdir(parents=True)
        (tmp_path / ".deviate" / "config.toml").write_text("")
        (tmp_path / "specs" / "my-feature" / "issues").mkdir(parents=True)
        (tmp_path / "specs" / "my-feature" / "issues" / "001-issue.md").write_text("")
        (tmp_path / "specs" / "my-feature" / "issues" / "002-issue.md").write_text("")
        contract = resolve_workspace_context(repo_root=tmp_path)
        assert len(contract.specs_issues) == 2
        assert any("001-issue.md" in p for p in contract.specs_issues)
        assert any("002-issue.md" in p for p in contract.specs_issues)

    def test_json_serialization_round_trip(self, tmp_path: Path):
        (tmp_path / ".deviate").mkdir(parents=True)
        (tmp_path / ".deviate" / "config.toml").write_text("")
        contract = resolve_workspace_context(repo_root=tmp_path)
        data = json.loads(contract.model_dump_json())
        restored = ContextContract.model_validate(data)
        assert restored.status == contract.status
        assert restored.repo_root == contract.repo_root
        assert restored.deviate_path == contract.deviate_path
        assert restored.specs_path == contract.specs_path
        assert restored.diagnostic == contract.diagnostic
        assert restored.timestamp == contract.timestamp


class TestGovernanceUpsert:
    def test_replaces_governance_block_preserving_surroundings(
        self, tmp_git_repo: Path
    ):
        original = """# Project README

Some intro text.

## Technical Execution Context
Status: INIT
Tasks=Pending

## Another Section
Some content here.
"""
        fresh_block = "Tasks=Environment Preflight Passed: YES\nPrimary Technical Milestone: Scaffold"
        result = upsert_governance_block(
            content=original,
            block_header="## Technical Execution Context",
            fresh_block=fresh_block.strip(),
            repo=tmp_git_repo,
        )
        assert "## Technical Execution Context" in result
        assert "Tasks=Environment Preflight Passed: YES" in result
        assert "Tasks=Pending" not in result
        assert "## Another Section" in result
        assert "Some intro text." in result
        assert "# Project README" in result

    def test_missing_header_appends_block(self, tmp_git_repo: Path):
        original = "# Only README\nNo governance here.\n"
        fresh_block = "Tasks=New Task"
        result = upsert_governance_block(
            content=original,
            block_header="## Technical Execution Context",
            fresh_block=fresh_block,
            repo=tmp_git_repo,
        )
        assert "## Technical Execution Context" in result
        assert "Tasks=New Task" in result
        assert "# Only README" in result

    def test_replaces_only_target_block(self, tmp_git_repo: Path):
        original = """## Other Section
Content.

## Technical Execution Context
Old tasks.

## Another Section
More content.
"""
        fresh_block = "New tasks."
        result = upsert_governance_block(
            content=original,
            block_header="## Technical Execution Context",
            fresh_block=fresh_block,
            repo=tmp_git_repo,
        )
        assert result.count("## Technical Execution Context") == 1
        assert "Old tasks." not in result
        assert "New tasks." in result
        assert "## Other Section" in result
        assert "## Another Section" in result


class TestSymlinkEnforcement:
    def test_creates_symlink_when_agents_missing(self, tmp_path: Path):
        claude = tmp_path / "CLAUDE.md"
        claude.write_text("# Content")
        agents = tmp_path / "AGENTS.md"
        with patch("os.name", "posix"):
            enforce_agents_symlink(claude_path=claude, agents_path=agents)
        assert agents.is_symlink()
        assert agents.readlink() == claude
        assert agents.read_text() == "# Content"

    def test_noop_when_already_symlink(self, tmp_path: Path):
        claude = tmp_path / "CLAUDE.md"
        claude.write_text("# Content")
        agents = tmp_path / "AGENTS.md"
        agents.symlink_to(claude)
        with patch("os.name", "posix"):
            enforce_agents_symlink(claude_path=claude, agents_path=agents)
        assert agents.is_symlink()
        assert agents.readlink() == claude

    def test_replaces_with_symlink_when_content_matches(self, tmp_path: Path):
        claude = tmp_path / "CLAUDE.md"
        claude.write_text("# Same Content")
        agents = tmp_path / "AGENTS.md"
        agents.write_text("# Same Content")
        with patch("os.name", "posix"):
            enforce_agents_symlink(claude_path=claude, agents_path=agents)
        assert agents.is_symlink()
        assert agents.readlink() == claude

    def test_leaves_as_is_when_content_differs(self, tmp_path: Path):
        claude = tmp_path / "CLAUDE.md"
        claude.write_text("# Claude Content")
        agents = tmp_path / "AGENTS.md"
        agents.write_text("# Different Content")
        with patch("os.name", "posix"):
            enforce_agents_symlink(claude_path=claude, agents_path=agents)
        assert not agents.is_symlink()
        assert agents.read_text() == "# Different Content"

    def test_windows_copy_fallback_missing_agents(self, tmp_path: Path):
        claude = tmp_path / "CLAUDE.md"
        claude.write_text("# Windows Content")
        agents = tmp_path / "AGENTS.md"
        with patch("os.name", "nt"):
            enforce_agents_symlink(claude_path=claude, agents_path=agents)
        assert not agents.is_symlink()
        assert agents.read_text() == "# Windows Content"

    def test_windows_copy_when_content_matches(self, tmp_path: Path):
        claude = tmp_path / "CLAUDE.md"
        claude.write_text("# Same")
        agents = tmp_path / "AGENTS.md"
        agents.write_text("# Same")
        with patch("os.name", "nt"):
            enforce_agents_symlink(claude_path=claude, agents_path=agents)
        assert not agents.is_symlink()
        assert agents.read_text() == "# Same"


class TestStaleReferenceRemoval:
    STALE_PATTERNS = [
        "rgr run",
        "manage-tasks.sh",
        "sdd-parse-ast.sh",
        "get-test-config.sh",
        ".rgr/",
    ]

    def test_removes_exact_stale_lines(self, tmp_path: Path):
        content = """# AGENTS.md

Some content.

rgr run
manage-tasks.sh
sdd-parse-ast.sh
get-test-config.sh
.rgr/

More content here.
"""
        result = remove_stale_references(content, self.STALE_PATTERNS)
        lines = result.splitlines()
        assert "rgr run" not in lines
        assert "manage-tasks.sh" not in lines
        assert "sdd-parse-ast.sh" not in lines
        assert "get-test-config.sh" not in lines
        assert ".rgr/" not in lines
        assert "# AGENTS.md" in lines
        assert "Some content." in lines
        assert "More content here." in lines

    def test_preserves_substring_lines(self, tmp_path: Path):
        content = "# rgr run with extra context\nrgr run\nindependent line\n"
        result = remove_stale_references(content, self.STALE_PATTERNS)
        lines = result.splitlines()
        assert "# rgr run with extra context" in lines
        assert "rgr run" not in lines
        assert "independent line" in lines

    def test_no_stale_patterns_no_change(self, tmp_path: Path):
        content = "# Clean file\nNo stale patterns here.\n"
        result = remove_stale_references(content, self.STALE_PATTERNS)
        assert result == content

    def test_whitespace_trimmed_before_match(self, tmp_path: Path):
        content = "  rgr run  \nother line\n"
        result = remove_stale_references(content, self.STALE_PATTERNS)
        lines = result.splitlines()
        assert "rgr run" not in lines

    def test_preserves_adjacent_lines(self, tmp_path: Path):
        content = "before\nrgr run\nafter\n"
        result = remove_stale_references(content, self.STALE_PATTERNS)
        assert "before" in result
        assert "after" in result
        assert "rgr run" not in result.splitlines()
