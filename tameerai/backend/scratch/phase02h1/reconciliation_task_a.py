import json
from collections import defaultdict

with open("scratch/phase02h1/all_observations.json", "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Total observations in DB: {len(records)}")

# Group records by category of provenance
# Let's inspect sources and provenance
by_provenance = defaultdict(list)
for r in records:
    sc = r["source_code"]
    meta = r["observation_metadata"]
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except:
            meta = {}
    elif meta is None:
        meta = {}

    if sc == "PBS_STATISTICAL_MONTHLY":
        by_provenance["live_pbs_monthly"].append(r)
    elif sc == "STEELRATETODAY_PK_PUBLISHER":
        by_provenance["live_steelratetoday"].append(r)
    elif "test" in sc.lower() or sc.startswith("SRC-PG17") or sc.startswith("PBS_SPI_") or sc.startswith("GHARHUB_SRC_") or sc == "PBS_STATISTICAL_SPI":
        by_provenance["integration_tests"].append(r)
    else:
        by_provenance["other"].append(r)

print("\nProvenance breakdown:")
for k, v in by_provenance.items():
    print(f"  {k}: {len(v)} records")

# Inspect integration tests breakdown
it_sources = defaultdict(list)
for r in by_provenance["integration_tests"]:
    it_sources[r["source_code"]].append(r)

print(f"\nIntegration test records ({len(by_provenance['integration_tests'])} total across {len(it_sources)} sources):")
for sc, recs in sorted(it_sources.items(), key=lambda x: x[1][0]["created_at"]):
    r0 = recs[0]
    print(f"  Source: {sc} | Count: {len(recs)} | Product: {r0['product_code']} | City: {r0['city']} | Price: {r0['observed_price_pkr']} {r0['observed_unit']} | Created: {r0['created_at']}")

# Check duplicate submissions / fingerprints
fps = set()
duplicates = 0
for r in records:
    fp = r["duplicate_fingerprint"]
    if fp in fps:
        duplicates += 1
    else:
        fps.add(fp)

print(f"\nUnique duplicate fingerprints in DB: {len(fps)} (Internal DB duplicates: {duplicates})")

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scratch.phase02h1.pg_helper import get_connection

async def check_source_runs():
    conn = await get_connection()
    try:
        runs = await conn.fetch("""
            SELECT 
                r.id::text,
                r.source_id::text,
                s.code as source_code,
                r.status,
                r.records_discovered,
                r.records_accepted,
                r.records_rejected,
                r.records_duplicated,
                r.error_message,
                r.started_at,
                r.completed_at
            FROM material_rate_source_runs r
            LEFT JOIN material_rate_sources s ON r.source_id = s.id
            ORDER BY r.started_at ASC;
        """)
        print(f"\nSource Runs in DB: {len(runs)}")
        for run in runs:
            print(f"  Run ID: {run['id']} | Source: {run['source_code']} | Status: {run['status']} | Discovered: {run['records_discovered']} | Accepted: {run['records_accepted']} | Duplicated: {run['records_duplicated']} | Rejected: {run['records_rejected']} | Started: {run['started_at']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_source_runs())
