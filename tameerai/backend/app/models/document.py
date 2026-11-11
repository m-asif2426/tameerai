"""
TameerAI - Document Metadata Database Model (Phase 01C.3)

Defines the Document model for blueprints, CAD drawings, contracts, and BOQs.
Employs dual identification: UUID primary key with project-scoped public code (e.g. DOC-01).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
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
    from app.models.compliance import ComplianceAudit, ComplianceFinding
    from app.models.contract import ContractAnalysis
    from app.models.cost import BOQAnalysis
    from app.models.knowledge import DocumentChunk


class Document(Base):
    """
    Project Document Metadata Model.
    Tracks uploaded engineering drawings, architectural blueprints, legal contracts, and BOQ schedules.
    Files are stored in private server/object storage; this table stores metadata, hashes, and parsing states.
    """

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_documents_project_code"),
        CheckConstraint(
            "document_category IN ('blueprint', 'building_code', 'contract', 'boq', 'general_project_document')",
            name="ck_documents_category",
        ),
        CheckConstraint(
            "status IN ('Verified', 'Review Required', 'Pending Analysis')",
            name="ck_documents_status",
        ),
        CheckConstraint(
            "analysis_status IN ('unprocessed', 'processing', 'completed', 'failed')",
            name="ck_documents_analysis_status",
        ),
        CheckConstraint(
            "file_size_bytes >= 0",
            name="ck_documents_file_size_bytes",
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
        comment="Public document code (e.g. DOC-01). Unique per project workspace.",
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
        comment="Uploader user UUID (RESTRICT prevents deleting user who authored legal submittals)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original filename (e.g. 'DHA-Plaza-Structural-Drawings-Rev4.dwg')",
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Human-readable file type: 'CAD Drawing', 'Architectural Blueprint', 'Legal Contract', etc.",
    )
    document_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="general_project_document",
        server_default="general_project_document",
        comment="Standardized domain category: blueprint, building_code, contract, boq, general_project_document",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="Exact file size in bytes",
    )
    file_size_human: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="0 KB",
        server_default="0 KB",
        comment="Human-readable file size string (e.g. '42.5 MB')",
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Internal private storage key / path (never exposed publicly)",
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME content type (e.g. 'application/pdf', 'image/vnd.dwg')",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Pending Analysis",
        server_default="Pending Analysis",
        comment="Review/verification status: 'Verified', 'Review Required', 'Pending Analysis'",
    )
    analysis_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unprocessed",
        server_default="unprocessed",
        comment="AI analysis pipeline state: 'unprocessed', 'processing', 'completed', 'failed'",
    )
    uploaded_by: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Cached display name of uploader at time of upload (e.g. 'Engr. Tariq')",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Safe document metadata (e.g. page counts, CAD layer names, sheet dimensions)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Upload creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last status update timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="documents",
    )
    uploader: Mapped["User"] = relationship(
        "User",
        back_populates="uploaded_documents",
    )
    compliance_audits: Mapped[List["ComplianceAudit"]] = relationship(
        "ComplianceAudit",
        back_populates="document",
        passive_deletes=True,
    )
    compliance_findings: Mapped[List["ComplianceFinding"]] = relationship(
        "ComplianceFinding",
        back_populates="document",
        passive_deletes=True,
    )
    contract_analyses: Mapped[List["ContractAnalysis"]] = relationship(
        "ContractAnalysis",
        back_populates="document",
        passive_deletes=True,
    )
    boq_analyses: Mapped[List["BOQAnalysis"]] = relationship(
        "BOQAnalysis",
        back_populates="document",
        passive_deletes=True,
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "document_category" not in kwargs:
            kwargs["document_category"] = "general_project_document"
        if "file_size_bytes" not in kwargs:
            kwargs["file_size_bytes"] = 0
        if "file_size_human" not in kwargs:
            kwargs["file_size_human"] = "0 KB"
        if "status" not in kwargs:
            kwargs["status"] = "Pending Analysis"
        if "analysis_status" not in kwargs:
            kwargs["analysis_status"] = "unprocessed"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, code='{self.code}', project_id={self.project_id}, name='{self.name}')>"

