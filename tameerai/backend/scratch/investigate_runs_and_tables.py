import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

from app.core.database import get_session_factory
from sqlalchemy import text

async def investigate():
    sf = get_session_factory()
    async with sf() as sess:
        print("=== SOURCE RUNS ===")
        runs = await sess.execute(text("SELECT * FROM material_rate_source_runs LIMIT 5"))
        for r in runs.fetchall():
            print(dict(r._mapping))
            
        print("\n=== ALL SOURCES ===")
        sources = await sess.execute(text("SELECT id, code, name FROM material_rate_sources"))
        for s in sources.fetchall():
            print(dict(s._mapping))

        print("\n=== TOTAL OBSERVATIONS IN DB ===")
        total_obs = await sess.execute(text("SELECT count(*) FROM material_rate_observations"))
        print("Total observations in material_rate_observations:", total_obs.scalar())

        print("\n=== OBSERVATIONS GROUPED BY SOURCE ===")
        by_source = await sess.execute(text("""
            SELECT s.code, count(*) as count, min(o.created_at) as earliest, max(o.created_at) as latest
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            GROUP BY s.code
        """))
        for bs in by_source.fetchall():
            print(dict(bs._mapping))

        print("\n=== ALL 6 MALFORMED RECORDS WITH EXACT FIELDS ===")
        malformed = await sess.execute(text("""
            SELECT o.id, o.product_id, p.code as product_code, o.city,
                   o.observed_price_pkr, o.normalized_price_pkr,
                   o.observed_unit, o.normalized_unit, o.created_at, o.published_at,
                   o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE o.normalized_unit LIKE 'rs_%'
        """))
        for m in malformed.fetchall():
            print(dict(m._mapping))

if __name__ == "__main__":
    asyncio.run(investigate())
