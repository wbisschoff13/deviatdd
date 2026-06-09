from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def run_command(
    task_id: str = typer.Argument(..., help="Task ID (TNNN or TSK-NNN-NN format)"),
    all_tasks: bool = typer.Option(False, "--all", help="Run all CREATED tasks"),
) -> None:
    """Run dispatcher: route task by execution_mode to TDD cycle or execute phase."""
    console.print("[red]NOT_IMPLEMENTED[/] deviate run is not yet implemented")
    raise typer.Exit(code=1)
