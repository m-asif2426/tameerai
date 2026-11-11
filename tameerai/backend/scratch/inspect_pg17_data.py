import asyncio
import asyncpg

DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def main():
    import subprocess
    from pathlib import Path
    pg_bin = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
    pg_data = Path("D:/new idea project/tameerai/backend/pgdata17")
    pg_log = Path("D:/new idea project/tameerai/backend/pg17.log")
    subprocess.run([str(pg_bin / "pg_ctl.exe"), "-D", str(pg_data), "-l", str(pg_log), "-o", "-p 5433", "start"], check=False)
    await asyncio.sleep(2)

    conn = await asyncpg.connect(DSN)
    try:
        obs_count = await conn.fetchval("SELECT COUNT(*) FROM material_rate_observations;")
        src_count = await conn.fetchval("SELECT COUNT(*) FROM material_rate_sources;")
        prod_count = await conn.fetchval("SELECT COUNT(*) FROM material_rate_products;")
        
        print(f"PostgreSQL 17 Database State:")
        print(f"   Material Rate Products: {prod_count}")
        print(f"   Material Rate Sources: {src_count}")
        print(f"   Material Rate Observations: {obs_count}")
        
        by_source = await conn.fetch("""
            SELECT s.code, s.name, COUNT(o.id) as obs_count, MIN(o.published_at) as min_date, MAX(o.published_at) as max_date
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            GROUP BY s.code, s.name;
        """)
        print("\nObservations by Source:")
        for r in by_source:
            print(f"   - {r['code']} ({r['name']}): {r['obs_count']} observations | From {r['min_date']} to {r['max_date']}")

        by_cat = await conn.fetch("""
            SELECT p.category, COUNT(o.id) as count, AVG(o.normalized_price_pkr)::numeric(10,2) as avg_price, o.normalized_unit
            FROM material_rate_observations o
            JOIN material_rate_products p ON o.product_id = p.id
            GROUP BY p.category, o.normalized_unit
            ORDER BY count DESC;
        """)
        print("\nObservations by Category:")
        for r in by_cat:
            print(f"   - {r['category']} ({r['normalized_unit']}): {r['count']} observations, Avg Price: Rs. {r['avg_price']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
