"""
Audit all steel observations for grade classification and snapshot calculation.
"""
import asyncio
import asyncpg
import json

DB_URL = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def run():
    conn = await asyncpg.connect(DB_URL)

    # 1. Inspect all observations where product is STEEL
    steel_obs = await conn.fetch("""
        SELECT o.id, o.city, o.observed_price_pkr, o.normalized_price_pkr, 
               o.observed_unit, o.normalized_unit, o.published_at, o.source_url, 
               s.name as source_name, p.code as product_code, p.canonical_name,
               o.observation_metadata
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE p.category = 'Steel & Metals' OR p.code LIKE '%STEEL%'
        ORDER BY s.name, o.city, o.published_at
    """)
    print(f"Total Steel Observations in DB: {len(steel_obs)}")

    # Classify based on evidence
    # Let's see what evidence exists in observation_metadata, product_code, item_name, etc.
    summary = {}
    for o in steel_obs:
        meta = o["observation_metadata"]
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: meta = {}
        elif meta is None:
            meta = {}
            
        item_name = meta.get("item_name", "")
        grade_meta = meta.get("grade", "")
        pcode = o["product_code"]
        source = o["source_name"]
        unit = o["normalized_unit"]
        
        # Check classification criteria:
        # What is verified Grade 40?
        # What is verified Grade 60?
        # What is unverified?
        
        key = (source, pcode, str(grade_meta), str(item_name), str(unit))
        summary[key] = summary.get(key, 0) + 1

    print("\nSTEEL OBSERVATIONS BREAKDOWN (Source, Code, Meta Grade, Meta Item, Unit):")
    for k, count in sorted(summary.items()):
        print(f"  Source: {k[0]}")
        print(f"    Product Code: {k[1]} | Meta Grade: '{k[2]}' | Item Name: '{k[3]}' | Unit: '{k[4]}' => Count: {count}")

    # 2. Check Task 2: Where did the snapshots get 17, 14, 14?
    # Let's inspect the actual backend code for snapshot calculation!
    print("\n" + "=" * 80)
    print("ALL STEEL OBSERVATIONS BY CITY (excluding anomaly units)")
    print("=" * 80)
    city_counts = await conn.fetch("""
        SELECT o.city, p.code, count(*) as count, 
               min(o.normalized_price_pkr) as min_p, 
               max(o.normalized_price_pkr) as max_p,
               avg(o.normalized_price_pkr) as avg_p
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        WHERE p.code IN ('STEEL_REBAR_G60', 'STEEL_REBAR_G40')
        GROUP BY o.city, p.code
        ORDER BY p.code, o.city
    """)
    for r in city_counts:
        print(f"Product: {r['code']} | City: {r['city']} | Count: {r['count']} | Min: {r['min_p']} | Max: {r['max_p']} | Avg: {r['avg_p']:.2f}")

    total = await conn.fetchval("SELECT count(*) FROM material_rate_observations")
    print(f"\nTOTAL OBSERVATIONS IN DB: {total}")
    by_prod = await conn.fetch("""
        SELECT p.code, count(*) as cnt
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        GROUP BY p.code
        ORDER BY cnt DESC
    """)
    for r in by_prod:
        print(f"  {r['code']}: {r['cnt']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
