import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G40

async def test_10_runs():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    results = []
    async with async_session() as db:
        prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G40)
        for i in range(10):
            res = await canonical_engine.compute_canonical_rate_for_product_and_city(db, prod, "Lahore")
            results.append((res.rate_pkr, res.confidence_score, res.contributing_observation_count))
            await asyncio.sleep(0.05)

    print("10 Consecutive Executions:")
    for idx, (rate, conf, count) in enumerate(results):
        print(f"Run {idx+1:02d}: Rate={rate} PKR | Conf={conf} | Contributing={count}")

asyncio.run(test_10_runs())

