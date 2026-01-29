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
    EXCEL = "excel"
    SQL = "sql"
    MARKDOWN = "markdown"
    YAML = "yaml"
    VCARD = "vcard"


class IdentityField(str, Enum):
    """Available identity fields."""

    # Personal information
    NAME = "name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    GENDER = "gender"
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
    # Chinese-specific fields
    ETHNICITY = "ethnicity"
    EDUCATION = "education"
    MAJOR = "major"
    POLITICAL_STATUS = "political_status"
    MARITAL_STATUS = "marital_status"
    BLOOD_TYPE = "blood_type"
    HEIGHT = "height"
    WEIGHT = "weight"
    BANK_CARD = "bank_card"
    WECHAT_ID = "wechat_id"
    QQ_NUMBER = "qq_number"
    LICENSE_PLATE = "license_plate"
    # New fields for enhanced identity
    ZODIAC_SIGN = "zodiac_sign"  # 星座
    CHINESE_ZODIAC = "chinese_zodiac"  # 生肖
    IP_ADDRESS = "ip_address"  # IP地址
    MAC_ADDRESS = "mac_address"  # MAC地址
    SOCIAL_CREDIT_CODE = "social_credit_code"  # 统一社会信用代码
    EMERGENCY_CONTACT = "emergency_contact"  # 紧急联系人
    EMERGENCY_PHONE = "emergency_phone"  # 紧急联系电话
    HOBBIES = "hobbies"  # 兴趣爱好
    RELIGION = "religion"  # 宗教信仰


class Identity(BaseModel):
    """Complete identity information model."""

    # Basic personal information
    name: Optional[str] = Field(None, description="Full name")
    first_name: Optional[str] = Field(None, description="First name (given name)")
    last_name: Optional[str] = Field(None, description="Last name (surname)")
    birthdate: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender (male/female)")

    # Contact information
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    zipcode: Optional[str] = Field(None, description="ZIP/Postal code")
    country: Optional[str] = Field(None, description="Country")

    # Identity documents
    ssn: Optional[str] = Field(None, description="Chinese ID card number (18 digits)")

    # Professional information
    company: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")
    education: Optional[str] = Field(None, description="Education level")
    major: Optional[str] = Field(None, description="College major")

    # Account credentials
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")
    wechat_id: Optional[str] = Field(None, description="WeChat ID")
    qq_number: Optional[str] = Field(None, description="QQ number")

    # Social information
    ethnicity: Optional[str] = Field(None, description="Ethnicity (民族)")
    political_status: Optional[str] = Field(
        None, description="Political status (政治面貌)"
    )
    marital_status: Optional[str] = Field(None, description="Marital status (婚姻状况)")
    religion: Optional[str] = Field(None, description="Religion (宗教信仰)")

    # Physical characteristics
    blood_type: Optional[str] = Field(None, description="Blood type (血型)")
    height: Optional[int] = Field(None, description="Height in cm (身高)")
    weight: Optional[int] = Field(None, description="Weight in kg (体重)")

    # Financial information
    bank_card: Optional[str] = Field(None, description="Bank card number (银行卡号)")
    license_plate: Optional[str] = Field(None, description="License plate (车牌号)")
    social_credit_code: Optional[str] = Field(
        None, description="Social credit code (统一社会信用代码)"
    )

    # Digital identity
    ip_address: Optional[str] = Field(None, description="IP address (IP地址)")
    mac_address: Optional[str] = Field(None, description="MAC address (MAC地址)")

    # Astrological/Birth characteristics
    zodiac_sign: Optional[str] = Field(None, description="Zodiac sign (星座)")
    chinese_zodiac: Optional[str] = Field(None, description="Chinese zodiac (生肖)")

    # Additional information
    emergency_contact: Optional[str] = Field(None, description="Emergency contact name")
    emergency_phone: Optional[str] = Field(None, description="Emergency contact phone")
    hobbies: Optional[str] = Field(None, description="Hobbies (兴趣爱好)")

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
