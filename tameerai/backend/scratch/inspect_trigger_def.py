import asyncio
import os
import sys

os.chdir(r"D:\new idea project\tameerai\backend")
sys.path.insert(0, r"D:\new idea project\tameerai\backend")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT tgname, proname, prosrc
            FROM pg_trigger
            JOIN pg_proc ON pg_trigger.tgfoid = pg_proc.oid
            WHERE tgname = 'trg_protect_immutable_observations';
        """))
        for row in res.fetchall():
            print(f"TRIGGER: {row[0]}, FUNC: {row[1]}\n{row[2]}\n")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
