from contextlib import chdir
from pathlib import Path

from typer.testing import CliRunner

from deviate.cli import cli

runner = CliRunner()


class TestInitCommand:
    def test_init_creates_dotfile_structure(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output
            assert (workdir / ".deviate" / "config.toml").exists()
            assert (workdir / ".deviate" / "session.json").exists()

    def test_init_creates_constitution(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            result = runner.invoke(cli, ["init", "--generate-constitution"])
            assert result.exit_code == 0, result.output
            constitution_path = workdir / "specs" / "constitution.md"
            assert constitution_path.exists()
            content = constitution_path.read_text()
            assert "${PROJECT_NAME}" not in content
            assert "${REPO_ROOT}" not in content

    def test_init_appends_governance_to_nonexistent_file(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output
            claude_path = workdir / "CLAUDE.md"
            assert claude_path.exists()
            content = claude_path.read_text()
            assert "## DeviaTDD Orchestration Rules" in content

    def test_init_overwrites_governance_block_when_exists(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            claude_path = workdir / "CLAUDE.md"
            existing_content = (
                "# My Project\n\n"
                "## DeviaTDD Orchestration Rules\n"
                "Old content\n\n"
                "## Other Section\n"
                "Preserved content\n"
            )
            claude_path.write_text(existing_content)

            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output

            content = claude_path.read_text()
            assert "Old content" not in content
            assert "Preserved content" in content
            assert "## DeviaTDD Orchestration Rules" in content
            assert "## Other Section" in content

    def test_init_skip_existing_dotfiles(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            dotfile_dir = workdir / ".deviate"
            dotfile_dir.mkdir()
            config_path = dotfile_dir / "config.toml"
            original_content = 'profile = "custom"\n'
            config_path.write_text(original_content)

            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output
            assert config_path.read_text() == original_content
            assert "skip" in result.output.lower() or "already" in result.output.lower()

    def test_init_recover_partial_scaffold(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            dotfile_dir = workdir / ".deviate"
            dotfile_dir.mkdir()
            config_path = dotfile_dir / "config.toml"
            config_path.write_text('profile = "default"\n')
            session_path = dotfile_dir / "session.json"

            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output
            assert session_path.exists()

    def test_init_prompt_scaffolding_creates_auto_dir(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output
            auto_dir = workdir / ".deviate" / "prompts" / "auto"
            assert auto_dir.is_dir()
            import importlib.resources

            pkg_auto = importlib.resources.files("deviate.prompts.auto")
            expected_files = [f.name for f in pkg_auto.iterdir() if f.suffix == ".md"]
            for fname in expected_files:
                target = auto_dir / fname
                assert target.exists(), f"{fname} not found in .deviate/prompts/auto/"
                expected = (pkg_auto / fname).read_text(encoding="utf-8")
                actual = target.read_text(encoding="utf-8")
                assert actual == expected

    def test_init_prompt_scaffolding_creates_commands_dir(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0, result.output
            commands_dir = workdir / ".deviate" / "prompts" / "commands"
            assert commands_dir.is_dir()
            import importlib.resources

            pkg_commands = importlib.resources.files("deviate.prompts.commands")
            expected_files = [
                f.name for f in pkg_commands.iterdir() if f.suffix == ".md"
            ]
            assert len(expected_files) == 18
            for fname in expected_files:
                target = commands_dir / fname
                assert target.exists(), (
                    f"{fname} not found in .deviate/prompts/commands/"
                )
                expected = (pkg_commands / fname).read_text(encoding="utf-8")
                actual = target.read_text(encoding="utf-8")
                assert actual == expected

    def test_init_prompt_scaffolding_idempotent(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            result1 = runner.invoke(cli, ["init"])
            assert result1.exit_code == 0
            auto_dir = workdir / ".deviate" / "prompts" / "auto"
            modified_file = auto_dir / "red.md"
            modified_content = "MODIFIED CONTENT"
            modified_file.write_text(modified_content)
            result2 = runner.invoke(cli, ["init"])
            assert result2.exit_code == 0, result2.output
            assert modified_file.read_text() == modified_content

    def test_init_prompt_scaffolding_skip_message(self, tmp_path: Path):
        with chdir(tmp_path):
            result1 = runner.invoke(cli, ["init"])
            assert result1.exit_code == 0
            result2 = runner.invoke(cli, ["init"])
            assert "prompts/ already exists, skipping" in result2.output

    def test_init_refresh_prompts_prompts_backup(self, tmp_path: Path):
        with chdir(tmp_path):
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["init", "--refresh-prompts"], input="\n")
            assert "Back up existing overrides?" in result.output

    def test_init_refresh_prompts_with_backup(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            runner.invoke(cli, ["init"])
            auto_dir = workdir / ".deviate" / "prompts" / "auto"
            modified_file = auto_dir / "red.md"
            modified_file.write_text("USER MODIFIED")
            result = runner.invoke(cli, ["init", "--refresh-prompts"], input="y\n")
            assert result.exit_code == 0, result.output
            bak_dirs = list((workdir / ".deviate").glob("prompts.bak/*/"))
            assert len(bak_dirs) == 1
            bak_auto = bak_dirs[0] / "auto" / "red.md"
            assert bak_auto.exists()
            assert bak_auto.read_text() == "USER MODIFIED"
            import importlib.resources

            pkg_auto = importlib.resources.files("deviate.prompts.auto")
            pkg_red = (pkg_auto / "red.md").read_text(encoding="utf-8")
            assert (auto_dir / "red.md").read_text() == pkg_red

    def test_init_refresh_prompts_no_backup(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            runner.invoke(cli, ["init"])
            auto_dir = workdir / ".deviate" / "prompts" / "auto"
            modified_file = auto_dir / "red.md"
            modified_file.write_text("USER MODIFIED")
            result = runner.invoke(cli, ["init", "--refresh-prompts"], input="N\n")
            assert result.exit_code == 0, result.output
            bak_dirs = list((workdir / ".deviate").glob("prompts.bak/*/"))
            assert len(bak_dirs) == 0
            import importlib.resources

            pkg_auto = importlib.resources.files("deviate.prompts.auto")
            pkg_red = (pkg_auto / "red.md").read_text(encoding="utf-8")
            assert (auto_dir / "red.md").read_text() == pkg_red

    def test_init_refresh_prompts_no_flag_does_not_overwrite(self, tmp_path: Path):
        with chdir(tmp_path):
            workdir = tmp_path
            runner.invoke(cli, ["init"])
            auto_dir = workdir / ".deviate" / "prompts" / "auto"
            modified_file = auto_dir / "red.md"
            modified_content = "USER MODIFIED"
            modified_file.write_text(modified_content)
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert modified_file.read_text() == modified_content

    def test_init_scaffolding_within_performance_budget(self, tmp_path: Path):
        import time

        with chdir(tmp_path):
            start = time.monotonic()
            result = runner.invoke(cli, ["init"])
            elapsed = time.monotonic() - start
            assert result.exit_code == 0
            assert elapsed < 0.5
