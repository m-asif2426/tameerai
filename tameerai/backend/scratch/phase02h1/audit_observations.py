import asyncio
import json
from decimal import Decimal
import asyncpg
import subprocess
from pathlib import Path

DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

def json_serial(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)

async def main():
    pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
    pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
    pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
    subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)
    await asyncio.sleep(2)

    conn = await asyncpg.connect(DSN)
    try:
        rows = await conn.fetch("""
            SELECT 
                o.id::text as id,
                o.source_id::text as source_id,
                s.code as source_code,
                s.name as source_name,
                o.product_id::text as product_id,
                p.code as product_code,
                p.canonical_name as product_name,
                p.category as product_category,
                o.city,
                o.observed_price_pkr::text as observed_price_pkr,
                o.observed_unit,
                o.normalized_price_pkr::text as normalized_price_pkr,
                o.normalized_unit,
                o.duplicate_fingerprint,
                o.published_at,
                o.collected_at,
                o.created_at,
                o.source_url,
                o.verification_status,
                o.dealer_quote_id::text as dealer_quote_id,
                o.background_job_id::text as background_job_id,
                o.observation_metadata
            FROM material_rate_observations o
            LEFT JOIN material_rate_sources s ON o.source_id = s.id
            LEFT JOIN material_rate_products p ON o.product_id = p.id
            ORDER BY o.created_at ASC;
        """)

        print(f"Total observations in DB: {len(rows)}")

        # Group by source
        by_source = {}
        for r in rows:
            sc = r["source_code"] or "UNKNOWN"
            by_source.setdefault(sc, []).append(r)

        print("\nBreakdown by Source Code:")
        for sc, group in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {sc}: {len(group)} records (Source Name: {group[0]['source_name']})")

        # Let's inspect raw_metadata / observation_metadata and provenance
        def parse_meta(val):
            if val is None:
                return {}
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return {"raw": val}
            return dict(val)

        pbs_monthly = by_source.get("PBS_STATISTICAL_MONTHLY", [])
        print(f"\nPBS_STATISTICAL_MONTHLY: {len(pbs_monthly)} records")
        if pbs_monthly:
            print("  Sample PBS metadata:", json.dumps(parse_meta(pbs_monthly[0]["observation_metadata"]), default=json_serial))
            cities = sorted(list(set(r["city"] for r in pbs_monthly if r["city"])))
            print(f"  Distinct cities in PBS: {len(cities)} -> {cities}")
            cats = set(r["product_category"] for r in pbs_monthly)
            print(f"  Distinct categories in PBS: {cats}")

        steelrate = by_source.get("STEELRATETODAY_PK_PUBLISHER", [])
        print(f"\nSTEELRATETODAY_PK_PUBLISHER: {len(steelrate)} records")
        if steelrate:
            print("  Sample SteelRateToday metadata:", json.dumps(parse_meta(steelrate[0]["observation_metadata"]), default=json_serial))
            cities = sorted(list(set(r["city"] for r in steelrate if r["city"])))
            print(f"  Distinct cities in SteelRateToday: {len(cities)} -> {cities}")
            cats = set(r["product_category"] for r in steelrate)
            print(f"  Distinct categories in SteelRateToday: {cats}")

        # Non-live / test records
        others = [r for r in rows if r["source_code"] not in ("PBS_STATISTICAL_MONTHLY", "STEELRATETODAY_PK_PUBLISHER")]
        print(f"\nOther observations (integration tests / synthetic): {len(others)} records")
        for r in others:
            print(f"  ID: {r['id']} | Src: {r['source_code']} | Prod: {r['product_code']} | City: {r['city']} | Obs: {r['observed_price_pkr']} {r['observed_unit']} -> Norm: {r['normalized_price_pkr']} {r['normalized_unit']} | Created: {r['created_at']} | Status: {r['verification_status']}")

        # Save all rows to json for detailed audit
        out_path = Path("D:/new idea project/tameerai/backend/scratch/phase02h1/all_observations.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([dict(r) for r in rows], f, default=json_serial, indent=2)
        print(f"\nSaved {len(rows)} observations to {out_path}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
