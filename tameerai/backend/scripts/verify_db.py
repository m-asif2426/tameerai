#!/usr/bin/env python3
"""
TameerAI — Developer Database Connectivity Diagnostic Utility
Runs safe, read-only queries (SELECT 1, pg version, pgvector check) without exposing credentials.
"""

import asyncio
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.config import settings
from app.db.diagnostic import check_database_connection


async def main() -> None:
    print("=" * 65)
    print("  TAMEERAI — DATABASE CONNECTIVITY & PGVECTOR DIAGNOSTIC")
    print("=" * 65)
    print(f"  Project Name       : {settings.PROJECT_NAME}")
    print(f"  Environment        : {settings.ENVIRONMENT}")
    print(f"  Database Configured: {settings.is_database_configured}")
    print(f"  Target URL (Masked): {settings.get_masked_database_url()}")
    print("-" * 65)

    result = await check_database_connection(timeout=8.0)

    print(f"  Connection Status  : {result['status']}")

    if result["status"] == "NOT_TESTED":
        print(f"\n  [INFO] {result['message']}")
        print("  To test your connection:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in DATABASE_URL with your Supabase credentials")
        print("  3. Re-run: python scripts/verify_db.py\n")
    elif result["status"] == "CONNECTED":
        print(f"  Database Name      : {result.get('database_name')}")
        print(f"  PostgreSQL Version : {result.get('postgres_version')}")
        pgv = result.get("pgvector", {})
        print(f"  pgvector Extension : {pgv.get('status')}")
        if pgv.get("status") == "ENABLED":
            print(f"  - Version          : {pgv.get('version')}")
            print(f"  - Schema           : {pgv.get('schema')}")
        else:
            print(f"  - Action Needed    : {pgv.get('instruction')}")
        print("\n  [SUCCESS] Database connection verified successfully.\n")
    else:
        print(f"  Error Type         : {result.get('error_type')}")
        print(f"  Error Message      : {result.get('error')}")
        if result.get("hint"):
            print(f"  Hint               : {result.get('hint')}")
        print("\n  [FAILED] Could not connect to remote database.\n")

    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())

