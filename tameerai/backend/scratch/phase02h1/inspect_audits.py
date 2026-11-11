import json

with open("scratch/live_sources_audit_results.json", "r", encoding="utf-8") as f:
    live_audit = json.load(f)

print(f"Total entries in live_sources_audit_results.json: {len(live_audit)}")

# Let's inspect fields of live_audit
publishers_in_audit = set()
domains_in_audit = set()
for i, item in enumerate(live_audit):
    url = item.get("url") or item.get("endpoint") or item.get("base_url")
    name = item.get("name") or item.get("publisher") or item.get("source_name")
    code = item.get("source_code") or item.get("code")
    print(f"[{i+1}] Code: {code} | Name: {name} | URL: {url} | Status: {item.get('status') or item.get('http_status')}")

try:
    with open("scratch/additional_sources_audit.json", "r", encoding="utf-8") as f:
        add_audit = json.load(f)
    print(f"\nTotal entries in additional_sources_audit.json: {len(add_audit)}")
    for i, item in enumerate(add_audit):
        print(f"[{i+1}] Name: {item.get('name')} | URL: {item.get('url')} | Status: {item.get('status')} | Classification: {item.get('classification')}")
except Exception as e:
    print(f"Error reading additional_sources_audit.json: {e}")

