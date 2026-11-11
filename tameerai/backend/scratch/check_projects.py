import asyncio
import asyncpg

async def check_projects():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'projects' ORDER BY ordinal_position;")
    print("=== PROJECTS COLUMNS ===")
    for c in cols:
        print(f"  {c['column_name']} ({c['data_type']})")
    
    projs = await conn.fetch("SELECT * FROM projects;")
    print(f"\nTotal projects: {len(projs)}")
    for p in projs:
        print(dict(p))
    await conn.close()

if __name__ == '__main__':
    asyncio.run(check_projects())

