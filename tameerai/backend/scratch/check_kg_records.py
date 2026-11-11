import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

from app.core.database import get_session_factory
from sqlalchemy import text

async def check():
    sf = get_session_factory()
    async with sf() as sess:
        res = await sess.execute(text("""
            SELECT o.id, p.code as prod_code, o.city, o.observed_price_pkr, o.normalized_price_pkr,
                   o.observed_unit, o.normalized_unit, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE o.observed_unit ILIKE '%kg%' OR o.normalized_unit ILIKE '%kg%'
               OR o.observation_metadata::text ILIKE '%kg%'
        """))
        rows = [dict(r._mapping) for r in res.fetchall()]
        print(f"Total records mentioning kg: {len(rows)}")
        by_prod = {}
        for r in rows:
            p = r["prod_code"]
            by_prod[p] = by_prod.get(p, 0) + 1
        print("Breakdown by product code:")
        for p, c in by_prod.items():
            print(f"  {p}: {c}")

        # Check steel specifically
        steel_kg = [r for r in rows if "STEEL" in r["prod_code"]]
        print(f"\nSteel records mentioning kg: {len(steel_kg)}")
        for s in steel_kg:
            print(s)

if __name__ == "__main__":
    asyncio.run(check())

