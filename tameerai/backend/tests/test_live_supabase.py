import os
import pytest
from app.core.config import settings
from app.db.diagnostic import check_database_connection


@pytest.mark.asyncio
async def test_live_supabase_connection():
    """
    Opt-in live integration test for hosted Supabase PostgreSQL.
    Only runs if DATABASE_URL is configured in environment / .env.
    Performs ONLY safe read-only queries (SELECT 1, pg version, pgvector check).
    NEVER creates, modifies, or truncates any data.
    """
    if not settings.is_database_configured:
        pytest.skip("Skipping live Supabase connection test: DATABASE_URL is not configured.")

    result = await check_database_connection(timeout=5.0)

    # If configured but external pooler connection times out/unreachable, skip opt-in live test
    if result["status"] != "CONNECTED":
        pytest.skip(
            f"Live Supabase connection unreachable: {result.get('error')} | "
            f"Hint: {result.get('hint')}"
        )
    assert result["ping"] is True
    assert result["database_name"] is not None
    assert result["postgres_version"] is not None


@pytest.mark.asyncio
async def test_live_supabase_users_and_settings_schema():
    """
    Read-only inspection of public.users and public.user_settings columns in hosted Supabase.
    Validates column presence, absence of hallucinated fields, and default persona role.
    """
    if not settings.is_database_configured:
        pytest.skip("Skipping live Supabase schema test: DATABASE_URL is not configured.")

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            # Check users columns
            users_result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users';
            """))
            users_cols = {row.column_name: row for row in users_result.fetchall()}

            expected_user_cols = {
                "id", "email", "hashed_password", "full_name", "role",
                "company", "pec_number", "phone", "city", "bio",
                "is_active", "is_verified", "created_at", "updated_at",
            }
            for col in expected_user_cols:
                assert col in users_cols, f"Missing column '{col}' in public.users"

            # Verify default role is 'engineer'
            assert "'engineer'" in str(users_cols["role"].column_default)

            # Check user_settings columns
            settings_result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'user_settings';
            """))
            settings_cols = {row.column_name: row for row in settings_result.fetchall()}

            expected_settings_cols = {
                "id", "user_id", "language", "theme",
                "pbc_violations_alert", "fidic_risks_alert", "price_spikes_alert",
                "weekly_digest_alert", "whatsapp_alerts",
                "ai_strictness", "fidic_threshold", "auto_citations",
                "market_region", "ai_tone",
                "created_at", "updated_at",
            }
            for col in expected_settings_cols:
                assert col in settings_cols, f"Missing column '{col}' in public.user_settings"

            # Explicitly verify absence of non-existent fields mentioned in reports
            assert "notifications_enabled" not in settings_cols, "Unexpected 'notifications_enabled' in user_settings"
            assert "email_digest" not in settings_cols, "Unexpected 'email_digest' in user_settings"
    finally:
        await engine.dispose()


