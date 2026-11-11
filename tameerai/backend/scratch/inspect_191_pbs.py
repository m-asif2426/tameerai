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
            SELECT o.id, o.created_at, o.observed_price_pkr, o.observation_metadata->>'item_name' as item_name,
                   o.observation_metadata->>'synthetic' as synthetic,
                   o.observation_metadata->>'test' as test
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
            ORDER BY o.created_at DESC
            LIMIT 15
        """))
        rows = res.fetchall()
        print(f"Latest 15 PBS records:")
        for r in rows:
            print(r)
            
        res_count = await conn.execute(text("""
            SELECT count(*)
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
        """))
        print(f"Total PBS count: {res_count.scalar()}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

