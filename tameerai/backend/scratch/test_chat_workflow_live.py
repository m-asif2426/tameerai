import sys
from pathlib import Path
import subprocess
import asyncio

backend_dir = Path("D:/new idea project/tameerai/backend")
sys.path.insert(0, str(backend_dir))

pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.ai.workflow.construction_chat import ConstructionChatWorkflow

async def run_chat_tests():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        workflow = ConstructionChatWorkflow()
        
        # Test A: Direct material rate query in English
        print("=== Test A: Direct Query English ===")
        resp_a = await workflow.process_user_query("What is today's cement rate in Lahore?", db=session)
        print("Answer:\n", resp_a.answer)
        print("Grounded:", resp_a.is_grounded, "| Tier:", resp_a.evidence_tier)
        print("Citations count:", len(resp_a.citations))
        print("-" * 50)
        
        # Test B: Turn 1 (missing city) -> Turn 2 (specifying city)
        print("=== Test B: Multi-Turn Conversation ===")
        resp_b1 = await workflow.process_user_query("Saria ka rate batao.", db=session)
        print("Turn 1 Answer:\n", resp_b1.answer)
        print("Turn 1 Telemetry:", resp_b1.telemetry)
        
        history = [
            {"role": "user", "content": "Saria ka rate batao."},
            {"role": "assistant", "content": resp_b1.answer},
        ]
        resp_b2 = await workflow.process_user_query("Lahore mein", conversation_history=history, db=session)
        print("Turn 2 Answer:\n", resp_b2.answer)
        print("Turn 2 Grounded:", resp_b2.is_grounded, "| Tier:", resp_b2.evidence_tier)
        print("Turn 2 Citations count:", len(resp_b2.citations))
        print("-" * 50)
        
        # Test C: Ordinary non-rate query should still work normally
        print("=== Test C: Ordinary Civil Query ===")
        resp_c = await workflow.process_user_query("What is the difference between isolated footing and raft foundation?", db=session)
        print("Ordinary Query Answer snippet:\n", resp_c.answer[:200])
        print("Ordinary Query Grounded:", resp_c.is_grounded)
        print("-" * 50)

    await engine.dispose()

asyncio.run(run_chat_tests())

