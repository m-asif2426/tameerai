"""
TameerAI - Citation & Evidence Validation Contracts (Phase 03A / Phase 03C / Phase 03G Stage B3.1)
Defines protocol contracts, independent verification dimensions, and validation result structures
to ensure AI outputs are strictly grounded in verified retrieved evidence.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from app.ai.contracts.retrieval import RetrievedChunk


class ValidationStatus(str, Enum):
    VALID = "valid"
    UNSUPPORTED_CITATION = "unsupported_citation"
    MISSING_EVIDENCE = "missing_evidence"
    INVALID_PAGE = "invalid_page"
    MALFORMED_IDENTIFIER = "malformed_identifier"
    UNAUTHORIZED_PROJECT_REFERENCE = "unauthorized_project_reference"
    VERSION_MISMATCH = "version_mismatch"
    INVALID_CHUNK_ID = "invalid_chunk_id"
    DOCUMENT_MISMATCH = "document_mismatch"
    INVALID_CLAUSE = "invalid_clause"
    UNSUPPORTED_CLAIM = "unsupported_claim"


# =====================================================================
# INDEPENDENT VERIFICATION DIMENSIONS (Phase 03G Stage B3.1)
# =====================================================================

class ClaimRelevanceStatus(str, Enum):
    """Claim-evidence alignment statuses separating source validity from claim support."""
    VALID_SOURCE = "valid_source"
    CLAIM_SUPPORTED = "claim_supported"
    CLAIM_PARTIALLY_SUPPORTED = "claim_partially_supported"
    CLAIM_UNSUPPORTED = "claim_unsupported"
    CLAIM_RELEVANCE_UNVERIFIED = "claim_relevance_unverified"


class EvidenceStatus(str, Enum):
    """Orthogonal evidence grounding status."""
    VERIFIED = "verified"
    PARTIALLY_SUPPORTED = "partially_supported"
    INSUFFICIENT = "insufficient"
    UNVERIFIED = "unverified"


class CalculationStatus(str, Enum):
    """Orthogonal mathematical verification status."""
    VERIFIED = "verified"
    MISMATCH = "mismatch"
    NOT_APPLICABLE = "not_applicable"
    NOT_VERIFIABLE = "not_verifiable"


class RegulatoryStatus(str, Enum):
    """Orthogonal regulatory compliance / clause status."""
    VERIFIED_REFERENCE = "verified_reference"
    UNVERIFIED_REFERENCE = "unverified_reference"
    INTERPRETATION_UNVERIFIED = "interpretation_unverified"
    NOT_APPLICABLE = "not_applicable"


class CitationStatus(str, Enum):
    """Orthogonal citation integrity status."""
    VALID = "valid"
    INVALID = "invalid"
    PARTIALLY_SUPPORTED = "partially_supported"
    RELEVANCE_UNVERIFIED = "relevance_unverified"


# =====================================================================
# CITATION AUDIT CONTRACTS
# =====================================================================

class CitationValidationItem(BaseModel):
    """Detailed audit for a single cited reference."""
    citation_text: str = Field(...)
    source_code: str = Field(...)
    clause_or_section: Optional[str] = None
    page_number: Optional[int] = None
    status: ValidationStatus = Field(...)
    matched_chunk_id: Optional[str] = None
    source_id_matches: Optional[bool] = None
    document_id_matches: Optional[bool] = None
    claim_support_verified: bool = Field(default=False, description="Whether evidence text semantically supports the generated claim")
    claim_relevance_status: Optional[ClaimRelevanceStatus] = Field(
        default=None,
        description="Granular alignment status between cited claim and retrieved chunk content."
    )
    claim_text: Optional[str] = Field(default=None, description="The specific factual claim asserted")
    evidence_text_snippet: Optional[str] = None
    explanation: str = Field(...)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CitationValidationReport(BaseModel):
    """Overall validation verdict for an AI generated answer."""
    is_fully_grounded: bool = Field(...)
    total_citations: int = Field(default=0, ge=0)
    valid_citations: int = Field(default=0, ge=0)
    unsupported_citations: int = Field(default=0, ge=0)
    citation_status: Optional[CitationStatus] = None
    items: List[CitationValidationItem] = Field(default_factory=list)
    conflicting_evidence: List[str] = Field(default_factory=list, description="Contradictions detected across retrieved evidence chunks")
    unsupported_warning: Optional[str] = None
    advisory_notice: str = Field(
        default="Reference verified against available official regulatory text; does not assert real statutory certification or official approval."
    )


@runtime_checkable
class CitationValidatorProtocol(Protocol):
    """Protocol for validating AI citations against retrieved grounding evidence."""
    def validate_citations(
        self,
        citations: List[dict],
        evidence_chunks: List[RetrievedChunk],
        project_id: Optional[Any] = None,
    ) -> CitationValidationReport:
        ...
