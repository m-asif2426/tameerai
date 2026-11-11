"""
TameerAI - Real-World Pakistani Construction Material Public Source Discovery & Extraction Audit.
Executes public read-only HTTP GET requests to inspect actual status, headers, and content.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import ssl
import sys
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (TameerAI/2.0 Research Bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CANDIDATES = [
    # 1. Official Statistical
    ("PBS SPI", "https://www.pbs.gov.pk/price-statistics/", "OFFICIAL_STATISTICAL"),
    ("PBS SPI Bulletin", "https://www.pbs.gov.pk/price-statistics/weekly-spi", "OFFICIAL_STATISTICAL"),
    
    # 2. Government Schedules
    ("NHA CSR", "https://nha.gov.pk/csr", "GOVERNMENT_SCHEDULE"),
    ("Punjab C&W MRS", "https://finance.punjab.gov.pk", "GOVERNMENT_SCHEDULE"),
    ("KP C&W CSR", "https://cwd.kp.gov.pk/page/composite_schedule_of_rates", "GOVERNMENT_SCHEDULE"),
    ("Sindh Works CSR", "https://works.sindh.gov.pk", "GOVERNMENT_SCHEDULE"),

    # 3. Primary Manufacturers
    ("Lucky Cement", "https://lucky-cement.com/en", "MANUFACTURER_EX_FACTORY"),
    ("Bestway Cement", "https://www.bestway.com.pk/products/", "MANUFACTURER_EX_FACTORY"),
    ("DG Khan Cement", "https://dgcement.com", "MANUFACTURER_EX_FACTORY"),
    ("Mughal Steel", "https://mughalsteel.com.pk/", "MANUFACTURER_EX_FACTORY"),
    ("Amreli Steels", "https://amrelisteels.com", "MANUFACTURER_EX_FACTORY"),
    ("Agha Steel", "https://aghasteel.com", "MANUFACTURER_EX_FACTORY"),
    ("FF Steel", "https://ff.com.pk", "MANUFACTURER_EX_FACTORY"),

    # 4. B2B Marketplaces
    ("Zarea Cement", "https://zarea.com/daily-price/cement", "MARKETPLACE_LISTING"),
    ("Zarea PK", "https://zarea.pk", "MARKETPLACE_LISTING"),

    # 5. Construction Material Publishers
    ("SteelRateToday Home", "https://steelratetoday.pk/", "SECONDARY_MARKET_PUBLISHER"),
    ("MaterialRate.pk Cement", "https://materialrate.pk/cement-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("MaterialRate.pk Saria", "https://materialrate.pk/saria-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("MaterialRate.pk Bricks", "https://materialrate.pk/bricks-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("MaterialRate.pk Sand", "https://materialrate.pk/sand-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("MaterialRate.pk Bajri", "https://materialrate.pk/bajri-crush-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("GharHub Bricks", "https://gharhub.com/bricks-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("GharHub Sand", "https://gharhub.com/sand-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("GharHub Crush", "https://gharhub.com/crush-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("GharHub Cement", "https://gharhub.com/cement-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
    ("GharHub Steel", "https://gharhub.com/steel-rate-in-pakistan/", "SECONDARY_MARKET_PUBLISHER"),
]

async def check_url(client: httpx.AsyncClient, name: str, url: str, cat: str) -> dict:
    start_t = datetime.now(timezone.utc)
    res = {
        "name": name,
        "url": url,
        "category": cat,
        "http_status": None,
        "accessible": False,
        "content_length": 0,
        "has_tables": False,
        "table_count": 0,
        "has_date": False,
        "date_info": None,
        "error": None,
        "html_preview": "",
    }
    try:
        resp = await client.get(url, timeout=12.0, follow_redirects=True)
        res["http_status"] = resp.status_code
        res["content_length"] = len(resp.content)
        if resp.status_code == 200:
            res["accessible"] = True
            text = resp.text
            res["has_tables"] = "<table" in text.lower()
            res["table_count"] = text.lower().count("<table")
            
            # Check for dates
            date_match = re.search(r'"date(?:Modified|Published)"\s*:\s*"([^"]+)"', text)
            if not date_match:
                date_match = re.search(r'<meta[^>]*(?:property|name)=["\'](?:article:modified_time|og:updated_time|article:published_time)["\'][^>]*content=["\']([^"\']+)["\']', text)
            if date_match:
                res["has_date"] = True
                res["date_info"] = date_match.group(1)
            
            # Save a snippet
            clean_snippet = re.sub(r'<[^>]+>', ' ', text[:1500])
            res["html_preview"] = ' '.join(clean_snippet.split())[:150]
        else:
            res["error"] = f"HTTP {resp.status_code}"
    except httpx.ConnectTimeout:
        res["error"] = "Connect Timeout"
    except httpx.ReadTimeout:
        res["error"] = "Read Timeout"
    except httpx.ConnectError as e:
        res["error"] = f"Connect Error: {str(e)[:80]}"
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {str(e)[:80]}"
    return res

async def main():
    print(f"=== Auditing {len(CANDIDATES)} Real-World Construction Data Sources ===")
    results = []
    
    # Custom client with generous limits and standard verification
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits, verify=False) as client:
        tasks = [check_url(client, name, url, cat) for name, url, cat in CANDIDATES]
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            status_str = f"HTTP {r['http_status']}" if r['http_status'] else r['error']
            tables_str = f"{r['table_count']} tables" if r['has_tables'] else "No tables"
            date_str = f"Date: {r['date_info']}" if r['has_date'] else "No date"
            print(f"[{r['name']}] -> {status_str} | {r['content_length']} bytes | {tables_str} | {date_str}")

    # Output detailed JSON
    out_file = Path("D:/new idea project/tameerai/backend/scratch/live_sources_audit_results.json")
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved results to {out_file}")

if __name__ == "__main__":
    asyncio.run(main())

