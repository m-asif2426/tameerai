import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async with engine.connect() as conn:
        print('--- SteelRateToday City Distribution ---')
        res = await conn.execute(text("""
            SELECT o.city, count(*), 
                   jsonb_agg(DISTINCT o.observation_metadata->>'city') as meta_cities,
                   jsonb_agg(DISTINCT o.observation_metadata->>'brand') as brands
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER'
            GROUP BY o.city
        """))
        for r in res.fetchall():
            print(f"city column: {repr(r[0])} | count: {r[1]} | meta_city: {r[2]} | brands: {r[3]}")

        print('\n--- All observations with city IS NULL ---')
        res = await conn.execute(text("""
            SELECT s.code, count(*)
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE o.city IS NULL
            GROUP BY s.code
        """))
        for r in res.fetchall():
            print(f"source: {r[0]} | null_city_count: {r[1]}")

if __name__ == "__main__":
    asyncio.run(check())

