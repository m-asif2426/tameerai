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
            SELECT o.id, o.created_at, o.observed_price_pkr, o.observation_metadata, o.product_id
            FROM material_rate_observations o
            WHERE o.id IN (
                '9d32e80c-2b03-409c-b117-909d9c404508',
                'c3265746-fd9c-4224-a18f-4bb7acc0f040',
                '775dbe70-47b3-4126-8d9f-13310684cb6e'
            )
        """))
        for r in res.fetchall():
            print(r)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

