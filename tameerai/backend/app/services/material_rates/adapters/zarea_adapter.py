"""
TameerAI - Zarea B2B Marketplace Source Adapter (Stage 2B)

Ingests commercial B2B raw material quotations and commodity marketplace listings
from Zarea (zarea.pk), Pakistan's premier B2B construction materials digital exchange.
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


class ZareaMarketplaceSourceAdapter(BaseSourceAdapter):
    """
    Adapter for Zarea B2B raw materials platform.
    Captures live commodity marketplace listings with manufacturer brand, grade,
    minimum order quantities (MOQ), and wholesale/ex-mill price quotes.
    """

    def __init__(
        self,
        *,
        source_code: str = "ZAREA_B2B_MARKETPLACE",
        source_name: str = "Zarea Raw Materials B2B Marketplace",
        base_url: str = "https://zarea.com",
        http_client: Optional[SafeHttpClient] = None,
        default_city: str = "Lahore",
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.AGGREGATOR,
            source_category=SourceCategory.MARKETPLACE_LISTING,
            default_price_basis=PriceBasis.WHOLESALE,
            base_url=base_url,
            default_city=default_city,
        )
        self.http_client = http_client

    async def fetch_raw_data(self, endpoint_url: Optional[str] = None, **kwargs) -> Any:
        """Fetches catalog or commodity rates via SafeHttpClient or returns supplied payload."""
        if "payload" in kwargs:
            return kwargs["payload"]
        if "raw_payload" in kwargs:
            return kwargs["raw_payload"]

        target_url = endpoint_url or f"{self.base_url}/daily-price/cement"
        if not self.http_client:
            self.http_client = SafeHttpClient(allowed_domains=["zarea.com", "www.zarea.com", "zarea.pk", "www.zarea.pk"])

        resp = await self.http_client.get(target_url)
        return resp.text

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """
        Parses Zarea API JSON responses or HTML commodity catalog listings.
        Extracts:
        - commodity_name (e.g. "Bestway Ordinary Portland Cement", "Mughal Steel Grade 60")
        - price / wholesale_price
        - unit (e.g. "50 kg Bag", "Metric Ton", "Ton")
        - manufacturer_brand (e.g. "Bestway", "Mughal Steel", "Lucky Cement")
        - grade (e.g. "Grade 60", "Grade 40")
        - city / dispatch_location
        - moq (minimum order quantity)
        """
        if isinstance(raw_payload, str):
            trimmed = raw_payload.strip()
            if trimmed.startswith(("{", "[")):
                try:
                    parsed = json.loads(trimmed)
                    return self._parse_json_listings(parsed)
                except json.JSONDecodeError:
                    pass
            return self._parse_html_listings(trimmed)

        if isinstance(raw_payload, (list, dict)):
            return self._parse_json_listings(raw_payload)

        return []

    def _parse_json_listings(self, payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        listings = payload if isinstance(payload, list) else payload.get("data", payload.get("products", payload.get("listings", [])))

        for item in listings:
            if not isinstance(item, dict):
                continue

            name = item.get("title") or item.get("name") or item.get("product_name") or item.get("commodity")
            price = item.get("price") or item.get("unit_price") or item.get("rate")
            unit = item.get("unit") or item.get("uom") or "ton"
            city = item.get("city") or item.get("location") or item.get("dispatch_city") or self.default_city
            brand = item.get("brand") or item.get("manufacturer")
            grade = item.get("grade")
            moq = item.get("moq") or item.get("min_order_quantity")

            if not name or price is None:
                continue

            # Infer brand from title if missing
            if not brand:
                title_lower = name.lower()
                for known_brand in ["bestway", "lucky", "maple leaf", "fauji", "cherat", "mughal", "amreli", "agha", "ff steel"]:
                    if known_brand in title_lower:
                        brand = known_brand.title()
                        break

            # Infer grade if missing
            if not grade:
                if "grade 60" in name.lower() or "g-60" in name.lower():
                    grade = "Grade 60"
                elif "grade 40" in name.lower() or "g-40" in name.lower():
                    grade = "Grade 40"

            records.append(
                RawSourceRecord(
                    raw_material_name=str(name),
                    raw_price=price,
                    raw_unit=str(unit),
                    raw_city=str(city),
                    raw_published_date=item.get("updated_at") or datetime.now(timezone.utc).date().isoformat(),
                    brand=brand,
                    grade=grade,
                    specification=item.get("specification") or f"Zarea B2B Commercial Listing (MOQ: {moq or 'Standard'})",
                    price_basis=PriceBasis.WHOLESALE,
                    is_syndicated=False,
                    original_source_citation="Zarea.pk Commercial Marketplace",
                    raw_metadata={
                        "zarea_product_id": item.get("id"),
                        "moq": moq,
                        "payment_terms": item.get("payment_terms"),
                        "delivery_terms": item.get("delivery_terms", "Ex-Mill / Loaded on Truck"),
                    },
                    source_url=f"{self.base_url}/product/{item.get('slug', item.get('id', ''))}",
                )
            )
        return records

    def _parse_html_listings(self, html_str: str) -> List[RawSourceRecord]:
        """Simple HTML extractor for product listing cards."""
        records: List[RawSourceRecord] = []
        card_pattern = re.compile(r"<div[^>]*class=\"[^\"]*product-card[^\"]*\"[^>]*>(.*?)</div>\s*</div>", re.DOTALL | re.IGNORECASE)
        for match in card_pattern.finditer(html_str):
            snippet = match.group(1)
            title_match = re.search(r"<h[2-4][^>]*>(.*?)</h[2-4]>", snippet, re.IGNORECASE)
            price_match = re.search(r"PKR\s*([\d,]+(?:\.\d+)?)", snippet, re.IGNORECASE)
            if title_match and price_match:
                title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
                try:
                    price = float(price_match.group(1).replace(",", ""))
                    records.append(
                        RawSourceRecord(
                            raw_material_name=title,
                            raw_price=price,
                            raw_unit="ton" if "steel" in title.lower() else "bag",
                            raw_city=self.default_city,
                            raw_published_date=datetime.now(timezone.utc).date().isoformat(),
                            price_basis=PriceBasis.WHOLESALE,
                            original_source_citation="Zarea B2B Exchange",
                            raw_metadata={"card_scraped": True},
                            source_url=self.base_url,
                        )
                    )
                except ValueError:
                    continue
        return records
