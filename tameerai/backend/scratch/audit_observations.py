import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    # 1. Columns of material_rate_observations
    cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'material_rate_observations' ORDER BY ordinal_position;")
    print("--- COLUMNS OF material_rate_observations ---")
    for c in cols:
        print(f"  {c['column_name']} ({c['data_type']})")
        
    # 2. Total observations
    total_obs = await conn.fetchval("SELECT count(*) FROM material_rate_observations;")
    print(f"\nTOTAL OBSERVATIONS: {total_obs}")
    
    # 3. Group by source_id / source_name
    sources_breakdown = await conn.fetch("""
        SELECT s.id, s.name, s.source_type, count(o.id) as cnt
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        GROUP BY s.id, s.name, s.source_type
        ORDER BY cnt DESC;
    """)
    print("\n--- OBSERVATIONS BY SOURCE ---")
    for r in sources_breakdown:
        print(f"  Source [{r['name']}] (type: {r['source_type']}): {r['cnt']}")
        
    # 4. Group by verification / status
    status_breakdown = await conn.fetch("""
        SELECT verification_status, count(*) as cnt
        FROM material_rate_observations
        GROUP BY verification_status;
    """)
    print("\n--- OBSERVATIONS BY VERIFICATION STATUS ---")
    for r in status_breakdown:
        print(f"  Status [{r['verification_status']}]: {r['cnt']}")

    # 5. Look for 244 vs 314
    # Check if there is a subset of 244 observations by some condition (e.g. source, product, status, date)
    print("\n--- INVESTIGATING 244 vs 314 ---")
    # Check PBS vs other sources
    pbs_count = await conn.fetchval("""
        SELECT count(o.id)
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE s.name ILIKE '%PBS%';
    """)
    print(f"  PBS sources count: {pbs_count}")
    
    non_pbs_count = await conn.fetchval("""
        SELECT count(o.id)
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE s.name NOT ILIKE '%PBS%';
    """)
    print(f"  Non-PBS sources count: {non_pbs_count}")

    # Check products
    products = await conn.fetch("""
        SELECT p.id, p.canonical_name, p.category, count(o.id) as cnt
        FROM material_rate_products p
        LEFT JOIN material_rate_observations o ON o.product_id = p.id
        GROUP BY p.id, p.canonical_name, p.category
        HAVING count(o.id) > 0
        ORDER BY cnt DESC;
    """)
    print(f"\n--- PRODUCTS WITH OBSERVATIONS ({len(products)} products) ---")
    for p in products:
        print(f"  Product [{p['canonical_name']}] ({p['category']}): {p['cnt']} observations")
        
    # Steel Grade 40 and Grade 60 products and observations
    steel_products = await conn.fetch("""
        SELECT p.id, p.canonical_name, p.category, p.specifications, count(o.id) as cnt,
               min(o.price) as min_p, max(o.price) as max_p, avg(o.price) as avg_p
        FROM material_rate_products p
        LEFT JOIN material_rate_observations o ON o.product_id = p.id
        WHERE p.canonical_name ILIKE '%steel%' OR p.canonical_name ILIKE '%grade%' OR p.category ILIKE '%steel%'
        GROUP BY p.id, p.canonical_name, p.category, p.specifications
        ORDER BY p.canonical_name;
    """)
    print(f"\n--- STEEL GRADE 40 & 60 PRODUCTS & STATS ---")
    for sp in steel_products:
        print(f"  Product: {sp['canonical_name']} | Cat: {sp['category']} | Specs: {sp['specifications']} | Cnt: {sp['cnt']} | Min: {sp['min_p']} | Max: {sp['max_p']} | Avg: {sp['avg_p']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

