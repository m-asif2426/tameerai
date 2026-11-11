import asyncio
import subprocess
from pathlib import Path
import asyncpg

DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

def ensure_pg17_started():
    pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
    pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
    pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
    subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)

async def get_connection():
    ensure_pg17_started()
    for attempt in range(5):
        try:
            return await asyncpg.connect(DSN)
        except Exception:
            await asyncio.sleep(1)
    return await asyncpg.connect(DSN)

