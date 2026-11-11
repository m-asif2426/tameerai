"""
TameerAI - Compliance & Building Code Audit Database Models (Phase 01C.4)

Defines:
- ComplianceAudit: Audit header record for project architectural / structural evaluations.
- ComplianceFinding: Detailed rule verification finding with CAD sheet pin coordinates.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.document import Document
    from app.models.report import Report


class ComplianceAudit(Base):
    """
    Project Building Code & Regulatory Audit Model.
    Tracks evaluation runs against the Pakistan Building Code (PBC 2021) and local authorities.
    Compliance scores remain NULL until assessment is performed; never default to 100%.
    """

    __tablename__ = "compliance_audits"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed')",
            name="ck_compliance_audits_status",
        ),
        CheckConstraint(
            "overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)",
            name="ck_compliance_audits_overall_score",
        ),
        CheckConstraint(
            "total_checks >= 0 AND passed_count >= 0 AND warning_count >= 0 AND violation_count >= 0",
            name="ck_compliance_audits_counts_non_negative",
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
        comment="Initiating engineer user UUID",
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source drawing / blueprint document UUID (SET NULL preserves audit if file record is removed)",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Audit status: pending, in_progress, completed, failed",
    )
    overall_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="Calculated compliance score (0-100). NULL until audit execution completes.",
    )
    governing_code: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        default=None,
        comment="Regulatory standard evaluated against (e.g. PBC 2021, LDA 2019, SBCA 2020)",
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Executive audit findings summary",
    )
    summary_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu executive audit findings summary",
    )
    total_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total rule checks evaluated",
    )
    passed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total checks passed",
    )
    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total advisory warnings flagged",
    )
    violation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total regulatory violations flagged",
    )
    assessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when audit rule processing was finalized",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Audit creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Audit modification timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="compliance_audits",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="initiated_compliance_audits",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="compliance_audits",
    )
    findings: Mapped[List["ComplianceFinding"]] = relationship(
        "ComplianceFinding",
        back_populates="audit",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="compliance_audit",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs:
            kwargs["status"] = "pending"
        if "total_checks" not in kwargs:
            kwargs["total_checks"] = 0
        if "passed_count" not in kwargs:
            kwargs["passed_count"] = 0
        if "warning_count" not in kwargs:
            kwargs["warning_count"] = 0
        if "violation_count" not in kwargs:
            kwargs["violation_count"] = 0
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ComplianceAudit(id={self.id}, project_id={self.project_id}, status='{self.status}', score={self.overall_score})>"


class ComplianceFinding(Base):
    """
    Compliance Rule Finding Model.
    Pinpoints architectural / structural deficiencies on CAD drawings or BIM coordinates.
    Stores exact regulatory citation details, non-fabricated remedies, and localized text.
    """

    __tablename__ = "compliance_findings"
    __table_args__ = (
        UniqueConstraint("audit_id", "code", name="uq_compliance_findings_audit_code"),
        CheckConstraint(
            "category IN ('egress', 'structural', 'zoning', 'fire')",
            name="ck_compliance_findings_category",
        ),
        CheckConstraint(
            "status IN ('violation', 'warning', 'passed')",
            name="ck_compliance_findings_status",
        ),
        CheckConstraint(
            "coordinate_space IN ('normalized_percentage', 'sheet_mm', 'pixel')",
            name="ck_compliance_findings_coordinate_space",
        ),
        CheckConstraint(
            "(pin_x IS NULL AND pin_y IS NULL) OR ("
            "pin_x IS NOT NULL AND pin_y IS NOT NULL "
            "AND pin_x >= 0 AND pin_y >= 0 "
            "AND (coordinate_space != 'normalized_percentage' OR (pin_x <= 100 AND pin_y <= 100)))",
            name="ck_compliance_findings_pin_coords",
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
        nullable=False,
        index=True,
        comment="Public-facing finding code (e.g. FIND-001 or RULE-01). Unique per audit.",
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("compliance_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent compliance audit UUID",
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Direct project reference for tenant isolation enforcement",
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Specific CAD/drawing document pinned",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Domain category: egress, structural, zoning, fire",
    )
    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category display name (e.g. 'Means of Egress')",
    )
    category_name_urdu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Urdu category display name",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Finding rule title (e.g. 'Corridor Width Deficit')",
    )
    title_urdu: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Urdu finding rule title",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Finding status: violation, warning, passed",
    )
    required_value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Mandated regulatory metric (e.g. '2.40 m min clear width')",
    )
    current_value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Observed architectural plan metric (e.g. '1.85 m')",
    )
    variance: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Delta metric (e.g. '-0.55 m (-23%)')",
    )
    reference_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Governing code codex (e.g. 'PBC 2021', 'LDA Building Byelaws 2019')",
    )
    reference_clause: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Exact section / clause citation (e.g. 'Chapter 4, Section 4.3.2.1')",
    )
    location_grid: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Architectural grid coordinate / floor (e.g. 'Grid C-4, Level 2')",
    )
    sheet_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Drawing sheet identifier (e.g. 'A-102')",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed technical description of the deficiency",
    )
    description_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu technical description of the deficiency",
    )
    remedy: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Engineering remedy or architectural correction",
    )
    remedy_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu engineering remedy",
    )
    pin_x: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Horizontal coordinate of drawing annotation pin",
    )
    pin_y: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Vertical coordinate of drawing annotation pin",
    )
    coordinate_space: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="normalized_percentage",
        server_default="normalized_percentage",
        comment="Coordinate system semantics: normalized_percentage (0-100), sheet_mm, pixel",
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="Status flag indicating architectural rectification",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Finding creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Finding last update timestamp",
    )

    # Relationships
    audit: Mapped["ComplianceAudit"] = relationship(
        "ComplianceAudit",
        back_populates="findings",
    )
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="compliance_findings",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="compliance_findings",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "coordinate_space" not in kwargs:
            kwargs["coordinate_space"] = "normalized_percentage"
        if "is_resolved" not in kwargs:
            kwargs["is_resolved"] = False
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ComplianceFinding(id={self.id}, code='{self.code}', audit_id={self.audit_id}, status='{self.status}')>"

