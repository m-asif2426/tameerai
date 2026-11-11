import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async with engine.connect() as conn:
        print('--- PostgreSQL Inventory: source | canonical_city | locality | material | grade | price_basis | count ---')
        res = await conn.execute(text("""
            SELECT 
                s.code as source,
                COALESCE(o.city, 'NATIONAL') as canonical_city,
                COALESCE(o.observation_metadata->>'locality', 'ALL') as locality,
                p.canonical_name as material,
                COALESCE(o.observation_metadata->>'grade', p.category) as grade,
                COALESCE(o.observation_metadata->>'price_basis', 'retail') as price_basis,
                count(*) as observation_count
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE o.verification_status IN ('verified_market_range', 'verified_quote', 'cross_checked', 'indicative')
            GROUP BY s.code, o.city, o.observation_metadata->>'locality', p.canonical_name, o.observation_metadata->>'grade', p.category, o.observation_metadata->>'price_basis'
            ORDER BY s.code, canonical_city, material;
        """))
        rows = res.fetchall()
        print(f"Total grouped inventory rows: {len(rows)}")
        for r in rows:
            print(f"{r[0]:<30} | {r[1]:<15} | {r[2]:<10} | {r[3]:<35} | {r[4]:<12} | {r[5]:<10} | {r[6]}")

        print('\n--- Specifically Steel Observations in Lahore ---')
        res = await conn.execute(text("""
            SELECT o.id, s.code, o.city, p.code, p.canonical_name, o.observed_price_pkr, o.normalized_price_pkr, o.normalized_unit, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE p.category = 'steel'
              AND LOWER(o.city) = 'lahore'
              AND o.verification_status IN ('verified_market_range', 'verified_quote', 'cross_checked', 'indicative')
        """))
        lahore_steel = res.fetchall()
        print(f"Total Lahore Steel observations: {len(lahore_steel)}")
        for r in lahore_steel[:10]:
            print(r[0], r[1], r[2], r[3], r[5], r[7], r[8])

if __name__ == "__main__":
    asyncio.run(check())

