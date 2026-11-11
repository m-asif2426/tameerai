"""
Ingests real PBS Urban Construction live records into PostgreSQL 17.
"""
import asyncio
from datetime import datetime, timezone
import json
import logging
from decimal import Decimal
import sys
from pathlib import Path
import uuid
import httpx
import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.material_rates.adapters.pbs_adapter import PbsStatisticalSourceAdapter
from app.services.material_rates.normalization import normalize_unit_and_price, normalize_city
from app.services.material_rates.fingerprint import generate_observation_fingerprint

DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def main():
    url = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Urbn-Construction-12.xlsx"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
    
    assert resp.status_code == 200, f"PBS returned {resp.status_code}"
    
    adapter = PbsStatisticalSourceAdapter(source_code="PBS_STATISTICAL_MONTHLY", source_name="Pakistan Bureau of Statistics - Monthly Construction Items")
    records = adapter.parse_raw_data(resp.content)
    print(f"Extracted {len(records)} records from official PBS workbook.")

    import subprocess
    pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
    pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
    pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
    subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)
    await asyncio.sleep(2)

    conn = await asyncpg.connect(DSN)
    try:
        # 1. Source
        src_id = await conn.fetchval("""
            INSERT INTO material_rate_sources (id, code, name, source_type, permission_status, reliability_tier, refresh_cadence, freshness_ttl_days, is_active)
            VALUES ($1, 'PBS_STATISTICAL_MONTHLY', 'Pakistan Bureau of Statistics - Monthly Construction Items', 'official', 'permitted', 'authoritative', 'monthly', 45, true)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, uuid.uuid4())

        # 2. Product mappings
        product_cache = {}
        for pcode, cat, name, unit in [
            ("CEMENT_OPC_50KG", "cement", "Ordinary Portland Cement 50kg Bag", "bag_50kg"),
            ("BRICK_CLAY_AWWAL", "bricks", "Clay Bricks Awwal Class", "1000_bricks"),
            ("SAND_CONSTRUCTION_CFT", "sand", "Pit Sand / Construction Sand", "cft"),
            ("CRUSH_AGGREGATE_CFT", "crush", "Crush / Bajri Aggregate", "cft"),
            ("BLOCK_CONCRETE_SOLID", "blocks", "Solid Concrete Masonry Blocks", "piece"),
            ("STEEL_REBAR_G60", "steel", "Deformed Steel Bar Grade 60", "metric_ton"),
        ]:
            pid = await conn.fetchval("""
                INSERT INTO material_rate_products (id, code, category, canonical_name, standard_unit, volatility_tier, is_active)
                VALUES ($1, $2, $3, $4, $5, 'medium', true)
                ON CONFLICT (code) DO UPDATE SET canonical_name = EXCLUDED.canonical_name
                RETURNING id;
            """, uuid.uuid4(), pcode, cat, name, unit)
            product_cache[cat] = pid

        accepted = 0
        duplicates = 0
        rejected = 0

        for r in records:
            try:
                obs_price, obs_unit, norm_price, norm_unit = normalize_unit_and_price(r.raw_price, r.raw_unit)
                norm_city = normalize_city(r.raw_city) or "Islamabad"
                
                # Determine category
                mat_lower = r.raw_material_name.lower()
                if "cement" in mat_lower:
                    cat = "cement"
                elif "brick" in mat_lower:
                    cat = "bricks"
                elif "sand" in mat_lower:
                    cat = "sand"
                elif "crush" in mat_lower or "bajri" in mat_lower:
                    cat = "crush"
                elif "block" in mat_lower:
                    cat = "blocks"
                elif "steel" in mat_lower or "iron" in mat_lower:
                    cat = "steel"
                else:
                    cat = "cement"

                product_id = product_cache[cat]

                fp = generate_observation_fingerprint(
                    source_id=src_id,
                    product_id=product_id,
                    city=norm_city,
                    published_at=r.raw_published_date or "2026-10-01",
                    normalized_price_pkr=norm_price,
                    normalized_unit=norm_unit,
                    dealer_id=None,
                )

                exists = await conn.fetchval("SELECT id FROM material_rate_observations WHERE duplicate_fingerprint = $1", fp)
                if exists:
                    duplicates += 1
                    continue

                await conn.execute("""
                    INSERT INTO material_rate_observations (
                        id, source_id, product_id, city, observed_price_pkr, observed_unit,
                        normalized_price_pkr, normalized_unit, published_at, collected_at,
                        verification_status, duplicate_fingerprint, observation_metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(),
                        'verified_market_range', $10, $11::jsonb
                    );
                """, uuid.uuid4(), src_id, product_id, norm_city, obs_price, obs_unit, norm_price, norm_unit,
                    datetime.fromisoformat(r.raw_published_date) if r.raw_published_date else datetime.now(timezone.utc),
                    fp, json.dumps({
                        "item_name": r.raw_material_name,
                        "source_url": url,
                        "price_basis": "retail_statistical",
                        "agency": "Pakistan Bureau of Statistics",
                    })
                )
                accepted += 1
            except Exception as e:
                rejected += 1

        print(f"\nPBS Ingestion into PostgreSQL 17 Complete:")
        print(f"   Accepted & Inserted: {accepted}")
        print(f"   Duplicates: {duplicates}")
        print(f"   Rejected: {rejected}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
