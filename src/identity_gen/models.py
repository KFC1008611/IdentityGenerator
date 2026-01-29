"""Pydantic data models for identity information."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Set

from pydantic import BaseModel, EmailStr, Field, field_validator


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    CSV = "csv"
    TABLE = "table"
    RAW = "raw"


class IdentityField(str, Enum):
    """Available identity fields."""

    NAME = "name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIPCODE = "zipcode"
    COUNTRY = "country"
    SSN = "ssn"
    BIRTHDATE = "birthdate"
    COMPANY = "company"
    JOB_TITLE = "job_title"
    USERNAME = "username"
    PASSWORD = "password"


class Identity(BaseModel):
    """Complete identity information model."""

    name: Optional[str] = Field(None, description="Full name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    zipcode: Optional[str] = Field(None, description="ZIP/Postal code")
    country: Optional[str] = Field(None, description="Country")
    ssn: Optional[str] = Field(None, description="Social Security Number/National ID")
    birthdate: Optional[date] = Field(None, description="Date of birth")
    company: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")

    def to_dict(self, include_fields: Optional[Set[str]] = None) -> dict:
        """Convert to dictionary with optional field filtering.

        Args:
            include_fields: Set of field names to include. If None, all fields.

        Returns:
            Dictionary representation of the identity.
        """
        data = self.model_dump()
        if include_fields:
            return {k: v for k, v in data.items() if k in include_fields}
        return {k: v for k, v in data.items() if v is not None}

    def get_field_names(self) -> List[str]:
        """Get list of available field names."""
        return list(self.model_fields.keys())


class IdentityConfig(BaseModel):
    """Configuration for identity generation."""

    locale: str = Field(
        default="zh_CN", description="Locale for generation (China only, use zh_CN)"
    )
    count: int = Field(
        default=1, ge=1, le=10000, description="Number of identities to generate"
    )
    include_fields: Optional[List[str]] = Field(
        default=None, description="Fields to include (None = all)"
    )
    exclude_fields: Optional[List[str]] = Field(
        default=None, description="Fields to exclude"
    )
    seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )
    format: OutputFormat = Field(
        default=OutputFormat.TABLE, description="Output format"
    )

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        """Validate locale - only zh_CN supported."""
        v = v.replace("-", "_")
        if v != "zh_CN":
            raise ValueError("Only zh_CN (Chinese) locale is supported")
        return v

    @field_validator("include_fields", "exclude_fields")
    @classmethod
    def validate_fields(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate field names."""
        if v is None:
            return v
        valid_fields = {f.value for f in IdentityField}
        invalid = set(v) - valid_fields
        if invalid:
            raise ValueError(f"Invalid fields: {invalid}. Valid: {valid_fields}")
        return v

    def get_effective_fields(self) -> Set[str]:
        """Calculate effective fields based on include/exclude."""
        all_fields = {f.value for f in IdentityField}

        if self.include_fields:
            fields = set(self.include_fields)
        else:
            fields = all_fields

        if self.exclude_fields:
            fields = fields - set(self.exclude_fields)

        return fields
