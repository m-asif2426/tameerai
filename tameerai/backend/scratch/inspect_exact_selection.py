import asyncio
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.material_rate import MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G40, PRODUCT_CODE_STEEL_G60, KNOWN_PRODUCT_ID_G60
from app.services.material_rates.registry import national_registry

async def inspect_exact():
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

        now = datetime.now(timezone.utc)
        obs_list = []
        for o in all_obs:
            if not centralized_identity_resolver.is_observation_eligible_for_product(o, prod.code, stored_product_code=prod.code):
                continue
            if o.city and o.city.lower() != 'lahore':
                continue
            src = sources_map.get(o.source_id)
            ttl_days = float(getattr(src, 'freshness_ttl_days', 45) or 45)
            market_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
            if not centralized_identity_resolver.is_market_date_fresh(market_date, ttl_days=ttl_days, now=now):
                continue
            obs_list.append(o)

        print(f"Total eligible Grade 40 observations: {len(obs_list)}")

        scored_obs = []
        for o in obs_list:
            src = sources_map.get(o.source_id)
            w = canonical_engine.compute_observation_weight(o, src, "Lahore", now, volume_count=len(obs_list))
            scored_obs.append((o, src, w))

        # Check sorting in canonical_engine:
        # scored_obs.sort(
        #     key=lambda pair: (
        #         pair[1],
        #         pair[0].published_at or datetime.min.replace(tzinfo=timezone.utc),
        #         pair[0].created_at or datetime.min.replace(tzinfo=timezone.utc),
        #         str(pair[0].id),
        #     ),
        #     reverse=True,
        # )
        
        # Let's see what each observation has:
        scored_obs.sort(
            key=lambda item: (
                item[2],
                item[0].published_at or datetime.min.replace(tzinfo=timezone.utc),
                item[0].created_at or datetime.min.replace(tzinfo=timezone.utc),
                str(item[0].id),
            ),
            reverse=True,
        )

        print("\nAll 17 sorted observations:")
        for idx, (o, src, w) in enumerate(scored_obs):
            meta = o.observation_metadata or {}
            brand = meta.get("brand") or meta.get("mill") or ""
            print(f"[{idx+1:02d}] ID: {o.id} | Pub: {o.published_at} | Created: {o.created_at} | Weight: {w} | Price: {o.normalized_price_pkr} | Brand: {brand} | Src: {src.code if src else ''}")

        top3 = scored_obs[:3]
        print("\n=== TOP 3 CANDIDATES SELECTED ===")
        total_w = Decimal("0")
        total_num = Decimal("0")
        for idx, (o, src, w) in enumerate(top3):
            meta = o.observation_metadata or {}
            brand = meta.get("brand") or meta.get("mill") or "GENERIC"
            num_i = o.normalized_price_pkr * w
            total_w += w
            total_num += num_i
            print(f"Candidate {idx+1}:")
            print(f"  UUID: {o.id}")
            print(f"  Source: {src.code if src else 'N/A'}")
            print(f"  Brand: {brand}")
            print(f"  Price: {o.normalized_price_pkr}")
            print(f"  Weight (exact): {w} (type: {type(w)})")
            print(f"  Numerator contribution: {num_i}")

        print("\n=== AGGREGATE CALCULATION ===")
        print(f"Exact Numerator Sum: {total_num}")
        print(f"Exact Denominator Sum: {total_w}")
        exact_quotient = total_num / total_w
        print(f"Exact Quotient (unrounded): {exact_quotient}")
        final_rate = exact_quotient.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        print(f"Final Rounded Rate (ROUND_HALF_UP): {final_rate}")

asyncio.run(inspect_exact())

