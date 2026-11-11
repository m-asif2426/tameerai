import asyncio
import asyncpg
import httpx

async def inspect_snapshots():
    client = httpx.Client(base_url="http://127.0.0.1:8000/api/v1")
    
    # 1. Snapshots by city
    cities = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Multan", "Quetta", "Faisalabad"]
    total_snaps = 0
    all_snapshots = []
    
    for c in cities:
        r = client.get(f"/material-rates/snapshots?city={c}")
        if r.status_code == 200:
            snaps = r.json()
            print(f"City '{c}': {len(snaps)} snapshots returned")
            for s in snaps:
                total_snaps += 1
                all_snapshots.append(s)
                print(f"   [{s['city']}] {s['product_code']} ({s['product_name']}): PKR {s['rate_pkr']} / {s['unit']} (obs: {s['observation_count']}, confidence: {s['confidence_score']}%)")

    print(f"\nTotal computed snapshots across cities: {total_snaps}")
    
    # Check the 14 snapshots: Lahore (6) + Karachi (?) + Islamabad (?)
    lahore_snaps = [s for s in all_snapshots if s['city'] == 'Lahore']
    karachi_snaps = [s for s in all_snapshots if s['city'] == 'Karachi']
    isb_snaps = [s for s in all_snapshots if s['city'] == 'Islamabad']
    print(f"\nLahore (6) + Karachi ({len(karachi_snaps)}) + Islamabad ({len(isb_snaps)}) = {len(lahore_snaps) + len(karachi_snaps) + len(isb_snaps)}")

    client.close()

if __name__ == '__main__':
    asyncio.run(inspect_snapshots())

