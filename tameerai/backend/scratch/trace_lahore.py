import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct
from app.services.material_rates.canonical_engine import canonical_engine

async def trace_lahore():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        steel_prod = (await session.execute(
            select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G60")
        )).scalar_one()

        snap = await canonical_engine.compute_canonical_rate_for_product_and_city(session, steel_prod, "Lahore")
        print("Snap Lahore Rate:", snap.rate_pkr)
        print("Snap Lahore Eligible Count:", snap.eligible_observation_count)
        print("Snap Lahore Contributing Count:", snap.contributing_observation_count)
        print("Snap Lahore Min/Max:", snap.min_rate_pkr, snap.max_rate_pkr)
        print("Snap Lahore Wholesale Rate:", snap.wholesale_rate_pkr)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(trace_lahore())

