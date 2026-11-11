import asyncio
import os
import sys
import json
from decimal import Decimal
import math
from datetime import datetime, timezone

os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test'
sys.path.insert(0, r'd:\new idea project\tameerai\backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver

async def run_task1():
    engine = create_async_engine(os.environ['DATABASE_URL'], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    # Reference audit timestamp from the previous report
    ref_time = datetime(2026, 11, 9, 8, 30, 0, tzinfo=timezone.utc)

    async with async_session() as session:
        steel_prod = (await session.execute(
            select(MaterialRateProduct).where(MaterialRateProduct.code == 'STEEL_REBAR_G60')
        )).scalar_one()

        stmt = select(MaterialRateObservation).where(
            MaterialRateObservation.product_id == steel_prod.id,
            MaterialRateObservation.normalized_unit == steel_prod.standard_unit,
        )
        all_obs = list((await session.execute(stmt)).scalars().all())
        
        sources_map = {}
        for o in all_obs:
            if o.source_id not in sources_map:
                src = (await session.execute(select(MaterialRateSource).where(MaterialRateSource.id == o.source_id))).scalar_one_or_none()
                sources_map[o.source_id] = src

        # National eligible (23)
        national_eligible = []
        for o in all_obs:
            src = sources_map.get(o.source_id)
            if centralized_identity_resolver.is_synthetic_test_fixture(o, src):
                continue
            if not centralized_identity_resolver.is_observation_eligible_for_product(o, steel_prod.code, stored_product_code=steel_prod.code):
                continue
            national_eligible.append(o)

        print(f"Total national eligible: {len(national_eligible)}")

        def score_list(obs_subset, target_city, vol_count):
            results = []
            for o in obs_subset:
                src = sources_map.get(o.source_id)
                m_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
                days_old = max(0.0, (ref_time - m_date).total_seconds() / 86400.0) if m_date else 999.0
                fresh_float = max(0.0, min(100.0, math.exp(-0.05 * days_old) * 100.0))
                fresh_pct = Decimal(str(round(fresh_float, 6)))
                
                # Weight
                w = canonical_engine.compute_observation_weight(o, src, target_city, ref_time, volume_count=vol_count)
                results.append({
                    'obs': o,
                    'price': o.normalized_price_pkr,
                    'city': o.city or 'National',
                    'pub': o.published_at.isoformat() if o.published_at else None,
                    'coll': o.collected_at.isoformat() if o.collected_at else None,
                    'created': o.created_at.isoformat() if o.created_at else None,
                    'days_old': days_old,
                    'cred': Decimal('63.0'),
                    'verif': Decimal('50.0'),
                    'fresh_pct': fresh_pct,
                    'vol_pct': Decimal('100.0'),
                    'weight': w,
                })
            
            # Sort as engine does: (weight, pub, created, id)
            def _sort_key(item):
                o = item['obs']
                w = item['weight']
                pub = o.published_at or o.created_at
                created = o.created_at
                return (w, pub, created, str(o.id))
            
            results.sort(key=_sort_key, reverse=True)
            for rank, r in enumerate(results, 1):
                r['rank'] = rank
            return results

        lahore_subset = [o for o in national_eligible if o.city and o.city.lower() == 'lahore']
        lahore_scored = score_list(lahore_subset, 'Lahore', len(lahore_subset))
        national_scored = score_list(national_eligible, '', len(national_eligible))

        print("\n================== LAHORE 17 OBSERVATIONS ==================")
        for r in lahore_scored:
            sel = "SELECTED (Rank 1-3)" if r['rank'] <= 3 else f"EXCLUDED (Rank {r['rank']} > 3)"
            print(f"Rank {r['rank']:2d} | ID: {r['obs'].id} | Price: {r['price']:9.2f} | W: {r['weight']} | Fresh: {r['fresh_pct']} | DaysOld: {r['days_old']:.6f} | Pub: {r['pub']} | {sel}")

        print("\n================== NATIONAL 23 OBSERVATIONS ==================")
        for r in national_scored:
            sel = "SELECTED (Rank 1-3)" if r['rank'] <= 3 else f"EXCLUDED (Rank {r['rank']} > 3)"
            print(f"Rank {r['rank']:2d} | City: {r['city']:12s} | ID: {r['obs'].id} | Price: {r['price']:9.2f} | W: {r['weight']} | Fresh: {r['fresh_pct']} | DaysOld: {r['days_old']:.6f} | Created: {r['created']} | {sel}")

        # Mathematical comparison
        print("\n=== METHODOLOGY COMPARISON: LAHORE ===")
        top3_lahore = lahore_scored[:3]
        top3_w_sum = sum(r['price'] * r['weight'] for r in top3_lahore)
        top3_tot_w = sum(r['weight'] for r in top3_lahore)
        top3_rate = top3_w_sum / top3_tot_w

        all_lahore_w_sum = sum(r['price'] * r['weight'] for r in lahore_scored)
        all_lahore_tot_w = sum(r['weight'] for r in lahore_scored)
        all_lahore_rate = all_lahore_w_sum / all_lahore_tot_w

        prices_lahore = [float(r['price']) for r in lahore_scored]
        prices_lahore.sort()
        median_lahore = prices_lahore[len(prices_lahore)//2]
        mean_lahore = sum(prices_lahore) / len(prices_lahore)

        print(f"Top-3 Weighted Rate: {top3_rate:.2f} PKR")
        print(f"All-Eligible (17) Weighted Rate: {all_lahore_rate:.2f} PKR")
        print(f"Arithmetic Mean (17): {mean_lahore:.2f} PKR")
        print(f"Median (17): {median_lahore:.2f} PKR")

        print("\n=== METHODOLOGY COMPARISON: NATIONAL ===")
        top3_nat = national_scored[:3]
        top3_nat_w_sum = sum(r['price'] * r['weight'] for r in top3_nat)
        top3_nat_tot_w = sum(r['weight'] for r in top3_nat)
        top3_nat_rate = top3_nat_w_sum / top3_nat_tot_w

        all_nat_w_sum = sum(r['price'] * r['weight'] for r in national_scored)
        all_nat_tot_w = sum(r['weight'] for r in national_scored)
        all_nat_rate = all_nat_w_sum / all_nat_tot_w

        prices_nat = [float(r['price']) for r in national_scored]
        prices_nat.sort()
        median_nat = prices_nat[len(prices_nat)//2]
        mean_nat = sum(prices_nat) / len(prices_nat)

        print(f"Top-3 Weighted Rate: {top3_nat_rate:.2f} PKR")
        print(f"All-Eligible (23) Weighted Rate: {all_nat_rate:.2f} PKR")
        print(f"Arithmetic Mean (23): {mean_nat:.2f} PKR")
        print(f"Median (23): {median_nat:.2f} PKR")

    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(run_task1())

