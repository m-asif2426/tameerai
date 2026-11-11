import asyncio
import asyncpg
import json

async def investigate():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    # 1. Total authentic observations
    sql_total = """
        SELECT count(o.id)
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE s.name IN (
            'Pakistan Bureau of Statistics - Monthly Construction Items',
            'SteelRateToday Rebar & Scrap Market Monitor',
            'Pakistan Bureau of Statistics'
        );
    """
    total_authentic = await conn.fetchval(sql_total)
    print(f"Total authentic source observations: {total_authentic}")

    # 2. Pull full details for the 6 observations
    sql_six = """
        SELECT 
            o.id AS observation_id,
            o.product_id,
            p.code AS product_code,
            p.canonical_name AS product_name,
            s.id AS source_id,
            s.name AS source_name,
            o.observed_price_pkr,
            o.observed_unit,
            o.normalized_price_pkr,
            o.normalized_unit,
            o.city,
            o.published_at,
            o.collected_at,
            o.source_url,
            o.background_job_id,
            o.duplicate_fingerprint,
            o.verification_status,
            o.observation_metadata
        FROM material_rate_observations o
        JOIN material_rate_sources s ON o.source_id = s.id
        LEFT JOIN material_rate_products p ON o.product_id = p.id
        WHERE s.name IN (
            'Pakistan Bureau of Statistics - Monthly Construction Items',
            'SteelRateToday Rebar & Scrap Market Monitor',
            'Pakistan Bureau of Statistics'
        )
        AND o.normalized_unit NOT IN ('metric_ton', 'bag_50kg', 'cft', '1000_bricks', 'piece')
        ORDER BY o.normalized_price_pkr;
    """
    six_records = await conn.fetch(sql_six)
    print(f"\n=== THE {len(six_records)} OBSERVATIONS WITH NON-STANDARD NORMALIZED UNITS ===")
    for idx, rec in enumerate(six_records, 1):
        print(f"\n--- RECORD #{idx} ---")
        print(f"  Observation UUID: {rec['observation_id']}")
        print(f"  Product UUID: {rec['product_id']}")
        print(f"  Product Code: {rec['product_code']}")
        print(f"  Product Name: {rec['product_name']}")
        print(f"  Source ID: {rec['source_id']}")
        print(f"  Source Name: {rec['source_name']}")
        print(f"  City: {rec['city']}")
        print(f"  Raw Observed Price: {rec['observed_price_pkr']}")
        print(f"  Raw Observed Unit: {rec['observed_unit']}")
        print(f"  Normalized Price: {rec['normalized_price_pkr']}")
        print(f"  Normalized Unit: {rec['normalized_unit']}")
        print(f"  Published At: {rec['published_at']}")
        print(f"  Collected At: {rec['collected_at']}")
        print(f"  Source URL: {rec['source_url']}")
        print(f"  Background Job ID: {rec['background_job_id']}")
        print(f"  Duplicate Fingerprint: {rec['duplicate_fingerprint']}")
        print(f"  Verification Status: {rec['verification_status']}")
        print(f"  Metadata: {rec['observation_metadata']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(investigate())
