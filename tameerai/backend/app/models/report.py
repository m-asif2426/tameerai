"""
TameerAI - Engineering Consulting Report Database Model (Phase 01C.4)

Defines:
- Report: Generated formal engineering dossiers (Compliance Certifications, Contract Risk Reviews, Cost Overrun Briefings).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.compliance import ComplianceAudit
    from app.models.contract import ContractAnalysis
    from app.models.cost import BOQAnalysis


class Report(Base):
    """
    Engineering Consulting Report Model.
    Tracks comprehensive dossiers compiled from compliance audits, contract reviews, and cost analyses.
    Uses dual identification: internal UUID primary key and project-scoped public code (e.g. RPT-001).
    File paths reference private cloud/server storage keys and are never exposed directly as raw URLs.
    """

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_reports_project_code"),
        CheckConstraint(
            "category IN ('compliance', 'contract', 'cost', 'executive_comprehensive')",
            name="ck_reports_category",
        ),
        CheckConstraint(
            "status IN ('certified', 'action_required', 'overrun_alert', 'in_review', 'approved')",
            name="ck_reports_status",
        ),
        CheckConstraint(
            "page_count >= 1",
            name="ck_reports_page_count",
        ),
        CheckConstraint(
            "status NOT IN ('certified', 'approved') OR generated_at IS NOT NULL",
            name="ck_reports_generation_status",
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
        comment="Public-facing report code (e.g. RPT-001). Unique per project workspace.",
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
        comment="Author engineer user UUID",
    )
    compliance_audit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("compliance_audits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Referenced compliance audit UUID",
    )
    contract_analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("contract_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Referenced contract analysis UUID",
    )
    boq_analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("boq_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Referenced BOQ analysis UUID",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Report domain: compliance, contract, cost, executive_comprehensive",
    )
    category_label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable domain label (e.g. 'Structural & Building Code Audit')",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Report title (e.g. 'Comprehensive Structural Compliance Dossier - Rev 2')",
    )
    title_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu report title",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="in_review",
        server_default="in_review",
        comment="Approval / verification state: certified, action_required, overrun_alert, in_review, approved",
    )
    status_label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display status label (e.g. 'Action Required - Redesign Egress')",
    )
    status_label_urdu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Urdu display status label",
    )
    file_size: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="0 MB",
        server_default="0 MB",
        comment="Human-readable file size string (e.g. '4.2 MB')",
    )
    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Number of document pages in generated report",
    )
    author: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="TameerAI Engineering Intelligence",
        server_default="TameerAI Engineering Intelligence",
        comment="Publishing engineering entity or lead engineer name",
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Internal private storage key / path (never exposed directly publicly)",
    )
    executive_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Executive summary of engineering analysis",
    )
    executive_summary_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu executive summary",
    )
    key_metric: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Headline metric (e.g. 'Score: 84% — 3 Critical Non-Compliances', '+18.4% Cost Escalation')",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Safe structured report metadata (charts, parameter summaries, signature states)",
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when report compilation finished",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Record modification timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="reports",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="authored_reports",
    )
    compliance_audit: Mapped[Optional["ComplianceAudit"]] = relationship(
        "ComplianceAudit",
        back_populates="reports",
    )
    contract_analysis: Mapped[Optional["ContractAnalysis"]] = relationship(
        "ContractAnalysis",
        back_populates="reports",
    )
    boq_analysis: Mapped[Optional["BOQAnalysis"]] = relationship(
        "BOQAnalysis",
        back_populates="reports",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs:
            kwargs["status"] = "in_review"
        if "page_count" not in kwargs:
            kwargs["page_count"] = 1
        if "author" not in kwargs:
            kwargs["author"] = "TameerAI Engineering Intelligence"
        if "file_size" not in kwargs:
            kwargs["file_size"] = "0 MB"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, code='{self.code}', project_id={self.project_id}, status='{self.status}')>"

