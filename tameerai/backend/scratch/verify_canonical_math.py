import asyncio
from datetime import datetime, timezone
import math
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.services.material_rates.canonical_engine import canonical_engine, CanonicalMarketRateEngine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G40, PRODUCT_CODE_STEEL_G60, KNOWN_PRODUCT_ID_G60
from app.services.material_rates.registry import national_registry
from app.models.material_rate import MaterialRateObservation, MaterialRateSource

async def print_all_17_table():
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
        details = []
        for o in obs_list:
            src = sources_map.get(o.source_id)
            entry = national_registry.get_source(src.code) if src else None
            if entry:
                cred = float(entry.credibility_score)
            elif src and src.reliability_tier == 'authoritative':
                cred = 95.0
            elif src and src.reliability_tier == 'verified':
                cred = 80.0
            else:
                cred = 50.0

            tier_w = float(canonical_engine.TIER_WEIGHTS.get(o.verification_status, 40))
            m_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
            if m_date.tzinfo is None:
                m_date = m_date.replace(tzinfo=timezone.utc)
            days_old = max(0.0, (now - m_date).total_seconds() / 86400.0)
            fresh_pct = max(0.0, min(100.0, math.exp(-0.05 * days_old) * 100.0))
            vol_pct = max(0.0, min(100.0, float(len(obs_list)) * 20.0))

            w = round(max(0.0, min(100.0, (0.35 * cred) + (0.30 * tier_w) + (0.25 * fresh_pct) + (0.10 * vol_pct))), 2)
            meta = o.observation_metadata or {}
            item_desc = meta.get('raw_specification') or meta.get('item_name') or meta.get('brand') or ''
            details.append({
                'id': str(o.id),
                'src': src.code if src else '',
                'item_name': item_desc,
                'price': o.normalized_price_pkr,
                'cred': cred,
                'tier': tier_w,
                'status': o.verification_status,
                'days_old': days_old,
                'fresh': fresh_pct,
                'vol': vol_pct,
                'weight': w,
            })

        details.sort(key=lambda x: x['weight'], reverse=True)
        print(f"{'Idx':<4} | {'UUID':<36} | {'Source':<28} | {'Price PKR':<10} | {'Cred':<5} | {'Tier':<5} | {'Fresh':<6} | {'Vol':<5} | {'Weight':<6}")
        print("-" * 125)
        for i, d in enumerate(details):
            print(f"{i+1:<4} | {d['id']:<36} | {d['src']:<28} | {d['price']:<10.2f} | {d['cred']:<5.1f} | {d['tier']:<5.1f} | {d['fresh']:<6.2f} | {d['vol']:<5.1f} | {d['weight']:<6.2f}")

        # Top 3
        top3 = details[:3]
        top3_w = sum(Decimal(str(d['weight'])) for d in top3)
        top3_num = sum(d['price'] * Decimal(str(d['weight'])) for d in top3)
        top3_avg = (top3_num / top3_w).quantize(Decimal('0.01'))
        print("\n--- TOP 3 BENCHMARK ---")
        print(f"Top 3 Numerator: {top3_num}")
        print(f"Top 3 Denominator: {top3_w}")
        print(f"Top 3 Weighted Rate: PKR {top3_avg} / ton")

        # All 17
        all_w = sum(Decimal(str(d['weight'])) for d in details)
        all_num = sum(d['price'] * Decimal(str(d['weight'])) for d in details)
        all_avg = (all_num / all_w).quantize(Decimal('0.01'))
        print("\n--- ALL 17 BENCHMARK ---")
        print(f"All 17 Numerator: {all_num}")
        print(f"All 17 Denominator: {all_w}")
        print(f"All 17 Weighted Rate: PKR {all_avg} / ton")

        # PBS Statistical
        pbs_items = [d for d in details if 'PBS' in d['src']]
        print("\n--- PBS STATISTICAL (N=1) ---")
        for p in pbs_items:
            print(f"Rate: PKR {p['price']} / ton | Status: {p['status']} | Weight: {p['weight']}")

        # SteelRateToday Wholesale (N=16)
        comm_items = [d for d in details if 'STEELRATETODAY' in d['src']]
        comm_prices = sorted([d['price'] for d in comm_items])
        n_comm = len(comm_prices)
        med_comm = (comm_prices[n_comm//2 - 1] + comm_prices[n_comm//2]) / Decimal('2') if n_comm % 2 == 0 else comm_prices[n_comm//2]
        print("\n--- STEELRATETODAY WHOLESALE (N=16) ---")
        print(f"Count: {n_comm}")
        print(f"Median: PKR {med_comm} / ton")
        print(f"Min: PKR {min(comm_prices)} / ton")
        print(f"Max: PKR {max(comm_prices)} / ton")

asyncio.run(print_all_17_table())
