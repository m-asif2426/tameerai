import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scratch.phase02h1.pg_helper import get_connection
import asyncio

async def main():
    conn = await get_connection()
    try:
        cnt = await conn.fetchval("SELECT COUNT(*) FROM material_rates;")
        print(f"Total rows in material_rates table: {cnt}")

        if cnt > 0:
            rows = await conn.fetch("SELECT * FROM material_rates LIMIT 10;")
            for r in rows:
                print(dict(r))
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

