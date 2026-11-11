import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.config import Settings
from app.core import database
from app.db.diagnostic import check_database_connection, sanitize_error_message


def test_database_url_normalization():
    """Verify that postgres:// and postgresql:// are normalized to postgresql+asyncpg://."""
    s1 = Settings(DATABASE_URL="postgres://user:pass@host:5432/db")
    assert s1.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/db"

    s2 = Settings(DATABASE_URL="postgresql://user:pass@host:5432/db")
    assert s2.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/db"

    s3 = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db")
    assert s3.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/db"

    s4 = Settings(DATABASE_URL="")
    assert s4.DATABASE_URL is None
    assert s4.is_database_configured is False


def test_missing_database_url_handling():
    """Verify safe behavior when DATABASE_URL is not configured."""
    s = Settings(DATABASE_URL=None)
    assert s.is_database_configured is False
    assert s.get_masked_database_url() == "NOT_CONFIGURED"

    with patch("app.core.database.settings", s):
        # Reset engine reference
        database._engine = None
        with pytest.raises(RuntimeError) as exc_info:
            database.get_engine()
        assert "DATABASE_URL is not configured" in str(exc_info.value)


def test_secret_redaction_in_url():
    """Verify that database passwords are never exposed in masked URLs."""
    raw_url = "postgresql+asyncpg://postgres:SuperSecretPassword123!@db.ttcykmdfzlmtsvxdupkq.supabase.co:5432/postgres"
    s = Settings(DATABASE_URL=raw_url)

    masked = s.get_masked_database_url()
    assert "SuperSecretPassword123!" not in masked
    assert "postgres:***@" in masked
    assert "db.ttcykmdfzlmtsvxdupkq.supabase.co" in masked


def test_sanitize_error_message():
    """Verify that exception messages containing credentials have secrets stripped."""
    error_with_pass = "connection to postgresql+asyncpg://myuser:P@ssword999@localhost:5432/db failed"
    sanitized = sanitize_error_message(error_with_pass)
    assert "P@ssword999" not in sanitized
    assert "myuser:***@" in sanitized


@pytest.mark.asyncio
async def test_diagnostic_not_tested_when_unconfigured():
    """Verify diagnostic safely reports NOT_TESTED when credentials are missing."""
    s = Settings(DATABASE_URL=None)
    with patch("app.db.diagnostic.settings", s):
        result = await check_database_connection()
        assert result["status"] == "NOT_TESTED"
        assert result["database_configured"] is False
        assert result["masked_url"] == "NOT_CONFIGURED"
        assert result["pgvector_status"] == "NOT_VERIFIED"


@pytest.mark.asyncio
async def test_diagnostic_connection_failure_handling():
    """Verify diagnostic safely handles and reports network/connection failure."""
    s = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@127.0.0.1:59999/dummy")
    with patch("app.db.diagnostic.settings", s):
        with patch("app.core.database.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.connect.side_effect = ConnectionRefusedError("Connection refused by host")
            mock_get_engine.return_value = mock_engine

            result = await check_database_connection(timeout=2.0)
            assert result["status"] == "FAILED"
            assert result["database_configured"] is True
            assert result["pgvector_status"] == "NOT_VERIFIED"
            assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_get_db_session_lifecycle_success():
    """Verify get_db session dependency lifecycle on successful request (commit and close)."""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.core.database.get_session_factory", return_value=mock_session_factory):
        async_gen = database.get_db()
        session = await anext(async_gen)
        assert session == mock_session

        # Simulate completion of endpoint
        try:
            await anext(async_gen)
        except StopAsyncIteration:
            pass

        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_session_lifecycle_error():
    """Verify get_db session dependency lifecycle on error (rollback and close)."""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.core.database.get_session_factory", return_value=mock_session_factory):
        async_gen = database.get_db()
        session = await anext(async_gen)
        assert session == mock_session

        # Simulate exception during request
        with pytest.raises(ValueError):
            await async_gen.athrow(ValueError("Simulated error in route"))

        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispose_engine():
    """Verify engine disposal cleanly disposes active connections."""
    mock_engine = AsyncMock()
    database._engine = mock_engine
    database._session_factory = MagicMock()

    await database.dispose_engine()
    mock_engine.dispose.assert_awaited_once()
    assert database._engine is None
    assert database._session_factory is None

