"""
Inspect the live snapshots returned by canonical_engine and api endpoint.
"""
import asyncio
import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def check_snapshots():
    for city in ["Lahore", "Karachi", "Islamabad"]:
        url = f"{BASE_URL}/material-rates/snapshots?city={city}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"\n=======================================================")
                print(f"SNAPSHOTS FOR {city.upper()} (Total items: {len(data)})")
                print(f"=======================================================")
                for snap in data:
                    print(f"Product: {snap['product_code']} ({snap['product_name']})")
                    print(f"  Rate: PKR {snap.get('rate_pkr')} | Prev: {snap.get('prev_rate_pkr')} | Trend: {snap.get('trend')}")
                    print(f"  Observations: {snap.get('observation_count')} (Eligible: {snap.get('eligible_observation_count')})")
                    print(f"  Confidence: {snap.get('confidence_score')} | Verification: {snap.get('verification_status')}")
                    print(f"  Price Basis: {snap.get('price_basis')} | Range: {snap.get('price_range')}")
        except Exception as e:
            print(f"Error for {city}: {e}")

if __name__ == "__main__":
    check_snapshots()

