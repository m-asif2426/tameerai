"""
TameerAI - Project Document Service (Phase 02D)

Business logic for:
- Document filename sanitization and magic-signature MIME validation
- Streaming upload with strict size limit enforcement (max 50 MB)
- Safe sequential document code allocation (DOC-01, DOC-02...) scoped per project workspace
- Compensating storage cleanup upon database commit failures
- Tenant-scoped document retrieval, listing, and signed download URL generation
- Strict deletion restrictions to preserve structural audit trails and evidence
"""

import io
import logging
import os
import re
import uuid
import zipfile
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import StorageError, StorageFileNotFoundError, StorageProvider
from app.models.document import Document
from app.models.project import Project, ProjectActivity
from app.models.user import User
from app.schemas.document import DocumentDownloadUrl

logger = logging.getLogger("tameerai.documents")

# Allowed extensions and standard mappings
ALLOWED_EXTENSIONS = {".pdf", ".dwg", ".dxf", ".xlsx", ".docx"}

# Magic byte signatures for supported binary formats
PDF_MAGIC = b"%PDF"
DWG_MAGICS = (b"AC10", b"AC09", b"AC1.2", b"AC")
ZIP_MAGIC = b"PK\x03\x04"  # Containers for .xlsx and .docx

# OpenXML archive safety boundaries (protects against ZIP bombs / excessive member traversal)
MAX_ZIP_ENTRIES = 1000
MAX_ZIP_UNCOMPRESSED_BYTES = 100 * 1024 * 1024  # 100 MB max uncompressed size across entries


def format_file_size(size_bytes: int) -> str:
    """Formats exact byte count into human-readable string (e.g. '42.5 MB')."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def sanitize_filename(filename: str) -> Tuple[str, str]:
    """
    Sanitizes raw client filename, strips directory path traversal components,
    and validates permitted extensions. Returns (safe_filename, lower_extension).
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Filename cannot be empty.",
        )

    # Strip null bytes and control characters
    cleaned = filename.replace("\x00", "").strip()
    # Extract basename only to neutralize path traversal
    base_name = os.path.basename(cleaned)
    # Remove leading dots or directory separators
    base_name = re.sub(r"^[./\\]+", "", base_name).strip()

    if not base_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid filename after path sanitization.",
        )

    _, ext = os.path.splitext(base_name)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Unsupported file extension '{ext}'. Allowed extensions: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    return base_name, ext_lower


def validate_file_signature(ext: str, first_bytes: bytes, file_bytes: bytes) -> Tuple[str, str, str]:
    """
    Validates actual file header signatures (magic bytes) and container structures against declared extensions.
    Returns (mime_type, file_type, document_category).
    """
    if ext == ".pdf":
        # Check for %PDF within the first 1024 bytes to allow for leading BOM/whitespace
        if PDF_MAGIC not in first_bytes[:1024]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content does not match PDF signature.",
            )
        return "application/pdf", "PDF Document", "general_project_document"

    elif ext == ".dwg":
        if not any(first_bytes.startswith(magic) for magic in DWG_MAGICS):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content does not match AutoCAD DWG signature.",
            )
        return "image/vnd.dwg", "CAD Drawing", "blueprint"

    elif ext == ".dxf":
        # Check binary DXF signature or ASCII DXF section marker
        is_binary_dxf = first_bytes.startswith(b"AutoCAD DXF")
        sample = first_bytes[:512].decode("ascii", errors="ignore").strip()
        is_ascii_dxf = sample.startswith(("0", "SECTION", "AutoCAD")) or "SECTION" in sample[:128]
        if not (is_binary_dxf or is_ascii_dxf):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content does not match AutoCAD DXF format signature.",
            )
        return "image/vnd.dxf", "CAD Drawing (DXF)", "blueprint"

    elif ext == ".xlsx":
        if not first_bytes.startswith(ZIP_MAGIC):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content does not match Excel OpenXML spreadsheet signature.",
            )
        # Deep inspection of ZIP container structure with decompression safety checks
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                infolist = zf.infolist()
                if len(infolist) > MAX_ZIP_ENTRIES:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File archive exceeds maximum allowed entry count (decompression safety limit).",
                    )
                total_uncompressed = sum(info.file_size for info in infolist)
                if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File archive exceeds maximum allowed uncompressed size (decompression safety limit).",
                    )
                namelist = zf.namelist()
                has_content_types = "[Content_Types].xml" in namelist
                has_xl = any(name.startswith("xl/") for name in namelist)
                if not (has_content_types and has_xl):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File content does not match valid Excel OpenXML package structure.",
                    )
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content is not a valid ZIP archive for Excel spreadsheet.",
            )
        return (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "BOQ Spreadsheet",
            "boq",
        )

    elif ext == ".docx":
        if not first_bytes.startswith(ZIP_MAGIC):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content does not match Word OpenXML document signature.",
            )
        # Deep inspection of ZIP container structure with decompression safety checks
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                infolist = zf.infolist()
                if len(infolist) > MAX_ZIP_ENTRIES:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File archive exceeds maximum allowed entry count (decompression safety limit).",
                    )
                total_uncompressed = sum(info.file_size for info in infolist)
                if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File archive exceeds maximum allowed uncompressed size (decompression safety limit).",
                    )
                namelist = zf.namelist()
                has_content_types = "[Content_Types].xml" in namelist
                has_word = any(name.startswith("word/") for name in namelist)
                if not (has_content_types and has_word):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File content does not match valid Word OpenXML package structure.",
                    )
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File content is not a valid ZIP archive for Word document.",
            )
        return (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Legal Contract",
            "contract",
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unsupported file format '{ext}'.",
    )


async def allocate_document_code(db: AsyncSession, project_id: UUID) -> str:
    """
    Allocates a safe sequential public document code (e.g. DOC-01, DOC-02...)
    scoped to the target project workspace.
    Requires caller to hold a row lock on the parent project row to serialize concurrent allocations.
    """
    stmt = select(Document.code).where(Document.project_id == project_id)
    result = await db.execute(stmt)
    existing_codes = result.scalars().all()

    max_num = 0
    pattern = re.compile(r"^DOC-(\d+)$")
    for c in existing_codes:
        m = pattern.match(c.strip())
        if m:
            try:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    next_num = max_num + 1
    return f"DOC-{next_num:02d}"


async def upload_and_create_document(
    db: AsyncSession,
    storage: StorageProvider,
    project: Project,
    uploader: User,
    upload_file: UploadFile,
    override_category: Optional[str] = None,
) -> Document:
    """
    Handles streaming file upload, validation, storage persistence, and database registration.
    Applies compensating storage cleanup if database insertion fails.
    """
    # 1. Sanitize filename and validate extension
    safe_filename, ext = sanitize_filename(upload_file.filename or "")

    # 2. Stream file and enforce size limits without loading arbitrarily large payloads into RAM
    max_size = settings.MAX_UPLOAD_SIZE_BYTES
    content_chunks = []
    total_bytes = 0
    first_chunk = True
    first_bytes = b""

    chunk_size = 64 * 1024  # 64 KB chunks
    while True:
        chunk = await upload_file.read(chunk_size)
        if not chunk:
            break
        if first_chunk:
            first_bytes = chunk[:512]
            first_chunk = False
        total_bytes += len(chunk)
        if total_bytes > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds maximum allowed upload size of {format_file_size(max_size)}.",
            )
        content_chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="File cannot be empty.",
        )

    file_bytes = b"".join(content_chunks)

    # 3. Validate header signature (magic bytes) and package structure
    mime_type, file_type, default_category = validate_file_signature(ext, first_bytes, file_bytes)
    category = override_category or default_category

    # 4. Bind identifiers upfront and generate unpredictable collision-resistant private storage path
    project_id = project.id
    uploader_id = uploader.id
    uploader_name = uploader.full_name
    random_doc_id = uuid.uuid4()
    storage_path = f"projects/{project_id}/{random_doc_id}/{safe_filename}"

    # 5. Upload to private storage provider
    try:
        await storage.upload(
            path=storage_path,
            content=file_bytes,
            content_type=mime_type,
        )
    except StorageError as exc:
        logger.error("Storage upload failure for project %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store document in private storage provider.",
        ) from exc

    # 6. Database registration with concurrency lock on project row
    try:
        # Lock project row to serialize document code allocation
        await db.execute(
            select(Project.id).where(Project.id == project_id).with_for_update()
        )

        doc_code = await allocate_document_code(db, project_id)

        document = Document(
            id=random_doc_id,
            code=doc_code,
            project_id=project_id,
            user_id=uploader_id,
            name=safe_filename,
            file_type=file_type,
            document_category=category,
            file_size_bytes=total_bytes,
            file_size_human=format_file_size(total_bytes),
            storage_path=storage_path,
            mime_type=mime_type,
            status="Pending Analysis",
            analysis_status="unprocessed",
            uploaded_by=uploader_name,
            metadata_json={"extension": ext, "originalName": safe_filename},
        )
        db.add(document)

        # Log project activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=uploader_id,
            actor_name=uploader_name,
            action=f"Document uploaded: {safe_filename} ({doc_code})",
            action_urdu=f"دستاویز اپ لوڈ کی گئی: {safe_filename}",
            activity_type="upload",
            metadata_json={
                "documentId": str(document.id),
                "code": doc_code,
                "name": safe_filename,
                "size": document.file_size_human,
                "category": category,
            },
        )
        db.add(activity)

        await db.commit()
        await db.refresh(document)
        logger.info(
            "Document created successfully: %s (%s) in project %s",
            document.id,
            document.code,
            project_id,
        )
        return document

    except Exception as exc:
        # 7. Compensating transaction: remove orphan storage object if DB commit fails
        await db.rollback()
        masked_log_path = f"projects/{project_id}/{random_doc_id}/[REDACTED]"
        logger.warning(
            "DB write failed for document %s; executing compensating storage cleanup on %s: %s",
            random_doc_id,
            masked_log_path,
            exc,
        )
        try:
            await storage.delete(storage_path)
        except Exception as cleanup_exc:
            logger.critical(
                "ORPHAN STORAGE OBJECT DETECTED: Storage cleanup failed for document %s at %s after database rollback: %s. "
                "Requires external reconciliation / persistent retry outbox.",
                random_doc_id,
                masked_log_path,
                cleanup_exc,
            )

        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register document in project database.",
        ) from exc


async def get_document_by_identifier(
    db: AsyncSession,
    project: Project,
    identifier: str,
) -> Optional[Document]:
    """
    Looks up a document strictly within the authorized project workspace.
    Accepts either an internal UUID or a public document code (e.g. DOC-01).
    """
    clean_id = identifier.strip()
    try:
        uuid_val = UUID(clean_id)
        stmt = select(Document).where(
            Document.id == uuid_val,
            Document.project_id == project.id,
        )
        return await db.scalar(stmt)
    except (ValueError, TypeError):
        # Query by public code scoped strictly to project
        stmt = select(Document).where(
            Document.code == clean_id,
            Document.project_id == project.id,
        )
        return await db.scalar(stmt)


async def list_project_documents(
    db: AsyncSession,
    project: Project,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
) -> Tuple[List[Document], int]:
    """
    Returns paginated list of documents belonging to the project workspace.
    """
    query = select(Document).where(Document.project_id == project.id)

    if status_filter:
        query = query.where(Document.status == status_filter.strip())

    if category_filter:
        query = query.where(Document.document_category == category_filter.strip())

    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.scalar(count_stmt)) or 0

    # Deterministic sorting: newest first
    offset = max(0, (page - 1) * page_size)
    stmt = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def generate_document_download_url(
    storage: StorageProvider,
    document: Document,
    expires_in_seconds: int = 300,
) -> DocumentDownloadUrl:
    """
    Generates a secure, short-lived signed download URL for the document.
    Verifies that the object exists in storage prior to signing.
    """
    exists = await storage.exists(document.storage_path)
    if not exists:
        logger.warning(
            "Document record %s exists in DB, but storage object is missing at %s",
            document.id,
            document.storage_path,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file object is not available in storage.",
        )

    try:
        signed_url = await storage.get_signed_url(
            path=document.storage_path,
            expires_in_seconds=expires_in_seconds,
        )
        return DocumentDownloadUrl(
            downloadUrl=signed_url,
            expiresInSeconds=expires_in_seconds,
            filename=document.name,
            mimeType=document.mime_type,
        )
    except StorageError as exc:
        logger.error("Failed to generate signed download URL for document %s: %s", document.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secure download link.",
        ) from exc

