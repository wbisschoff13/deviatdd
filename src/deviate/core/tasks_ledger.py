from __future__ import annotations

import re
from pathlib import Path

from pydantic import ValidationError

from deviate.state.ledger import TaskRecord


_TASK_LINE_PATTERN = re.compile(r"^- (TSK-\d{3}-\d{2}): (.+)")
_MODE_PATTERN = re.compile(r"\*\*Mode\*\*:\s*(\S+)")


def generate_jsonl_from_md(tasks_md: Path, issue_id: str) -> list[dict]:
    content = tasks_md.read_text(encoding="utf-8")
    records: list[dict] = []
    current_id: str | None = None
    current_desc: str | None = None
    current_mode: str = "TDD"

    for line in content.splitlines():
        m = _TASK_LINE_PATTERN.match(line)
        if m:
            if current_id:
                records.append(
                    {
                        "id": current_id,
                        "issue_id": issue_id,
                        "description": current_desc,
                        "status": "PENDING",
                        "execution_mode": current_mode,
                    }
                )
            current_id = m.group(1)
            current_desc = m.group(2).strip()
            current_mode = "TDD"
        elif current_id:
            mode_m = _MODE_PATTERN.search(line)
            if mode_m:
                current_mode = mode_m.group(1)

    if current_id:
        records.append(
            {
                "id": current_id,
                "issue_id": issue_id,
                "description": current_desc,
                "status": "PENDING",
                "execution_mode": current_mode,
            }
        )

    return records


def validate_tasks_jsonl(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for i, record in enumerate(records):
        try:
            TaskRecord.model_validate(record)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(part) for part in err["loc"])
                errors.append(f"Record {i}: {loc}: {err['msg']}")
    return errors
