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
from app.models.material_rate import MaterialRateObservation, MaterialRateProduct

async def inspect_steel_prices():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        stmt = (
            select(
                MaterialRateObservation.observed_price_pkr,
                MaterialRateObservation.observed_unit,
                MaterialRateObservation.normalized_price_pkr,
                MaterialRateObservation.normalized_unit,
                MaterialRateObservation.observation_metadata,
            )
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .where(
                MaterialRateProduct.code == "STEEL_REBAR_G60",
                MaterialRateObservation.city == "Lahore",
            )
        )
        res = (await session.execute(stmt)).all()
        for r in res:
            if r[2] < 10000:
                print("Under 10,000 PKR:", r)

    await engine.dispose()

asyncio.run(inspect_steel_prices())
