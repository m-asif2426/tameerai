import asyncio
import subprocess
import time
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

PG_BIN = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
PG_DATA = Path("D:/new idea project/tameerai/backend/pgdata17")
PG_LOG = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(PG_BIN / "pg_ctl.exe"), "-D", str(PG_DATA), "-l", str(PG_LOG), "-o", "-p 5433", "start"], check=False)
time.sleep(2)

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async with engine.connect() as conn:
        print('--- PBS Sample Metadata ---')
        res = await conn.execute(text("""
            SELECT o.published_at, o.collected_at, o.observation_metadata 
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
            LIMIT 3
        """))
        for r in res.fetchall():
            print('published_at:', r[0], 'collected_at:', r[1], 'metadata:', r[2])

        print('\n--- SteelRateToday Sample Metadata ---')
        res = await conn.execute(text("""
            SELECT o.published_at, o.collected_at, o.observation_metadata 
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER'
            LIMIT 3
        """))
        for r in res.fetchall():
            print('published_at:', r[0], 'collected_at:', r[1], 'metadata:', r[2])

if __name__ == "__main__":
    asyncio.run(check())
