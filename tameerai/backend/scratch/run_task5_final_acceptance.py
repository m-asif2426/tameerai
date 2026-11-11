import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, desc

from app.models.cost import MaterialRate
from app.models.material_rate import MaterialRateObservation, MaterialRateSource, MaterialRateProduct
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import (
    centralized_identity_resolver,
    PRODUCT_CODE_STEEL_G40,
    PRODUCT_CODE_STEEL_G60,
    KNOWN_PRODUCT_ID_G60,
)
from app.services.material_rates.historical_service import historical_service

async def run_task5_verification():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        print("=== 1. CANONICAL PRODUCT IDENTITIES ===")
        prod_g40 = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G40)
        prod_g60 = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G60)
        print(f"Grade 40 Canonical Product: ID={prod_g40.id} | Code={prod_g40.code} | Name={prod_g40.canonical_name} | Unit={prod_g40.standard_unit}")
        print(f"Grade 60 Canonical Product: ID={prod_g60.id} | Code={prod_g60.code} | Name={prod_g60.canonical_name} | Unit={prod_g60.standard_unit}")

        print("\n=== 2. CANONICAL MARKET RATE CALCULATION (LAHORE G40) ===")
        # Use a fixed reference timestamp for 100% reproducible audit proof
        ref_now = datetime(2026, 11, 8, 20, 0, 0, tzinfo=timezone.utc)
        res_g40 = await canonical_engine.compute_canonical_rate_for_product_and_city(db, prod_g40, "Lahore", now=ref_now)
        
        print(f"Product: {res_g40.product.code} ({res_g40.product.canonical_name})")
        print(f"City: {res_g40.city}")
        print(f"Indicative Composite Rate: PKR {res_g40.rate_pkr} / {res_g40.product.standard_unit}")
        print(f"Statistical Benchmark (PBS): PKR {res_g40.statistical_rate_pkr} / {res_g40.product.standard_unit}")
        print(f"Wholesale Benchmark (Commercial): PKR {res_g40.wholesale_rate_pkr} / {res_g40.product.standard_unit}")
        print(f"Eligible Observation Count: {res_g40.eligible_observation_count}")
        print(f"Contributing Observation Count: {res_g40.contributing_observation_count}")
        print(f"Statistical Observation Count: {res_g40.statistical_observation_count}")
        print(f"Wholesale Observation Count: {res_g40.wholesale_observation_count}")
        print(f"Is Composite: {res_g40.is_composite}")
        print(f"Price Basis: {res_g40.price_basis}")
        print(f"Verification Status: {res_g40.verification_status}")
        print(f"Evidence Quality Score: {res_g40.evidence_quality_score} / 100")
        print(f"Confidence Methodology: {res_g40.confidence_methodology}")

        print("\n=== 3. SYNCHRONIZE INTO MATERIAL_RATES & VERIFY BOQ ISOLATION ===")
        synced_rate = await canonical_engine.synchronize_canonical_rate(db, res_g40)
        print(f"Synchronized Rate ID: {synced_rate.id}")
        print(f"Stored Rate: PKR {synced_rate.rate_pkr}")
        print(f"Stored Verification Status: {synced_rate.verification_status}")
        print(f"Stored Source Name: {synced_rate.source_name}")

        # Simulate BOQ query for verified rates
        boq_stmt = (
            select(MaterialRate)
            .where(
                MaterialRate.product_id == prod_g40.id,
                MaterialRate.city == "Lahore",
                MaterialRate.verification_status.in_(["verified", "verified_quote", "verified_market_range"]),
            )
        )
        boq_rows = (await db.execute(boq_stmt)).scalars().all()
        print(f"BOQ Verified Query Count: {len(boq_rows)} (Expected: 0 - STRICTLY ISOLATED)")

        print("\n=== 4. GRADE 40 VS GRADE 60 DATABASE OBSERVATION ISOLATION ===")
        all_steel_obs_stmt = (
            select(MaterialRateObservation)
            .where(
                MaterialRateObservation.product_id.in_([prod_g40.id, prod_g60.id]),
                MaterialRateObservation.city == "Lahore",
            )
        )
        all_steel_obs = (await db.execute(all_steel_obs_stmt)).scalars().all()
        g40_eligible = []
        g60_eligible = []
        for o in all_steel_obs:
            if centralized_identity_resolver.is_observation_eligible_for_product(o, PRODUCT_CODE_STEEL_G40, stored_product_code=PRODUCT_CODE_STEEL_G40):
                g40_eligible.append(o)
            if centralized_identity_resolver.is_observation_eligible_for_product(o, PRODUCT_CODE_STEEL_G60, stored_product_code=PRODUCT_CODE_STEEL_G60):
                g60_eligible.append(o)

        print(f"Total Lahore Steel Observations in DB: {len(all_steel_obs)}")
        print(f"Eligible for Grade 40: {len(g40_eligible)}")
        print(f"Eligible for Grade 60: {len(g60_eligible)}")
        overlap = set(o.id for o in g40_eligible).intersection(set(o.id for o in g60_eligible))
        print(f"Grade 40 & Grade 60 Overlap: {len(overlap)} (Expected: 0 - 100% MUTUALLY EXCLUSIVE)")

        print("\n=== 5. HISTORICAL SERVICE API COMPATIBILITY ===")
        hist = await historical_service.get_price_history(db, product_code=prod_g40.code, city="Lahore", interval="weekly")
        print(f"History Service Product: {hist.get('product_code')} | Unit: {hist.get('standard_unit')}")
        datapoints = hist.get("data_points", [])
        print(f"History Data Points: {len(datapoints)}")
        if datapoints:
            pt = datapoints[0]
            print(f"Sample Point: Period={pt.get('period')} | Median Price={pt.get('median_price_pkr')} PKR | Count={pt.get('observation_count')}")

asyncio.run(run_task5_verification())
