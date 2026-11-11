import asyncio
import asyncpg

async def check_user_projects():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    user_id = '374c9682-aef5-4f26-9718-63e242e23dae' # e2e_tester@tameerai.pk
    projs = await conn.fetch("SELECT * FROM projects WHERE user_id = $1;", user_id)
    print(f"Projects for e2e_tester@tameerai.pk ({len(projs)}):")
    for p in projs:
        print(f"  {p['id']} | {p['code']} | {p['name']} | {p['budget_raw']} | {p['created_at']}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(check_user_projects())

