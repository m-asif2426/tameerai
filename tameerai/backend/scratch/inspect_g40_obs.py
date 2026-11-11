import asyncio
import asyncpg
import json

async def inspect_g40_obs():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    sql = """
        SELECT 
            o.id,
            o.city,
            o.observed_price_pkr,
            o.observed_unit,
            o.normalized_price_pkr,
            o.normalized_unit,
            s.name as source_name,
            o.observation_metadata
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE o.product_id = '70b657f5-9947-424b-859b-0c87f668841b'::uuid
        ORDER BY o.city;
    """
    rows = await conn.fetch(sql)
    print(f"Total observations for product 70b657f5 (STEEL_REBAR_G40): {len(rows)}")
    for r in rows:
        meta = json.loads(r['observation_metadata']) if isinstance(r['observation_metadata'], str) else (r['observation_metadata'] or {})
        print(f"  ID: {r['id']} | City: {r['city']} | Price: {r['observed_price_pkr']} | Source: {r['source_name']} | Meta: {meta}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(inspect_g40_obs())

