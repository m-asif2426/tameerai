"""
Extract exact underlying observation UUIDs, prices, dates, and sources
for Grade 60 across Lahore, Karachi, Islamabad.
"""
import asyncio
import asyncpg
import json

DB_URL = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def run():
    conn = await asyncpg.connect(DB_URL)

    cities = ["Lahore", "Karachi", "Islamabad"]
    for city in cities:
        print(f"\n=======================================================")
        print(f"GRADE 60 OBSERVATIONS FOR CITY: {city.upper()}")
        print(f"=======================================================")
        rows = await conn.fetch("""
            SELECT o.id, o.product_id, p.code as product_code, o.city,
                   o.observed_price_pkr, o.observed_unit, o.normalized_price_pkr,
                   o.normalized_unit, o.published_at, o.source_url,
                   s.name as source_name, o.verification_status,
                   o.observation_metadata
            FROM material_rate_observations o
            JOIN material_rate_products p ON o.product_id = p.id
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE p.code = 'STEEL_REBAR_G60'
              AND o.city ILIKE $1
            ORDER BY o.normalized_price_pkr DESC
        """, city)
        print(f"Total rows found for {city}: {len(rows)}")
        for r in rows:
            meta = r["observation_metadata"]
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: pass
            print(f"- UUID: {r['id']}")
            print(f"  Source: {r['source_name']}")
            print(f"  Observed: {r['observed_price_pkr']} / {r['observed_unit']}")
            print(f"  Normalized: {r['normalized_price_pkr']} / {r['normalized_unit']}")
            print(f"  Published: {r['published_at']}")
            print(f"  Metadata Grade: {meta.get('grade')} | Item: {meta.get('item_name')} | Basis: {meta.get('price_basis')}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())

