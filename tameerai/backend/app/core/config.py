import json
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    """
    Application Settings for TameerAI Backend.
    Uses Pydantic Settings v2 to load configuration from environment variables
    and .env file with type validation and defaults.
    """
    PROJECT_NAME: str = "TameerAI Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Default development CORS origins allowing Next.js local frontend
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database Configuration (Phase 01B: Supabase PostgreSQL)
    DATABASE_URL: Optional[str] = None
    MIGRATION_DATABASE_URL: Optional[str] = None

    # Database Connection Pool Settings (Conservative defaults for development)
    DB_POOL_SIZE: int = 3
    DB_MAX_OVERFLOW: int = 2
    DB_POOL_TIMEOUT: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_COMMAND_TIMEOUT: int = 10

    # Authentication & JWT Configuration (Phase 02A)
    JWT_SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-tameerai-fyp-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "tameerai-backend"
    JWT_AUDIENCE: str = "tameerai-frontend"

    # Refresh Token Cookie Transport Security Settings
    AUTH_COOKIE_NAME: str = "tameerai_refresh_token"
    AUTH_COOKIE_SECURE: bool = False  # Set True in production (HTTPS)
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_COOKIE_HTTPONLY: bool = True

    # Storage & Document Management Configuration (Phase 02D)
    STORAGE_BACKEND: str = "supabase"  # Options: 'supabase', 'in_memory'
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "project-documents"
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    STORAGE_SIGNED_URL_EXPIRES_SECONDS: int = 300  # 5 minutes

    # Background Jobs Configuration (Phase 02G)
    ENABLE_SYNTHETIC_JOBS: bool = False  # Disabled by default; only allowed in development/test

    # AI Core Foundation Configuration (Phase 03A)
    ENABLE_AI_FEATURES: bool = False  # Disabled by default in production
    AI_DEFAULT_PROVIDER: str = "mock"  # Options: 'mock', 'openai', 'gemini', 'anthropic'
    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_MAX_INPUT_CHARS: int = 32000
    AI_MAX_OUTPUT_TOKENS: int = 4096
    AI_DEFAULT_TEMPERATURE: float = 0.2

    # Google Gemini & Free-Tier Cost Controls (Phase 03D)
    ENABLE_GEMINI_API: bool = False  # False by default; network calls disabled unless explicitly enabled
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"  # Preferred initial model for affordable testing; configurable via env
    GEMINI_MAX_INPUT_CHARS: int = 10000
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    GEMINI_RPM_LIMIT: int = 15  # Application-side guardrail (15 RPM); not a guaranteed Google billing limit
    GEMINI_DAILY_REQUEST_CAP: int = 1500  # Application-side guardrail (1500 RPD); not a guaranteed Google billing limit
    GEMINI_CONCURRENT_REQUEST_LIMIT: int = 3
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_MAX_RETRIES: int = 2

    # Material Rate Intelligence System Configuration (Phase 03H / Stage 2A)
    ENABLE_MATERIAL_RATE_COLLECTION: bool = False
    MATERIAL_RATE_HTTP_TIMEOUT_SECONDS: float = 15.0
    MATERIAL_RATE_HTTP_MAX_RETRIES: int = 3
    MATERIAL_RATE_HTTP_MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5 MiB (5,242,880 bytes) authoritative response limit

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        if v is None:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []

    @field_validator("DATABASE_URL", "MIGRATION_DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # Normalize postgresql:// or postgres:// to postgresql+asyncpg:// for asyncpg driver
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """
        Validates that critical security secrets and HTTPS cookie parameters
        are strictly configured before booting in production.
        """
        if self.ENVIRONMENT.lower() == "production":
            if "dev-insecure" in self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be configured with a secure random key of at least 32 characters in production."
                )
            if not self.AUTH_COOKIE_SECURE:
                raise ValueError(
                    "AUTH_COOKIE_SECURE must be True in production to enforce HTTPS cookie transport."
                )
            if self.ENABLE_SYNTHETIC_JOBS:
                raise ValueError(
                    "ENABLE_SYNTHETIC_JOBS must be False in production."
                )
            if self.ENABLE_AI_FEATURES and self.AI_DEFAULT_PROVIDER.lower() == "mock":
                raise ValueError(
                    "Mock AI provider is not permitted when AI features are enabled in production."
                )
        return self

    @property
    def is_database_configured(self) -> bool:
        """Returns True if DATABASE_URL is configured."""
        return bool(self.DATABASE_URL and self.DATABASE_URL.strip())

    def get_masked_database_url(self, target: Optional[str] = None) -> str:
        """
        Returns the database URL with credentials safely redacted.
        Safe for logging, error reports, and diagnostics.
        """
        raw_url = target if target is not None else self.DATABASE_URL
        if not raw_url:
            return "NOT_CONFIGURED"
        try:
            url_obj = make_url(raw_url)
            return url_obj.render_as_string(hide_password=True)
        except Exception:
            # Fallback regex masking if URL parsing fails
            import re
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", raw_url)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
