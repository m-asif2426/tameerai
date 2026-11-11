import asyncio
import sys
from pathlib import Path
import asyncpg
import subprocess

backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def check():
    pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
    pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
    pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
    subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)
    await asyncio.sleep(2)

    conn = await asyncpg.connect(DSN)
    try:
        rev = await conn.fetchval("SELECT version_num FROM alembic_version;")
        obs_count = await conn.fetchval("SELECT count(1) FROM material_rate_observations;")
        src_count = await conn.fetchval("SELECT count(1) FROM material_rate_sources;")
        prod_count = await conn.fetchval("SELECT count(1) FROM material_rate_products;")
        
        print(f"=== PostgreSQL 17 Preflight State ===")
        print(f"Port: 5433 | DB: tameerai_isolated_test")
        print(f"Alembic Revision: {rev}")
        print(f"Total Sources: {src_count}")
        print(f"Total Products: {prod_count}")
        print(f"Total Observations: {obs_count}")

        # Provenance breakdown
        pbs_count = await conn.fetchval("""
            SELECT count(1) FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY';
        """)
        steel_count = await conn.fetchval("""
            SELECT count(1) FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER';
        """)
        synthetic_count = obs_count - pbs_count - steel_count
        print(f"  - PBS Monthly: {pbs_count}")
        print(f"  - SteelRateToday: {steel_count}")
        print(f"  - Synthetic / Test Observations: {synthetic_count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())

