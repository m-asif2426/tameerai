import asyncio, os, sys
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource

async def check_grade_field():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        res = await session.execute(
            select(MaterialRateObservation)
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateProduct.code == "STEEL_REBAR_G60",
                MaterialRateSource.code == "STEELRATETODAY_PK_PUBLISHER",
                MaterialRateObservation.normalized_unit == "metric_ton",
            )
        )
        obs_list = list(res.scalars().all())
        print(f"Total G60 observations: {len(obs_list)}")
        for o in obs_list:
            meta = o.observation_metadata or {}
            print(f"UUID: {o.id} | City: {o.city:12} | Price: {o.normalized_price_pkr:10} | grade: {meta.get('grade')} | brand: {meta.get('brand')}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_grade_field())

