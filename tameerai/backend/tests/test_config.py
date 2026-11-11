from app.core.config import Settings, settings


def test_default_settings():
    """Verify default configuration attributes."""
    assert settings.PROJECT_NAME == "TameerAI Backend"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ENVIRONMENT == "development"
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
    assert "http://127.0.0.1:3000" in settings.BACKEND_CORS_ORIGINS


def test_cors_origins_parsing_list():
    """Verify list parsing for CORS origins."""
    s = Settings(BACKEND_CORS_ORIGINS=["https://example.com", "https://tameerai.pk"])
    assert s.BACKEND_CORS_ORIGINS == ["https://example.com", "https://tameerai.pk"]


def test_cors_origins_parsing_comma_string():
    """Verify comma-separated string parsing for CORS origins."""
    s = Settings(BACKEND_CORS_ORIGINS="https://example.com, https://tameerai.pk")
    assert s.BACKEND_CORS_ORIGINS == ["https://example.com", "https://tameerai.pk"]


def test_cors_origins_parsing_json_string():
    """Verify JSON array string parsing for CORS origins."""
    s = Settings(BACKEND_CORS_ORIGINS='["https://example.com", "https://tameerai.pk"]')
    assert s.BACKEND_CORS_ORIGINS == ["https://example.com", "https://tameerai.pk"]


def test_cors_origins_empty_fallback():
    """Verify empty string falls back to empty list."""
    s = Settings(BACKEND_CORS_ORIGINS="")
    assert s.BACKEND_CORS_ORIGINS == []

