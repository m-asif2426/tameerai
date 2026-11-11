"""
TameerAI - Document Metadata Pydantic Schemas (Phase 01C.3)

Defines Pydantic v2 schemas for project documents.
Ensures camelCase serialization matching frontend TypeScript contracts
(src/types/project.ts -> ProjectDocument), safe validation, and public code aliasing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums matching frontend and domain constraints
# ---------------------------------------------------------------------------

class DocumentCategory(str, Enum):
    BLUEPRINT = "blueprint"
    BUILDING_CODE = "building_code"
    CONTRACT = "contract"
    BOQ = "boq"
    GENERAL_PROJECT_DOCUMENT = "general_project_document"


class DocumentReviewStatus(str, Enum):
    VERIFIED = "Verified"
    REVIEW_REQUIRED = "Review Required"
    PENDING_ANALYSIS = "Pending Analysis"


class DocumentAnalysisStatus(str, Enum):
    UNPROCESSED = "unprocessed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Document Schemas
# ---------------------------------------------------------------------------

class DocumentBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    name: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_type: str = Field(
        ...,
        max_length=50,
        alias="type",
        serialization_alias="type",
        description="Display type: 'CAD Drawing', 'Architectural Blueprint', 'Legal Contract', etc.",
    )
    document_category: str = Field(
        default="general_project_document",
        max_length=50,
        alias="category",
        serialization_alias="category",
        description="Domain category: blueprint, building_code, contract, boq, general_project_document",
    )
    file_size_human: str = Field(
        default="0 KB",
        max_length=30,
        alias="size",
        serialization_alias="size",
        description="Human-readable file size string",
    )
    file_size_bytes: int = Field(
        default=0,
        ge=0,
        alias="sizeBytes",
        serialization_alias="sizeBytes",
        description="Exact file size in bytes",
    )
    status: str = Field(
        default="Pending Analysis",
        max_length=50,
        description="Status: 'Verified', 'Review Required', 'Pending Analysis'",
    )
    uploaded_by: Optional[str] = Field(
        default=None,
        max_length=150,
        alias="uploadedBy",
        serialization_alias="uploadedBy",
    )


class DocumentCreate(DocumentBase):
    """Payload for registering an uploaded document."""
    code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional public document code (e.g. DOC-01). Auto-assigned if omitted.",
    )
    storage_path: str = Field(
        ...,
        max_length=500,
        alias="storagePath",
        serialization_alias="storagePath",
        description="Private object storage key/path",
    )
    mime_type: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="mimeType",
        serialization_alias="mimeType",
    )
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="metadata",
        serialization_alias="metadata",
    )


class DocumentUpdate(BaseModel):
    """Payload for updating document metadata or review status."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    file_type: Optional[str] = Field(default=None, alias="type", serialization_alias="type")
    document_category: Optional[str] = Field(default=None, alias="category", serialization_alias="category")
    status: Optional[str] = None
    analysis_status: Optional[str] = Field(default=None, alias="analysisStatus", serialization_alias="analysisStatus")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, alias="metadata", serialization_alias="metadata")


class DocumentRead(DocumentBase):
    """
    Document schema matching the frontend `ProjectDocument` interface (src/types/project.ts).
    Exposes `id` containing the public human-readable code (e.g. 'DOC-01') and internal `uuid`.
    Private storage path is strictly omitted to preserve storage key confidentiality.
    """
    id: str = Field(..., description="Frontend-facing public document code (e.g. DOC-01)")
    uuid: UUID = Field(..., description="Internal collision-free UUID")
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    mime_type: Optional[str] = Field(default=None, alias="mimeType", serialization_alias="mimeType")
    analysis_status: str = Field(default="unprocessed", alias="analysisStatus", serialization_alias="analysisStatus")
    upload_time: str = Field(default="Just now", alias="uploadTime", serialization_alias="uploadTime")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt", serialization_alias="updatedAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_document(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):  # SQLAlchemy ORM model instance
            return {
                "id": data.code,
                "uuid": data.id,
                "code": data.code,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "name": data.name,
                "type": data.file_type,
                "file_type": data.file_type,
                "category": data.document_category,
                "document_category": data.document_category,
                "size": data.file_size_human,
                "file_size_human": data.file_size_human,
                "sizeBytes": data.file_size_bytes,
                "file_size_bytes": data.file_size_bytes,
                "mimeType": data.mime_type,
                "mime_type": data.mime_type,
                "status": data.status,
                "analysisStatus": data.analysis_status,
                "analysis_status": data.analysis_status,
                "uploadedBy": data.uploaded_by or "Workspace User",
                "uploaded_by": data.uploaded_by or "Workspace User",
                "uploadTime": "Recently uploaded",
                "upload_time": "Recently uploaded",
                "createdAt": data.created_at,
                "created_at": data.created_at,
                "updatedAt": data.updated_at,
                "updated_at": data.updated_at,
            }
        return data


class DocumentDownloadUrl(BaseModel):
    """Temporary signed URL for downloading a project document."""
    model_config = ConfigDict(
        populate_by_name=True,
    )

    download_url: str = Field(..., alias="downloadUrl", serialization_alias="downloadUrl")
    expires_in_seconds: int = Field(default=300, alias="expiresInSeconds", serialization_alias="expiresInSeconds")
    filename: str = Field(..., description="Display filename for client download header")
    mime_type: Optional[str] = Field(default=None, alias="mimeType", serialization_alias="mimeType")

