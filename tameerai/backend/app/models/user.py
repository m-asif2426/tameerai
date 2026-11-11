"""
TameerAI - Identity Database Models (Phase 01C.2)

Defines SQLAlchemy 2.0 declarative models for:
- User: Core user accounts with profile and engineering credentials.
- UserSettings: Strict 1:1 user preferences for notifications and AI behavior.
- UserSession: Active device sessions and hashed refresh token tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
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
    from app.models.project import Project, ProjectMember
    from app.models.document import Document
    from app.models.compliance import ComplianceAudit
    from app.models.contract import ContractAnalysis
    from app.models.cost import BOQAnalysis
    from app.models.report import Report
    from app.models.chat import ChatSession


class User(Base):
    """
    User Account Model.
    Represents authenticated users (engineers, contractors, architects, firms)
    in the TameerAI ecosystem.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free UUID primary key",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Unique user login email",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt-hashed password string. Never plaintext.",
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Full name of user (matches frontend Profile)",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="engineer",
        server_default="engineer",
        comment="Professional persona: engineer, contractor, architect, company",
    )
    company: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Company / Engineering consultancy firm name",
    )
    pec_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Pakistan Engineering Council (PEC) registration number",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Contact phone number (e.g. +92 300 1234567)",
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Lahore",
        server_default="Lahore",
        comment="Primary operating city / municipal jurisdiction",
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Professional biographical overview",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        comment="Account activation status",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="Email / PEC credentials verification status",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Account creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last profile modification timestamp",
    )

    # 1:1 relationship with UserSettings
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 1:N relationship with UserSession
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 1:N relationship with Project (as owner)
    owned_projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="owner",
        passive_deletes=True,
    )

    # 1:N relationship with ProjectMember (as member)
    project_memberships: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 1:N relationship with Document (as uploader)
    uploaded_documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="uploader",
        passive_deletes=True,
    )

    # 1:N relationship with ComplianceAudit (as initiator)
    initiated_compliance_audits: Mapped[List["ComplianceAudit"]] = relationship(
        "ComplianceAudit",
        back_populates="user",
        passive_deletes=True,
    )

    # 1:N relationship with ContractAnalysis (as initiator)
    initiated_contract_analyses: Mapped[List["ContractAnalysis"]] = relationship(
        "ContractAnalysis",
        back_populates="user",
        passive_deletes=True,
    )

    # 1:N relationship with BOQAnalysis (as initiator)
    initiated_boq_analyses: Mapped[List["BOQAnalysis"]] = relationship(
        "BOQAnalysis",
        back_populates="user",
        passive_deletes=True,
    )

    # 1:N relationship with Report (as author)
    authored_reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="user",
        passive_deletes=True,
    )

    # 1:N relationship with ChatSession (as user/initiator)
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "role" not in kwargs:
            kwargs["role"] = "engineer"
        if "city" not in kwargs:
            kwargs["city"] = "Lahore"
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        if "is_verified" not in kwargs:
            kwargs["is_verified"] = False
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class UserSettings(Base):
    """
    User Settings & Preferences Model.
    Enforces a strict 1:1 relationship with User. Stores notification flags,
    language preferences, and AI behavior parameters.
    """

    __tablename__ = "user_settings"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_settings_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Primary key",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key referencing users.id (Strict 1:1)",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
        comment="Preferred UI language: 'en' or 'ur'",
    )
    theme: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="system",
        server_default="system",
        comment="Preferred UI theme: 'light', 'dark', 'system'",
    )
    pbc_violations_alert: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        comment="Alert on Pakistan Building Code violations",
    )
    fidic_risks_alert: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        comment="Alert on FIDIC contractual liabilities",
    )
    price_spikes_alert: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        comment="Alert on construction material price fluctuations",
    )
    weekly_digest_alert: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="Receive weekly compliance summary digest",
    )
    whatsapp_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        comment="Receive critical site alerts via WhatsApp",
    )
    ai_strictness: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="strict",
        server_default="strict",
        comment="AI compliance strictness: 'strict' or 'consultative'",
    )
    fidic_threshold: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="8",
        server_default="8",
        comment="FIDIC risk scoring threshold: '6', '8', '9'",
    )
    auto_citations: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        comment="Automatically attach legal/code citations in AI answers",
    )
    market_region: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="lahore",
        server_default="lahore",
        comment="Commodity price reference market: 'lahore', 'karachi', 'islamabad'",
    )
    ai_tone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="professional",
        server_default="professional",
        comment="AI response tone: 'professional', 'practical', 'legal'",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Settings record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Settings modification timestamp",
    )

    # 1:1 relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="settings",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "language" not in kwargs:
            kwargs["language"] = "en"
        if "theme" not in kwargs:
            kwargs["theme"] = "system"
        if "pbc_violations_alert" not in kwargs:
            kwargs["pbc_violations_alert"] = True
        if "fidic_risks_alert" not in kwargs:
            kwargs["fidic_risks_alert"] = True
        if "price_spikes_alert" not in kwargs:
            kwargs["price_spikes_alert"] = True
        if "weekly_digest_alert" not in kwargs:
            kwargs["weekly_digest_alert"] = False
        if "whatsapp_alerts" not in kwargs:
            kwargs["whatsapp_alerts"] = True
        if "ai_strictness" not in kwargs:
            kwargs["ai_strictness"] = "strict"
        if "fidic_threshold" not in kwargs:
            kwargs["fidic_threshold"] = "8"
        if "auto_citations" not in kwargs:
            kwargs["auto_citations"] = True
        if "market_region" not in kwargs:
            kwargs["market_region"] = "lahore"
        if "ai_tone" not in kwargs:
            kwargs["ai_tone"] = "professional"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<UserSettings(id={self.id}, user_id={self.user_id}, language='{self.language}')>"


class UserSession(Base):
    """
    User Device Session Model.
    Tracks active logins, client metadata, and hashed refresh token identifiers
    to support secure session management and token revocation.
    """

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Session UUID primary key",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="Foreign key referencing users.id",
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
        comment="Cryptographic hash of refresh token. Raw token is never stored.",
    )
    device_info: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Client device / browser string (e.g. 'Chrome 128 on Windows 11')",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Client IP address at session initiation",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Estimated geographic location (e.g. 'Lahore, Pakistan')",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="Revocation flag for instant logout / session invalidation",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Refresh token expiration timestamp",
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Timestamp of latest activity",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Session creation timestamp",
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "is_revoked" not in kwargs:
            kwargs["is_revoked"] = False
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
