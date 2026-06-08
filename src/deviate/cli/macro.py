from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer

from deviate.cli._common import (
    _halt,
    _handle_missing_dot_dir,
    _handle_transition_error,
    _load_manifest,
    _validate_constitution,
    console,
)
from deviate.core.commit import commit_artifact
from deviate.core.epic import (
    allocate_feature_bucket,
    discover_epic,
    resolve_active_feature,
)
from deviate.core.prd import extract_prd_requirements
from deviate.state.config import SessionState, TransitionViolationError
from deviate.state.ledger import IssueRecord, _read_ledger, append_issue_record


def _load_and_transition(phase: str) -> tuple[SessionState, Path]:
    dot_dir = Path(".deviate")
    if not dot_dir.exists():
        _handle_missing_dot_dir(phase)
    session_path = dot_dir / "session.json"
    session = SessionState.load(session_path)
    try:
        session = session.transition_to(phase)
    except TransitionViolationError as e:
        _handle_transition_error(phase, e)
    return session, session_path


def _load_session(phase: str) -> tuple[SessionState, Path]:
    dot_dir = Path(".deviate")
    if not dot_dir.exists():
        _handle_missing_dot_dir(phase)
    session_path = dot_dir / "session.json"
    session = SessionState.load(session_path)
    if session.current_phase != phase:
        _halt(phase, f"session is in '{session.current_phase}' not '{phase}'")
    return session, session_path


def _save_session(session: SessionState, session_path: Path, phase: str) -> None:
    session.save(session_path)
    console.print(f"[green]{phase}[/] session advanced to {phase} phase")


def _resolve_specs_root() -> Path:
    return Path("specs")


def _emit_contract(
    phase: str,
    session: SessionState,
    session_path: Path,
    **extra: str | int | bool | None,
) -> None:
    contract = {"phase": phase, **extra}
    console.print(json.dumps(contract, indent=2))
    _save_session(session, session_path, phase)


def _compute_next_issue_id(ledger_path: Path) -> str:
    records = _read_ledger(ledger_path)
    numbers: list[int] = []
    for data in records:
        iid = data.get("issue_id", "")
        if isinstance(iid, str) and iid.startswith("ISS-"):
            try:
                numbers.append(int(iid.split("-")[1]))
            except (ValueError, IndexError):
                continue
    next_num = (max(numbers) + 1) if numbers else 1
    return f"ISS-{next_num:03d}"


# ---------------------------------------------------------------------------
# Explore
# ---------------------------------------------------------------------------

explore_app = typer.Typer(no_args_is_help=True, help="Explore phase commands")


@explore_app.command("pre")
def explore_pre(
    problem: str = typer.Argument(..., help="Problem description"),
    slug: str = typer.Option(..., "--slug", help="Feature bucket slug"),
) -> None:
    """Allocate feature bucket and register scratch entry"""
    _validate_constitution("EXPLORE")

    session, session_path = _load_and_transition("EXPLORE")

    bucket = allocate_feature_bucket(slug)
    console.print(f"[green]BUCKET_CREATED[/] {bucket}")

    record = IssueRecord(
        issue_id=str(uuid.uuid4()),
        type="feature",
        title=problem,
        status="DRAFT",
        source_file=str(_resolve_specs_root() / slug / "explore.md"),
        timestamp=datetime.now(timezone.utc),
    )
    ledger_path = _resolve_specs_root() / "issues.jsonl"
    appended = append_issue_record(record, ledger_path)
    if appended:
        console.print(f"[green]LEDGER_APPENDED[/] {record.issue_id}")
    else:
        console.print(
            f"[yellow]LEDGER_IDEMPOTENT[/] record for {record.issue_id} already exists"
        )

    _emit_contract(
        "EXPLORE",
        session,
        session_path,
        problem=problem,
        slug=slug,
        bucket_path=str(bucket),
        issue_id=record.issue_id,
    )


@explore_app.command("post")
def explore_post() -> None:
    """Validate explore.md and commit"""
    session, session_path = _load_session("EXPLORE")

    explore_files = list(_resolve_specs_root().rglob("explore.md"))
    if not explore_files:
        _halt("EXPLORE", "no explore.md found to commit")

    for f in explore_files:
        if f.read_text(encoding="utf-8").strip():
            commit_artifact(f, f"EXPLORE: {f.parent.name}", repo=Path.cwd())
            console.print(f"[green]COMMITTED[/] {f}")

    _save_session(session, session_path, "EXPLORE")


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------

research_app = typer.Typer(no_args_is_help=True, help="Research phase commands")


@research_app.command("pre")
def research_pre(
    epic: str = typer.Argument("", help="Epic slug"),
) -> None:
    """Gate on explore.md, validate constitution"""
    specs_root = _resolve_specs_root()
    epic_slug = epic if epic else resolve_active_feature(specs_root)
    if not epic_slug:
        _halt("RESEARCH", "no active feature bucket found")

    explore_path = specs_root / epic_slug / "explore.md"
    if not explore_path.exists():
        _halt("RESEARCH", "explore.md not found in feature bucket")

    _validate_constitution("RESEARCH")

    session, session_path = _load_and_transition("RESEARCH")

    _emit_contract(
        "RESEARCH",
        session,
        session_path,
        epic_slug=epic_slug,
        explore_path=str(explore_path),
    )


@research_app.command("post")
def research_post() -> None:
    """Scan for constitutional violations, commit artifacts"""
    session, session_path = _load_session("RESEARCH")

    specs_root = _resolve_specs_root()
    epic_slug = resolve_active_feature(specs_root)
    if epic_slug:
        for artifact in ("design.md", "data-model.md"):
            path = specs_root / epic_slug / artifact
            if path.exists() and path.read_text(encoding="utf-8").strip():
                commit_artifact(
                    path, f"RESEARCH: {artifact} for {epic_slug}", repo=Path.cwd()
                )
                console.print(f"[green]COMMITTED[/] {path}")

    _save_session(session, session_path, "RESEARCH")


# ---------------------------------------------------------------------------
# PRD
# ---------------------------------------------------------------------------

prd_app = typer.Typer(no_args_is_help=True, help="PRD phase commands")


@prd_app.command("pre")
def prd_pre() -> None:
    """Discover epic slug, resolve upstream artifacts"""
    specs_root = _resolve_specs_root()
    epic_slug = discover_epic(specs_root)
    if not epic_slug:
        _halt("PRD", "no epic discovered")

    required = ["design.md", "data-model.md"]
    missing = [a for a in required if not (specs_root / epic_slug / a).exists()]
    if missing:
        paths = "\n  - ".join(str(specs_root / epic_slug / a) for a in missing)
        _halt("PRD", f"missing upstream artifacts\n  - {paths}")

    session, session_path = _load_and_transition("PRD")

    _emit_contract("PRD", session, session_path, epic_slug=epic_slug)


@prd_app.command("post")
def prd_post(
    manifest: Path = typer.Argument(..., help="Path to manifest JSON file"),
) -> None:
    """Read manifest, validate PRD, commit"""
    session, session_path = _load_session("PRD")

    manifest_data = _load_manifest(manifest, "PRD")

    epic_slug = manifest_data.get("epic_slug", "")
    if not epic_slug:
        _halt("PRD", "manifest missing 'epic_slug'")

    prd_path = _resolve_specs_root() / epic_slug / "prd.md"
    if not prd_path.exists():
        _halt("PRD", f"prd.md not found at {prd_path}")

    reqs = extract_prd_requirements(prd_path)
    manifest_reqs = manifest_data.get("prd_requirements", [])
    missing = [r for r in manifest_reqs if r not in reqs]
    if missing:
        console.print(
            f"[yellow]PRD_WARNING[/] missing requirements in prd.md: {missing}"
        )

    try:
        sha = commit_artifact(prd_path, f"PRD: {epic_slug}", repo=Path.cwd())
        console.print(f"[green]COMMITTED[/] prd.md at {sha[:8]}")
    except Exception as e:
        _halt("PRD", f"commit failed - {e}")

    _save_session(session, session_path, "PRD")


# ---------------------------------------------------------------------------
# Shard
# ---------------------------------------------------------------------------

shard_app = typer.Typer(no_args_is_help=True, help="Shard phase commands")


@shard_app.command("pre")
def shard_pre() -> None:
    """Discover epic, resolve PRD, compute next_issue_id"""
    specs_root = _resolve_specs_root()
    epic_slug = discover_epic(specs_root)
    if not epic_slug:
        _halt("SHARD", "no epic discovered")

    prd_path = specs_root / epic_slug / "prd.md"
    if not prd_path.exists():
        _halt("SHARD", f"prd.md not found at {prd_path}")

    ledger_path = _resolve_specs_root() / "issues.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    next_issue_id = _compute_next_issue_id(ledger_path)

    session, session_path = _load_and_transition("SHARD")

    _emit_contract(
        "SHARD",
        session,
        session_path,
        epic_slug=epic_slug,
        prd_path=str(prd_path),
        next_issue_id=next_issue_id,
    )


@shard_app.command("post")
def shard_post(
    manifest: Path = typer.Argument(..., help="Path to shard manifest JSON file"),
) -> None:
    """Validate shard output, register issues as BACKLOG, reset session to IDLE"""
    session, session_path = _load_session("SHARD")

    manifest_data = _load_manifest(manifest, "SHARD")

    issues = manifest_data.get("issues", [])
    ledger_path = _resolve_specs_root() / "issues.jsonl"

    for issue_data in issues:
        record = IssueRecord(
            issue_id=issue_data.get("issue_id", str(uuid.uuid4())),
            type=issue_data.get("type", "feature"),
            title=issue_data.get("title", ""),
            status="BACKLOG",
            source_file=issue_data.get("source_file", ""),
            timestamp=datetime.now(timezone.utc),
        )
        appended = append_issue_record(record, ledger_path)
        if appended:
            console.print(
                f"[green]LEDGER_APPENDED[/] {record.issue_id} ({record.title})"
            )
        else:
            console.print(
                f"[yellow]LEDGER_IDEMPOTENT[/] {record.issue_id} already exists"
            )

    try:
        session = session.transition_to("IDLE")
    except TransitionViolationError as e:
        _handle_transition_error("SHARD", e)

    session.save(session_path)
    console.print("[green]SHARD_POST[/] session reset to IDLE")
