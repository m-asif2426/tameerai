"""
TameerAI - Knowledge Retrieval & Grounding Contracts (Phase 03A)
Defines protocol contracts and typed data structures for multi-tenant,
scoped knowledge retrieval across global regulatory codices and private project documents.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from uuid import UUID
from pydantic import BaseModel, Field


class ScopeType(str, Enum):
    """Retrieval boundary separation matching database CHECK constraints."""
    GLOBAL_REGULATORY = "global_regulatory"  # Public codices (Building Code of Pakistan, LDA, CDA, SBCA, FIDIC)
    PROJECT_PRIVATE = "project_private"      # Tenant-specific uploaded project drawings, specs, agreements
    HYBRID = "hybrid"                        # Combined retrieval with explicit boundary tracking


class RetrievedChunk(BaseModel):
    """Individual retrieved text passage with provenance metadata."""
    chunk_id: UUID = Field(...)
    source_title: str = Field(...)
    source_code: str = Field(...)
    content: str = Field(...)
    content_urdu: Optional[str] = None
    page_number: Optional[int] = Field(default=None, ge=1)
    clause_or_section: Optional[str] = None
    scope: ScopeType = Field(default=ScopeType.GLOBAL_REGULATORY)
    project_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalQuery(BaseModel):
    """Structured query for knowledge retrieval."""
    query_text: str = Field(..., min_length=1)
    project_id: Optional[UUID] = None
    scope: ScopeType = Field(default=ScopeType.HYBRID)
    top_k: int = Field(default=5, ge=1, le=50)
    minimum_score: float = Field(default=0.5, ge=0.0, le=1.0)
    authority_filter: Optional[List[str]] = None  # e.g. ["LDA", "CDA", "SBCA", "PEC", "FIDIC"]
    language: str = Field(default="en", pattern="^(en|ur|mixed)$")


class RetrievalResult(BaseModel):
    """Collection of retrieved evidence with retrieval execution metadata."""
    query: str = Field(...)
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    total_found: int = Field(default=0, ge=0)
    scope_used: ScopeType = Field(...)
    latency_ms: float = Field(default=0.0, ge=0.0)


@runtime_checkable
class KnowledgeRetriever(Protocol):
    """Protocol for querying grounded regulatory and project knowledge."""
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """Executes a scoped retrieval query adhering to tenant isolation rules."""
        ...

