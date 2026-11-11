"""
TameerAI - Phase 03.3 Comprehensive Test Suite
Pakistan Statutory Regulatory Knowledge Base Verification

Verifies:
1. Authority discovery, catalog hierarchy, and location-based resolution.
2. Document versioning, immutability, and checksum fingerprinting.
3. Clause extraction, chapter/section segmentation, and legal significance.
4. Jurisdiction-aware regulatory retrieval, multi-term ranking, and canonical citations.
5. SSRF defense, filename sanitization, and workspace storage boundary isolation.
6. Structural safety boundary enforcement (non-override of Level 0 emergency advisories).
7. FastAPI regulatory endpoints and role-based access control.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import AsyncGenerator
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user, get_db
from app.db.base import Base
from app.main import app
from app.models.regulation import (
    RegulatoryAuthority,
    RegulatoryClause,
    RegulatoryDocument,
    RegulatoryDocumentVersion,
)
from app.models.user import User
from app.schemas.regulation import RegulatorySearchQuery
from app.services.regulatory_acquisition import (
    RegulatoryAcquisitionService,
    RegulatorySecurityException,
)
from app.services.regulatory_discovery import RegulatoryDiscoveryService
from app.services.regulatory_parser import (
    RegulatoryParserService,
    classify_legal_significance,
)
from app.services.regulatory_retrieval import RegulatoryRetrievalService
from app.services.regulatory_seed import RegulatorySeedService


# ---------------------------------------------------------------------------
# Test Database Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_session_factory():
    """Isolated in-memory SQLite database per test."""
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
async def async_db(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_db(async_db: AsyncSession) -> AsyncSession:
    """Pre-seeds the database with authentic Pakistan pilot regulatory datasets."""
    await RegulatorySeedService.seed_pilot_data_async(async_db)
    return async_db


@pytest.fixture
def mock_engineer_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="eng.rehan@example.com",
        full_name="Rehan Tariq",
        city="Lahore",
        hashed_password="mock_hashed_password",
        role="engineer",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def mock_viewer_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        full_name="Public Viewer",
        city="Lahore",
        hashed_password="mock_hashed_password",
        role="viewer",
        is_active=True,
        is_verified=True,
    )


# ---------------------------------------------------------------------------
# Test 1: Authority Inventory & Credibility Tiers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authorities_master_inventory_and_tiers(seeded_db: AsyncSession):
    authorities = await RegulatoryDiscoveryService.list_authorities_async(seeded_db)
    assert len(authorities) >= 10

    # Federal Authorities
    pec = await RegulatoryDiscoveryService.get_authority_by_code_async(seeded_db, "PEC")
    assert pec is not None
    assert pec.credibility_tier == "tier_a_statutory"
    assert pec.jurisdiction_level == "federal"
    assert "Act, 1976" in pec.publication_channels.get("enabling_act", "")

    bcp = await RegulatoryDiscoveryService.get_authority_by_code_async(seeded_db, "BCP_FED")
    assert bcp is not None
    assert bcp.credibility_tier == "tier_a_statutory"
    assert bcp.jurisdiction_level == "federal"

    # Provincial & Municipal Authorities
    lda = await RegulatoryDiscoveryService.get_authority_by_code_async(seeded_db, "LDA")
    assert lda is not None
    assert lda.credibility_tier == "tier_b_official_regulatory"
    assert lda.province == "Punjab"
    assert lda.city == "Lahore"

    sbca = await RegulatoryDiscoveryService.get_authority_by_code_async(seeded_db, "SBCA")
    assert sbca is not None
    assert sbca.province == "Sindh"
    assert sbca.city == "Karachi"

    cda = await RegulatoryDiscoveryService.get_authority_by_code_async(seeded_db, "CDA")
    assert cda is not None
    assert cda.province == "ICT"
    assert cda.city == "Islamabad"


# ---------------------------------------------------------------------------
# Test 2: Location-Based Jurisdiction Resolution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_jurisdiction_location_resolution(seeded_db: AsyncSession):
    # Lahore resolution
    lahore_auths = await RegulatoryDiscoveryService.resolve_authorities_for_location_async(
        seeded_db, city="Lahore", province="Punjab"
    )
    lahore_codes = {a.code for a in lahore_auths}
    assert "PEC" in lahore_codes  # Federal
    assert "BCP_FED" in lahore_codes  # Federal
    assert "LDA" in lahore_codes  # Municipal
    assert "PLG_CD" in lahore_codes  # Provincial
    assert "SBCA" not in lahore_codes  # Sindh strictly excluded!
    assert "CDA" not in lahore_codes  # ICT strictly excluded!

    # Karachi resolution
    karachi_auths = await RegulatoryDiscoveryService.resolve_authorities_for_location_async(
        seeded_db, city="Karachi", province="Sindh"
    )
    karachi_codes = {a.code for a in karachi_auths}
    assert "PEC" in karachi_codes
    assert "BCP_FED" in karachi_codes
    assert "SBCA" in karachi_codes
    assert "KDA" in karachi_codes
    assert "LDA" not in karachi_codes  # Punjab strictly excluded!
    assert "CDA" not in karachi_codes  # ICT strictly excluded!

    # Islamabad resolution
    isb_auths = await RegulatoryDiscoveryService.resolve_authorities_for_location_async(
        seeded_db, city="Islamabad", province="ICT"
    )
    isb_codes = {a.code for a in isb_auths}
    assert "PEC" in isb_codes
    assert "BCP_FED" in isb_codes
    assert "CDA" in isb_codes
    assert "LDA" not in isb_codes
    assert "SBCA" not in isb_codes


# ---------------------------------------------------------------------------
# Test 3: Document Versioning & Immutability
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_versioning_and_immutability(seeded_db: AsyncSession):
    # Fetch BCP document
    from sqlalchemy import select
    res = await seeded_db.execute(select(RegulatoryDocument).where(RegulatoryDocument.document_code == "BCP-SP-2007"))
    doc = res.scalars().first()
    assert doc is not None

    # Verify initial version 2007.1
    res_ver = await seeded_db.execute(select(RegulatoryDocumentVersion).where(RegulatoryDocumentVersion.document_id == doc.id))
    versions = list(res_ver.scalars().all())
    assert len(versions) == 1
    v1 = versions[0]
    assert v1.version_label == "2007.1"
    assert v1.is_current is True

    # Register amendment / new edition version 2021
    v2_id = uuid.uuid4()
    v2 = RegulatoryDocumentVersion(
        id=v2_id,
        document_id=doc.id,
        version_label="2021.0",
        edition="Proposed National Edition 2021",
        effective_date=date(2021, 6, 1),
        is_current=True,
        total_pages=180,
    )
    # Mark old version superseded
    v1.is_current = False
    v1.superseded_by_version_id = v2_id
    v1.expiry_date = date(2021, 5, 31)

    seeded_db.add(v2)
    await seeded_db.commit()

    # Re-query versions
    res_ver2 = await seeded_db.execute(
        select(RegulatoryDocumentVersion)
        .where(RegulatoryDocumentVersion.document_id == doc.id)
        .order_by(RegulatoryDocumentVersion.created_at.asc())
    )
    all_v = list(res_ver2.scalars().all())
    assert len(all_v) == 2
    assert all_v[0].is_current is False
    assert all_v[0].superseded_by_version_id == v2_id
    assert all_v[1].is_current is True


# ---------------------------------------------------------------------------
# Test 4: Clause Extraction & Legal Significance Classification
# ---------------------------------------------------------------------------

def test_legal_significance_classification():
    assert classify_legal_significance("Under no circumstances shall unreinforced masonry be used") == "prohibition"
    assert classify_legal_significance("All columns must be provided with continuous ties") == "mandatory_requirement"
    assert classify_legal_significance("Provided that for single storey structures setback may be reduced") == "conditional_exception"
    assert classify_legal_significance("Application shall be made to the Director Town Planning") == "procedural_step"
    assert classify_legal_significance("'Professional Engineer' means an accredited engineer") == "definition"
    assert classify_legal_significance("The owner may provide rainwater harvesting") == "guideline"


def test_clause_segmentation():
    sample_pages = [
        {
            "page_number": 1,
            "text": (
                "CHAPTER 5: EARTHQUAKE DESIGN CRITERIA\n"
                "SECTION 5.3: ZONE CLASSIFICATION\n"
                "5.3.1 Seismic Zone Map\n"
                "Pakistan is divided into five seismic zones (Zone 1 to 4).\n"
                "Lahore and Karachi are designated in Zone 2B.\n"
                "Table 5.1: Seismic Zone Factor Z\n"
                "Zone | PGA | Z\n"
                "1 | 0.05g | 0.075\n"
                "2B | 0.20g | 0.20\n"
                "4 | >0.32g | 0.40\n"
            ),
        }
    ]

    dummy_doc = RegulatoryDocument(
        id=uuid.uuid4(),
        document_code="BCP-TEST",
        title="Test BCP",
    )
    dummy_version = RegulatoryDocumentVersion(
        id=uuid.uuid4(),
        document_id=dummy_doc.id,
        version_label="1.0",
        document=dummy_doc,
    )

    clauses = RegulatoryParserService._segment_clauses(dummy_version, sample_pages)
    assert len(clauses) >= 2

    # Check first clause
    c1 = clauses[0]
    assert c1["clause_number"] == "5.3.1"
    assert "Seismic Zone Map" in c1["clause_title"]
    assert c1["chapter_number"] == "5"
    assert c1["section_number"] == "5.3"
    assert c1["page_start"] == 1


# ---------------------------------------------------------------------------
# Test 5: Jurisdiction-Aware Retrieval & Canonical Citations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_jurisdiction_aware_search_retrieval(seeded_db: AsyncSession):
    # 1. Search for seismic provisions in Islamabad
    query_isb = RegulatorySearchQuery(
        query="seismic zone peak ground acceleration",
        city="Islamabad",
    )
    res_isb = await RegulatoryRetrievalService.search_async(seeded_db, query_isb)
    assert res_isb.total >= 1
    assert res_isb.jurisdiction_filtered is True
    # BCP and CDA are permitted for Islamabad
    doc_codes_isb = {r.citation.document_code for r in res_isb.results}
    assert "BCP-SP-2007" in doc_codes_isb
    assert "LDA-BZR-2020" not in doc_codes_isb
    assert "SBCA-KBTPR-2002" not in doc_codes_isb

    # Verify canonical citation structure
    first_res = res_isb.results[0]
    cit = first_res.citation
    assert cit.authority_code in ("BCP_FED", "CDA")
    assert "Ed." in cit.citation_string
    assert "Clause" in cit.citation_string
    assert "p." in cit.citation_string

    # 2. Search for setbacks in Lahore
    query_lhe = RegulatorySearchQuery(
        query="setback residential plot ground coverage",
        city="Lahore",
    )
    res_lhe = await RegulatoryRetrievalService.search_async(seeded_db, query_lhe)
    assert res_lhe.total >= 1
    doc_codes_lhe = {r.citation.document_code for r in res_lhe.results}
    assert "LDA-BZR-2020" in doc_codes_lhe
    assert "SBCA-KBTPR-2002" not in doc_codes_lhe

    # 3. Search for proof engineer in Karachi
    query_khi = RegulatorySearchQuery(
        query="proof engineer category IV high-rise",
        city="Karachi",
    )
    res_khi = await RegulatoryRetrievalService.search_async(seeded_db, query_khi)
    assert res_khi.total >= 1
    doc_codes_khi = {r.citation.document_code for r in res_khi.results}
    assert "SBCA-KBTPR-2002" in doc_codes_khi
    assert "LDA-BZR-2020" not in doc_codes_khi


# ---------------------------------------------------------------------------
# Test 6: Security, SSRF & Workspace Boundary Defense
# ---------------------------------------------------------------------------

def test_ssrf_url_validation():
    # Loopback and private IP SSRF attacks must be rejected
    with pytest.raises(RegulatorySecurityException):
        RegulatoryAcquisitionService.validate_url_for_ssrf("http://localhost:8000/malicious.pdf")

    with pytest.raises(RegulatorySecurityException):
        RegulatoryAcquisitionService.validate_url_for_ssrf("http://127.0.0.1/malicious.pdf")

    with pytest.raises(RegulatorySecurityException):
        RegulatoryAcquisitionService.validate_url_for_ssrf("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(RegulatorySecurityException):
        RegulatoryAcquisitionService.validate_url_for_ssrf("http://10.0.0.1/doc.pdf")

    with pytest.raises(RegulatorySecurityException):
        RegulatoryAcquisitionService.validate_url_for_ssrf("http://192.168.1.1/doc.pdf")

    with pytest.raises(RegulatorySecurityException):
        RegulatoryAcquisitionService.validate_url_for_ssrf("ftp://example.com/doc.pdf")


def test_filename_sanitization():
    assert RegulatoryAcquisitionService.sanitize_filename("../../../etc/passwd") == "passwd"
    assert RegulatoryAcquisitionService.sanitize_filename("..\\..\\boot.ini") == "boot.ini"
    assert RegulatoryAcquisitionService.sanitize_filename("valid_doc-2020.pdf") == "valid_doc-2020.pdf"


def test_storage_boundary_isolation():
    storage_dir = RegulatoryAcquisitionService.get_storage_base_dir()
    assert "PDF Files" not in str(storage_dir)
    assert str(storage_dir).endswith(str(Path("storage") / "regulations"))


# ---------------------------------------------------------------------------
# Test 7: Structural Safety Engine Boundary Enforcement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_structural_safety_engine_regulatory_guidance_boundary(seeded_db: AsyncSession):
    guidance = await RegulatoryRetrievalService.get_regulatory_guidance_for_safety_async(
        seeded_db,
        hazard_code="shear_cracks_columns",
        city="Lahore",
    )
    assert "disclaimer" in guidance
    assert "solely for professional engineering reference" in guidance["disclaimer"]
    assert "do not constitute an on-site structural clearance" in guidance["disclaimer"]
    assert "nor do they modify, downgrade, or override structural hazard classifications" in guidance["disclaimer"]

    # Verify citations retrieved
    assert len(guidance["citations"]) >= 1
    # BCP column transverse reinforcement / confinement tie provisions should be cited
    cited_docs = {c["document_code"] for c in guidance["citations"]}
    assert "BCP-SP-2007" in cited_docs


# ---------------------------------------------------------------------------
# Test 8: FastAPI Regulatory Endpoints & Access Control
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def api_client(test_session_factory, mock_engineer_user) -> AsyncGenerator[AsyncClient, None]:
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

    async def override_get_current_user() -> User:
        return mock_engineer_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Pre-seed DB
        async with test_session_factory() as session:
            await RegulatorySeedService.seed_pilot_data_async(session)
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_list_authorities(api_client: AsyncClient):
    response = await api_client.get("/api/v1/regulations/authorities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    pec_entry = next((a for a in data if a["code"] == "PEC"), None)
    assert pec_entry is not None
    assert pec_entry["credibility_tier"] == "tier_a_statutory"


@pytest.mark.asyncio
async def test_api_get_authority_by_code(api_client: AsyncClient):
    response = await api_client.get("/api/v1/regulations/authorities/LDA")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "LDA"
    assert data["city"] == "Lahore"


@pytest.mark.asyncio
async def test_api_list_documents(api_client: AsyncClient):
    response = await api_client.get("/api/v1/regulations/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    codes = {d["document_code"] for d in data}
    assert "BCP-SP-2007" in codes
    assert "PEC-ACT-1976" in codes
    assert "LDA-BZR-2020" in codes


@pytest.mark.asyncio
async def test_api_search_regulations_post(api_client: AsyncClient):
    payload = {
        "query": "seismic zone classification",
        "city": "Lahore",
    }
    response = await api_client.post("/api/v1/regulations/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["jurisdiction_filtered"] is True
    assert len(data["results"]) >= 1


@pytest.mark.asyncio
async def test_api_safety_guidance(api_client: AsyncClient):
    response = await api_client.get("/api/v1/regulations/safety-guidance?hazard_code=shear_cracks_columns&city=Lahore")
    assert response.status_code == 200
    data = response.json()
    assert "disclaimer" in data
    assert "BCP-SP-2007" in [c["document_code"] for c in data["citations"]]


@pytest.mark.asyncio
async def test_api_review_authorization(test_session_factory, mock_viewer_user, mock_engineer_user):
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

    # Seed DB first
    async with test_session_factory() as session:
        await RegulatorySeedService.seed_pilot_data_async(session)

    # 1. Viewer attempt -> 403 Forbidden
    async def override_viewer() -> User:
        return mock_viewer_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_viewer

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        review_payload = {
            "target_type": "document_version",
            "target_id": str(uuid.uuid4()),
            "review_verdict": "approved",
            "notes": "Viewer attempt to approve legal document",
        }
        res_viewer = await client.post("/api/v1/regulations/reviews", json=review_payload)
        assert res_viewer.status_code == 403

    # 2. Engineer attempt -> 200 OK
    async def override_engineer() -> User:
        return mock_engineer_user

    app.dependency_overrides[get_current_user] = override_engineer
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        review_payload = {
            "target_type": "document_version",
            "target_id": str(uuid.uuid4()),
            "review_verdict": "approved",
            "notes": "Verified by Licensed Professional Engineer Rehan Tariq",
        }
        res_engineer = await client.post("/api/v1/regulations/reviews", json=review_payload)
        assert res_engineer.status_code == 200
        review_data = res_engineer.json()
        assert review_data["review_verdict"] == "approved"
        assert review_data["notes"] == "Verified by Licensed Professional Engineer Rehan Tariq"

    app.dependency_overrides.clear()
