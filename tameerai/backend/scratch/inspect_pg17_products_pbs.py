import asyncio
import os
import sys

os.chdir(r"D:\new idea project\tameerai\backend")
sys.path.insert(0, r"D:\new idea project\tameerai\backend")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource

async def inspect_products_and_pbs():
    dsn = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
    engine = create_async_engine(dsn, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. All products in database
        res = await session.execute(select(MaterialRateProduct).order_by(MaterialRateProduct.category, MaterialRateProduct.code))
        products = res.scalars().all()
        print("=== 1. ALL PRODUCTS IN DATABASE ===")
        for p in products:
            print(f"ID: {p.id} | Code: {p.code:25} | Cat: {p.category:10} | Subcat: {str(p.subcategory):15} | Unit: {p.standard_unit:10} | Name: {p.canonical_name}")

        # 2. Check PBS observations and their products
        stmt = (
            select(
                MaterialRateProduct.code,
                MaterialRateProduct.canonical_name,
                MaterialRateObservation.id,
                MaterialRateObservation.city,
                MaterialRateObservation.observed_price_pkr,
                MaterialRateObservation.observed_unit,
                MaterialRateObservation.normalized_price_pkr,
                MaterialRateObservation.normalized_unit,
                MaterialRateObservation.observation_metadata,
            )
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(MaterialRateSource.code == "PBS_STATISTICAL_MONTHLY")
        )
        rows = (await session.execute(stmt)).all()
        print(f"\n=== 2. PBS OBSERVATIONS BY PRODUCT ({len(rows)} rows) ===")
        by_prod = {}
        for r in rows:
            by_prod.setdefault(r[0], []).append(r)
        
        for p_code, p_rows in by_prod.items():
            sample = p_rows[0]
            print(f"\nProduct Code: {p_code} (Total: {len(p_rows)} observations)")
            print(f"Canonical Name: {sample[1]}")
            print(f"Sample City: {sample[3]} | Price: {sample[4]} {sample[5]} -> Norm: {sample[6]} {sample[7]}")
            print(f"Sample Metadata: {sample[8]}")

        # 3. Check append-only triggers on material_rate_observations
        trigger_query = text("""
            SELECT tgname, tgenabled, tgtype
            FROM pg_trigger
            JOIN pg_class ON pg_trigger.tgrelid = pg_class.oid
            WHERE pg_class.relname = 'material_rate_observations';
        """)
        triggers = (await session.execute(trigger_query)).all()
        print("\n=== 3. TRIGGERS ON material_rate_observations ===")
        for t in triggers:
            print(f"Trigger Name: {t[0]} | Enabled: {t[1]} | Type: {t[2]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_products_and_pbs())

