"""
TameerAI - Project Workspace & Collaboration Models (Phase 01C.3)

Defines SQLAlchemy 2.0 declarative models for:
- Project: Commercial & residential construction workspaces (Dual ID: UUID PK + tenant-scoped code).
- ProjectMember: Collaborative multi-user team access & role assignment.
- ProjectActivity: Append-only audit trail and activity logging.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
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
    from app.models.document import Document
    from app.models.compliance import ComplianceAudit, ComplianceFinding
    from app.models.contract import ContractAnalysis
    from app.models.cost import BOQAnalysis
    from app.models.report import Report
    from app.models.chat import ChatSession
    from app.models.knowledge import DocumentChunk


class Project(Base):
    """
    Project Workspace Model.
    Represents an active construction site, commercial plaza, or residential development.
    Uses an internal UUID primary key and a tenant-scoped public human-readable code (e.g. PRJ-001).
    Authoritative financial values are stored in raw PKR (NUMERIC(15, 2)) with non-negative constraints.
    Crore conversions are calculated dynamically to avoid redundant state.
    """

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_projects_user_code"),
        CheckConstraint("budget_raw >= 0", name="ck_projects_budget_raw_non_negative"),
        CheckConstraint("spent_raw >= 0", name="ck_projects_spent_raw_non_negative"),
        CheckConstraint(
            "compliance_score IS NULL OR (compliance_score >= 0 AND compliance_score <= 100)",
            name="ck_projects_compliance_score_range",
        ),
        CheckConstraint(
            "status IN ('Under Analysis', 'Active', 'Planning', 'Completed')",
            name="ck_projects_status",
        ),
        CheckConstraint(
            "risk IN ('Low', 'Medium', 'High')",
            name="ck_projects_risk",
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
        comment="Public-facing project code (e.g. PRJ-001). Unique per owner.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Owner user UUID (RESTRICT prevents accidental deletion of active commercial projects)",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="English project name",
    )
    name_urdu: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Urdu project name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed engineering scope / description",
    )
    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Site address or sector location",
    )
    location_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu site location",
    )
    city: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Lahore",
        server_default="Lahore",
        index=True,
        comment="Pakistani city jurisdiction (Lahore, Karachi, Islamabad)",
    )
    city_urdu: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="لاہور",
        server_default="لاہور",
        comment="Urdu city label",
    )
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Commercial",
        server_default="Commercial",
        comment="Building typology (e.g. Commercial G+12, Residential Villa)",
    )
    type_urdu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Urdu building typology",
    )

    # Single Authoritative Financial State in exact raw PKR (NUMERIC(15, 2))
    budget_raw: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Authoritative raw budget in PKR (e.g. 120,000,000.00)",
    )
    spent_raw: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Authoritative spent amount in raw PKR",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Planning",
        server_default="Planning",
        index=True,
        comment="Lifecycle status: Under Analysis, Active, Planning, Completed",
    )
    status_urdu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="منصوبہ بندی (Planning)",
        server_default="منصوبہ بندی (Planning)",
        comment="Urdu status display string",
    )
    risk: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Low",
        server_default="Low",
        comment="Overall risk level: Low, Medium, High",
    )
    risk_urdu: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="کم (Low)",
        server_default="کم (Low)",
        comment="Urdu risk display string",
    )

    # Compliance score: Nullable initially (NULL represents unassessed project; no false 100% claim)
    compliance_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        server_default=None,
        comment="Current building-code compliance score (0-100 or NULL if unassessed)",
    )

    floors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Number of storeys/floors",
    )
    area_sqft: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="N/A",
        server_default="N/A",
        comment="Total covered area (e.g. '45,000 sq ft')",
    )
    engineer: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Lead engineer or contractor name",
    )

    # Governing authority: Nullable without false city-specific defaults
    governing_authority: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        default=None,
        server_default=None,
        comment="Jurisdictional building authority (LDA, CDA, SBCA, etc.)",
    )

    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Site mobilization / construction start date",
    )
    expected_completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Target handover / completion date",
    )
    handover_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Display handover date string (e.g. 'December 2024')",
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
        comment="Last modification timestamp",
    )

    # Dynamic Crore Properties (Derived cleanly in Python without DB state redundancy)
    @property
    def budget_crore(self) -> Decimal:
        """Dynamically computes Crore value (1 Crore = 10 Million PKR). Truncates without round-up to avoid phantom money."""
        if self.budget_raw is None:
            return Decimal("0.0000")
        return (Decimal(str(self.budget_raw)) / Decimal("10000000")).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)

    @property
    def spent_crore(self) -> Decimal:
        """Dynamically computes Crore value (1 Crore = 10 Million PKR). Truncates without round-up to avoid phantom money."""
        if self.spent_raw is None:
            return Decimal("0.0000")
        return (Decimal(str(self.spent_raw)) / Decimal("10000000")).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_projects",
    )
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    activities: Mapped[List["ProjectActivity"]] = relationship(
        "ProjectActivity",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    compliance_audits: Mapped[List["ComplianceAudit"]] = relationship(
        "ComplianceAudit",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    compliance_findings: Mapped[List["ComplianceFinding"]] = relationship(
        "ComplianceFinding",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    contract_analyses: Mapped[List["ContractAnalysis"]] = relationship(
        "ContractAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    boq_analyses: Mapped[List["BOQAnalysis"]] = relationship(
        "BOQAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="project",
        passive_deletes=True,
    )
    document_chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "city" not in kwargs:
            kwargs["city"] = "Lahore"
        if "city_urdu" not in kwargs:
            kwargs["city_urdu"] = "لاہور"
        if "type" not in kwargs:
            kwargs["type"] = "Commercial"
        if "status" not in kwargs:
            kwargs["status"] = "Planning"
        if "status_urdu" not in kwargs:
            kwargs["status_urdu"] = "منصوبہ بندی (Planning)"
        if "risk" not in kwargs:
            kwargs["risk"] = "Low"
        if "risk_urdu" not in kwargs:
            kwargs["risk_urdu"] = "کم (Low)"
        if "floors" not in kwargs:
            kwargs["floors"] = 1
        if "area_sqft" not in kwargs:
            kwargs["area_sqft"] = "N/A"

        # Handle financial conversions if budget_crore is passed
        if "budget_raw" not in kwargs:
            if "budget_crore" in kwargs and kwargs["budget_crore"] is not None:
                kwargs["budget_raw"] = (Decimal(str(kwargs["budget_crore"])) * Decimal("10000000")).quantize(Decimal("0.01"))
            else:
                kwargs["budget_raw"] = Decimal("0.00")
        else:
            kwargs["budget_raw"] = Decimal(str(kwargs["budget_raw"])).quantize(Decimal("0.01"))

        if "spent_raw" not in kwargs:
            if "spent_crore" in kwargs and kwargs["spent_crore"] is not None:
                kwargs["spent_raw"] = (Decimal(str(kwargs["spent_crore"])) * Decimal("10000000")).quantize(Decimal("0.01"))
            else:
                kwargs["spent_raw"] = Decimal("0.00")
        else:
            kwargs["spent_raw"] = Decimal(str(kwargs["spent_raw"])).quantize(Decimal("0.01"))

        kwargs.pop("budget_crore", None)
        kwargs.pop("spent_crore", None)

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, code='{self.code}', name='{self.name}', city='{self.city}')>"


class ProjectMember(Base):
    """
    Project Collaborative Membership Model.
    Connects secondary team members (Lead Engineers, Architects, Contractors, Viewers)
    to a project workspace.
    The primary project creator is recorded authoritatively in projects.user_id.
    Collaborative membership roles are strictly restricted to non-owner collaborator roles.
    """

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
        CheckConstraint(
            "role IN ('lead_engineer', 'architect', 'contractor', 'viewer')",
            name="ck_project_members_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Membership record primary key",
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Referenced project UUID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Collaborating user UUID",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="viewer",
        server_default="viewer",
        comment="Workspace role: lead_engineer, architect, contractor, viewer",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Membership grant timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="project_memberships",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "role" not in kwargs:
            kwargs["role"] = "viewer"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"


class ProjectActivity(Base):
    """
    Project Activity Audit Trail Model.
    Maintains an append-only audit trail and event log of actions performed within the workspace.
    When a member leaves or an account is deactivated, historical entries are preserved
    via ON DELETE SET NULL on user_id with actor_name cached.
    """

    __tablename__ = "project_activities"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('compliance', 'contract', 'cost', 'upload', 'general')",
            name="ck_project_activities_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Activity event primary key",
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Referenced project UUID",
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Actor user UUID (SET NULL preserves audit history if user is deleted)",
    )
    actor_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Cached actor display name at event occurrence (e.g. 'Engr. Tariq')",
    )
    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="English action description",
    )
    action_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu action description",
    )
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="upload",
        server_default="upload",
        comment="Category: compliance, contract, cost, upload, general",
    )
    detail: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed activity log or diff snippet",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Safe structured event parameters (never stores credentials or raw binaries)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Event occurrence timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="activities",
    )
    actor: Mapped[Optional["User"]] = relationship(
        "User",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "activity_type" not in kwargs:
            kwargs["activity_type"] = "upload"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ProjectActivity(id={self.id}, project_id={self.project_id}, action='{self.action}')>"
