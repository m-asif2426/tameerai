import asyncio
import logging
import re
from typing import Any, Dict, Optional
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger("tameerai.diagnostic")


def sanitize_error_message(message: str) -> str:
    """Removes sensitive credentials or passwords from exception messages."""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", message)


async def check_database_connection(timeout: float = 6.0) -> Dict[str, Any]:
    """
    Performs a safe, read-only diagnostic check against the configured database.
    Does NOT modify data, create tables, or expose credentials.

    Returns:
        dict: Standardized diagnostic results dictionary.
    """
    masked_url = settings.get_masked_database_url()

    if not settings.is_database_configured:
        return {
            "status": "NOT_TESTED",
            "database_configured": False,
            "masked_url": "NOT_CONFIGURED",
            "message": "DATABASE_URL is not configured. Set DATABASE_URL in .env to test connection.",
            "details": None,
            "pgvector_status": "NOT_VERIFIED",
        }

    from app.core.database import get_engine

    try:
        engine = get_engine()
        async with asyncio.timeout(timeout):
            async with engine.connect() as conn:
                # 1. Ping query
                ping_result = await conn.execute(text("SELECT 1;"))
                ping_val = ping_result.scalar()

                # 2. Database Name
                db_name_result = await conn.execute(text("SELECT current_database();"))
                db_name = db_name_result.scalar()

                # 3. PostgreSQL Version
                version_result = await conn.execute(text("SELECT version();"))
                pg_version_raw = version_result.scalar() or "Unknown"
                # Extract concise version e.g. "PostgreSQL 16.1 ..."
                pg_version = pg_version_raw.split(",")[0].strip()

                # 4. Check pgvector extension status
                vector_result = await conn.execute(
                    text(
                        "SELECT extname, extversion, extnamespace::regnamespace::text "
                        "FROM pg_extension WHERE extname = 'vector';"
                    )
                )
                vector_row = vector_result.fetchone()

                pgvector_info: Dict[str, Any]
                if vector_row:
                    pgvector_info = {
                        "status": "ENABLED",
                        "name": vector_row[0],
                        "version": vector_row[1],
                        "schema": vector_row[2],
                    }
                else:
                    pgvector_info = {
                        "status": "NOT_ENABLED",
                        "name": "vector",
                        "version": None,
                        "schema": None,
                        "instruction": "Run 'CREATE EXTENSION IF NOT EXISTS vector;' in Supabase SQL Editor.",
                    }

                return {
                    "status": "CONNECTED",
                    "database_configured": True,
                    "masked_url": masked_url,
                    "database_name": db_name,
                    "postgres_version": pg_version,
                    "ping": ping_val == 1,
                    "pgvector": pgvector_info,
                    "pgvector_status": pgvector_info["status"],
                    "error": None,
                }

    except TimeoutError:
        logger.warning("Database connection timed out for %s", masked_url)
        return {
            "status": "FAILED",
            "database_configured": True,
            "masked_url": masked_url,
            "error_type": "TimeoutError",
            "error": "Connection timed out. If using direct connection, IPv6 or firewall may be blocking. Consider using Supabase Session Pooler (port 5432).",
            "pgvector_status": "NOT_VERIFIED",
        }
    except Exception as exc:
        raw_msg = str(exc)
        sanitized_msg = sanitize_error_message(raw_msg)
        logger.error("Database connection failed for %s: %s", masked_url, sanitized_msg)

        # Diagnose common connectivity issues
        error_hint: Optional[str] = None
        lower_msg = sanitized_msg.lower()
        if "getaddrinfo failed" in lower_msg or "name or service not known" in lower_msg:
            error_hint = "DNS resolution failed. Check the hostname in DATABASE_URL."
        elif "password authentication failed" in lower_msg:
            error_hint = "Authentication failed. Check your database password."
        elif "connection refused" in lower_msg or "cannot assign requested address" in lower_msg:
            error_hint = "Connection refused or network unreachable. Check port and pooler configuration."

        return {
            "status": "FAILED",
            "database_configured": True,
            "masked_url": masked_url,
            "error_type": type(exc).__name__,
            "error": sanitized_msg,
            "hint": error_hint,
            "pgvector_status": "NOT_VERIFIED",
        }

