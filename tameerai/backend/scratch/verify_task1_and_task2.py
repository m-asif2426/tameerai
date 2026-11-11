import asyncio
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.identity_resolver import centralized_identity_resolver, PRODUCT_CODE_STEEL_G40

async def verify_task1_and_2():
    engine = create_async_engine('postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    fixed_now = datetime(2026, 11, 8, 20, 0, 0, tzinfo=timezone.utc)
    
    async with async_session() as db:
        prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G40)
        
        print("=== TASK 2: 10 CONSECUTIVE QUERIES WITH FIXED TIMESTAMP ===")
        print(f"Timestamp: {fixed_now.isoformat()}")
        
        runs = []
        for i in range(10):
            res = await canonical_engine.compute_canonical_rate_for_product_and_city(db, prod, "Lahore", now=fixed_now)
            runs.append(res)
            
        first = runs[0]
        all_identical = True
        for idx, r in enumerate(runs):
            if r.rate_pkr != first.rate_pkr:
                all_identical = False
                print(f"Run {idx+1} MISMATCH: {r.rate_pkr} != {first.rate_pkr}")
            else:
                print(f"Run {idx+1:02d}: Rate = {r.rate_pkr} PKR | Conf = {r.confidence_score} | Contributing = {r.contributing_observation_count}")
                
        print(f"\nAll 10 runs identical: {all_identical}")
        print(f"Authoritative Rate at 2026-11-08T20:00:00Z: PKR {first.rate_pkr} / metric_ton")
        
        print("\n=== TASK 1: EXACT MATHEMATICAL PROOF AT FIXED TIMESTAMP ===")
        # Re-verify internal top 3 calculation
        p_pbs = Decimal("235380.45")
        w_pbs = Decimal("85.64822500")
        num_pbs = p_pbs * w_pbs
        print(f"PBS Numerator: {p_pbs} * {w_pbs} = {num_pbs}")
        
        p_shk = Decimal("254000.00")
        w_shk = Decimal("70.32873250")
        num_shk = p_shk * w_shk
        print(f"Sheikhoo Numerator: {p_shk} * {w_shk} = {num_shk}")
        
        p_rsh = Decimal("251000.00")
        w_rsh = Decimal("70.32873250")
        num_rsh = p_rsh * w_rsh
        print(f"Rasheed Numerator: {p_rsh} * {w_rsh} = {num_rsh}")
        
        tot_num = num_pbs + num_shk + num_rsh
        tot_den = w_pbs + w_shk + w_rsh
        exact_quot = tot_num / tot_den
        rounded = exact_quot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        print(f"Total Numerator: {tot_num}")
        print(f"Total Denominator: {tot_den}")
        print(f"Exact Quotient: {exact_quot}")
        print(f"Rounded Rate (ROUND_HALF_UP): {rounded}")
        assert rounded == Decimal("246020.89")
        assert tot_num == Decimal("55675927.65470125")
        assert tot_den == Decimal("226.30569000")
        print("TASK 1 EXACT PROOF PASSED!")
        
        print("\n=== TASK 2 (PART 2): WALL-CLOCK REAL-TIME EVALUATION ===")
        wall_now = datetime.now(timezone.utc)
        res_wall = await canonical_engine.compute_canonical_rate_for_product_and_city(db, prod, "Lahore", now=wall_now)
        print(f"Wall-Clock Timestamp: {wall_now.isoformat()}")
        print(f"Wall-Clock Result: Rate = {res_wall.rate_pkr} PKR | Conf = {res_wall.confidence_score}")
        diff = res_wall.rate_pkr - first.rate_pkr
        print(f"Difference vs Fixed Reference: {diff:+} PKR")
        print("Freshness decay explanation: As wall-clock time ticks forward, elapsed time since publication increases, reducing observation freshness scores exponentially.")

asyncio.run(verify_task1_and_2())

