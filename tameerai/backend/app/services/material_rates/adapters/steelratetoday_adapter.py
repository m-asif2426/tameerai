"""
TameerAI - SteelRateToday Source Adapter (Stage 2B / 2B.1 Correction)

Ingests specialized rebar and structural steel wholesale market intelligence
from SteelRateToday (https://steelratetoday.pk/), focusing on major trading yards:
Badami Bagh / Misri Shah (Lahore), Shershah (Karachi), Islamabad, Rawalpindi, etc.

Supports:
- Table 1: Size-wise Grade 40 and Grade 60 rates (Per KG & Per Ton)
- Table 2: Brand-wise rates by bar size with multi-row span (Mughal, Amreli, Ittehad, etc.)
- Table 3: City-specific baseline market rates (Lahore, Karachi, Islamabad, etc.)
- Publication / Modified date discovery via Schema.org JSON-LD and meta tags
- Disclaimer capture ("Indicative market rates; not confirmed dealer transactions")
"""

from datetime import datetime, timezone
from decimal import Decimal
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


class SteelRateTodaySourceAdapter(BaseSourceAdapter):
    """
    Adapter for SteelRateToday specialized steel market tracker.
    Category: SECONDARY_MARKET_PUBLISHER.
    Price Basis: WHOLESALE (Steel yard trade level).
    Verification Status: Indicative estimate (secondary publisher roundup).
    """

    def __init__(
        self,
        *,
        source_code: str = "STEELRATETODAY_PK_PUBLISHER",
        source_name: str = "SteelRateToday Steel Market Monitor",
        base_url: str = "https://steelratetoday.pk",
        http_client: Optional[SafeHttpClient] = None,
        default_city: str = "Lahore",
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.AGGREGATOR,
            source_category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
            default_price_basis=PriceBasis.WHOLESALE,
            base_url=base_url,
            default_city=default_city,
        )
        self.http_client = http_client

    async def fetch_raw_data(self, endpoint_url: Optional[str] = None, **kwargs) -> Any:
        """Fetches steel rate sheets via SafeHttpClient or returns supplied payload."""
        if "payload" in kwargs:
            return kwargs["payload"]
        if "raw_payload" in kwargs:
            return kwargs["raw_payload"]

        target_url = endpoint_url or self.base_url
        if not self.http_client:
            self.http_client = SafeHttpClient(allowed_domains=["steelratetoday.pk", "www.steelratetoday.pk"])

        resp = await self.http_client.get(target_url)
        return resp.text

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """
        Parses structured steel market quotes from JSON or HTML tables.
        Captures brand, grade (Grade 40/60), bar sizes, per kg/ton, city, and dates.
        """
        if isinstance(raw_payload, str):
            trimmed = raw_payload.strip()
            if trimmed.startswith(("{", "[")):
                try:
                    parsed = json.loads(trimmed)
                    return self._parse_json_steel(parsed)
                except json.JSONDecodeError:
                    pass
            return self._parse_html_steel(trimmed)

        if isinstance(raw_payload, (list, dict)):
            return self._parse_json_steel(raw_payload)

        return []

    def _extract_published_date(self, html_content: str) -> Optional[str]:
        """Extracts dateModified or datePublished from JSON-LD schema or meta tags."""
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

    def _extract_disclaimer(self, html_content: str) -> str:
        """Extracts market disclaimer if present in HTML."""
        disc_match = re.search(r'(?:disclaimer|note)[^<\n]{0,20}:?\s*([^<\n]+(?:market|indicative|vary|dealer)[^<\n]+)', html_content, re.IGNORECASE)
        if disc_match:
            return " ".join(disc_match.group(0).split())
        return "Steel rates are collected from local markets/mills and are indicative secondary estimates."

    def _clean_price_num(self, val_str: str) -> Optional[float]:
        """Extracts clean numeric price from formatted text."""
        clean = val_str.replace("Rs.", "").replace("Rs", "").replace("PKR", "").replace(",", "").strip()
        clean = clean.replace("—", "").replace("-", "").strip()
        if not clean:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)", clean)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _parse_html_steel(self, html_content: str) -> List[RawSourceRecord]:
        """Parses steel tables from steelratetoday.pk (Table 1: Sizes, Table 2: Brands, Table 3: Cities)."""
        records: List[RawSourceRecord] = []
        pub_date = self._extract_published_date(html_content)
        disclaimer = self._extract_disclaimer(html_content)

        tables = re.findall(r"<table[^>]*>(.*?)</table>", html_content, re.DOTALL | re.IGNORECASE)
        if not tables:
            # Fall back to regex over rows if no complete table tags
            return self._parse_generic_rows(html_content, pub_date, disclaimer)

        for table_idx, t_html in enumerate(tables):
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", t_html, re.DOTALL | re.IGNORECASE)
            if not rows:
                continue

            current_brand = "Standard Deformed Rebar"

            for r_html in rows:
                cells = [
                    " ".join(re.sub(r"<[^>]+>", " ", c).split())
                    for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r_html, re.DOTALL | re.IGNORECASE)
                ]
                cells = [c for c in cells if c]
                if not cells:
                    continue

                first_lower = cells[0].lower()
                # Skip header rows
                if any(h in first_lower for h in ["steel brand", "size", "city", "rates", "product", "sr"]):
                    continue

                # Table 2 pattern: Brand-wise with rowspan
                # Header: [Steel Brand, Size, Grade 40 Per KG, Grade 40 Per Ton, Grade 60 Per KG, Grade 60 Per Ton]
                if len(cells) == 6 and any("sutar" in c.lower() or "mm" in c.lower() for c in cells):
                    current_brand = cells[0]
                    size = cells[1]
                    p_g40_kg = self._clean_price_num(cells[2])
                    p_g40_ton = self._clean_price_num(cells[3])
                    p_g60_kg = self._clean_price_num(cells[4])
                    p_g60_ton = self._clean_price_num(cells[5])

                    self._add_brand_grade_records(
                        records, current_brand, size, p_g40_kg, p_g40_ton, p_g60_kg, p_g60_ton, pub_date, disclaimer
                    )
                    continue

                if len(cells) == 5 and any("sutar" in c.lower() or "mm" in c.lower() for c in cells):
                    # Continued row under current_brand
                    size = cells[0]
                    p_g40_kg = self._clean_price_num(cells[1])
                    p_g40_ton = self._clean_price_num(cells[2])
                    p_g60_kg = self._clean_price_num(cells[3])
                    p_g60_ton = self._clean_price_num(cells[4])

                    self._add_brand_grade_records(
                        records, current_brand, size, p_g40_kg, p_g40_ton, p_g60_kg, p_g60_ton, pub_date, disclaimer
                    )
                    continue

                # Table 1 pattern: Size-wise baseline
                # Header: [Size, Grade 40 Per KG, Grade 40 Per Ton, Grade 60 Per KG, Grade 60 Per Ton]
                if len(cells) == 5 and ("sutar" in first_lower or "mm" in first_lower):
                    size = cells[0]
                    p_g40_kg = self._clean_price_num(cells[1])
                    p_g40_ton = self._clean_price_num(cells[2])
                    p_g60_kg = self._clean_price_num(cells[3])
                    p_g60_ton = self._clean_price_num(cells[4])

                    self._add_brand_grade_records(
                        records, "Baseline Steel", size, p_g40_kg, p_g40_ton, p_g60_kg, p_g60_ton, pub_date, disclaimer
                    )
                    continue

                # Table 3 pattern: City-wise rates
                # Header: [City, Steel Rate Per KG, Steel Rate Per Ton]
                if len(cells) >= 3 and any(city_name in first_lower for city_name in ["lahore", "karachi", "islamabad", "rawalpindi", "faisalabad", "multan", "peshawar"]):
                    city = cells[0]
                    p_kg = self._clean_price_num(cells[1])
                    p_ton = self._clean_price_num(cells[2])

                    if p_ton:
                        records.append(
                            RawSourceRecord(
                                raw_material_name="Deformed Steel Bar Grade 60",
                                raw_price=p_ton,
                                raw_unit="metric_ton",
                                raw_city=city,
                                raw_published_date=pub_date,
                                brand="Market Average",
                                grade="Grade 60",
                                specification=f"City Market Baseline Rate ({city})",
                                price_basis=PriceBasis.WHOLESALE,
                                is_syndicated=False,
                                original_source_citation="SteelRateToday City Table",
                                raw_metadata={
                                    "city": city,
                                    "disclaimer": disclaimer,
                                    "evidence_url": self.base_url,
                                },
                                source_url=self.base_url,
                            )
                        )
                    elif p_kg:
                        records.append(
                            RawSourceRecord(
                                raw_material_name="Deformed Steel Bar Grade 60",
                                raw_price=p_kg,
                                raw_unit="kg",
                                raw_city=city,
                                raw_published_date=pub_date,
                                brand="Market Average",
                                grade="Grade 60",
                                specification=f"City Market Baseline Rate ({city})",
                                price_basis=PriceBasis.WHOLESALE,
                                is_syndicated=False,
                                original_source_citation="SteelRateToday City Table",
                                raw_metadata={
                                    "city": city,
                                    "disclaimer": disclaimer,
                                    "evidence_url": self.base_url,
                                },
                                source_url=self.base_url,
                            )
                        )
                    continue

                # Fallback: 3+ column generic row [Brand/Mill, Price, Unit, City?]
                if len(cells) >= 2:
                    p_val = self._clean_price_num(cells[1])
                    if p_val:
                        unit = cells[2] if len(cells) > 2 and len(cells[2]) < 15 else "kg"
                        city = cells[3] if len(cells) > 3 and len(cells[3]) < 25 else self.default_city
                        records.append(
                            RawSourceRecord(
                                raw_material_name=f"Steel Rebar {cells[0]}",
                                raw_price=p_val,
                                raw_unit=unit,
                                raw_city=city,
                                raw_published_date=pub_date,
                                brand=cells[0],
                                grade="Grade 60",
                                price_basis=PriceBasis.WHOLESALE,
                                original_source_citation="SteelRateToday Generic Table",
                                raw_metadata={"disclaimer": disclaimer},
                                source_url=self.base_url,
                            )
                        )

        return records

    def _add_brand_grade_records(
        self,
        records: List[RawSourceRecord],
        brand: str,
        size: str,
        p_g40_kg: Optional[float],
        p_g40_ton: Optional[float],
        p_g60_kg: Optional[float],
        p_g60_ton: Optional[float],
        pub_date: Optional[str],
        disclaimer: str,
    ):
        """Helper to create standardized raw source records for steel grades and units."""
        # Grade 60 Per Ton (Canonical)
        if p_g60_ton:
            records.append(
                RawSourceRecord(
                    raw_material_name=f"Deformed Steel Bar {brand} Grade 60",
                    raw_price=p_g60_ton,
                    raw_unit="metric_ton",
                    raw_city=self.default_city,
                    raw_published_date=pub_date,
                    brand=brand,
                    grade="Grade 60",
                    specification=f"ASTM A615 Grade 60 ({size})",
                    price_basis=PriceBasis.WHOLESALE,
                    original_source_citation="SteelRateToday Brand Sheet",
                    raw_metadata={
                        "bar_size": size,
                        "mill": brand,
                        "disclaimer": disclaimer,
                    },
                    source_url=self.base_url,
                )
            )
        elif p_g60_kg:
            records.append(
                RawSourceRecord(
                    raw_material_name=f"Deformed Steel Bar {brand} Grade 60",
                    raw_price=p_g60_kg,
                    raw_unit="kg",
                    raw_city=self.default_city,
                    raw_published_date=pub_date,
                    brand=brand,
                    grade="Grade 60",
                    specification=f"ASTM A615 Grade 60 ({size})",
                    price_basis=PriceBasis.WHOLESALE,
                    original_source_citation="SteelRateToday Brand Sheet",
                    raw_metadata={
                        "bar_size": size,
                        "mill": brand,
                        "disclaimer": disclaimer,
                    },
                    source_url=self.base_url,
                )
            )

        # Grade 40 Per Ton (Canonical)
        if p_g40_ton:
            records.append(
                RawSourceRecord(
                    raw_material_name=f"Deformed Steel Bar {brand} Grade 40",
                    raw_price=p_g40_ton,
                    raw_unit="metric_ton",
                    raw_city=self.default_city,
                    raw_published_date=pub_date,
                    brand=brand,
                    grade="Grade 40",
                    specification=f"ASTM A615 Grade 40 ({size})",
                    price_basis=PriceBasis.WHOLESALE,
                    original_source_citation="SteelRateToday Brand Sheet",
                    raw_metadata={
                        "bar_size": size,
                        "mill": brand,
                        "disclaimer": disclaimer,
                    },
                    source_url=self.base_url,
                )
            )
        elif p_g40_kg:
            records.append(
                RawSourceRecord(
                    raw_material_name=f"Deformed Steel Bar {brand} Grade 40",
                    raw_price=p_g40_kg,
                    raw_unit="kg",
                    raw_city=self.default_city,
                    raw_published_date=pub_date,
                    brand=brand,
                    grade="Grade 40",
                    specification=f"ASTM A615 Grade 40 ({size})",
                    price_basis=PriceBasis.WHOLESALE,
                    original_source_citation="SteelRateToday Brand Sheet",
                    raw_metadata={
                        "bar_size": size,
                        "mill": brand,
                        "disclaimer": disclaimer,
                    },
                    source_url=self.base_url,
                )
            )

    def _parse_generic_rows(self, html_content: str, pub_date: Optional[str], disclaimer: str) -> List[RawSourceRecord]:
        """Fallback row parser when no <table> tags are enclosed."""
        records: List[RawSourceRecord] = []
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
        cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)

        for row_match in row_pattern.finditer(html_content):
            row_html = row_match.group(1)
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cell_pattern.findall(row_html)]
            if len(cells) >= 2:
                p_val = self._clean_price_num(cells[1])
                if p_val:
                    records.append(
                        RawSourceRecord(
                            raw_material_name=f"Steel Rebar {cells[0]}",
                            raw_price=p_val,
                            raw_unit="kg" if len(cells) < 3 else cells[2],
                            raw_city=self.default_city,
                            raw_published_date=pub_date,
                            brand=cells[0],
                            grade="Grade 60",
                            price_basis=PriceBasis.WHOLESALE,
                            original_source_citation="SteelRateToday Row",
                            raw_metadata={"disclaimer": disclaimer},
                            source_url=self.base_url,
                        )
                    )
        return records

    def _parse_json_steel(self, payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        entries = payload if isinstance(payload, list) else payload.get("steel_rates", payload.get("items", []))
        is_syndicated = bool(payload.get("is_syndicated", False)) if isinstance(payload, dict) else False

        for item in entries:
            if not isinstance(item, dict):
                continue

            brand = item.get("brand") or item.get("mill", "Standard Steel")
            grade = item.get("grade") or ("Grade 60" if "60" in str(item.get("name", "")) else "Grade 40")
            city = item.get("city") or self.default_city
            yard = item.get("market_yard") or ("Badami Bagh" if city.lower() == "lahore" else "Shershah")

            price = item.get("rate") or item.get("price") or item.get("price_per_kg")
            unit = item.get("unit", "kg")
            if not price and item.get("price_per_ton"):
                price = item.get("price_per_ton")
                unit = "metric_ton"

            if price is None:
                continue

            material_name = f"Deformed Steel Bar {brand} {grade}".strip()

            records.append(
                RawSourceRecord(
                    raw_material_name=material_name,
                    raw_price=price,
                    raw_unit=unit,
                    raw_city=city,
                    raw_published_date=item.get("date"),
                    brand=brand,
                    grade=grade,
                    specification=f"ASTM A615 {grade} ({yard} Wholesale Yard)",
                    price_basis=PriceBasis.WHOLESALE,
                    is_syndicated=is_syndicated,
                    original_source_citation=f"SteelRateToday ({yard})",
                    raw_metadata={
                        "trading_yard": yard,
                        "mill": brand,
                        "rebar_type": item.get("type", "Deformed Rebar"),
                        "disclaimer": "Indicative wholesale steel rate",
                    },
                    source_url=self.base_url,
                )
            )
        return records
