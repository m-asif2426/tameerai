import asyncio
import os
import sys
from datetime import datetime, timezone

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver

async def see_top_3():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        steel_prod = (await session.execute(
            select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G60")
        )).scalar_one()

        # Let's run the exact logic in compute_canonical_rate_for_product_and_city
        city = "Lahore"
        stmt = (
            select(MaterialRateObservation)
            .where(
                MaterialRateObservation.product_id == steel_prod.id,
                MaterialRateObservation.normalized_unit == steel_prod.standard_unit,
            )
        )
        all_obs = list((await session.execute(stmt)).scalars().all())
        
        sources_map = {}
        for o in all_obs:
            if o.source_id not in sources_map:
                src = (await session.execute(select(MaterialRateSource).where(MaterialRateSource.id == o.source_id))).scalar_one_or_none()
                sources_map[o.source_id] = src

        obs_list = []
        for o in all_obs:
            src = sources_map.get(o.source_id)
            if centralized_identity_resolver.is_synthetic_test_fixture(o, src):
                continue
            if not centralized_identity_resolver.is_observation_eligible_for_product(o, steel_prod.code, stored_product_code=steel_prod.code):
                continue
            if city and o.city and o.city.lower() != city.lower():
                continue
            obs_list.append(o)

        print(f"Eligible obs_list count for {city}: {len(obs_list)}")

        now = datetime.now(timezone.utc)
        scored_obs = []
        for o in obs_list:
            w = canonical_engine.compute_observation_weight(o, sources_map.get(o.source_id), city, now, volume_count=len(obs_list))
            scored_obs.append((o, w))

        def _sort_key(pair):
            o, w = pair
            pub = o.published_at or o.created_at
            created = o.created_at
            return (w, pub, created, str(o.id))

        scored_obs.sort(key=_sort_key, reverse=True)

        print("\nTOP 5 CANDIDATES FOR LAHORE:")
        for rank, (o, w) in enumerate(scored_obs[:5], 1):
            meta = o.observation_metadata or {}
            print(f"Rank {rank}: ID={o.id} | Price={o.normalized_price_pkr} | Brand={meta.get('brand')} | Weight={w} | Pub={o.published_at} | Created={o.created_at}")

        top3 = scored_obs[:3]
        total_w = sum(w for _, w in top3)
        weighted_sum = sum(o.normalized_price_pkr * w for o, w in top3)
        print(f"\nWeighted Sum: {weighted_sum}")
        print(f"Total Weight: {total_w}")
        print(f"Rate: {weighted_sum / total_w}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(see_top_3())
