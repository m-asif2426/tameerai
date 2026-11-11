"""
TameerAI - Direct Dealer Quotation Ingestion Connector (Stage 2B)

Ingests verified direct quotations submitted by registered construction material
dealers, suppliers, and regional distributors across Pakistan.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.services.material_rates.base_adapter import BaseSourceAdapter
from app.services.material_rates.contracts import (
    CollectionSourceType,
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
)

logger = logging.getLogger(__name__)


class DirectDealerConnector(BaseSourceAdapter):
    """
    Direct ingestion connector for registered construction material dealer submissions.
    Price Basis: DEALER_QUOTATION.
    Category: VERIFIED_DEALER_QUOTATION.
    """

    def __init__(
        self,
        *,
        source_code: str = "DIRECT_DEALER_QUOTATION",
        source_name: str = "Verified Direct Dealer Quotation Network",
        base_url: Optional[str] = None,
        default_city: str = "Lahore",
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.DEALER_NETWORK,
            source_category=SourceCategory.VERIFIED_DEALER_QUOTATION,
            default_price_basis=PriceBasis.DEALER_QUOTATION,
            base_url=base_url or "https://tameerai.com/dealer-portal",
            default_city=default_city,
        )

    async def fetch_raw_data(self, quotation_payload: Optional[Any] = None, **kwargs) -> Any:
        """
        Direct dealer connector receives in-memory or API payload directly.
        Does not issue remote HTTP requests unless syncing with external dealer ERP.
        """
        if quotation_payload is not None:
            return quotation_payload
        if "payload" in kwargs:
            return kwargs["payload"]
        raise ValueError("DirectDealerConnector requires quotation_payload to ingest")

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """
        Parses structured dealer quotation payload.
        Expected schema:
        {
            "dealer_id": "...",
            "dealer_quote_id": "...",
            "dealer_business_name": "Al-Rehman Steel & Cement Traders",
            "city": "Lahore",
            "quotation_date": "2026-11-06",
            "valid_until": "2026-11-13",
            "items": [
                {
                    "material_name": "Bestway Ordinary Portland Cement",
                    "price": 1560.00,
                    "unit": "50 kg Bag",
                    "brand": "Bestway",
                    "grade": "OPC",
                    "terms": "Ex-godown"
                }
            ]
        }
        """
        if isinstance(raw_payload, str):
            try:
                raw_payload = json.loads(raw_payload)
            except json.JSONDecodeError as err:
                logger.error("Failed to parse dealer JSON payload: %s", err)
                return []

        if not isinstance(raw_payload, dict):
            return []

        dealer_id_raw = raw_payload.get("dealer_id")
        dealer_quote_id_raw = raw_payload.get("dealer_quote_id")
        dealer_name = raw_payload.get("dealer_business_name", "Registered Construction Material Dealer")
        city = raw_payload.get("city", self.default_city)
        quote_date = raw_payload.get("quotation_date", datetime.now(timezone.utc).date().isoformat())
        valid_until = raw_payload.get("valid_until")

        dealer_id = uuid.UUID(str(dealer_id_raw)) if dealer_id_raw else None
        dealer_quote_id = uuid.UUID(str(dealer_quote_id_raw)) if dealer_quote_id_raw else None

        records: List[RawSourceRecord] = []
        items = raw_payload.get("items", [])

        for it in items:
            if not isinstance(it, dict):
                continue

            mat_name = it.get("material_name") or it.get("item")
            price = it.get("price") or it.get("quoted_price") or it.get("rate")
            unit = it.get("unit") or it.get("measurement_unit")

            if not mat_name or price is None or not unit:
                continue

            records.append(
                RawSourceRecord(
                    raw_material_name=str(mat_name),
                    raw_price=price,
                    raw_unit=str(unit),
                    raw_city=city,
                    raw_published_date=quote_date,
                    brand=it.get("brand"),
                    grade=it.get("grade"),
                    specification=it.get("specification", f"Direct Dealer Quote from {dealer_name}"),
                    price_basis=PriceBasis.DEALER_QUOTATION,
                    dealer_id=dealer_id,
                    dealer_quote_id=dealer_quote_id,
                    is_syndicated=False,
                    original_source_citation=f"Dealer Quotation: {dealer_name}",
                    raw_metadata={
                        "dealer_business_name": dealer_name,
                        "valid_until": valid_until,
                        "payment_terms": it.get("payment_terms", raw_payload.get("payment_terms")),
                        "delivery_terms": it.get("delivery_terms", raw_payload.get("delivery_terms", "Ex-depot")),
                        "invoice_reference": raw_payload.get("invoice_reference"),
                    },
                    source_url=f"tameerai://dealers/{dealer_id or 'direct'}/quotes/{dealer_quote_id or 'new'}",
                )
            )

        return records

