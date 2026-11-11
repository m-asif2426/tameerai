import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from collections import Counter
from scratch.phase02h1.pg_helper import get_connection
import asyncio

async def main():
    conn = await get_connection()
    try:
        # Check tables in database
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        print("Tables in PostgreSQL 17 database:")
        for t in tables:
            print(f"  {t['table_name']}")

        # Count observations by verification status and source
        status_counts = await conn.fetch("""
            SELECT 
                s.code as source_code,
                o.verification_status,
                COUNT(o.id) as cnt
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            GROUP BY s.code, o.verification_status
            ORDER BY s.code, cnt DESC;
        """)
        print("\nObservations by Source and Verification Status:")
        for row in status_counts:
            print(f"  Source: {row['source_code']:<30} | Status: {row['verification_status']:<22} | Count: {row['cnt']}")

        # Check total verification status
        tot_status = await conn.fetch("""
            SELECT verification_status, COUNT(*) as cnt
            FROM material_rate_observations
            GROUP BY verification_status
            ORDER BY cnt DESC;
        """)
        print("\nTotal Observations by Verification Status:")
        for row in tot_status:
            print(f"  Status: {row['verification_status']:<22} | Count: {row['cnt']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

