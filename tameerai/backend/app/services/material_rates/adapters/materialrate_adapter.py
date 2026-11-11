"""
TameerAI - MaterialRate.pk Secondary Market Publisher Source Adapter (Stage 2B / 2B.1 Correction)

Ingests retail and wholesale market rate snapshots from MaterialRate.pk (https://materialrate.pk/),
tracking daily cement, steel, bricks, sand, crush, and blocks across major urban hubs.

Correction Requirements:
- Records are classified as indicative estimates (secondary publisher roundup).
- When no publication timestamp exists:
  - Keep raw_published_date = None (persisted as NULL published_at).
  - Record fetched_at independently in metadata.
  - Never invent or fabricate today's date for missing publication dates.
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


class MaterialRatePublisherSourceAdapter(BaseSourceAdapter):
    """
    Adapter for MaterialRate.pk secondary market rate publisher.
    Category: SECONDARY_MARKET_PUBLISHER.
    Price Basis: RETAIL (with depot pickup / open market context).
    Verification Status: Indicative estimate.
    """

    def __init__(
        self,
        *,
        source_code: str = "MATERIALRATE_PK_PUBLISHER",
        source_name: str = "MaterialRate.pk National Construction Intelligence",
        base_url: str = "https://materialrate.pk",
        http_client: Optional[SafeHttpClient] = None,
        default_city: str = "Lahore",
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.AGGREGATOR,
            source_category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
            default_price_basis=PriceBasis.RETAIL,
            base_url=base_url,
            default_city=default_city,
        )
        self.http_client = http_client

    async def fetch_raw_data(self, endpoint_url: Optional[str] = None, **kwargs) -> Any:
        """Fetches market price table via SafeHttpClient or returns supplied payload."""
        if "payload" in kwargs:
            return kwargs["payload"]
        if "raw_payload" in kwargs:
            return kwargs["raw_payload"]

        target_url = endpoint_url or self.base_url
        if not self.http_client:
            self.http_client = SafeHttpClient(allowed_domains=["materialrate.pk", "www.materialrate.pk"])

        resp = await self.http_client.get(target_url)
        return resp.text

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """Parses structured dictionary or HTML tabular content from MaterialRate.pk."""
        if isinstance(raw_payload, str):
            trimmed = raw_payload.strip()
            if trimmed.startswith(("{", "[")):
                try:
                    parsed = json.loads(trimmed)
                    return self._parse_structured_tables(parsed)
                except json.JSONDecodeError:
                    pass
            return self._parse_html_tables(trimmed)

        if isinstance(raw_payload, (list, dict)):
            return self._parse_structured_tables(raw_payload)

        return []

    def _extract_page_date(self, html_content: str) -> Optional[str]:
        """
        Extracts dateModified or datePublished from Schema.org JSON-LD or meta tags.
        Returns None if no official publication/modification timestamp is present.
        """
        # 1. Schema.org JSON-LD
        for script_match in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE):
            script_text = script_match.group(1)
            date_mod = re.search(r'"dateModified"\s*:\s*"([^"]+)"', script_text)
            if date_mod:
                return date_mod.group(1)
            date_pub = re.search(r'"datePublished"\s*:\s*"([^"]+)"', script_text)
            if date_pub:
                return date_pub.group(1)

        # 2. Meta tags
        meta_match = re.search(r'<meta[^>]*(?:property|name)=["\'](?:article:modified_time|og:updated_time|article:published_time)["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if meta_match:
            return meta_match.group(1)

        return None

    def _parse_structured_tables(self, payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        entries = payload if isinstance(payload, list) else payload.get("rates", payload.get("data", []))
        source_citation = payload.get("citation", "MaterialRate.pk Daily Market Survey") if isinstance(payload, dict) else "MaterialRate.pk Daily Market Survey"
        is_syndicated = bool(payload.get("is_syndicated", False)) if isinstance(payload, dict) else False
        republished_from = payload.get("republished_from") if isinstance(payload, dict) else None
        fetched_at = datetime.now(timezone.utc).isoformat()

        for item in entries:
            if not isinstance(item, dict):
                continue

            name = item.get("material") or item.get("name") or item.get("item")
            rate = item.get("price") or item.get("rate") or item.get("today_price")
            unit = item.get("unit") or item.get("uom")
            city = item.get("city") or self.default_city
            brand = item.get("brand")
            grade = item.get("grade")
            spec = item.get("specification")

            if not name or rate is None or not unit:
                continue

            # Detect brand if missing
            if not brand:
                lower_name = name.lower()
                for b in ["bestway", "lucky", "maple leaf", "fauji", "dg khan", "cherat", "mughal", "amreli", "agha", "ff steel"]:
                    if b in lower_name:
                        brand = b.title()
                        break

            # Detect grade if missing
            if not grade:
                if "grade 60" in name.lower() or "g60" in name.lower():
                    grade = "Grade 60"
                elif "grade 40" in name.lower() or "g40" in name.lower():
                    grade = "Grade 40"

            records.append(
                RawSourceRecord(
                    raw_material_name=str(name),
                    raw_price=rate,
                    raw_unit=str(unit),
                    raw_city=str(city),
                    raw_published_date=item.get("date"),  # None if undated (no inventing dates)
                    brand=brand,
                    grade=grade,
                    specification=spec or f"Open Market Indicative Estimate ({city})",
                    price_basis=PriceBasis.RETAIL,
                    is_syndicated=is_syndicated,
                    original_source_citation=source_citation,
                    republished_from=republished_from,
                    raw_metadata={
                        "publisher": "MaterialRate.pk",
                        "survey_type": item.get("survey_type", "daily_retail_roundup"),
                        "raw_city_input": city,
                        "fetched_at": fetched_at,
                        "estimate_classification": "indicative",
                    },
                    source_url=item.get("url") or self.base_url,
                )
            )
        return records

    def _parse_html_tables(self, html_content: str) -> List[RawSourceRecord]:
        """Parses HTML tables rendered on MaterialRate pages with multi-column, range, and brand support."""
        records: List[RawSourceRecord] = []
        fetched_at = datetime.now(timezone.utc).isoformat()
        pub_date = self._extract_page_date(html_content)

        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
        cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)

        current_header = []
        for row_match in row_pattern.finditer(html_content):
            row_html = row_match.group(1)
            raw_cells = [re.sub(r"<[^>]+>", " ", c).strip() for c in cell_pattern.findall(row_html)]
            cells = [" ".join(c.split()) for c in raw_cells if c]

            if len(cells) < 2:
                continue

            # Check if this row is a header
            first_cell_lower = cells[0].lower()
            if any(h in first_cell_lower for h in ["brand", "material", "brick type", "city", "size & unit", "sand type"]):
                current_header = [c.lower() for c in cells]
                continue

            # Table Type A: Cement Table [Brand, Price (PKR / 50kg), Origin/Plant Location]
            if len(cells) >= 3 and any("50kg" in h or "pkr" in h for h in current_header[:3]):
                brand_or_mat = cells[0]
                price_str = cells[1]
                origin_city = cells[2]
                price_val = self._extract_price(price_str)
                if price_val:
                    records.append(
                        RawSourceRecord(
                            raw_material_name=f"Ordinary Portland Cement {brand_or_mat}",
                            raw_price=price_val,
                            raw_unit="bag_50kg",
                            raw_city=origin_city or self.default_city,
                            raw_published_date=pub_date,
                            brand=brand_or_mat,
                            grade="OPC",
                            price_basis=PriceBasis.RETAIL,
                            original_source_citation="MaterialRate.pk Cement Price Table",
                            raw_metadata={
                                "raw_price": price_str,
                                "origin": origin_city,
                                "fetched_at": fetched_at,
                                "estimate_classification": "indicative",
                            },
                            source_url=self.base_url,
                        )
                    )
                continue

            # Table Type B: Steel Table [Brand Name, Sotar, 40 Grade Rate, 40 Grade Ton, 60 Grade Rate]
            if len(cells) >= 5 and "brand" in first_cell_lower:
                continue
            if len(cells) >= 5 and ("grade" in " ".join(current_header) or len(cells) == 5):
                brand = cells[0]
                sotar = cells[1]
                rate_g40 = self._extract_price(cells[2])
                rate_g60 = self._extract_price(cells[4]) if len(cells) > 4 else None

                if rate_g60:
                    records.append(
                        RawSourceRecord(
                            raw_material_name=f"Deformed Steel Bar {brand} Grade 60",
                            raw_price=rate_g60,
                            raw_unit="kg",
                            raw_city=self.default_city,
                            raw_published_date=pub_date,
                            brand=brand,
                            grade="Grade 60",
                            specification=f"ASTM A615 Grade 60 ({sotar} Sotar)",
                            price_basis=PriceBasis.RETAIL,
                            original_source_citation="MaterialRate.pk Steel Table",
                            raw_metadata={
                                "sotar": sotar,
                                "mill": brand,
                                "fetched_at": fetched_at,
                                "estimate_classification": "indicative",
                            },
                            source_url=self.base_url,
                        )
                    )
                if rate_g40:
                    records.append(
                        RawSourceRecord(
                            raw_material_name=f"Deformed Steel Bar {brand} Grade 40",
                            raw_price=rate_g40,
                            raw_unit="kg",
                            raw_city=self.default_city,
                            raw_published_date=pub_date,
                            brand=brand,
                            grade="Grade 40",
                            specification=f"Grade 40 ({sotar} Sotar)",
                            price_basis=PriceBasis.RETAIL,
                            original_source_citation="MaterialRate.pk Steel Table",
                            raw_metadata={
                                "sotar": sotar,
                                "mill": brand,
                                "fetched_at": fetched_at,
                                "estimate_classification": "indicative",
                            },
                            source_url=self.base_url,
                        )
                    )
                continue

            # Table Type C: General / Bricks / Sand / Bajri [Name, Price, ...]
            name = cells[0]
            price_val = None
            price_str = None
            unit = "cft"

            for c in cells[1:]:
                p = self._extract_price(c)
                if p:
                    price_val = p
                    price_str = c
                    break

            if price_val is not None:
                lower_combined = f"{name} {price_str} {' '.join(cells)}".lower()
                if "/ bag" in lower_combined or "bag" in lower_combined:
                    unit = "bag_50kg"
                elif "/ kg" in lower_combined or "per kg" in lower_combined:
                    unit = "kg"
                elif "ton" in lower_combined:
                    unit = "metric_ton"
                elif "/ brick" in lower_combined or "brick" in lower_combined:
                    unit = "piece"
                elif "1000" in lower_combined or "1,000" in lower_combined or "hazar" in lower_combined:
                    unit = "1000_bricks"
                elif "100 cft" in lower_combined or "hundred" in lower_combined:
                    unit = "100_cft"
                elif "cft" in lower_combined:
                    unit = "cft"

                records.append(
                    RawSourceRecord(
                        raw_material_name=name,
                        raw_price=price_val,
                        raw_unit=unit,
                        raw_city=self.default_city,
                        raw_published_date=pub_date,
                        price_basis=PriceBasis.RETAIL,
                        original_source_citation="MaterialRate.pk HTML Table",
                        raw_metadata={
                            "raw_cells": cells,
                            "fetched_at": fetched_at,
                            "estimate_classification": "indicative",
                        },
                        source_url=self.base_url,
                    )
                )

        return records

    def _extract_price(self, text: str) -> Optional[float]:
        """Extracts clean price; handles ranges like 1,540 – 1,555 by returning midpoint."""
        clean = text.replace("Rs.", "").replace("RS.", "").replace("Rs", "").replace("PKR", "").replace("₨", "").replace(",", "")
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*[–\-—]\s*(\d+(?:\.\d+)?)", clean)
        if range_match:
            try:
                p1 = float(range_match.group(1))
                p2 = float(range_match.group(2))
                return round((p1 + p2) / 2.0, 2)
            except ValueError:
                pass

        match = re.search(r"(\d+(?:\.\d+)?)", clean)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None
