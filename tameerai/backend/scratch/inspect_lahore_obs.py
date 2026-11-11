import asyncio
import os
import sys

sys.path.insert(0, r"D:\new idea project\tameerai\backend")
os.chdir(r"D:\new idea project\tameerai\backend")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT o.id, o.city, o.observed_price_pkr, o.normalized_price_pkr, s.code, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE o.city IS NULL OR lower(o.city) = 'lahore'
        """))
        rows = res.fetchall()
        print(f"Total Lahore or city IS NULL: {len(rows)}")
        for r in rows:
            print(r.id, r.city, r.observed_price_pkr, r.code, r.observation_metadata)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

