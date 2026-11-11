import asyncio
import os
import sys

sys.path.insert(0, r"D:\new idea project\tameerai\backend")
os.chdir(r"D:\new idea project\tameerai\backend")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def main():
    print("=== PRE-EXECUTION SAFETY CHECK ===")
    print(f"ENABLE_MATERIAL_RATE_COLLECTION: {settings.ENABLE_MATERIAL_RATE_COLLECTION}")
    print(f"ENABLE_GEMINI_API: {settings.ENABLE_GEMINI_API}")
    print(f"ENABLE_AI_FEATURES: {settings.ENABLE_AI_FEATURES}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    
    # Check PG17 connection
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT version_num FROM alembic_version"))
        version = res.scalar()
        print(f"Local PostgreSQL 17 Alembic Version: {version}")
        
        db_name = await conn.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
        row = db_name.fetchone()
        print(f"Database Identity: {row}")
        
        # Check table count
        tables_res = await conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        print(f"Total Public Tables in PG17: {tables_res.scalar()}")
        
    await engine.dispose()
    print("Pre-execution check complete.")

if __name__ == "__main__":
    asyncio.run(main())

