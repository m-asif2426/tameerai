import httpx
import re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
resp = httpx.get("https://www.pbs.gov.pk/price-statistics/", headers=headers, timeout=20.0, follow_redirects=True, verify=False)
print("Status:", resp.status_code, "Length:", len(resp.content))

# Look for links to excel or construction
excel_links = re.findall(r'href=["\']([^"\']+\.xlsx?)["\']', resp.text, re.I)
print("Excel links found:", len(excel_links))
for l in excel_links[:10]:
    print("  ", l)

# Look for links containing spi or construction
rel_links = re.findall(r'href=["\']([^"\']*(?:construction|spi|price|monthly|weekly)[^"\']*)["\']', resp.text, re.I)
print("Relevant links found:", len(rel_links))
for l in set(rel_links)[:15]:
    print("  ", l)
