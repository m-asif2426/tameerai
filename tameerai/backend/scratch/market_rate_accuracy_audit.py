import asyncio
import os
import sys
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.canonical_engine import canonical_engine

async def audit_market_rate_accuracy():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # 1. Fetch active products
        res = await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.is_active.is_(True)).order_by(MaterialRateProduct.code))
        products = list(res.scalars().all())
        print(f"=== ACTIVE PRODUCTS AUDIT ({len(products)} products) ===")
        for p in products:
            print(f"Product: {p.code} | Name: {p.canonical_name} | Unit: {p.standard_unit} | Category: {p.category}")

        # 2. Compute canonical snapshot for STEEL_REBAR_G60 across cities
        steel_prod = next((p for p in products if p.code == "STEEL_REBAR_G60"), None)
        cities = ["Karachi", "Lahore", "Islamabad", "Multan", "Peshawar", "Rawalpindi", None]
        
        print("\n=== STEEL_REBAR_G60 CITY-WISE BENCHMARKS ===")
        if steel_prod:
            for city in cities:
                snap = await canonical_engine.compute_canonical_rate_for_product_and_city(session, steel_prod, city)
                if snap:
                    data = snap.to_dict()
                    print(f"City: {data.get('city') or 'National Composite'}")
                    print(f"  Rate PKR: {data.get('rate_pkr')} | Standard Unit: {data.get('unit')}")
                    print(f"  Price Basis: {data.get('price_basis')} | Is Composite: {data.get('is_composite')}")
                    print(f"  Statistical Rate: {data.get('statistical_rate_pkr')} (Obs: {data.get('statistical_observation_count')})")
                    print(f"  Wholesale Rate: {data.get('wholesale_rate_pkr')} (Obs: {data.get('wholesale_observation_count')})")
                    print(f"  Eligible Obs: {data.get('eligible_observation_count')} | Contributing Obs: {data.get('contributing_observation_count')}")
                    print(f"  Price Range: Min={data.get('price_range', {}).get('min')} Max={data.get('price_range', {}).get('max')}")
                    print(f"  Verification Status: {data.get('verification_status')} | Confidence Score: {data.get('confidence_score')}")
                else:
                    print(f"City: {city or 'National Composite'} -> NO SNAPSHOT")

        # 3. Check cement benchmarks
        cement_prod = next((p for p in products if p.code == "CEMENT_OPC_50KG"), None)
        print("\n=== CEMENT_OPC_50KG BENCHMARKS ===")
        if cement_prod:
            for city in ["Karachi", "Lahore", "Islamabad", None]:
                snap = await canonical_engine.compute_canonical_rate_for_product_and_city(session, cement_prod, city)
                if snap:
                    data = snap.to_dict()
                    print(f"City: {data.get('city') or 'National Composite'}")
                    print(f"  Rate PKR: {data.get('rate_pkr')} | Unit: {data.get('unit')} | Basis: {data.get('price_basis')}")
                    print(f"  Statistical Rate: {data.get('statistical_rate_pkr')} | Wholesale Rate: {data.get('wholesale_rate_pkr')}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(audit_market_rate_accuracy())

