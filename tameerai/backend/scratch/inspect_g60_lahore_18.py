import asyncio
import os
import sys

sys.path.insert(0, r"D:\new idea project\tameerai\backend")
os.chdir(r"D:\new idea project\tameerai\backend")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT 
                o.id,
                s.code as source_code,
                o.city,
                o.observed_price_pkr,
                o.normalized_price_pkr,
                o.verification_status,
                o.published_at,
                o.collected_at,
                o.created_at,
                o.observation_metadata,
                o.dealer_quote_id
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE (lower(o.city) = 'lahore' OR o.city IS NULL)
              AND (p.code = 'STEEL_REBAR_G60' OR o.observation_metadata::text ILIKE '%grade 60%')
            ORDER BY o.created_at
        """))
        rows = res.fetchall()
        print(f"Total candidate Grade 60 records for Lahore: {len(rows)}")
        for i, r in enumerate(rows, 1):
            meta = r.observation_metadata if isinstance(r.observation_metadata, dict) else json.loads(r.observation_metadata or "{}")
            brand = meta.get("brand")
            grade = meta.get("grade")
            item = meta.get("item_name")
            spec = meta.get("raw_specification")
            print(f"[{i:02d}] ID: {r.id} | Source: {r.source_code} | Price: {r.observed_price_pkr} | Status: {r.verification_status} | QuoteID: {r.dealer_quote_id} | Brand: '{brand}' | Grade: '{grade}' | Item: '{item}'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

