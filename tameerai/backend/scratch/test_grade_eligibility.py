import asyncio
import os
import sys

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.material_rate import MaterialRateProduct, MaterialRateObservation, MaterialRateSource
from app.services.material_rates.identity_resolver import centralized_identity_resolver, detect_observation_steel_grade

async def test_grade_eligibility():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Fetch all authentic observations for steel
        stmt = (
            select(MaterialRateObservation, MaterialRateSource, MaterialRateProduct)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .where(
                MaterialRateSource.code.in_(["PBS_STATISTICAL_MONTHLY", "STEELRATETODAY_PK_PUBLISHER"])
            )
        )
        res = await session.execute(stmt)
        rows = res.all()

        steel_rows = [
            (o, s, p) for o, s, p in rows
            if "steel" in p.category.lower() or "steel" in (p.code or "").lower()
        ]
        print(f"Total authentic steel observations: {len(steel_rows)}")

        g40_eligible = []
        g60_eligible = []
        unverified = []

        for o, s, p in steel_rows:
            grade = detect_observation_steel_grade(o)
            if grade == "Grade 40":
                g40_eligible.append(o)
            elif grade == "Grade 60":
                g60_eligible.append(o)
            else:
                unverified.append(o)

        print(f"Detected Grade 40: {len(g40_eligible)}")
        print(f"Detected Grade 60: {len(g60_eligible)}")
        print(f"Detected Unverified: {len(unverified)}")

        assert len(g40_eligible) == 51, f"Expected 51 Grade 40, got {len(g40_eligible)}"
        assert len(g60_eligible) == 23, f"Expected 23 Grade 60, got {len(g60_eligible)}"
        assert len(unverified) == 6, f"Expected 6 Unverified, got {len(unverified)}"
        print("\nPERFECT! EXACTLY 51 Grade 40, 23 Grade 60, and 6 Unverified!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_grade_eligibility())

