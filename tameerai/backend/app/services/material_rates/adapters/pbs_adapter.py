"""
TameerAI - Pakistan Bureau of Statistics (PBS) Statistical Source Adapter (Stage 2B / 2B.1 Correction)

Ingests official government price statistics from the Pakistan Bureau of Statistics (PBS):
1. Monthly Inter-City Construction Items Prices (Urban & Rural Excel workbooks:
   Urbn-Construction-12.xlsx, Rural-Construction-13.xlsx).
   Price Basis: RETAIL (Inter-City Consumer Prices).
2. Weekly Sensitive Price Indicator (SPI) bulletins (Annexures across 17 commercial centers).
   Price Basis: STATISTICAL_INDEX.

Zero external dependencies: uses native Python zipfile + xml.etree.ElementTree OpenXML parser.
"""

from datetime import datetime, timezone
import io
import json
import logging
import re
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET
import zipfile

from app.services.material_rates.base_adapter import BaseSourceAdapter
from app.services.material_rates.contracts import (
    CollectionSourceType,
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
)
from app.services.material_rates.http_client import SafeHttpClient

logger = logging.getLogger(__name__)


class PbsStatisticalSourceAdapter(BaseSourceAdapter):
    """
    Adapter for official statistical data from Pakistan Bureau of Statistics (PBS).
    Distinguishes:
    - Monthly Inter-City Construction Consumer Prices (Bricks, Blocks, Bajri, Sand, Cement, Steel)
    - Weekly Sensitive Price Indicator (SPI) bulletins
    """

    def __init__(
        self,
        *,
        source_code: str = "PBS_STATISTICAL_SPI",
        source_name: str = "Pakistan Bureau of Statistics - Price Statistics",
        base_url: str = "https://www.pbs.gov.pk",
        http_client: Optional[SafeHttpClient] = None,
    ):
        super().__init__(
            source_code=source_code,
            source_name=source_name,
            source_type=CollectionSourceType.OFFICIAL,
            source_category=SourceCategory.OFFICIAL_STATISTICAL,
            default_price_basis=PriceBasis.STATISTICAL_INDEX,
            base_url=base_url,
            default_city="Islamabad",
        )
        self.http_client = http_client

    async def fetch_raw_data(self, endpoint_url: Optional[str] = None, **kwargs) -> Any:
        """Fetches raw SPI or monthly Excel payload via SafeHttpClient or returns supplied payload."""
        if "payload" in kwargs:
            return kwargs["payload"]
        if "raw_payload" in kwargs:
            return kwargs["raw_payload"]

        target_url = endpoint_url or f"{self.base_url}/price-statistics/weekly-spi"
        if not self.http_client:
            self.http_client = SafeHttpClient(allowed_domains=["pbs.gov.pk", "www.pbs.gov.pk"])

        resp = await self.http_client.get(target_url)
        return resp.content if target_url.endswith(".xlsx") else resp.text

    def parse_raw_data(self, raw_payload: Any) -> List[RawSourceRecord]:
        """
        Parses PBS data in various formats:
        1. Excel bytes (.xlsx OpenXML) from monthly construction reports.
        2. JSON payload from API/fixture.
        3. HTML table strings from SPI reports.
        """
        if isinstance(raw_payload, bytes):
            return self.parse_construction_excel(raw_payload)

        if isinstance(raw_payload, str):
            trimmed = raw_payload.strip()
            if trimmed.startswith(("{", "[")):
                try:
                    parsed_json = json.loads(trimmed)
                    return self._parse_json_data(parsed_json)
                except json.JSONDecodeError:
                    pass
            return self._parse_html_table(trimmed)

        if isinstance(raw_payload, (list, dict)):
            return self._parse_json_data(raw_payload)

        return []

    def parse_construction_excel(self, content_bytes: bytes) -> List[RawSourceRecord]:
        """
        Native zero-dependency OpenXML parser for PBS Monthly Construction Items Prices.
        Extracts:
        - Bricks (New first class) (1000)
        - Cement Blocks (6"x8"x12") (100)
        - Bajri (rata) (per truck) (100 CFT)
        - Sand (Black Pit) (per truck) (100 CFT)
        - Cement (local) (50kg bag)
        - Iron bars (1/2" 40 grade) (per tonne)
        """
        records: List[RawSourceRecord] = []
        try:
            zf = zipfile.ZipFile(io.BytesIO(content_bytes))
        except Exception as e:
            logger.warning("Failed to open PBS Excel archive: %s", e)
            return []

        # 1. Read shared strings table
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            ss_xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss_xml.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                t_node = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                if t_node is not None and t_node.text:
                    shared_strings.append(t_node.text)
                else:
                    texts = [r.text for r in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t") if r.text]
                    shared_strings.append("".join(texts))

        # 1b. Read package compilation metadata from docProps/core.xml (Task 6)
        compilation_dt = None
        if "docProps/core.xml" in zf.namelist():
            try:
                core_xml = ET.fromstring(zf.read("docProps/core.xml"))
                ns = {"dcterms": "http://purl.org/dc/terms/"}
                created_node = core_xml.find("dcterms:created", ns)
                if created_node is not None and created_node.text:
                    compilation_dt = created_node.text.strip()
            except Exception as e:
                logger.debug("Could not parse docProps/core.xml: %s", e)

        # 2. Read sheet1.xml
        if "xl/worksheets/sheet1.xml" not in zf.namelist():
            return []

        sheet_xml = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        raw_rows: List[Dict[str, str]] = []
        for r in sheet_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            row_vals: Dict[str, str] = {}
            for c in r.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                ref = c.attrib.get("r", "")
                col_letter = re.sub(r"[0-9]", "", ref)
                cell_type = c.attrib.get("t")
                v_tag = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                val = v_tag.text if v_tag is not None else ""
                if cell_type == "s" and val.isdigit():
                    idx = int(val)
                    val = shared_strings[idx] if idx < len(shared_strings) else val
                row_vals[col_letter] = val
            if row_vals:
                raw_rows.append(row_vals)

        if len(raw_rows) < 4:
            return []

        # Title and Period
        report_title = raw_rows[0].get("A", "Construction Consumer Prices")
        period_str = raw_rows[1].get("A", "October, 2026")
        is_rural = "rural" in report_title.lower()
        scope_tag = "Rural" if is_rural else "Urban"

        # Parse period date (e.g. "October, 2026")
        published_dt = None
        for fmt in ("%B, %Y", "%B %Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                published_dt = datetime.strptime(period_str.strip(), fmt).replace(tzinfo=timezone.utc).isoformat()
                break
            except ValueError:
                continue

        # Column definitions map column letter to (material_name, canonical_unit, raw_unit)
        header_row = raw_rows[2]
        col_map: Dict[str, Dict[str, str]] = {}

        for col_let, text in header_row.items():
            if col_let == "A":
                continue
            lower_h = text.lower()
            if "brick" in lower_h:
                col_map[col_let] = {
                    "name": "Clay Bricks Awwal Class 1000 Nos",
                    "unit": "1000 nos",
                    "category": "bricks",
                    "grade": "First Class",
                }
            elif "block" in lower_h:
                col_map[col_let] = {
                    "name": "Solid Concrete Masonry Blocks",
                    "unit": "100 nos",
                    "category": "blocks",
                    "grade": '6"x8"x12"',
                }
            elif "bajri" in lower_h or "crush" in lower_h:
                col_map[col_let] = {
                    "name": "Crush / Bajri Aggregate",
                    "unit": "100 CFT",
                    "category": "crush",
                    "grade": "Rata",
                }
            elif "sand" in lower_h:
                col_map[col_let] = {
                    "name": "Pit Sand / Construction Sand",
                    "unit": "100 CFT",
                    "category": "sand",
                    "grade": "Black Pit",
                }
            elif "cement" in lower_h:
                col_map[col_let] = {
                    "name": "Ordinary Portland Cement 50kg Bag",
                    "unit": "50kg bag",
                    "category": "cement",
                    "grade": "Local",
                }
            elif "iron" in lower_h or "bar" in lower_h or "steel" in lower_h:
                # Task 1: PBS explicitly reports Iron bars (1/2" 40 grade) (M.S. bars) -> Grade 40
                col_map[col_let] = {
                    "name": "Mild Steel Deformed Iron Bars Grade 40",
                    "unit": "per tonne",
                    "category": "steel",
                    "grade": "Grade 40",
                }

        # Data rows start at index 3
        for r_dict in raw_rows[3:]:
            city_name = r_dict.get("A", "").strip()
            if not city_name or "average" in city_name.lower() or "pakistan" in city_name.lower():
                continue

            for col_let, info in col_map.items():
                val_str = r_dict.get(col_let, "").strip()
                if not val_str or val_str in ("-", "—", "N/A", "Nil"):
                    continue

                try:
                    price_val = float(val_str)
                except ValueError:
                    continue

                records.append(
                    RawSourceRecord(
                        raw_material_name=info["name"],
                        raw_price=price_val,
                        raw_unit=info["unit"],
                        raw_city=city_name,
                        raw_published_date=published_dt,
                        grade=info.get("grade"),
                        specification=f"PBS Monthly Inter-City Consumer Retail Price (1/2\" {info.get('grade', '')} M.S. bars, {scope_tag} Center: {city_name})",
                        price_basis=PriceBasis.RETAIL,  # Direct retail consumer market survey
                        is_syndicated=False,
                        original_source_citation=f"PBS {scope_tag} Inter-City Consumer Prices ({period_str})",
                        raw_metadata={
                            "report_title": report_title,
                            "survey_reference_period": period_str,
                            "period": period_str,
                            "survey_date": None,  # Task 2: Do not fabricate day-level survey date (use NULL)
                            "workbook_compilation_date": compilation_dt,  # From OpenXML docProps/core.xml, NULL if missing
                            "official_publication_date": None,  # Task 2: NULL for unknown dates without independent evidence
                            "system_collection_timestamp": datetime.now(timezone.utc).isoformat(),
                            "scope": scope_tag,
                            "statistical_agency": "Pakistan Bureau of Statistics",
                            "evidence_type": "official_statutory_excel",
                        },
                        source_url=f"{self.base_url}/price-statistics/monthly-construction-items",
                    )
                )

        return records

    def _parse_json_data(self, payload: Any) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        item_list = payload if isinstance(payload, list) else payload.get("items", [])
        bulletin_date = payload.get("bulletin_date") if isinstance(payload, dict) else None

        for item in item_list:
            if not isinstance(item, dict):
                continue

            raw_name = item.get("item_name") or item.get("material_name") or item.get("item", "Cement Ordinary Portland")
            raw_price = item.get("price") or item.get("avg_price") or item.get("rate")
            raw_unit = item.get("unit") or item.get("measurement_unit", "50 kg bag")
            raw_city = item.get("city") or item.get("center") or self.default_city
            pub_date = item.get("published_date") or item.get("date") or bulletin_date

            if raw_price is None:
                continue

            records.append(
                RawSourceRecord(
                    raw_material_name=str(raw_name),
                    raw_price=raw_price,
                    raw_unit=str(raw_unit),
                    raw_city=str(raw_city),
                    raw_published_date=pub_date,
                    price_basis=PriceBasis.STATISTICAL_INDEX,
                    brand=item.get("brand"),
                    grade=item.get("grade"),
                    specification=item.get("specification", "SPI Weighted Average Sample"),
                    is_syndicated=False,
                    original_source_citation="Pakistan Bureau of Statistics SPI Bulletin",
                    raw_metadata={
                        "bulletin_number": item.get("bulletin_no"),
                        "sampling_center_count": item.get("centers_count", 17),
                        "source_agency": "Pakistan Bureau of Statistics",
                    },
                    source_url=f"{self.base_url}/spi",
                )
            )
        return records

    def _parse_html_table(self, html_content: str) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
        cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)

        for row_match in row_pattern.finditer(html_content):
            row_html = row_match.group(1)
            cells = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cell_pattern.findall(row_html)]
            if len(cells) >= 4:
                first_cell = cells[0].lower()
                if "cement" in first_cell or "steel" in first_cell or "brick" in first_cell:
                    item_name = cells[0]
                    unit = cells[1]
                    city = cells[2]
                    price_str = cells[3].replace(",", "").strip()
                    try:
                        price_val = float(price_str)
                        records.append(
                            RawSourceRecord(
                                raw_material_name=item_name,
                                raw_price=price_val,
                                raw_unit=unit,
                                raw_city=city,
                                raw_published_date=None,  # Do not invent fake dates if missing
                                price_basis=PriceBasis.STATISTICAL_INDEX,
                                original_source_citation="PBS Statistical Bulletin",
                                raw_metadata={"html_scraped": True},
                                source_url=f"{self.base_url}/spi",
                            )
                        )
                    except ValueError:
                        continue
        return records
