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
from sqlalchemy import select
from app.models.material_rate import MaterialRateObservation, MaterialRateSource, MaterialRateProduct

async def inspect_lahore_steel():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        stmt = (
            select(
                MaterialRateObservation.id,
                MaterialRateObservation.normalized_price_pkr,
                MaterialRateObservation.normalized_unit,
                MaterialRateObservation.published_at,
                MaterialRateObservation.verification_status,
                MaterialRateSource.code,
                MaterialRateSource.reliability_tier,
                MaterialRateSource.permission_status,
                MaterialRateObservation.observation_metadata,
            )
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateProduct.code == "STEEL_REBAR_G60",
                MaterialRateObservation.city == "Lahore",
                MaterialRateSource.is_active == True,
                MaterialRateSource.permission_status == "permitted",
                MaterialRateSource.reliability_tier.in_(["authoritative", "indicative"]),
                MaterialRateObservation.verification_status.in_(["verified_market_range", "verified_quote", "cross_checked", "indicative"]),
            )
        )
        res = (await session.execute(stmt)).all()
        print(f"Total eligible steel G60 in Lahore: {len(res)}")
        for r in res[:5]:
            print(r)

    await engine.dispose()

asyncio.run(inspect_lahore_steel())
