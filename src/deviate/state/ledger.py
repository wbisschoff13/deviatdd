from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class IssueRecord(BaseModel):
    id: str
    title: str
    status: Literal["SHARDED"]
    epic_slug: str
    issue_slug: str
    timestamp: datetime


def append_issue_record(record: IssueRecord, ledger_path: Path) -> bool:
    raise NotImplementedError
