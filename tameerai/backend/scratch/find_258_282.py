import asyncio, os, sys
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource

async def find_258_282():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        # Search all observations where price >= 258000 and price <= 282000
        stmt = select(MaterialRateObservation).where(
            MaterialRateObservation.normalized_price_pkr >= 258000,
            MaterialRateObservation.normalized_price_pkr <= 282000,
        )
        res = await session.execute(stmt)
        obs_list = list(res.scalars().all())
        print(f"Found {len(obs_list)} observations between 258,000 and 282,000:")
        for o in obs_list:
            # get product
            prod = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.id == o.product_id))).scalar_one_or_none()
            src = (await session.execute(select(MaterialRateSource).where(MaterialRateSource.id == o.source_id))).scalar_one_or_none()
            p_code = prod.code if prod else "NO_PROD"
            s_code = src.code if src else "NO_SRC"
            meta = o.observation_metadata or {}
            print(f"ID: {o.id} | Prod: {p_code} | Src: {s_code} | City: {o.city} | Price: {o.normalized_price_pkr} | Item: {meta.get('item_name')} | Brand: {meta.get('brand')}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(find_258_282())

