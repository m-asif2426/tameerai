"""
TameerAI - National Construction Material Source Discovery & Credibility Registry (Stage 2B)

Maintains the authoritative national catalog of construction material data providers,
manufacturers, statutory government schedules, statistical agencies, marketplaces,
secondary publishers, and dealer trade networks across Pakistan.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.material_rates.contracts import (
    PriceBasis,
    SourceCategory,
    SourceOperationalStatus,
)


@dataclass(frozen=True)
class SourceRegistryEntry:
    """Detailed metadata and evaluation profile for an identified data source."""
    source_code: str
    name: str
    category: SourceCategory
    operational_status: SourceOperationalStatus
    price_basis: PriceBasis
    credibility_score: int  # 1-100 scale
    geographic_scope: str  # "National", "Provincial", "District/City", "Localized"
    update_cadence: str  # "Daily", "Weekly", "Bi-Annual", "Quarterly", "On-Demand"
    materials_covered: List[str]
    cities_covered: List[str]
    access_method: str  # "REST API", "HTML Table", "PDF Document", "Direct Ingestion"
    base_url: Optional[str] = None
    requires_auth: bool = False
    notes_and_rationale: str = ""
    evaluation_metadata: Dict[str, Any] = field(default_factory=dict)


def compute_transparent_credibility_score(
    category: SourceCategory,
    operational_status: SourceOperationalStatus,
    is_primary_producer_or_statutory: bool,
    evidence_tier: str,  # "statutory_bulletin", "verified_invoice", "b2b_exchange", "structured_daily_table", "secondary_web_survey"
    geographic_granularity: str,  # "city_or_mill_specific", "district_specific", "provincial", "national_general"
    has_syndication_risk: bool = False,
) -> int:
    """
    Computes a transparent, auditable 0-100 publisher credibility score across seven objective pillars:
    1. Publisher Institutional Standing (Max 25 pts)
    2. Originality of Data / Ground Truth (Max 20 pts)
    3. Evidence Quality & Traceability (Max 20 pts)
    4. Geographic Specificity (Max 15 pts)
    5. Historical Consistency (Max 10 pts)
    6. Freshness / Operational Readiness (Max 10 pts)
    7. Penalties:
       - Offline / Inaccessible Penalty: -25 pts (SourceOperationalStatus.INACCESSIBLE)
       - Syndication / Re-aggregation Risk Penalty: -15 pts (has_syndication_risk=True)

    Enforces final score range of strictly 0 to 100.
    """
    score = 0

    # 1. Publisher Standing (0-25)
    if category == SourceCategory.OFFICIAL_STATISTICAL:
        score += 25
    elif category == SourceCategory.VERIFIED_DEALER_QUOTATION:
        score += 25
    elif category == SourceCategory.MANUFACTURER_EX_FACTORY:
        score += 24
    elif category == SourceCategory.GOVERNMENT_SCHEDULE:
        score += 22
    elif category == SourceCategory.MARKETPLACE_LISTING:
        score += 18
    elif category == SourceCategory.SECONDARY_MARKET_PUBLISHER:
        score += 12
    else:
        score += 10

    # 2. Originality (0-20)
    if is_primary_producer_or_statutory:
        score += 20
    elif category == SourceCategory.MARKETPLACE_LISTING:
        score += 16
    elif category == SourceCategory.VERIFIED_DEALER_QUOTATION:
        score += 18
    else:
        score += 8

    # 3. Evidence Quality (0-20)
    if evidence_tier in ("statutory_bulletin", "verified_invoice"):
        score += 20
    elif evidence_tier == "b2b_exchange":
        score += 16
    elif evidence_tier == "structured_daily_table":
        score += 12
    else:
        score += 6

    # 4. Geographic Specificity (0-15)
    if geographic_granularity == "city_or_mill_specific":
        score += 15
    elif geographic_granularity == "district_specific":
        score += 13
    elif geographic_granularity == "provincial":
        score += 9
    else:
        score += 5

    # 5. Historical Consistency (0-10)
    if category in (SourceCategory.OFFICIAL_STATISTICAL, SourceCategory.GOVERNMENT_SCHEDULE, SourceCategory.MANUFACTURER_EX_FACTORY):
        score += 10
    elif category == SourceCategory.VERIFIED_DEALER_QUOTATION:
        score += 8
    else:
        score += 6

    # 6. Operational Status Adjustment & Inaccessible Penalty (-25 pts)
    if operational_status == SourceOperationalStatus.VERIFIED_CURRENT:
        score += 10
    elif operational_status == SourceOperationalStatus.VERIFIED_HISTORICAL:
        score += 6
    elif operational_status == SourceOperationalStatus.RESTRICTED:
        score -= 5
    elif operational_status == SourceOperationalStatus.INACCESSIBLE:
        score -= 25  # Documented Offline / Unreachable Penalty

    # 7. Syndication Penalty (-15 pts)
    if has_syndication_risk:
        score -= 15  # Documented Syndication / Secondary Aggregation Penalty

    return max(0, min(100, score))


def compute_observation_confidence(
    publisher_credibility: int,
    verification_status: str,
    is_stale: bool = False,
    has_exact_date: bool = True,
    is_cross_verified: bool = False,
) -> int:
    """
    Computes distinct observation-level confidence score (0-100), keeping separate:
    1. Source publisher credibility (base score)
    2. Observation verification status (verified_quote, cross_checked, indicative, conflicted, etc.)
    3. Freshness / Staleness (stale penalty -30)
    4. Exact quotation date presence (missing date penalty -20)
    5. Cross-source verification bonus (+15)
    """
    conf = publisher_credibility
    if verification_status == "indicative":
        conf -= 20
    elif verification_status == "conflicted":
        conf -= 40
    elif verification_status == "verified_quote":
        conf += 10

    if not has_exact_date:
        conf -= 20
    if is_stale:
        conf -= 30
    if is_cross_verified:
        conf += 15

    return max(0, min(100, conf))


class NationalSourceRegistry:
    """
    Central discovery registry managing evaluated Pakistani construction material sources.
    Enforces architectural separation between official statistical benchmarks, statutory
    schedules, mill circulars, verified dealer quotes, and secondary market aggregators.
    """

    def __init__(self):
        self._entries: Dict[str, SourceRegistryEntry] = {}
        self._initialize_national_sources()

    def _initialize_national_sources(self):
        sources = [
            # 1. Official Statistical
            SourceRegistryEntry(
                source_code="PBS_STATISTICAL_SPI",
                name="Pakistan Bureau of Statistics - Sensitive Price Indicator (SPI)",
                category=SourceCategory.OFFICIAL_STATISTICAL,
                operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                price_basis=PriceBasis.STATISTICAL_INDEX,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.OFFICIAL_STATISTICAL,
                    operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="statutory_bulletin",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National (17 Urban Centers)",
                update_cadence="Weekly",
                materials_covered=["Cement (50 kg bag)"],
                cities_covered=[
                    "Islamabad", "Rawalpindi", "Lahore", "Karachi", "Peshawar",
                    "Quetta", "Multan", "Faisalabad", "Gujranwala", "Sialkot",
                    "Hyderabad", "Sukkur", "Larkana", "Bannu", "Sargodha", "Abbottabad", "Bahawalpur",
                ],
                access_method="Weekly Excel / PDF Bulletin (Verified Nov 5, 2026)",
                base_url="https://www.pbs.gov.pk/price-statistics/",
                notes_and_rationale="Statutory statistical agency tracking 50 markets across 17 major commercial centers weekly.",
            ),
            SourceRegistryEntry(
                source_code="PBS_STATISTICAL_MONTHLY",
                name="Pakistan Bureau of Statistics - Monthly Construction Material Prices",
                category=SourceCategory.OFFICIAL_STATISTICAL,
                operational_status=SourceOperationalStatus.VERIFIED_HISTORICAL,
                price_basis=PriceBasis.STATISTICAL_INDEX,
                credibility_score=95,
                geographic_scope="National (Urban Centers)",
                update_cadence="Monthly",
                materials_covered=["Cement", "Steel Rebar Grade 40", "Bricks", "Sand", "Bajri", "Blocks"],
                cities_covered=[
                    "Islamabad", "Rawalpindi", "Lahore", "Karachi", "Peshawar",
                    "Quetta", "Multan", "Faisalabad", "Gujranwala", "Sialkot",
                    "Hyderabad", "Sukkur", "Larkana", "Bannu", "Sargodha", "Abbottabad", "Bahawalpur",
                ],
                access_method="Monthly Excel Workbook (Urbn-Construction)",
                base_url="https://www.pbs.gov.pk",
                notes_and_rationale="Statutory statistical agency tracking urban construction material prices monthly across Pakistan.",
            ),
            SourceRegistryEntry(
                source_code="PBS_MONTHLY_INDICES",
                name="Pakistan Bureau of Statistics - Monthly Wholesale & Consumer Indices",
                category=SourceCategory.OFFICIAL_STATISTICAL,
                operational_status=SourceOperationalStatus.INACCESSIBLE,
                price_basis=PriceBasis.STATISTICAL_INDEX,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.OFFICIAL_STATISTICAL,
                    operational_status=SourceOperationalStatus.INACCESSIBLE,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="statutory_bulletin",
                    geographic_granularity="national_general",
                ),
                geographic_scope="National",
                update_cadence="Monthly",
                materials_covered=["Cement", "Steel Rebar", "Bricks", "Tiles", "Glass", "Timber"],
                cities_covered=["National Average"],
                access_method="PDF Bulletin",
                base_url="https://www.pbs.gov.pk/price-statistics/",
                notes_and_rationale="Previous web path /content/monthly-review-price-indices moved (HTTP 404); requires PDF extraction from portal.",
            ),

            # 2. Statutory Government Schedules
            SourceRegistryEntry(
                source_code="NHA_CSR_SCHEDULE",
                name="National Highway Authority (NHA) - Composite Schedule of Rates",
                category=SourceCategory.GOVERNMENT_SCHEDULE,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.GOVERNMENT_SCHEDULE,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="statutory_bulletin",
                    geographic_granularity="district_specific",
                ),
                geographic_scope="National (156 Districts)",
                update_cadence="Bi-Annual",
                materials_covered=["Cement", "Steel Rebar Grade 60/40", "Aggregates/Crush", "Sand", "Bitumen/Asphalt", "Bricks"],
                cities_covered=["All 156 Districts of Pakistan"],
                access_method="PDF Schedule / Restricted Portal",
                base_url="https://nha.gov.pk/csr",
                notes_and_rationale="Authoritative statutory rate standard for Pakistani public infrastructure. Web portal blocks automated GET requests (HTTP 403 WAF).",
            ),
            SourceRegistryEntry(
                source_code="PUNJAB_CW_MRS",
                name="Punjab C&W / Finance Department - Market Rate System (MRS)",
                category=SourceCategory.GOVERNMENT_SCHEDULE,
                operational_status=SourceOperationalStatus.VERIFIED_HISTORICAL,
                price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.GOVERNMENT_SCHEDULE,
                    operational_status=SourceOperationalStatus.VERIFIED_HISTORICAL,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="statutory_bulletin",
                    geographic_granularity="district_specific",
                ),
                geographic_scope="Provincial (Punjab - 36 Districts)",
                update_cadence="Bi-Annual (1st Bi-annual Jan-Jun, 2nd Bi-annual Jul-Dec)",
                materials_covered=["Cement", "Steel Rebar", "Sand Chenab/Ravi", "Crush Sargodha/Margalla", "Bricks Awwal", "Blocks"],
                cities_covered=["Lahore", "Rawalpindi", "Faisalabad", "Multan", "Gujranwala", "Sargodha", "Sialkot", "Bahawalpur"],
                access_method="PDF Gazette Notifications",
                base_url="https://finance.punjab.gov.pk",
                notes_and_rationale="Statutory public works rates published bi-annually as gazette PDFs, not real-time APIs.",
            ),
            SourceRegistryEntry(
                source_code="SINDH_WSD_CSR",
                name="Sindh Works & Services Department - Composite Schedule of Rates",
                category=SourceCategory.GOVERNMENT_SCHEDULE,
                operational_status=SourceOperationalStatus.INACCESSIBLE,
                price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.GOVERNMENT_SCHEDULE,
                    operational_status=SourceOperationalStatus.INACCESSIBLE,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="statutory_bulletin",
                    geographic_granularity="provincial",
                ),
                geographic_scope="Provincial (Sindh - 30 Districts)",
                update_cadence="Annual / Bi-Annual",
                materials_covered=["Cement", "Steel Rebar", "Sand Bolan/Malir", "Crush Thatta/Hub", "Blocks", "Bricks"],
                cities_covered=["Karachi", "Hyderabad", "Sukkur", "Larkana", "Mirpurkhas", "Shaheed Benazirabad"],
                access_method="Unreachable (DNS Resolution Failure)",
                base_url="https://works.sindh.gov.pk",
                notes_and_rationale="works.sindh.gov.pk nameserver currently unresolvable.",
            ),
            SourceRegistryEntry(
                source_code="KP_CW_CSR",
                name="Khyber Pakhtunkhwa C&W Department - Composite Schedule of Rates",
                category=SourceCategory.GOVERNMENT_SCHEDULE,
                operational_status=SourceOperationalStatus.VERIFIED_HISTORICAL,
                price_basis=PriceBasis.GOVERNMENT_SCHEDULE_RATE,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.GOVERNMENT_SCHEDULE,
                    operational_status=SourceOperationalStatus.VERIFIED_HISTORICAL,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="statutory_bulletin",
                    geographic_granularity="provincial",
                ),
                geographic_scope="Provincial (KPK - 35 Districts)",
                update_cadence="Annual",
                materials_covered=["Cement", "Steel Rebar", "Sand", "Crush Nizampur/Kohat", "Bricks"],
                cities_covered=["Peshawar", "Mardan", "Abbottabad", "Swat", "Kohat", "Dera Ismail Khan"],
                access_method="PDF Downloads on Web Portal (HTTP 200 OK)",
                base_url="https://cwd.kp.gov.pk/page/composite_schedule_of_rates",
                notes_and_rationale="Portal accessible, provides annual statutory PDF schedule downloads.",
            ),

            # 3. Primary Manufacturers (Ex-Factory / Ex-Mill)
            SourceRegistryEntry(
                source_code="MFR_LUCKY_CEMENT",
                name="Lucky Cement Limited - Mill Circulars & Dispatch Pricing",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_FACTORY,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National (North & South Zones)",
                update_cadence="Weekly / As-Revised",
                materials_covered=["Ordinary Portland Cement", "Sulphate Resistant Cement", "Slag Cement"],
                cities_covered=["Karachi", "Pezu (KPK)", "Lahore", "Islamabad"],
                access_method="Dealer Allocation Circulars (Website hosts corporate/technical specs only)",
                base_url="https://lucky-cement.com/en",
                notes_and_rationale="Public website active (200 OK) but does not publish live pricing sheets; requires authorized dealer quota invoices.",
            ),
            SourceRegistryEntry(
                source_code="MFR_BESTWAY_CEMENT",
                name="Bestway Cement Limited - Dealer Allocation Circulars",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_FACTORY,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="Regional (Punjab, KPK, AJK, ICT)",
                update_cadence="Weekly / As-Revised",
                materials_covered=["Ordinary Portland Cement", "Pakcem OPC", "Tile Grout"],
                cities_covered=["Islamabad", "Rawalpindi", "Lahore", "Hattar", "Farooqia", "Chakwal"],
                access_method="Stockist Dispatch Invoices (Website hosts product catalogs only)",
                base_url="https://www.bestway.com.pk/products/",
                notes_and_rationale="Public site active (200 OK) but transaction rates are restricted to stockist booking desks.",
            ),
            SourceRegistryEntry(
                source_code="MFR_DGKHAN_CEMENT",
                name="D.G. Khan Cement Company Limited - Dispatch Pricing",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_FACTORY,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National (Punjab, Sindh, Balochistan)",
                update_cadence="Weekly / As-Revised",
                materials_covered=["Ordinary Portland Cement", "Sulphate Resistant Cement"],
                cities_covered=["D.G. Khan", "Khairpur", "Hub", "Lahore", "Karachi"],
                access_method="Stockist Circulars",
                base_url="https://dgcement.com",
                notes_and_rationale="Website active (200 OK) with product specs; commercial pricing distributed through regional depots.",
            ),
            SourceRegistryEntry(
                source_code="MFR_MUGHAL_STEEL",
                name="Mughal Iron & Steel Industries Limited - Mill-Gate Price List",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_MILL,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National",
                update_cadence="Daily / Weekly",
                materials_covered=["Deformed Steel Rebar Grade 60", "Mughal Supreme Grade 72 Steel", "Steel Girders/Beams"],
                cities_covered=["Lahore (Badami Bagh)", "Islamabad", "Karachi", "Faisalabad"],
                access_method="Distributor Booking Circulars",
                base_url="https://mughalsteel.com.pk/?v=null",
                notes_and_rationale="Website active (200 OK); mill-gate booking rates are issued directly to Badami Bagh distributors.",
            ),
            SourceRegistryEntry(
                source_code="MFR_AMRELI_STEEL",
                name="Amreli Steels Limited - Mill Price Circulars",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_MILL,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National (Southern Anchor)",
                update_cadence="Daily / Weekly",
                materials_covered=["Amreli Maxima Grade 60 Steel Rebar", "Amreli Ultima Grade 500W Steel"],
                cities_covered=["Karachi (Shershah)", "Lahore", "Islamabad", "Hyderabad"],
                access_method="Distributor Price Sheets",
                base_url="https://amrelisteels.com",
                notes_and_rationale="Website active (200 OK); transactions governed by mill booking desk at Shershah Karachi.",
            ),
            SourceRegistryEntry(
                source_code="MFR_AGHA_STEEL",
                name="Agha Steel Industries Limited - Mill Quotes",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_MILL,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National",
                update_cadence="Weekly",
                materials_covered=["Agha Arcon Grade 60 Steel Rebar"],
                cities_covered=["Karachi", "Lahore", "Islamabad"],
                access_method="Distributor Price Circulars",
                base_url="https://aghasteel.com",
                notes_and_rationale="Website active (200 OK); prices negotiated via authorized trade dealers.",
            ),
            SourceRegistryEntry(
                source_code="MFR_FF_STEEL",
                name="Frontier Foundry Steel (FF Steel) - Mill Gate List",
                category=SourceCategory.MANUFACTURER_EX_FACTORY,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.EX_MILL,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MANUFACTURER_EX_FACTORY,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National (Peshawar & Lahore Plants)",
                update_cadence="Weekly",
                materials_covered=["FF Grade 60 Steel Rebar", "Thermex Quenched Steel Rebar"],
                cities_covered=["Peshawar", "Lahore", "Islamabad", "Rawalpindi"],
                access_method="Distributor Circulars",
                base_url="https://ff.com.pk",
                notes_and_rationale="Website active (200 OK); pricing managed via regional sales offices.",
            ),

            # 4. Commercial B2B Exchanges & Digital Marketplaces
            SourceRegistryEntry(
                source_code="ZAREA_B2B_MARKETPLACE",
                name="Zarea Raw Materials B2B Digital Exchange",
                category=SourceCategory.MARKETPLACE_LISTING,
                operational_status=SourceOperationalStatus.RESTRICTED,
                price_basis=PriceBasis.WHOLESALE,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.MARKETPLACE_LISTING,
                    operational_status=SourceOperationalStatus.RESTRICTED,
                    is_primary_producer_or_statutory=False,
                    evidence_tier="b2b_exchange",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National",
                update_cadence="Daily",
                materials_covered=["Cement (All Brands)", "Steel Rebar (Mughal, Amreli, Kamran)", "Coal", "Aggregates"],
                cities_covered=["Lahore", "Karachi", "Islamabad", "Faisalabad", "Multan"],
                access_method="Next.js Client Hydration (Static GET returns empty container)",
                base_url="https://zarea.com/daily-price/cement",
                notes_and_rationale="Dynamic B2B commodity platform. Rates rendered client-side via Next.js hydration; static GET returns empty container 'No Data Available'. Classified as restricted without browser-rendering engine or authorized B2B API.",
            ),

            # 5. Secondary Market Rate Publishers & Aggregators
            SourceRegistryEntry(
                source_code="MATERIALRATE_PK_PUBLISHER",
                name="MaterialRate.pk Daily Construction Materials Monitor",
                category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
                operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                price_basis=PriceBasis.RETAIL,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
                    operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                    is_primary_producer_or_statutory=False,
                    evidence_tier="structured_daily_table",
                    geographic_granularity="city_or_mill_specific",
                    has_syndication_risk=True,
                ),
                geographic_scope="National (Major Cities)",
                update_cadence="Daily",
                materials_covered=["Cement", "Steel Rebar", "Bricks Awwal", "Sand Chenab/Ravi", "Crush Margalla/Sargodha", "Blocks"],
                cities_covered=["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Multan", "Peshawar", "Faisalabad", "Gujranwala"],
                access_method="HTML Live Tables (Verified 200 OK on 5 Sub-Endpoints)",
                base_url="https://materialrate.pk",
                notes_and_rationale="Extracted live tables for Cement, Steel Rebar (Grade 40/60), Bricks, Sand, and Bajri. Subject to syndication discount.",
            ),
            SourceRegistryEntry(
                source_code="GHARHUB_PK_PUBLISHER",
                name="GharHub Pakistan Construction Cost Guide",
                category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
                operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                price_basis=PriceBasis.RETAIL,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
                    operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                    is_primary_producer_or_statutory=False,
                    evidence_tier="structured_daily_table",
                    geographic_granularity="city_or_mill_specific",
                    has_syndication_risk=False,
                ),
                geographic_scope="Regional (Punjab & ICT)",
                update_cadence="Daily",
                materials_covered=["Bricks (Awwal/Doyam)", "Sand", "Crush", "Cement", "Steel"],
                cities_covered=["Lahore", "Rawalpindi", "Islamabad"],
                access_method="HTML Live Tables (Verified 200 OK on 5 Sub-Endpoints)",
                base_url="https://gharhub.com",
                notes_and_rationale="Accessible retail benchmark with brand-level tables for Cement (Maple Leaf, DG Khan, Bestway), Steel (Mughal, Sheikhoo), Bricks, Sand, and Crush.",
            ),
            SourceRegistryEntry(
                source_code="STEELRATETODAY_PK_PUBLISHER",
                name="SteelRateToday Rebar & Scrap Market Monitor",
                category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
                operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                price_basis=PriceBasis.WHOLESALE,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
                    operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
                    is_primary_producer_or_statutory=False,
                    evidence_tier="structured_daily_table",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="National (Steel Hubs)",
                update_cadence="Daily",
                materials_covered=["Deformed Steel Rebar Grade 60", "Grade 40", "Billet", "Scrap"],
                cities_covered=["Lahore (Badami Bagh / Misri Shah)", "Karachi (Shershah)", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Peshawar"],
                access_method="HTML Daily Rate Tables (3 Verified Tables: Sizes, Brands, Cities)",
                base_url="https://steelratetoday.pk",
                notes_and_rationale="Active WordPress site with daily rebar updates by brand, size, and city. Rates are secondary publisher indicative estimates.",
            ),

            # 6. Direct Verified Dealer Submissions
            SourceRegistryEntry(
                source_code="DIRECT_DEALER_QUOTATION",
                name="TameerAI Verified Construction Material Dealer Network",
                category=SourceCategory.VERIFIED_DEALER_QUOTATION,
                operational_status=SourceOperationalStatus.CANDIDATE,
                price_basis=PriceBasis.DEALER_QUOTATION,
                credibility_score=compute_transparent_credibility_score(
                    category=SourceCategory.VERIFIED_DEALER_QUOTATION,
                    operational_status=SourceOperationalStatus.CANDIDATE,
                    is_primary_producer_or_statutory=True,
                    evidence_tier="verified_invoice",
                    geographic_granularity="city_or_mill_specific",
                ),
                geographic_scope="Localized / City-Specific",
                update_cadence="On-Demand / Transactional",
                materials_covered=["Cement", "Steel", "Bricks", "Sand", "Crush", "Blocks", "Tiles"],
                cities_covered=["All Registered Dealer Municipalities"],
                access_method="Direct Ingestion API / Dealer Portal",
                base_url="https://tameerai.com/dealer-portal",
                notes_and_rationale="Ingestion connector implemented in code; 0 registered dealers currently onboarded. Network registration is pending live dealer verification.",
            ),
        ]

        for s in sources:
            self._entries[s.source_code] = s

    def get_source(self, source_code: str) -> Optional[SourceRegistryEntry]:
        """Retrieves a source entry by unique code."""
        return self._entries.get(source_code)

    def list_sources(
        self,
        *,
        category: Optional[SourceCategory] = None,
        operational_status: Optional[SourceOperationalStatus] = None,
        material_keyword: Optional[str] = None,
        city_keyword: Optional[str] = None,
    ) -> List[SourceRegistryEntry]:
        """Filters registered sources by category, status, material, or city coverage."""
        results = list(self._entries.values())

        if category:
            results = [s for s in results if s.category == category]

        if operational_status:
            results = [s for s in results if s.operational_status == operational_status]

        if material_keyword:
            kw = material_keyword.lower()
            results = [s for s in results if any(kw in m.lower() for m in s.materials_covered)]

        if city_keyword:
            ck = city_keyword.lower()
            results = [s for s in results if any(ck in c.lower() for c in s.cities_covered) or "all" in s.geographic_scope.lower() or "national" in s.geographic_scope.lower()]

        return results

    def get_source_inventory_summary(self) -> Dict[str, Any]:
        """Aggregates inventory counts by category, price basis, and status."""
        categories: Dict[str, int] = {}
        price_bases: Dict[str, int] = {}
        statuses: Dict[str, int] = {}

        for entry in self._entries.values():
            cat = entry.category.value
            categories[cat] = categories.get(cat, 0) + 1

            pb = entry.price_basis.value
            price_bases[pb] = price_bases.get(pb, 0) + 1

            st = entry.operational_status.value
            statuses[st] = statuses.get(st, 0) + 1

        return {
            "total_registered_sources": len(self._entries),
            "by_category": categories,
            "by_price_basis": price_bases,
            "by_status": statuses,
        }


# Global singleton instance
national_registry = NationalSourceRegistry()
