"""
Audits additional Pakistani steel and construction material candidates:
AtaPata Pulse, Royal Steel, Kamran Steel, Ittehad Steel, Pakistan Steel Mills.
"""
import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (TameerAI/2.0 Research Bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

ADDITIONAL_CANDIDATES = [
    ("AtaPata Pulse", "https://atapata.com/", "SECONDARY_MARKET_PUBLISHER"),
    ("AtaPata Saria Rate", "https://atapata.com/saria-rate-in-pakistan-today/", "SECONDARY_MARKET_PUBLISHER"),
    ("Royal Steel", "https://royalsteel.com.pk/", "MANUFACTURER_EX_FACTORY"),
    ("Royal Rebar", "https://royalrebar.com/", "MANUFACTURER_EX_FACTORY"),
    ("Kamran Steel", "https://kamransteel.com/", "MANUFACTURER_EX_FACTORY"),
    ("Ittehad Steel", "https://ittehadsteel.com/", "MANUFACTURER_EX_FACTORY"),
    ("Pakistan Steel Mills", "https://paksteel.gov.pk/", "MANUFACTURER_EX_FACTORY"),
]

async def check(client, name, url, cat):
    info = {
        "name": name,
        "url": url,
        "category": cat,
        "status": None,
        "length": 0,
        "tables": 0,
        "has_date": False,
        "date_info": None,
        "error": None,
        "snippet": "",
    }
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True)
        info["status"] = r.status_code
        info["length"] = len(r.content)
        if r.status_code == 200:
            text = r.text
            info["tables"] = text.lower().count("<table")
            d_match = re.search(r'"date(?:Modified|Published)"\s*:\s*"([^"]+)"', text)
            if not d_match:
                d_match = re.search(r'<meta[^>]*(?:property|name)=["\'](?:article:modified_time|og:updated_time|article:published_time)["\'][^>]*content=["\']([^"\']+)["\']', text)
            if d_match:
                info["has_date"] = True
                info["date_info"] = d_match.group(1)
            clean = re.sub(r'<[^>]+>', ' ', text[:1500])
            info["snippet"] = ' '.join(clean.split())[:150]
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {str(e)[:80]}"
    return info

async def main():
    print(f"=== Auditing {len(ADDITIONAL_CANDIDATES)} Additional Candidates ===")
    results = []
    async with httpx.AsyncClient(headers=HEADERS, verify=False) as client:
        for name, url, cat in ADDITIONAL_CANDIDATES:
            r = await check(client, name, url, cat)
            results.append(r)
            s_str = f"HTTP {r['status']}" if r['status'] else f"Error: {r['error']}"
            print(f"[{r['name']}] -> {s_str} | {r['length']} bytes | {r['tables']} tables | Date: {r['date_info']}")

    out = Path("scratch/additional_sources_audit.json")
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    asyncio.run(main())

