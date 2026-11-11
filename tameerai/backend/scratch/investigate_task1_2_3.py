"""
TameerAI - Phase 03.4E.2 Acceptance Challenge Investigation
Tasks 1, 2, 3:
- Grade classification (Verified G40, Verified G60, Unverified)
- 6 anomaly SteelRateToday records inspection (URL, scrap vs rebar, raw specs)
- Snapshot mathematical reconciliation (sample counts 17, 14, 14 vs 29, prices PKR 265k-268k vs 263k max)
- PBS steel records original dates, workbook metadata, and row numbers
"""

import asyncio
import asyncpg
import json

DB_URL = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def run():
    conn = await asyncpg.connect(DB_URL)
    
    print("=" * 80)
    print("1. STEEL PRODUCTS IN CATALOG")
    print("=" * 80)
    products = await conn.fetch("""
        SELECT id, code, canonical_name, category, standard_unit
        FROM material_rate_products
        WHERE category = 'Steel & Metals' OR code LIKE '%STEEL%'
    """)
    for p in products:
        print(f"Product ID: {p['id']} | Code: {p['code']} | Name: {p['canonical_name']} | Unit: {p['standard_unit']}")

    print("=" * 80)
    print("COLUMNS IN material_rate_observations:")
    print("=" * 80)
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'material_rate_observations'
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"  {c['column_name']}: {c['data_type']}")

    print("\n" + "=" * 80)
    print("2. THE 6 STEELRATETODAY ANOMALIES (DETAILED FORENSIC AUDIT)")
    print("=" * 80)
    anomalies = await conn.fetch("""
        SELECT o.*, p.code as product_code, s.name as source_name
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE o.normalized_unit LIKE 'rs_%'
        ORDER BY o.published_at DESC
    """)
    for a in anomalies:
        d = dict(a)
        meta = d.get("observation_metadata")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except:
                pass
        d["observation_metadata"] = meta
        print(json.dumps(d, indent=2, default=str))

    print("\n" + "=" * 80)
    print("3. ALL OBSERVATIONS CURRENTLY MAPPED TO STEEL_REBAR_G60")
    print("=" * 80)
    g60_obs = await conn.fetch("""
        SELECT o.*, s.name as source_name
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE p.code = 'STEEL_REBAR_G60'
        ORDER BY o.city, o.published_at
    """)
    print(f"Total records mapped to STEEL_REBAR_G60: {len(g60_obs)}")
    
    by_source_city = {}
    for o in g60_obs:
        key = (o["source_name"], o["city"])
        by_source_city[key] = by_source_city.get(key, 0) + 1
    for k, v in sorted(by_source_city.items()):
        print(f"  Source: {k[0]} | City: {k[1]} | Count: {v}")

    print("\n" + "=" * 80)
    print("4. ALL OBSERVATIONS CURRENTLY MAPPED TO STEEL_REBAR_G40")
    print("=" * 80)
    g40_obs = await conn.fetch("""
        SELECT o.*, s.name as source_name
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE p.code = 'STEEL_REBAR_G40'
        ORDER BY o.city, o.published_at
    """)
    print(f"Total records mapped to STEEL_REBAR_G40: {len(g40_obs)}")
    by_source_city_40 = {}
    for o in g40_obs:
        key = (o["source_name"], o["city"])
        by_source_city_40[key] = by_source_city_40.get(key, 0) + 1
    for k, v in sorted(by_source_city_40.items()):
        print(f"  Source: {k[0]} | City: {k[1]} | Count: {v}")
    for o in g40_obs:
        key = (o["source_name"], o["city"])
        by_source_city_40[key] = by_source_city_40.get(key, 0) + 1
    for k, v in sorted(by_source_city_40.items()):
        print(f"  Source: {k[0]} | City: {k[1]} | Count: {v}")
    for o in g40_obs:
        key = (o["source_name"], o["city"])
        by_source_city_40[key] = by_source_city_40.get(key, 0) + 1
    for k, v in sorted(by_source_city_40.items()):
        print(f"  Source: {k[0]} | City: {k[1]} | Count: {v}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
