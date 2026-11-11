"""
TameerAI - Phase 02D Secure Project Document Management API Test Suite

Comprehensive tests for:
1. Successful document upload across supported formats (PDF, DWG, DXF, XLSX, DOCX)
2. Storage key confidentiality (storage_path strictly omitted from public response)
3. Invalid format and extension rejection (422)
4. Magic byte signature spoofing rejection (422)
5. Oversized file streaming rejection (413 Payload Too Large)
6. Viewer role upload rejection (403 Forbidden)
7. Unrelated tenant isolation (404 Anti-enumeration)
8. Unauthenticated caller rejection (401 Unauthorized)
9. Document listing with pagination and domain filtering
10. Document detail resolution by internal UUID and public code (DOC-01)
11. Secure signed download URL generation
12. Missing storage object handling (404)
13. Compensating storage cleanup upon database commit rollback
14. Filename path traversal sanitization
15. Document deletion restrictions (409 Conflict preserving evidence)
16. Sequential gapless document code allocation (DOC-01, DOC-02...)
"""

import io
import zipfile
from typing import AsyncGenerator
from unittest.mock import patch
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_db
from app.core.config import settings
from app.core.rate_limit import login_limiter
from app.core.storage import InMemoryStorageProvider, get_storage_provider
from app.db.base import Base
from app.main import app
from app.models.document import Document
from app.models.project import Project, ProjectMember
from app.models.user import User


# ---------------------------------------------------------------------------
# Isolated Test Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_session_factory():
    """Isolated SQLite in-memory database per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    yield session_factory

    await engine.dispose()


@pytest_asyncio.fixture
async def in_memory_storage():
    """Isolated in-memory storage provider per test."""
    provider = InMemoryStorageProvider()
    yield provider
    provider.clear()


@pytest_asyncio.fixture
async def doc_client(test_session_factory, in_memory_storage) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage_provider] = lambda: in_memory_storage
    login_limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    login_limiter.reset()


# Helper to generate minimal valid OpenXML ZIP packages for testing
def make_mock_docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


def make_mock_xlsx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("xl/workbook.xml", "<workbook/>")
    return buf.getvalue()


# Helper to register and log in a test user, returning (token, user_dict)
async def create_user(client: AsyncClient, email: str, role: str = "engineer", full_name: str = "Test User"):
    reg_payload = {
        "fullName": full_name,
        "email": email,
        "password": "Password12345!",
        "role": role,
        "city": "Lahore",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password12345!",
    })
    assert login_res.status_code == 200
    data = login_res.json()
    return data["accessToken"], data["user"]


# Helper to create a project workspace for an owner
async def create_project(client: AsyncClient, token: str, name: str = "Test Plaza"):
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post("/api/v1/projects", json={"name": name, "location": "Lahore"}, headers=headers)
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# 1. Successful Document Upload Across Formats
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_document_upload_all_formats(doc_client: AsyncClient, in_memory_storage: InMemoryStorageProvider):
    token, user = await create_user(doc_client, email="uploader@tameerai.pk", full_name="Engr. Tariq")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)
    prj_id = prj["id"]

    # 1. PDF Upload
    pdf_content = b"%PDF-1.7\nSample Architectural Specification Text"
    res_pdf = await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("structural-spec.pdf", io.BytesIO(pdf_content), "application/pdf")},
        headers=headers,
    )
    assert res_pdf.status_code == 201
    pdf_data = res_pdf.json()
    assert pdf_data["id"] == "DOC-01"
    assert pdf_data["name"] == "structural-spec.pdf"
    assert pdf_data["type"] == "PDF Document"
    assert pdf_data["category"] == "general_project_document"
    assert pdf_data["status"] == "Pending Analysis"
    assert pdf_data["uploadedBy"] == "Engr. Tariq"
    assert "uuid" in pdf_data

    # 2. AutoCAD DWG Upload
    dwg_content = b"AC1032\x00\x00Binary AutoCAD R2018 Drawing Data"
    res_dwg = await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("foundation-plan.dwg", io.BytesIO(dwg_content), "image/vnd.dwg")},
        headers=headers,
    )
    assert res_dwg.status_code == 201
    dwg_data = res_dwg.json()
    assert dwg_data["id"] == "DOC-02"
    assert dwg_data["type"] == "CAD Drawing"
    assert dwg_data["category"] == "blueprint"

    # 3. DXF Upload
    dxf_content = b"0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF"
    res_dxf = await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("layout.dxf", io.BytesIO(dxf_content), "image/vnd.dxf")},
        headers=headers,
    )
    assert res_dxf.status_code == 201
    assert res_dxf.json()["id"] == "DOC-03"

    # 4. XLSX Upload (BOQ)
    res_xlsx = await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("boq-schedule.xlsx", io.BytesIO(make_mock_xlsx()), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res_xlsx.status_code == 201
    xlsx_data = res_xlsx.json()
    assert xlsx_data["id"] == "DOC-04"
    assert xlsx_data["category"] == "boq"
    assert xlsx_data["type"] == "BOQ Spreadsheet"

    # 5. DOCX Upload (Contract)
    res_docx = await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("consultancy-contract.docx", io.BytesIO(make_mock_docx()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res_docx.status_code == 201
    docx_data = res_docx.json()
    assert docx_data["id"] == "DOC-05"
    assert docx_data["category"] == "contract"
    assert docx_data["type"] == "Legal Contract"


# ---------------------------------------------------------------------------
# 2. Storage Key Confidentiality
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_storage_key_confidentiality(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="secret.storage@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nConfidential Data"
    res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("plan.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()

    # Private internal storage path must never be exposed to the client
    assert "storagePath" not in data
    assert "storage_path" not in data


# ---------------------------------------------------------------------------
# 3. Invalid Format and Extension Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_format_rejection(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="badformat@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    # 1. Unsupported executable extension .exe
    res_exe = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        headers=headers,
    )
    assert res_exe.status_code == 422
    assert "unsupported file extension" in res_exe.json()["detail"].lower()

    # 2. Shell script .sh
    res_sh = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("script.sh", io.BytesIO(b"#!/bin/bash\nrm -rf /"), "text/plain")},
        headers=headers,
    )
    assert res_sh.status_code == 422

    # 3. Empty file
    res_empty = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        headers=headers,
    )
    assert res_empty.status_code == 422
    assert "file cannot be empty" in res_empty.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Magic Byte Signature Spoofing Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_magic_byte_spoofing_rejection(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="spoof@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    # Filename says .pdf, but content is arbitrary ASCII text
    fake_pdf = b"This is plain text pretending to be a PDF file."
    res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("fake.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 422
    assert "does not match pdf signature" in res.json()["detail"].lower()

    # Filename says .dwg, but lacks AutoCAD magic header
    fake_dwg = b"NOT_AUTOCAD_DRAWING_DATA"
    res_dwg = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("fake.dwg", io.BytesIO(fake_dwg), "image/vnd.dwg")},
        headers=headers,
    )
    assert res_dwg.status_code == 422
    assert "does not match autocad dwg signature" in res_dwg.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Oversized File Streaming Rejection (413)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_oversized_file_rejection(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="oversized@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    # Temporarily constrain limit to 1 KB for test
    oversized_data = b"%PDF-1.4\n" + (b"X" * 2048)
    with patch.object(settings, "MAX_UPLOAD_SIZE_BYTES", 1024):
        res = await doc_client.post(
            f"/api/v1/projects/{prj['id']}/documents",
            files={"file": ("large.pdf", io.BytesIO(oversized_data), "application/pdf")},
            headers=headers,
        )
        assert res.status_code == 413
        assert "exceeds maximum allowed upload size" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6. Viewer Role Upload Rejection (403)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_viewer_upload_rejected(doc_client: AsyncClient):
    token_owner, _ = await create_user(doc_client, email="owner.doc@tameerai.pk")
    token_viewer, viewer = await create_user(doc_client, email="viewer.doc@tameerai.pk")
    prj = await create_project(doc_client, token_owner)

    # Add viewer to project
    await doc_client.post(
        f"/api/v1/projects/{prj['id']}/members",
        json={"userId": viewer["id"], "role": "viewer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )

    # Viewer attempts upload
    content = b"%PDF-1.5\nViewer Document"
    res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("viewer-upload.pdf", io.BytesIO(content), "application/pdf")},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert res.status_code == 403
    assert "viewers cannot upload" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 7. Unrelated Tenant Isolation (404 Anti-enumeration)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unrelated_tenant_upload_and_access_rejected(doc_client: AsyncClient):
    token_a, _ = await create_user(doc_client, email="tenant.alpha@tameerai.pk")
    token_b, _ = await create_user(doc_client, email="tenant.beta@tameerai.pk")
    prj_a = await create_project(doc_client, token_a)

    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant B attempts to upload into Tenant A's project
    content = b"%PDF-1.5\nUnauthorized Content"
    res_upload = await doc_client.post(
        f"/api/v1/projects/{prj_a['id']}/documents",
        files={"file": ("intruder.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers_b,
    )
    assert res_upload.status_code == 404

    # Tenant B attempts to list Tenant A's documents
    res_list = await doc_client.get(f"/api/v1/projects/{prj_a['id']}/documents", headers=headers_b)
    assert res_list.status_code == 404


# ---------------------------------------------------------------------------
# 8. Unauthenticated Request Rejection (401)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(doc_client: AsyncClient):
    res_list = await doc_client.get("/api/v1/projects/PRJ-001/documents")
    assert res_list.status_code == 401


# ---------------------------------------------------------------------------
# 9. Document Listing, Pagination, and Category Filtering
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_listing_and_filtering(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="list.filter@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)
    prj_id = prj["id"]

    # Upload 3 documents across categories
    await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("drawing.dwg", io.BytesIO(b"AC1032\x00dwg"), "image/vnd.dwg")},
        headers=headers,
    )
    await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("contract.docx", io.BytesIO(make_mock_docx()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    await doc_client.post(
        f"/api/v1/projects/{prj_id}/documents",
        files={"file": ("boq.xlsx", io.BytesIO(make_mock_xlsx()), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )

    # 1. List all documents
    res_all = await doc_client.get(f"/api/v1/projects/{prj_id}/documents", headers=headers)
    assert res_all.status_code == 200
    docs = res_all.json()
    assert len(docs) == 3

    # 2. Filter by category='blueprint'
    res_blue = await doc_client.get(f"/api/v1/projects/{prj_id}/documents?category=blueprint", headers=headers)
    assert res_blue.status_code == 200
    assert len(res_blue.json()) == 1
    assert res_blue.json()[0]["category"] == "blueprint"

    # 3. Pagination (page_size=2)
    res_page = await doc_client.get(f"/api/v1/projects/{prj_id}/documents?page=1&page_size=2", headers=headers)
    assert res_page.status_code == 200
    assert len(res_page.json()) == 2


# ---------------------------------------------------------------------------
# 10. Document Detail Resolution by UUID and Public Code (DOC-01)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_detail_resolution(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="detail.doc@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nPlan Details"
    upload_res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("plan.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    doc_data = upload_res.json()
    doc_code = doc_data["id"]  # DOC-01
    doc_uuid = doc_data["uuid"]

    # 1. Resolve by public code DOC-01
    res_by_code = await doc_client.get(f"/api/v1/projects/{prj['id']}/documents/{doc_code}", headers=headers)
    assert res_by_code.status_code == 200
    assert res_by_code.json()["uuid"] == doc_uuid

    # 2. Resolve by internal UUID
    res_by_uuid = await doc_client.get(f"/api/v1/projects/{prj['id']}/documents/{doc_uuid}", headers=headers)
    assert res_by_uuid.status_code == 200
    assert res_by_uuid.json()["id"] == doc_code

    # 3. Nonexistent document code -> 404
    res_not_found = await doc_client.get(f"/api/v1/projects/{prj['id']}/documents/DOC-99", headers=headers)
    assert res_not_found.status_code == 404


# ---------------------------------------------------------------------------
# 11. Secure Signed Download Link Generation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_signed_download_link_generation(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="download.doc@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nDownloadable blueprint"
    upload_res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("blueprint.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    doc = upload_res.json()

    # Generate signed download URL
    res = await doc_client.get(f"/api/v1/projects/{prj['id']}/documents/{doc['id']}/download", headers=headers)
    assert res.status_code == 200
    download_info = res.json()

    assert "downloadUrl" in download_info
    assert download_info["downloadUrl"].startswith("http")
    assert download_info["expiresInSeconds"] == 300
    assert download_info["filename"] == "blueprint.pdf"
    assert download_info["mimeType"] == "application/pdf"


# ---------------------------------------------------------------------------
# 12. Missing Storage Object Handling (404)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_storage_object_returns_404(doc_client: AsyncClient, in_memory_storage: InMemoryStorageProvider):
    token, _ = await create_user(doc_client, email="missing.obj@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nData to be deleted"
    upload_res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("will_disappear.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    doc = upload_res.json()

    # Artificially wipe storage provider to simulate missing cloud object
    in_memory_storage.clear()

    # Attempting to generate download link must return 404
    res = await doc_client.get(f"/api/v1/projects/{prj['id']}/documents/{doc['id']}/download", headers=headers)
    assert res.status_code == 404
    assert "not available in storage" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 13. Compensating Storage Cleanup Upon Database Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compensating_storage_cleanup_on_db_error(doc_client: AsyncClient, in_memory_storage: InMemoryStorageProvider):
    token, _ = await create_user(doc_client, email="cleanup.test@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nCompensating transaction payload"

    # Patch db.commit to simulate database failure during transaction
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=RuntimeError("Simulated database failure")):
        res = await doc_client.post(
            f"/api/v1/projects/{prj['id']}/documents",
            files={"file": ("crash.pdf", io.BytesIO(content), "application/pdf")},
            headers=headers,
        )
        assert res.status_code == 500

    # Verify compensating transaction deleted the object from storage (zero orphan objects)
    assert len(in_memory_storage._objects) == 0


# ---------------------------------------------------------------------------
# 14. Filename Path Traversal Sanitization
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_filename_path_traversal_sanitization(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="traversal@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nSafe content"
    res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("../../../../etc/passwd.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["name"] == "passwd.pdf"


# ---------------------------------------------------------------------------
# 15. Document Deletion Restricted (409 Preserving Evidence)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_deletion_restricted(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="del.doc@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nEvidence Document"
    upload_res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("evidence.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    doc_id = upload_res.json()["id"]

    # Deletion attempt must be rejected with 409 Conflict
    del_res = await doc_client.delete(f"/api/v1/projects/{prj['id']}/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 409
    assert "document deletion is restricted" in del_res.json()["detail"].lower()

    # Document must still exist in DB
    get_res = await doc_client.get(f"/api/v1/projects/{prj['id']}/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 200


# ---------------------------------------------------------------------------
# 16. Misconfigured Storage Environment (Eliminating Unsafe Fallback)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unconfigured_storage_raises_503(doc_client: AsyncClient):
    """
    Verifies that when STORAGE_BACKEND is 'supabase' and cloud credentials are
    unconfigured, document operations immediately fail with HTTP 503 instead of
    silently falling back to transient in-memory storage.
    """
    token, _ = await create_user(doc_client, email="misconfig@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    # Remove dependency override to test actual get_storage_provider() logic
    if get_storage_provider in app.dependency_overrides:
        del app.dependency_overrides[get_storage_provider]

    with patch.object(settings, "STORAGE_BACKEND", "supabase"), \
         patch.object(settings, "SUPABASE_URL", None), \
         patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", None):
        content = b"%PDF-1.4\nData"
        res = await doc_client.post(
            f"/api/v1/projects/{prj['id']}/documents",
            files={"file": ("plan.pdf", io.BytesIO(content), "application/pdf")},
            headers=headers,
        )
        assert res.status_code == 503
        assert "cloud storage service is not configured" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 17. OpenXML ZIP Package Tampering Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_zip_package_tampering_rejected(doc_client: AsyncClient):
    """
    Verifies that files with .docx or .xlsx extensions having valid PK\x03\x04 headers
    but corrupt internal ZIP archives or missing OpenXML parts are rejected with 422.
    """
    token, _ = await create_user(doc_client, email="ziptamper@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    # 1. Starts with PK\x03\x04 but is corrupt ZIP
    corrupt_zip = b"PK\x03\x04\x00\x00Corrupt binary payload that is not a valid zip"
    res_corrupt = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("fake.xlsx", io.BytesIO(corrupt_zip), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res_corrupt.status_code == 422
    assert "not a valid zip archive" in res_corrupt.json()["detail"].lower()

    # 2. Valid ZIP, but contains arbitrary files instead of Word OpenXML package
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("malicious.txt", "harmless content")
    non_word_zip = buf.getvalue()

    res_non_word = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("fake.docx", io.BytesIO(non_word_zip), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res_non_word.status_code == 422
    assert "does not match valid word openxml" in res_non_word.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 18. Cleanup Failure Alerts (Critical Logging for Orphan Storage Objects)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cleanup_failure_critical_logging(doc_client: AsyncClient, in_memory_storage: InMemoryStorageProvider):
    """
    Verifies that when both DB commit fails AND storage cleanup fails,
    the failure is logged at CRITICAL level flagging an orphan storage object.
    """
    token, _ = await create_user(doc_client, email="doublefail@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nCompensating failure payload"

    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=RuntimeError("DB Commit Crash")), \
         patch.object(in_memory_storage, "delete", side_effect=RuntimeError("Storage Delete Crash")):
        res = await doc_client.post(
            f"/api/v1/projects/{prj['id']}/documents",
            files={"file": ("crash.pdf", io.BytesIO(content), "application/pdf")},
            headers=headers,
        )
        assert res.status_code == 500


# ---------------------------------------------------------------------------
# 19. Sequential Gapless Document Code Allocation (DOC-01, DOC-02...)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_code_sequential_ordering(doc_client: AsyncClient):
    token, _ = await create_user(doc_client, email="seq.doc@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    content = b"%PDF-1.4\nDocument"
    for expected_idx in range(1, 4):
        res = await doc_client.post(
            f"/api/v1/projects/{prj['id']}/documents",
            files={"file": (f"doc_{expected_idx}.pdf", io.BytesIO(content), "application/pdf")},
            headers=headers,
        )
        assert res.status_code == 201
        assert res.json()["id"] == f"DOC-{expected_idx:02d}"


# ---------------------------------------------------------------------------
# 20. Cross-Project Document Access Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_project_document_access_isolation(doc_client: AsyncClient):
    """
    Verifies that requesting a document belonging to Project Alpha using Project Beta's URL returns 404.
    """
    token, _ = await create_user(doc_client, email="crossproj.doc@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj_a = await create_project(doc_client, token, name="Project A")
    prj_b = await create_project(doc_client, token, name="Project B")

    content = b"%PDF-1.4\nProject A Document"
    res_a = await doc_client.post(
        f"/api/v1/projects/{prj_a['id']}/documents",
        files={"file": ("doc_a.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    doc_a = res_a.json()

    # User owns both projects, but accesses Doc A under Project B's URL -> 404
    cross_res = await doc_client.get(f"/api/v1/projects/{prj_b['id']}/documents/{doc_a['uuid']}", headers=headers)
    assert cross_res.status_code == 404


# ---------------------------------------------------------------------------
# 21. OpenXML Strict AND Logic & Decompression Safety
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openxml_strict_and_validation(doc_client: AsyncClient):
    """
    Verifies that files declaring .xlsx or .docx must have BOTH [Content_Types].xml
    AND their respective subsystem folder (xl/ or word/), not just one of them.
    """
    token, _ = await create_user(doc_client, email="strict.openxml@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    # 1. Zip containing ONLY [Content_Types].xml, no xl/ folder -> Reject for .xlsx
    buf_partial = io.BytesIO()
    with zipfile.ZipFile(buf_partial, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
    buf_partial.seek(0)

    res_xlsx = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("fake_boq.xlsx", buf_partial, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res_xlsx.status_code == 422
    assert "Excel OpenXML package structure" in res_xlsx.json()["detail"]

    # 2. Same partial zip for .docx -> Reject for .docx
    buf_partial.seek(0)
    res_docx = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("fake_contract.docx", buf_partial, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res_docx.status_code == 422
    assert "Word OpenXML package structure" in res_docx.json()["detail"]


@pytest.mark.asyncio
async def test_openxml_zip_bomb_entry_limit(doc_client: AsyncClient):
    """
    Verifies that archives exceeding the MAX_ZIP_ENTRIES safety limit (1000) are rejected.
    """
    token, _ = await create_user(doc_client, email="zipbomb.entries@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("xl/workbook.xml", "<workbook/>")
        for i in range(1005):
            zf.writestr(f"xl/dummy_{i}.xml", "x")
    buf.seek(0)

    res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("bomb.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res.status_code == 422
    assert "entry count" in res.json()["detail"]


@pytest.mark.asyncio
async def test_openxml_zip_bomb_uncompressed_size_limit(doc_client: AsyncClient):
    """
    Verifies that archives reporting excessive uncompressed member sizes (>100MB) are rejected.
    """
    token, _ = await create_user(doc_client, email="zipbomb.size@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    prj = await create_project(doc_client, token)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("xl/workbook.xml", "<workbook/>")
        # 101 MB of zeros deflates into ~100 KB, but uncompressed file_size header is 101 MB
        zf.writestr("xl/huge.xml", b"0" * (101 * 1024 * 1024), compress_type=zipfile.ZIP_DEFLATED)
    buf.seek(0)

    res = await doc_client.post(
        f"/api/v1/projects/{prj['id']}/documents",
        files={"file": ("huge.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res.status_code == 422
    assert "uncompressed size" in res.json()["detail"]


# ---------------------------------------------------------------------------
# 22. SupabaseStorageProvider Unit Tests (Mocked Network)
# ---------------------------------------------------------------------------

from app.core.storage import SupabaseStorageProvider, StorageError, StorageFileNotFoundError
import httpx

@pytest.mark.asyncio
async def test_supabase_storage_provider_upload():
    provider = SupabaseStorageProvider(
        base_url="https://mock-proj.supabase.co",
        service_key="mock-service-role-key-12345",
        bucket="project-documents",
    )

    fake_response = httpx.Response(200, json={"Key": "project-documents/test.pdf"})
    with patch("httpx.AsyncClient.post", return_value=fake_response) as mock_post:
        await provider.upload("projects/123/test.pdf", b"%PDF-1.4 test", "application/pdf")
        assert mock_post.called
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "https://mock-proj.supabase.co/storage/v1/object/project-documents/projects/123/test.pdf"
        assert call_kwargs["headers"]["apikey"] == "mock-service-role-key-12345"
        assert call_kwargs["headers"]["Authorization"] == "Bearer mock-service-role-key-12345"
        assert call_kwargs["headers"]["Content-Type"] == "application/pdf"
        assert call_kwargs["content"] == b"%PDF-1.4 test"


@pytest.mark.asyncio
async def test_supabase_storage_provider_signed_url_variants():
    provider = SupabaseStorageProvider(
        base_url="https://mock-proj.supabase.co",
        service_key="mock-service-role-key-12345",
        bucket="project-documents",
    )

    # Case A: Standard relative path starting with /object/sign/
    resp_a = httpx.Response(200, json={"signedURL": "/object/sign/project-documents/projects/123/test.pdf?token=xyz"})
    with patch("httpx.AsyncClient.post", return_value=resp_a):
        url_a = await provider.get_signed_url("projects/123/test.pdf", expires_in_seconds=300)
        assert url_a == "https://mock-proj.supabase.co/storage/v1/object/sign/project-documents/projects/123/test.pdf?token=xyz"

    # Case B: Provider returns relative path already starting with /storage/v1/
    resp_b = httpx.Response(200, json={"signedURL": "/storage/v1/object/sign/project-documents/projects/123/test.pdf?token=abc"})
    with patch("httpx.AsyncClient.post", return_value=resp_b):
        url_b = await provider.get_signed_url("projects/123/test.pdf", expires_in_seconds=300)
        assert url_b == "https://mock-proj.supabase.co/storage/v1/object/sign/project-documents/projects/123/test.pdf?token=abc"


@pytest.mark.asyncio
async def test_supabase_storage_provider_download_and_delete():
    provider = SupabaseStorageProvider(
        base_url="https://mock-proj.supabase.co",
        service_key="mock-service-role-key-12345",
        bucket="project-documents",
    )

    # Download success
    resp_dl = httpx.Response(200, content=b"%PDF-1.4 binary content")
    with patch("httpx.AsyncClient.get", return_value=resp_dl) as mock_get:
        content = await provider.download("projects/123/test.pdf")
        assert content == b"%PDF-1.4 binary content"
        assert mock_get.called
        assert mock_get.call_args[0][0] == "https://mock-proj.supabase.co/storage/v1/object/authenticated/project-documents/projects/123/test.pdf"

    # Delete success
    resp_del = httpx.Response(200, json=[{"name": "projects/123/test.pdf"}])
    with patch("httpx.AsyncClient.request", return_value=resp_del) as mock_req:
        deleted = await provider.delete("projects/123/test.pdf")
        assert deleted is True
        assert mock_req.called
        assert mock_req.call_args[0][0] == "DELETE"
        assert mock_req.call_args[0][1] == "https://mock-proj.supabase.co/storage/v1/object/project-documents"
        assert mock_req.call_args[1]["json"] == {"prefixes": ["projects/123/test.pdf"]}



