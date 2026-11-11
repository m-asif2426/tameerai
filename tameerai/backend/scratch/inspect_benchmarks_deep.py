import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver

async def inspect_benchmarks():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        steel_prod = (await session.execute(
            select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G60")
        )).scalar_one()

        now = datetime.now(timezone.utc)

        # 1. Inspect Lahore
        print("=== TASK 1: LAHORE GRADE 60 OBSERVATIONS AND WEIGHTS ===")
        stmt_lahore = (
            select(MaterialRateObservation, MaterialRateSource)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateObservation.product_id == steel_prod.id,
                MaterialRateObservation.normalized_unit == "metric_ton",
                MaterialRateObservation.city == "Lahore",
            )
        )
        res_l = await session.execute(stmt_lahore)
        lahore_rows = res_l.all()
        print(f"Total Lahore observations: {len(lahore_rows)}")

        scored_l = []
        for o, src in lahore_rows:
            meta = o.observation_metadata or {}
            # compute individual factors
            cred = Decimal("50.0")
            from app.services.material_rates.registry import national_registry
            entry = national_registry.get_source(src.code)
            if entry:
                cred = Decimal(str(entry.credibility_score))
            elif src.reliability_tier == "authoritative":
                cred = Decimal("95.0")
            elif src.reliability_tier == "verified":
                cred = Decimal("80.0")
            
            ver_score = Decimal(str(canonical_engine.TIER_WEIGHTS.get(o.verification_status, 40)))
            
            market_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
            if market_date:
                if market_date.tzinfo is None:
                    market_date = market_date.replace(tzinfo=timezone.utc)
                days_old = max(0.0, (now - market_date).total_seconds() / 86400.0)
                import math
                fresh_score = Decimal(str(round(max(0.0, min(100.0, math.exp(-0.05 * days_old) * 100.0)), 6)))
            else:
                days_old = None
                fresh_score = Decimal("0.0")

            vol_score = Decimal(str(min(100.0, float(len(lahore_rows)) * 20.0)))

            w = canonical_engine.compute_observation_weight(o, src, "Lahore", now, volume_count=len(lahore_rows))
            scored_l.append((o, src, cred, ver_score, fresh_score, vol_score, w, days_old))

        # Sort exactly as canonical engine
        def _sort_key(item):
            o, src, cred, ver_score, fresh_score, vol_score, w, days_old = item
            pub = o.published_at.replace(tzinfo=timezone.utc) if o.published_at and o.published_at.tzinfo is None else (o.published_at or datetime.min.replace(tzinfo=timezone.utc))
            created = o.created_at.replace(tzinfo=timezone.utc) if o.created_at and o.created_at.tzinfo is None else (o.created_at or datetime.min.replace(tzinfo=timezone.utc))
            return (w, pub, created, str(o.id))

        scored_l.sort(key=_sort_key, reverse=True)

        print("\nRANKED LAHORE OBSERVATIONS (TOP 17):")
        for rank, (o, src, cred, ver_score, fresh_score, vol_score, w, days_old) in enumerate(scored_l, 1):
            meta = o.observation_metadata or {}
            print(f"Rank {rank:2}: ID {o.id} | Price: PKR {o.normalized_price_pkr:9} | Brand: {str(meta.get('brand'))[:15]:15} | W: {w:.4f} [Cred={cred}, Ver={ver_score}, Fresh={fresh_score} ({days_old:.1f}d), Vol={vol_score}] | Pub: {o.published_at} | Created: {o.created_at.strftime('%H:%M:%S.%f')}")

        top3_l = scored_l[:3]
        total_w_l = sum(item[6] for item in top3_l)
        weighted_sum_l = sum(item[0].normalized_price_pkr * item[6] for item in top3_l)
        rate_l = (weighted_sum_l / total_w_l)
        print(f"\nTop 3 Lahore Weights: {[float(item[6]) for item in top3_l]}")
        print(f"Top 3 Lahore Prices:  {[float(item[0].normalized_price_pkr) for item in top3_l]}")
        print(f"Lahore Weighted Benchmark Calculation: {weighted_sum_l} / {total_w_l} = PKR {rate_l:.2f}")

        # 2. Inspect National Composite (all 23)
        print("\n\n=== TASK 1: NATIONAL COMPOSITE OBSERVATIONS AND WEIGHTS ===")
        stmt_all = (
            select(MaterialRateObservation, MaterialRateSource)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(
                MaterialRateObservation.product_id == steel_prod.id,
                MaterialRateObservation.normalized_unit == "metric_ton",
            )
        )
        res_all = await session.execute(stmt_all)
        all_rows = [r for r in res_all.all() if not centralized_identity_resolver.is_synthetic_test_fixture(r[0], r[1]) and centralized_identity_resolver.is_observation_eligible_for_product(r[0], steel_prod.code, steel_prod.code)]
        print(f"Total Eligible National G60 observations: {len(all_rows)}")

        scored_nat = []
        for o, src in all_rows:
            w = canonical_engine.compute_observation_weight(o, src, None, now, volume_count=len(all_rows))
            scored_nat.append((o, src, w))

        def _sort_key_nat(item):
            o, src, w = item
            pub = o.published_at.replace(tzinfo=timezone.utc) if o.published_at and o.published_at.tzinfo is None else (o.published_at or datetime.min.replace(tzinfo=timezone.utc))
            created = o.created_at.replace(tzinfo=timezone.utc) if o.created_at and o.created_at.tzinfo is None else (o.created_at or datetime.min.replace(tzinfo=timezone.utc))
            return (w, pub, created, str(o.id))

        scored_nat.sort(key=_sort_key_nat, reverse=True)

        print("\nRANKED NATIONAL OBSERVATIONS (ALL 23):")
        for rank, (o, src, w) in enumerate(scored_nat, 1):
            meta = o.observation_metadata or {}
            print(f"Rank {rank:2}: ID {o.id} | City: {o.city:12} | Price: PKR {o.normalized_price_pkr:9} | Brand: {str(meta.get('brand'))[:15]:15} | W: {w:.4f} | Pub: {o.published_at} | Created: {o.created_at.strftime('%H:%M:%S.%f')}")

        top3_nat = scored_nat[:3]
        total_w_nat = sum(item[2] for item in top3_nat)
        weighted_sum_nat = sum(item[0].normalized_price_pkr * item[2] for item in top3_nat)
        rate_nat = (weighted_sum_nat / total_w_nat)
        print(f"\nTop 3 National Weights: {[float(item[2]) for item in top3_nat]}")
        print(f"Top 3 National Prices:  {[float(item[0].normalized_price_pkr) for item in top3_nat]}")
        print(f"National Weighted Benchmark Calculation: {weighted_sum_nat} / {total_w_nat} = PKR {rate_nat:.2f}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_benchmarks())

