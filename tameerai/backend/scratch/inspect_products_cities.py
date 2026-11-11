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
from sqlalchemy import select, func, distinct
from app.models.material_rate import MaterialRateObservation, MaterialRateSource, MaterialRateProduct

async def inspect_products_and_cities():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Eligible observations only
        stmt = (
            select(
                MaterialRateProduct.category,
                MaterialRateProduct.code,
                MaterialRateProduct.canonical_name,
                MaterialRateObservation.city,
                func.count(MaterialRateObservation.id)
            )
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateSource.is_active == True,
                MaterialRateSource.permission_status == "permitted",
                MaterialRateSource.reliability_tier.in_(["authoritative", "indicative"]),
                MaterialRateObservation.verification_status.in_(["verified_market_range", "verified_quote", "cross_checked", "indicative"]),
            )
            .group_by(MaterialRateProduct.category, MaterialRateProduct.code, MaterialRateProduct.canonical_name, MaterialRateObservation.city)
            .order_by(MaterialRateProduct.category, MaterialRateProduct.code, MaterialRateObservation.city)
        )
        res = (await session.execute(stmt)).all()
        print(f"Total eligible group rows: {len(res)}")
        categories = set()
        cities = set()
        for cat, code, name, city, cnt in res:
            categories.add(cat)
            cities.add(city)
            print(f"  {cat} | {code} | {city} | count={cnt}")
        print("\nCategories:", sorted(list(categories)))
        print("Cities:", sorted([str(c) for c in cities]))

    await engine.dispose()

asyncio.run(inspect_products_and_cities())
