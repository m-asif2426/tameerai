"""
Three-tier mutually exclusive grade classification query demonstration.
"""
import asyncio
import asyncpg
import json

DB_URL = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def test_classification():
    conn = await asyncpg.connect(DB_URL)

    sql = """
    WITH classified_observations AS (
        SELECT 
            o.id,
            o.city,
            p.code as product_code,
            p.canonical_name as product_name,
            s.name as source_name,
            o.observed_price_pkr,
            o.observed_unit,
            o.normalized_price_pkr,
            o.normalized_unit,
            o.published_at,
            o.observation_metadata,
            CASE 
                -- 1. VERIFIED_GRADE_40: Explicit Grade 40 evidence in metadata/code + valid unit & pricing scale
                WHEN (
                    p.code = 'STEEL_REBAR_G40' 
                    OR COALESCE(o.observation_metadata->>'grade', '') ILIKE '%Grade 40%'
                    OR COALESCE(o.observation_metadata->>'item_name', '') ILIKE '%Grade 40%'
                    OR COALESCE(o.observation_metadata->>'raw_specification', '') ILIKE '%Grade 40%'
                )
                AND o.normalized_unit = 'metric_ton'
                AND o.normalized_price_pkr >= 100000.00
                THEN 'VERIFIED_GRADE_40'

                -- 2. VERIFIED_GRADE_60: Explicit Grade 60 evidence + NO Grade 40 conflict + valid unit & pricing scale
                WHEN (
                    COALESCE(o.observation_metadata->>'grade', '') ILIKE '%Grade 60%'
                    OR COALESCE(o.observation_metadata->>'raw_specification', '') ILIKE '%Grade 60%'
                    OR (p.code = 'STEEL_REBAR_G60' AND p.canonical_name ILIKE '%Grade 60%')
                )
                AND COALESCE(o.observation_metadata->>'item_name', '') NOT ILIKE '%Grade 40%'
                AND COALESCE(o.observation_metadata->>'raw_specification', '') NOT ILIKE '%Grade 40%'
                AND COALESCE(o.observation_metadata->>'grade', '') NOT ILIKE '%Grade 40%'
                AND o.normalized_unit = 'metric_ton'
                AND o.normalized_price_pkr >= 100000.00
                THEN 'VERIFIED_GRADE_60'

                -- 3. UNVERIFIED_GRADE: Malformed units, scrap entries, ambiguous grades, or pricing anomalies
                ELSE 'UNVERIFIED_GRADE'
            END AS grade_classification
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE p.category = 'Steel & Metals' OR p.code LIKE '%STEEL%'
    )
    SELECT grade_classification, source_name, count(*) as count,
           min(normalized_price_pkr) as min_price,
           max(normalized_price_pkr) as max_price
    FROM classified_observations
    GROUP BY grade_classification, source_name
    ORDER BY grade_classification, source_name;
    """

    rows = await conn.fetch(sql)
    print("=" * 80)
    print("THREE-TIER MUTUALLY EXCLUSIVE CLASSIFICATION RESULTS:")
    print("=" * 80)
    for r in rows:
        print(f"Classification: {r['grade_classification']:<20} | Source: {r['source_name']:<45} | Count: {r['count']:<3} | Range: PKR {r['min_price']} - {r['max_price']}")

    # Let's inspect the UNVERIFIED records specifically
    print("\n" + "=" * 80)
    print("UNVERIFIED RECORDS AUDIT (MUST NOT BE ASSUMED TO BE G60):")
    print("=" * 80)
    unverified = await conn.fetch("""
        SELECT o.id, o.city, o.observed_price_pkr, o.observed_unit, o.normalized_price_pkr, o.normalized_unit,
               o.observation_metadata
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        WHERE o.normalized_unit NOT IN ('metric_ton')
           OR o.normalized_price_pkr < 100000.00
    """)
    for u in unverified:
        meta = u['observation_metadata'] or {}
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: meta = {}
        print(f"UUID: {u['id']} | City: {u['city']} | Obs: {u['observed_price_pkr']} ({u['observed_unit']}) | Norm: {u['normalized_price_pkr']} ({u['normalized_unit']}) | Brand/City: {meta.get('brand')} | URL: {meta.get('source_url')}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_classification())
