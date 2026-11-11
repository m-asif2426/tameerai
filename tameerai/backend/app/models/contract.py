"""
TameerAI - Contract Intelligence & Legal Risk Database Models (Phase 01C.4)

Defines:
- ContractAnalysis: Header record for FIDIC / PEC construction contract evaluation.
- ContractRiskCard: Individual liability exposure card tied to specific clauses with page references.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
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
    from app.models.document import Document
    from app.models.report import Report


class ContractAnalysis(Base):
    """
    Construction Contract Risk Assessment Model.
    Analyzes FIDIC (Red, Yellow, Silver) and Pakistan Engineering Council (PEC) standard forms
    for contractor/client liability imbalances, delay liquidated damages, and indemnities.
    Risk scores remain NULL until analysis execution completes.
    """

    __tablename__ = "contract_analyses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('unprocessed', 'processing', 'completed', 'failed')",
            name="ck_contract_analyses_status",
        ),
        CheckConstraint(
            "risk_score IS NULL OR (risk_score >= 0.00 AND risk_score <= 10.00)",
            name="ck_contract_analyses_risk_score",
        ),
        CheckConstraint(
            "risk_category IS NULL OR risk_category IN ('Critical Risk', 'Moderate Risk', 'Low Risk')",
            name="ck_contract_analyses_risk_category",
        ),
        CheckConstraint(
            "total_clauses_audited >= 0 AND flagged_clauses_count >= 0",
            name="ck_contract_analyses_clauses_non_negative",
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
        comment="Initiating legal engineer UUID",
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source contract PDF/DOCX document UUID",
    )
    contract_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Title of the agreement (e.g. 'General Conditions of Contract - DHA Mall')",
    )
    standard_format: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="FIDIC Red Book 2017 & PEC",
        server_default="FIDIC Red Book 2017 & PEC",
        comment="Benchmark standard contract template",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unprocessed",
        server_default="unprocessed",
        comment="Analysis lifecycle state: unprocessed, processing, completed, failed",
    )
    risk_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        default=None,
        comment="Overall contract risk score on 0.00 to 10.00 scale (NULL until completed)",
    )
    risk_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Summary risk categorization: Critical Risk, Moderate Risk, Low Risk",
    )
    total_clauses_audited: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total contract clauses parsed and evaluated",
    )
    flagged_clauses_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Count of non-standard or high-risk clauses identified",
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Executive legal/risk analysis summary",
    )
    summary_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu executive legal/risk analysis summary",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when analysis reached final completed state",
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
        back_populates="contract_analyses",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="initiated_contract_analyses",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="contract_analyses",
    )
    risk_cards: Mapped[List["ContractRiskCard"]] = relationship(
        "ContractRiskCard",
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="contract_analysis",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "standard_format" not in kwargs:
            kwargs["standard_format"] = "FIDIC Red Book 2017 & PEC"
        if "status" not in kwargs:
            kwargs["status"] = "unprocessed"
        if "total_clauses_audited" not in kwargs:
            kwargs["total_clauses_audited"] = 0
        if "flagged_clauses_count" not in kwargs:
            kwargs["flagged_clauses_count"] = 0
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ContractAnalysis(id={self.id}, project_id={self.project_id}, status='{self.status}', risk_score={self.risk_score})>"


class ContractRiskCard(Base):
    """
    Contract Risk Card Model.
    Tracks high/medium/low severity legal exposure flagged within specific contract clauses.
    Contains original text snippets, page numbers, impact metrics, and mitigation recommendations.
    """

    __tablename__ = "contract_risk_cards"
    __table_args__ = (
        UniqueConstraint("analysis_id", "code", name="uq_contract_risk_cards_analysis_code"),
        CheckConstraint(
            "risk_level IN ('high', 'medium', 'low')",
            name="ck_contract_risk_cards_risk_level",
        ),
        CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="ck_contract_risk_cards_page_number",
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
        comment="Public-facing risk card code (e.g. RISK-001 or risk-delay). Unique per analysis.",
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("contract_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent contract analysis UUID",
    )
    clause_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Subject title of clause (e.g. 'Extension of Time for Completion')",
    )
    clause_title_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu subject title of clause",
    )
    fidic_reference: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Benchmark standard reference (e.g. 'FIDIC Clause 8.4', 'PEC Clause 44.1')",
    )
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Exact page number in original uploaded contract file",
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Risk level severity: high, medium, low",
    )
    risk_level_label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display label (e.g. 'High Risk - Contractor Exposure')",
    )
    risk_level_label_urdu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Urdu display label",
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed explanation of legal ambiguity or commercial imbalance",
    )
    explanation_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu legal explanation",
    )
    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Practical mitigation or amendment recommendation",
    )
    recommendation_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu mitigation recommendation",
    )
    impact_metric: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Quantifiable commercial exposure metric (e.g. 'Liquidated damages capped at 10%')",
    )
    raw_clause_snippet: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Specific verbatim sentence / excerpt from the uploaded submittal document",
    )
    citation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Structured citation trace (e.g. char offsets, section numbering, OCR bbox)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Risk card creation timestamp",
    )

    # Relationships
    analysis: Mapped["ContractAnalysis"] = relationship(
        "ContractAnalysis",
        back_populates="risk_cards",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ContractRiskCard(id={self.id}, code='{self.code}', analysis_id={self.analysis_id}, level='{self.risk_level}')>"

