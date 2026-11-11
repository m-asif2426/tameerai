"""
TameerAI - Document Chunking Contracts (Phase 03C)
Defines data structures, configuration, and protocols for structured document chunking
with strict page provenance and regulatory clause preservation.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator


class ChunkingConfig(BaseModel):
    """Configuration parameters for structured document chunking."""
    chunk_size: int = Field(default=800, ge=50, le=4000, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=150, ge=0, le=1000, description="Character overlap between consecutive chunks")
    preserve_clauses: bool = Field(default=True, description="Avoid splitting regulatory and contract clauses")
    preserve_headings: bool = Field(default=True, description="Retain chapter and section headers")
    min_chunk_size: int = Field(default=20, ge=10, description="Drop chunks smaller than this threshold")
    estimate_tokens: bool = Field(default=True, description="Compute token count approximations")

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkingConfig":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"chunk_overlap ({self.chunk_overlap}) must be strictly less than chunk_size ({self.chunk_size})")
        return self


class StructuredChunk(BaseModel):
    """
    In-memory structured chunk with complete provenance.
    Schema-compatible with the database DocumentChunk model.
    """
    id: UUID = Field(default_factory=uuid4)
    knowledge_source_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    chunk_index: int = Field(default=0, ge=0)
    content: str = Field(..., min_length=1)
    content_urdu: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = Field(default=None, ge=1)
    token_count: int = Field(default=0, ge=0)
    content_hash: Optional[str] = None
    extraction_method: str = Field(default="native_pdf")  # native_pdf, ocr, hybrid
    source_title: Optional[str] = None
    source_code: Optional[str] = None
    source_version: Optional[str] = "1.0"
    is_synthetic: bool = Field(default=False)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scope_integrity(self) -> "StructuredChunk":
        """Enforces identical scope boundary to DB constraint ck_document_chunks_scope."""
        is_global = (self.knowledge_source_id is not None and self.project_id is None and self.document_id is None)
        is_private = (self.knowledge_source_id is None and self.project_id is not None and self.document_id is not None)
        # In test mode or staging before DB insertion, we allow unbound chunks if clearly flagged,
        # but if either knowledge_source_id or project_id is set, it must strictly satisfy the boundary.
        if self.knowledge_source_id is not None or self.project_id is not None or self.document_id is not None:
            if not (is_global or is_private):
                raise ValueError(
                    "Scope constraint violation: Chunk must be EITHER global (knowledge_source_id set, "
                    "project_id and document_id None) OR private (project_id and document_id set, "
                    "knowledge_source_id None)."
                )
        return self


class ChunkingResult(BaseModel):
    """Result of a document chunking execution."""
    document_id: Optional[UUID] = None
    knowledge_source_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    total_chunks: int = Field(default=0, ge=0)
    total_characters: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    chunks: List[StructuredChunk] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(default=0.0, ge=0.0)


@runtime_checkable
class DocumentChunkerProtocol(Protocol):
    """Protocol for chunking structured or raw documents."""
    def chunk_document(
        self,
        document_text: str,
        config: Optional[ChunkingConfig] = None,
        **kwargs
    ) -> ChunkingResult:
        ...
