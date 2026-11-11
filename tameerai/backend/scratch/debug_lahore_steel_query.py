import sys
from pathlib import Path
backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    bridge = MaterialRateIntelligenceBridge()

    async with async_session() as session:
        query = bridge.parse_material_query("Steel rate in Lahore per ton")
        print("Parsed query:")
        print("  category:", query.material_category)
        print("  product_code:", query.product_code)
        print("  grade:", query.grade)
        print("  city:", query.city)
        print("  unit:", query.unit)
        print("  price_basis:", query.price_basis)

        eligible = await bridge.query_eligible_observations(session, query)
        print(f"\nEligible observations count: {len(eligible)}")
        cities_in_eligible = set(o.city for o, s, p in eligible)
        print(f"Cities present in eligible observations: {cities_in_eligible}")
        for o, s, p in eligible[:10]:
            print(f"  obs_id={o.id} | source={s.code} | city={o.city} | prod={p.code} | price={o.normalized_price_pkr} | unit={o.normalized_unit}")

        res = await bridge.resolve_material_rate_query("Steel rate in Lahore per ton", db=session)
        print(f"\nresolve_material_rate_query evidence_items count: {len(res.evidence_items)}")
        if res.canonical_benchmark:
            print(f"Canonical benchmark data_points_count: {res.canonical_benchmark.data_points_count}")
            print(f"Benchmark rate: {res.canonical_benchmark.benchmark_rate_pkr}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
