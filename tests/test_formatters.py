"""Tests for formatters."""

import json

import pytest
from identity_gen.formatters import IdentityFormatter
from identity_gen.models import Identity, OutputFormat


class TestIdentityFormatter:
    """Tests for IdentityFormatter."""

    @pytest.fixture
    def sample_identities(self):
        """Create sample identities for testing."""
        return [
            Identity(name="John Doe", email="john@example.com"),
            Identity(name="Jane Smith", email="jane@example.com"),
        ]

    def test_format_json(self, sample_identities):
        """Test JSON formatting."""
        formatted = IdentityFormatter.format_json(sample_identities)
        data = json.loads(formatted)
        assert len(data) == 2
        assert data[0]["name"] == "John Doe"

    def test_format_json_filtered(self, sample_identities):
        """Test JSON formatting with field filtering."""
        formatted = IdentityFormatter.format_json(
            sample_identities, include_fields={"name"}
        )
        data = json.loads(formatted)
        assert "name" in data[0]
        assert "email" not in data[0]

    def test_format_csv(self, sample_identities):
        """Test CSV formatting."""
        formatted = IdentityFormatter.format_csv(sample_identities)
        assert "John Doe" in formatted
        assert "john@example.com" in formatted

    def test_format_csv_empty(self):
        """Test CSV formatting with empty list."""
        formatted = IdentityFormatter.format_csv([])
        assert formatted == ""

    def test_format_table(self, sample_identities):
        """Test table formatting."""
        formatted = IdentityFormatter.format_table(sample_identities)
        assert "John Doe" in formatted
        assert "Jane Smith" in formatted

    def test_format_table_empty(self):
        """Test table formatting with empty list."""
        formatted = IdentityFormatter.format_table([])
        assert "No identities" in formatted

    def test_format_raw(self, sample_identities):
        """Test raw text formatting."""
        formatted = IdentityFormatter.format_raw(sample_identities)
        assert "Identity #1" in formatted
        assert "John Doe" in formatted

    def test_format_method_json(self, sample_identities):
        """Test generic format method with JSON."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.JSON)
        data = json.loads(formatted)
        assert len(data) == 2

    def test_format_method_csv(self, sample_identities):
        """Test generic format method with CSV."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.CSV)
        assert "John Doe" in formatted

    def test_format_method_table(self, sample_identities):
        """Test generic format method with table."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.TABLE)
        assert "John Doe" in formatted

    def test_format_method_raw(self, sample_identities):
        """Test generic format method with raw."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.RAW)
        assert "Identity #1" in formatted

    def test_write_output_stdout(self, sample_identities, capsys):
        """Test writing to stdout."""
        formatted = IdentityFormatter.format_json(sample_identities)
        IdentityFormatter.write_output(formatted)
        captured = capsys.readouterr()
        assert "John Doe" in captured.out

    def test_write_output_file(self, sample_identities, tmp_path):
        """Test writing to file."""
        output_file = tmp_path / "output.json"
        formatted = IdentityFormatter.format_json(sample_identities)
        IdentityFormatter.write_output(formatted, str(output_file))

        content = output_file.read_text()
        assert "John Doe" in content
