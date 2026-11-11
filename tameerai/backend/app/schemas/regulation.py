"""
TameerAI - Pydantic Request & Response Schemas for Statutory Regulatory Knowledge Base (Phase 03.3)

Matches SQLAlchemy models in app/models/regulation.py exactly.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Regulatory Authority Schemas
# ---------------------------------------------------------------------------

class RegulatoryAuthorityBase(BaseModel):
    code: str = Field(..., max_length=50, description="Unique authority mnemonic (e.g. PEC, BCP_FED, LDA, SBCA, CDA)")
    name: str = Field(..., max_length=255, description="Full legal name of the authority in English")
    name_urdu: Optional[str] = Field(None, max_length=255, description="Official authority name in Urdu script")
    jurisdiction_level: str = Field(..., description="federal, provincial, municipal, special_authority")
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    official_website: str = Field(..., max_length=500)
    regulatory_domain: str = Field(..., max_length=100)
    publication_channels: Optional[Dict[str, Any]] = None
    credibility_tier: str = Field(
        "tier_b_official_regulatory",
        description="tier_a_statutory, tier_b_official_regulatory, tier_c_recognized_technical, tier_d_secondary"
    )
    verification_status: str = Field("discovered", description="verified, discovered, unverified")


class RegulatoryAuthorityCreate(RegulatoryAuthorityBase):
    pass


class RegulatoryAuthorityUpdate(BaseModel):
    name: Optional[str] = None
    name_urdu: Optional[str] = None
    jurisdiction_level: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    official_website: Optional[str] = None
    regulatory_domain: Optional[str] = None
    publication_channels: Optional[Dict[str, Any]] = None
    credibility_tier: Optional[str] = None
    verification_status: Optional[str] = None


class RegulatoryAuthorityRead(RegulatoryAuthorityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    last_discovered_at: datetime
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 2. Regulatory Document Schemas
# ---------------------------------------------------------------------------

class RegulatoryDocumentBase(BaseModel):
    authority_id: uuid.UUID
    document_code: str = Field(..., max_length=100, description="e.g. BCP-SP-2007, LDA-BZR-2020, PEC-ACT-1976")
    title: str = Field(..., max_length=300)
    title_urdu: Optional[str] = Field(None, max_length=300)
    official_document_number: Optional[str] = Field(None, max_length=150)
    document_category: str = Field(
        "building_code",
        description="building_code, zoning_regulation, act_legislation, bye_law, technical_standard, guideline"
    )
    legal_instrument_type: str = Field(
        "authority_regulations",
        description="statutory_act, gazette_notification, authority_regulations, standard_specification, advisory_guideline"
    )
    legal_force_status: str = Field(
        "mandatory_notified",
        description="legally_binding, mandatory_notified, adopted_standard, guideline_only, draft_non_binding"
    )
    jurisdiction_country: str = Field("Pakistan", max_length=50)
    jurisdiction_province: Optional[str] = Field(None, max_length=100)
    jurisdiction_city: Optional[str] = Field(None, max_length=100)
    applicable_districts: Optional[Dict[str, Any]] = None
    status: str = Field(
        "DISCOVERED",
        description="DISCOVERED, SOURCE_VERIFIED, ACQUIRED, INGESTED, PARSED, REVIEW_REQUIRED, PUBLISHED, SUPERSEDED, WITHDRAWN, REJECTED"
    )
    superseded_by_document_id: Optional[uuid.UUID] = None


class RegulatoryDocumentCreate(RegulatoryDocumentBase):
    pass


class RegulatoryDocumentUpdate(BaseModel):
    title: Optional[str] = None
    title_urdu: Optional[str] = None
    official_document_number: Optional[str] = None
    document_category: Optional[str] = None
    legal_instrument_type: Optional[str] = None
    legal_force_status: Optional[str] = None
    jurisdiction_province: Optional[str] = None
    jurisdiction_city: Optional[str] = None
    applicable_districts: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    superseded_by_document_id: Optional[uuid.UUID] = None


class RegulatoryDocumentRead(RegulatoryDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    authority: Optional[RegulatoryAuthorityRead] = None


# ---------------------------------------------------------------------------
# 3. Regulatory Document Version Schemas
# ---------------------------------------------------------------------------

class RegulatoryDocumentVersionBase(BaseModel):
    document_id: uuid.UUID
    version_label: str = Field(..., max_length=50, description="e.g. 2007, 2020-Original, 2020-Amended-2023")
    edition: Optional[str] = Field(None, max_length=50)
    publication_date: Optional[date] = None
    notification_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_current: bool = Field(True)
    superseded_by_version_id: Optional[uuid.UUID] = None
    storage_path: Optional[str] = Field(None, max_length=500)
    official_source_url: Optional[str] = Field(None, max_length=500)
    source_file_sha256: Optional[str] = Field(None, max_length=64)
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = Field("application/pdf", max_length=100)
    total_pages: int = Field(0)
    language: str = Field("en", max_length=10)
    provenance_details: Optional[Dict[str, Any]] = None
    verification_notes: Optional[str] = None


class RegulatoryDocumentVersionCreate(RegulatoryDocumentVersionBase):
    pass


class RegulatoryDocumentVersionRead(RegulatoryDocumentVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 4. Regulatory Clause Schemas
# ---------------------------------------------------------------------------

class RegulatoryClauseBase(BaseModel):
    version_id: uuid.UUID
    chapter_number: Optional[str] = Field(None, max_length=50)
    chapter_title: Optional[str] = Field(None, max_length=255)
    section_number: Optional[str] = Field(None, max_length=50)
    section_title: Optional[str] = Field(None, max_length=255)
    clause_number: str = Field(..., max_length=100, description="e.g. '4.2.1', 'Section 15(1)(a)', 'Table 4.3'")
    clause_title: Optional[str] = Field(None, max_length=255)
    subclause_number: Optional[str] = Field(None, max_length=50)
    page_start: int = Field(..., ge=1)
    page_end: int = Field(..., ge=1)
    original_text: str
    normalized_text: str
    content_type: str = Field(
        "text",
        description="text, table, formula, figure_caption, annexure, schedule, definition"
    )
    table_data_json: Optional[Dict[str, Any]] = None
    extraction_method: str = Field(
        "native_pdf",
        description="native_pdf, docx_xml, structured_text, ocr"
    )
    ocr_confidence: Optional[Decimal] = None
    legal_significance: str = Field(
        "mandatory_requirement",
        description="mandatory_requirement, prohibition, conditional_exception, procedural_step, technical_formula, definition, guideline"
    )
    review_status: str = Field(
        "unreviewed",
        description="unreviewed, reviewed, flagged_uncertain"
    )


class RegulatoryClauseCreate(RegulatoryClauseBase):
    pass


class RegulatoryClauseUpdate(BaseModel):
    chapter_number: Optional[str] = None
    chapter_title: Optional[str] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    clause_title: Optional[str] = None
    original_text: Optional[str] = None
    normalized_text: Optional[str] = None
    legal_significance: Optional[str] = None
    review_status: Optional[str] = None


class RegulatoryClauseRead(RegulatoryClauseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 5. Regulatory Amendment Schemas
# ---------------------------------------------------------------------------

class RegulatoryAmendmentBase(BaseModel):
    base_version_id: uuid.UUID
    amending_version_id: Optional[uuid.UUID] = None
    amendment_gazette_number: Optional[str] = Field(None, max_length=150)
    notification_date: Optional[date] = None
    effective_date: Optional[date] = None
    affected_clause_reference: str = Field(..., max_length=100)
    amendment_type: str = Field("substitution", description="substitution, insertion, deletion, modification")
    prior_text: Optional[str] = None
    amended_text: Optional[str] = None


class RegulatoryAmendmentCreate(RegulatoryAmendmentBase):
    pass


class RegulatoryAmendmentRead(RegulatoryAmendmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# 6. Ingestion Job Schemas
# ---------------------------------------------------------------------------

class RegulatoryIngestionJobCreate(BaseModel):
    document_code: str = Field(..., max_length=100)
    version_id: Optional[uuid.UUID] = None
    source_url_or_path: str = Field(..., max_length=500)
    file_sha256: Optional[str] = None


class RegulatoryIngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_code: str
    version_id: Optional[uuid.UUID] = None
    status: str
    source_url_or_path: str
    file_sha256: Optional[str] = None
    total_pages_processed: int
    clauses_extracted_count: int
    tables_extracted_count: int
    errors_json: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# 7. Review Record Schemas
# ---------------------------------------------------------------------------

class RegulatoryReviewRecordCreate(BaseModel):
    target_type: str = Field("document_version", description="document_version, clause, amendment")
    target_id: uuid.UUID
    review_verdict: str = Field(..., description="approved, flagged_review_required, rejected")
    notes: str = Field(..., description="Technical evaluation and legal vetting notes")


class RegulatoryReviewRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    reviewer_id: uuid.UUID
    review_verdict: str
    notes: str
    reviewed_at: datetime


# ---------------------------------------------------------------------------
# 8. Search & Citation Schemas
# ---------------------------------------------------------------------------

class RegulatorySearchQuery(BaseModel):
    query: str = Field(..., min_length=2, description="Search terms or keywords")
    jurisdiction_level: Optional[str] = Field(None, description="federal, provincial, municipal, special_authority")
    province: Optional[str] = Field(None, description="e.g. Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, ICT")
    city: Optional[str] = Field(None, description="e.g. Lahore, Karachi, Islamabad, Rawalpindi")
    authority_codes: Optional[List[str]] = Field(None, description="e.g. ['PEC', 'LDA', 'BCP_FED']")
    document_codes: Optional[List[str]] = Field(None, description="e.g. ['BCP-SP-2007', 'LDA-BZR-2020']")
    content_types: Optional[List[str]] = Field(None, description="e.g. ['text', 'table', 'formula']")
    legal_significance: Optional[List[str]] = Field(None, description="e.g. ['mandatory_requirement', 'prohibition']")
    is_current_only: bool = Field(True, description="Only search currently active versions")
    effective_date: Optional[date] = Field(None, description="Point-in-time statutory lookup")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class RegulatoryCitation(BaseModel):
    citation_string: str = Field(
        ...,
        description="Canonical citation string, e.g. [BCP_FED, Building Code of Pakistan - Seismic Provisions 2007, Ed. 2007, Ch. 5, Sec. 5.3, Clause 5.3.1, p. 42]"
    )
    authority_code: str
    authority_name: str
    document_code: str
    document_title: str
    version_label: str
    section_identifier: Optional[str] = None
    clause_number: str
    page_start: int
    page_end: int
    legal_force_status: str
    legal_significance: str
    credibility_tier: str


class RegulatorySearchResult(BaseModel):
    clause: RegulatoryClauseRead
    citation: RegulatoryCitation
    relevance_score: float
    matched_terms: List[str]


class RegulatorySearchResponse(BaseModel):
    total: int
    page: int
    limit: int
    results: List[RegulatorySearchResult]
    jurisdiction_filtered: bool
    applied_filters: Dict[str, Any]
