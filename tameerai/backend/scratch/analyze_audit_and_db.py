import json
import asyncio
import asyncpg
from pathlib import Path
import subprocess

PG_BIN = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
PG_DATA = Path("D:/new idea project/tameerai/backend/pgdata17")
PG_PORT = 5433
PG_LOG = Path("D:/new idea project/tameerai/backend/pg17.log")
DSN = f"postgresql://postgres@127.0.0.1:{PG_PORT}/tameerai_isolated_test"

async def main():
    print("=== 1. AUDITING 26 CANDIDATES IN live_sources_audit_results.json ===")
    json_path = Path("scratch/live_sources_audit_results.json")
    if json_path.exists():
        entries = json.loads(json_path.read_text(encoding="utf-8"))
        print(f"Total entries recorded: {len(entries)}")
        for i, e in enumerate(entries, 1):
            status = f"HTTP {e['http_status']}" if e.get('http_status') else f"Error: {e.get('error')}"
            print(f"  {i:2d}. {e['name']:25s} | {e['url'][:45]:45s} | {status:20s} | {e['category']}")

    print("\n=== 2. EXACT POSTGRESQL 17 OBSERVATION RECONCILIATION ===")
    # Ensure server running
    subprocess.run([str(PG_BIN / "pg_ctl.exe"), "-D", str(PG_DATA), "-l", str(PG_LOG), "-o", f"-p {PG_PORT}", "start"], check=False)
    await asyncio.sleep(2)

    conn = await asyncpg.connect(DSN)
    try:
        total_obs = await conn.fetchval("SELECT COUNT(*) FROM material_rate_observations;")
        distinct_fp = await conn.fetchval("SELECT COUNT(DISTINCT duplicate_fingerprint) FROM material_rate_observations;")
        print(f"Total observations in DB: {total_obs}")
        print(f"Distinct fingerprints:    {distinct_fp}")

        # By Source
        print("\n--- By Source ---")
        rows = await conn.fetch("""
            SELECT COALESCE(s.code, 'NO_SOURCE') as source_code,
                   COALESCE(s.name, 'Unknown') as source_name,
                   COUNT(o.id) as count,
                   MIN(o.collected_at) as min_collected,
                   MAX(o.collected_at) as max_collected
            FROM material_rate_observations o
            LEFT JOIN material_rate_sources s ON o.source_id = s.id
            GROUP BY s.code, s.name
            ORDER BY count DESC;
        """)
        for r in rows:
            print(f"  {r['source_code']:30s} | {r['count']:4d} obs | {r['min_collected']} -> {r['max_collected']}")

        # By Product & Category
        print("\n--- By Product Category & Unit ---")
        rows = await conn.fetch("""
            SELECT COALESCE(p.category, 'unknown') as category,
                   o.normalized_unit,
                   COUNT(o.id) as count,
                   MIN(o.normalized_price_pkr) as min_price,
                   MAX(o.normalized_price_pkr) as max_price
            FROM material_rate_observations o
            LEFT JOIN material_rate_products p ON o.product_id = p.id
            GROUP BY p.category, o.normalized_unit
            ORDER BY count DESC;
        """)
        for r in rows:
            print(f"  {r['category']:15s} | {r['normalized_unit']:15s} | {r['count']:4d} obs | Range: Rs. {r['min_price']} - {r['max_price']}")

        # Check the test observations created during earlier tests
        print("\n--- Detailed breakdown of ALL sources ---")
        rows = await conn.fetch("""
            SELECT o.id, s.code, p.code as prod_code, p.category, o.city, o.normalized_price_pkr, o.normalized_unit, o.collected_at
            FROM material_rate_observations o
            LEFT JOIN material_rate_sources s ON o.source_id = s.id
            LEFT JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code NOT IN ('PBS_STATISTICAL_MONTHLY', 'STEELRATETODAY_PK_PUBLISHER')
            ORDER BY o.collected_at ASC;
        """)
        print(f"Total non-(PBS/SteelRateToday) observations: {len(rows)}")
        for r in rows:
            print(f"  ID: {r['id']} | Src: {r['code']} | Prod: {r['prod_code']} ({r['category']}) | City: {r['city']} | Price: {r['normalized_price_pkr']} {r['normalized_unit']} | At: {r['collected_at']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

