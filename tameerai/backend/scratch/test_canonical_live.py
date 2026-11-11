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
from app.models.material_rate import MaterialRateProduct
from app.services.material_rates.canonical_engine import CanonicalMarketRateEngine

async def test_canonical():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    canonical_engine = CanonicalMarketRateEngine()
    async with async_session() as session:
        # 1. Cement in Lahore
        p_cement = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.code == "CEMENT_OPC_50KG"))).scalar_one_or_none()
        if p_cement:
            res_c = await canonical_engine.compute_canonical_rate_for_product_and_city(session, p_cement, "Lahore")
            print("Cement in Lahore:", res_c.to_dict() if res_c else "None")
        
        # 2. Steel G60 in Lahore
        p_steel = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G60"))).scalar_one_or_none()
        if p_steel:
            res_s = await canonical_engine.compute_canonical_rate_for_product_and_city(session, p_steel, "Lahore")
            print("Steel G60 in Lahore:", res_s.to_dict() if res_s else "None")

    await engine.dispose()

asyncio.run(test_canonical())
