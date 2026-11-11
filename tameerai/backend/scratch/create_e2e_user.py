import sys
sys.path.insert(0, 'd:/new idea project/tameerai/backend')
import asyncio
import asyncpg
from app.core.security import hash_password

async def main():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    pwd_hash = hash_password('Password123!')
    await conn.execute("""
        INSERT INTO users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES (gen_random_uuid(), 'e2e_tester@tameerai.pk', $1, 'Engr. Playwright E2E', 'engineer', true, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password, is_active = true
    """, pwd_hash)
    row = await conn.fetchrow("SELECT id, email, full_name, role FROM users WHERE email = 'e2e_tester@tameerai.pk'")
    print("E2E User ready:", dict(row))
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

