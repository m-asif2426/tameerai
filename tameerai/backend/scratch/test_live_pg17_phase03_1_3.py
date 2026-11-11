import asyncio
import os
import sys
from decimal import Decimal

os.chdir(r"D:\new idea project\tameerai\backend")
sys.path.insert(0, r"D:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateObservation, MaterialRateProduct, MaterialRateSource
from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge

async def main():
    dsn = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
    engine = create_async_engine(dsn, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    bridge = MaterialRateIntelligenceBridge()

    async with async_session() as session:
        # 1. Test Steel Grade 60 query (Lahore)
        res_g60 = await bridge.resolve_material_rate_query("Steel Grade 60 rate in Lahore", db=session)
        print("=== 1. LIVE PG17: Steel Grade 60 Query ===")
        print(f"Status: {res_g60.status}, Evidence Count: {len(res_g60.evidence_items)}")
        has_g40_leak = any("40" in (item.grade_or_spec or "") for item in res_g60.evidence_items)
        print(f"Grade 40 Leak in Grade 60 Query: {has_g40_leak}")
        assert not has_g40_leak, "Grade 40 leaked into Grade 60 query!"

        # 2. Check anonymous query vs dealer quotes
        res_anon = await bridge.resolve_material_rate_query("Steel in Lahore", db=session, project_id=None)
        dealer_items = [i for i in res_anon.evidence_items if i.price_basis == "dealer_direct"]
        print(f"Anonymous Dealer Items: {len(dealer_items)} (Expected: 0)")
        assert len(dealer_items) == 0, "Anonymous query retrieved private dealer quotes!"

        # 3. PBS Unit Conversions in Database
        stmt = (
            select(MaterialRateObservation, MaterialRateProduct)
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .where(MaterialRateSource.code == "PBS_STATISTICAL_MONTHLY")
        )
        pbs_rows = (await session.execute(stmt)).all()
        print(f"\n=== 2. LIVE PG17: PBS Database Unit Integrity ({len(pbs_rows)} observations) ===")
        for obs, prod in pbs_rows[:6]:
            print(f"- {prod.canonical_name[:35]:35} | Raw: {obs.observed_price_pkr:9.2f} / {obs.observed_unit:12} -> Norm: {obs.normalized_price_pkr:9.2f} / {obs.normalized_unit:10}")

    await engine.dispose()
    print("\nALL LIVE PG17 CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())

