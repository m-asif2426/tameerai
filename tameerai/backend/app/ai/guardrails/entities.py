"""
TameerAI - Construction Entity Extraction Engine (Phase 03F)
Layer 3 of the Intelligent Construction Intent Architecture.
Extracts structured technical entities: materials, building components, structural elements,
measurements, units, quantities, soil conditions, building loads, activities, cost parameters,
and Pakistani regulatory jurisdictions.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.guardrails.normalizer import NormalizedQuery


class EntityCategory(str, Enum):
    MATERIAL = "material"
    BUILDING_COMPONENT = "building_component"
    STRUCTURAL_ELEMENT = "structural_element"
    MEASUREMENT = "measurement"
    UNIT = "unit"
    QUANTITY = "quantity"
    SOIL_CONDITION = "soil_condition"
    BUILDING_LOAD = "building_load"
    CONSTRUCTION_ACTIVITY = "construction_activity"
    COST_PARAMETER = "cost_parameter"
    LOCATION_JURISDICTION = "location_jurisdiction"


class ExtractedEntity(BaseModel):
    """Structured representation of a recognized technical construction entity."""
    category: EntityCategory
    value: str
    canonical_value: str
    unit: Optional[str] = None
    numeric_quantity: Optional[float] = None
    confidence: float = 0.90


# Entity lexical databases
MATERIALS_MAP = {
    "cement": "cement", "opc": "ordinary_portland_cement", "src": "sulphate_resistant_cement",
    "saria": "steel_rebar", "steel": "steel_rebar", "rebar": "steel_rebar",
    "ret": "sand", "sand": "sand", "bajri": "coarse_aggregate", "aggregate": "coarse_aggregate",
    "crush": "crushed_stone", "brick": "clay_brick", "eent": "clay_brick", "block": "concrete_block",
    "concrete": "concrete", "rcc": "reinforced_concrete", "pcc": "plain_concrete",
    "plaster": "mortar_plaster", "paint": "paint", "marble": "marble", "tiles": "ceramic_tiles",
    "mortar": "cement_mortar", "epoxy": "epoxy", "waterproofing": "waterproofing_membrane",
    # Urdu Script
    "کنکریٹ": "concrete", "سیمنٹ": "cement", "سریہ": "steel_rebar", "ریت": "sand",
    "بجری": "coarse_aggregate", "اینٹ": "clay_brick", "پلستر": "mortar_plaster",
}

BUILDING_COMPONENTS_MAP = {
    "foundation": "foundation", "bunyaad": "foundation", "footing": "footing",
    "raft": "raft_foundation", "pile": "pile_foundation", "slab": "floor_slab",
    "lanter": "concrete_slab_or_lintel", "beam": "structural_beam", "column": "structural_column",
    "pillar": "structural_column", "wall": "masonry_wall", "deewar": "masonry_wall",
    "lintel": "lintel_beam", "parapet": "parapet_wall", "plinth": "plinth_beam",
    "dpc": "damp_proof_course", "staircase": "staircase", "basement": "basement",
    "tehkhaana": "basement", "roof": "roof_slab", "chhat": "roof_slab",
    # Urdu Script
    "بنیاد": "foundation", "لینٹر": "concrete_slab_or_lintel", "سلیب": "floor_slab",
    "کالم": "structural_column", "بیم": "structural_beam", "دیوار": "masonry_wall",
    "چھت": "roof_slab",
}

STRUCTURAL_ELEMENTS_MAP = {
    "main bar": "main_reinforcement", "stirrup": "shear_stirrup", "ring": "shear_stirrup",
    "tie": "column_tie", "clear cover": "concrete_cover", "cover block": "cover_block",
    "lap length": "lap_splice", "development length": "development_length",
    "retaining wall": "retaining_wall", "expansion joint": "expansion_joint",
}

ACTIVITIES_MAP = {
    "curing": "curing", "tarai": "curing", "dhalai": "concrete_pouring", "pouring": "concrete_pouring",
    "casting": "concrete_pouring", "shuttering": "formwork", "formwork": "formwork",
    "excavation": "excavation", "khudai": "excavation", "compaction": "soil_compaction",
    "slump test": "slump_test", "soil test": "soil_investigation", "spt": "standard_penetration_test",
    "plastering": "plastering",
    # Urdu Script
    "ترائی": "curing", "ڈھلائی": "concrete_pouring", "شٹرنگ": "formwork",
    "کھدائی": "excavation", "سلمپ ٹیسٹ": "slump_test",
}

SOIL_CONDITIONS_MAP = {
    "bearing capacity": "soil_bearing_capacity", "clay": "clayey_soil", "sand": "sandy_soil",
    "silt": "silty_soil", "loose soil": "loose_soil", "water table": "groundwater_table",
    "settlement": "differential_settlement", "hard strata": "hard_soil_strata",
    # Urdu Script
    "برداشت کی صلاحیت": "soil_bearing_capacity", "مٹی کی برداشت کی صلاحیت": "soil_bearing_capacity",
    "مٹی": "soil",
}

BUILDING_LOADS_MAP = {
    "dead load": "dead_load", "live load": "live_load", "wind load": "wind_load",
    "seismic": "earthquake_load", "single storey": "single_storey_load",
    "double storey": "double_storey_load", "commercial load": "commercial_occupancy_load",
    "1 storey": "1_storey", "2 storey": "2_storey", "3 storey": "3_storey",
}

JURISDICTIONS_MAP = {
    "lda": "Lahore Development Authority",
    "cda": "Capital Development Authority",
    "sbca": "Sindh Building Control Authority",
    "kda": "Karachi Development Authority",
    "rda": "Rawalpindi Development Authority",
    "pec": "Pakistan Engineering Council",
}

PAKISTANI_CITIES_MAP = {
    "lahore": "Lahore", "karachi": "Karachi", "islamabad": "Islamabad",
    "rawalpindi": "Rawalpindi", "pindi": "Rawalpindi", "peshawar": "Peshawar",
    "multan": "Multan", "faisalabad": "Faisalabad", "quetta": "Quetta",
    "gujranwala": "Gujranwala", "sialkot": "Sialkot", "abbottabad": "Abbottabad",
    "bahawalpur": "Bahawalpur", "sukkur": "Sukkur", "hyderabad": "Hyderabad",
    "sargodha": "Sargodha", "sahiwal": "Sahiwal", "sheikhupura": "Sheikhupura",
    "larkana": "Larkana", "rahim yar khan": "Rahim Yar Khan", "ryk": "Rahim Yar Khan",
    "mianwali": "Mianwali", "mingora": "Mingora", "swat": "Mingora",
    "gwadar": "Gwadar", "gawadar": "Gwadar", "گوادر": "Gwadar", "turbat": "Turbat",
    "attock": "Attock", "dadu": "Dadu", "bannu": "Bannu", "khuzdar": "Khuzdar",
    "vehari": "Vehari", "jhang": "Jhang", "nawabshah": "Nawabshah", "mirpurkhas": "Mirpukhas",
    "mirpukhas": "Mirpukhas", "kasur": "Kasur", "okara": "Okara", "gujrat": "Gujrat",
    # Urdu script
    "لاہور": "Lahore", "کراچی": "Karachi", "اسلام آباد": "Islamabad",
    "راولپنڈی": "Rawalpindi", "پشاور": "Peshawar", "ملتان": "Multan",
    "فیصل آباد": "Faisalabad", "کوئٹہ": "Quetta", "گوجرانوالہ": "Gujranwala",
    "سیالکوٹ": "Sialkot", "ایبٹ آباد": "Abbottabad", "حیدرآباد": "Hyderabad",
    "سکھر": "Sukkur", "بہاولپور": "Bahawalpur", "سرگودھا": "Sargodha",
}

COST_MAP = {
    "rate": "unit_rate", "cost": "construction_cost", "estimate": "cost_estimate",
    "budget": "project_budget", "running bill": "interim_payment_certificate",
    "thekedar": "contractor_fee", "daily wage": "labor_daily_wage", "boq": "bill_of_quantities",
}


class ConstructionEntityExtractor:
    """
    Extracts structured technical entities from normalized construction queries.
    """

    @classmethod
    def extract_entities(cls, normalized: NormalizedQuery) -> List[ExtractedEntity]:
        """
        Scans normalized text for civil engineering entities, dimensions, and plot areas.
        """
        text = normalized.normalized_query
        entities: List[ExtractedEntity] = []
        found_spans: Set[str] = set()

        # 1. Plot area and dimension patterns (e.g. 5 marla, 10 kanal, 1000 sqft, 12 mm, 3000 psi)
        dimension_patterns = [
            (re.compile(r"\b(\d+(?:\.\d+)?)\s*(marla|kanal|sqft|sft|sqyd|square\s+feet|gaz)\b", re.IGNORECASE), "area"),
            (re.compile(r"\b(\d+(?:\.\d+)?)\s*(feet|ft|inch|inches|in|meter|m|mm|cm)\b", re.IGNORECASE), "length"),
            (re.compile(r"\b(\d+(?:\.\d+)?)\s*(psi|mpa|n/mm2)\b", re.IGNORECASE), "strength"),
            (re.compile(r"\b(\d+(?:\.\d+)?)\s*(bags?|bori|boriyan|ton|tons|kg|lbs?)\b", re.IGNORECASE), "weight_or_volume"),
            (re.compile(r"\bgrade\s*(40|60)\b", re.IGNORECASE), "rebar_grade"),
            (re.compile(r"\b(1:2:4|1:4:8|1:1\.5:3|1:3|1:4|1:6)\b", re.IGNORECASE), "mix_ratio"),
        ]

        for pat, dim_type in dimension_patterns:
            for match in pat.finditer(text):
                matched_str = match.group(0)
                if matched_str in found_spans:
                    continue
                found_spans.add(matched_str)

                qty_val = None
                unit_val = None
                if len(match.groups()) >= 2:
                    try:
                        qty_val = float(match.group(1))
                    except ValueError:
                        pass
                    unit_val = match.group(2).lower()
                elif len(match.groups()) == 1:
                    unit_val = match.group(1).lower()

                entities.append(
                    ExtractedEntity(
                        category=EntityCategory.MEASUREMENT,
                        value=matched_str,
                        canonical_value=f"{dim_type}:{matched_str.lower()}",
                        unit=unit_val,
                        numeric_quantity=qty_val,
                        confidence=0.95,
                    )
                )

        # Helper to search dictionary mappings
        def match_dict(mapping: Dict[str, str], cat: EntityCategory):
            for phrase, canon in mapping.items():
                if " " in phrase:
                    if phrase in text:
                        if phrase not in found_spans:
                            found_spans.add(phrase)
                            entities.append(ExtractedEntity(category=cat, value=phrase, canonical_value=canon))
                else:
                    if re.search(r"\b" + re.escape(phrase) + r"\b", text):
                        if phrase not in found_spans:
                            found_spans.add(phrase)
                            entities.append(ExtractedEntity(category=cat, value=phrase, canonical_value=canon))

        match_dict(MATERIALS_MAP, EntityCategory.MATERIAL)
        match_dict(BUILDING_COMPONENTS_MAP, EntityCategory.BUILDING_COMPONENT)
        match_dict(STRUCTURAL_ELEMENTS_MAP, EntityCategory.STRUCTURAL_ELEMENT)
        match_dict(ACTIVITIES_MAP, EntityCategory.CONSTRUCTION_ACTIVITY)
        match_dict(SOIL_CONDITIONS_MAP, EntityCategory.SOIL_CONDITION)
        match_dict(BUILDING_LOADS_MAP, EntityCategory.BUILDING_LOAD)
        match_dict(JURISDICTIONS_MAP, EntityCategory.LOCATION_JURISDICTION)
        match_dict(PAKISTANI_CITIES_MAP, EntityCategory.LOCATION_JURISDICTION)
        match_dict(COST_MAP, EntityCategory.COST_PARAMETER)

        return entities
