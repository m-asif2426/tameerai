"""
TameerAI - RAG Knowledgebase & Document Chunk Database Models (Phase 01C.5)

Defines:
- KnowledgeSource: Official regulatory, planning, contract, and engineering codices.
- DocumentChunk: Granular text units for RAG retrieval with strict global/private scope separation.
"""

import uuid
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
from sqlalchemy.sql import expression

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.document import Document


class KnowledgeSource(Base):
    """
    RAG Knowledge Source Reference Model.
    Tracks official building codes, planning bye-laws, standard contract forms, and engineering guidelines.
    Only verified, officially promulgated references are made retrievable for RAG generation.
    """

    __tablename__ = "knowledge_sources"
    __table_args__ = (
        UniqueConstraint("short_code", name="uq_knowledge_sources_short_code"),
        CheckConstraint(
            "category IN ('building_code', 'planning_regulation', 'construction_contract_standard', 'engineering_guideline', 'other_authorized_reference')",
            name="ck_knowledge_sources_category",
        ),
        CheckConstraint(
            "verification_status IN ('unverified', 'verified', 'deprecated')",
            name="ck_knowledge_sources_verification_status",
        ),
        CheckConstraint(
            "ingestion_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_knowledge_sources_ingestion_status",
        ),
        CheckConstraint(
            "language IN ('en', 'ur', 'mixed')",
            name="ck_knowledge_sources_language",
        ),
        CheckConstraint(
            "total_pages >= 0",
            name="ck_knowledge_sources_total_pages_non_negative",
        ),
        CheckConstraint(
            "edition_year IS NULL OR (edition_year >= 1900 AND edition_year <= 2100)",
            name="ck_knowledge_sources_edition_year",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Official title of regulatory codex or engineering standard",
    )
    title_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu title of regulatory codex or standard",
    )
    short_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique identifier code (e.g. PBC_2021, LDA_2020, SBCA_2020, FIDIC_RED_2017)",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Domain category: building_code, planning_regulation, construction_contract_standard, engineering_guideline, other_authorized_reference",
    )
    authority: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Promulgating body (e.g. 'Pakistan Engineering Council', 'Lahore Development Authority', 'SBCA')",
    )
    edition_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Publication or gazette notification year (e.g. 2021)",
    )
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
        server_default="1.0",
        comment="Standard edition version identifier",
    )
    jurisdiction: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Geographic jurisdiction: Federal - Pakistan, Punjab, Sindh, KPK, Balochistan, International",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
        comment="Primary codex language: en (English), ur (Urdu), mixed",
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Official publication URL or regulatory repository link",
    )
    storage_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Internal cloud/server storage key for full text PDF",
    )
    total_pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total documented pages in source volume",
    )
    effective_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date when regulation came into legal force",
    )
    provenance: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full legal provenance: gazette notification number, publisher details, copyright clearance",
    )
    is_official_regulatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="Whether this is an officially approved/promulgated standard (default false until verified)",
    )
    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unverified",
        server_default="unverified",
        index=True,
        comment="Editorial verification state: unverified, verified, deprecated",
    )
    ingestion_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Document parsing & chunking state: pending, processing, completed, failed",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Structured metadata (table of contents, chapter map, amendment history)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Source registration timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Source last modification timestamp",
    )

    # Relationships
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="knowledge_source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "category" not in kwargs:
            kwargs["category"] = "building_code"
        if "version" not in kwargs:
            kwargs["version"] = "1.0"
        if "language" not in kwargs:
            kwargs["language"] = "en"
        if "total_pages" not in kwargs:
            kwargs["total_pages"] = 0
        if "is_official_regulatory" not in kwargs:
            kwargs["is_official_regulatory"] = False
        if "verification_status" not in kwargs:
            kwargs["verification_status"] = "unverified"
        if "ingestion_status" not in kwargs:
            kwargs["ingestion_status"] = "pending"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<KnowledgeSource(id={self.id}, code='{self.short_code}', title='{self.title[:30]}', verified='{self.verification_status}')>"


class DocumentChunk(Base):
    """
    RAG Text Chunk Model.
    Stores chunked passages for semantic retrieval.
    Enforces strict global/private scope separation via database CHECK constraint:
    - Global chunks MUST reference knowledge_source_id and MUST NOT reference project/document.
    - Private chunks MUST reference project_id and document_id and MUST NOT reference knowledge_source.
    Vector embedding column is deferred until the embedding model and dimensionality are finalized.
    """

    __tablename__ = "document_chunks"
    __table_args__ = (
        CheckConstraint(
            "(knowledge_source_id IS NOT NULL AND project_id IS NULL AND document_id IS NULL) "
            "OR (knowledge_source_id IS NULL AND project_id IS NOT NULL AND document_id IS NOT NULL)",
            name="ck_document_chunks_scope",
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name="ck_document_chunks_chunk_index_non_negative",
        ),
        CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="ck_document_chunks_page_number_positive",
        ),
        CheckConstraint(
            "token_count >= 0",
            name="ck_document_chunks_token_count_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    knowledge_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Referenced global regulatory source UUID (populated ONLY for public regulatory chunks)",
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Referenced private project UUID (populated ONLY for private tenant documents)",
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Referenced private document UUID (populated ONLY for private tenant documents)",
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Ordinal position of this chunk within the parent source/document",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Passage text extracted for contextual embedding and prompt synthesis",
    )
    content_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu translation or native passage text",
    )
    chapter: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Parent chapter name or heading (e.g. 'Chapter 4: Means of Egress')",
    )
    section: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        index=True,
        comment="Specific clause or section identifier (e.g. 'Section 4.3.2.1', 'Clause 14.1')",
    )
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Exact page number in original published volume / PDF document",
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Computed token count of chunk text",
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="SHA-256 hash of chunk content for deduplication and update tracking",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Structured chunk metadata (bounding box coordinates, headings, table cells)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Chunk generation timestamp",
    )

    # Relationships
    knowledge_source: Mapped[Optional["KnowledgeSource"]] = relationship(
        "KnowledgeSource",
        back_populates="chunks",
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="document_chunks",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="chunks",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "chunk_index" not in kwargs:
            kwargs["chunk_index"] = 0
        if "token_count" not in kwargs:
            kwargs["token_count"] = 0
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        scope = f"global_source={self.knowledge_source_id}" if self.knowledge_source_id else f"proj={self.project_id},doc={self.document_id}"
        return f"<DocumentChunk(id={self.id}, idx={self.chunk_index}, {scope}, sec='{self.section}')>"

