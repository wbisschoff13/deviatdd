from __future__ import annotations

import typer

from deviate.core.complexity import ComplexityGate  # noqa: F401 — used by GREEN impl

adhoc_app = typer.Typer()


@adhoc_app.command()
def pre(
    description: str = typer.Argument(help="Task description"),
    skip_gates: bool = typer.Option(
        False, "--skip-gates", help="Skip complexity gate check"
    ),
) -> None:
    """Classify and record an adhoc task."""
    typer.echo("adhoc pre stub")
    raise typer.Exit(code=1)


@adhoc_app.command()
def post(
    manifest: str = typer.Argument(help="Manifest ID to complete"),
) -> None:
    """Complete an adhoc task record."""
    typer.echo("adhoc post stub")
    raise typer.Exit(code=1)
