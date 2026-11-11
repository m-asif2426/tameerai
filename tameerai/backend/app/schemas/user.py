"""
TameerAI - Identity Pydantic Schemas (Phase 01C.2)

Pydantic v2 schemas for User, UserSettings, and UserSession.
Enforces validation, camelCase serialization aliases for frontend alignment,
and strict exclusion of password hashes and raw session secrets.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Enums matching frontend contracts
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    ENGINEER = "engineer"
    CONTRACTOR = "contractor"
    ARCHITECT = "architect"
    COMPANY = "company"


class LanguagePreference(str, Enum):
    EN = "en"
    UR = "ur"


class ThemePreference(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class AIStrictness(str, Enum):
    STRICT = "strict"
    CONSULTATIVE = "consultative"


class FidicThreshold(str, Enum):
    SIX = "6"
    EIGHT = "8"
    NINE = "9"


class MarketRegion(str, Enum):
    LAHORE = "lahore"
    KARACHI = "karachi"
    ISLAMABAD = "islamabad"


class AITone(str, Enum):
    PROFESSIONAL = "professional"
    PRACTICAL = "practical"
    LEGAL = "legal"


# ---------------------------------------------------------------------------
# User Schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    """Shared user fields."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    email: EmailStr
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        alias="fullName",
        serialization_alias="fullName",
        description="Full name of the user",
    )
    role: str = Field(
        default="engineer",
        max_length=50,
        description="Role: engineer, contractor, architect, company",
    )
    company: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Consulting firm or construction company",
    )
    pec_number: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="pecNumber",
        serialization_alias="pecNumber",
        description="Pakistan Engineering Council registration number",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Contact phone number",
    )
    city: str = Field(
        default="Lahore",
        max_length=100,
        description="Operating city jurisdiction",
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Professional biography",
    )


class UserCreate(UserBase):
    """
    Schema for user registration.
    Requires password for credential creation.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password submitted for hashing. Never stored.",
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile fields.
    All fields are optional.
    Mass-assignment protected: id, email, role, is_active, is_verified, hashed_password are strictly forbidden.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
        alias="fullName",
        serialization_alias="fullName",
    )
    company: Optional[str] = Field(default=None, max_length=150)
    pec_number: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="pecNumber",
        serialization_alias="pecNumber",
    )
    phone: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("city", "full_name", mode="before")
    @classmethod
    def validate_required_strings_not_null(cls, v: Any) -> Any:
        if v is None:
            raise ValueError("Field cannot be null.")
        return v


class UserRead(UserBase):
    """
    Schema for reading user details.
    Guarantees hashed_password and raw passwords are never serialized.
    """
    id: UUID = Field(..., description="Unique user UUID")
    is_active: bool = Field(
        default=True,
        alias="isActive",
        serialization_alias="isActive",
    )
    is_verified: bool = Field(
        default=False,
        alias="isVerified",
        serialization_alias="isVerified",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        serialization_alias="createdAt",
    )
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        serialization_alias="updatedAt",
    )


class UserProfileContract(BaseModel):
    """
    Frontend contract directly matching `src/types/user.ts -> UserProfile`.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    full_name: str = Field(..., alias="fullName", serialization_alias="fullName")
    role: str
    company: str = ""
    pec_number: str = Field(default="", alias="pecNumber", serialization_alias="pecNumber")
    email: str
    phone: str = ""
    city: str
    bio: str = ""


# ---------------------------------------------------------------------------
# UserSettings Schemas
# ---------------------------------------------------------------------------

class UserSettingsBase(BaseModel):
    """Shared user settings fields with dual naming."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    language: str = Field(default="en", max_length=10)
    theme: str = Field(default="system", max_length=10)

    # Notification preferences
    pbc_violations_alert: bool = Field(
        default=True,
        alias="pbcViolations",
        serialization_alias="pbcViolations",
    )
    fidic_risks_alert: bool = Field(
        default=True,
        alias="fidicRisks",
        serialization_alias="fidicRisks",
    )
    price_spikes_alert: bool = Field(
        default=True,
        alias="priceSpikes",
        serialization_alias="priceSpikes",
    )
    weekly_digest_alert: bool = Field(
        default=False,
        alias="weeklyDigest",
        serialization_alias="weeklyDigest",
    )
    whatsapp_alerts: bool = Field(
        default=True,
        alias="whatsappAlerts",
        serialization_alias="whatsappAlerts",
    )

    # AI settings
    ai_strictness: str = Field(
        default="strict",
        alias="strictness",
        serialization_alias="strictness",
    )
    fidic_threshold: str = Field(
        default="8",
        alias="fidicThreshold",
        serialization_alias="fidicThreshold",
    )
    auto_citations: bool = Field(
        default=True,
        alias="autoCitations",
        serialization_alias="autoCitations",
    )
    market_region: str = Field(
        default="lahore",
        alias="marketRegion",
        serialization_alias="marketRegion",
    )
    ai_tone: str = Field(
        default="professional",
        alias="aiTone",
        serialization_alias="aiTone",
    )


class UserSettingsUpdate(BaseModel):
    """Schema for updating user preferences with strict enum validation and mass-assignment protection."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
    )

    language: Optional[str] = None
    theme: Optional[str] = None
    pbc_violations_alert: Optional[bool] = Field(
        default=None, alias="pbcViolations", serialization_alias="pbcViolations"
    )
    fidic_risks_alert: Optional[bool] = Field(
        default=None, alias="fidicRisks", serialization_alias="fidicRisks"
    )
    price_spikes_alert: Optional[bool] = Field(
        default=None, alias="priceSpikes", serialization_alias="priceSpikes"
    )
    weekly_digest_alert: Optional[bool] = Field(
        default=None, alias="weeklyDigest", serialization_alias="weeklyDigest"
    )
    whatsapp_alerts: Optional[bool] = Field(
        default=None, alias="whatsappAlerts", serialization_alias="whatsappAlerts"
    )
    ai_strictness: Optional[str] = Field(
        default=None, alias="strictness", serialization_alias="strictness"
    )
    fidic_threshold: Optional[str] = Field(
        default=None, alias="fidicThreshold", serialization_alias="fidicThreshold"
    )
    auto_citations: Optional[bool] = Field(
        default=None, alias="autoCitations", serialization_alias="autoCitations"
    )
    market_region: Optional[str] = Field(
        default=None, alias="marketRegion", serialization_alias="marketRegion"
    )
    ai_tone: Optional[str] = Field(
        default=None, alias="aiTone", serialization_alias="aiTone"
    )

    @field_validator("language", mode="after")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in {"en", "ur"}:
                raise ValueError("Language must be either 'en' (English) or 'ur' (Urdu).")
            return v_clean
        return v

    @field_validator("theme", mode="after")
    @classmethod
    def validate_theme(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in {"light", "dark", "system"}:
                raise ValueError("Theme must be 'light', 'dark', or 'system'.")
            return v_clean
        return v

    @field_validator("ai_strictness", mode="after")
    @classmethod
    def validate_ai_strictness(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in {"strict", "consultative"}:
                raise ValueError("AI strictness must be 'strict' or 'consultative'.")
            return v_clean
        return v

    @field_validator("fidic_threshold", mode="after")
    @classmethod
    def validate_fidic_threshold(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if v_clean not in {"6", "8", "9"}:
                raise ValueError("FIDIC risk threshold must be '6', '8', or '9'.")
            return v_clean
        return v

    @field_validator("market_region", mode="after")
    @classmethod
    def validate_market_region(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in {"lahore", "karachi", "islamabad"}:
                raise ValueError("Market region must be 'lahore', 'karachi', or 'islamabad'.")
            return v_clean
        return v

    @field_validator("ai_tone", mode="after")
    @classmethod
    def validate_ai_tone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in {"professional", "practical", "legal"}:
                raise ValueError("AI tone must be 'professional', 'practical', or 'legal'.")
            return v_clean
        return v


class UserSettingsRead(UserSettingsBase):
    """Schema for reading user settings."""
    id: UUID
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    created_at: datetime = Field(
        ..., alias="createdAt", serialization_alias="createdAt"
    )
    updated_at: datetime = Field(
        ..., alias="updatedAt", serialization_alias="updatedAt"
    )


# ---------------------------------------------------------------------------
# UserSession Schemas
# ---------------------------------------------------------------------------

class UserSessionRead(BaseModel):
    """
    Schema for reading active sessions.
    Guarantees refresh_token_hash is NEVER exposed in API outputs.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    device_info: Optional[str] = Field(
        default=None,
        alias="device",
        serialization_alias="device",
        description="Client device details",
    )
    ip_address: Optional[str] = Field(
        default=None,
        alias="ip",
        serialization_alias="ip",
        description="Originating IP address",
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location",
    )
    is_revoked: bool = Field(
        default=False,
        alias="isRevoked",
        serialization_alias="isRevoked",
    )
    expires_at: datetime = Field(
        ...,
        alias="expiresAt",
        serialization_alias="expiresAt",
    )
    last_active_at: datetime = Field(
        ...,
        alias="lastActive",
        serialization_alias="lastActive",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        serialization_alias="createdAt",
    )

