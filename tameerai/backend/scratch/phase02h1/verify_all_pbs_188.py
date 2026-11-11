import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
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
                o.observed_price_pkr::text as observed_price,
                o.observed_unit,
                o.normalized_price_pkr::text as normalized_price,
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

        print(f"Total PBS_STATISTICAL_MONTHLY rows: {len(rows)}")

        # Verify all 188 have required attributes
        missing_fields = []
        for r in rows:
            meta = r["observation_metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            elif meta is None:
                meta = {}

            if not r["duplicate_fingerprint"]:
                missing_fields.append((r["id"], "duplicate_fingerprint"))
            if not r["published_at"]:
                missing_fields.append((r["id"], "published_at"))
            if not r["observed_price"]:
                missing_fields.append((r["id"], "observed_price"))
            if not r["normalized_price"]:
                missing_fields.append((r["id"], "normalized_price"))
            if not r["observed_unit"]:
                missing_fields.append((r["id"], "observed_unit"))
            if not r["normalized_unit"]:
                missing_fields.append((r["id"], "normalized_unit"))

        print(f"Verification of 188 records completeness: {len(missing_fields)} missing fields found.")

        # Check unique fingerprints
        fps = set(r["duplicate_fingerprint"] for r in rows)
        print(f"Unique duplicate fingerprints among 188 PBS records: {len(fps)}")

        # Breakdown by category
        from collections import Counter
        cat_counts = Counter(r["category"] for r in rows)
        print("\nCategory breakdown of 188 PBS records:")
        for cat, cnt in sorted(cat_counts.items()):
            print(f"  {cat}: {cnt}")

        # Breakdown by city
        city_counts = Counter(r["city"] for r in rows)
        print(f"\nCity breakdown of 188 PBS records ({len(city_counts)} distinct stored city strings):")
        for city, cnt in sorted(city_counts.items()):
            print(f"  {city}: {cnt}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

