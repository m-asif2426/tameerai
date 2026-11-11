"""
TameerAI - Project Document Management Endpoints (Phase 02D)

Endpoints for:
- POST /api/v1/projects/{project_id}/documents (Upload file with magic byte validation)
- GET /api/v1/projects/{project_id}/documents (List project documents with pagination & filtering)
- GET /api/v1/projects/{project_id}/documents/{document_id} (Document details)
- GET /api/v1/projects/{project_id}/documents/{document_id}/download (Secure signed download link)
- DELETE /api/v1/projects/{project_id}/documents/{document_id} (Deletion safety check)
"""

import logging
from typing import List, Optional, Tuple

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.projects import get_project_with_view_access
from app.core.storage import StorageProvider, get_storage_provider
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentDownloadUrl, DocumentRead
from app.services.document_service import (
    generate_document_download_url,
    get_document_by_identifier,
    list_project_documents,
    upload_and_create_document,
)

logger = logging.getLogger("tameerai.api.documents")

router = APIRouter()


# ---------------------------------------------------------------------------
# Authorization Dependencies
# ---------------------------------------------------------------------------

async def get_project_with_upload_access(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> Tuple[Project, str]:
    """
    Ensures current_user has document upload access to the project workspace.
    Permitted: owner, lead_engineer, architect, contractor.
    Viewer role is strictly rejected with 403 Forbidden.
    """
    project, user_role = project_data
    if user_role not in {"owner", "lead_engineer", "architect", "contractor"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to upload project documents. Viewers cannot upload files.",
        )
    return project, user_role


async def get_project_with_delete_doc_access(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> Tuple[Project, str]:
    """
    Ensures caller has project administration access for deletion evaluation.
    """
    project, user_role = project_data
    if user_role not in {"owner", "lead_engineer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to request document deletion.",
        )
    return project, user_role


# ---------------------------------------------------------------------------
# Document Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload project document",
    description=(
        "Streams and uploads an engineering drawing, blueprint, contract, or BOQ. "
        "Validates magic bytes, enforces 50 MB limit, and records audit trail. "
        "Viewer role is rejected with 403."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="Project file to upload (PDF, DWG, DXF, XLSX, DOCX)"),
    category: Optional[str] = Form(None, description="Optional domain category override"),
    project_data: Tuple[Project, str] = Depends(get_project_with_upload_access),
    current_user: User = Depends(get_current_user),
    storage: StorageProvider = Depends(get_storage_provider),
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    project, _ = project_data
    doc = await upload_and_create_document(
        db=db,
        storage=storage,
        project=project,
        uploader=current_user,
        upload_file=file,
        override_category=category,
    )
    return DocumentRead.model_validate(doc)


@router.get(
    "",
    response_model=List[DocumentRead],
    status_code=status.HTTP_200_OK,
    summary="List project documents",
    description="Lists documents in this workspace with pagination and optional filtering by status/category.",
)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(default=None, description="Filter by review status"),
    category: Optional[str] = Query(default=None, description="Filter by domain category"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
) -> List[DocumentRead]:
    project, _ = project_data
    docs, _ = await list_project_documents(
        db=db,
        project=project,
        page=page,
        page_size=page_size,
        status_filter=status,
        category_filter=category,
    )
    return [DocumentRead.model_validate(d) for d in docs]


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_200_OK,
    summary="Get project document details",
    description="Retrieves metadata for a specific document by internal UUID or public code (e.g. DOC-01).",
)
async def get_document(
    document_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    project, _ = project_data
    doc = await get_document_by_identifier(db=db, project=project, identifier=document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this project workspace.",
        )
    return DocumentRead.model_validate(doc)


@router.get(
    "/{document_id}/download",
    response_model=DocumentDownloadUrl,
    status_code=status.HTTP_200_OK,
    summary="Get secure signed download link",
    description=(
        "Generates a short-lived (5 minute) signed download URL for the project document. "
        "Credentials and private object keys are never exposed."
    ),
)
async def download_document(
    document_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    storage: StorageProvider = Depends(get_storage_provider),
    db: AsyncSession = Depends(get_db),
) -> DocumentDownloadUrl:
    project, _ = project_data
    doc = await get_document_by_identifier(db=db, project=project, identifier=document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this project workspace.",
        )

    return await generate_document_download_url(storage=storage, document=doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete project document (Protected)",
    description=(
        "Irreversible document deletion is restricted to preserve structural audit trails, "
        "legal evidence, and engineering intelligence. Archival schema migration is pending authorization."
    ),
)
async def delete_document(
    document_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_delete_doc_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    doc = await get_document_by_identifier(db=db, project=project, identifier=document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this project workspace.",
        )

    # Document deletion is restricted by default to preserve audit trails and engineering evidence
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "Document deletion is restricted to preserve structural audit trails, "
            "legal evidence, and engineering intelligence. Archival schema migration is pending authorization."
        ),
    )

