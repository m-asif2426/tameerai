"""
TameerAI - Pakistan Statutory Regulatory Knowledge Base Models (Phase 03.3)

Defines:
- RegulatoryAuthority: Official promulgating bodies (PEC, BCP_FED, LDA, SBCA, CDA, etc.).
- RegulatoryDocument: Construction acts, building codes, zoning regulations, bye-laws.
- RegulatoryDocumentVersion: Immutable, version-aware editions and historical revisions.
- RegulatoryClause: Granular legal clauses, sections, tables, formulas, and schedules.
- RegulatoryAmendment: Gazette-notified amendments modifying base document clauses.
- RegulatoryIngestionJob: Traceable audit records of document parsing and ingestion runs.
- RegulatoryReviewRecord: Attributable editorial and legal verification reviews.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.sql import expression

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RegulatoryAuthority(Base):
    """
    Promulgating regulatory authority in Pakistan's construction ecosystem.
    Tracks official jurisdiction, geographic boundaries, credibility tier, and publication channels.
    """

    __tablename__ = "regulatory_authorities"
    __table_args__ = (
        UniqueConstraint("code", name="uq_regulatory_authorities_code"),
        CheckConstraint(
            "jurisdiction_level IN ('federal', 'provincial', 'municipal', 'special_authority')",
            name="ck_regulatory_authorities_jurisdiction_level",
        ),
        CheckConstraint(
            "credibility_tier IN ('tier_a_statutory', 'tier_b_official_regulatory', 'tier_c_recognized_technical', 'tier_d_secondary')",
            name="ck_regulatory_authorities_credibility_tier",
        ),
        CheckConstraint(
            "verification_status IN ('verified', 'discovered', 'unverified')",
            name="ck_regulatory_authorities_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique authority mnemonic (e.g. PEC, BCP_FED, LDA, SBCA, CDA, RDA, FDA, PSQCA)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full legal name of the authority in English",
    )
    name_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Official authority name in Urdu script",
    )
    jurisdiction_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="Administrative scale: federal, provincial, municipal, special_authority",
    )
    province: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Province/Territory: Punjab, Sindh, ICT, Khyber Pakhtunkhwa, Balochistan",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Primary municipal seat (e.g. Lahore, Karachi, Islamabad, Rawalpindi, Peshawar, Quetta)",
    )
    official_website: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Primary official website URL",
    )
    regulatory_domain: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Domain responsibility: structural_and_licensing, planning_and_zoning, seismic_and_safety, national_standards",
    )
    publication_channels: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Structured list of official gazettes, websites, and statutory repositories",
    )
    credibility_tier: Mapped[str] = mapped_column(
        String(35),
        nullable=False,
        default="tier_b_official_regulatory",
        server_default="tier_b_official_regulatory",
        comment="Source credibility hierarchy: tier_a_statutory, tier_b_official_regulatory, tier_c_recognized_technical, tier_d_secondary",
    )
    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="discovered",
        server_default="discovered",
        index=True,
        comment="Verification state: verified, discovered, unverified",
    )
    last_discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    documents: Mapped[List["RegulatoryDocument"]] = relationship(
        "RegulatoryDocument",
        back_populates="authority",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "jurisdiction_level" not in kwargs:
            kwargs["jurisdiction_level"] = "provincial"
        if "credibility_tier" not in kwargs:
            kwargs["credibility_tier"] = "tier_b_official_regulatory"
        if "verification_status" not in kwargs:
            kwargs["verification_status"] = "discovered"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<RegulatoryAuthority(code='{self.code}', name='{self.name[:30]}', tier='{self.credibility_tier}')>"


class RegulatoryDocument(Base):
    """
    Statutory construction document, building code, or zoning regulation.
    Parent container for immutable editions and versions.
    """

    __tablename__ = "regulatory_documents"
    __table_args__ = (
        UniqueConstraint("document_code", name="uq_regulatory_documents_code"),
        CheckConstraint(
            "document_category IN ('building_code', 'zoning_regulation', 'act_legislation', 'bye_law', 'technical_standard', 'guideline')",
            name="ck_regulatory_documents_category",
        ),
        CheckConstraint(
            "legal_instrument_type IN ('statutory_act', 'gazette_notification', 'authority_regulations', 'standard_specification', 'advisory_guideline')",
            name="ck_regulatory_documents_instrument_type",
        ),
        CheckConstraint(
            "legal_force_status IN ('legally_binding', 'mandatory_notified', 'adopted_standard', 'guideline_only', 'draft_non_binding')",
            name="ck_regulatory_documents_legal_force",
        ),
        CheckConstraint(
            "status IN ('DISCOVERED', 'SOURCE_VERIFIED', 'ACQUIRED', 'INGESTED', 'PARSED', 'REVIEW_REQUIRED', 'PUBLISHED', 'SUPERSEDED', 'WITHDRAWN', 'REJECTED')",
            name="ck_regulatory_documents_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    authority_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("regulatory_authorities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Canonical document code (e.g. BCP-SP-2007, LDA-BZR-2020, SBCA-KBTPR-2002, CDA-BR-2020, PEC-ACT-1976)",
    )
    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="Official promulgated title of the regulation",
    )
    title_urdu: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="Urdu title of the regulation",
    )
    official_document_number: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Statutory notification, gazette, or ordinance number (e.g. Act No. V of 1976, Notification No. SO(D-II)1-12/2019)",
    )
    document_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: building_code, zoning_regulation, act_legislation, bye_law, technical_standard, guideline",
    )
    legal_instrument_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="statutory_act, gazette_notification, authority_regulations, standard_specification, advisory_guideline",
    )
    legal_force_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="mandatory_notified",
        server_default="mandatory_notified",
        index=True,
        comment="Legal force: legally_binding, mandatory_notified, adopted_standard, guideline_only, draft_non_binding",
    )
    jurisdiction_country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Pakistan",
        server_default="Pakistan",
    )
    jurisdiction_province: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Province/Territory: Punjab, Sindh, ICT, Khyber Pakhtunkhwa, Balochistan, or NULL for federal",
    )
    jurisdiction_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Applicable city (e.g. Lahore, Karachi, Islamabad, or NULL for province-wide/national)",
    )
    applicable_districts: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="List of specific districts where regulation is in legal force",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DISCOVERED",
        server_default="DISCOVERED",
        index=True,
        comment="Lifecycle status: DISCOVERED, SOURCE_VERIFIED, ACQUIRED, INGESTED, PARSED, REVIEW_REQUIRED, PUBLISHED, SUPERSEDED, WITHDRAWN, REJECTED",
    )
    superseded_by_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("regulatory_documents.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to document that formally supersedes this regulation",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    authority: Mapped["RegulatoryAuthority"] = relationship(
        "RegulatoryAuthority",
        back_populates="documents",
    )
    versions: Mapped[List["RegulatoryDocumentVersion"]] = relationship(
        "RegulatoryDocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RegulatoryDocumentVersion.created_at.desc()",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "jurisdiction_country" not in kwargs:
            kwargs["jurisdiction_country"] = "Pakistan"
        if "legal_force_status" not in kwargs:
            kwargs["legal_force_status"] = "mandatory_notified"
        if "status" not in kwargs:
            kwargs["status"] = "DISCOVERED"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<RegulatoryDocument(code='{self.document_code}', title='{self.title[:30]}', status='{self.status}')>"


class RegulatoryDocumentVersion(Base):
    """
    Immutable version of a regulatory codex.
    Never silently overwritten. Preserves historical applicability and exact effective dates.
    """

    __tablename__ = "regulatory_document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_label", name="uq_regulatory_versions_doc_label"),
        CheckConstraint("total_pages >= 0", name="ck_regulatory_versions_total_pages_non_negative"),
        CheckConstraint("file_size_bytes IS NULL OR file_size_bytes >= 0", name="ck_regulatory_versions_file_size_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("regulatory_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Version string (e.g. '2007', '2020-Original', '2020-Amended-2023')",
    )
    edition: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Edition text (e.g. 'First Edition', 'Revised 2020 Edition')",
    )
    publication_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date published by the authority or printing corporation",
    )
    notification_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date published in the official provincial or federal gazette",
    )
    effective_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Date when this regulatory version entered into legal effect",
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date when this version was repealed, replaced, or expired",
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        index=True,
        comment="Whether this version is currently in legal force (False if superseded)",
    )
    superseded_by_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("regulatory_document_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Private server/cloud storage key for original document file",
    )
    official_source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Official authority URL from which document was acquired",
    )
    source_file_sha256: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Cryptographic SHA-256 fingerprint of the acquired source binary",
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Original binary file size in bytes",
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="application/pdf",
        server_default="application/pdf",
    )
    total_pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
    )
    provenance_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Statutory provenance metadata, publisher attribution, gazette issue",
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verification evidence and legal vetting remarks",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    document: Mapped["RegulatoryDocument"] = relationship(
        "RegulatoryDocument",
        back_populates="versions",
    )
    clauses: Mapped[List["RegulatoryClause"]] = relationship(
        "RegulatoryClause",
        back_populates="version",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RegulatoryClause.page_start.asc(), RegulatoryClause.clause_number.asc()",
    )
    amendments: Mapped[List["RegulatoryAmendment"]] = relationship(
        "RegulatoryAmendment",
        back_populates="base_version",
        foreign_keys="RegulatoryAmendment.base_version_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "version_label" not in kwargs:
            kwargs["version_label"] = "1.0"
        if "is_current" not in kwargs:
            kwargs["is_current"] = True
        if "total_pages" not in kwargs:
            kwargs["total_pages"] = 0
        if "language" not in kwargs:
            kwargs["language"] = "en"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<RegulatoryDocumentVersion(id={self.id}, doc_id={self.document_id}, v='{self.version_label}', current={self.is_current})>"


class RegulatoryClause(Base):
    """
    Granular, verifiable statutory clause, section, formula, or table.
    Retains page-level traceability, chapter hierarchy, original text, and normalized text.
    """

    __tablename__ = "regulatory_clauses"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('text', 'table', 'formula', 'figure_caption', 'annexure', 'schedule', 'definition')",
            name="ck_regulatory_clauses_content_type",
        ),
        CheckConstraint(
            "extraction_method IN ('native_pdf', 'docx_xml', 'structured_text', 'ocr')",
            name="ck_regulatory_clauses_extraction_method",
        ),
        CheckConstraint(
            "legal_significance IN ('mandatory_requirement', 'prohibition', 'conditional_exception', 'procedural_step', 'technical_formula', 'definition', 'guideline')",
            name="ck_regulatory_clauses_legal_significance",
        ),
        CheckConstraint(
            "review_status IN ('unreviewed', 'reviewed', 'flagged_uncertain')",
            name="ck_regulatory_clauses_review_status",
        ),
        CheckConstraint("page_start >= 1", name="ck_regulatory_clauses_page_start_positive"),
        CheckConstraint("page_end >= page_start", name="ck_regulatory_clauses_page_end_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("regulatory_document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Chapter reference (e.g. 'Chapter 4', 'Part II')",
    )
    chapter_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Official title of the chapter",
    )
    section_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Section reference (e.g. 'Section 15', '4.2')",
    )
    section_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Section heading",
    )
    clause_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Exact statutory clause reference (e.g. '4.2.1', 'Section 15(1)(a)', 'Table 4.3')",
    )
    clause_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Specific title or subject of clause",
    )
    subclause_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Subclause or paragraph notation (e.g. '(i)', '(b)')",
    )
    page_start: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Document physical page where clause begins",
    )
    page_end: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Document physical page where clause concludes",
    )
    original_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Verbatim text extracted from official source",
    )
    normalized_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Cleaned, normalized text optimized for lexical and semantic retrieval",
    )
    content_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="text",
        server_default="text",
        comment="Content format: text, table, formula, figure_caption, annexure, schedule, definition",
    )
    table_data_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Parsed structured table rows, columns, and headings when content_type is 'table'",
    )
    extraction_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="native_pdf",
        server_default="native_pdf",
        comment="native_pdf, docx_xml, structured_text, ocr",
    )
    ocr_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="OCR confidence percentage (0.00 to 100.00) if extracted via OCR",
    )
    legal_significance: Mapped[str] = mapped_column(
        String(35),
        nullable=False,
        default="mandatory_requirement",
        server_default="mandatory_requirement",
        comment="mandatory_requirement, prohibition, conditional_exception, procedural_step, technical_formula, definition, guideline",
    )
    review_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unreviewed",
        server_default="unreviewed",
        index=True,
        comment="unreviewed, reviewed, flagged_uncertain",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    version: Mapped["RegulatoryDocumentVersion"] = relationship(
        "RegulatoryDocumentVersion",
        back_populates="clauses",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "content_type" not in kwargs:
            kwargs["content_type"] = "text"
        if "extraction_method" not in kwargs:
            kwargs["extraction_method"] = "native_pdf"
        if "legal_significance" not in kwargs:
            kwargs["legal_significance"] = "mandatory_requirement"
        if "review_status" not in kwargs:
            kwargs["review_status"] = "unreviewed"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<RegulatoryClause(id={self.id}, clause='{self.clause_number}', page={self.page_start})>"


class RegulatoryAmendment(Base):
    """
    Gazette-notified amendment modifying, adding, or deleting clauses in a base regulation.
    Maintains historical traceability of legal amendments.
    """

    __tablename__ = "regulatory_amendments"
    __table_args__ = (
        CheckConstraint(
            "amendment_type IN ('substitution', 'insertion', 'deletion', 'modification')",
            name="ck_regulatory_amendments_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    base_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("regulatory_document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Base document version being modified",
    )
    amending_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("regulatory_document_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Document version enacting the amendment, if separately cataloged",
    )
    amendment_gazette_number: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Official gazette notification number for the amendment",
    )
    notification_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    effective_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    affected_clause_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Exact reference of clause modified (e.g. 'Clause 4.2.1', 'Section 12(3)')",
    )
    amendment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="substitution, insertion, deletion, modification",
    )
    prior_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Historical wording before amendment",
    )
    amended_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="New statutory wording enacted by amendment",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    base_version: Mapped["RegulatoryDocumentVersion"] = relationship(
        "RegulatoryDocumentVersion",
        foreign_keys=[base_version_id],
        back_populates="amendments",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "amendment_type" not in kwargs:
            kwargs["amendment_type"] = "substitution"
        super().__init__(**kwargs)


class RegulatoryIngestionJob(Base):
    """
    Tracks execution and audit metrics for regulatory document parsing and ingestion runs.
    """

    __tablename__ = "regulatory_ingestion_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_regulatory_ingestion_jobs_status",
        ),
        CheckConstraint("total_pages_processed >= 0", name="ck_regulatory_ingestion_jobs_pages_non_neg"),
        CheckConstraint("clauses_extracted_count >= 0", name="ck_regulatory_ingestion_jobs_clauses_non_neg"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    document_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("regulatory_document_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    source_url_or_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_sha256: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    total_pages_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    clauses_extracted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    tables_extracted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    errors_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs:
            kwargs["status"] = "pending"
        super().__init__(**kwargs)


class RegulatoryReviewRecord(Base):
    """
    Attributable record of professional and legal review before regulatory publishing.
    """

    __tablename__ = "regulatory_review_records"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('document_version', 'clause', 'amendment')",
            name="ck_regulatory_reviews_target_type",
        ),
        CheckConstraint(
            "review_verdict IN ('approved', 'flagged_review_required', 'rejected')",
            name="ck_regulatory_reviews_verdict",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    target_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="document_version, clause, amendment",
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_verdict: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="approved, flagged_review_required, rejected",
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Technical evaluation and legal vetting notes",
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        super().__init__(**kwargs)

