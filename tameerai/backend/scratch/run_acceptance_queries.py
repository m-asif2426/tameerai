import asyncio
import asyncpg
import json

async def run_queries():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    print("=" * 80)
    print("SQL QUERY 1: TOTAL OBSERVATIONS AND SOURCE BREAKDOWN")
    print("=" * 80)
    sql1 = """
    SELECT 
        s.name AS source_name,
        s.source_type,
        COUNT(o.id) AS observation_count,
        MIN(o.published_at) AS earliest_published,
        MAX(o.published_at) AS latest_published,
        MIN(o.observed_price_pkr) AS min_price,
        MAX(o.observed_price_pkr) AS max_price
    FROM material_rate_observations o
    JOIN material_rate_sources s ON o.source_id = s.id
    GROUP BY s.name, s.source_type
    ORDER BY observation_count DESC;
    """
    rows1 = await conn.fetch(sql1)
    print(f"Statement:\n{sql1.strip()}\n")
    print("Output:")
    print(f"{'Source Name':<60} | {'Type':<15} | {'Count':<6} | {'Price Range (PKR)':<25}")
    print("-" * 115)
    for r in rows1:
        price_range = f"{r['min_price']} - {r['max_price']}"
        print(f"{r['source_name']:<60} | {r['source_type']:<15} | {r['observation_count']:<6} | {price_range:<25}")

    print("\n" + "=" * 80)
    print("SQL QUERY 2: RECONCILIATION OF 314 VS 244 OBSERVATIONS")
    print("=" * 80)
    sql2 = """
    SELECT 
        CASE 
            WHEN s.name IN (
                'Pakistan Bureau of Statistics - Monthly Construction Items',
                'SteelRateToday Rebar & Scrap Market Monitor',
                'Pakistan Bureau of Statistics'
            ) THEN 'AUTHENTIC_INGESTED_SOURCE'
            ELSE 'AUTOMATED_TEST_FIXTURE_SOURCE'
        END AS source_classification,
        COUNT(o.id) AS observation_count,
        COUNT(DISTINCT o.product_id) AS distinct_products,
        COUNT(DISTINCT o.city) AS distinct_cities,
        MIN(o.created_at) AS earliest_created,
        MAX(o.created_at) AS latest_created
    FROM material_rate_observations o
    JOIN material_rate_sources s ON o.source_id = s.id
    GROUP BY 1
    ORDER BY observation_count DESC;
    """
    rows2 = await conn.fetch(sql2)
    print(f"Statement:\n{sql2.strip()}\n")
    print("Output:")
    for r in rows2:
        print(f"Class: {r['source_classification']} | Count: {r['observation_count']} | Products: {r['distinct_products']} | Cities: {r['distinct_cities']}")

    print("\n" + "=" * 80)
    print("SQL QUERY 3: GRADE 40 VS GRADE 60 STEEL PRODUCT IDENTITY")
    print("=" * 80)
    sql3 = """
    SELECT 
        p.id AS product_id,
        p.code AS product_code,
        p.canonical_name,
        p.category,
        p.standard_unit,
        p.is_active,
        COUNT(o.id) AS total_observations,
        COUNT(CASE WHEN s.name = 'Pakistan Bureau of Statistics - Monthly Construction Items' THEN 1 END) AS pbs_monthly_obs,
        COUNT(CASE WHEN s.name = 'SteelRateToday Rebar & Scrap Market Monitor' THEN 1 END) AS srt_obs,
        COUNT(CASE WHEN s.name = 'Pakistan Bureau of Statistics' THEN 1 END) AS pbs_stat_obs,
        COUNT(CASE WHEN s.name NOT IN ('Pakistan Bureau of Statistics - Monthly Construction Items', 'SteelRateToday Rebar & Scrap Market Monitor', 'Pakistan Bureau of Statistics') THEN 1 END) AS test_fixture_obs,
        MIN(o.normalized_price_pkr) AS min_normalized_pkr,
        MAX(o.normalized_price_pkr) AS max_normalized_pkr
    FROM material_rate_products p
    LEFT JOIN material_rate_observations o ON o.product_id = p.id
    LEFT JOIN material_rate_sources s ON o.source_id = s.id
    WHERE p.code IN ('STEEL_REBAR_G40', 'STEEL_REBAR_G60')
    GROUP BY p.id, p.code, p.canonical_name, p.category, p.standard_unit, p.is_active
    ORDER BY p.code;
    """
    rows3 = await conn.fetch(sql3)
    print(f"Statement:\n{sql3.strip()}\n")
    print("Output:")
    for r in rows3:
        print(f"Product: {r['canonical_name']} (Code: {r['product_code']}, ID: {r['product_id']})")
        print(f"  Standard Unit: {r['standard_unit']} | Is Active: {r['is_active']}")
        print(f"  Total Observations: {r['total_observations']}")
        print(f"    - PBS Monthly Ingestion: {r['pbs_monthly_obs']}")
        print(f"    - SteelRateToday Aggregator: {r['srt_obs']}")
        print(f"    - PBS Official: {r['pbs_stat_obs']}")
        print(f"    - Test Fixtures: {r['test_fixture_obs']}")
        print(f"  Normalized Price Range: PKR {r['min_normalized_pkr']} to PKR {r['max_normalized_pkr']} / {r['standard_unit']}")
        print("-" * 60)

    print("\n" + "=" * 80)
    print("SQL QUERY 4: STEEL GRADE 40 & GRADE 60 OBSERVATIONS BY CITY (AUTHENTIC DATA)")
    print("=" * 80)
    sql4 = """
    SELECT 
        p.code AS product_code,
        p.canonical_name,
        o.city,
        s.name AS source_name,
        COUNT(o.id) AS obs_count,
        ROUND(AVG(o.normalized_price_pkr), 2) AS avg_price_pkr,
        MIN(o.normalized_price_pkr) AS min_price_pkr,
        MAX(o.normalized_price_pkr) AS max_price_pkr,
        o.normalized_unit
    FROM material_rate_observations o
    JOIN material_rate_products p ON o.product_id = p.id
    JOIN material_rate_sources s ON o.source_id = s.id
    WHERE p.code IN ('STEEL_REBAR_G40', 'STEEL_REBAR_G60')
      AND s.name IN ('Pakistan Bureau of Statistics - Monthly Construction Items', 'SteelRateToday Rebar & Scrap Market Monitor', 'Pakistan Bureau of Statistics')
    GROUP BY p.code, p.canonical_name, o.city, s.name, o.normalized_unit
    ORDER BY p.code, o.city, s.name;
    """
    rows4 = await conn.fetch(sql4)
    print(f"Statement:\n{sql4.strip()}\n")
    print("Output:")
    for r in rows4:
        print(f"{r['product_code']} | {r['city']:<12} | {r['obs_count']} obs | Avg: PKR {r['avg_price_pkr']:<10} | Range: {r['min_price_pkr']} - {r['max_price_pkr']} | {r['source_name']}")

    print("\n" + "=" * 80)
    print("SQL QUERY 5: ALL OTHER PRODUCTS IN THE 244 AUTHENTIC DATASET")
    print("=" * 80)
    sql5 = """
    SELECT 
        p.category,
        p.code,
        p.canonical_name,
        p.standard_unit,
        COUNT(o.id) AS authentic_obs_count,
        ROUND(AVG(o.normalized_price_pkr), 2) AS avg_price_pkr,
        o.normalized_unit
    FROM material_rate_observations o
    JOIN material_rate_products p ON o.product_id = p.id
    JOIN material_rate_sources s ON o.source_id = s.id
    WHERE s.name IN ('Pakistan Bureau of Statistics - Monthly Construction Items', 'SteelRateToday Rebar & Scrap Market Monitor', 'Pakistan Bureau of Statistics')
    GROUP BY p.category, p.code, p.canonical_name, p.standard_unit, o.normalized_unit
    ORDER BY authentic_obs_count DESC;
    """
    rows5 = await conn.fetch(sql5)
    print(f"Statement:\n{sql5.strip()}\n")
    print("Output:")
    for r in rows5:
        print(f"{r['category']:<12} | {r['code']:<20} | {r['canonical_name']:<35} | {r['authentic_obs_count']} obs | Avg: PKR {r['avg_price_pkr']} / {r['normalized_unit']}")

    print("\n" + "=" * 80)
    print("SQL QUERY 6: PROJECTS IN POSTGRESQL 17")
    print("=" * 80)
    sql6 = """
    SELECT id, code, name, city, budget_crore, status, created_at
    FROM projects
    ORDER BY created_at DESC;
    """
    rows6 = await conn.fetch(sql6)
    print(f"Statement:\n{sql6.strip()}\n")
    print("Output:")
    for r in rows6:
        print(f"ID: {r['id']} | Code: {r['code']} | Name: {r['name']} | City: {r['city']} | Budget (Cr): {r['budget_crore']} | Status: {r['status']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(run_queries())

