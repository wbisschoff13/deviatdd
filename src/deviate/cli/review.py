from __future__ import annotations

import json

import typer

from deviate.cli._common import console

review_app = typer.Typer(no_args_is_help=True)


@review_app.command()
def pre() -> None:
    """Gather git state and governance context for review."""
    contract = {"status": "READY"}
    print(json.dumps(contract, indent=2))


@review_app.command()
def post() -> None:
    """Persist review report and mark review complete."""
    console.print("[green]OK[/] no-op")
