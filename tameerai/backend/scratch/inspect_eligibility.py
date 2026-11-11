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
from sqlalchemy import select
from app.models.material_rate import MaterialRateObservation, MaterialRateSource, MaterialRateDealerQuote

async def inspect_sources():
    await asyncio.sleep(2)
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        stmt = (
            select(
                MaterialRateObservation.id,
                MaterialRateObservation.verification_status,
                MaterialRateObservation.published_at,
                MaterialRateObservation.collected_at,
                MaterialRateObservation.dealer_quote_id,
                MaterialRateSource.code,
                MaterialRateSource.reliability_tier,
                MaterialRateSource.permission_status,
                MaterialRateSource.is_active.label("source_active"),
                MaterialRateSource.freshness_ttl_days,
            )
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
        )
        res = (await session.execute(stmt)).all()
        print(f"Total observations joined to source: {len(res)}")
        
        eligible_count = 0
        source_counts = {}
        excluded_reasons = {}
        
        for row in res:
            (obs_id, v_status, pub_at, coll_at, quote_id, src_code, src_tier, src_perm, src_act, ttl_days) = row
            
            # Criteria
            is_eligible = True
            reasons = []
            if not src_act:
                is_eligible = False
                reasons.append("src_inactive")
            if src_perm != "permitted":
                is_eligible = False
                reasons.append(f"src_perm={src_perm}")
            if src_tier not in ("authoritative", "indicative") or src_tier == "synthetic":
                is_eligible = False
                reasons.append(f"src_tier={src_tier}")
            if v_status not in ("verified_market_range", "verified_quote", "cross_checked", "indicative") or v_status in ("unverified", "conflicted"):
                is_eligible = False
                reasons.append(f"v_status={v_status}")
            
            # Check quote if dealer quote
            if quote_id is not None:
                pass
            
            # Check date
            effective_date = pub_at or coll_at
            if not effective_date:
                is_eligible = False
                reasons.append("missing_date")
            
            if is_eligible:
                eligible_count += 1
                source_counts[src_code] = source_counts.get(src_code, 0) + 1
            else:
                r_key = tuple(reasons)
                excluded_reasons[r_key] = excluded_reasons.get(r_key, 0) + 1
        
        print(f"Eligible observations count: {eligible_count}")
        print("Eligible by source:")
        for s, cnt in source_counts.items():
            print(f"  {s}: {cnt}")
        print("Excluded observation counts by reason:")
        for r, cnt in excluded_reasons.items():
            print(f"  {r}: {cnt}")

    await engine.dispose()

asyncio.run(inspect_sources())
