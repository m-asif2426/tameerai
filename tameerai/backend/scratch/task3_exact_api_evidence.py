import asyncio
import json
import requests
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

BASE_URL = "http://127.0.0.1:8000"
PG_URL = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def run_verification():
    print("================================================================================")
    print("TASK 3: GRADE 40 / GRADE 60 EXACT API & RECORD IDENTITY EVIDENCE")
    print("================================================================================")

    # 1. Live API Requests
    url_g40 = f"{BASE_URL}/api/v1/material-rates/history?product_code=STEEL_REBAR_G40&days=365"
    resp_g40 = requests.get(url_g40)
    data_g40 = resp_g40.json()

    url_g60 = f"{BASE_URL}/api/v1/material-rates/history?product_code=STEEL_REBAR_G60&days=365"
    resp_g60 = requests.get(url_g60)
    data_g60 = resp_g60.json()

    print("\n--- 1. LIVE HTTP API RESPONSES ---")
    print(f"Request 1: GET {url_g40}")
    print(f"Status Code: {resp_g40.status_code}")
    print(f"Product Code: {data_g40.get('product_code')} | Product Name: {data_g40.get('product_name')}")
    print(f"Total Observations: {data_g40.get('total_observations')}")
    print(f"Buckets: {json.dumps(data_g40.get('data_points'), indent=2)}")

    print(f"\nRequest 2: GET {url_g60}")
    print(f"Status Code: {resp_g60.status_code}")
    print(f"Product Code: {data_g60.get('product_code')} | Product Name: {data_g60.get('product_name')}")
    print(f"Total Observations: {data_g60.get('total_observations')}")
    print(f"Buckets: {json.dumps(data_g60.get('data_points'), indent=2)}")

    # 2. Database Record Identity & UUID Extraction
    engine = create_async_engine(PG_URL)
    async with engine.connect() as conn:
        # SQL for Grade 40 (51 observations)
        sql_g40 = text("""
            SELECT o.id, o.city, o.normalized_price_pkr, o.normalized_unit, s.code as source_code, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON s.id = o.source_id
            WHERE o.normalized_unit = 'metric_ton'
              AND o.normalized_price_pkr >= 1000
              AND (
                s.code = 'PBS_STATISTICAL_MONTHLY'
                OR (
                    s.code = 'STEELRATETODAY_PK_PUBLISHER'
                    AND (o.observation_metadata->>'grade' = 'Grade 40' OR o.observation_metadata->>'item_name' ILIKE '%grade 40%')
                )
              )
              AND (o.observation_metadata->>'is_synthetic' IS NULL OR o.observation_metadata->>'is_synthetic' = 'false')
            ORDER BY o.id;
        """)
        res_g40 = await conn.execute(sql_g40)
        rows_g40 = res_g40.fetchall()

        # SQL for Grade 60 (23 observations)
        sql_g60 = text("""
            SELECT o.id, o.city, o.normalized_price_pkr, o.normalized_unit, s.code as source_code, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON s.id = o.source_id
            WHERE o.normalized_unit = 'metric_ton'
              AND o.normalized_price_pkr >= 1000
              AND s.code = 'STEELRATETODAY_PK_PUBLISHER'
              AND (o.observation_metadata->>'grade' = 'Grade 60' OR o.observation_metadata->>'grade' IS NULL)
              AND (o.observation_metadata->>'is_synthetic' IS NULL OR o.observation_metadata->>'is_synthetic' = 'false')
            ORDER BY o.id;
        """)
        res_g60 = await conn.execute(sql_g60)
        rows_g60 = res_g60.fetchall()

        # SQL for Unverified Malformed (6 observations)
        sql_unv = text("""
            SELECT o.id, o.city, o.observed_price_pkr, o.normalized_unit, s.code as source_code, o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON s.id = o.source_id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER'
              AND (o.normalized_unit LIKE 'rs_%' OR o.normalized_price_pkr < 1000)
              AND (o.observation_metadata->>'is_synthetic' IS NULL OR o.observation_metadata->>'is_synthetic' = 'false')
            ORDER BY o.id;
        """)
        res_unv = await conn.execute(sql_unv)
        rows_unv = res_unv.fetchall()

    uuids_g40 = set(str(r[0]) for r in rows_g40)
    uuids_g60 = set(str(r[0]) for r in rows_g60)
    uuids_unv = set(str(r[0]) for r in rows_unv)

    print("\n--- 2. DATABASE POPULATION COUNTS ---")
    print(f"Grade 40 Verified Observations: {len(uuids_g40)} (PBS: {sum(1 for r in rows_g40 if r[4] == 'PBS_STATISTICAL_MONTHLY')}, SteelRateToday: {sum(1 for r in rows_g40 if r[4] == 'STEELRATETODAY_PK_PUBLISHER')})")
    print(f"Grade 60 Verified Observations: {len(uuids_g60)} (SteelRateToday: {len(uuids_g60)})")
    print(f"Unverified Malformed Observations: {len(uuids_unv)}")
    print(f"Total SteelRateToday Rebar Observations: {sum(1 for r in rows_g40 if r[4] == 'STEELRATETODAY_PK_PUBLISHER') + len(uuids_g60) + len(uuids_unv)} (16 G40 + 23 G60 + 6 Unverified = 45)")
    print(f"Total Authentic Rebar-Related Observations: {len(uuids_g40) + len(uuids_g60) + len(uuids_unv)} (51 + 23 + 6 = 80)")

    print("\n--- 3. SET INTERSECTION TESTS ---")
    int_g40_g60 = uuids_g40.intersection(uuids_g60)
    int_g40_unv = uuids_g40.intersection(uuids_unv)
    int_g60_unv = uuids_g60.intersection(uuids_unv)

    print(f"Grade40 ∩ Grade60: {len(int_g40_g60)} (Intersecting UUIDs: {list(int_g40_g60)})")
    print(f"Grade40 ∩ Unverified: {len(int_g40_unv)} (Intersecting UUIDs: {list(int_g40_unv)})")
    print(f"Grade60 ∩ Unverified: {len(int_g60_unv)} (Intersecting UUIDs: {list(int_g60_unv)})")

    assert data_g40.get("total_observations") == 51, f"API G40 mismatch: {data_g40.get('total_observations')}"
    assert data_g60.get("total_observations") == 23, f"API G60 mismatch: {data_g60.get('total_observations')}"
    assert len(uuids_g40) == 51, f"DB G40 mismatch: {len(uuids_g40)}"
    assert len(uuids_g60) == 23, f"DB G60 mismatch: {len(uuids_g60)}"
    assert len(uuids_unv) == 6, f"DB Unverified mismatch: {len(uuids_unv)}"
    assert len(int_g40_g60) == 0, "Cross-contamination between G40 and G60!"
    assert len(int_g40_unv) == 0, "Cross-contamination between G40 and Unverified!"
    assert len(int_g60_unv) == 0, "Cross-contamination between G60 and Unverified!"

    print("\n>>> ALL TASK 3 ASSERTIONS PASSED WITH ZERO DISCREPANCIES <<<")

    print("\n--- 4. EXACT UUID INVENTORIES ---")
    print("Grade 60 UUIDs (23):")
    for idx, uid in enumerate(sorted(uuids_g60)):
        print(f"  {idx+1:02d}: {uid}")

    print("\nUnverified Malformed UUIDs (6):")
    for idx, r in enumerate(rows_unv):
        print(f"  {idx+1:02d}: ID={r[0]} | City={r[1]} | Price={r[2]} | Unit={r[3]}")

    print("\nGrade 40 UUIDs (51):")
    for idx, uid in enumerate(sorted(uuids_g40)):
        print(f"  {idx+1:02d}: {uid}")

if __name__ == "__main__":
    asyncio.run(run_verification())
