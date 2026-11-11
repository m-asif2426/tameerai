"""
TameerAI - RAG Knowledgebase & Chunk Pydantic Schemas (Phase 01C.5)

Defines Pydantic v2 schemas for KnowledgeSource and DocumentChunk.
Supports official regulatory codex metadata, strict global/private scope validation,
and safe API serialization without exposing internal private storage keys.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums for Knowledge Source classification
# ---------------------------------------------------------------------------

class KnowledgeCategoryEnum(str, Enum):
    BUILDING_CODE = "building_code"
    PLANNING_REGULATION = "planning_regulation"
    CONSTRUCTION_CONTRACT_STANDARD = "construction_contract_standard"
    ENGINEERING_GUIDELINE = "engineering_guideline"
    OTHER_AUTHORIZED_REFERENCE = "other_authorized_reference"


class VerificationStatusEnum(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


class IngestionStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeLanguageEnum(str, Enum):
    EN = "en"
    UR = "ur"
    MIXED = "mixed"


# ---------------------------------------------------------------------------
# KnowledgeSource Schemas
# ---------------------------------------------------------------------------

class KnowledgeSourceBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    title: str = Field(min_length=1, max_length=255, description="Official title of codex or standard")
    title_urdu: Optional[str] = Field(default=None, max_length=255, alias="titleUrdu", description="Urdu title")
    short_code: str = Field(min_length=2, max_length=50, alias="shortCode", description="Unique identifier (e.g. PBC_2021)")
    category: KnowledgeCategoryEnum = Field(description="Domain category")
    authority: str = Field(min_length=1, max_length=150, description="Promulgating authority (e.g. PEC, SBCA)")
    edition_year: Optional[int] = Field(default=None, ge=1900, le=2100, alias="editionYear", description="Publication year")
    version: str = Field(default="1.0", max_length=50, description="Version string")
    jurisdiction: str = Field(min_length=1, max_length=100, description="Geographic jurisdiction")
    language: KnowledgeLanguageEnum = Field(default=KnowledgeLanguageEnum.EN, description="Language: en, ur, mixed")
    source_url: Optional[str] = Field(default=None, max_length=500, alias="sourceUrl", description="Official publication URL")
    total_pages: int = Field(default=0, ge=0, alias="totalPages", description="Total page count")
    effective_date: Optional[date] = Field(default=None, alias="effectiveDate", description="Legal effective date")
    provenance: Optional[str] = Field(default=None, description="Official legal and gazette provenance")
    is_official_regulatory: bool = Field(default=False, alias="isOfficialRegulatory", description="Whether officially approved / promulgated")


class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass


class KnowledgeSourceRead(KnowledgeSourceBase):
    id: UUID
    verification_status: VerificationStatusEnum = Field(alias="verificationStatus")
    ingestion_status: IngestionStatusEnum = Field(alias="ingestionStatus")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    # storage_path is strictly excluded from public read serialization


# ---------------------------------------------------------------------------
# DocumentChunk Schemas
# ---------------------------------------------------------------------------

class DocumentChunkBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    content: str = Field(min_length=1, description="Extracted text content of passage")
    content_urdu: Optional[str] = Field(default=None, alias="contentUrdu", description="Urdu translation or text")
    chunk_index: int = Field(default=0, ge=0, alias="chunkIndex", description="Ordinal position within document")
    chapter: Optional[str] = Field(default=None, max_length=150, description="Chapter heading")
    section: Optional[str] = Field(default=None, max_length=150, description="Clause or section identifier")
    page_number: Optional[int] = Field(default=None, ge=1, alias="pageNumber", description="Page number")
    token_count: int = Field(default=0, ge=0, alias="tokenCount", description="Token count")


class DocumentChunkCreate(DocumentChunkBase):
    knowledge_source_id: Optional[UUID] = Field(default=None, alias="knowledgeSourceId")
    project_id: Optional[UUID] = Field(default=None, alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId")
    content_hash: Optional[str] = Field(default=None, max_length=64, alias="contentHash")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, alias="metadataJson")

    @model_validator(mode="after")
    def validate_scope(self) -> "DocumentChunkCreate":
        """Enforces mutual exclusion between global regulatory chunks and private project chunks."""
        is_global = self.knowledge_source_id is not None
        is_private = self.project_id is not None or self.document_id is not None

        if is_global and is_private:
            raise ValueError("DocumentChunk cannot be simultaneously global (knowledgeSourceId) and private (projectId/documentId).")

        if not is_global and not is_private:
            raise ValueError("DocumentChunk must specify either a global knowledgeSourceId or private projectId and documentId.")

        if is_private and (self.project_id is None or self.document_id is None):
            raise ValueError("Private DocumentChunk requires BOTH projectId and documentId.")

        return self


class DocumentChunkRead(DocumentChunkBase):
    id: UUID
    knowledge_source_id: Optional[UUID] = Field(default=None, alias="knowledgeSourceId")
    project_id: Optional[UUID] = Field(default=None, alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId")
    content_hash: Optional[str] = Field(default=None, alias="contentHash")
    created_at: datetime = Field(alias="createdAt")

    @property
    def is_global(self) -> bool:
        """Helper indicating whether this chunk belongs to the public regulatory knowledge base."""
        return self.knowledge_source_id is not None

