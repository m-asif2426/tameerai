import asyncio
import sys
sys.path.insert(0, ".")
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT id, city, normalized_price_pkr, normalized_unit, observation_metadata
            FROM material_rate_observations
            WHERE id IN (
                '07e16342-c18a-42b2-ba00-ed5bd4ace73f',
                '17f86c09-dcda-409f-9e38-ffb344f47600',
                '19aab3db-5c48-4afa-9fcc-ebf791d59683',
                '238ea5d8-791a-4928-a0d8-8d543d97286a',
                '24ecaf51-a617-4da1-9e54-6644f86dad22',
                '43f2eb30-aa09-4506-829b-f5b7104c76ae',
                '4ec9bdb3-caf4-4f9f-94fc-32d2405900e0',
                '568d23ca-d060-447f-b07e-5922f5e46bcf',
                '5fefe33a-fd94-4808-875c-c8b469e77555',
                '72269345-039a-4b05-9cb2-3e8bac530478',
                '9b527040-384d-41b2-8f2d-22c43dde60b6',
                '9f2ec359-5398-4602-ac0b-ee787366251f',
                'b1e6b35d-c0fb-4104-973b-0cf531793733',
                'bea6e920-f4b2-41b0-b25b-a59664a85806',
                'c76857a8-5b54-47b0-b79f-8f2331948c84',
                'ce62fcc8-80f5-47eb-a7a0-48381247e46e',
                'd01316a3-3698-4fed-9614-f1347bafcf2f',
                'd2e1dc23-7f2c-4aac-8c59-dfa1b70ce2b1',
                'd844edb3-4a2a-4419-9261-5bbce8c17c21',
                'da1b7687-13b0-4219-a235-b140cb7f6cac',
                'e0434659-516f-47fd-b433-9144f08749fc',
                'f172f9a5-e0c9-4b4b-a41c-eadde7089fe5',
                'f5ae3e5d-9243-4129-af21-889ab88a341f'
            )
            ORDER BY city, id;
        """))
        rows = res.fetchall()
        for r in rows:
            meta = r[4] or {}
            print(f"{r[0]} | {r[1]:<11} | {r[2]} | grade={meta.get('grade')} | spec={meta.get('specification')} | mill={meta.get('mill')} | brand={meta.get('brand')}")

if __name__ == "__main__":
    asyncio.run(check())

