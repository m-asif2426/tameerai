"""
TameerAI - Construction Cost Intelligence & BOQ Database Models (Phase 01C.4)

Defines:
- MaterialRate: Verified market rate observations for construction commodities across Pakistani cities.
- BOQAnalysis: Bill of Quantities evaluation header comparing baseline estimates against execution costs.
- BOQItem: Detailed schedule line items across structural phases (Substructure, Superstructure, MEP, Finishing).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.document import Document
    from app.models.report import Report
    from app.models.material_rate import MaterialRateProduct


class MaterialRate(Base):
    """
    Market Material Rate Observation Model.
    Tracks time-series wholesale and retail material rates across major Pakistani hubs (Lahore, Karachi, Islamabad).
    Rates record authoritative PKR pricing, unit bases, collection timestamps, and verifiable sources.
    """

    __tablename__ = "material_rates"
    __table_args__ = (
        CheckConstraint(
            "rate_pkr >= 0",
            name="ck_material_rates_rate_pkr_non_negative",
        ),
        CheckConstraint(
            "trend IN ('up', 'down', 'neutral')",
            name="ck_material_rates_trend",
        ),
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'stale', 'verified_quote', 'cross_checked', 'verified_market_range', 'indicative', 'conflicted')",
            name="ck_material_rates_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("material_rate_products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional link to canonical product catalog",
    )
    city: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Market jurisdiction: Lahore, Karachi, Islamabad, Peshawar, Quetta, Rawalpindi",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Material category: steel, cement, bricks, aggregates, sand, tiles, labor, general",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Standard material name (e.g. 'Deformed Steel Bars Grade 60 1/2\"')",
    )
    name_urdu: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Urdu material name (e.g. 'سٹیل سریا گریڈ 60')",
    )
    spec: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Technical ASTM / PSQCA specification",
    )
    spec_urdu: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Urdu specification summary",
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Standard measurement unit: ton, bag (50kg), 1000 bricks, cu ft, sq ft",
    )
    unit_urdu: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Urdu measurement unit",
    )
    rate_pkr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Authoritative observed price in Pakistani Rupees (PKR)",
    )
    change_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Percentage change relative to previous survey period",
    )
    trend: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="neutral",
        server_default="neutral",
        comment="Price movement direction: up, down, neutral",
    )
    primary_brands: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Representative market manufacturers (e.g. 'Mughal, Amreli, Bestway, Fauji')",
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Exact timestamp when the market quote was collected",
    )
    source_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Verifiable reporting agency (e.g. 'Pakistan Bureau of Statistics', 'C&W Dept')",
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Official reference or published bulletin link",
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        server_default="unverified",
        comment="Verification condition: verified, unverified, stale",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Database insertion timestamp",
    )

    # Relationships
    product: Mapped[Optional["MaterialRateProduct"]] = relationship(
        "MaterialRateProduct",
        back_populates="canonical_rates",
    )
    boq_items: Mapped[List["BOQItem"]] = relationship(
        "BOQItem",
        back_populates="material_rate",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "change_pct" not in kwargs:
            kwargs["change_pct"] = Decimal("0.00")
        if "trend" not in kwargs:
            kwargs["trend"] = "neutral"
        if "verification_status" not in kwargs:
            kwargs["verification_status"] = "unverified"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<MaterialRate(id={self.id}, name='{self.name}', city='{self.city}', rate_pkr={self.rate_pkr})>"


class BOQAnalysis(Base):
    """
    Bill of Quantities (BOQ) Analysis Model.
    Compares baseline tender / contract budgets against real-time estimated execution costs.
    Financial metrics use exact NUMERIC(15, 2) values; uncalculated fields remain NULL.
    """

    __tablename__ = "boq_analyses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('unprocessed', 'processing', 'completed', 'failed')",
            name="ck_boq_analyses_status",
        ),
        CheckConstraint(
            "project_budget IS NULL OR project_budget >= 0",
            name="ck_boq_analyses_project_budget_non_negative",
        ),
        CheckConstraint(
            "estimated_cost IS NULL OR estimated_cost >= 0",
            name="ck_boq_analyses_estimated_cost_non_negative",
        ),
        CheckConstraint(
            "current_cost IS NULL OR current_cost >= 0",
            name="ck_boq_analyses_current_cost_non_negative",
        ),
        CheckConstraint(
            "risk_indicator IN ('Low', 'Medium', 'High')",
            name="ck_boq_analyses_risk_indicator",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Referenced project workspace UUID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Initiating quantity surveyor UUID",
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source Excel / CSV BOQ schedule document UUID",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unprocessed",
        server_default="unprocessed",
        comment="Analysis state: unprocessed, processing, completed, failed",
    )
    project_budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        default=None,
        comment="Baseline budgeted tender cost in PKR",
    )
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        default=None,
        comment="Estimated current execution cost in PKR based on verified quantities",
    )
    current_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        default=None,
        comment="Real-time revised project cost taking into account commodity market trends",
    )
    cost_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        default=None,
        comment="Absolute cost variance in PKR (positive represents cost overrun)",
    )
    variance_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        default=None,
        comment="Percentage variance relative to baseline budget",
    )
    risk_indicator: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Low",
        server_default="Low",
        comment="Overall budget escalation risk indicator: Low, Medium, High",
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Executive cost analysis summary",
    )
    summary_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu executive cost analysis summary",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when schedule processing finished",
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
        comment="Modification timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="boq_analyses",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="initiated_boq_analyses",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="boq_analyses",
    )
    items: Mapped[List["BOQItem"]] = relationship(
        "BOQItem",
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="boq_analysis",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs:
            kwargs["status"] = "unprocessed"
        if "risk_indicator" not in kwargs:
            kwargs["risk_indicator"] = "Low"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<BOQAnalysis(id={self.id}, project_id={self.project_id}, status='{self.status}', variance={self.cost_variance})>"


class BOQItem(Base):
    """
    Bill of Quantities Schedule Item Model.
    Itemized cost entries organized by construction phase (Substructure, Superstructure, MEP, Finishing).
    Uses NUMERIC for all arithmetic to prevent binary floating-point roundoff errors.
    """

    __tablename__ = "boq_items"
    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="ck_boq_items_quantity_non_negative",
        ),
        CheckConstraint(
            "boq_base_rate >= 0",
            name="ck_boq_items_boq_base_rate_non_negative",
        ),
        CheckConstraint(
            "current_price >= 0",
            name="ck_boq_items_current_price_non_negative",
        ),
        CheckConstraint(
            "budget_amount >= 0",
            name="ck_boq_items_budget_amount_non_negative",
        ),
        CheckConstraint(
            "estimated_amount >= 0",
            name="ck_boq_items_estimated_amount_non_negative",
        ),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high')",
            name="ck_boq_items_risk_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("boq_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent BOQ analysis UUID",
    )
    material_rate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("material_rates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional matched commodity market quote UUID",
    )
    phase: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Project phase: Substructure, Superstructure, Finishing, MEP, External Works",
    )
    phase_urdu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Urdu construction phase name",
    )
    item_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Schedule line identifier (e.g. '1.02', 'BOQ-STR-04')",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full engineering description of works / materials",
    )
    description_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu engineering description",
    )
    spec: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Material specification or strength class (e.g. '1:2:4 3000 PSI')",
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unit of measurement: cu m, cu ft, ton, sq ft, bag",
    )
    unit_urdu: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Urdu measurement unit",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
        comment="Physical quantity required",
    )
    boq_base_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Contract tender unit rate in PKR",
    )
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Current market unit rate in PKR",
    )
    budget_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Authoritative baseline amount (quantity * boq_base_rate)",
    )
    estimated_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Current execution cost amount (quantity * current_price)",
    )
    overrun_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Projected cost overrun (estimated_amount - budget_amount)",
    )
    variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Percentage escalation",
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="low",
        server_default="low",
        comment="Cost escalation risk level: low, medium, high",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Item creation timestamp",
    )

    # Relationships
    analysis: Mapped["BOQAnalysis"] = relationship(
        "BOQAnalysis",
        back_populates="items",
    )
    material_rate: Mapped[Optional["MaterialRate"]] = relationship(
        "MaterialRate",
        back_populates="boq_items",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "quantity" not in kwargs:
            kwargs["quantity"] = Decimal("0.000")
        if "boq_base_rate" not in kwargs:
            kwargs["boq_base_rate"] = Decimal("0.00")
        if "current_price" not in kwargs:
            kwargs["current_price"] = Decimal("0.00")
        if "budget_amount" not in kwargs:
            kwargs["budget_amount"] = Decimal("0.00")
        if "estimated_amount" not in kwargs:
            kwargs["estimated_amount"] = Decimal("0.00")
        if "overrun_amount" not in kwargs:
            kwargs["overrun_amount"] = Decimal("0.00")
        if "variance_pct" not in kwargs:
            kwargs["variance_pct"] = Decimal("0.00")
        if "risk_level" not in kwargs:
            kwargs["risk_level"] = "low"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<BOQItem(id={self.id}, phase='{self.phase}', desc='{self.description[:20]}', budget={self.budget_amount})>"

