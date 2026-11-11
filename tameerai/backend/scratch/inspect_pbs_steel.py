import asyncio
import asyncpg
import json

async def inspect_pbs_steel():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    # 1. Query all PBS steel observations
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
          AND (p.code ILIKE '%STEEL%' OR p.canonical_name ILIKE '%steel%' OR o.observation_metadata::text ILIKE '%iron%' OR o.observation_metadata::text ILIKE '%steel%')
        ORDER BY o.city, o.observed_price_pkr;
    """
    rows = await conn.fetch(sql)
    print(f"Total PBS steel observations found: {len(rows)}")
    
    # Check sample observation metadata structure
    if rows:
        print("\nSample PBS steel observation metadata:")
        print(rows[0]['observation_metadata'])

    # Search specifically for 30ed83c4
    sql_target = """
        SELECT o.*, p.code as product_code, p.canonical_name, s.name as source_name
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        LEFT JOIN material_rate_products p ON o.product_id = p.id
        WHERE o.id::text ILIKE '30ed83c4%' OR o.duplicate_fingerprint ILIKE '30ed83c4%';
    """
    target = await conn.fetch(sql_target)
    print(f"\nSearch for '30ed83c4': {len(target)} found")
    for t in target:
        print(dict(t))

    # Also check if any observation has metadata with 30ed83c4
    sql_meta = """
        SELECT o.id, o.product_id, p.code, o.observation_metadata
        FROM material_rate_observations o
        LEFT JOIN material_rate_products p ON o.product_id = p.id
        WHERE o.observation_metadata::text ILIKE '%30ed83c4%';
    """
    meta_target = await conn.fetch(sql_meta)
    print(f"Search for '30ed83c4' in metadata: {len(meta_target)} found")

    # Check products table history / UUIDs (01950000-0000-7000-8000-000000000002 vs 3ccf0cab-0b2f-4212-b3b8-ec332f7af5bc)
    sql_prods = """
        SELECT id, code, canonical_name, spec_attributes, created_at, updated_at
        FROM material_rate_products
        WHERE code IN ('STEEL_REBAR_G60', 'STEEL_REBAR_G40')
           OR id IN ('01950000-0000-7000-8000-000000000002'::uuid, '3ccf0cab-0b2f-4212-b3b8-ec332f7af5bc'::uuid);
    """
    prods = await conn.fetch(sql_prods)
    print("\n=== STEEL PRODUCTS IN DB ===")
    for p in prods:
        print(dict(p))

    # Also search for '01950000-0000-7000-8000-000000000002' anywhere in observations
    sql_old_uuid = """
        SELECT count(*)
        FROM material_rate_observations
        WHERE product_id = '01950000-0000-7000-8000-000000000002'::uuid
           OR observation_metadata::text ILIKE '%01950000-0000-7000-8000-000000000002%';
    """
    old_uuid_cnt = await conn.fetchval(sql_old_uuid)
    print(f"\nOccurrences of UUID 01950000-0000-7000-8000-000000000002: {old_uuid_cnt}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(inspect_pbs_steel())

