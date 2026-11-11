from datetime import datetime, timezone
import math
from decimal import Decimal

def test_freshness_calculation():
    # 1. Timestamps
    # Audit timestamp: 2026-11-09T13:10:00+05:00
    # In UTC: 13:10 - 5 hours = 08:10:00 UTC
    audit_dt = datetime.fromisoformat("2026-11-09T13:10:00+05:00").astimezone(timezone.utc)
    
    # Effective period end: 2026-10-31T23:59:59Z
    period_end = datetime.fromisoformat("2026-10-31T23:59:59+00:00")

    # 2. Elapsed time
    elapsed_delta = audit_dt - period_end
    total_seconds = elapsed_delta.total_seconds()
    days_old = total_seconds / 86400.0

    print("=== PBS FRESHNESS MATHEMATICAL RECONCILIATION ===")
    print(f"Audit Timestamp (Local):    2026-11-09T13:10:00+05:00")
    print(f"Audit Timestamp (UTC):      {audit_dt.isoformat()}")
    print(f"Effective Period End (UTC): {period_end.isoformat()}")
    print(f"Total Elapsed Seconds:      {total_seconds} seconds")
    print(f"Elapsed Time:               {elapsed_delta.days} days, {int(elapsed_delta.seconds // 3600)} hours, {int((elapsed_delta.seconds % 3600) // 60)} minutes, {int(elapsed_delta.seconds % 60)} seconds")
    print(f"Exact Days Old:             {days_old:.6f} days")

    # 3. Configured TTL policy
    TTL_MONTHLY_SERIES_DAYS = 45.0
    print(f"\nConfigured Policy TTL:      {TTL_MONTHLY_SERIES_DAYS} days")
    is_fresh = days_old <= TTL_MONTHLY_SERIES_DAYS
    print(f"Freshness Condition:        ({days_old:.6f} <= {TTL_MONTHLY_SERIES_DAYS}) -> {is_fresh}")
    assert is_fresh, "PBS records evaluated as expired under 45-day TTL!"

    # 4. Freshness score formula from CanonicalMarketRateEngine:
    # freshness_float = max(0.0, min(100.0, math.exp(-0.05 * days_old) * 100.0))
    decay = math.exp(-0.05 * days_old) * 100.0
    freshness_score = round(decay, 2)
    print(f"Freshness Score (Decay):    {freshness_score} / 100.0 (exp(-0.05 * {days_old:.4f}) * 100)")
    print("STATUS: VERIFIED ACTIVE_CURRENT (FRESH)")

if __name__ == "__main__":
    test_freshness_calculation()

