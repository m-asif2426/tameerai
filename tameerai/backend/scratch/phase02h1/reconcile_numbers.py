import json
from collections import Counter
from datetime import datetime

with open("scratch/phase02h1/all_observations.json", "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Total loaded: {len(records)}")

# Group by source code
sources = Counter(r["source_code"] for r in records)
print("\nSources breakdown:")
for sc, count in sources.most_common():
    print(f"  {sc}: {count}")

# Check timestamps
created_dates = [datetime.fromisoformat(r["created_at"]) for r in records]
print(f"\nEarliest created: {min(created_dates)}")
print(f"Latest created: {max(created_dates)}")

# Categorize into:
# 1. PBS_STATISTICAL_MONTHLY (188)
# 2. STEELRATETODAY_PK_PUBLISHER (45)
# 3. Pre-existing test records prior to 2026-11-07 10:12:00
# 4. New test records created during Phase 02H test run (2026-11-07 10:12:00 onwards)

live_pbs = [r for r in records if r["source_code"] == "PBS_STATISTICAL_MONTHLY"]
live_steel = [r for r in records if r["source_code"] == "STEELRATETODAY_PK_PUBLISHER"]
test_prior_1012 = [r for r in records if r["source_code"] not in ("PBS_STATISTICAL_MONTHLY", "STEELRATETODAY_PK_PUBLISHER") and datetime.fromisoformat(r["created_at"]) < datetime.fromisoformat("2026-11-07T10:12:00+00:00")]
test_after_1012 = [r for r in records if r["source_code"] not in ("PBS_STATISTICAL_MONTHLY", "STEELRATETODAY_PK_PUBLISHER") and datetime.fromisoformat(r["created_at"]) >= datetime.fromisoformat("2026-11-07T10:12:00+00:00")]

print(f"\nExact Grouping:")
print(f"  Live PBS Monthly: {len(live_pbs)}")
print(f"  Live SteelRateToday: {len(live_steel)}")
print(f"  Sum Live Extracted: {len(live_pbs) + len(live_steel)}")
print(f"  Integration Test Records (prior to Phase 02H final test run): {len(test_prior_1012)}")
print(f"  Total at Phase 02H report time: {len(live_pbs) + len(live_steel) + len(test_prior_1012)}")
print(f"  New Integration Test Records (during 10:12-10:14 test run): {len(test_after_1012)}")
print(f"  Current Total: {len(records)}")

print(f"\nTest records added at 10:12-10:14:")
for r in test_after_1012:
    print(f"  {r['id']} | {r['source_code']} | {r['product_code']} | {r['created_at']}")

# Now let's examine the 250 and 256 numbers!
# In the previous reports:
# What was the breakdown by category of the 256 or 262 records?
cat_unit = Counter((r["product_category"], r["normalized_unit"]) for r in records)
print("\nProduct category + normalized unit breakdown for all 266:")
for (cat, unit), cnt in cat_unit.most_common():
    print(f"  {cat} ({unit}): {cnt}")

cat_unit_prior = Counter((r["product_category"], r["normalized_unit"]) for r in records if r not in test_after_1012)
print("\nProduct category + normalized unit breakdown for 262 records:")
for (cat, unit), cnt in cat_unit_prior.most_common():
    print(f"  {cat} ({unit}): {cnt}")

cat_total = Counter(r["product_category"] for r in records if r not in test_after_1012)
print("\nProduct category total for 262 records:")
for cat, cnt in cat_total.most_common():
    print(f"  {cat}: {cnt}")

