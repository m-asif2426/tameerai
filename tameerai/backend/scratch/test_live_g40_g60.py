import asyncio
import os
import sys

os.chdir(r"D:\new idea project\tameerai\backend")
sys.path.insert(0, r"D:\new idea project\tameerai\backend")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge

async def main():
    dsn = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
    engine = create_async_engine(dsn, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    bridge = MaterialRateIntelligenceBridge()

    async with async_session() as session:
        # Query Grade 40 in Lahore
        res_g40 = await bridge.resolve_material_rate_query("Steel Grade 40 in Lahore", db=session)
        print("=== GRADE 40 QUERY IN LAHORE ===")
        print(f"Status: {res_g40.status}")
        print(f"Evidence Count: {len(res_g40.evidence_items)}")
        for item in res_g40.evidence_items:
            print(f"- Product: {item.product_name} | Code: {item.product_code} | Price: {item.price_pkr} | Spec: {item.grade_or_spec} | Source: {item.source_name}")
        if res_g40.canonical_benchmark:
            print(f"Benchmark: {res_g40.canonical_benchmark.benchmark_rate_pkr} | Product Code: {res_g40.canonical_benchmark.product_code} | Name: {res_g40.canonical_benchmark.product_name}")

        # Query Grade 60 in Lahore
        res_g60 = await bridge.resolve_material_rate_query("Steel Grade 60 in Lahore", db=session)
        print("\n=== GRADE 60 QUERY IN LAHORE ===")
        print(f"Status: {res_g60.status}")
        print(f"Evidence Count: {len(res_g60.evidence_items)}")
        has_g40 = any("40" in (i.grade_or_spec or "") for i in res_g60.evidence_items)
        print(f"Contains any Grade 40 items: {has_g40}")
        if res_g60.canonical_benchmark:
            print(f"Benchmark: {res_g60.canonical_benchmark.benchmark_rate_pkr} | Product Code: {res_g60.canonical_benchmark.product_code}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

