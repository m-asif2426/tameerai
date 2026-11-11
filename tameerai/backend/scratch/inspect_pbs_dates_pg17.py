import asyncio
import os
import sys

os.chdir(r"D:\new idea project\tameerai\backend")
sys.path.insert(0, r"D:\new idea project\tameerai\backend")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT DISTINCT published_at, observation_metadata
            FROM material_rate_observations
            WHERE source_id IN (SELECT id FROM material_rate_sources WHERE code = 'PBS_STATISTICAL_MONTHLY')
            LIMIT 5;
        """))
        for row in res.fetchall():
            print(f"published_at: {row[0]} | metadata: {row[1]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

