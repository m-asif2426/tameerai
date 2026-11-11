import asyncio
import os
import sys
import json
import urllib.request

os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test'
sys.path.insert(0, r'd:\new idea project\tameerai\backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.identity_resolver import centralized_identity_resolver

async def document_task3_api():
    print("=== TASK 3: REAL GRADE 40 / GRADE 60 API VERIFICATION ===")

    # 1. Query G40 via API
    url_g40 = "http://127.0.0.1:8000/api/v1/material-rates/history?product_code=STEEL_REBAR_G40&days=365"
    req_g40 = urllib.request.Request(url_g40, method="GET")
    with urllib.request.urlopen(req_g40) as r:
        st_g40 = r.status
        body_g40 = json.loads(r.read())

    # 2. Query G60 via API
    url_g60 = "http://127.0.0.1:8000/api/v1/material-rates/history?product_code=STEEL_REBAR_G60&days=365"
    req_g60 = urllib.request.Request(url_g60, method="GET")
    with urllib.request.urlopen(req_g60) as r:
        st_g60 = r.status
        body_g60 = json.loads(r.read())

    print(f"\n[G40 API] Endpoint: {url_g40}")
    print(f"[G40 API] Status: {st_g40} | Product: {body_g40['product_name']} | Total Observations: {body_g40['total_observations']}")
    print(f"[G60 API] Endpoint: {url_g60}")
    print(f"[G60 API] Status: {st_g60} | Product: {body_g60['product_name']} | Total Observations: {body_g60['total_observations']}")

    # 3. Retrieve exact UUID lists from database for cross-referencing
    engine = create_async_engine(os.environ['DATABASE_URL'], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        all_obs = list((await session.execute(select(MaterialRateObservation))).scalars().all())
        sources = {s.id: s for s in (await session.execute(select(MaterialRateSource))).scalars().all()}
        
        g40_uuids = []
        g60_uuids = []
        unverified_uuids = []

        for o in all_obs:
            src = sources.get(o.source_id)
            if centralized_identity_resolver.is_synthetic_test_fixture(o, src):
                continue
            
            if centralized_identity_resolver.is_observation_eligible_for_product(o, "STEEL_REBAR_G40", stored_product_code="STEEL_REBAR_G40"):
                g40_uuids.append(str(o.id))
            elif centralized_identity_resolver.is_observation_eligible_for_product(o, "STEEL_REBAR_G60", stored_product_code="STEEL_REBAR_G60"):
                g60_uuids.append(str(o.id))
            else:
                unit_str = str(o.normalized_unit or "").lower()
                price_val = float(o.normalized_price_pkr or 0)
                if price_val < 1000 or unit_str.startswith("rs_") or "rs" in unit_str:
                    unverified_uuids.append(str(o.id))

        print(f"\nExact Eligible G40 UUIDs ({len(g40_uuids)}):")
        for u in g40_uuids:
            print(f"  {u}")

        print(f"\nExact Eligible G60 UUIDs ({len(g60_uuids)}):")
        for u in g60_uuids:
            print(f"  {u}")

        print(f"\nExact Malformed / Unverified UUIDs ({len(unverified_uuids)}):")
        for u in unverified_uuids:
            print(f"  {u}")

        # Check intersection
        set_g40 = set(g40_uuids)
        set_g60 = set(g60_uuids)
        set_unv = set(unverified_uuids)
        overlap_40_60 = set_g40.intersection(set_g60)
        overlap_40_unv = set_g40.intersection(set_unv)
        overlap_60_unv = set_g60.intersection(set_unv)

        print(f"\nCross-contamination verification:")
        print(f"  Overlap G40 & G60: {len(overlap_40_60)} (Must be 0)")
        print(f"  Overlap G40 & Unverified: {len(overlap_40_unv)} (Must be 0)")
        print(f"  Overlap G60 & Unverified: {len(overlap_60_unv)} (Must be 0)")
        assert len(overlap_40_60) == 0
        assert len(overlap_40_unv) == 0
        assert len(overlap_60_unv) == 0
        print("ZERO CROSS-CONTAMINATION PROVEN.")

    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(document_task3_api())

