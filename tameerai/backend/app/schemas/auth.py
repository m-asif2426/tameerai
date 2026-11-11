"""
TameerAI - Authentication Pydantic Schemas (Phase 02A)

Defines request and response schemas for registration, login, token refresh, and logout.
Supports dual naming (camelCase for frontend alignment, snake_case for Python backend).
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user import UserRead


ALLOWED_ROLES = {"engineer", "contractor", "architect", "company"}


class RegisterRequest(BaseModel):
    """
    Registration payload matching frontend signup form.
    Guarantees role safety (rejects privileged / administrative role escalation).
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        alias="fullName",
        description="Full legal or professional name",
    )
    email: EmailStr = Field(
        ...,
        description="User email address for login and notifications",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password to be hashed with Argon2id",
    )
    role: str = Field(
        default="engineer",
        description="Professional persona: engineer, contractor, architect, company",
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
        description="Pakistan Engineering Council registration number",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Contact phone number (e.g. +92 300 1234567)",
    )
    city: str = Field(
        default="Lahore",
        max_length=100,
        description="Primary operating city in Pakistan",
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Brief professional summary",
    )

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).lower().strip()

    @field_validator("role", mode="after")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_clean = v.lower().strip()
        if v_clean not in ALLOWED_ROLES:
            raise ValueError(f"Invalid role '{v}'. Allowed roles: {', '.join(sorted(ALLOWED_ROLES))}")
        return v_clean


class LoginRequest(BaseModel):
    """
    Login credential payload.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    email: EmailStr = Field(..., description="User login email")
    password: str = Field(..., min_length=1, max_length=128, description="User password")
    remember_me: bool = Field(
        default=False,
        alias="rememberMe",
        description="Extend refresh token lifetime from 7 to 30 days",
    )
    device_info: Optional[str] = Field(
        default=None,
        alias="deviceInfo",
        max_length=255,
        description="Client device details or user agent label",
    )

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).lower().strip()


class RefreshRequest(BaseModel):
    """
    Refresh token payload. Optional if token is delivered via HttpOnly cookie.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    refresh_token: Optional[str] = Field(
        default=None,
        alias="refreshToken",
        description="Raw refresh token (if not provided in HttpOnly cookie)",
    )


class LogoutRequest(BaseModel):
    """
    Optional logout payload for explicit token revocation.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    refresh_token: Optional[str] = Field(
        default=None,
        alias="refreshToken",
        description="Specific refresh token to revoke (if not in cookie)",
    )


class TokenResponse(BaseModel):
    """
    Authentication success response schema.
    Returns the JWT access token and user profile.
    Refresh token is included for clients that do not use cookies.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    access_token: str = Field(
        ...,
        alias="accessToken",
        serialization_alias="accessToken",
        description="Signed JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        alias="tokenType",
        serialization_alias="tokenType",
        description="Token scheme type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        alias="expiresIn",
        serialization_alias="expiresIn",
        description="Seconds until access token expiration",
    )
    refresh_token: Optional[str] = Field(
        default=None,
        alias="refreshToken",
        serialization_alias="refreshToken",
        description="Raw refresh token (also set in HttpOnly cookie where supported)",
    )
    user: UserRead = Field(
        ...,
        description="Authenticated user identity and profile details",
    )


class AuthMessageResponse(BaseModel):
    """
    Generic operation status response.
    """
    message: str
    success: bool = True

