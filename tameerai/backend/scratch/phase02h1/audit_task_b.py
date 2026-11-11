import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from urllib.parse import urlparse
from collections import defaultdict
from app.services.material_rates.registry import national_registry

with open("scratch/live_sources_audit_results.json", "r", encoding="utf-8") as f:
    live_audit = json.load(f)

# Extract domains and publishers
endpoint_to_pub = {
    "https://www.pbs.gov.pk/price-statistics/weekly-spi": "Pakistan Bureau of Statistics (PBS)",
    "https://finance.punjab.gov.pk": "Government of the Punjab (Finance / C&W Department)",
    "https://zarea.com/daily-price/cement": "Zarea Limited",
    "https://nha.gov.pk/csr": "National Highway Authority (NHA)",
    "https://cwd.kp.gov.pk/page/composite_schedule_of_rates": "Government of Khyber Pakhtunkhwa (C&W Department)",
    "https://dgcement.com": "D.G. Khan Cement Company Limited",
    "https://mughalsteel.com.pk/": "Mughal Iron & Steel Industries Limited",
    "https://works.sindh.gov.pk": "Government of Sindh (Works & Services Department)",
    "https://www.pbs.gov.pk/price-statistics/": "Pakistan Bureau of Statistics (PBS)",
    "https://steelratetoday.pk/": "SteelRateToday",
    "https://www.bestway.com.pk/products/": "Bestway Cement Limited",
    "https://amrelisteels.com": "Amreli Steels Limited",
    "https://zarea.pk": "Zarea Limited",
    "https://lucky-cement.com/en": "Lucky Cement Limited",
    "https://gharhub.com/steel-rate-in-pakistan/": "GharHub Pakistan",
    "https://gharhub.com/cement-rate-in-pakistan/": "GharHub Pakistan",
    "https://ff.com.pk": "Frontier Foundry Steel (FF Steel)",
    "https://aghasteel.com": "Agha Steel Industries Limited",
    "https://gharhub.com/bricks-rate-in-pakistan/": "GharHub Pakistan",
    "https://gharhub.com/sand-rate-in-pakistan/": "GharHub Pakistan",
    "https://gharhub.com/crush-rate-in-pakistan/": "GharHub Pakistan",
    "https://materialrate.pk/bajri-crush-rate-in-pakistan/": "MaterialRate.pk",
    "https://materialrate.pk/bricks-rate-in-pakistan/": "MaterialRate.pk",
    "https://materialrate.pk/cement-rate-in-pakistan/": "MaterialRate.pk",
    "https://materialrate.pk/saria-rate-in-pakistan/": "MaterialRate.pk",
    "https://materialrate.pk/sand-rate-in-pakistan/": "MaterialRate.pk",
}

print(f"Total audited endpoints in live_sources_audit_results.json: {len(live_audit)}")

pub_groups = defaultdict(list)
for item in live_audit:
    url = item.get("url")
    pub = endpoint_to_pub.get(url, "UNKNOWN")
    pub_groups[pub].append(item)

print(f"\nDistinct Legal Publisher Entities in the 26-Endpoint List: {len(pub_groups)}")
for pub, items in sorted(pub_groups.items()):
    print(f"  - {pub} ({len(items)} endpoint{'s' if len(items)>1 else ''}):")
    for it in items:
        print(f"      URL: {it.get('url')} | HTTP Status: {it.get('status')} | Name: {it.get('name')}")

print("\n--- NationalSourceRegistry Analysis ---")
reg_sources = national_registry.list_sources()
print(f"Total entries in NationalSourceRegistry: {len(reg_sources)}")
for s in reg_sources:
    print(f"  Code: {s.source_code:<28} | Category: {s.category.value:<26} | Status: {s.operational_status.value:<18} | Base URL: {s.base_url}")

# Check adapters implemented
import app.services.material_rates.adapters as adapters_pkg
import pkgutil
adapter_modules = [name for _, name, _ in pkgutil.iter_modules(adapters_pkg.__path__)]
print(f"\nImplemented Adapter Modules in app/services/material_rates/adapters/: {adapter_modules}")
