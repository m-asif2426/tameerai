import asyncio
import sys
sys.path.insert(0, ".")
from datetime import datetime, timezone
from decimal import Decimal
import math
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import CanonicalMarketRateEngine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G60, KNOWN_PRODUCT_ID_G60

async def calculate():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    canonical_engine = CanonicalMarketRateEngine()

    async with async_session() as session:
        g60_prod = await centralized_identity_resolver.get_canonical_product(session, PRODUCT_CODE_STEEL_G60)
        g60_id = g60_prod.id if g60_prod else KNOWN_PRODUCT_ID_G60

        stmt = select(MaterialRateObservation).where(
            MaterialRateObservation.product_id == g60_id,
            MaterialRateObservation.normalized_unit == 'metric_ton'
        )
        res = await session.execute(stmt)
        all_obs = res.scalars().all()

        eligible_g60 = [o for o in all_obs if centralized_identity_resolver.is_observation_eligible_for_product(o, PRODUCT_CODE_STEEL_G60)]
        
        sources_map = {}
        for o in eligible_g60:
            if o.source_id not in sources_map:
                s_res = await session.execute(select(MaterialRateSource).where(MaterialRateSource.id == o.source_id))
                sources_map[o.source_id] = s_res.scalar_one_or_none()

        t_ref = datetime(2026, 11, 9, 8, 30, 0, 0, tzinfo=timezone.utc)

        # Sort in deterministic order as canonical engine does
        def _sort_key(o):
            src = sources_map.get(o.source_id)
            w = canonical_engine.compute_observation_weight(o, src, o.city or '', t_ref, volume_count=len(eligible_g60))
            pub = o.published_at.replace(tzinfo=timezone.utc) if o.published_at and o.published_at.tzinfo is None else (o.published_at or datetime.min.replace(tzinfo=timezone.utc))
            created = o.created_at.replace(tzinfo=timezone.utc) if o.created_at and o.created_at.tzinfo is None else (o.created_at or datetime.min.replace(tzinfo=timezone.utc))
            return (w, pub, created, str(o.id))

        eligible_g60.sort(key=_sort_key, reverse=True)

        print(f"=== FULL PRECISION SCORING RECONCILIATION FOR ALL 23 OBSERVATIONS ===")
        print(f"Evaluation Timestamp: {t_ref.isoformat()}")
        print("-" * 140)

        rows_data = []
        for idx, o in enumerate(eligible_g60):
            src = sources_map.get(o.source_id)
            m_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
            if m_date.tzinfo is None:
                m_date = m_date.replace(tzinfo=timezone.utc)
            
            delta_sec = (t_ref - m_date).total_seconds()
            days_old = delta_sec / 86400.0
            unrounded_freshness = math.exp(-0.05 * days_old) * 100.0
            rounded_freshness = Decimal(str(round(unrounded_freshness, 6)))

            credibility = Decimal("63.0")
            verification = Decimal("50.0")
            volume = Decimal("100.0")

            c_cred = Decimal("0.35") * credibility
            c_ver = Decimal("0.30") * verification
            c_fresh = Decimal("0.25") * rounded_freshness
            c_vol = Decimal("0.10") * volume

            weight = c_cred + c_ver + c_fresh + c_vol

            # Also check what compute_observation_weight returns
            engine_w = canonical_engine.compute_observation_weight(o, src, o.city or '', t_ref, volume_count=len(eligible_g60))

            assert weight == engine_w, f"Mismatch in row {idx+1}: {weight} != {engine_w}"

            rows_data.append({
                "idx": idx + 1,
                "id": str(o.id),
                "city": o.city,
                "price": o.normalized_price_pkr,
                "pub": o.published_at.isoformat(),
                "col": o.collected_at.isoformat(),
                "m_date": m_date.isoformat(),
                "days_old": days_old,
                "unrounded_freshness": unrounded_freshness,
                "rounded_freshness": rounded_freshness,
                "credibility": credibility,
                "verification": verification,
                "volume": volume,
                "weight": weight
            })

            print(f"#{idx+1:02d} | {str(o.id)} | {o.city:<11} | DaysOld: {days_old:.8f} | UnroundedFresh: {unrounded_freshness:.8f} | RoundedFresh: {rounded_freshness} | Weight: {weight}")

        print("-" * 140)
        print("Detailed verification of weight differences:")
        w_max = rows_data[0]["weight"]
        w_min = rows_data[-1]["weight"]
        print(f"Max Weight (Row 1): {w_max}")
        print(f"Min Weight (Row 23): {w_min}")
        print(f"Exact Difference: {w_max - w_min} (NOT 0.000002!)")
        
        # Check consecutive differences
        diffs = set()
        for i in range(len(rows_data) - 1):
            d = rows_data[i]["weight"] - rows_data[i+1]["weight"]
            diffs.add(d)
        print(f"Unique consecutive differences: {sorted(list(diffs))}")

if __name__ == "__main__":
    asyncio.run(calculate())
