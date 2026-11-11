"""
TameerAI - Construction Material Rate Intelligence Models (Stage 1 / Phase 03H)

Defines:
- MaterialRateProduct: Canonical catalog product specifications across Pakistani markets.
- MaterialRateSource: Official agencies, manufacturers, and data collection adapters.
- MaterialRateDealer: Verified hardware merchants, distributors, and supplier profiles.
- MaterialRateDealerQuote: Direct commercial quotation submissions from verified dealers.
- MaterialRateObservation: Immutable time-series market price observations.
- MaterialRateVerificationEvent: Explainable audit trail for status reviews and transitions.
- MaterialRateSourceRun: Execution telemetry for automated collection and sync workers.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    func,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.cost import MaterialRate
    from app.models.job import BackgroundJob


# ---------------------------------------------------------------------------
# 1. Canonical Product Catalog
# ---------------------------------------------------------------------------

class MaterialRateProduct(Base):
    """
    Canonical Construction Material Product Definition.
    Standardizes commodity naming, measurement units, specifications, and volatility
    tiers across Pakistani regional markets (Lahore, Karachi, Islamabad, Rawalpindi, etc.).
    """

    __tablename__ = "material_rate_products"
    __table_args__ = (
        CheckConstraint(
            "volatility_tier IN ('low', 'medium', 'high', 'extreme')",
            name="ck_material_rate_products_volatility_tier",
        ),
        CheckConstraint(
            "max_acceptable_variance_pct >= 0 AND max_acceptable_variance_pct <= 100",
            name="ck_material_rate_products_max_variance",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique product code (e.g. 'CEMENT-OPC-50KG', 'STEEL-G60-12MM', 'BRICK-AWWAL-STD')",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: cement, steel, bricks, sand, crush, blocks, tiles, other",
    )
    subcategory: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Subcategory (e.g. 'OPC', 'SRC', 'Grade 60 Billet', 'Clay Masonry')",
    )
    canonical_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Authoritative English name (e.g. 'Deformed Steel Bars Grade 60 1/2\" (4 Sutar)')",
    )
    canonical_name_urdu: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Authoritative Urdu name (e.g. 'سٹیل سریا گریڈ 60 چار سوتر')",
    )
    standard_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Standard measurement unit: bag_50kg, metric_ton, kg, 1000_bricks, cft, sqft, piece",
    )
    standard_unit_urdu: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Standard Urdu measurement unit",
    )
    spec_attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        default=dict,
        comment="Flexible JSON attributes (grade, diameter_mm, sutar, origin, standard)",
    )
    volatility_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        server_default="medium",
        comment="Price change frequency tier: low, medium, high, extreme",
    )
    max_acceptable_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("15.00"),
        server_default="15.00",
        comment="Maximum expected price spread before triggering anomaly flag",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Active product flag",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Relationships
    canonical_rates: Mapped[List["MaterialRate"]] = relationship(
        "MaterialRate",
        back_populates="product",
    )
    observations: Mapped[List["MaterialRateObservation"]] = relationship(
        "MaterialRateObservation",
        back_populates="product",
    )
    dealer_quotes: Mapped[List["MaterialRateDealerQuote"]] = relationship(
        "MaterialRateDealerQuote",
        back_populates="product",
    )

    def __repr__(self) -> str:
        return f"<MaterialRateProduct(code='{self.code}', category='{self.category}', unit='{self.standard_unit}')>"


# ---------------------------------------------------------------------------
# 2. Material Rate Data Sources
# ---------------------------------------------------------------------------

class MaterialRateSource(Base):
    """
    Authoritative Agency, Manufacturer, or Dealer Network Data Source.
    Controls legal permission status, reliability classification, refresh schedule,
    and source-specific freshness thresholds (TTL).
    """

    __tablename__ = "material_rate_sources"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('official', 'manufacturer', 'dealer_network', 'aggregator', 'manual_survey')",
            name="ck_material_rate_sources_source_type",
        ),
        CheckConstraint(
            "permission_status IN ('permitted', 'manual_only', 'restricted')",
            name="ck_material_rate_sources_permission_status",
        ),
        CheckConstraint(
            "reliability_tier IN ('authoritative', 'verified', 'indicative', 'unverified')",
            name="ck_material_rate_sources_reliability_tier",
        ),
        CheckConstraint(
            "refresh_cadence IN ('daily', 'weekly', 'monthly', 'ad_hoc')",
            name="ck_material_rate_sources_refresh_cadence",
        ),
        CheckConstraint(
            "freshness_ttl_days >= 1 AND freshness_ttl_days <= 365",
            name="ck_material_rate_sources_freshness_ttl",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Short code (e.g. 'PBS_SPI', 'PBS_MONTHLY', 'MFR_FF_STEEL', 'DEALER_DIRECT')",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Official reporting agency or network name",
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Source category: official, manufacturer, dealer_network, aggregator, manual_survey",
    )
    permission_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="permitted",
        server_default="permitted",
        comment="Legal status: permitted, manual_only, restricted",
    )
    reliability_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="indicative",
        server_default="indicative",
        comment="Reliability rank: authoritative, verified, indicative, unverified",
    )
    refresh_cadence: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="weekly",
        server_default="weekly",
        comment="Update frequency: daily, weekly, monthly, ad_hoc",
    )
    freshness_ttl_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default="30",
        comment="Number of calendar days after publication before quotes from this source become stale",
    )

    @property
    def freshness_ttl_hours(self) -> int:
        """Convenience property computing TTL in hours from canonical freshness_ttl_days column."""
        return self.freshness_ttl_days * 24
    base_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Authoritative public website or portal URL",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Active collector flag",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Relationships
    observations: Mapped[List["MaterialRateObservation"]] = relationship(
        "MaterialRateObservation",
        back_populates="source",
    )
    source_runs: Mapped[List["MaterialRateSourceRun"]] = relationship(
        "MaterialRateSourceRun",
        back_populates="source",
    )

    def __repr__(self) -> str:
        return f"<MaterialRateSource(code='{self.code}', reliability='{self.reliability_tier}', ttl={self.freshness_ttl_days}d)>"


# ---------------------------------------------------------------------------
# 3. Verified Dealers & Suppliers
# ---------------------------------------------------------------------------

class MaterialRateDealer(Base):
    """
    Registered Pakistani Building Material Merchant / Distributor.
    Maintains vetting state, business profile, market territory, and audit references.
    """

    __tablename__ = "material_rate_dealers"
    __table_args__ = (
        CheckConstraint(
            "verification_state IN ('unverified', 'verified', 'suspended', 'rejected')",
            name="ck_material_rate_dealers_verification_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Linked registered user account (optional)",
    )
    business_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        comment="Official trading name of the dealer or dealership",
    )
    dealer_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique identifier (e.g. 'DLR-LHR-0042')",
    )
    city: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Primary operating market city: Lahore, Karachi, Islamabad, Rawalpindi, Peshawar, etc.",
    )
    market_area: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Local market neighborhood (e.g. 'Badami Bagh', 'Shershah', 'I-9 Industrial')",
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Physical warehouse or shop address",
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Owner or manager name",
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Business telephone or mobile number (masked on public APIs)",
    )
    ntn_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="National Tax Number for business identity verification",
    )
    verification_state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        server_default="unverified",
        comment="Dealer status: unverified, verified, suspended, rejected",
    )
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Administrator or engineering reviewer UUID who vetted the dealer",
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of formal business verification",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Active participation status",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    verified_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by_user_id])
    quotes: Mapped[List["MaterialRateDealerQuote"]] = relationship(
        "MaterialRateDealerQuote",
        back_populates="dealer",
    )

    def __repr__(self) -> str:
        return f"<MaterialRateDealer(code='{self.dealer_code}', name='{self.business_name}', city='{self.city}', state='{self.verification_state}')>"


# ---------------------------------------------------------------------------
# 4. Dealer Commercial Quotations
# ---------------------------------------------------------------------------

class MaterialRateDealerQuote(Base):
    """
    Direct Commercial Price Quotation Submitted by a Dealer.
    Maintains payment conditions, minimum quantities, delivery fees, validity period,
    and independent storage evidence references without requiring project workspace scoping.
    """

    __tablename__ = "material_rate_dealer_quotes"
    __table_args__ = (
        CheckConstraint(
            "quoted_price_pkr >= 0",
            name="ck_dealer_quotes_quoted_price_pkr",
        ),
        CheckConstraint(
            "normalized_price_pkr >= 0",
            name="ck_dealer_quotes_normalized_price_pkr",
        ),
        CheckConstraint(
            "delivery_charges_pkr >= 0",
            name="ck_dealer_quotes_delivery_charges",
        ),
        CheckConstraint(
            "validity_days >= 1 AND validity_days <= 90",
            name="ck_dealer_quotes_validity_days",
        ),
        CheckConstraint(
            "status IN ('pending_review', 'verified', 'rejected', 'expired')",
            name="ck_dealer_quotes_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    dealer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("material_rate_dealers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Submitting dealer UUID",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("material_rate_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Target canonical product UUID",
    )
    city: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Market city for the quotation",
    )
    quoted_price_pkr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Raw price in PKR as quoted by the merchant",
    )
    quoted_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Raw unit specified by merchant (e.g. 'per bori', 'per sutar-ton', 'per trolley')",
    )
    normalized_price_pkr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Normalized rate converted to standard canonical product unit",
    )
    normalized_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Standard unit (bag_50kg, metric_ton, 1000_bricks, cft)",
    )
    quotation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Date and time when quotation was formally issued",
    )
    validity_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
        server_default="7",
        comment="Number of calendar days quotation remains legally binding/valid",
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Exact expiration timestamp of the quotation",
    )
    minimum_order_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Minimum order quantity in quoted units (MOQ)",
    )
    delivery_charges_pkr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Included or extra delivery fee (0.00 if ex-mill/ex-shop or free)",
    )
    tax_included: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="True if 18% GST / sales taxes are included in the price",
    )
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Payment terms: '100% Advance', 'Cash on Delivery', '30 Days Credit'",
    )
    evidence_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Safe storage bucket reference path for quotation slip or receipt",
    )
    evidence_file_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Original uploaded evidence filename",
    )
    evidence_content_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type of evidence (image/jpeg, application/pdf)",
    )
    evidence_file_size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="File size in bytes",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_review",
        server_default="pending_review",
        index=True,
        comment="Lifecycle status: pending_review, verified, rejected, expired",
    )
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reviewing engineer/admin UUID",
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when review decision was recorded",
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason recorded if quote was rejected (e.g. illegible slip, outlier)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Database insertion timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Relationships
    dealer: Mapped["MaterialRateDealer"] = relationship("MaterialRateDealer", back_populates="quotes")
    product: Mapped["MaterialRateProduct"] = relationship("MaterialRateProduct", back_populates="dealer_quotes")
    verified_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by_user_id])
    observations: Mapped[List["MaterialRateObservation"]] = relationship(
        "MaterialRateObservation",
        back_populates="dealer_quote",
        passive_deletes="all",
    )
    verification_events: Mapped[List["MaterialRateVerificationEvent"]] = relationship(
        "MaterialRateVerificationEvent",
        back_populates="dealer_quote",
    )

    def __repr__(self) -> str:
        return f"<MaterialRateDealerQuote(id={self.id}, price={self.normalized_price_pkr} PKR/{self.normalized_unit}, status='{self.status}')>"


# ---------------------------------------------------------------------------
# 5. Immutable Rate Observations
# ---------------------------------------------------------------------------

class MaterialRateObservation(Base):
    """
    Immutable Time-Series Market Observation.
    Records every surveyed, scraped, or dealer-quoted price point with a unique SHA-256
    fingerprint for deterministic deduplication. Historical rows are never overwritten.
    """

    __tablename__ = "material_rate_observations"
    __table_args__ = (
        CheckConstraint(
            "observed_price_pkr >= 0",
            name="ck_observations_observed_price_pkr",
        ),
        CheckConstraint(
            "normalized_price_pkr >= 0",
            name="ck_observations_normalized_price_pkr",
        ),
        CheckConstraint(
            "verification_status IN ('unverified', 'verified_quote', 'cross_checked', 'verified_market_range', 'indicative', 'conflicted', 'stale')",
            name="ck_observations_verification_status",
        ),
        Index(
            "ix_observations_product_city_published",
            "product_id", "city", "published_at",
        ),
        Index(
            "ix_observations_status_published",
            "verification_status", "published_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("material_rate_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Parent data source UUID",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("material_rate_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Parent canonical product UUID",
    )
    dealer_quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("material_rate_dealer_quotes.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Linked dealer quotation UUID (RESTRICT prevents accidental deletion of quoted parent)",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Market city: Lahore, Karachi, Islamabad, Rawalpindi, etc. (null if source only provides regional quarry/basin)",
    )
    observed_price_pkr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Observed raw price in PKR",
    )
    observed_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Observed unit of measurement",
    )
    normalized_price_pkr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Price normalized to standard product measurement unit",
    )
    normalized_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Canonical standard measurement unit",
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Official publication or quotation issuance timestamp (null if undated indicative estimate)",
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Timestamp when system collected and ingested the observation",
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Specific URL or document reference for verification",
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        server_default="unverified",
        index=True,
        comment="Status: unverified, verified_quote, cross_checked, verified_market_range, indicative, conflicted, stale",
    )
    duplicate_fingerprint: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 fingerprint: SHA256(source_id + product_id + city + published_at + normalized_unit)",
    )
    background_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("background_jobs.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Associated sync background job UUID (RESTRICT preserves job lineage)",
    )
    observation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        default=dict,
        comment="Contextual metadata (e.g. delivery inclusion, brand variants, raw payload)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Creation timestamp",
    )

    # Relationships
    source: Mapped["MaterialRateSource"] = relationship("MaterialRateSource", back_populates="observations")
    product: Mapped["MaterialRateProduct"] = relationship("MaterialRateProduct", back_populates="observations")
    dealer_quote: Mapped[Optional["MaterialRateDealerQuote"]] = relationship(
        "MaterialRateDealerQuote",
        back_populates="observations",
    )
    background_job: Mapped[Optional["BackgroundJob"]] = relationship("BackgroundJob")
    verification_events: Mapped[List["MaterialRateVerificationEvent"]] = relationship(
        "MaterialRateVerificationEvent",
        back_populates="observation",
    )

    def __repr__(self) -> str:
        return f"<MaterialRateObservation(id={self.id}, city='{self.city}', price={self.normalized_price_pkr} PKR/{self.normalized_unit}, status='{self.verification_status}')>"


@event.listens_for(MaterialRateObservation, "before_update")
def _enforce_observation_immutable_update(mapper, connection, target):
    """Enforces strict append-only immutability. Updates to market observations are prohibited."""
    raise PermissionError("MaterialRateObservation is strictly append-only. Modification (UPDATE) is forbidden.")


@event.listens_for(MaterialRateObservation, "before_delete")
def _enforce_observation_immutable_delete(mapper, connection, target):
    """Enforces strict append-only immutability. Deletions of market observations are prohibited."""
    raise PermissionError("MaterialRateObservation is strictly append-only. Deletion (DELETE) is forbidden.")


# ---------------------------------------------------------------------------
# 6. Verification Events & Explainable Audit Trail
# ---------------------------------------------------------------------------

class MaterialRateVerificationEvent(Base):
    """
    Explainable Verification Decision Log.
    Records reasons, previous states, and actor references (user or system worker)
    for every status transition.
    """

    __tablename__ = "material_rate_verification_events"
    __table_args__ = (
        CheckConstraint(
            "((observation_id IS NOT NULL) OR (dealer_quote_id IS NOT NULL))",
            name="ck_verification_events_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("material_rate_observations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Audited observation UUID",
    )
    dealer_quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("material_rate_dealer_quotes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Audited dealer quotation UUID",
    )
    previous_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Prior status before review",
    )
    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Resulting status assigned",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human explanation or deterministic rule justification",
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reviewing engineer/admin UUID (null if automated system decision)",
    )
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        default=dict,
        comment="Snapshot of metrics or parameters evaluated during verification",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Audit log timestamp",
    )

    # Relationships
    observation: Mapped[Optional["MaterialRateObservation"]] = relationship(
        "MaterialRateObservation",
        back_populates="verification_events",
    )
    dealer_quote: Mapped[Optional["MaterialRateDealerQuote"]] = relationship(
        "MaterialRateDealerQuote",
        back_populates="verification_events",
    )
    actor: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<MaterialRateVerificationEvent(id={self.id}, transition='{self.previous_status}->{self.new_status}')>"


# ---------------------------------------------------------------------------
# 7. Source Execution Runs & Worker Telemetry
# ---------------------------------------------------------------------------

class MaterialRateSourceRun(Base):
    """
    Execution History of Data Collection and Synchronization Runs.
    Tracks success rates, record counts, execution latency, and error summaries.
    """

    __tablename__ = "material_rate_source_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="ck_source_runs_status",
        ),
        CheckConstraint(
            "records_discovered >= 0",
            name="ck_source_runs_discovered",
        ),
        CheckConstraint(
            "records_accepted >= 0",
            name="ck_source_runs_accepted",
        ),
        CheckConstraint(
            "records_rejected >= 0",
            name="ck_source_runs_rejected",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("material_rate_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target data source UUID",
    )
    background_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("background_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Executing background job UUID",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="running",
        server_default="running",
        comment="Run state: running, completed, failed",
    )
    records_discovered: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total raw records discovered during fetch",
    )
    records_accepted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Records normalized and saved successfully",
    )
    records_rejected: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Records rejected due to validation or duplicate fingerprint",
    )
    error_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Sanitized error description on run failure",
    )
    duration_seconds: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Total elapsed execution time in seconds",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Execution start timestamp",
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Execution finish timestamp",
    )

    # Relationships
    source: Mapped["MaterialRateSource"] = relationship("MaterialRateSource", back_populates="source_runs")
    background_job: Mapped[Optional["BackgroundJob"]] = relationship("BackgroundJob")

    def __repr__(self) -> str:
        return f"<MaterialRateSourceRun(id={self.id}, status='{self.status}', accepted={self.records_accepted})>"

