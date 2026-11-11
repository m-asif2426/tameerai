import sys
from pathlib import Path
backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

import asyncio
import subprocess
import time
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

PG_BIN = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
PG_DATA = Path("D:/new idea project/tameerai/backend/pgdata17")
PG_LOG = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(PG_BIN / "pg_ctl.exe"), "-D", str(PG_DATA), "-l", str(PG_LOG), "-o", "-p 5433", "start"], check=False)
time.sleep(2)

from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    bridge = MaterialRateIntelligenceBridge()

    async with async_session() as session:
        print("=== 1. LIVE PBS QUERY: Cement in Lahore ===")
        res_c = await bridge.resolve_material_rate_query("What is the cement rate in Lahore?", db=session)
        print("Status:", res_c.status)
        print("Evidence count:", len(res_c.evidence_items))
        if res_c.evidence_items:
            item = res_c.evidence_items[0]
            print("Item:", item.product_name, "| Price:", item.price_pkr, "| Basis:", item.price_basis, "| Prov:", item.provenance_label)
            print("Disclaimer:", item.disclaimer)
        print("Benchmark:", res_c.canonical_benchmark.benchmark_rate_pkr if res_c.canonical_benchmark else None)

        print("\n=== 2. LIVE STEELRATETODAY QUERY: Steel in Lahore ===")
        res_s = await bridge.resolve_material_rate_query("Steel rate in Lahore per ton", db=session)
        print("Status:", res_s.status)
        print("Evidence count:", len(res_s.evidence_items))
        if res_s.evidence_items:
            item = res_s.evidence_items[0]
            print("Item:", item.product_name, "| Price:", item.price_pkr, "| Basis:", item.price_basis, "| Prov:", item.provenance_label)
        print("Benchmark:", res_s.canonical_benchmark.benchmark_rate_pkr if res_s.canonical_benchmark else None)

        print("\n=== 3. LIVE NATURAL STONE QUERY: Italian Marble in Gwadar ===")
        res_m = await bridge.resolve_material_rate_query("What is the rate of Italian marble in Gwadar?", db=session)
        print("Status:", res_m.status)
        print("Formatted answer:\n", res_m.formatted_answer)

        print("\n=== 4. LIVE SYNTHETIC EXCLUSION CHECK ===")
        all_res = await bridge.resolve_material_rate_query("Cement in Lahore", db=session)
        for item in all_res.evidence_items:
            assert item.verification_status != "unverified", "Unverified record leaked!"
            assert "synthetic" not in item.source_code.lower(), "Synthetic source leaked!"
            assert "mock" not in item.source_name.lower(), "Mock source leaked!"
        print("Synthetic quarantine verification: PASSED (Zero synthetic records leaked)")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
