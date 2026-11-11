import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

from app.core.database import get_session_factory
from sqlalchemy import text

async def check():
    session_factory = get_session_factory()
    async with session_factory() as sess:
        print("=== TABLES ===")
        res = await sess.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        for r in res.fetchall():
            print(r[0])
            
        print("\n=== PROJECTS COLUMNS ===")
        cols = await sess.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'projects'"))
        for c in cols.fetchall():
            print(c[0])
            
        print("\n=== PROJECTS SAMPLE ===")
        projects = await sess.execute(text('SELECT * FROM projects LIMIT 2'))
        for p in projects.fetchall():
            print(dict(p._mapping))

if __name__ == "__main__":
    asyncio.run(check())
