import asyncio
import os
import sys

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver

async def check():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        steel_prod = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G60"))).scalar_one()
        print("STEEL_REBAR_G60 ID:", steel_prod.id)
        
        # Query all observations linked to this product
        obs_res = await session.execute(
            select(MaterialRateObservation).where(MaterialRateObservation.product_id == steel_prod.id)
        )
        all_obs = list(obs_res.scalars().all())
        print(f"Total observations with product_id == {steel_prod.id}: {len(all_obs)}")
        
        for o in all_obs:
            meta = o.observation_metadata or {}
            is_synth = centralized_identity_resolver.is_synthetic_test_fixture(o, None)
            is_elig = centralized_identity_resolver.is_observation_eligible_for_product(o, steel_prod.code, steel_prod.code)
            print(f"ID: {o.id} | City: {o.city} | Price: {o.normalized_price_pkr} | Unit: {o.normalized_unit} | Synth: {is_synth} | Elig: {is_elig} | Item: {meta.get('item_name')} | Spec: {meta.get('specification')}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
