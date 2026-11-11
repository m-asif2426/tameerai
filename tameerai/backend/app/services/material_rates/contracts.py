"""
TameerAI - Material Rate Collection Domain Models & Typing Contracts (Stage 2A)

Provides immutable dataclasses, enums, and schemas for the material rate
collection engine, base source adapters, and normalization pipeline.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
import enum
from typing import Any, Dict, List, Optional
import uuid


class CollectionSourceType(str, enum.Enum):
    OFFICIAL = "official"
    MANUFACTURER = "manufacturer"
    DEALER_NETWORK = "dealer_network"
    AGGREGATOR = "aggregator"
    MANUAL_SURVEY = "manual_survey"


class SourceCategory(str, enum.Enum):
    """Authoritative classification of construction material pricing sources."""
    OFFICIAL_STATISTICAL = "official_statistical"
    GOVERNMENT_SCHEDULE = "government_schedule"
    MANUFACTURER_EX_FACTORY = "manufacturer_ex_factory"
    AUTHORIZED_DISTRIBUTOR = "authorized_distributor"
    VERIFIED_DEALER_QUOTATION = "verified_dealer_quotation"
    MARKETPLACE_LISTING = "marketplace_listing"
    SECONDARY_MARKET_PUBLISHER = "secondary_market_publisher"
    HISTORICAL_ARCHIVE = "historical_archive"
    PROCUREMENT_RECORD = "procurement_record"


class SourceOperationalStatus(str, enum.Enum):
    """Operational reliability & ingestion eligibility status for a data source."""
    VERIFIED_CURRENT = "verified_current"
    VERIFIED_HISTORICAL = "verified_historical"
    CANDIDATE = "candidate"
    STALE = "stale"
    INACCESSIBLE = "inaccessible"
    RESTRICTED = "restricted"
    REJECTED = "rejected"


class PriceBasis(str, enum.Enum):
    """Commercial transaction basis & supply-chain stage for a reported rate."""
    EX_FACTORY = "ex_factory"
    EX_MILL = "ex_mill"
    WHOLESALE = "wholesale"
    RETAIL = "retail"
    DEALER_QUOTATION = "dealer_quotation"
    RETAIL_DEPOT = "retail_depot"
    DELIVERED_TO_SITE = "delivered_to_site"
    GOVERNMENT_SCHEDULE_RATE = "government_schedule_rate"
    STATISTICAL_INDEX = "statistical_index"
    PLANNING_ESTIMATE = "planning_estimate"


class NormalizedCategory(str, enum.Enum):
    CEMENT = "cement"
    STEEL = "steel"
    BRICKS = "bricks"
    SAND = "sand"
    CRUSH = "crush"
    BLOCKS = "blocks"
    TILES = "tiles"
    OTHER = "other"


@dataclass(frozen=True)
class RawSourceRecord:
    """Unprocessed data record extracted directly from a source response/document."""
    raw_material_name: str
    raw_price: Any
    raw_unit: str
    raw_city: Optional[str] = None
    raw_published_date: Optional[Any] = None
    brand: Optional[str] = None
    grade: Optional[str] = None
    specification: Optional[str] = None
    price_basis: Optional[PriceBasis] = None
    dealer_id: Optional[uuid.UUID] = None
    dealer_quote_id: Optional[uuid.UUID] = None
    is_syndicated: bool = False
    original_source_citation: Optional[str] = None
    republished_from: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    source_url: Optional[str] = None


@dataclass(frozen=True)
class NormalizedObservationCandidate:
    """
    Validated and standardized material rate observation candidate ready for
    fingerprinting, deduplication, and database persistence.
    """
    source_id: uuid.UUID
    product_id: uuid.UUID
    category: NormalizedCategory
    canonical_name: str
    city: Optional[str]
    observed_price_pkr: Decimal
    observed_unit: str
    normalized_price_pkr: Decimal
    normalized_unit: str
    published_at: Optional[datetime]
    verification_status: str  # e.g., 'unverified', 'verified_quote', 'indicative'
    raw_payload_hash: str
    brand: Optional[str] = None
    grade: Optional[str] = None
    specification: Optional[str] = None
    price_basis: PriceBasis = PriceBasis.RETAIL
    dealer_id: Optional[uuid.UUID] = None
    dealer_quote_id: Optional[uuid.UUID] = None
    is_syndicated: bool = False
    original_source_citation: Optional[str] = None
    republished_from: Optional[str] = None
    source_url: Optional[str] = None
    observation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceRunSummary:
    """Execution telemetry and metric accounting for an adapter collection run."""
    source_id: uuid.UUID
    source_code: str
    status: str  # "completed", "partial", "failed"
    total_fetched: int = 0
    inserted_count: int = 0
    duplicate_count: int = 0
    rejected_count: int = 0
    failed_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata_snapshot: Dict[str, Any] = field(default_factory=dict)

