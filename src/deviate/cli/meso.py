import typer
from rich.console import Console

console = Console()


def specify(
    issue_id: str = typer.Argument(..., help="Issue ID to specify"),
) -> None:
    pass
