import sys
from pathlib import Path
import subprocess
import asyncio

backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models.material_rate import MaterialRateObservation, MaterialRateSource

async def inspect_dates():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        stmt = (
            select(
                MaterialRateSource.code,
                func.min(MaterialRateObservation.published_at),
                func.max(MaterialRateObservation.published_at),
                func.min(MaterialRateObservation.collected_at),
                func.max(MaterialRateObservation.collected_at),
                func.count(MaterialRateObservation.id)
            )
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateSource.is_active == True,
                MaterialRateSource.permission_status == "permitted",
                MaterialRateSource.reliability_tier.in_(["authoritative", "indicative"]),
                MaterialRateObservation.verification_status.in_(["verified_market_range", "verified_quote", "cross_checked", "indicative"]),
            )
            .group_by(MaterialRateSource.code)
        )
        res = (await session.execute(stmt)).all()
        for code, min_pub, max_pub, min_col, max_col, cnt in res:
            print(f"Source: {code}")
            print(f"  Count: {cnt}")
            print(f"  Published: {min_pub} -> {max_pub}")
            print(f"  Collected: {min_col} -> {max_col}")

    await engine.dispose()

asyncio.run(inspect_dates())
