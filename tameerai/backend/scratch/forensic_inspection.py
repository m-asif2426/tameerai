import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.material_rate import MaterialRateObservation, MaterialRateSource, MaterialRateProduct
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G40
from app.services.material_rates.registry import national_registry

async def forensic_inspection():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        print("=== 1. SOURCES IN DB ===")
        sources_res = await db.execute(select(MaterialRateSource))
        sources = sources_res.scalars().all()
        for s in sources:
            reg_entry = national_registry.get_source(s.code)
            reg_cred = reg_entry.credibility_score if reg_entry else "NOT_IN_REGISTRY"
            print(f"ID: {s.id} | Code: {s.code:<30} | Tier: {s.reliability_tier:<14} | Reg Cred: {reg_cred} | TTL: {s.freshness_ttl_days}d")

        print("\n=== 2. CANONICAL ENGINE COMPUTATION ===")
        prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G40)
        res = await canonical_engine.compute_canonical_rate_for_product_and_city(db, prod, "Lahore")
        
        print(f"Product: {res.product.code} - {res.product.canonical_name}")
        print(f"City: {res.city}")
        print(f"Final Benchmark Rate: {res.rate_pkr} PKR / {res.product.standard_unit}")
        print(f"Eligible Count: {res.eligible_observation_count}")
        print(f"Contributing Count: {res.contributing_observation_count}")
        print(f"Statistical Count: {res.statistical_observation_count} (Rate: {res.statistical_rate_pkr})")
        print(f"Wholesale Count: {res.wholesale_observation_count} (Rate: {res.wholesale_rate_pkr})")
        print(f"Is Composite: {res.is_composite}")
        print(f"Verification Status: {res.verification_status}")
        print(f"Price Basis: {res.price_basis}")
        print(f"Confidence Score: {res.confidence_score}")
        print(f"Evidence Quality Score: {res.evidence_quality_score}")
        print(f"Confidence Methodology: {res.confidence_methodology}")

asyncio.run(forensic_inspection())

