"""
Live extraction test for SteelRateToday against isolated PostgreSQL 17.
"""
import asyncio
from datetime import datetime, timezone
import json
import logging
from decimal import Decimal
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import uuid
import httpx
import asyncpg

from app.services.material_rates.adapters.steelratetoday_adapter import SteelRateTodaySourceAdapter
from app.services.material_rates.contracts import RawSourceRecord, PriceBasis
from app.services.material_rates.normalization import normalize_unit_and_price, normalize_city, normalize_location
from app.services.material_rates.fingerprint import generate_observation_fingerprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def main():
    print("=== Testing SteelRateToday Live Extraction & PostgreSQL 17 Persistence ===")
    url = "https://steelratetoday.pk/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (TameerAI/2.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    
    # 1. Fetch
    print(f"Fetching from {url}...")
    start_time = datetime.now(timezone.utc)
    async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url)
    
    print(f"HTTP Status: {resp.status_code}, Length: {len(resp.content)} bytes")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    
    # 2. Parse via SteelRateTodaySourceAdapter
    adapter = SteelRateTodaySourceAdapter()
    raw_records = adapter.parse_raw_data(resp.text)
    print(f"Discovered {len(raw_records)} raw records from live HTML!")
    
    assert len(raw_records) > 0, "No records parsed from live HTML!"
    
    # Sample a few records
    for r in raw_records[:5]:
        print(f"   Record: {r.raw_material_name} | Brand: {r.brand} | Grade: {r.grade} | Price: {r.raw_price} {r.raw_unit} | City: {r.raw_city} | Date: {r.raw_published_date}")

    # 3. Ensure PostgreSQL 17 is running
    pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
    pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
    pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
    subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)
    await asyncio.sleep(2)

    # Connect to PostgreSQL 17
    conn = await asyncpg.connect(DSN)
    try:
        # Ensure source exists in DB
        src_id = await conn.fetchval("""
            INSERT INTO material_rate_sources (id, code, name, source_type, permission_status, reliability_tier, refresh_cadence, freshness_ttl_days, is_active)
            VALUES ($1, 'STEELRATETODAY_PK_PUBLISHER', 'SteelRateToday Rebar & Scrap Market Monitor', 'aggregator', 'permitted', 'indicative', 'daily', 7, true)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, uuid.uuid4())
        
        # Ensure products exist
        prod_map = {}
        for pcode, cat, name, unit in [
            ("STEEL_REBAR_G60", "steel", "Deformed Steel Bar Grade 60", "metric_ton"),
            ("STEEL_REBAR_G40", "steel", "Mild Steel Bar Grade 40", "metric_ton"),
        ]:
            pid = await conn.fetchval("""
                INSERT INTO material_rate_products (id, code, category, canonical_name, standard_unit, volatility_tier, is_active)
                VALUES ($1, $2, $3, $4, $5, 'high', true)
                ON CONFLICT (code) DO UPDATE SET canonical_name = EXCLUDED.canonical_name
                RETURNING id;
            """, uuid.uuid4(), pcode, cat, name, unit)
            prod_map[pcode] = pid

        accepted = 0
        rejected = 0
        duplicates = 0
        
        for r in raw_records:
            try:
                obs_price, obs_unit, norm_price, norm_unit = normalize_unit_and_price(r.raw_price, r.raw_unit)
                norm_city = normalize_city(r.raw_city) or "Lahore"
                
                # Map to product
                p_code = "STEEL_REBAR_G60" if (r.grade and "60" in r.grade) else "STEEL_REBAR_G40"
                product_id = prod_map[p_code]
                
                # Fingerprint
                fp = generate_observation_fingerprint(
                    source_id=src_id,
                    product_id=product_id,
                    city=norm_city,
                    published_at=r.raw_published_date or "2026-09-12",
                    normalized_price_pkr=norm_price,
                    normalized_unit=norm_unit,
                    dealer_id=None,
                )
                
                # Check duplicate
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
                        $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW(),
                        'indicative', $9, $10::jsonb
                    );
                """, uuid.uuid4(), src_id, product_id, norm_city, obs_price, obs_unit, norm_price, norm_unit, fp, json.dumps({
                    "brand": r.brand,
                    "grade": r.grade,
                    "source_url": url,
                    "price_basis": "wholesale",
                    "disclaimer": "Indicative secondary publisher rate",
                }))
                accepted += 1
            except Exception as e:
                rejected += 1
                logger.warning(f"Rejected record: {e}")

        print(f"\n=== Extraction Summary ===")
        print(f"Total Discovered: {len(raw_records)}")
        print(f"Accepted & Inserted into PostgreSQL 17: {accepted}")
        print(f"Duplicates Filtered: {duplicates}")
        print(f"Rejected: {rejected}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
