"""
TameerAI - AI Background Job Integration Contracts (Phase 03A / Phase 03C)
Defines typed payload contracts and execution schemas for asynchronous processing jobs:
Phase 03A Contracts:
- OCRJobPayload
- DocumentExtractionPayload
- EmbeddingJobPayload
- ComplianceAnalysisJobPayload

Phase 03C Contracts:
- DocumentChunkingPayload
- EmbeddingGenerationPayload
- IndexBuildPayload
- ReindexPayload
- KnowledgeSourceUpdatePayload

Designed to integrate seamlessly with the Phase 02G BackgroundJob infrastructure.
No active production handlers are registered; this defines the typed interfaces and validation rules.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

from app.ai.contracts.chunking import ChunkingConfig


# ---------------------------------------------------------------------------
# Phase 03A Legacy Payloads
# ---------------------------------------------------------------------------

class OCRJobPayload(BaseModel):
    """Payload for OCR extraction jobs."""
    document_id: UUID
    storage_path: str
    target_dpi: int = 300


class DocumentExtractionPayload(BaseModel):
    """Payload for native/hybrid document extraction jobs."""
    document_id: UUID
    storage_path: str
    extract_tables: bool = True


class EmbeddingJobPayload(BaseModel):
    """Payload for embedding computation jobs."""
    chunk_ids: List[UUID]
    model_identifier: str = "mock-bge-small-en-v1.5"


class ComplianceAnalysisJobPayload(BaseModel):
    """Payload for compliance analysis pipeline jobs."""
    audit_id: UUID
    document_ids: List[UUID]
    building_type: str
    authority: str


# ---------------------------------------------------------------------------
# Phase 03C RAG Ingestion & Indexing Payloads
# ---------------------------------------------------------------------------

class DocumentChunkingPayload(BaseModel):
    """Payload for asynchronous document chunking jobs."""
    document_id: Optional[UUID] = None
    knowledge_source_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    storage_path: str = Field(..., min_length=1)
    chunking_config: ChunkingConfig = Field(default_factory=ChunkingConfig)
    is_synthetic: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_scope(self) -> "DocumentChunkingPayload":
        is_global = (self.knowledge_source_id is not None and self.project_id is None and self.document_id is None)
        is_private = (self.knowledge_source_id is None and self.project_id is not None and self.document_id is not None)
        if not (is_global or is_private):
            raise ValueError(
                "Scope violation: DocumentChunkingPayload must target EITHER a global knowledge_source "
                "OR a project-scoped document."
            )
        return self


class EmbeddingGenerationPayload(BaseModel):
    """Payload for batch embedding generation jobs."""
    chunk_ids: List[UUID] = Field(..., min_length=1, max_length=500)
    project_id: Optional[UUID] = None
    knowledge_source_id: Optional[UUID] = None
    model_identifier: str = Field(default="mock-bge-small-en-v1.5")
    target_dimensions: int = Field(default=384, gt=0)
    batch_size: int = Field(default=64, ge=1, le=128)


class IndexBuildPayload(BaseModel):
    """Payload for building or updating a vector/hybrid index for a project or knowledge source."""
    project_id: Optional[UUID] = None
    knowledge_source_id: Optional[UUID] = None
    index_type: str = Field(default="hybrid", pattern="^(hybrid|vector|keyword)$")
    recreate: bool = Field(default=False)


class ReindexPayload(BaseModel):
    """Payload for full re-indexing of a knowledge base or workspace."""
    target_scope: str = Field(default="project_private", pattern="^(project_private|global_regulatory|all)$")
    project_id: Optional[UUID] = None
    knowledge_source_id: Optional[UUID] = None
    target_model: str = Field(default="mock-bge-small-en-v1.5")
    batch_size: int = Field(default=100, ge=10, le=500)


class KnowledgeSourceUpdatePayload(BaseModel):
    """Payload for ingesting new regulatory editions or amendment codices."""
    knowledge_source_id: UUID = Field(...)
    short_code: str = Field(..., min_length=2, max_length=50)
    edition_year: int = Field(..., ge=1900, le=2100)
    version: str = Field(..., min_length=1, max_length=20)
    storage_path: str = Field(..., min_length=1)
    is_official_regulatory: bool = Field(default=False)
    verification_status: str = Field(default="unverified", pattern="^(unverified|verified|deprecated)$")
