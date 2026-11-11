import httpx
import re

url = "https://zarea.com/daily-price/cement"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
resp = httpx.get(url, headers=headers, timeout=20.0, follow_redirects=True)
print("Status:", resp.status_code, "Length:", len(resp.content))

# Look for table or prices
tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL | re.I)
print("Tables count:", len(tables))
for i, t in enumerate(tables):
    clean = re.sub(r'<[^>]+>', ' ', t)
    clean_lines = [l.strip() for l in clean.split('\n') if l.strip()]
    print(f"Table {i+1} preview: {' '.join(clean_lines)[:300]}")

# Look for price keywords
prices = re.findall(r'(?:Rs\.?|PKR)\s*[\d,]+', resp.text, re.I)
print("Price mentions found:", len(prices), prices[:5])

