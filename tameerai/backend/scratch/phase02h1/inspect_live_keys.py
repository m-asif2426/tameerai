import json

with open("scratch/live_sources_audit_results.json", "r", encoding="utf-8") as f:
    live_audit = json.load(f)

for i in range(min(5, len(live_audit))):
    print(f"Sample entry {i}:", live_audit[i])

