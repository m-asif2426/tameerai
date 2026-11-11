import sys
from pathlib import Path
import subprocess
import asyncio
from decimal import Decimal

backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge, material_rate_bridge

async def run_tests():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        bridge = MaterialRateIntelligenceBridge()
        
        print("=== TEST 1: Cement in Lahore (English) ===")
        res1 = await bridge.resolve_material_rate_query("What is today's cement rate in Lahore?", db=session)
        print("Status:", res1.status)
        print("Evidence count:", len(res1.evidence_items))
        if res1.canonical_benchmark:
            print(f"Benchmark: PKR {res1.canonical_benchmark.benchmark_rate_pkr} / {res1.canonical_benchmark.unit}")
        print("Formatted Answer:\n", res1.formatted_answer)
        print("-" * 50)

        print("=== TEST 2: Steel in Lahore (Brand & Roman Urdu) ===")
        res2 = await bridge.resolve_material_rate_query("Lahore mein Mughal steel saria ka rate kya hai?", db=session)
        print("Status:", res2.status)
        print("Evidence count:", len(res2.evidence_items))
        if res2.canonical_benchmark:
            print(f"Benchmark: PKR {res2.canonical_benchmark.benchmark_rate_pkr} / {res2.canonical_benchmark.unit}")
        print("Formatted Answer:\n", res2.formatted_answer)
        print("-" * 50)

        print("=== TEST 3: Multi-Turn Context Resolution ===")
        history = [
            {"role": "user", "content": "Saria ka rate batao."},
            {"role": "assistant", "content": "Aap kis shehar ke liye saria ka rate malum karna chahte hain?"}
        ]
        res3 = await bridge.resolve_material_rate_query("Lahore mein", db=session, conversation_history=history)
        print("Resolved Category:", res3.query.material_category)
        print("Resolved City:", res3.query.city)
        print("Evidence count:", len(res3.evidence_items))
        print("-" * 50)

        print("=== TEST 4: Unavailable Commodity/City ===")
        res4 = await bridge.resolve_material_rate_query("What is the rate of Italian marble in Gwadar?", db=session)
        print("Status:", res4.status)
        print("Evidence count:", len(res4.evidence_items))
        print("Formatted Answer:\n", res4.formatted_answer)
        print("-" * 50)

        print("=== TEST 5: Urdu Script Query ===")
        res5 = await bridge.resolve_material_rate_query("لاہور میں سیمنٹ کا آج کا ریٹ کیا ہے؟", db=session)
        print("Status:", res5.status)
        print("Formatted Answer:\n", res5.formatted_answer)
        print("-" * 50)

        print("=== TEST 6: Unit Conversion (Per KG) ===")
        res6 = await bridge.resolve_material_rate_query("What is the per kg price of Grade 60 steel in Lahore?", db=session)
        print("Requested unit:", res6.query.unit)
        print("Formatted Answer snippet:")
        print(res6.formatted_answer[:200])
        print("-" * 50)

        print("=== TEST 7: Cross-City Comparison ===")
        res7 = await bridge.resolve_material_rate_query("Karachi aur Lahore mein cement ke rates compare karo.", db=session)
        print("Status:", res7.status)
        print("Comparison cities:", res7.query.comparison_cities)
        print("Formatted Answer:\n", res7.formatted_answer)
        print("-" * 50)

    await engine.dispose()

asyncio.run(run_tests())

