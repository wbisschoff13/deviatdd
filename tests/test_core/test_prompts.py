from __future__ import annotations

from pathlib import Path

import pytest

from deviate.core.prompts import (
    interpolate,
    list_defaults,
    list_overrides,
    resolve_command,
    resolve_prompt,
)


class TestResolvePrompt:
    def test_resolve_prompt_override_before_default(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "auto").mkdir(parents=True)
        (package_dir / "auto").mkdir(parents=True)
        (override_dir / "auto" / "red.md").write_text("CUSTOM RED")
        (package_dir / "auto" / "red.md").write_text("DEFAULT RED")
        result = resolve_prompt(
            "auto/red.md", overrides_root=override_dir, package_root=package_dir
        )
        assert result == "CUSTOM RED"

    def test_resolve_prompt_silent_fallback(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "auto").mkdir(parents=True)
        (package_dir / "auto").mkdir(parents=True)
        (package_dir / "auto" / "red.md").write_text("DEFAULT RED")
        result = resolve_prompt(
            "auto/red.md", overrides_root=override_dir, package_root=package_dir
        )
        assert result == "DEFAULT RED"

    def test_resolve_prompt_not_found_raises(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "auto").mkdir(parents=True)
        (package_dir / "auto").mkdir(parents=True)
        with pytest.raises(FileNotFoundError):
            resolve_prompt(
                "auto/red.md", overrides_root=override_dir, package_root=package_dir
            )

    def test_resolve_prompt_partial_override_set(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "auto").mkdir(parents=True)
        (package_dir / "auto").mkdir(parents=True)
        (override_dir / "auto" / "red.md").write_text("CUSTOM RED")
        (package_dir / "auto" / "red.md").write_text("DEFAULT RED")
        (package_dir / "auto" / "green.md").write_text("DEFAULT GREEN")
        red_result = resolve_prompt(
            "auto/red.md", overrides_root=override_dir, package_root=package_dir
        )
        assert red_result == "CUSTOM RED"
        green_result = resolve_prompt(
            "auto/green.md", overrides_root=override_dir, package_root=package_dir
        )
        assert green_result == "DEFAULT GREEN"


class TestResolveCommand:
    def test_resolve_command_override_before_default(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "commands").mkdir(parents=True)
        (package_dir / "commands").mkdir(parents=True)
        (override_dir / "commands" / "deviate-red.md").write_text("CUSTOM")
        (package_dir / "commands" / "deviate-red.md").write_text("DEFAULT")
        result = resolve_command(
            "deviate-red", overrides_root=override_dir, package_root=package_dir
        )
        assert result == "CUSTOM"

    def test_resolve_command_falls_back_to_package(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "commands").mkdir(parents=True)
        (package_dir / "commands").mkdir(parents=True)
        (package_dir / "commands" / "deviate-red.md").write_text("DEFAULT")
        result = resolve_command(
            "deviate-red", overrides_root=override_dir, package_root=package_dir
        )
        assert result == "DEFAULT"


class TestInterpolate:
    def test_interpolate_resolves_dynamic_variables(self):
        template = "Task: ${TASK_DESCRIPTION} (ID: ${TASK_ID})"
        variables = {"TASK_DESCRIPTION": "Write tests", "TASK_ID": "T001"}
        result = interpolate(template, variables)
        assert result == "Task: Write tests (ID: T001)"


class TestListOverrides:
    def test_list_overrides_returns_only_customized(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "auto").mkdir(parents=True)
        (package_dir / "auto").mkdir(parents=True)
        (override_dir / "auto" / "red.md").write_text("CUSTOM CONTENT")
        (package_dir / "auto" / "red.md").write_text("DEFAULT CONTENT")
        result = list_overrides(overrides_root=override_dir, package_root=package_dir)
        assert "auto/red.md" in result


class TestListDefaults:
    def test_list_defaults_excludes_overrides(self, tmp_path: Path):
        override_dir = tmp_path / "override"
        package_dir = tmp_path / "package"
        (override_dir / "auto").mkdir(parents=True)
        (package_dir / "auto").mkdir(parents=True)
        (override_dir / "auto" / "red.md").write_text("CUSTOM")
        (package_dir / "auto" / "red.md").write_text("DEFAULT")
        (package_dir / "auto" / "green.md").write_text("DEFAULT GREEN")
        result = list_defaults(overrides_root=override_dir, package_root=package_dir)
        assert "auto/green.md" in result
        assert "auto/red.md" not in result
