import asyncio
import asyncpg

async def check_users():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    users = await conn.fetch("SELECT id, email, full_name, role, is_active, created_at FROM users;")
    print(f"Total users: {len(users)}")
    for u in users:
        print(dict(u))
    await conn.close()

if __name__ == '__main__':
    asyncio.run(check_users())

