import asyncio
import os
import sys

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def db_forensics():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database();"))
        pg_ver = await conn.scalar(text("SELECT version();"))
        alembic_rev = await conn.scalar(text("SELECT version_num FROM alembic_version;"))
        print(f"Current Database: {db_name}")
        print(f"PostgreSQL Version: {pg_ver}")
        print(f"Alembic Revision: {alembic_rev}")

        # Check all alembic migration files in backend/alembic/versions
        versions_dir = r"d:\new idea project\tameerai\backend\alembic\versions"
        found_in_migrations = []
        if os.path.exists(versions_dir):
            for f in os.listdir(versions_dir):
                if f.endswith(".py"):
                    with open(os.path.join(versions_dir, f), "r", encoding="utf-8") as fp:
                        content = fp.read()
                        if "0195" in content or "01950000" in content:
                            found_in_migrations.append(f)
        print(f"Found '0195' in migrations: {found_in_migrations}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(db_forensics())

