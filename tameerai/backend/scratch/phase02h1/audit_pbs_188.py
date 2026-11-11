import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from decimal import Decimal
from scratch.phase02h1.pg_helper import get_connection
import asyncio

async def main():
    conn = await get_connection()
    try:
        rows = await conn.fetch("""
            SELECT 
                o.id::text,
                o.city,
                p.code as product_code,
                p.canonical_name as product_name,
                p.category,
                o.observed_price_pkr::text,
                o.observed_unit,
                o.normalized_price_pkr::text,
                o.normalized_unit,
                o.published_at,
                o.collected_at,
                o.duplicate_fingerprint,
                o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
            ORDER BY o.city, p.category;
        """)

        print(f"Total PBS_STATISTICAL_MONTHLY records in DB: {len(rows)}")

        # Group by city
        by_city = {}
        for r in rows:
            by_city.setdefault(r["city"], []).append(r)

        print(f"Total unique cities stored: {len(by_city)}")
        for city, recs in sorted(by_city.items()):
            cats = [r["category"] for r in recs]
            print(f"  City: '{city}' ({len(recs)} records): {cats}")

        # Group by category
        by_cat = {}
        for r in rows:
            by_cat.setdefault(r["category"], []).append(r)

        print(f"\nTotal unique categories: {len(by_cat)}")
        for cat, recs in sorted(by_cat.items()):
            print(f"  Category: '{cat}' ({len(recs)} records)")

        # Save to JSON for exact documentation
        with open("scratch/phase02h1/pbs_188_observations.json", "w", encoding="utf-8") as f:
            json.dump([dict(r) for r in rows], f, indent=2, default=str)
        print(f"Saved to scratch/phase02h1/pbs_188_observations.json")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

