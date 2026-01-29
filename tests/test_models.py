"""Tests for identity models."""

import pytest
from identity_gen.models import Identity, IdentityConfig, IdentityField, OutputFormat


class TestIdentity:
    """Tests for Identity model."""

    def test_basic_identity_creation(self):
        """Test creating an identity with basic fields."""
        identity = Identity(name="John Doe", email="john@example.com")
        assert identity.name == "John Doe"
        assert identity.email == "john@example.com"

    def test_to_dict_all_fields(self):
        """Test converting identity to dictionary."""
        identity = Identity(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
        )
        data = identity.to_dict()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["phone"] == "123-456-7890"

    def test_to_dict_filtered_fields(self):
        """Test converting identity with field filtering."""
        identity = Identity(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
        )
        data = identity.to_dict(include_fields={"name", "email"})
        assert "name" in data
        assert "email" in data
        assert "phone" not in data

    def test_to_dict_skips_none(self):
        """Test that None values are skipped by default."""
        identity = Identity(name="John Doe")
        data = identity.to_dict()
        assert "name" in data
        assert "email" not in data

    def test_get_field_names(self):
        """Test getting all field names."""
        identity = Identity()
        fields = identity.get_field_names()
        assert "name" in fields
        assert "email" in fields
        assert "phone" in fields


class TestIdentityConfig:
    """Tests for IdentityConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = IdentityConfig()
        assert config.locale == "zh_CN"
        assert config.count == 1
        assert config.format == OutputFormat.TABLE

    def test_locale_validation_hyphen(self):
        """Test locale validation with hyphen."""
        config = IdentityConfig(locale="zh-CN")
        assert config.locale == "zh_CN"

    def test_locale_validation_underscore(self):
        """Test locale validation with underscore."""
        config = IdentityConfig(locale="zh_CN")
        assert config.locale == "zh_CN"

    def test_locale_validation_invalid(self):
        """Test locale validation with non-Chinese locale."""
        with pytest.raises(ValueError):
            IdentityConfig(locale="en_US")
        with pytest.raises(ValueError):
            IdentityConfig(locale="invalid")

    def test_count_validation(self):
        """Test count validation."""
        with pytest.raises(ValueError):
            IdentityConfig(count=0)
        with pytest.raises(ValueError):
            IdentityConfig(count=10001)

    def test_field_validation_valid(self):
        """Test field validation with valid fields."""
        config = IdentityConfig(include_fields=["name", "email"])
        assert config.include_fields == ["name", "email"]

    def test_field_validation_invalid(self):
        """Test field validation with invalid fields."""
        with pytest.raises(ValueError):
            IdentityConfig(include_fields=["name", "invalid_field"])

    def test_get_effective_fields_all(self):
        """Test getting all fields when no include/exclude."""
        config = IdentityConfig()
        fields = config.get_effective_fields()
        assert "name" in fields
        assert "email" in fields
        assert len(fields) == len(IdentityField)

    def test_get_effective_fields_include(self):
        """Test getting included fields only."""
        config = IdentityConfig(include_fields=["name", "email"])
        fields = config.get_effective_fields()
        assert fields == {"name", "email"}

    def test_get_effective_fields_exclude(self):
        """Test getting fields with exclusions."""
        config = IdentityConfig(exclude_fields=["ssn", "password"])
        fields = config.get_effective_fields()
        assert "ssn" not in fields
        assert "password" not in fields
        assert "name" in fields

    def test_get_effective_fields_include_and_exclude(self):
        """Test getting fields with both include and exclude."""
        config = IdentityConfig(
            include_fields=["name", "email", "phone"], exclude_fields=["phone"]
        )
        fields = config.get_effective_fields()
        assert fields == {"name", "email"}


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_format_values(self):
        """Test format enum values."""
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.CSV.value == "csv"
        assert OutputFormat.TABLE.value == "table"
        assert OutputFormat.RAW.value == "raw"
