import asyncio
import subprocess
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)

DATABASE_URL = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def audit():
    await asyncio.sleep(2)
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # Check columns of material_rate_observations
        res = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'material_rate_observations'
            ORDER BY ordinal_position
        """))
        print("\n--- Columns in material_rate_observations ---")
        for row in res.fetchall():
            print(f"  {row[0]} ({row[1]}, nullable={row[2]})")

        # Check columns of material_rate_sources
        res = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'material_rate_sources'
            ORDER BY ordinal_position
        """))
        print("\n--- Columns in material_rate_sources ---")
        for row in res.fetchall():
            print(f"  {row[0]} ({row[1]}, nullable={row[2]})")

        # Statuses breakdown
        res = await conn.execute(text("""
            SELECT verification_status, count(*) 
            FROM material_rate_observations 
            GROUP BY verification_status
            ORDER BY count(*) DESC
        """))
        print("\n--- Verification Statuses ---")
        for row in res.fetchall():
            print(f"  verification_status={row[0]}: {row[1]}")

        # Sources breakdown with observation count
        res = await conn.execute(text("""
            SELECT s.code, s.name, s.reliability_tier, s.permission_status, s.is_active, s.freshness_ttl_days, count(o.id)
            FROM material_rate_sources s
            LEFT JOIN material_rate_observations o ON o.source_id = s.id
            GROUP BY s.code, s.name, s.reliability_tier, s.permission_status, s.is_active, s.freshness_ttl_days
            ORDER BY count(o.id) DESC
        """))
        print("\n--- Sources Breakdown ---")
        for row in res.fetchall():
            print(f"  {row[0]} | {row[1]} | tier={row[2]} | perm={row[3]} | active={row[4]} | ttl={row[5]}d | count={row[6]}")

        # Check the 33 records that are not PBS / SteelRateToday
        res = await conn.execute(text("""
            SELECT s.code, o.city, o.verification_status, o.observation_metadata, count(*)
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code NOT IN ('PBS_STATISTICAL_MONTHLY', 'STEELRATETODAY_PK_PUBLISHER')
            GROUP BY s.code, o.city, o.verification_status, o.observation_metadata
        """))
        print("\n--- Other observations (33 records) ---")
        for row in res.fetchall():
            print(f"  source={row[0]} | city={row[1]} | status={row[2]} | metadata={row[3]} | count={row[4]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(audit())
