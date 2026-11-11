import httpx
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.material_rates.adapters.pbs_adapter import PbsStatisticalSourceAdapter

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
url = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Urbn-Construction-12.xlsx"
print(f"Fetching official PBS workbook: {url}")
resp = httpx.get(url, headers=headers, timeout=25.0, follow_redirects=True, verify=False)
print("HTTP Status:", resp.status_code, "Length:", len(resp.content), "bytes")

if resp.status_code == 200:
    adapter = PbsStatisticalSourceAdapter()
    records = adapter.parse_raw_data(resp.content)
    print(f"Parsed {len(records)} official records from PBS Urban Construction workbook!")
    for r in records[:5]:
        print(f"   PBS Item: {r.raw_material_name} | City: {r.raw_city} | Price: {r.raw_price} {r.raw_unit} | Date: {r.raw_published_date}")

