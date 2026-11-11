import asyncio
import os
import sys

os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test'
sys.path.insert(0, r'd:\new idea project\tameerai\backend')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def inspect_pg_instance():
    engine = create_async_engine(os.environ['DATABASE_URL'], echo=False)
    
    async with engine.connect() as conn:
        # 1. Cluster info & system identifier
        res_sys = await conn.execute(text("SELECT system_identifier FROM pg_control_system()"))
        sys_id = res_sys.scalar()
        print(f"System Identifier: {sys_id}")

        # 2. Database OID
        res_oid = await conn.execute(text("SELECT oid, datname, datdba FROM pg_database WHERE datname = 'tameerai_isolated_test'"))
        row_oid = res_oid.fetchone()
        print(f"Database OID row: {row_oid}")

        # 3. Data directory setting
        res_dir = await conn.execute(text("SHOW data_directory"))
        print(f"Data Directory: {res_dir.scalar()}")

        # 4. Port, version, start time
        res_ver = await conn.execute(text("SELECT version()"))
        print(f"PostgreSQL Version: {res_ver.scalar()}")
        res_start = await conn.execute(text("SELECT pg_postmaster_start_time()"))
        print(f"Postmaster Start Time: {res_start.scalar()}")

        # 5. Alembic version
        res_alem = await conn.execute(text("SELECT version_num FROM alembic_version"))
        print(f"Alembic Version Num: {res_alem.scalars().all()}")

        # 6. Any other databases in this cluster?
        res_dbs = await conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
        print(f"Non-template databases in cluster: {res_dbs.scalars().all()}")

    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(inspect_pg_instance())

