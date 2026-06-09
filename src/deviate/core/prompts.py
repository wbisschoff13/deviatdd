from __future__ import annotations

from pathlib import Path


def resolve_prompt(
    name: str,
    overrides_root: Path | None = None,
    package_root: Path | None = None,
) -> str:
    raise NotImplementedError


def resolve_command(
    name: str,
    overrides_root: Path | None = None,
    package_root: Path | None = None,
) -> str:
    raise NotImplementedError


def interpolate(template: str, variables: dict[str, str]) -> str:
    raise NotImplementedError


def list_overrides(overrides_root: Path, package_root: Path) -> list[str]:
    raise NotImplementedError


def list_defaults(overrides_root: Path, package_root: Path) -> list[str]:
    raise NotImplementedError
