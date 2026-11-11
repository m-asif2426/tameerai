"""
TameerAI - Pydantic Request & Response Schemas for Material Rate Intelligence (Phase 02)
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Product Catalog Schemas
# ---------------------------------------------------------------------------

class MaterialRateProductBase(BaseModel):
    code: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50)
    subcategory: Optional[str] = Field(None, max_length=50)
    canonical_name: str = Field(..., max_length=150)
    canonical_name_urdu: Optional[str] = Field(None, max_length=150)
    standard_unit: str = Field(..., max_length=50)
    standard_unit_urdu: Optional[str] = Field(None, max_length=50)
    spec_attributes: Optional[Dict[str, Any]] = None
    volatility_tier: str = Field("medium", max_length=20)
    max_acceptable_variance_pct: Decimal = Field(Decimal("15.00"))


class MaterialRateProductCreate(MaterialRateProductBase):
    pass


class MaterialRateProductRead(MaterialRateProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 2. Source & Telemetry Schemas
# ---------------------------------------------------------------------------

class MaterialRateSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    source_type: str
    permission_status: str
    reliability_tier: str
    refresh_cadence: str
    freshness_ttl_days: int
    base_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MaterialRateSourceRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    background_job_id: Optional[uuid.UUID] = None
    status: str
    records_discovered: int
    records_accepted: int
    records_rejected: int
    duplicates_detected: int
    source_duration_ms: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None


class MaterialRateTelemetryRead(BaseModel):
    total_runs: int
    total_records_accepted: int
    total_duplicates_detected: int
    total_records_rejected: int
    collection_enabled: bool
    recent_runs: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# 3. Snapshot & Canonical Market Rate Schemas
# ---------------------------------------------------------------------------

class PriceRange(BaseModel):
    min: float
    max: float


class CanonicalRateSnapshotRead(BaseModel):
    product_id: str
    product_code: str
    product_name: str
    category: str
    city: str
    rate_pkr: float
    prev_rate_pkr: Optional[float] = None
    unit: str
    trend: str
    verification_status: str
    confidence_score: int
    observation_count: int
    price_range: PriceRange
    is_conflicted: bool
    snapshot_at: str


# ---------------------------------------------------------------------------
# 4. Historical Intelligence Schemas
# ---------------------------------------------------------------------------

class PriceHistoryDataPoint(BaseModel):
    period: str
    median_pkr: float
    mean_pkr: float
    min_pkr: float
    max_pkr: float
    observation_count: int


class PriceHistoryResponse(BaseModel):
    product_code: str
    product_name: str
    category: str
    city: Optional[str] = None
    interval: str
    total_observations: int
    data_points: List[PriceHistoryDataPoint]
    price_change_pct: float
    volatility_pkr: float
    trend_confidence: int


class CityComparisonItem(BaseModel):
    city: str
    rate_pkr: Optional[float] = None
    unit: str
    trend: str
    verification_status: str
    confidence_score: int
    observation_count: int
    is_conflicted: bool


class CrossCityComparisonResponse(BaseModel):
    product_code: str
    product_name: str
    category: str
    standard_unit: str
    national_median_pkr: float
    cities: List[CityComparisonItem]


# ---------------------------------------------------------------------------
# 5. Dealer & Quotation Schemas
# ---------------------------------------------------------------------------

class DealerCreate(BaseModel):
    business_name: str = Field(..., max_length=150)
    dealer_code: str = Field(..., max_length=50)
    city: str = Field(..., max_length=50)
    market_area: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    ntn_number: Optional[str] = Field(None, max_length=50)


class DealerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    business_name: str
    dealer_code: str
    city: str
    market_area: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    ntn_number: Optional[str] = None
    verification_state: str
    verified_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DealerQuoteCreate(BaseModel):
    dealer_id: uuid.UUID
    product_id: uuid.UUID
    city: str = Field(..., max_length=50)
    quoted_price_pkr: Decimal = Field(..., ge=0)
    quoted_unit: str = Field(..., max_length=50)
    validity_days: int = Field(7, ge=1, le=90)
    minimum_order_quantity: Optional[Decimal] = Field(None, ge=0)
    delivery_charges_pkr: Decimal = Field(Decimal("0.00"), ge=0)
    tax_included: bool = True
    payment_terms: Optional[str] = Field(None, max_length=100)
    vehicle_capacity_cft: Optional[Decimal] = Field(None, ge=0)


class DealerQuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dealer_id: uuid.UUID
    product_id: uuid.UUID
    city: str
    quoted_price_pkr: Decimal
    quoted_unit: str
    normalized_price_pkr: Decimal
    normalized_unit: str
    quotation_date: datetime
    validity_days: int
    valid_until: datetime
    minimum_order_quantity: Optional[Decimal] = None
    delivery_charges_pkr: Decimal
    tax_included: bool
    payment_terms: Optional[str] = None
    evidence_file_name: Optional[str] = None
    status: str
    created_at: datetime


class EvidenceUploadResponse(BaseModel):
    quote_id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    signed_download_token: str
    message: str


# ---------------------------------------------------------------------------
# 6. Verification Audit Schemas
# ---------------------------------------------------------------------------

class VerificationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    observation_id: Optional[uuid.UUID] = None
    dealer_quote_id: Optional[uuid.UUID] = None
    previous_status: Optional[str] = None
    new_status: str
    reason: str
    actor_user_id: Optional[uuid.UUID] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# 7. Orchestration Schemas
# ---------------------------------------------------------------------------

class OrchestrationTriggerRequest(BaseModel):
    source_code: str
    force: bool = False
    category_hint: Optional[str] = None


class OrchestrationTriggerResponse(BaseModel):
    source_code: str
    status: str
    records_discovered: int
    records_accepted: int
    records_rejected: int
    duplicates_detected: int
    error_message: Optional[str] = None

