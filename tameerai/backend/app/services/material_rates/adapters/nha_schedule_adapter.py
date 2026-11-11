"""
TameerAI - National Highway Authority (NHA) & Provincial C&W Schedule Adapter (Stage 2B)

Ingests statutory government benchmark rates from the National Highway Authority (NHA)
Composite Schedule of Rates (CSR) and Provincial Communications & Works (C&W) Market
Rate Systems (MRS) across Pakistani districts.
"""

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.services.material_rates.base_adapter import BaseSourceAdapter
from app.services.material_rates.contracts import (
    CollectionSourceType,
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
)
from app.services.material_rates.http_client import SafeHttpClient

logger = logging.getLogger(__name__)


class NhaScheduleSourceAdapter(BaseSourceAdapter):
    """
    Adapter for statutory government construction schedules (NHA CSR, Punjab MRS, Sindh CSR).
    Price Basis: GOVERNMENT_SCHEDULE_RATE.
    Category: GOVERNMENT_SCHEDULE.
    """

    def __init__(
        self,
        *,
        source_code: str = "NHA_CSR_SCHEDULE",
        source_name: str = "National Highway Authority - Composite Schedule of Rates",
        base_url: str = "https://nha.gov.pk",
        http_client: Optional[SafeHttpClient] = None,
        default_district: str = "Rawalpindi",
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.OFFICIAL,
            source_category=SourceCategory.GOVERNMENT_SCHEDULE,
            default_price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
            base_url=base_url,
            default_city=default_district,
        )
        self.http_client = http_client
        self.default_district = default_district

    async def fetch_raw_data(self, endpoint_url: Optional[str] = None, **kwargs) -> Any:
        """Fetches CSR document data or schedule tables via SafeHttpClient or returns supplied payload."""
        if "payload" in kwargs:
            return kwargs["payload"]
        if "raw_payload" in kwargs:
            return kwargs["raw_payload"]

        target_url = endpoint_url or f"{self.base_url}/schedule-of-rates"
        if not self.http_client:
            self.http_client = SafeHttpClient(allowed_domains=["nha.gov.pk", "www.nha.gov.pk"])

        resp = await self.http_client.get(target_url)
        return resp.text

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """
        Parses structured NHA CSR schedule records (JSON or tabular text/HTML).
        Expected schedule fields:
        - item_code (e.g. 101-A, 102-B)
        - description (e.g. "Deformed Steel Bar Grade 60 (ASTM A615)")
        - unit (e.g. "Metric Ton", "100 Cft", "50 Kg Bag", "1000 Nos")
        - rate (e.g. 265000.00)
        - district / city (e.g. "Lahore", "Rawalpindi", "Karachi", "Peshawar")
        - schedule_edition (e.g. "CSR 2024-2025")
        """
        if isinstance(raw_payload, str):
            trimmed = raw_payload.strip()
            if trimmed.startswith(("{", "[")):
                try:
                    parsed = json.loads(trimmed)
                    return self._parse_structured_items(parsed)
                except json.JSONDecodeError:
                    pass
            return self._parse_text_table(trimmed)

        if isinstance(raw_payload, (list, dict)):
            return self._parse_structured_items(raw_payload)

        return []

    def _parse_structured_items(self, payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        items = payload if isinstance(payload, list) else payload.get("rates", payload.get("items", []))
        schedule_edition = payload.get("edition", "CSR 2024-2025") if isinstance(payload, dict) else "CSR 2024-2025"
        effective_date = payload.get("effective_date", datetime.now(timezone.utc).date().isoformat()) if isinstance(payload, dict) else datetime.now(timezone.utc).date().isoformat()

        for item in items:
            if not isinstance(item, dict):
                continue

            desc = item.get("description") or item.get("material_name") or item.get("item_name")
            rate = item.get("rate") or item.get("price") or item.get("composite_rate")
            unit = item.get("unit") or item.get("measurement_unit")
            district = item.get("district") or item.get("city") or self.default_district

            if not desc or rate is None or not unit:
                continue

            # Detect grade, brand, and specification hints
            grade = item.get("grade")
            if not grade and "grade 60" in desc.lower():
                grade = "Grade 60"
            elif not grade and "grade 40" in desc.lower():
                grade = "Grade 40"

            spec = item.get("specification") or item.get("standard") or f"NHA {schedule_edition} Statutory Standard"

            records.append(
                RawSourceRecord(
                    raw_material_name=str(desc),
                    raw_price=rate,
                    raw_unit=str(unit),
                    raw_city=str(district),
                    raw_published_date=effective_date,
                    brand=item.get("brand"),
                    grade=grade,
                    specification=spec,
                    price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
                    is_syndicated=False,
                    original_source_citation=f"National Highway Authority {schedule_edition}",
                    raw_metadata={
                        "csr_item_code": item.get("item_code"),
                        "district": district,
                        "schedule_edition": schedule_edition,
                        "authority": "National Highway Authority (NHA)",
                    },
                    source_url=f"{self.base_url}/csr",
                )
            )
        return records

    def _parse_text_table(self, text_payload: str) -> List[RawSourceRecord]:
        """Parses pipe-delimited or tab-delimited CSR rate lines."""
        records: List[RawSourceRecord] = []
        for line in text_payload.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in re.split(r"[,|\t]", line) if p.strip()]
            if len(parts) >= 4:
                # Format: [Code/Item, Unit, Rate, District]
                try:
                    item_name = parts[0]
                    unit = parts[1]
                    rate = float(parts[2].replace(",", ""))
                    district = parts[3]
                    records.append(
                        RawSourceRecord(
                            raw_material_name=item_name,
                            raw_price=rate,
                            raw_unit=unit,
                            raw_city=district,
                            raw_published_date=datetime.now(timezone.utc).date().isoformat(),
                            price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
                            specification="NHA Composite Schedule of Rates",
                            original_source_citation="NHA CSR Schedule",
                            raw_metadata={"raw_line": line},
                            source_url=f"{self.base_url}/csr",
                        )
                    )
                except ValueError:
                    continue
        return records
