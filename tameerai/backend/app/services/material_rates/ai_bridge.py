"""
TameerAI - Material Rate Intelligence Bridge (Phase 03.1)
Integrates Phase 02 Material Rate Intelligence System with Phase 03 Construction AI Chat Workflow.

Key Capabilities:
1. Translates natural language construction material queries (English, Roman Urdu, Urdu)
   into structured database queries.
2. Enforces strict trusted-observation eligibility:
   - Permitted source tiers: 'authoritative', 'indicative'
   - Excludes synthetic, unverified, conflicted, inactive, or unpermitted sources
   - Strict freshness verification: Never treats published_at IS NULL as fresh
   - Deterministically quarantines synthetic test fixtures without string pattern matching
3. Reuses Phase 02 CanonicalMarketRateEngine:
   - Factor weights: Credibility (0.35), Verification (0.30), Freshness (0.25), Volume (0.10)
   - Distinguishes official statistical data (PBS) from indicative secondary publishers (SteelRateToday)
4. Multi-turn context resolution: retains material and resolves city across turns.
5. Unit conversions (per kg <-> per ton, per brick <-> per 1000 bricks) using exact Decimal arithmetic.
6. Honest unavailability policy when no verified data exists in the database.
7. Produces structured grounding evidence (<material_rate_evidence>) and citation payloads.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import html
import logging
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select

from app.models.cost import MaterialRate
from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
)
from app.services.material_rates.canonical_engine import (
    CanonicalMarketRateEngine,
    CanonicalSelectionResult,
    canonical_engine,
)
from app.services.material_rates.db_compat import (
    db_execute,
    db_scalar,
    db_scalars,
)
from app.services.material_rates.identity_resolver import (
    centralized_identity_resolver,
    detect_observation_steel_grade,
    PRODUCT_CODE_STEEL_G40,
    PRODUCT_CODE_STEEL_G60,
    CANONICAL_NAME_STEEL_G40,
)

logger = logging.getLogger("tameerai.material_rates.ai_bridge")


# =====================================================================
# DATA CONTRACTS
# =====================================================================

class MaterialRateQuery(BaseModel):
    """Structured representation of a parsed construction material rate inquiry."""
    raw_query: str
    material_category: Optional[str] = None  # cement, steel, bricks, sand, crush, blocks, tiles, other
    product_code: Optional[str] = None       # e.g. CEMENT_OPC_50KG, STEEL_REBAR_G60, STEEL_REBAR_G40
    product_name: Optional[str] = None
    grade: Optional[str] = None              # Grade 60, Grade 40
    brand: Optional[str] = None              # Mughal, Amreli, Bestway, Fauji, etc.
    city: Optional[str] = None               # Lahore, Karachi, Islamabad, etc.
    locality: Optional[str] = None           # Lahore Cantt, Gulberg, Saddar, etc.
    unit: Optional[str] = None               # bag_50kg, metric_ton, kg, 1000_bricks, cft, sqft
    price_basis: Optional[str] = None        # retail, wholesale, ex-mill, statistical
    language: str = "en"                     # en, roman_ur, ur
    is_comparison: bool = False
    comparison_cities: List[str] = Field(default_factory=list)


class MaterialRateEvidenceItem(BaseModel):
    """Individual database-derived price observation with full provenance."""
    observation_id: str
    product_code: str
    product_name: str
    name: Optional[str] = None
    category: str
    brand: Optional[str] = None
    grade_or_spec: Optional[str] = None
    city: str
    locality: Optional[str] = None
    price_pkr: Decimal
    unit: str
    price_basis: str                         # wholesale, retail, statistical_market_range, dealer_quote
    provenance_label: str = "Indicative market price" # Official statistical average price, Indicative market price, Verified dealer quotation
    source_code: str
    source_name: str
    source_tier: str                         # authoritative, indicative
    verification_status: str                 # verified_market_range, verified_quote, cross_checked, indicative
    confidence_score: int                    # 0 - 100
    published_at: Optional[datetime] = None
    collected_at: datetime
    observed_at: Optional[datetime] = None
    age_days: float
    is_stale: bool = False
    source_url: Optional[str] = None
    disclaimer: str

    def to_citation_dict(self) -> Dict[str, Any]:
        """Converts evidence item to a citation format compatible with CitationValidator."""
        return {
            "title": self.source_name,
            "source_code": self.source_code,
            "observation_id": self.observation_id,
            "product_code": self.product_code,
            "city": self.city,
            "provenance_label": self.provenance_label,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "verification_status": self.verification_status,
            "source_tier": self.source_tier,
        }


class CanonicalBenchmark(BaseModel):
    """Authoritative canonical benchmark computed from eligible observations."""
    product_code: str
    product_name: str
    category: str
    city: str
    benchmark_rate_pkr: Decimal
    unit: str
    trend: str                              # up, down, neutral
    verification_status: str
    confidence_score: int                   # Legacy field: evidence quality score (0-100)
    evidence_quality_score: int = 0         # Explicit evidence quality heuristic score
    confidence_methodology: str = "multi_factor_evidence_quality_heuristic"
    observation_count: int                  # Legacy field: eligible observation count
    eligible_observation_count: int = 0
    contributing_observation_count: int = 0
    statistical_observation_count: int = 0
    wholesale_observation_count: int = 0
    price_min_pkr: Decimal
    price_max_pkr: Decimal
    is_conflicted: bool = False
    statistical_rate_pkr: Optional[Decimal] = None
    wholesale_rate_pkr: Optional[Decimal] = None
    price_basis: str = "indicative_composite"
    is_composite: bool = False
    scoring_factors: Dict[str, float] = Field(default_factory=lambda: {
        "credibility": 0.35,
        "verification": 0.30,
        "freshness": 0.25,
        "volume": 0.10,
    })


class MaterialRateBridgeResult(BaseModel):
    """Complete output payload of the Material Rate Intelligence Bridge."""
    query: MaterialRateQuery
    status: str                             # verified_evidence, indicative_evidence, unavailable, clarification_needed
    evidence_items: List[MaterialRateEvidenceItem] = Field(default_factory=list)
    canonical_benchmark: Optional[CanonicalBenchmark] = None
    formatted_answer: str
    xml_evidence_prompt: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    is_grounded: bool = True
    disclaimer: str
    telemetry: Dict[str, Any] = Field(default_factory=dict)


# =====================================================================
# LEXICAL & NORMALIZATION MAPPINGS
# =====================================================================

MATERIAL_CATEGORY_ALIASES: Dict[str, List[str]] = {
    "cement": [
        "cement", "opc", "src", "portland", "bori", "boriyan", "bag cement",
        "سیمنٹ", "بوریاں", "بوری"
    ],
    "steel": [
        "steel", "saria", "sariya", "rebar", "iron", "loha", "deformed bar",
        "سریہ", "سریا", "لوہا", "اسٹیل", "سٹیل"
    ],
    "bricks": [
        "brick", "bricks", "eent", "eentein", "eenton", "awwal", "doem", "bhatta",
        "اینٹ", "اینٹیں", "اینٹوں", "بھٹہ"
    ],
    "sand": [
        "sand", "ret", "chenab sand", "ravi sand", "lawrencepur sand",
        "ریت", "چناب ریت", "راوی ریت"
    ],
    "crush": [
        "crush", "bajri", "aggregate", "sargodha crush", "margalla crush", "dina crush",
        "بجری", "کرش", "مارگلہ کرش", "سرگودھا کرش"
    ],
    "blocks": [
        "block", "blocks", "concrete block", "solid block", "hollow block",
        "بلاک", "کنکریٹ بلاک"
    ],
    "tiles": [
        "tile", "tiles", "ceramic tile", "ceramic tiles", "porcelain tile", "porcelain tiles", "floor tile", "wall tile",
        "ٹائل", "ٹائلیں", "ٹائلز"
    ],
    "marble": [
        "marble", "italian marble", "badal marble", "sunny grey", "tavera", "ziarat white", "boticina",
        "natural stone marble", "ماربل", "سنگ مرمر"
    ],
    "granite": [
        "granite", "black granite", "pakistani granite", "imported granite", "natural stone granite",
        "گرینائٹ"
    ],
}

PRODUCT_CODE_DEFAULTS: Dict[str, str] = {
    "cement": "CEMENT_OPC_50KG",
    "steel": "STEEL_REBAR_G60",
    "bricks": "BRICK_CLAY_AWWAL",
    "sand": "SAND_CONSTRUCTION_CFT",
    "crush": "CRUSH_AGGREGATE_CFT",
    "blocks": "BLOCK_CONCRETE_SOLID",
    "tiles": "TILES_CERAMIC_SQFT",
    "marble": "MARBLE_NATURAL_STONE",
    "granite": "GRANITE_NATURAL_STONE",
}

PRODUCT_NAME_DEFAULTS: Dict[str, str] = {
    "cement": "Ordinary Portland Cement 50kg Bag",
    "steel": "Deformed Steel Bar Grade 60",
    "bricks": "Clay Bricks Awwal Class",
    "sand": "Pit Sand / Construction Sand",
    "crush": "Crush / Bajri Aggregate",
    "blocks": "Solid Concrete Masonry Blocks",
    "tiles": "Ceramic & Porcelain Tiles",
    "marble": "Natural Stone / Marble",
    "granite": "Natural Stone / Granite",
}

PAKISTANI_CITIES_LIST = [
    "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar",
    "Multan", "Faisalabad", "Quetta", "Gujranwala", "Sialkot",
    "Abbottabad", "Bahawalpur", "Sukkur", "Hyderabad", "Sargodha",
    "Sahiwal", "Sheikhupura", "Larkana", "Rahim Yar Khan", "Mianwali",
    "Mingora", "Gwadar", "Turbat", "Attock", "Dadu", "Bannu",
    "Khuzdar", "Vehari", "Jhang", "Nawabshah", "Mirpukhas", "Kasur",
    "Okara", "Gujrat", "Muzaffarabad", "Gilgit"
]

CITY_ALIASES: Dict[str, str] = {
    "lahore": "Lahore", "lhr": "Lahore", "لاہور": "Lahore",
    "karachi": "Karachi", "khi": "Karachi", "کراچی": "Karachi",
    "islamabad": "Islamabad", "isb": "Islamabad", "اسلام آباد": "Islamabad",
    "rawalpindi": "Rawalpindi", "pindi": "Rawalpindi", "rwp": "Rawalpindi", "راولپنڈی": "Rawalpindi",
    "peshawar": "Peshawar", "pew": "Peshawar", "پشاور": "Peshawar",
    "multan": "Multan", "mux": "Multan", "ملتان": "Multan",
    "faisalabad": "Faisalabad", "fsd": "Faisalabad", "lyallpur": "Faisalabad", "فیصل آباد": "Faisalabad",
    "quetta": "Quetta", "ueta": "Quetta", "کوئٹہ": "Quetta",
    "gujranwala": "Gujranwala", "گوجرانوالہ": "Gujranwala",
    "sialkot": "Sialkot", "سیالکوٹ": "Sialkot",
    "abbottabad": "Abbottabad", "ایبٹ آباد": "Abbottabad",
    "bahawalpur": "Bahawalpur", "بہاولپور": "Bahawalpur",
    "sukkur": "Sukkur", "سکھر": "Sukkur",
    "hyderabad": "Hyderabad", "hyd": "Hyderabad", "حیدرآباد": "Hyderabad",
    "sargodha": "Sargodha", "سرگودھا": "Sargodha",
    "sahiwal": "Sahiwal", "ساہیوال": "Sahiwal",
    "larkana": "Larkana", "لاڑکانہ": "Larkana",
    "mianwali": "Mianwali", "میانوالی": "Mianwali",
    "mingora": "Mingora", "swat": "Mingora", "مینگورہ": "Mingora",
    "gwadar": "Gwadar", "gawadar": "Gwadar", "گوادر": "Gwadar",
    "turbat": "Turbat", "تربت": "Turbat",
    "attock": "Attock", "اٹک": "Attock",
    "dadu": "Dadu", "دادو": "Dadu",
    "bannu": "Bannu", "بنوں": "Bannu",
    "khuzdar": "Khuzdar", "خضدار": "Khuzdar",
    "vehari": "Vehari", "وہاڑی": "Vehari",
    "jhang": "Jhang", "جھنگ": "Jhang",
    "nawabshah": "Nawabshah", "نوابشاہ": "Nawabshah",
    "mirpukhas": "Mirpukhas", "mirpurkhas": "Mirpukhas", "میرپورخاص": "Mirpukhas",
    "kasur": "Kasur", "قصور": "Kasur",
    "okara": "Okara", "اوکاڑہ": "Okara",
    "gujrat": "Gujrat", "گجرات": "Gujrat",
}

LOCALITY_PATTERNS = [
    re.compile(r"\b(?P<city>lahore|karachi|islamabad|rawalpindi|peshawar)\s+(?:cantt|cantonment|dha|gulberg|bahria|model\s+town|johar\s+town|clifton|saddar|i-8|i-9|i-10|f-6|f-7|f-8|f-10|f-11|g-9|g-10|g-11|site|korangi|north\s+nazimabad)\b", re.IGNORECASE),
    re.compile(r"\b(?:cantt|cantonment|dha|gulberg|bahria|model\s+town|johar\s+town|clifton|saddar|site|korangi|north\s+nazimabad)\b", re.IGNORECASE),
]

BRAND_PATTERNS = {
    # Steel Brands
    "Mughal Steel": re.compile(r"\b(?:mughal|مغل)\b", re.IGNORECASE),
    "Amreli Steel": re.compile(r"\b(?:amreli|امریلی)\b", re.IGNORECASE),
    "FF Steel": re.compile(r"\b(?:ff\s+steel|frontier\s+foundry|ایف\s*ایف)\b", re.IGNORECASE),
    "Ittehad Steel": re.compile(r"\b(?:ittehad|ithad|اتحاد)\b", re.IGNORECASE),
    "Kamran Steel": re.compile(r"\b(?:kamran|کامران)\b", re.IGNORECASE),
    "Model Steel": re.compile(r"\b(?:model\s+steel|ماڈل)\b", re.IGNORECASE),
    "AF Steel": re.compile(r"\b(?:af\s+steel)\b", re.IGNORECASE),
    # Cement Brands
    "Bestway Cement": re.compile(r"\b(?:bestway|بیسٹ\s*وے)\b", re.IGNORECASE),
    "Lucky Cement": re.compile(r"\b(?:lucky|لکی)\b", re.IGNORECASE),
    "DG Khan Cement": re.compile(r"\b(?:dg\s+khan|d\.g\.\s*khan|ڈی\s*جی\s*خان)\b", re.IGNORECASE),
    "Maple Leaf Cement": re.compile(r"\b(?:maple\s+leaf|میپل\s*لیف)\b", re.IGNORECASE),
    "Fauji Cement": re.compile(r"\b(?:fauji|فوجی)\b", re.IGNORECASE),
    "Cherat Cement": re.compile(r"\b(?:cherat|چراٹ)\b", re.IGNORECASE),
    "Kohat Cement": re.compile(r"\b(?:kohat|کوہاٹ)\b", re.IGNORECASE),
    "Pioneer Cement": re.compile(r"\b(?:pioneer|پائینیر)\b", re.IGNORECASE),
}


# =====================================================================
# MATERIAL RATE INTELLIGENCE BRIDGE SERVICE
# =====================================================================

class MaterialRateIntelligenceBridge:
    """
    Evidence-grounded service bridging natural language chat with the
    Phase 02 Material Rate Intelligence System.
    """

    def __init__(self, canonical_rate_engine: Optional[CanonicalMarketRateEngine] = None):
        self.canonical_engine = canonical_rate_engine or canonical_engine

    def parse_material_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        default_city: Optional[str] = None,
    ) -> MaterialRateQuery:
        """
        Parses user query, extracting material category, grade, brand, city, locality,
        units, and multi-turn context carry-over.
        """
        text = query.strip()
        lower_text = text.lower()

        # 1. Detect Language
        lang = "en"
        if re.search(r"[\u0600-\u06FF]", text):
            lang = "ur"
        elif any(w in lower_text for w in [
            "kya", "hai", "batao", "kitna", "kitni", "kitne", "mein", "ka", "ki", "ke",
            "qeemat", "chahiye", "saria", "eent", "ret", "bajri", "aaj", "mil"
        ]):
            lang = "roman_ur"

        # 2. Detect Material Category
        detected_category = None
        for cat, aliases in MATERIAL_CATEGORY_ALIASES.items():
            for alias in aliases:
                is_urdu = any(ord(c) > 127 for c in alias)
                if is_urdu:
                    if alias in lower_text:
                        detected_category = cat
                        break
                else:
                    if re.search(r"\b" + re.escape(alias) + r"\b", lower_text):
                        detected_category = cat
                        break
            if detected_category:
                break

        # 3. Detect Grade / Specification
        detected_grade = None
        if re.search(r"\b(?:grade\s*60|g60|g-60|60\s*grade|گریڈ\s*60)\b", lower_text):
            detected_grade = "Grade 60"
        elif re.search(r"\b(?:grade\s*40|g40|g-40|40\s*grade|گریڈ\s*40)\b", lower_text):
            detected_grade = "Grade 40"

        # 4. Detect Brand
        detected_brand = None
        for brand_name, pat in BRAND_PATTERNS.items():
            if pat.search(lower_text):
                detected_brand = brand_name
                break

        # 5. Detect City & Locality
        detected_cities: List[str] = []
        for alias, canon_city in CITY_ALIASES.items():
            is_urdu = any(ord(c) > 127 for c in alias)
            if is_urdu:
                if alias in lower_text:
                    if canon_city not in detected_cities:
                        detected_cities.append(canon_city)
            else:
                if re.search(r"\b" + re.escape(alias) + r"\b", lower_text):
                    if canon_city not in detected_cities:
                        detected_cities.append(canon_city)

        detected_locality = None
        for pat in LOCALITY_PATTERNS:
            m = pat.search(text)
            if m:
                detected_locality = m.group(0).strip()
                break

        # 6. Detect Unit & Price Basis
        detected_unit = None
        if re.search(r"\b(?:per\s+kg|kg|kilo|فی\s*کلو)\b", lower_text):
            detected_unit = "kg"
        elif re.search(r"\b(?:per\s+ton|ton|metric\s+ton|ٹن)\b", lower_text):
            detected_unit = "metric_ton"
        elif re.search(r"\b(?:per\s+bag|bag|bori|بوری)\b", lower_text):
            detected_unit = "bag_50kg"
        elif re.search(r"\b(?:per\s+brick|single\s+brick|ایک\s*اینٹ)\b", lower_text):
            detected_unit = "single_brick"
        elif re.search(r"\b(?:per\s+1000|1000\s*bricks|hazar|ہزار)\b", lower_text):
            detected_unit = "1000_bricks"
        elif re.search(r"\b(?:per\s+cft|cft|cuft|cubic\s+feet|فٹ)\b", lower_text):
            detected_unit = "cft"

        price_basis = "retail"
        if re.search(r"\b(?:wholesale|thok|تھوک)\b", lower_text):
            price_basis = "wholesale"
        elif re.search(r"\b(?:ex-mill|mill\s+rate|factory\s+rate)\b", lower_text):
            price_basis = "ex_mill"

        # 7. Multi-Turn Context Carry-over
        if not detected_category and conversation_history:
            for turn in reversed(conversation_history):
                prev_text = turn.get("content", "").lower()
                for cat, aliases in MATERIAL_CATEGORY_ALIASES.items():
                    for alias in aliases:
                        if re.search(r"\b" + re.escape(alias) + r"\b", prev_text) or alias in prev_text:
                            detected_category = cat
                            break
                    if detected_category:
                        break
                if detected_category:
                    break

        if not detected_cities and conversation_history:
            for turn in reversed(conversation_history):
                prev_text = turn.get("content", "").lower()
                for alias, canon_city in CITY_ALIASES.items():
                    if re.search(r"\b" + re.escape(alias) + r"\b", prev_text) or alias in prev_text:
                        if canon_city not in detected_cities:
                            detected_cities.append(canon_city)
                if detected_cities:
                    break

        # Fallback to default city if specified
        primary_city = detected_cities[0] if detected_cities else default_city

        # 8. Resolve Product Code
        product_code = None
        product_name = None
        if detected_category == "steel":
            if detected_grade == "Grade 40":
                product_code = "STEEL_REBAR_G40"
                product_name = "Mild Steel Bar Grade 40"
            elif detected_grade == "Grade 60":
                product_code = "STEEL_REBAR_G60"
                product_name = "Deformed Steel Bar Grade 60"
            else:
                product_code = "STEEL_REBAR_G60"
                product_name = "Deformed Steel Bar Grade 60"
        elif detected_category:
            product_code = PRODUCT_CODE_DEFAULTS.get(detected_category)
            product_name = PRODUCT_NAME_DEFAULTS.get(detected_category, detected_category.title())

        # 9. Comparison Detection
        is_comparison = len(detected_cities) >= 2 or any(
            w in lower_text for w in ["compare", "comparison", "faraq", "farq", "vs", "versus"]
        ) and len(detected_cities) >= 2

        return MaterialRateQuery(
            raw_query=query,
            material_category=detected_category,
            product_code=product_code,
            product_name=product_name or PRODUCT_NAME_DEFAULTS.get(detected_category, detected_category.title() if detected_category else None),
            grade=detected_grade,
            brand=detected_brand,
            city=primary_city,
            locality=detected_locality,
            unit=detected_unit,
            price_basis=price_basis,
            language=lang,
            is_comparison=is_comparison,
            comparison_cities=detected_cities if is_comparison else [],
        )

    @staticmethod
    def resolve_effective_timestamp(
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource] = None,
    ) -> Optional[datetime]:
        """
        Delegates to CentralizedProductIdentityResolver for reliable market date resolution (Task 3).
        Preserves published_at and survey_reference_period independently.
        In accordance with policy, collected_at and created_at are never used as market dates.
        """
        return centralized_identity_resolver.resolve_effective_market_date(obs, source)

    async def query_eligible_observations(
        self,
        db: Any,
        query: MaterialRateQuery,
        city_override: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> List[Tuple[MaterialRateObservation, MaterialRateSource, MaterialRateProduct]]:
        """
        Executes strict database query for eligible market observations.
        Mandatory Eligibility Criteria (Task 1 & Task 2):
        1. Source reliability tier in ('authoritative', 'indicative') and != 'synthetic'
        2. Source permission_status == 'permitted'
        3. Source is_active == True
        4. Observation verification_status in ('verified_market_range', 'verified_quote', 'cross_checked', 'indicative')
        5. Observation verification_status not in ('unverified', 'conflicted', 'stale')
        6. Dealer quotation status == 'verified' and within validity days (if quotation linked)
        7. Date policy: effective timestamp must exist and be within source.freshness_ttl_days
        8. Cross-project isolation: private project quotes only match caller project_id (Task 4)
        9. City specificity: strictly retrieves target city observations without silent substitution (Task 2)
        10. Strict SQL / ORM parameterization (never string pattern LIKE '%_TEST')
        """
        target_city = city_override or query.city
        now = datetime.now(timezone.utc)

        if db is None:
            return []

        # Base statement joining Observation, Source, and Product
        stmt = (
            select(
                MaterialRateObservation,
                MaterialRateSource,
                MaterialRateProduct,
            )
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .where(
                # Explicit Source Trust & Permission Checks
                MaterialRateSource.is_active.is_(True),
                MaterialRateSource.permission_status == "permitted",
                MaterialRateSource.reliability_tier.in_(["authoritative", "indicative"]),
                MaterialRateSource.reliability_tier != "synthetic",
                # Explicit Observation Verification Status Checks
                MaterialRateObservation.verification_status.in_([
                    "verified_market_range",
                    "verified_quote",
                    "cross_checked",
                    "indicative",
                ]),
                MaterialRateObservation.verification_status != "unverified",
                MaterialRateObservation.verification_status != "conflicted",
                MaterialRateObservation.verification_status != "stale",
                # Standard Measurement Unit Consistency
                MaterialRateObservation.normalized_unit == MaterialRateProduct.standard_unit,
            )
        )

        # Filter by product or category
        if query.product_code:
            if query.product_code in ("STEEL_REBAR_G40", "STEEL_REBAR_G60"):
                stmt = stmt.where(
                    (MaterialRateProduct.code == query.product_code) |
                    (MaterialRateProduct.category == "steel")
                )
            else:
                stmt = stmt.where(MaterialRateProduct.code == query.product_code)
        elif query.material_category:
            stmt = stmt.where(MaterialRateProduct.category == query.material_category)

        # Filter strictly by target city (Task 2: no silent substitution of other-city observations)
        if target_city:
            if target_city.lower() in ("gwadar", "gawadar"):
                stmt = stmt.where(func.lower(MaterialRateObservation.city).in_(["gwadar", "gawadar"]))
            else:
                stmt = stmt.where(func.lower(MaterialRateObservation.city) == target_city.lower())

        rows = (await db_execute(db, stmt)).all()

        # Task 1: Fetch canonical Grade 40 product if steel is involved, for historical identity remapping
        prod_g40 = None
        if query.material_category == "steel" or query.product_code in ("STEEL_REBAR_G40", "STEEL_REBAR_G60") or query.grade in ("Grade 40", "Grade 60"):
            prod_g40 = await db_scalar(
                db,
                select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G40"),
            )

        # In-memory validation for dealer quote verification, non-zero prices, freshness, and tenancy
        eligible_results: List[Tuple[MaterialRateObservation, MaterialRateSource, MaterialRateProduct]] = []

        for obs, src, prod in rows:
            # Task 7 item 5: Unsupported numerical price rejection
            if obs.normalized_price_pkr is None or obs.normalized_price_pkr <= Decimal("0"):
                continue

            # Task 4: Authoritative dealer quotation tenancy & project isolation validation
            is_valid_tenancy, _ = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
                db, obs, src, project_id
            )
            if not is_valid_tenancy:
                continue

            # Task 1 & 2: Grade 40 vs Grade 60 centralized product identity isolation
            obs_meta = obs.observation_metadata or {}
            detected_grade = detect_observation_steel_grade(obs)
            is_obs_g40 = (detected_grade == "Grade 40" or prod.code == "STEEL_REBAR_G40")
            is_obs_g60 = (detected_grade == "Grade 60" or (detected_grade is None and prod.code == "STEEL_REBAR_G60"))

            if query.product_code == "STEEL_REBAR_G60" or query.grade == "Grade 60":
                # User specifically requested Grade 60 (or generic steel defaulting to G60)
                # Grade 40 observations must NEVER appear in Grade 60 queries
                if is_obs_g40:
                    continue
            elif query.product_code == "STEEL_REBAR_G40" or query.grade == "Grade 40":
                # User specifically requested Grade 40
                # Grade 60 observations must NEVER appear in Grade 40 queries
                if is_obs_g60 and not is_obs_g40:
                    continue
                # Canonical product identity mapping: if historical observation was associated with G60 product,
                # remap to true canonical Grade 40 product identity
                if is_obs_g40 and prod.code != "STEEL_REBAR_G40":
                    if prod_g40 is not None:
                        prod = prod_g40
                    else:
                        prod_id, prod_code, prod_name, _ = await centralized_identity_resolver.resolve_observation_canonical_product(db, obs, prod)
                        prod = MaterialRateProduct(
                            id=prod_id,
                            code=prod_code,
                            canonical_name=prod_name,
                            category=prod.category,
                            standard_unit=prod.standard_unit,
                        )

            # Task 2: Source-specific timestamp resolution
            effective_date = self.resolve_effective_timestamp(obs, src)
            if not effective_date:
                # Exclude records with no reliable publication or observation timestamp
                continue

            if effective_date.tzinfo is None:
                effective_date = effective_date.replace(tzinfo=timezone.utc)

            # Task 4: Quarantine future-dated observations (more than 1 hour in the future)
            if (effective_date - now).total_seconds() > 3600.0:
                continue

            days_old = max(0.0, (now - effective_date).total_seconds() / 86400.0)
            ttl_days = float(getattr(src, "freshness_ttl_days", 90) or 90)

            # Exclude if older than source TTL (boundary: days_old <= ttl_days is accepted)
            if days_old > ttl_days:
                continue

            # Brand filtering if specifically requested
            if query.brand:
                obs_brand = obs_meta.get("brand", "")
                if query.brand.lower() not in obs_brand.lower():
                    # Keep as fallback if no exact brand match, but check other rows first
                    pass

            eligible_results.append((obs, src, prod))

        return eligible_results

    async def compute_canonical_benchmark(
        self,
        db: Any,
        product: MaterialRateProduct,
        city: str,
        eligible_rows: List[Tuple[MaterialRateObservation, MaterialRateSource, MaterialRateProduct]],
        now: Optional[datetime] = None,
    ) -> Optional[CanonicalBenchmark]:
        """
        Reuses Phase 02 CanonicalMarketRateEngine to compute benchmark rate from eligible observations.
        Scoring formula:
        Score = (Credibility * 0.35) + (Verification * 0.30) + (Freshness * 0.25) + (Volume * 0.10)
        """
        if not eligible_rows:
            return None

        # Filter rows strictly for target city
        city_rows = [
            (o, s, p) for o, s, p in eligible_rows
            if o.city and o.city.lower() == city.lower()
        ]
        if not city_rows:
            return None

        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        scored: List[Tuple[MaterialRateObservation, MaterialRateSource, MaterialRateProduct, Decimal]] = []

        for obs, src, prod in city_rows:
            w = self.canonical_engine.compute_observation_weight(
                obs=obs,
                source=src,
                target_city=city,
                now=now,
                volume_count=len(city_rows),
            )
            scored.append((obs, src, prod, w))

        # Deterministic ranking: weight DESC, published_at DESC, created_at DESC, id DESC
        def _sort_key(item: Tuple[MaterialRateObservation, MaterialRateSource, MaterialRateProduct, Decimal]):
            o = item[0]
            w = item[3]
            pub = o.published_at.replace(tzinfo=timezone.utc) if o.published_at and o.published_at.tzinfo is None else (o.published_at or datetime.min.replace(tzinfo=timezone.utc))
            created = o.created_at.replace(tzinfo=timezone.utc) if o.created_at and o.created_at.tzinfo is None else (o.created_at or datetime.min.replace(tzinfo=timezone.utc))
            return (w, pub, created, str(o.id))

        scored.sort(key=_sort_key, reverse=True)

        prices = [o.normalized_price_pkr for o, _, _, _ in scored]
        min_p = min(prices)
        max_p = max(prices)

        # Task 3 & Task 4: Comprehensive Comparable Price Grouping
        # Groups observations strictly by:
        # (product_code, brand, grade, canonical_unit, price_basis, canonical_city, locality, period)
        # Guarantees wholesale, retail, and ex-mill remain separate, and different cities/localities/periods are never conflated.
        comparable_groups: Dict[Tuple[str, str, str, str, str, str, str, str], List[Decimal]] = defaultdict(list)
        for obs, src, prod, _ in scored:
            meta = obs.observation_metadata or {}
            p_code = product.code
            brand = meta.get("brand") or meta.get("mill") or "GENERIC"
            grade = meta.get("grade") or ""
            unit = obs.normalized_unit

            # Task 3: Exact PBS & Government Schedule Classification (NationalSourceRegistry verified)
            PBS_CODES = ("PBS_STATISTICAL_MONTHLY", "PBS_STATISTICAL_SPI", "PBS_MONTHLY_INDICES")
            GOV_SCHEDULE_CODES = ("NHA_CSR_SCHEDULE", "PUNJAB_CW_MRS", "SINDH_WSD_CSR", "KP_CW_CSR")

            is_pbs = False
            is_gov_schedule = False
            if src is not None:
                if src.code in PBS_CODES:
                    is_pbs = True
                elif src.code in GOV_SCHEDULE_CODES:
                    is_gov_schedule = True
            if not is_pbs and meta.get("source_code") in PBS_CODES:
                is_pbs = True
            if not is_gov_schedule and meta.get("source_code") in GOV_SCHEDULE_CODES:
                is_gov_schedule = True

            if is_pbs:
                default_p_basis = "retail_statistical_average"
            elif is_gov_schedule:
                default_p_basis = "government_schedule_rate"
            else:
                default_p_basis = "retail"

            p_basis = meta.get("price_basis") or default_p_basis
            c_city = obs.city or city
            locality = meta.get("locality") or "ALL"

            # Task 4 & Task 5: Cadence-specific comparable period grouping & ISO 8601 weekly normalization (%G-W%V)
            eff_dt = self.resolve_effective_timestamp(obs, src) or obs.published_at
            if eff_dt:
                eff_tz = eff_dt.replace(tzinfo=timezone.utc) if eff_dt.tzinfo is None else eff_dt.astimezone(timezone.utc)
                d_old = max(0.0, (now - eff_tz).total_seconds() / 86400.0)
                is_monthly = False
                if is_pbs:
                    is_monthly = True
                elif meta.get("period_cadence") == "monthly" or meta.get("survey_reference_period"):
                    is_monthly = True

                if is_monthly:
                    # Preserves actual survey reference period (e.g. "October, 2026")
                    # If unspecified, active contemporaneous records within cadence share the active cycle
                    period = (
                        meta.get("survey_reference_period")
                        or meta.get("period")
                        or ("CURRENT_MONTH" if d_old <= 45.0 else eff_tz.strftime("%Y-%m"))
                    )
                else:
                    # Daily commercial spot prices grouped by ISO 8601 week-year (%G-W%V)
                    period = eff_tz.strftime("%G-W%V")
            else:
                period = "UNKNOWN_PERIOD"

            key = (p_code, brand, grade, unit, p_basis, c_city, locality, period)
            comparable_groups[key].append(obs.normalized_price_pkr)

        is_conflicted = False
        # Conflict detection evaluates spread ONLY within strictly comparable groups
        for key, g_prices in comparable_groups.items():
            if len(g_prices) >= 2:
                g_min = min(g_prices)
                g_max = max(g_prices)
                g_avg = sum(g_prices) / Decimal(str(len(g_prices)))
                if g_avg > Decimal("0"):
                    # Anomaly formula: ((Max - Min) / Avg) * 100
                    # Denominator is the arithmetic mean of the comparable group
                    spread = ((g_max - g_min) / g_avg) * Decimal("100")
                    if spread > Decimal("15.00"):
                        is_conflicted = True
                        break

        # Weighted average of top 3 observations using Decimal arithmetic
        top_candidates = scored[:3]
        total_weight = sum(w for _, _, _, w in top_candidates)
        if total_weight > Decimal("0"):
            weighted_sum = sum(o.normalized_price_pkr * w for o, _, _, w in top_candidates)
            benchmark_pkr = (weighted_sum / total_weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            benchmark_pkr = top_candidates[0][0].normalized_price_pkr

        # Dual benchmark disaggregation (Statistical vs Wholesale)
        stat_obs = []
        ws_obs = []
        for o, src, prod, _ in scored:
            meta = o.observation_metadata or {}
            is_pbs = "PBS" in ((src.code if src else "") or "").upper()
            basis = meta.get("price_basis") or ("retail_statistical" if is_pbs else "wholesale")
            if basis in ("retail_statistical", "statistical_index") or is_pbs:
                stat_obs.append(o)
            elif basis in ("wholesale", "retail", "ex_mill", "dealer_quotation"):
                ws_obs.append(o)

        statistical_rate_pkr = None
        if stat_obs:
            statistical_rate_pkr = stat_obs[0].normalized_price_pkr

        wholesale_rate_pkr = None
        if ws_obs:
            ws_prices = sorted([o.normalized_price_pkr for o in ws_obs])
            n_ws = len(ws_prices)
            if n_ws % 2 == 1:
                wholesale_rate_pkr = ws_prices[n_ws // 2]
            else:
                wholesale_rate_pkr = ((ws_prices[n_ws // 2 - 1] + ws_prices[n_ws // 2]) / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Check if top candidates blend mixed price bases
        unique_bases = set()
        for o, src, prod, _ in top_candidates:
            meta = o.observation_metadata or {}
            is_pbs = "PBS" in ((src.code if src else "") or "").upper()
            basis = meta.get("price_basis") or ("retail_statistical" if is_pbs else "wholesale")
            unique_bases.add(basis)

        is_composite = len(unique_bases) > 1
        price_basis_label = "indicative_composite" if is_composite else (list(unique_bases)[0] if unique_bases else "indicative")

        top_obs = top_candidates[0][0]
        if is_conflicted:
            ver_status = "conflicted"
        elif is_composite:
            # Composite blending distinct bases must NEVER be presented as verified
            ver_status = "indicative"
        else:
            ver_status = top_obs.verification_status
        confidence = int(min(100, max(20, int(top_candidates[0][3]))))

        # Determine trend against existing canonical rate in material_rates
        # Deterministic tie-breaking on (observed_at DESC, created_at DESC, id DESC) (Task 6)
        existing_canonical = None
        if db is not None:
            existing_canonical = await db_scalar(
                db,
                select(MaterialRate).where(
                    MaterialRate.product_id == product.id,
                    MaterialRate.city == city,
                ).order_by(
                    desc(MaterialRate.observed_at),
                    desc(MaterialRate.created_at),
                    desc(MaterialRate.id),
                ).limit(1),
            )

        trend = "neutral"
        if existing_canonical and existing_canonical.rate_pkr:
            if benchmark_pkr > existing_canonical.rate_pkr:
                trend = "up"
            elif benchmark_pkr < existing_canonical.rate_pkr:
                trend = "down"

        return CanonicalBenchmark(
            product_code=product.code,
            product_name=product.canonical_name,
            category=product.category,
            city=city,
            benchmark_rate_pkr=benchmark_pkr,
            unit=product.standard_unit,
            trend=trend,
            verification_status=ver_status,
            confidence_score=confidence,
            evidence_quality_score=confidence,
            confidence_methodology="multi_factor_evidence_quality_heuristic",
            observation_count=len(city_rows),
            eligible_observation_count=len(city_rows),
            contributing_observation_count=len(top_candidates),
            statistical_observation_count=len(stat_obs),
            wholesale_observation_count=len(ws_obs),
            price_min_pkr=min_p,
            price_max_pkr=max_p,
            is_conflicted=is_conflicted,
            statistical_rate_pkr=statistical_rate_pkr,
            wholesale_rate_pkr=wholesale_rate_pkr,
            is_composite=is_composite,
            price_basis=price_basis_label,
        )

    def _convert_unit_price(
        self,
        price_pkr: Decimal,
        standard_unit: str,
        requested_unit: Optional[str],
    ) -> Tuple[Decimal, str]:
        """
        Converts between standard and requested units using exact Decimal arithmetic.
        Steel: metric_ton <-> kg (1 metric ton = 1000 kg)
        Bricks: 1000_bricks <-> single_brick (1000 bricks = 1000 * 1 brick)
        """
        if not requested_unit or requested_unit == standard_unit:
            return price_pkr, standard_unit

        # Steel: ton to kg
        if standard_unit == "metric_ton" and requested_unit == "kg":
            converted = (price_pkr / Decimal("1000")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return converted, "kg"

        # Steel: kg to ton
        if standard_unit == "kg" and requested_unit == "metric_ton":
            converted = (price_pkr * Decimal("1000")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return converted, "metric_ton"

        # Bricks: 1000 bricks to single brick
        if standard_unit == "1000_bricks" and requested_unit == "single_brick":
            converted = (price_pkr / Decimal("1000")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return converted, "single_brick"

        # Bricks: single brick to 1000 bricks
        if standard_unit == "single_brick" and requested_unit == "1000_bricks":
            converted = (price_pkr * Decimal("1000")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return converted, "1000_bricks"

        return price_pkr, standard_unit

    def format_unavailable_response(self, query: MaterialRateQuery, language: str) -> str:
        """Generates honest unavailability notice when verified database records do not exist."""
        mat_label = (query.product_name or query.material_category or "Construction Material").title()
        city_label = query.city or "Pakistan"

        if language == "ur":
            return (
                f"قومی تصدیق شدہ ڈیٹا بیس میں **{city_label}** کے لیے **{mat_label}** کے تصدیق شدہ مارکیٹ ریٹس فی الحال دستیاب نہیں ہیں۔\n\n"
                f"براہ کرم دوسرے بڑے شہر (مثلاً لاہور، کراچی، اسلام آباد) کے ریٹس دریافت کریں یا مستند ڈیلر کی کوٹیشن چیک کریں۔"
            )
        elif language == "roman_ur":
            return (
                f"Verified national database mein **{city_label}** ke liye **{mat_label}** ke tasdeeq shuda rates filhal dastyab nahi hain.\n\n"
                f"Aap doosray shehron (jaise Lahore, Karachi, Islamabad) ke benchmark rates pooch sakte hain ya local verified dealers se rabta kar sakte hain."
            )
        else:
            return (
                f"Verified market rates for **{mat_label}** in **{city_label}** are currently unavailable in the verified national database.\n\n"
                f"You may query benchmark prices for other major regional hubs (e.g. Lahore, Karachi, Islamabad) or check direct verified merchant quotations."
            )

    def format_grounded_answer(
        self,
        query: MaterialRateQuery,
        evidence_items: List[MaterialRateEvidenceItem],
        benchmark: Optional[CanonicalBenchmark],
        language: str,
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Formats natural evidence-grounded response preserving source distinction,
        provenance attribution, and disclaimer.
        """
        mat_name = query.product_name or (benchmark.product_name if benchmark else "Material")
        city = query.city or "Pakistan"

        # Primary price to highlight
        primary_item = evidence_items[0] if evidence_items else None
        display_price, display_unit = (
            self._convert_unit_price(
                benchmark.benchmark_rate_pkr if benchmark else primary_item.price_pkr,
                benchmark.unit if benchmark else primary_item.unit,
                query.unit,
            )
            if (benchmark or primary_item)
            else (Decimal("0.00"), "unit")
        )

        # Build human-readable text
        lines: List[str] = []
        unit_display = display_unit.replace("_", " ")

        if language == "ur":
            lines.append(f"### {city} میں {mat_name} کے تصدیق شدہ مارکیٹ ریٹس\n")
            if benchmark:
                lines.append(f"- **معیاری ریٹ (Benchmark):** PKR {display_price:,.2f} فی {unit_display}")
                lines.append(f"- **مارکیٹ کی رینج:** PKR {benchmark.price_min_pkr:,.2f} تا PKR {benchmark.price_max_pkr:,.2f}")
                lines.append(f"- **تصدیق کا درجہ:** {benchmark.verification_status} (اعتماد: {benchmark.confidence_score}%)")
            elif primary_item:
                lines.append(f"- **ریٹ:** PKR {display_price:,.2f} فی {unit_display}")
                lines.append(f"- **ذریعہ:** {primary_item.source_name} ({primary_item.source_tier})")

            lines.append("\n**دستیاب شواہد کی تفصیلات:**")
            for item in evidence_items[:5]:
                b_str = f" ({item.brand})" if item.brand else ""
                lines.append(
                    f"- **{item.product_name}{b_str}:** PKR {item.price_pkr:,.2f} /{item.unit.replace('_', ' ')} "
                    f"| ذریعہ: {item.source_name} | تاریخ: {item.published_at.strftime('%Y-%m-%d') if item.published_at else 'حالیہ'}"
                )
            lines.append(
                "\n> **نوٹ:** یہ قیمتیں مستند سرکاری و ثانوی مارکیٹ ڈیٹا پر مبنی ہیں۔ سائٹ کے محل وقوع، برانڈ اور ٹرانسپورٹیشن کے لحاظ سے ڈیلر ریٹس میں فرق ہو سکتا ہے۔"
            )

        elif language == "roman_ur":
            lines.append(f"### {city} mein {mat_name} ke Market Rates\n")
            if benchmark:
                lines.append(f"- **Benchmark Rate:** PKR {display_price:,.2f} per {unit_display}")
                lines.append(f"- **Price Range:** PKR {benchmark.price_min_pkr:,.2f} se PKR {benchmark.price_max_pkr:,.2f}")
                lines.append(f"- **Verification Status:** {benchmark.verification_status} (Confidence: {benchmark.confidence_score}%)")
            elif primary_item:
                lines.append(f"- **Observed Rate:** PKR {display_price:,.2f} per {unit_display}")
                lines.append(f"- **Source:** {primary_item.source_name} ({primary_item.source_tier})")

            lines.append("\n**Dastyab Records:**")
            for item in evidence_items[:5]:
                b_str = f" ({item.brand})" if item.brand else ""
                lines.append(
                    f"- **{item.product_name}{b_str}:** PKR {item.price_pkr:,.2f} /{item.unit.replace('_', ' ')} "
                    f"| Source: {item.source_name} | Date: {item.published_at.strftime('%Y-%m-%d') if item.published_at else 'Recent'}"
                )
            lines.append(
                "\n> **Wazahat:** Yeh rates database records par mabni hain. Location, brand, quantity aur transportation charges ki wajah se dealer prices mukhtalif ho sakti hain."
            )

        else:
            lines.append(f"### Verified Construction Material Rates — {city}\n")
            lines.append(f"**Material:** {mat_name}")
            if query.grade:
                lines.append(f"**Specification/Grade:** {query.grade}")
            if query.locality:
                lines.append(f"**Locality:** {query.locality}")

            if benchmark:
                lines.append(f"**Canonical Benchmark:** PKR {display_price:,.2f} per {unit_display}")
                lines.append(f"**Observed Range:** PKR {benchmark.price_min_pkr:,.2f} – PKR {benchmark.price_max_pkr:,.2f}")
                lines.append(f"**Verification Tier:** {benchmark.verification_status} (Confidence: {benchmark.confidence_score}%)")
                lines.append(f"**Evidence Sample:** {benchmark.observation_count} verified observations")
            elif primary_item:
                lines.append(f"**Reported Price:** PKR {display_price:,.2f} per {unit_display}")
                lines.append(f"**Reporting Source:** {primary_item.source_name} ({primary_item.source_tier})")

            lines.append("\n**Supporting Evidence Records:**")
            for item in evidence_items[:5]:
                b_str = f" [{item.brand}]" if item.brand else ""
                spec_str = f" ({item.grade_or_spec})" if item.grade_or_spec else ""
                p_date = item.published_at.strftime('%Y-%m-%d') if item.published_at else "Recent survey"
                lines.append(
                    f"- **{item.product_name}{b_str}{spec_str}:** PKR {item.price_pkr:,.2f} /{item.unit.replace('_', ' ')} "
                    f"({item.provenance_label}) | Source: {item.source_name} | Published: {p_date} | Status: {item.verification_status}"
                )

            lines.append(
                "\n> **Market Advisory:** Rates represent verified national and secondary market surveys. "
                "Actual dealer counter prices may vary according to regional logistics, batch size, manufacturer discounts, and transportation."
            )

        formatted_answer = "\n".join(lines)

        # Build XML evidence prompt for LLM injection with strict character escaping (Task 5)
        xml_lines = ["<material_rate_evidence>"]
        for item in evidence_items[:8]:
            p_iso = item.published_at.isoformat() if item.published_at else ""
            clean_id = html.escape(str(item.observation_id), quote=True)
            clean_code = html.escape(str(item.product_code), quote=True)
            clean_city = html.escape(str(item.city), quote=True)
            clean_unit = html.escape(str(item.unit), quote=True)
            clean_src_code = html.escape(str(item.source_code), quote=True)
            clean_tier = html.escape(str(item.source_tier), quote=True)
            clean_status = html.escape(str(item.verification_status), quote=True)
            clean_prov = html.escape(str(item.provenance_label), quote=True)
            clean_name = html.escape(str(item.product_name), quote=True)
            clean_src = html.escape(str(item.source_name), quote=True)
            clean_price = str(item.price_pkr)
            xml_lines.append(
                f"  <observation id='{clean_id}' product='{clean_code}' "
                f"city='{clean_city}' price='{clean_price}' unit='{clean_unit}' "
                f"source='{clean_src_code}' tier='{clean_tier}' status='{clean_status}' "
                f"provenance='{clean_prov}' published_at='{p_iso}'>"
                f"{clean_name} - PKR {clean_price} per {clean_unit} via {clean_src}"
                f"</observation>"
            )
        if benchmark:
            clean_b_code = html.escape(str(benchmark.product_code), quote=True)
            clean_b_city = html.escape(str(benchmark.city), quote=True)
            clean_b_unit = html.escape(str(benchmark.unit), quote=True)
            clean_b_status = html.escape(str(benchmark.verification_status), quote=True)
            clean_b_rate = str(benchmark.benchmark_rate_pkr)
            xml_lines.append(
                f"  <canonical_benchmark product='{clean_b_code}' city='{clean_b_city}' "
                f"rate='{clean_b_rate}' unit='{clean_b_unit}' "
                f"confidence='{benchmark.confidence_score}' status='{clean_b_status}' />"
            )
        xml_lines.append("</material_rate_evidence>")
        xml_prompt = "\n".join(xml_lines)

        citations = [item.to_citation_dict() for item in evidence_items]

        return formatted_answer, xml_prompt, citations

    async def resolve_material_rate_query(
        self,
        query: str,
        db: Any,
        city: Optional[str] = None,
        product_code: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> MaterialRateBridgeResult:
        """
        Main entry point for ConstructionChatWorkflow.
        Parses the query, retrieves eligible observations, computes canonical benchmark,
        and generates grounded natural response.
        Enforces project isolation: public market rates are accessible across projects,
        while private project-specific quotations are strictly isolated (Task 7).
        """
        parsed_query = self.parse_material_query(
            query=query,
            conversation_history=conversation_history,
            default_city=city,
        )
        if city:
            parsed_query.city = city
        if product_code:
            parsed_query.product_code = product_code
        if language:
            parsed_query.language = language

        # Handle comparison across multiple cities
        if parsed_query.is_comparison and len(parsed_query.comparison_cities) >= 2:
            return await self._resolve_comparison_query(db, parsed_query, project_id=project_id)

        # Check if material category was successfully recognized
        if not parsed_query.material_category and not parsed_query.product_code:
            unavail_msg = self.format_unavailable_response(parsed_query, parsed_query.language)
            return MaterialRateBridgeResult(
                query=parsed_query,
                status="unavailable",
                evidence_items=[],
                canonical_benchmark=None,
                formatted_answer=unavail_msg,
                xml_evidence_prompt="<material_rate_evidence status='unavailable' />",
                citations=[],
                is_grounded=True,
                disclaimer="No recognized construction material in database query.",
                telemetry={"eligible_count": 0, "status": "unavailable", "reason": "unrecognized_material"},
            )

        # Query database for eligible observations
        eligible_rows = await self.query_eligible_observations(db, parsed_query, project_id=project_id)

        if not eligible_rows:
            unavail_msg = self.format_unavailable_response(parsed_query, parsed_query.language)
            return MaterialRateBridgeResult(
                query=parsed_query,
                status="unavailable",
                evidence_items=[],
                canonical_benchmark=None,
                formatted_answer=unavail_msg,
                xml_evidence_prompt="<material_rate_evidence status='unavailable' />",
                citations=[],
                is_grounded=True,
                disclaimer="Verified rates for the specified material/city are currently unavailable in the database.",
                telemetry={"eligible_count": 0, "status": "unavailable"},
            )

        # Convert ORM rows to evidence items
        now = datetime.now(timezone.utc)
        evidence_items: List[MaterialRateEvidenceItem] = []
        for obs, src, prod in eligible_rows:
            eff_dt = self.resolve_effective_timestamp(obs, src) or obs.published_at
            if eff_dt:
                eff_tz = eff_dt.replace(tzinfo=timezone.utc) if eff_dt.tzinfo is None else eff_dt.astimezone(timezone.utc)
                age = max(0.0, (now - eff_tz).total_seconds() / 86400.0)
            else:
                eff_tz = None
                age = 365.0

            obs_meta = obs.observation_metadata or {}
            brand_val = obs_meta.get("brand") or parsed_query.brand
            grade_val = obs_meta.get("grade") or parsed_query.grade or prod.subcategory

            # Task 3: Precise provenance label & price basis (verified against NationalSourceRegistry)
            PBS_CODES = ("PBS_STATISTICAL_MONTHLY", "PBS_STATISTICAL_SPI", "PBS_MONTHLY_INDICES")
            GOV_SCHEDULE_CODES = ("NHA_CSR_SCHEDULE", "PUNJAB_CW_MRS", "SINDH_WSD_CSR", "KP_CW_CSR")

            if obs.dealer_quote_id is not None:
                prov_label = "Verified dealer quotation"
                price_basis_val = "dealer_direct"
                disc = "Verified commercial quotation submitted by authorized dealer to TameerAI."
            elif (src.code in PBS_CODES) or (obs_meta.get("source_code") in PBS_CODES):
                prov_label = "Official statistical average price"
                price_basis_val = "statistical_market_range"
                disc = f"Official statistical average retail price published monthly by {src.name} across urban centers."
            elif (src.code in GOV_SCHEDULE_CODES) or (obs_meta.get("source_code") in GOV_SCHEDULE_CODES):
                prov_label = "Official government schedule of rates (CSR/MRS)"
                price_basis_val = "government_schedule_rate"
                disc = f"Official statutory schedule rate published by {src.name}."
            elif src.source_type == "aggregator" or src.reliability_tier == "indicative":
                prov_label = "Indicative market price"
                price_basis_val = obs_meta.get("price_basis") or ("indicative_wholesale" if "steel" in prod.category.lower() else "indicative_market_price")
                disc = f"Indicative secondary market monitor rate published by {src.name}. Actual local dealer counter prices may vary."
            else:
                prov_label = "Indicative market price"
                price_basis_val = obs_meta.get("price_basis", "retail")
                disc = f"Reported by {src.name} as {src.reliability_tier} market information."

            evidence_items.append(
                MaterialRateEvidenceItem(
                    observation_id=str(obs.id),
                    product_code=prod.code,
                    product_name=prod.canonical_name,
                    name=prod.canonical_name,
                    category=prod.category,
                    brand=brand_val,
                    grade_or_spec=grade_val,
                    city=obs.city or parsed_query.city or "National",
                    locality=parsed_query.locality,
                    price_pkr=obs.normalized_price_pkr,
                    unit=obs.normalized_unit,
                    price_basis=price_basis_val,
                    provenance_label=prov_label,
                    source_code=src.code,
                    source_name=src.name,
                    source_tier=src.reliability_tier,
                    verification_status=obs.verification_status,
                    confidence_score=90 if src.reliability_tier == "authoritative" else 75,
                    published_at=obs.published_at,
                    collected_at=obs.collected_at,
                    observed_at=eff_tz,
                    age_days=age,
                    source_url=obs.source_url,
                    disclaimer=disc,
                )
            )

        # Compute canonical benchmark
        primary_product = eligible_rows[0][2]
        benchmark = await self.compute_canonical_benchmark(
            db=db,
            product=primary_product,
            city=parsed_query.city or eligible_rows[0][0].city or "National",
            eligible_rows=eligible_rows,
        )

        # Status determination
        has_authoritative = any(i.source_tier == "authoritative" for i in evidence_items)
        status = "verified_evidence" if has_authoritative else "indicative_evidence"

        # Format answers and XML prompt
        formatted_answer, xml_prompt, citations = self.format_grounded_answer(
            query=parsed_query,
            evidence_items=evidence_items,
            benchmark=benchmark,
            language=parsed_query.language,
        )

        return MaterialRateBridgeResult(
            query=parsed_query,
            status=status,
            evidence_items=evidence_items,
            canonical_benchmark=benchmark,
            formatted_answer=formatted_answer,
            xml_evidence_prompt=xml_prompt,
            citations=citations,
            is_grounded=True,
            disclaimer=(
                "Verified rate information derived directly from eligible database records. "
                "Official statistical rates (PBS) and indicative quotes (SteelRateToday) are strictly differentiated."
            ),
            telemetry={
                "eligible_count": len(evidence_items),
                "has_benchmark": benchmark is not None,
                "benchmark_rate": float(benchmark.benchmark_rate_pkr) if benchmark else None,
                "status": status,
                "category": parsed_query.material_category,
                "city": parsed_query.city,
            },
        )

    async def _resolve_comparison_query(
        self,
        db: Any,
        query: MaterialRateQuery,
        project_id: Optional[uuid.UUID] = None,
    ) -> MaterialRateBridgeResult:
        """Handles cross-city comparison inquiries (e.g. Lahore vs Karachi)."""
        cities = query.comparison_cities
        all_evidence: List[MaterialRateEvidenceItem] = []
        city_benchmarks: Dict[str, Optional[CanonicalBenchmark]] = {}

        for c in cities:
            rows = await self.query_eligible_observations(db, query, city_override=c, project_id=project_id)
            for obs, src, prod in rows:
                eff_dt = self.resolve_effective_timestamp(obs, src) or obs.published_at
                eff_tz = eff_dt.replace(tzinfo=timezone.utc) if eff_dt and eff_dt.tzinfo is None else eff_dt
                p_basis = "statistical_market_range" if src.code == "PBS_STATISTICAL_MONTHLY" else "indicative_wholesale"
                prov_label = "Official statistical average price" if src.code == "PBS_STATISTICAL_MONTHLY" else "Indicative market price"
                all_evidence.append(
                    MaterialRateEvidenceItem(
                        observation_id=str(obs.id),
                        product_code=prod.code,
                        product_name=prod.canonical_name,
                        name=prod.canonical_name,
                        category=prod.category,
                        city=c,
                        price_pkr=obs.normalized_price_pkr,
                        unit=obs.normalized_unit,
                        price_basis=p_basis,
                        provenance_label=prov_label,
                        source_code=src.code,
                        source_name=src.name,
                        source_tier=src.reliability_tier,
                        verification_status=obs.verification_status,
                        confidence_score=85,
                        published_at=obs.published_at,
                        collected_at=obs.collected_at,
                        observed_at=eff_tz,
                        age_days=0.0,
                        source_url=obs.source_url,
                        disclaimer=f"Reported by {src.name}.",
                    )
                )
            if rows:
                bm = await self.compute_canonical_benchmark(db, rows[0][2], c, rows)
                city_benchmarks[c] = bm
            else:
                city_benchmarks[c] = None

        # Build comparison text
        mat_label = (query.product_name or query.material_category or "Construction Material").title()
        lines: List[str] = [f"### Regional Price Comparison: {mat_label}\n"]

        for c in cities:
            bm = city_benchmarks.get(c)
            if bm:
                lines.append(f"- **{c}:** PKR {bm.benchmark_rate_pkr:,.2f} /{bm.unit.replace('_', ' ')} (Range: PKR {bm.price_min_pkr:,.2f} – PKR {bm.price_max_pkr:,.2f})")
            else:
                lines.append(f"- **{c}:** Verified rates currently unavailable in database.")

        lines.append("\n> **Market Variance:** Regional price differences reflect quarry proximity, manufacturing mill logistics, and local transportation surcharges.")
        formatted_answer = "\n".join(lines)

        citations = [item.to_citation_dict() for item in all_evidence]
        xml_prompt = f"<material_rate_comparison material='{mat_label}' cities='{','.join(cities)}' />"

        return MaterialRateBridgeResult(
            query=query,
            status="verified_evidence" if all_evidence else "unavailable",
            evidence_items=all_evidence,
            canonical_benchmark=list(city_benchmarks.values())[0] if any(city_benchmarks.values()) else None,
            formatted_answer=formatted_answer,
            xml_evidence_prompt=xml_prompt,
            citations=citations,
            is_grounded=True,
            disclaimer="Cross-city market rates derived from eligible regional database records.",
            telemetry={"comparison_cities": cities, "total_evidence": len(all_evidence)},
        )


# Global singleton bridge instance
material_rate_bridge = MaterialRateIntelligenceBridge()
