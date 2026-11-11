import asyncio
import sys
sys.path.insert(0, ".")
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test_corrected_sql():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async with engine.connect() as conn:
        # 1. Grade 40
        q_g40 = text("""
            SELECT o.id, o.city, o.normalized_price_pkr, o.normalized_unit, s.code AS source_code
            FROM material_rate_observations o
            JOIN material_rate_sources s ON s.id = o.source_id
            JOIN material_rate_products p ON p.id = o.product_id
            WHERE o.normalized_unit = 'metric_ton'
              AND o.normalized_price_pkr >= 1000
              AND NOT (o.normalized_unit LIKE 'rs\_%' ESCAPE '\\')
              AND (
                (o.observation_metadata->>'grade' = 'Grade 40' OR o.observation_metadata->>'item_name' ~* '(grade\\s*40|40\\s*grade|g40)')
                OR (s.code = 'PBS_STATISTICAL_MONTHLY' AND p.code = 'STEEL_REBAR_G40')
              )
              AND (o.verification_status != 'synthetic_test_fixture')
              AND (o.observation_metadata->>'is_synthetic' IS NULL OR (o.observation_metadata->>'is_synthetic')::boolean = false)
              AND (o.observation_metadata->>'synthetic' IS NULL OR (o.observation_metadata->>'synthetic')::boolean = false)
              AND NOT (s.code LIKE 'SRC-PG17-%' OR s.code LIKE 'GHARHUB_SRC_%' OR s.code LIKE 'PBS_SPI_%' OR s.code LIKE 'SRC-AUDIT-%' OR s.code ILIKE '%TEST%' OR s.name ILIKE '%TEST%')
            ORDER BY o.id;
        """)
        rows_g40 = (await conn.execute(q_g40)).fetchall()

        # 2. Grade 60 (explicit grade = 'Grade 60' or regex match, NEVER grade IS NULL)
        q_g60 = text("""
            SELECT o.id, o.city, o.normalized_price_pkr, o.normalized_unit, s.code AS source_code
            FROM material_rate_observations o
            JOIN material_rate_sources s ON s.id = o.source_id
            JOIN material_rate_products p ON p.id = o.product_id
            WHERE o.normalized_unit = 'metric_ton'
              AND o.normalized_price_pkr >= 1000
              AND NOT (o.normalized_unit LIKE 'rs\_%' ESCAPE '\\')
              AND p.code = 'STEEL_REBAR_G60'
              AND (o.observation_metadata->>'grade' = 'Grade 60' OR o.observation_metadata->>'item_name' ~* '(grade\\s*60|60\\s*grade|g60)')
              AND (o.verification_status != 'synthetic_test_fixture')
              AND (o.observation_metadata->>'is_synthetic' IS NULL OR (o.observation_metadata->>'is_synthetic')::boolean = false)
              AND (o.observation_metadata->>'synthetic' IS NULL OR (o.observation_metadata->>'synthetic')::boolean = false)
              AND NOT (s.code LIKE 'SRC-PG17-%' OR s.code LIKE 'GHARHUB_SRC_%' OR s.code LIKE 'PBS_SPI_%' OR s.code LIKE 'SRC-AUDIT-%' OR s.code ILIKE '%TEST%' OR s.name ILIKE '%TEST%')
            ORDER BY o.id;
        """)
        rows_g60 = (await conn.execute(q_g60)).fetchall()

        # 3. Unverified Malformed
        q_unv = text("""
            SELECT o.id, o.city, o.observed_price_pkr, o.normalized_unit, s.code AS source_code
            FROM material_rate_observations o
            JOIN material_rate_sources s ON s.id = o.source_id
            JOIN material_rate_products p ON p.id = o.product_id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER'
              AND (
                o.normalized_unit LIKE 'rs\_%' ESCAPE '\\'
                OR o.normalized_price_pkr < 1000
                OR o.normalized_unit != 'metric_ton'
              )
              AND (o.verification_status != 'synthetic_test_fixture')
              AND (o.observation_metadata->>'is_synthetic' IS NULL OR (o.observation_metadata->>'is_synthetic')::boolean = false)
              AND (o.observation_metadata->>'synthetic' IS NULL OR (o.observation_metadata->>'synthetic')::boolean = false)
              AND NOT (s.code LIKE 'SRC-PG17-%' OR s.code LIKE 'GHARHUB_SRC_%' OR s.code LIKE 'PBS_SPI_%' OR s.code LIKE 'SRC-AUDIT-%' OR s.code ILIKE '%TEST%' OR s.name ILIKE '%TEST%')
            ORDER BY o.id;
        """)
        rows_unv = (await conn.execute(q_unv)).fetchall()

    uuids_g40 = set(str(r[0]) for r in rows_g40)
    uuids_g60 = set(str(r[0]) for r in rows_g60)
    uuids_unv = set(str(r[0]) for r in rows_unv)

    print("=== CORRECTED SQL EXECUTION RESULTS ===")
    print(f"Grade 40 Count: {len(uuids_g40)} (Expected: 51)")
    print(f"Grade 60 Count: {len(uuids_g60)} (Expected: 23)")
    print(f"Unverified Malformed Count: {len(uuids_unv)} (Expected: 6)")

    int_g40_g60 = uuids_g40.intersection(uuids_g60)
    int_g40_unv = uuids_g40.intersection(uuids_unv)
    int_g60_unv = uuids_g60.intersection(uuids_unv)

    print(f"Grade40 ∩ Grade60: {len(int_g40_g60)} (expected 0)")
    print(f"Grade40 ∩ Unverified: {len(int_g40_unv)} (expected 0)")
    print(f"Grade60 ∩ Unverified: {len(int_g60_unv)} (expected 0)")

    assert len(uuids_g40) == 51, f"Expected 51 G40, got {len(uuids_g40)}"
    assert len(uuids_g60) == 23, f"Expected 23 G60, got {len(uuids_g60)}"
    assert len(uuids_unv) == 6, f"Expected 6 unverified, got {len(uuids_unv)}"
    assert len(int_g40_g60) == 0
    assert len(int_g40_unv) == 0
    assert len(int_g60_unv) == 0
    print("\nALL CORRECTED SQL ASSERTIONS PASSED WITH ZERO DISCREPANCIES!")

if __name__ == "__main__":
    asyncio.run(test_corrected_sql())

