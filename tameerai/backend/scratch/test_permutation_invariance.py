import asyncio
import random
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.material_rate import MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G40, PRODUCT_CODE_STEEL_G60, KNOWN_PRODUCT_ID_G60

async def test_permutation_invariance():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G40)
        g60_prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G60)
        g60_id = g60_prod.id if g60_prod else KNOWN_PRODUCT_ID_G60
        stmt = (
            select(MaterialRateObservation)
            .where(
                MaterialRateObservation.product_id.in_([prod.id, g60_id]),
                MaterialRateObservation.normalized_unit == prod.standard_unit,
            )
        )
        res = await db.execute(stmt)
        all_obs = list(res.scalars().all())

        sources_res = await db.execute(select(MaterialRateSource))
        sources_map = {s.id: s for s in sources_res.scalars().all()}

        fixed_now = datetime(2026, 11, 8, 20, 30, 0, tzinfo=timezone.utc)
        
        # Filter eligible
        obs_list = []
        for o in all_obs:
            if not centralized_identity_resolver.is_observation_eligible_for_product(o, prod.code, stored_product_code=prod.code):
                continue
            if o.city and o.city.lower() != 'lahore':
                continue
            src = sources_map.get(o.source_id)
            ttl_days = float(getattr(src, 'freshness_ttl_days', 45) or 45)
            market_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
            if not centralized_identity_resolver.is_market_date_fresh(market_date, ttl_days=ttl_days, now=fixed_now):
                continue
            obs_list.append(o)

        print(f"Eligible observations count: {len(obs_list)}")

        def _sort_key(pair):
            o, w = pair
            pub = o.published_at.replace(tzinfo=timezone.utc) if o.published_at and o.published_at.tzinfo is None else (o.published_at or datetime.min.replace(tzinfo=timezone.utc))
            created = o.created_at.replace(tzinfo=timezone.utc) if o.created_at and o.created_at.tzinfo is None else (o.created_at or datetime.min.replace(tzinfo=timezone.utc))
            return (w, pub, created, str(o.id))

        baseline_uuids = None
        baseline_rate = None

        runs_count = 50
        all_matched = True
        for r in range(runs_count):
            shuffled = list(obs_list)
            random.shuffle(shuffled)
            
            scored = []
            for o in shuffled:
                src = sources_map.get(o.source_id)
                w = canonical_engine.compute_observation_weight(o, src, "Lahore", fixed_now, volume_count=len(obs_list))
                scored.append((o, w))

            scored.sort(key=_sort_key, reverse=True)
            top3 = scored[:3]
            top3_uuids = [str(o.id) for o, _ in top3]
            
            total_w = sum(w for _, w in top3)
            weighted_sum = sum(o.normalized_price_pkr * w for o, w in top3)
            rate = (weighted_sum / total_w).quantize(Decimal("0.01"))

            if baseline_uuids is None:
                baseline_uuids = top3_uuids
                baseline_rate = rate
                print(f"Baseline Run 1:")
                print(f"  Top 3 UUIDs: {baseline_uuids}")
                print(f"  Weighted Rate: {baseline_rate} PKR")
            else:
                if top3_uuids != baseline_uuids or rate != baseline_rate:
                    all_matched = False
                    print(f"MISMATCH at run {r+1}: {top3_uuids} != {baseline_uuids}")
                    break

        if all_matched:
            print(f"\nSUCCESS: All {runs_count} randomized permutation runs produced 100% IDENTICAL top 3 UUIDs and rate!")

asyncio.run(test_permutation_invariance())

