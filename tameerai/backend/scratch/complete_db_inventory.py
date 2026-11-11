import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

from app.core.database import get_session_factory
from sqlalchemy import text

async def inventory():
    sf = get_session_factory()
    async with sf() as sess:
        print("=== TOTAL OBSERVATIONS COUNT ===")
        total = await sess.scalar(text("SELECT count(*) FROM material_rate_observations"))
        print(f"Total count: {total}")

        print("\n=== BREAKDOWN BY PRODUCT ===")
        by_prod = await sess.execute(text("""
            SELECT p.id as product_id, p.code as product_code, p.category, p.canonical_name,
                   count(*) as observation_count,
                   min(o.normalized_price_pkr) as min_price,
                   max(o.normalized_price_pkr) as max_price
            FROM material_rate_observations o
            JOIN material_rate_products p ON o.product_id = p.id
            GROUP BY p.id, p.code, p.category, p.canonical_name
            ORDER BY count(*) DESC
        """))
        for bp in by_prod.fetchall():
            print(dict(bp._mapping))

        print("\n=== BREAKDOWN BY SOURCE ===")
        by_src = await sess.execute(text("""
            SELECT s.code as source_code, s.name as source_name, count(*) as observation_count
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            GROUP BY s.code, s.name
            ORDER BY count(*) DESC
        """))
        for bs in by_src.fetchall():
            print(dict(bs._mapping))

        print("\n=== STEEL OBSERVATIONS BREAKDOWN BY UNIT AND SCALE ===")
        steel_breakdown = await sess.execute(text("""
            SELECT o.normalized_unit, 
                   count(*) as count,
                   min(o.normalized_price_pkr) as min_p,
                   max(o.normalized_price_pkr) as max_p,
                   min(o.observed_price_pkr) as min_obs,
                   max(o.observed_price_pkr) as max_obs
            FROM material_rate_observations o
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE p.category = 'steel'
            GROUP BY o.normalized_unit
        """))
        for sb in steel_breakdown.fetchall():
            print(dict(sb._mapping))

if __name__ == "__main__":
    asyncio.run(inventory())

