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
        res = await conn.execute(text("SELECT id, code, category, subcategory, canonical_name, standard_unit FROM material_rate_products ORDER BY category, code"))
        for r in res.fetchall():
            print(f"{r[1]} | cat={r[2]} | subcat={r[3]} | name={r[4]} | unit={r[5]}")

if __name__ == "__main__":
    asyncio.run(check())

