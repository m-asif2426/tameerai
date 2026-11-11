import httpx
import re

url = "https://cwd.kp.gov.pk/page/composite_schedule_of_rates"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
resp = httpx.get(url, headers=headers, timeout=20.0, follow_redirects=True, verify=False)
print("Status:", resp.status_code, "Length:", len(resp.content))
pdf_links = re.findall(r'href=["\']([^"\']+\.pdf)["\']', resp.text, re.I)
print("PDF links found:", len(pdf_links))
for p in pdf_links[:5]:
    print("  ", p)
clean = re.sub(r'<[^>]+>', ' ', resp.text)
print("Text preview:", ' '.join(clean.split())[:300])

