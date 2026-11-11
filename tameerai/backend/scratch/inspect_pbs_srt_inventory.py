import asyncio
import subprocess
import time
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

PG_BIN = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
PG_DATA = Path("D:/new idea project/tameerai/backend/pgdata17")
PG_LOG = Path("D:/new idea project/tameerai/backend/pg17.log")
subprocess.run([str(PG_BIN / "pg_ctl.exe"), "-D", str(PG_DATA), "-l", str(PG_LOG), "-o", "-p 5433", "start"], check=False)
time.sleep(2)

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async with engine.connect() as conn:
        print('--- PBS Observations by Product, Unit, Price Basis ---')
        res = await conn.execute(text("""
            SELECT p.category, p.canonical_name, o.observed_unit, o.normalized_unit, 
                   count(*), min(o.normalized_price_pkr), max(o.normalized_price_pkr),
                   o.verification_status, min(o.published_at), max(o.published_at)
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
            GROUP BY p.category, p.canonical_name, o.observed_unit, o.normalized_unit, o.verification_status
            ORDER BY count(*) DESC
        """))
        for r in res.fetchall():
            print(f"cat={r[0]} | name={r[1]} | unit={r[2]}->{r[3]} | count={r[4]} | price={r[5]}..{r[6]} | status={r[7]} | pub={r[8]}..{r[9]}")

        print('\n--- SteelRateToday Observations by Product, Unit, Price Basis ---')
        res = await conn.execute(text("""
            SELECT p.category, p.canonical_name, o.observed_unit, o.normalized_unit, 
                   count(*), min(o.normalized_price_pkr), max(o.normalized_price_pkr),
                   o.verification_status, min(o.published_at), max(o.published_at)
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER'
            GROUP BY p.category, p.canonical_name, o.observed_unit, o.normalized_unit, o.verification_status
            ORDER BY count(*) DESC
        """))
        for r in res.fetchall():
            print(f"cat={r[0]} | name={r[1]} | unit={r[2]}->{r[3]} | count={r[4]} | price={r[5]}..{r[6]} | status={r[7]} | pub={r[8]}..{r[9]}")

        print('\n--- Distinct Cities in PBS ---')
        res = await conn.execute(text("""
            SELECT DISTINCT city FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
            ORDER BY city
        """))
        cities_pbs = [r[0] for r in res.fetchall()]
        print(f"Total PBS cities ({len(cities_pbs)}): {cities_pbs}")

        print('\n--- Distinct Cities in SteelRateToday ---')
        res = await conn.execute(text("""
            SELECT DISTINCT city FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            WHERE s.code = 'STEELRATETODAY_PK_PUBLISHER'
            ORDER BY city
        """))
        cities_srt = [r[0] for r in res.fetchall()]
        print(f"Total SRT cities ({len(cities_srt)}): {cities_srt}")

if __name__ == "__main__":
    asyncio.run(check())
