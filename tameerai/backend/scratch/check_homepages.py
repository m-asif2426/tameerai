import httpx
import asyncio

async def test():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
        for url in ["https://materialrate.pk", "https://gharhub.com"]:
            try:
                r = await client.get(url)
                print(f"{url} -> HTTP {r.status_code} | {len(r.content)} bytes | tables: {'<table' in r.text.lower()}")
            except Exception as e:
                print(f"{url} -> Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())

