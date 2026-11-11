import asyncio
import asyncpg
import json

async def inspect_all_pbs_steel():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    sql = """
        SELECT 
            o.id,
            o.product_id,
            p.code AS product_code,
            p.canonical_name,
            s.name AS source_name,
            o.city,
            o.observed_price_pkr,
            o.observed_unit,
            o.normalized_price_pkr,
            o.normalized_unit,
            o.duplicate_fingerprint,
            o.observation_metadata
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        LEFT JOIN material_rate_products p ON o.product_id = p.id
        WHERE s.name ILIKE '%Pakistan Bureau of Statistics%'
          AND p.code IN ('STEEL_REBAR_G60', 'STEEL_REBAR_G40')
        ORDER BY o.city;
    """
    rows = await conn.fetch(sql)
    print(f"Total PBS steel observations mapped to G40 or G60: {len(rows)}")
    
    items_count = {}
    for r in rows:
        meta = json.loads(r['observation_metadata']) if isinstance(r['observation_metadata'], str) else (r['observation_metadata'] or {})
        item_name = meta.get('item_name', 'UNKNOWN')
        items_count[item_name] = items_count.get(item_name, 0) + 1
        
    print("\nBreakdown of PBS item_name in metadata:")
    for k, v in items_count.items():
        print(f"  '{k}': {v} observations")

    print("\nDetailed list of all PBS steel observations:")
    for idx, r in enumerate(rows, 1):
        meta = json.loads(r['observation_metadata']) if isinstance(r['observation_metadata'], str) else (r['observation_metadata'] or {})
        print(f"{idx}. ID: {r['id']} | City: {r['city']:<15} | Price: {r['normalized_price_pkr']} | Linked Code: {r['product_code']} | Raw Item Name: '{meta.get('item_name')}' | Source URL: {meta.get('source_url')}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(inspect_all_pbs_steel())

