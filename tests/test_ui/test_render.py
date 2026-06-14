from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from rich.panel import Panel
from rich.table import Table

from deviate.ui.monitor import MarkdownStatus, TaskStatus
from deviate.ui.render import (
    build_task_table,
    emit_jsonl,
    is_interactive,
    render_agent_buffer,
    render_status_bar,
)


def _make_task(
    id: str,
    description: str = "test",
    marker: MarkdownStatus = MarkdownStatus.PENDING,
    phase: str = "",
    error_reason: str | None = None,
) -> TaskStatus:
    return TaskStatus(
        id=id,
        description=description,
        marker=marker,
        phase=phase,
        error_reason=error_reason,
    )


class TestTaskTable:
    def test_render_task_list(self) -> None:
        tasks = [
            _make_task("TSK-001", "Implement auth", MarkdownStatus.COMPLETED),
            _make_task("TSK-002", "Fix bug", MarkdownStatus.IN_PROGRESS, phase="GREEN"),
            _make_task("TSK-003", "Deploy", MarkdownStatus.PENDING),
        ]
        table = build_task_table(tasks)
        assert isinstance(table, Table)
        assert table.columns[0].header == "Marker"
        assert table.columns[1].header == "ID"
        assert table.columns[2].header == "Description"
        assert table.row_count == 3

    def test_render_task_list_empty(self) -> None:
        table = build_task_table([])
        assert isinstance(table, Table)
        assert table.row_count == 0


class TestAgentBuffer:
    def test_render_agent_buffer(self) -> None:
        lines = ["line 1", "line 2", "line 3"]
        panel = render_agent_buffer(lines)
        assert isinstance(panel, Panel)

    def test_render_agent_buffer_eviction(self) -> None:
        lines = [f"line {i}" for i in range(1, 7)]
        panel = render_agent_buffer(lines)
        assert isinstance(panel, Panel)

    def test_render_agent_buffer_truncation(self) -> None:
        long_line = "x" * 200
        lines = [long_line]
        panel = render_agent_buffer(lines)
        assert isinstance(panel, Panel)


class TestStatusBar:
    def test_render_status_bar(self) -> None:
        result = render_status_bar(3, 5, "GREEN")
        assert "Task 3 of 5" in result
        assert "Phase: GREEN" in result


class TestJsonlFallback:
    @patch.object(sys.stdout, "isatty", return_value=False)
    def test_render_no_tty_fallback(
        self, mock_isatty: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        emit_jsonl("task_started", task_id="TSK-001", phase="RED")
        captured = capsys.readouterr()
        assert captured.out.strip() != ""

    @patch.object(sys.stdout, "isatty", return_value=False)
    def test_render_jsonl_event_fields(
        self, mock_isatty: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        emit_jsonl("agent_output", task_id="T1", phase="RED", line="test line")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert "event" in parsed
        assert "task_id" in parsed
        assert "phase" in parsed
        assert "line" in parsed
        assert "timestamp" in parsed

    @patch.object(sys.stdout, "isatty", return_value=False)
    def test_render_jsonl_agent_output_event(
        self, mock_isatty: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        emit_jsonl("agent_output", task_id="T1", phase="RED", line="Running tests...")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["event"] == "agent_output"
        assert parsed["task_id"] == "T1"
        assert parsed["phase"] == "RED"
        assert parsed["line"] == "Running tests..."
        assert "timestamp" in parsed


class TestIsInteractive:
    def test_is_interactive_returns_bool(self) -> None:
        result = is_interactive()
        assert isinstance(result, bool)
