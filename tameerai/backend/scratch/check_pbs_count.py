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
            SELECT count(*)
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
              AND o.dealer_quote_id IS NULL
        """))
        print(f"Original PBS count (dealer_quote_id IS NULL): {res.scalar()}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

