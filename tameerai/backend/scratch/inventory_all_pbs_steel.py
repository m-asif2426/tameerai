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
        # Check all observations from PBS that might be steel or attached to STEEL_REBAR_G60 or G40
        res = await conn.execute(text("""
            SELECT 
                o.id,
                s.code as source_code,
                o.city,
                o.observed_price_pkr,
                o.observed_unit,
                o.normalized_price_pkr,
                o.normalized_unit,
                p.id as stored_product_id,
                p.code as stored_product_code,
                p.canonical_name as stored_canonical_name,
                o.observation_metadata,
                o.verification_status,
                o.published_at,
                o.collected_at,
                o.created_at
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
              AND (p.code LIKE '%STEEL%' OR p.code LIKE '%REBAR%' OR o.observation_metadata::text ILIKE '%iron%' OR o.observation_metadata::text ILIKE '%steel%')
            ORDER BY o.city, o.created_at
        """))
        rows = res.fetchall()
        print(f"Total PBS steel/iron observations found: {len(rows)}")
        for i, r in enumerate(rows, 1):
            meta = r.observation_metadata if isinstance(r.observation_metadata, dict) else json.loads(r.observation_metadata or "{}")
            item_name = meta.get("item_name")
            raw_spec = meta.get("raw_specification")
            print(f"[{i:02d}] ID: {r.id} | City: {r.city} | Price: {r.observed_price_pkr} / {r.observed_unit} | Product: {r.stored_product_code} | Item: '{item_name}' | Spec: '{raw_spec}'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

