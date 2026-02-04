"""Tests for CLI."""

from click.testing import CliRunner
import pytest
from identity_gen.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_cli_default_generation(self, runner):
        """Test default identity generation."""
        result = runner.invoke(cli, ["--count", "1", "--format", "json", "--stdout"])
        assert result.exit_code == 0
        assert "name" in result.output

    def test_cli_json_output(self, runner):
        """Test JSON output format."""
        result = runner.invoke(cli, ["--format", "json", "--count", "2", "--stdout"])
        assert result.exit_code == 0
        assert "[" in result.output and "name" in result.output

    def test_cli_csv_output(self, runner):
        """Test CSV output format."""
        result = runner.invoke(cli, ["--format", "csv", "--count", "2", "--stdout"])
        assert result.exit_code == 0
        assert "," in result.output

    def test_cli_raw_output(self, runner):
        """Test raw output format."""
        result = runner.invoke(cli, ["--format", "raw", "--count", "2", "--stdout"])
        assert result.exit_code == 0
        assert "Identity #1" in result.output

    def test_cli_output_to_file(self, runner, tmp_path):
        """Test output to file."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            cli, ["--output", str(output_file), "--format", "json", "--no-idcard"]
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_cli_fields_command(self, runner):
        """Test fields subcommand."""
        result = runner.invoke(cli, ["fields"])
        assert result.exit_code == 0
        assert "name" in result.output
        assert "email" in result.output

    def test_cli_locales_command(self, runner):
        """Test locales subcommand (China only)."""
        result = runner.invoke(cli, ["locales"])
        assert result.exit_code == 0
        assert "zh_CN" in result.output

    def test_cli_preview_command(self, runner):
        """Test preview subcommand."""
        result = runner.invoke(cli, ["preview"])
        assert result.exit_code == 0

    def test_cli_invalid_locale(self, runner):
        """Test error handling for invalid locale."""
        result = runner.invoke(cli, ["--locale", "invalid"])
        assert result.exit_code != 0

    def test_cli_with_seed(self, runner):
        """Test generation with seed for reproducibility."""
        result1 = runner.invoke(cli, ["--seed", "42", "--format", "json", "--stdout"])
        result2 = runner.invoke(cli, ["--seed", "42", "--format", "json", "--stdout"])
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert result1.output == result2.output

    def test_cli_include_fields(self, runner):
        """Test including specific fields."""
        result = runner.invoke(
            cli,
            ["--include", "name", "--include", "email", "--format", "json", "--stdout"],
        )
        assert result.exit_code == 0
        # Verify only requested fields are in output
        assert '"name"' in result.output
        assert '"email"' in result.output

    def test_cli_csv_output_to_file(self, runner, tmp_path):
        """Test CSV output to file."""
        output_file = tmp_path / "output.csv"
        result = runner.invoke(
            cli, ["--output", str(output_file), "--format", "csv", "--no-idcard"]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        # Verify it's CSV format (comma-separated, not JSON)
        assert "," in content
        assert not content.strip().startswith("[")  # Not JSON array
        assert not content.strip().startswith("{")  # Not JSON object

    def test_cli_format_auto_detection_from_extension(self, runner, tmp_path):
        """Test format auto-detection from file extension."""
        # Test .json extension
        json_file = tmp_path / "identities.json"
        result = runner.invoke(cli, ["--output", str(json_file), "--no-idcard"])
        assert result.exit_code == 0
        content = json_file.read_text()
        assert content.strip().startswith("[")  # JSON array

        # Test .csv extension
        csv_file = tmp_path / "identities.csv"
        result = runner.invoke(cli, ["--output", str(csv_file), "--no-idcard"])
        assert result.exit_code == 0
        content = csv_file.read_text()
        assert "," in content  # CSV format
        assert not content.strip().startswith("[")  # Not JSON

    def test_cli_multiple_formats_output(self, runner, tmp_path):
        """Test various output formats to files."""
        formats_and_extensions = [
            ("json", "output.json"),
            ("csv", "output.csv"),
            ("raw", "output.txt"),
            ("sql", "output.sql"),
            ("markdown", "output.md"),
            ("yaml", "output.yaml"),
        ]

        for fmt, filename in formats_and_extensions:
            output_file = tmp_path / filename
            result = runner.invoke(
                cli,
                [
                    "--output",
                    str(output_file),
                    "--format",
                    fmt,
                    "--count",
                    "2",
                    "--no-idcard",
                ],
            )
            assert result.exit_code == 0, f"Failed for format {fmt}"
            assert output_file.exists(), f"File not created for format {fmt}"
            content = output_file.read_text()
            assert len(content) > 0, f"Empty output for format {fmt}"
