from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich.console import Console

console = Console()

_LEDGER_GLOB = "specs/**/tasks.jsonl"


def _read_ledger_records(ledger_file: Path) -> list[dict]:
    records: list[dict] = []
    try:
        with open(ledger_file, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(json.loads(stripped))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return records


def _resolve_issue_number(task_id: str) -> str | None:
    m = re.match(r"^T(\d{3})$", task_id)
    if m:
        return m.group(1)
    m = re.match(r"^TSK-(\d{3})-\d{2}$", task_id)
    if m:
        return m.group(1)
    return None


def _find_issue_record(root: Path, issue_number: str) -> tuple[dict, Path] | None:
    for ledger_file in sorted(root.glob(_LEDGER_GLOB)):
        for record in _read_ledger_records(ledger_file):
            if record.get("issue_id") == f"ISS-{issue_number}":
                return record, ledger_file
    return None


def _find_all_pending_tasks(root: Path) -> list[tuple[dict, Path]]:
    results: list[tuple[dict, Path]] = []
    for ledger_file in sorted(root.glob(_LEDGER_GLOB)):
        for record in _read_ledger_records(ledger_file):
            if record.get("status") == "PENDING":
                results.append((record, ledger_file))
    return results


def _update_ledger_status(ledger_path: Path, task_uuid: str, new_status: str) -> bool:
    records: list[str] = []
    found = False
    try:
        with open(ledger_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    records.append(line)
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    records.append(line)
                    continue
                if record.get("id") == task_uuid:
                    record["status"] = new_status
                    found = True
                    records.append(json.dumps(record, ensure_ascii=False) + "\n")
                else:
                    records.append(line)
    except FileNotFoundError:
        return False

    with open(ledger_path, "w", encoding="utf-8") as f:
        f.writelines(records)
    return found


def _run_tdd_cycle(task: dict, ledger_path: Path, c: Console) -> None:
    tid = task.get("id", "?")
    # TODO: TDD cycle stubs — replace with actual RED/GREEN/REFACTOR phase
    #       invocations once micro-layer phase functions exist.
    c.print(f"  [bold blue]RED →[/] {tid}")
    _update_ledger_status(ledger_path, tid, "RED")
    c.print(f"  [bold green]GREEN →[/] {tid}")
    _update_ledger_status(ledger_path, tid, "GREEN")
    c.print(f"  [bold yellow]REFACTOR →[/] {tid}")
    _update_ledger_status(ledger_path, tid, "REFACTOR")
    _update_ledger_status(ledger_path, tid, "COMPLETED")
    c.print(f"  [bold green]COMPLETED[/] {tid}")


def _run_execute_phase(task: dict, ledger_path: Path, c: Console) -> None:
    tid = task.get("id", "?")
    # TODO: execute phase stub — replace with actual IMMEDIATE-mode
    #       implementation handler once micro-layer phase functions exist.
    c.print(f"  [bold green]EXECUTE →[/] {tid}")
    _update_ledger_status(ledger_path, tid, "COMPLETED")
    c.print(f"  [bold green]COMPLETED[/] {tid}")


def _dispatch_task(task: dict, ledger_path: Path, c: Console) -> None:
    mode = task.get("execution_mode", "TDD")
    c.print(f"[cyan]Processing {task.get('id', '?')} ({mode})[/]")
    if mode == "TDD":
        _run_tdd_cycle(task, ledger_path, c)
    else:
        _run_execute_phase(task, ledger_path, c)


def _run_single(task_id: str, root: Path, c: Console) -> None:
    issue_number = _resolve_issue_number(task_id)
    if issue_number is None:
        c.print(f"[red]TASK_NOT_FOUND[/] Unrecognised task ID format: {task_id}")
        raise typer.Exit(code=1)

    result = _find_issue_record(root, issue_number)
    if result is None:
        c.print(f"[red]TASK_NOT_FOUND[/] No task matching {task_id}")
        raise typer.Exit(code=1)

    task, ledger_file = result
    status = task.get("status", "PENDING")

    if status == "COMPLETED":
        c.print(f"[yellow]TASK_ALREADY_DONE[/] {task_id} is already completed")
        raise typer.Exit(code=0)

    _dispatch_task(task, ledger_file, c)


def _run_all(root: Path, c: Console) -> None:
    pending = _find_all_pending_tasks(root)
    if not pending:
        c.print("[yellow]No PENDING tasks found[/]")
        raise typer.Exit(code=0)
    for task, ledger_file in pending:
        _dispatch_task(task, ledger_file, c)


def run_command(
    task_id: str | None = typer.Argument(
        None, help="Task ID (TNNN or TSK-NNN-NN format)"
    ),
    all_tasks: bool = typer.Option(False, "--all", help="Run all PENDING tasks"),
) -> None:
    """Run dispatcher: route task by execution_mode to TDD cycle or execute phase."""
    if not task_id and not all_tasks:
        console.print("[red]ERROR[/] Provide a task ID or use --all")
        raise typer.Exit(code=1)

    root = Path.cwd()

    if all_tasks:
        _run_all(root, console)
        raise typer.Exit(code=0)

    assert task_id is not None
    _run_single(task_id, root, console)
