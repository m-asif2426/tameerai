"""
TameerAI - Fixture Source Adapter for Local Deterministic Testing (Stage 2A)

Provides a mock/fixture adapter for local testing and CI/CD without making external HTTP requests.
Simulates:
- Valid cement quotations across Lahore, Karachi, and Islamabad.
- Steel rebar rates across different measurement units (ton, kg).
- Missing prices and malformed data records.
- Source timeouts and simulated network failures.
"""

from typing import Any, Dict, List, Optional

from app.services.material_rates.base_adapter import BaseSourceAdapter
from app.services.material_rates.contracts import CollectionSourceType, RawSourceRecord
from app.services.material_rates.http_client import CollectionFetchError


class FixtureSourceAdapter(BaseSourceAdapter):
    """
    Test fixture adapter returning controlled test payloads.
    Guaranteed zero external network dependencies.
    """

    def __init__(
        self,
        *,
        source_code: str = "FIXTURE_SRC_01",
        source_name: str = "Deterministic Test Fixture Source",
        fixture_payload: Optional[List[Dict[str, Any]]] = None,
        simulate_timeout: bool = False,
        simulate_failure: bool = False,
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.OFFICIAL,
            base_url="https://mock-market-rates.tameerai.pk/api/rates",
            default_city="Lahore",
        )
        self.fixture_payload = fixture_payload
        self.simulate_timeout = simulate_timeout
        self.simulate_failure = simulate_failure

    async def fetch_raw_data(self, **kwargs) -> Any:
        if self.simulate_timeout:
            raise CollectionFetchError("Simulated socket timeout connecting to fixture endpoint")
        if self.simulate_failure:
            raise CollectionFetchError("Simulated upstream HTTP 503 Service Unavailable")

        if self.fixture_payload is not None:
            return self.fixture_payload

        # Default rich multi-material test payload
        return [
            {
                "material": "Lucky Cement OPC 50kg",
                "price": "1,520.00",
                "unit": "bori",
                "city": "Lahore",
                "date": "2026-11-06",
                "metadata": {"brand": "Lucky", "grade": "OPC"},
            },
            {
                "material": "Falcon Cement OPC 50kg",
                "price": "1,480.00",
                "unit": "50kg bag",
                "city": "Karachi",
                "date": "2026-11-06",
                "metadata": {"brand": "Falcon", "grade": "OPC"},
            },
            {
                "material": "Mughal Supreme Deformed Steel G60 12mm",
                "price": "265000",
                "unit": "metric ton",
                "city": "Islamabad",
                "date": "2026-11-06",
                "metadata": {"grade": "60", "standard": "ASTM A615"},
            },
            {
                "material": "Awwal Clay Bricks",
                "price": "14500",
                "unit": "1000 bricks",
                "city": "Multan",
                "date": "2026-11-06",
                "metadata": {"quality": "Awwal"},
            },
            # Invalid/corrupted records to verify rejection handling
            {
                "material": "Unknown Broken Material",
                "price": None,  # Missing price
                "unit": "bag",
                "city": "Lahore",
                "date": "2026-11-06",
            },
            {
                "material": "Lucky Cement OPC 50kg",
                "price": "1520.00",
                "unit": "bag",
                "city": "Lahore",
                "date": "invalid-date-string-32-13",  # Malformed date
            },
            {
                "material": "Corrupt Negative Steel",
                "price": "-500.00",  # Negative price
                "unit": "ton",
                "city": "Lahore",
                "date": "2026-11-06",
            },
        ]

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        for item in raw_payload:
            records.append(
                RawSourceRecord(
                    raw_material_name=item.get("material", ""),
                    raw_price=item.get("price"),
                    raw_unit=item.get("unit", ""),
                    raw_city=item.get("city"),
                    raw_published_date=item.get("date"),
                    raw_metadata=item.get("metadata", {}),
                    source_url=self.base_url,
                )
            )
        return records

