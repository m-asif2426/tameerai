"""
TameerAI - GharHub Secondary Market Publisher Source Adapter (Stage 2B / 2B.1 Correction)

Ingests retail market prices for construction materials from GharHub (https://gharhub.com/),
covering Cement (OPC brands), Steel Rebar, Bricks, Sand, and Crush.

Enforces strict block precedence:
- Prioritizes prominently labelled "Live Rates Today" / "Live Cement Rates Today" table.
- Ignores older static article/SEO tables when a newer live listing table exists.
- Captures:
  - Source publication / update timestamp
  - System extraction timestamp
  - Product listing price
  - Material brand and unit
  - Original raw HTML snippet evidence
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


class GharHubPublisherSourceAdapter(BaseSourceAdapter):
    """
    Adapter for GharHub construction cost monitor.
    Category: SECONDARY_MARKET_PUBLISHER.
    Price Basis: RETAIL (Depot / Site Delivery Quotes).
    Verification Status: Indicative estimate.
    """

    def __init__(
        self,
        *,
        source_code: str = "GHARHUB_PK_PUBLISHER",
        source_name: str = "GharHub Construction Cost Guide",
        base_url: str = "https://gharhub.com",
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
        """Fetches market pricing tables or returns supplied in-memory payload."""
        if "payload" in kwargs:
            return kwargs["payload"]
        if "raw_payload" in kwargs:
            return kwargs["raw_payload"]

        target_url = endpoint_url or f"{self.base_url}/shop/cement-rate-in-pakistan-today/"
        if not self.http_client:
            self.http_client = SafeHttpClient(allowed_domains=["gharhub.com", "www.gharhub.com"])

        resp = await self.http_client.get(target_url)
        return resp.text

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """Parses GharHub structured dictionaries or live HTML price tables."""
        if isinstance(raw_payload, str):
            trimmed = raw_payload.strip()
            if trimmed.startswith(("{", "[")):
                try:
                    parsed = json.loads(trimmed)
                    return self._parse_structured_records(parsed)
                except json.JSONDecodeError:
                    pass
            return self._parse_html_tables(trimmed)

        if isinstance(raw_payload, (list, dict)):
            return self._parse_structured_records(raw_payload)

        return []

    def _extract_page_date(self, html_content: str) -> Optional[str]:
        """Extracts dateModified or datePublished or visible update date."""
        # 1. Schema.org JSON-LD
        for s in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE):
            mod = re.search(r'"dateModified"\s*:\s*"([^"]+)"', s)
            if mod:
                return mod.group(1)
            pub = re.search(r'"datePublished"\s*:\s*"([^"]+)"', s)
            if pub:
                return pub.group(1)

        # 2. Meta tags
        meta = re.search(r'<meta[^>]*(?:modified_time|published_time)[^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if meta:
            return meta.group(1)

        # 3. Visible text
        vis = re.search(r'(?:Updated|Modified|Published)\s*:?\s*(\d{4}-\d{2}-\d{2})', html_content, re.IGNORECASE)
        if vis:
            return vis.group(1)

        return None

    def _parse_structured_records(self, payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        items = payload if isinstance(payload, list) else payload.get("rates", payload.get("items", []))
        for it in items:
            if not isinstance(it, dict):
                continue
            name = it.get("material") or it.get("product") or it.get("name")
            price = it.get("price") or it.get("rate")
            unit = it.get("unit") or "cft"
            if not name or price is None:
                continue
            records.append(
                RawSourceRecord(
                    raw_material_name=str(name),
                    raw_price=price,
                    raw_unit=str(unit),
                    raw_city=it.get("city", self.default_city),
                    raw_published_date=it.get("date"),
                    brand=it.get("brand"),
                    grade=it.get("grade"),
                    price_basis=PriceBasis.RETAIL,
                    original_source_citation="GharHub Retail Cost Monitor",
                    raw_metadata={
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                        "source_type": "structured",
                    },
                    source_url=self.base_url,
                )
            )
        return records

    def _parse_html_tables(self, html_content: str) -> List[RawSourceRecord]:
        """
        Parses GharHub HTML with strict section precedence:
        1. If 'Live Rates Today' / 'Live Cement Rates' section is detected, ONLY extract from that section's table.
        2. Discard older static article / SEO price tables to prevent conflicting stale prices.
        3. Captures raw HTML evidence and extraction timestamp.
        """
        extracted_at = datetime.now(timezone.utc).isoformat()
        pub_date = self._extract_page_date(html_content)

        # Check for Live Rates section table
        live_table_match = re.search(
            r'(?:Live\s+(?:Cement\s+)?Rates\s+Today|Live\s+Rates).*?(<table[^>]*>.*?</table>)',
            html_content,
            re.DOTALL | re.IGNORECASE,
        )

        target_tables: List[str] = []
        is_live_block = False
        if live_table_match:
            # Found distinct live section; parse only this table
            target_tables = [live_table_match.group(1)]
            is_live_block = True
        else:
            # Fall back to all tables, but skip tables that are marked as old articles or archives
            all_tables = re.findall(r"<table[^>]*>.*?</table>", html_content, re.DOTALL | re.IGNORECASE)
            for t in all_tables:
                if "archive" not in t.lower() and "previous" not in t.lower():
                    target_tables.append(t)

        records: List[RawSourceRecord] = []
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
        cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)

        for t_html in target_tables:
            for row_match in row_pattern.finditer(t_html):
                row_html = row_match.group(1)
                raw_cells = [re.sub(r"<[^>]+>", " ", c).strip() for c in cell_pattern.findall(row_html)]
                cells = [" ".join(c.split()) for c in raw_cells if c]

                if len(cells) < 2:
                    continue

                # Skip header row
                first_cell_lower = cells[0].lower()
                if any(h in first_cell_lower for h in ["product", "item", "brick type", "commodity", "brand name"]):
                    continue

                product_name = cells[0]
                price_text = cells[1]

                # Parse price (handles ranges e.g. "PKR 1,610 / bag", "PKR 256 – 258 / kg")
                price_val = self._extract_price(price_text)
                if price_val is None:
                    continue

                # Detect unit
                unit = self._extract_unit(product_name, price_text, cells)

                # Detect brand
                brand = self._extract_brand(product_name)

                # Detect grade
                grade = self._extract_grade(product_name, cells)

                # Locality / Origin
                locality = cells[2] if len(cells) > 2 and len(cells[2]) < 30 else None

                records.append(
                    RawSourceRecord(
                        raw_material_name=product_name,
                        raw_price=price_val,
                        raw_unit=unit,
                        raw_city=self.default_city,
                        raw_published_date=pub_date,
                        brand=brand,
                        grade=grade,
                        specification=f"GharHub Retail Benchmark ({locality or 'General'})",
                        price_basis=PriceBasis.RETAIL,
                        original_source_citation="GharHub Live Rates Monitor" if is_live_block else "GharHub Cost Guide",
                        raw_metadata={
                            "raw_price_string": price_text,
                            "origin_or_type": locality,
                            "extracted_at": extracted_at,
                            "is_live_block": is_live_block,
                            "html_evidence": "<tr>" + row_html + "</tr>",
                        },
                        source_url=self.base_url,
                    )
                )

        return records

    def _extract_price(self, price_str: str) -> Optional[float]:
        """Extracts clean numeric price; computes midpoint if range given."""
        clean = price_str.replace("PKR", "").replace("Rs.", "").replace("Rs", "").replace(",", "")
        clean = clean.replace("—", "").replace("-", " - ")

        range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)", clean)
        if range_match:
            try:
                p1 = float(range_match.group(1))
                p2 = float(range_match.group(2))
                return round((p1 + p2) / 2.0, 2)
            except ValueError:
                pass

        single_match = re.search(r"(\d+(?:\.\d+)?)", clean)
        if single_match:
            try:
                return float(single_match.group(1))
            except ValueError:
                pass
        return None

    def _extract_unit(self, name: str, price_str: str, cells: List[str]) -> str:
        combined = f"{name} {price_str} {' '.join(cells)}".lower()
        if "/ bag" in combined or "bag" in combined:
            return "bag_50kg"
        if "/ kg" in combined or "per kg" in combined:
            return "kg"
        if "per ton" in combined or "/ ton" in combined:
            return "metric_ton"
        if "/ brick" in combined or "brick" in combined:
            return "piece"
        if "per 1,000" in combined or "per 1000" in combined:
            return "1000_bricks"
        if "/ cft" in combined or "per cft" in combined or "cft" in combined:
            return "cft"
        if "dumper" in combined:
            return "100_cft"
        return "cft"

    def _extract_brand(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        for b in [
            "maple leaf", "dg khan", "bestway", "lucky", "flying",
            "fauji", "cherat", "mughal", "sheikhoo", "kamran",
            "amreli", "agha", "pakcem", "pioneer", "xtreme"
        ]:
            if b in name_lower:
                return b.title()
        return None

    def _extract_grade(self, name: str, cells: List[str]) -> Optional[str]:
        combined = f"{name} {' '.join(cells)}".lower()
        if "grade 60" in combined or "g-60" in combined or "g60" in combined:
            return "Grade 60"
        if "grade 40" in combined or "g-40" in combined or "g40" in combined:
            return "Grade 40"
        if "opc" in combined:
            return "OPC"
        if "src" in combined:
            return "SRC"
        if "white" in combined:
            return "White Cement"
        if "awwal" in combined or "a-grade" in combined or "a-class" in combined:
            return "Awwal Class"
        if "doam" in combined or "doem" in combined or "b-grade" in combined:
            return "Doam Class"
        return None
