from __future__ import annotations

import json
from pathlib import Path

import typer

context_app = typer.Typer(no_args_is_help=True, help="Context sync commands")


@context_app.command("pre")
def context_pre() -> None:
    """Crawl workspace and emit ContextContract JSON."""
    print(json.dumps({"status": "STUB"}))


@context_app.command("post")
def context_post(
    manifest: Path = typer.Argument(..., help="Path to ContextContract JSON file"),
) -> None:
    """Read manifest, sync governance, enforce symlink, remove stale refs, commit."""
