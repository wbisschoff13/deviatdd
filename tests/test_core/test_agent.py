from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from deviate.state.config import AgentConfig, DeviateConfig


class TestAgentConfigModel:
    def test_agent_config_defaults(self):
        config = AgentConfig()
        assert config.backend == "opencode"
        assert config.timeout == 600

    def test_agent_config_custom_values(self):
        config = AgentConfig(backend="claude", timeout=300)
        assert config.backend == "claude"
        assert config.timeout == 300

    def test_agent_config_droid_backend(self):
        config = AgentConfig(backend="droid", timeout=120)
        assert config.backend == "droid"
        assert config.timeout == 120

    def test_agent_config_rejects_invalid_backend(self):
        with pytest.raises(ValidationError):
            AgentConfig(backend="invalid-backend")

    def test_agent_config_rejects_zero_timeout(self):
        with pytest.raises(ValidationError):
            AgentConfig(timeout=0)

    def test_agent_config_rejects_negative_timeout(self):
        with pytest.raises(ValidationError):
            AgentConfig(timeout=-1)

    def test_agent_config_in_deviate_config(self):
        deviate = DeviateConfig(agent=AgentConfig(backend="claude", timeout=300))
        assert deviate.agent.backend == "claude"
        assert deviate.agent.timeout == 300

    def test_agent_config_in_deviate_config_default(self):
        deviate = DeviateConfig()
        assert deviate.agent.backend == "opencode"
        assert deviate.agent.timeout == 600

    def test_agent_config_forbids_extra_fields(self):
        with pytest.raises(ValidationError):
            AgentConfig(backend="opencode", timeout=600, unknown_field="x")

    def test_agent_config_aider_backend_valid(self):
        config = AgentConfig(backend="aider")
        assert config.backend == "aider"

    def test_agent_config_aider_backend_with_config(self):
        from deviate.state.config import AiderConfig

        config = AgentConfig(
            backend="aider",
            aider=AiderConfig(model="deepseek", auto_commits=True),
        )
        assert config.aider is not None
        assert config.aider.model == "deepseek"
        assert config.aider.auto_commits is True

    def test_agent_config_aider_defaults_nested(self):
        config = AgentConfig(backend="aider")
        from deviate.state.config import AiderConfig

        assert isinstance(config.aider, AiderConfig)
        assert config.aider.model == "claude-sonnet-4-20250514"
        assert config.aider.auto_commits is False
        assert config.aider.yes_mode is True

    def test_agent_config_aider_in_deviate_config(self):
        from deviate.state.config import AiderConfig

        deviate = DeviateConfig(
            agent=AgentConfig(
                backend="aider",
                aider=AiderConfig(model="deepseek"),
            )
        )
        assert deviate.agent.backend == "aider"
        assert deviate.agent.aider.model == "deepseek"


class TestHandoverManifestModel:
    def test_handover_manifest_parsed_from_yaml(self):
        from deviate.core.agent import HandoverManifest

        manifest = HandoverManifest(
            phase="RED",
            status="TEST_WRITTEN_FAILING",
            test_file="tests/test_core/test_agent.py",
            verification_command="pytest tests/test_core/test_agent.py -v",
        )
        assert manifest.phase == "RED"
        assert manifest.status == "TEST_WRITTEN_FAILING"
        assert manifest.test_file == "tests/test_core/test_agent.py"
        assert (
            manifest.verification_command == "pytest tests/test_core/test_agent.py -v"
        )
        assert manifest.yellow_trigger is None

    def test_handover_manifest_yellow_trigger(self):
        from deviate.core.agent import HandoverManifest

        manifest = HandoverManifest(
            phase="GREEN",
            status="YELLOW_TRIGGERED",
            yellow_trigger=True,
            test_changes={"file": "test_x.py", "diff": "..."},
            rationale="Need to adjust assertion",
        )
        assert manifest.yellow_trigger is True
        assert manifest.test_changes == {"file": "test_x.py", "diff": "..."}
        assert manifest.rationale == "Need to adjust assertion"

    def test_handover_manifest_minimal_fields(self):
        from deviate.core.agent import HandoverManifest

        manifest = HandoverManifest(phase="RED", status="TEST_WRITTEN_FAILING")
        assert manifest.test_file is None
        assert manifest.verification_command is None
        assert manifest.yellow_trigger is None

    def test_handover_manifest_allows_extra_fields(self):
        from deviate.core.agent import HandoverManifest

        manifest = HandoverManifest(phase="RED", status="FAIL", unknown_field="x")
        assert manifest.phase == "RED"
        assert manifest.status == "FAIL"


class TestAgentBackendInvocation:
    def test_agent_successful_invocation(self):
        from deviate.core.agent import AgentBackend

        yaml_output = (
            "phase: RED\n"
            "status: TEST_WRITTEN_FAILING\n"
            "test_file: tests/test_core/test_agent.py\n"
            "verification_command: pytest tests/test_core/test_agent.py -v\n"
        )
        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (yaml_output.encode("utf-8"), b"")
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc):
            backend = AgentBackend()
            manifest = backend.invoke("test prompt")

        assert manifest.phase == "RED"
        assert manifest.status == "TEST_WRITTEN_FAILING"
        assert manifest.test_file == "tests/test_core/test_agent.py"

    def test_agent_backend_parses_yellow_handover(self):
        from deviate.core.agent import AgentBackend

        yaml_output = (
            "phase: GREEN\n"
            "status: YELLOW_TRIGGERED\n"
            "yellow_trigger: true\n"
            "test_changes:\n"
            "  file: test_agent.py\n"
            '  diff: "@@ -1,5 +1,6 @@"\n'
            "rationale: Need to widen assertion scope\n"
        )
        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (yaml_output.encode("utf-8"), b"")
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc):
            backend = AgentBackend()
            manifest = backend.invoke("test prompt")

        assert manifest.yellow_trigger is True
        assert manifest.phase == "GREEN"
        assert manifest.rationale == "Need to widen assertion scope"

    def test_agent_uses_opencode_command_default(self):
        from deviate.core.agent import AgentBackend

        yaml_output = "phase: RED\nstatus: TEST_WRITTEN_FAILING\n"
        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (yaml_output.encode("utf-8"), b"")
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            backend = AgentBackend()
            backend.invoke("test prompt")

        args, kwargs = mock_popen.call_args
        cmd_str = " ".join(args[0]) if isinstance(args[0], list) else str(args[0])
        assert "opencode run" in cmd_str

    def test_agent_backend_pipe_heredoc_stdin(self):
        from deviate.core.agent import AgentBackend

        yaml_output = "phase: RED\nstatus: TEST_WRITTEN_FAILING\n"
        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (yaml_output.encode("utf-8"), b"")
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            backend = AgentBackend()
            backend.invoke("test prompt")

        _, kwargs = mock_popen.call_args
        assert "stdin" in kwargs

    def test_agent_backend_respects_config_backend(self):
        from deviate.core.agent import AgentBackend

        yaml_output = "phase: RED\nstatus: TEST_WRITTEN_FAILING\n"
        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (yaml_output.encode("utf-8"), b"")
        mock_proc.returncode = 0

        with (
            patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
            patch(
                "deviate.core.agent.BACKEND_COMMANDS",
                {"claude": "claude -p"},
            ),
        ):
            config = AgentConfig(backend="claude", timeout=300)
            backend = AgentBackend(config=config)
            backend.invoke("test prompt")

        args, _ = mock_popen.call_args
        cmd_str = " ".join(args[0]) if isinstance(args[0], list) else str(args[0])
        assert "claude" in cmd_str


class TestAgentBackendErrors:
    def test_agent_timeout_retry(self):
        from deviate.core.agent import AgentBackend, AgentTimeoutError

        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="opencode run", timeout=10, output=b""
        )

        with (
            patch("subprocess.Popen", return_value=mock_proc),
            patch("time.sleep", return_value=None) as mock_sleep,
        ):
            backend = AgentBackend()
            with pytest.raises(AgentTimeoutError):
                backend.invoke("test prompt", timeout=10)

        assert mock_sleep.called
        sleep_args = mock_sleep.call_args[0]
        assert sleep_args[0] == 30

    def test_agent_timeout_retry_twice_then_raises(self):
        from deviate.core.agent import AgentBackend, AgentTimeoutError

        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="opencode run", timeout=10, output=b""
        )

        with (
            patch("subprocess.Popen", return_value=mock_proc),
            patch("time.sleep", return_value=None),
        ):
            backend = AgentBackend()
            with pytest.raises(AgentTimeoutError) as exc_info:
                backend.invoke("test prompt", timeout=10)

        assert (
            "timed out" in str(exc_info.value).lower()
            or "timeout" in str(exc_info.value).lower()
        )

    def test_agent_malformed_yaml(self):
        from deviate.core.agent import AgentBackend, MalformedHandoverManifestError

        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (b"not: valid: yaml: [\nbroken", b"")
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc):
            backend = AgentBackend()
            with pytest.raises(MalformedHandoverManifestError) as exc_info:
                backend.invoke("test prompt")

        assert (
            "yaml" in str(exc_info.value).lower()
            or "malformed" in str(exc_info.value).lower()
        )

    def test_agent_nonzero_exit(self):
        from deviate.core.agent import AgentBackend, AgentSubprocessError

        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (b"", b"command not found")
        mock_proc.returncode = 1

        with patch("subprocess.Popen", return_value=mock_proc):
            backend = AgentBackend()
            with pytest.raises(AgentSubprocessError) as exc_info:
                backend.invoke("test prompt")

        assert "command not found" in str(exc_info.value)

    def test_agent_empty_output(self):
        from deviate.core.agent import AgentBackend, EmptyOutputError

        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc):
            backend = AgentBackend()
            with pytest.raises(EmptyOutputError):
                backend.invoke("test prompt")

    def test_agent_binary_not_found(self):
        from deviate.core.agent import AgentBackend, AgentBinaryNotFoundError

        with patch("subprocess.Popen", side_effect=FileNotFoundError):
            backend = AgentBackend()
            with pytest.raises(AgentBinaryNotFoundError):
                backend.invoke("test prompt")

    def test_agent_timeout_error_is_exception(self):
        from deviate.core.agent import AgentTimeoutError

        assert issubclass(AgentTimeoutError, Exception)

    def test_agent_subprocess_error_captures_exit_code(self):
        from deviate.core.agent import (
            AgentSubprocessError,
            MalformedHandoverManifestError,
            AgentBinaryNotFoundError,
            EmptyOutputError,
        )

        assert issubclass(AgentSubprocessError, Exception)
        assert issubclass(MalformedHandoverManifestError, Exception)
        assert issubclass(AgentBinaryNotFoundError, Exception)
        assert issubclass(EmptyOutputError, Exception)


class TestAiderBackendInvocation:
    """AiderBackend: subprocess invocation, flag building, binary handling."""

    def test_aider_backend_invocation_default_flags(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        args = backend._build_aider_command(
            prompt="test prompt",
            aider_cfg=AiderConfig(),
            repo_root=tmp_path,
        )

        assert args[0] == "aider"
        assert "--message" in args
        msg_idx = args.index("--message")
        assert args[msg_idx + 1] == "test prompt"
        assert "--yes" in args
        assert "--no-suggest-shell-commands" in args
        assert "--no-auto-commits" in args
        assert "--model" in args
        model_idx = args.index("--model")
        assert args[model_idx + 1] == "claude-sonnet-4-20250514"

    def test_aider_backend_custom_model(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        cfg = AiderConfig(model="deepseek")
        args = backend._build_aider_command("prompt", cfg, tmp_path)

        model_idx = args.index("--model")
        assert args[model_idx + 1] == "deepseek"

    def test_aider_backend_auto_commits_true_omits_flag(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        cfg = AiderConfig(auto_commits=True)
        args = backend._build_aider_command("prompt", cfg, tmp_path)

        assert "--no-auto-commits" not in args

    def test_aider_backend_suggest_shell_commands_true_omits_flag(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        cfg = AiderConfig(suggest_shell_commands=True)
        args = backend._build_aider_command("prompt", cfg, tmp_path)

        assert "--no-suggest-shell-commands" not in args

    def test_aider_backend_yes_mode_false_omits_flag(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        cfg = AiderConfig(yes_mode=False)
        args = backend._build_aider_command("prompt", cfg, tmp_path)

        assert "--yes" not in args

    def test_aider_backend_not_found(self):
        from deviate.core.agent import AiderBackend, AgentBinaryNotFoundError

        with (
            patch("subprocess.run", side_effect=FileNotFoundError),
            patch("pathlib.Path.exists", return_value=True),
        ):
            config = AgentConfig(backend="aider")
            backend = AiderBackend(config=config)
            with pytest.raises(AgentBinaryNotFoundError):
                backend.invoke("test prompt")

    def test_aider_backend_read_files_from_config(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")
        (tmp_path / "notes.md").write_text("# Notes")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        cfg = AiderConfig(read_files=["specs/constitution.md", "notes.md"])
        args = backend._build_aider_command("prompt", cfg, tmp_path)

        read_indices = [i for i, a in enumerate(args) if a == "--read"]
        read_values = [args[i + 1] for i in read_indices]
        assert "specs/constitution.md" in read_values
        assert "notes.md" in read_values


class TestAiderBackendContextInjection:
    """AiderBackend: context injection via --read flags for constitution / CLAUDE.md."""

    def test_aider_backend_context_read_both_exist(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")
        (tmp_path / "CLAUDE.md").write_text("# CLAUDE")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        args = backend._build_aider_command("prompt", AiderConfig(), tmp_path)

        read_indices = [i for i, a in enumerate(args) if a == "--read"]
        read_values = [args[i + 1] for i in read_indices]
        assert "specs/constitution.md" in read_values
        assert "CLAUDE.md" in read_values

    def test_aider_backend_context_constitution_missing_aborts(self, tmp_path):
        from deviate.core.agent import AiderBackend, ConstitutionMissingError
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        with pytest.raises(ConstitutionMissingError):
            backend._build_aider_command("prompt", AiderConfig(), tmp_path)

    def test_aider_backend_context_claude_missing_skips(self, tmp_path):
        from deviate.core.agent import AiderBackend
        from deviate.state.config import AiderConfig

        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "constitution.md").write_text("# Constitution")

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        args = backend._build_aider_command("prompt", AiderConfig(), tmp_path)

        read_indices = [i for i, a in enumerate(args) if a == "--read"]
        read_values = [args[i + 1] for i in read_indices]
        assert "specs/constitution.md" in read_values
        assert "CLAUDE.md" not in read_values


class TestAiderBackendOutputParsing:
    """AiderBackend: output parsing from aider's chat-style output."""

    SAMPLE_SUCCESS = """\
Aider v0.75.0
Model: claude-sonnet-4-20250514
Added src/deviate/core/micro.py to the chat.
Applied edit to src/deviate/core/micro.py.
✓ All tests passed!
"""

    SAMPLE_FAILURE = """\
Aider v0.75.0
Model: claude-sonnet-4-20250514
Applied edit to src/deviate/core/micro.py.
Tests: 1 failed
FAILED test_micro.py::test_something - AssertionError: assert False
"""

    SAMPLE_AMBIGUOUS = """\
Aider v0.75.0
Model: claude-sonnet-4-20250514
Applied edit to src/deviate/core/micro.py.
No errors detected.
All changes applied successfully.
"""

    SAMPLE_MALFORMED = ""

    def test_aider_output_parse_all_tests_passed(self):
        from deviate.core.agent import AiderBackend

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        manifest = backend.parse_output(self.SAMPLE_SUCCESS, "aider")

        assert manifest.status == "PASS"

    def test_aider_output_parse_tests_failed(self):
        from deviate.core.agent import AiderBackend

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        manifest = backend.parse_output(self.SAMPLE_FAILURE, "aider")

        assert manifest.status == "FAIL"

    def test_aider_output_parse_ambiguous(self):
        from deviate.core.agent import AiderBackend

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        manifest = backend.parse_output(self.SAMPLE_AMBIGUOUS, "aider")

        assert manifest.status == "PASS"
        assert manifest.verification_result == "UNKNOWN"

    def test_aider_output_parse_malformed(self):
        from deviate.core.agent import AiderBackend, AiderParseError

        backend = AiderBackend(config=AgentConfig(backend="aider"))
        with pytest.raises(AiderParseError):
            backend.parse_output(self.SAMPLE_MALFORMED, "aider")


class TestAiderBackendPostGuard:
    """AiderBackend: post-invocation `mise run test` guard behavior."""

    def test_aider_post_guard_runs_mise_test(self):
        from deviate.core.agent import AiderBackend

        aider_result = MagicMock(spec=subprocess.CompletedProcess)
        aider_result.returncode = 0
        aider_result.stdout = "All tests passed"
        aider_result.stderr = ""

        guard_result = MagicMock(spec=subprocess.CompletedProcess)
        guard_result.returncode = 0
        guard_result.stdout = "1 passed"
        guard_result.stderr = ""

        with (
            patch(
                "subprocess.run", side_effect=[aider_result, guard_result]
            ) as mock_run,
            patch("pathlib.Path.exists", return_value=True),
        ):
            config = AgentConfig(backend="aider")
            backend = AiderBackend(config=config)
            manifest = backend.invoke("test prompt")

        assert mock_run.call_count == 2
        mise_call_args = mock_run.call_args_list[1][0][0]
        assert mise_call_args == ["mise", "run", "test"]
        assert manifest.status == "PASS"

    def test_aider_post_guard_catches_false_positive(self):
        from deviate.core.agent import AiderBackend

        aider_result = MagicMock(spec=subprocess.CompletedProcess)
        aider_result.returncode = 0
        aider_result.stdout = "All tests passed"
        aider_result.stderr = ""

        failed_guard = MagicMock(spec=subprocess.CompletedProcess)
        failed_guard.returncode = 1
        failed_guard.stdout = "1 failed"
        failed_guard.stderr = ""

        with (
            patch("subprocess.run", side_effect=[aider_result, failed_guard]),
            patch("pathlib.Path.exists", return_value=True),
        ):
            config = AgentConfig(backend="aider")
            backend = AiderBackend(config=config)
            manifest = backend.invoke("test prompt")

        assert manifest.status == "FAIL"

    def test_aider_nonzero_exit_aborts_immediately(self):
        from deviate.core.agent import AiderBackend, AgentSubprocessError

        failed_result = MagicMock(spec=subprocess.CompletedProcess)
        failed_result.returncode = 1
        failed_result.stdout = ""
        failed_result.stderr = "Error: something went wrong"

        with (
            patch("subprocess.run", return_value=failed_result),
            patch("pathlib.Path.exists", return_value=True),
        ):
            config = AgentConfig(backend="aider")
            backend = AiderBackend(config=config)
            with pytest.raises(AgentSubprocessError) as exc_info:
                backend.invoke("test prompt")

        assert "something went wrong" in str(exc_info.value)


class TestGetAgentBackend:
    def test_factory_returns_agent_backend_by_default(self):
        from deviate.core.agent import AgentBackend, get_agent_backend

        backend = get_agent_backend()
        assert isinstance(backend, AgentBackend)

    def test_factory_returns_agent_backend_for_opencode(self):
        from deviate.core.agent import AgentBackend, get_agent_backend

        backend = get_agent_backend(AgentConfig(backend="opencode"))
        assert isinstance(backend, AgentBackend)

    def test_factory_returns_agent_backend_for_claude(self):
        from deviate.core.agent import AgentBackend, get_agent_backend

        backend = get_agent_backend(AgentConfig(backend="claude"))
        assert isinstance(backend, AgentBackend)

    def test_factory_returns_aider_backend_for_aider(self):
        from deviate.core.agent import AiderBackend, get_agent_backend

        backend = get_agent_backend(AgentConfig(backend="aider"))
        assert isinstance(backend, AiderBackend)


class TestInvokeAgentDispatch:
    def test_invoke_agent_uses_factory_for_aider(self, tmp_path):
        from rich.console import Console
        from deviate.core.agent import HandoverManifest

        with (
            patch("deviate.cli.micro.get_agent_backend") as mock_factory,
            patch("deviate.cli.micro._save_agent_log"),
            patch(
                "deviate.cli.micro._make_output_handler", return_value=lambda x: None
            ),
        ):
            from deviate.cli.micro import _invoke_agent

            mock_backend = MagicMock()
            mock_manifest = HandoverManifest(phase="RED", status="TEST_WRITTEN_FAILING")
            mock_backend.invoke.return_value = mock_manifest
            mock_factory.return_value = mock_backend

            manifest, _ = _invoke_agent(
                "test prompt",
                Console(),
                backend_name="aider",
                task_id="TSK-004-99",
                phase="RED",
            )

            assert manifest is mock_manifest
            mock_factory.assert_called_once()
            call_config = mock_factory.call_args[0][0]
            assert call_config.backend == "aider"
