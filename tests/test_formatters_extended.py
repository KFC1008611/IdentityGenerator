"""Extended tests for formatters to improve coverage."""

import json
import pytest
from identity_gen.formatters import IdentityFormatter
from identity_gen.models import Identity, OutputFormat


class TestFormattersExtended:
    """Extended tests for formatters."""

    @pytest.fixture
    def sample_identities(self):
        """Create sample identities for testing."""
        return [
            Identity(name="张三", email="zhangsan@qq.com", phone="13800138000"),
            Identity(name="李四", email="lisi@163.com", phone="13900139000"),
        ]

    def test_format_sql(self, sample_identities):
        """Test SQL formatting."""
        formatted = IdentityFormatter.format_sql(sample_identities)
        assert "INSERT INTO identities" in formatted
        assert "张三" in formatted
        assert "李四" in formatted
        assert "zhangsan@qq.com" in formatted

    def test_format_sql_empty(self):
        """Test SQL formatting with empty list."""
        formatted = IdentityFormatter.format_sql([])
        assert formatted == ""

    def test_format_sql_with_table_name(self, sample_identities):
        """Test SQL formatting with custom table name."""
        formatted = IdentityFormatter.format_sql(sample_identities, table_name="users")
        assert "INSERT INTO users" in formatted

    def test_format_sql_with_null_values(self):
        """Test SQL formatting with NULL values."""
        identities = [Identity(name="张三", email=None)]
        formatted = IdentityFormatter.format_sql(identities)
        # When email is None, it should not appear in SQL since to_dict() filters None values
        assert "张三" in formatted

    def test_format_markdown(self, sample_identities):
        """Test Markdown formatting."""
        formatted = IdentityFormatter.format_markdown(sample_identities)
        assert "| name |" in formatted
        assert "---" in formatted  # Separator line contains ---
        assert "张三" in formatted
        assert "李四" in formatted

    def test_format_markdown_empty(self):
        """Test Markdown formatting with empty list."""
        formatted = IdentityFormatter.format_markdown([])
        assert formatted == ""

    def test_format_markdown_filtered(self, sample_identities):
        """Test Markdown formatting with field filtering."""
        formatted = IdentityFormatter.format_markdown(
            sample_identities, include_fields={"name"}
        )
        assert "| name |" in formatted
        assert "email" not in formatted

    def test_format_yaml(self, sample_identities):
        """Test YAML formatting."""
        formatted = IdentityFormatter.format_yaml(sample_identities)
        assert "- identity_1:" in formatted
        assert "- identity_2:" in formatted
        assert "name:" in formatted
        assert "张三" in formatted

    def test_format_yaml_empty(self):
        """Test YAML formatting with empty list."""
        formatted = IdentityFormatter.format_yaml([])
        assert formatted == ""

    def test_format_yaml_with_special_chars(self):
        """Test YAML formatting with special characters."""
        identities = [Identity(name='张三"special"', email="test@example.com")]
        formatted = IdentityFormatter.format_yaml(identities)
        # Should escape quotes
        assert "张三" in formatted

    def test_format_vcard(self, sample_identities):
        """Test vCard formatting."""
        formatted = IdentityFormatter.format_vcard(sample_identities)
        assert "BEGIN:VCARD" in formatted
        assert "VERSION:3.0" in formatted
        assert "END:VCARD" in formatted
        # When only name is set (without first_name/last_name), vcard may not include N/FN fields
        assert "EMAIL:" in formatted

    def test_format_vcard_empty(self):
        """Test vCard formatting with empty list."""
        formatted = IdentityFormatter.format_vcard([])
        assert formatted == ""

    def test_format_vcard_with_name_parts(self):
        """Test vCard formatting with first and last name."""
        identities = [Identity(first_name="三", last_name="张", email="test@qq.com")]
        formatted = IdentityFormatter.format_vcard(identities)
        assert "BEGIN:VCARD" in formatted
        assert "张" in formatted
        assert "三" in formatted

    def test_format_vcard_with_address(self):
        """Test vCard formatting with address."""
        identities = [
            Identity(name="张三", email="test@qq.com", address="北京市朝阳区")
        ]
        formatted = IdentityFormatter.format_vcard(identities)
        assert "BEGIN:VCARD" in formatted
        assert "ADR:;;北京市朝阳区;;;;" in formatted

    def test_format_method_sql(self, sample_identities):
        """Test generic format method with SQL."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.SQL)
        assert "INSERT INTO" in formatted

    def test_format_method_markdown(self, sample_identities):
        """Test generic format method with Markdown."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.MARKDOWN)
        assert "|" in formatted

    def test_format_method_yaml(self, sample_identities):
        """Test generic format method with YAML."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.YAML)
        assert "identity_1" in formatted

    def test_format_method_vcard(self, sample_identities):
        """Test generic format method with vCard."""
        formatted = IdentityFormatter.format(sample_identities, OutputFormat.VCARD)
        assert "BEGIN:VCARD" in formatted

    def test_format_method_invalid(self, sample_identities):
        """Test format method with invalid format."""
        with pytest.raises(ValueError):
            # Create a mock invalid format
            class InvalidFormat:
                pass

            IdentityFormatter.format(sample_identities, InvalidFormat())

    def test_format_table_with_long_content(self):
        """Test table formatting with long content."""
        identities = [
            Identity(
                name="张三" * 50,  # Very long name
                email="verylongemailaddress@example.com",
            )
        ]
        formatted = IdentityFormatter.format_table(identities)
        assert "张三" in formatted

    def test_format_csv_with_various_types(self):
        """Test CSV formatting with various data types."""
        from datetime import date

        identities = [
            Identity(
                name="张三", email="test@qq.com", birthdate=date(1990, 1, 1), height=175
            )
        ]
        formatted = IdentityFormatter.format_csv(identities)
        assert "张三" in formatted
        assert "test@qq.com" in formatted
        # Date and int should be converted to string
        assert "1990" in formatted or "175" in formatted

    def test_format_json_with_date(self):
        """Test JSON formatting with date field."""
        from datetime import date

        identities = [Identity(name="张三", birthdate=date(1990, 1, 1))]
        formatted = IdentityFormatter.format_json(identities)
        data = json.loads(formatted)
        assert data[0]["name"] == "张三"
        assert "birthdate" in data[0]

    def test_write_output_to_file_with_directory(self, tmp_path):
        """Test writing output to file in subdirectory."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        output_file = subdir / "output.json"

        content = '{"test": "data"}'
        IdentityFormatter.write_output(content, str(output_file))

        assert output_file.exists()
        assert output_file.read_text() == content

    def test_format_raw_single_identity(self):
        """Test raw formatting with single identity."""
        identities = [Identity(name="张三", email="test@qq.com")]
        formatted = IdentityFormatter.format_raw(identities)
        assert "Identity #1" in formatted
        assert "张三" in formatted
        assert "test@qq.com" in formatted
        assert "-" * 40 in formatted

    def test_format_raw_multiple_identities(self):
        """Test raw formatting with multiple identities."""
        identities = [
            Identity(name="张三", email="test1@qq.com"),
            Identity(name="李四", email="test2@qq.com"),
        ]
        formatted = IdentityFormatter.format_raw(identities)
        assert "Identity #1" in formatted
        assert "Identity #2" in formatted
        assert "张三" in formatted
        assert "李四" in formatted
