import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async with engine.connect() as conn:
        print('--- PBS Steel Observations in PG 17 ---')
        res = await conn.execute(text("""
            SELECT o.id, s.code, p.code, p.canonical_name, o.city, o.normalized_price_pkr, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY' AND p.category = 'steel'
            LIMIT 5
        """))
        for r in res.fetchall():
            print(r[0], r[1], r[2], r[3], r[4], r[5], r[6])

if __name__ == "__main__":
    asyncio.run(check())

