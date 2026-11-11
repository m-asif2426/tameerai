import asyncio
import os
import sys

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sql = """
SELECT 
    CASE 
        WHEN o.normalized_unit != 'metric_ton' OR o.normalized_price_pkr < 10000 THEN 'UNVERIFIED_GRADE'
        WHEN (
            COALESCE(o.observation_metadata->>'item_name', '') ILIKE '%grade 40%' OR
            COALESCE(o.observation_metadata->>'grade', '') = 'Grade 40'
        ) THEN 'VERIFIED_GRADE_40'
        WHEN (
            o.normalized_unit = 'metric_ton' AND
            COALESCE(o.observation_metadata->>'grade', '') = 'Grade 60'
        ) THEN 'VERIFIED_GRADE_60'
        ELSE 'UNVERIFIED_GRADE'
    END AS tier,
    COUNT(*) AS count,
    MIN(o.normalized_price_pkr) AS min_price,
    MAX(o.normalized_price_pkr) AS max_price,
    ROUND(AVG(o.normalized_price_pkr), 2) AS avg_price
FROM material_rate_observations o
JOIN material_rate_sources s ON o.source_id = s.id
JOIN material_rate_products p ON o.product_id = p.id
WHERE s.code IN ('PBS_STATISTICAL_MONTHLY', 'STEELRATETODAY_PK_PUBLISHER')
  AND (p.code IN ('STEEL_REBAR_G60', 'STEEL_REBAR_G40') OR p.category = 'steel')
GROUP BY 1
ORDER BY 1;
"""

async def run_sql():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async with engine.connect() as conn:
        res = await conn.execute(text(sql))
        rows = res.fetchall()
        print("=== THREE-TIER STEEL CLASSIFICATION SQL RESULTS ===")
        for r in rows:
            print(f"Tier: {r[0]:18} | Count: {r[1]:2} | Min: {r[2]:10} | Max: {r[3]:10} | Avg: {r[4]:10}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_sql())

