import asyncio, os, sys
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource

async def print_all_g60_records():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        # Find all observations from SteelRateToday where normalized_unit == 'metric_ton' and product is STEEL_REBAR_G60
        res = await session.execute(
            select(MaterialRateObservation, MaterialRateProduct, MaterialRateSource)
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateProduct.code == "STEEL_REBAR_G60",
                MaterialRateSource.code == "STEELRATETODAY_PK_PUBLISHER",
                MaterialRateObservation.normalized_unit == "metric_ton",
            )
            .order_by(MaterialRateObservation.city, MaterialRateObservation.normalized_price_pkr)
        )
        rows = res.all()
        print(f"Total matching rows: {len(rows)}")
        prices = []
        for obs, prod, src in rows:
            meta = obs.observation_metadata or {}
            prices.append(obs.normalized_price_pkr)
            print(f"UUID: {obs.id} | City: {obs.city:12} | Price: {obs.normalized_price_pkr:10} | Brand: {meta.get('brand')} | Spec: {meta.get('specification')} | Item: {meta.get('item_name')}")

        if prices:
            print(f"\n--- MATHEMATICAL SUMMARY OF THE {len(prices)} RECORDS ---")
            print(f"Count: {len(prices)}")
            print(f"Min: {min(prices)}")
            print(f"Max: {max(prices)}")
            print(f"Average: {sum(prices) / len(prices):.2f}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(print_all_g60_records())

