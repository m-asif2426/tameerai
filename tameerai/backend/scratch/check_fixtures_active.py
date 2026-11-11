import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

from app.core.database import get_session_factory
from sqlalchemy import text

async def check():
    sf = get_session_factory()
    async with sf() as sess:
        print("=== PRODUCTS IS_ACTIVE SUMMARY ===")
        res = await sess.execute(text("SELECT is_active, count(*) FROM material_rate_products GROUP BY is_active"))
        for r in res.fetchall():
            print(dict(r._mapping))
            
        print("\n=== TEST FIXTURE PRODUCTS ===")
        test_prods = await sess.execute(text("""
            SELECT code, is_active FROM material_rate_products 
            WHERE code LIKE 'STEEL_G60_REAL_%' OR code LIKE 'PRD-PG17%' OR code LIKE 'CEMENT_OPC_PG_%'
        """))
        test_rows = test_prods.fetchall()
        print(f"Total test fixture products: {len(test_rows)}")
        print(f"Active test fixture products: {len([r for r in test_rows if r[1] is True])}")
        print(f"Inactive test fixture products: {len([r for r in test_rows if r[1] is False])}")

if __name__ == "__main__":
    asyncio.run(check())

