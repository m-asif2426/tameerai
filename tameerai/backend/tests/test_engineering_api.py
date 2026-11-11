"""
TameerAI - Phase 02E Automated Engineering Intelligence Data APIs Test Suite

Comprehensive tests for:
1. Compliance audits draft creation, listing, retrieval, and counter updates
2. Compliance findings creation, spatial pin coordinates, and code assignment (FIND-001)
3. Contract analyses draft creation, listing, retrieval, and standard format defaults
4. Contract risk cards creation, FIDIC references, and code assignment (RISK-001)
5. Material rates global market queries with city/category filtering
6. BOQ analyses draft creation, listing, retrieval, and Decimal variance calculation
7. BOQ schedule items with exact Decimal financial arithmetic and negative rejection
8. Consulting reports creation, public code allocation (RPT-001), and storage path masking
9. Evidentiary preservation safety: DELETE returns HTTP 409 Conflict across all engineering tables
10. Cross-project isolation: anti-enumeration (404) for non-members
11. Cross-project document attachment rejection (400 Bad Request)
12. Role-based access control: Viewer gets 403 Forbidden on write, 200 OK on read
"""

from decimal import Decimal
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_db
from app.core.rate_limit import login_limiter
from app.db.base import Base
from app.main import app
from app.models.cost import MaterialRate
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
async def engineering_client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
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
    login_limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    login_limiter.reset()


async def register_and_login(client: AsyncClient, email: str, full_name: str = "Engineer Lead"):
    reg_payload = {
        "fullName": full_name,
        "email": email,
        "password": "Password12345!",
        "role": "engineer",
        "city": "Lahore",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password12345!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    token = data["accessToken"]
    return token


async def create_test_project(client: AsyncClient, token: str, name: str = "Gulberg Towers"):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": name,
        "location": "Gulberg III, Lahore",
        "city": "Lahore",
        "type": "Commercial G+12",
        "budgetCrore": 25.0,
        "floors": 12,
        "areaSqft": "45,000 sq ft",
        "status": "Under Analysis",
        "risk": "Medium",
    }
    res = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    return data["uuid"], data["id"]


# ---------------------------------------------------------------------------
# Test 1: Compliance Audits and Findings Lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compliance_audits_and_findings(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "lead@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token)

    # 1. Create draft compliance audit
    audit_payload = {
        "governingCode": "Building Code of Pakistan (BCP 2021) / LDA",
        "summary": "Initial structural & egress compliance audit for Gulberg Towers",
        "status": "pending",
    }
    res = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits",
        json=audit_payload,
        headers=headers,
    )
    assert res.status_code == 201
    audit = res.json()
    assert audit["status"] == "pending"
    assert audit["overallScore"] is None
    assert audit["totalChecks"] == 0
    assert audit["violationCount"] == 0
    audit_id = audit["id"]

    # 2. List compliance audits
    list_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/compliance-audits",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 3. Retrieve single audit
    get_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == audit_id

    # 4. Create compliance finding with pin coordinates
    finding_payload = {
        "category": "egress",
        "categoryName": "Egress & Means of Escape",
        "title": "Corridor width deficiency on Floor 3",
        "status": "violation",
        "requiredValue": "2.4 m",
        "currentValue": "1.8 m",
        "variance": "-0.6 m",
        "referenceCode": "BCP-2021",
        "referenceClause": "Clause 4.3.2",
        "locationGrid": "Grid C-4",
        "sheetNumber": "A-103",
        "description": "Corridor width does not meet minimum escape capacity.",
        "remedy": "Widen corridor by realigning interior drywall partition.",
        "pinCoordinates": {
            "x": 42.5,
            "y": 68.0,
            "space": "normalized_percentage",
        },
    }
    res_f = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings",
        json=finding_payload,
        headers=headers,
    )
    assert res_f.status_code == 201
    finding = res_f.json()
    assert finding["id"] == "FIND-001"
    assert finding["category"] == "egress"
    assert finding["status"] == "violation"
    assert finding["pinCoordinates"]["x"] == 42.5
    finding_id = finding["id"]

    # 5. Verify parent audit counts updated
    audit_after = (await client.get(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}",
        headers=headers,
    )).json()
    assert audit_after["totalChecks"] == 1
    assert audit_after["violationCount"] == 1

    # 6. List findings
    list_f_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings?category=egress",
        headers=headers,
    )
    assert list_f_res.status_code == 200
    assert len(list_f_res.json()) == 1

    # 7. Get finding by public code
    get_f_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings/{finding_id}",
        headers=headers,
    )
    assert get_f_res.status_code == 200
    assert get_f_res.json()["title"] == "Corridor width deficiency on Floor 3"

    # 8. Deletion safety returns 409 Conflict
    del_f_res = await client.delete(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings/{finding_id}",
        headers=headers,
    )
    assert del_f_res.status_code == 409

    del_a_res = await client.delete(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}",
        headers=headers,
    )
    assert del_a_res.status_code == 409


# ---------------------------------------------------------------------------
# Test 2: Contract Analyses and Risk Cards Lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_contract_analyses_and_risk_cards(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "contractor@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="DHA Commercial Plaza")

    # 1. Create draft contract analysis
    c_payload = {
        "contractTitle": "Main Construction Contract - DHA Plaza",
        "standardFormat": "FIDIC Red Book 2017 & PEC",
        "summary": "Tender contract clause risk evaluation",
    }
    res = await client.post(
        f"/api/v1/projects/{proj_uuid}/contract-analyses",
        json=c_payload,
        headers=headers,
    )
    assert res.status_code == 201
    analysis = res.json()
    assert analysis["status"] == "unprocessed"
    assert analysis["riskScore"] is None
    assert analysis["totalClausesAudited"] == 0
    analysis_id = analysis["id"]

    # 2. List contract analyses
    list_c = await client.get(
        f"/api/v1/projects/{proj_uuid}/contract-analyses",
        headers=headers,
    )
    assert list_c.status_code == 200
    assert len(list_c.json()) == 1

    # 3. Create contract risk card
    card_payload = {
        "clauseTitle": "Delay Damages and Liquidated Claims",
        "fidicReference": "Clause 8.7",
        "pageNumber": 34,
        "riskLevel": "high",
        "riskLevelLabel": "High Risk - Uncapped Exposure",
        "explanation": "Contract provides no ceiling or cap on daily liquidated delay damages.",
        "recommendation": "Cap delay damages at 10% of total contract value in line with PEC standard conditions.",
        "rawClauseSnippet": "The Contractor shall pay delay damages of PKR 500,000 per day until Taking-Over.",
    }
    res_card = await client.post(
        f"/api/v1/projects/{proj_uuid}/contract-analyses/{analysis_id}/risk-cards",
        json=card_payload,
        headers=headers,
    )
    assert res_card.status_code == 201
    card = res_card.json()
    assert card["id"] == "RISK-001"
    assert card["riskLevel"] == "high"
    card_id = card["id"]

    # 4. Verify flagged clause count updated without inflating total_clauses_audited
    analysis_after = (await client.get(
        f"/api/v1/projects/{proj_uuid}/contract-analyses/{analysis_id}",
        headers=headers,
    )).json()
    assert analysis_after["totalClausesAudited"] == 0
    assert analysis_after["flaggedClausesCount"] == 1

    # 5. List and get risk card
    get_card_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/contract-analyses/{analysis_id}/risk-cards/{card_id}",
        headers=headers,
    )
    assert get_card_res.status_code == 200
    assert get_card_res.json()["clauseTitle"] == "Delay Damages and Liquidated Claims"

    # 6. Deletion safety returns 409 Conflict
    del_card_res = await client.delete(
        f"/api/v1/projects/{proj_uuid}/contract-analyses/{analysis_id}/risk-cards/{card_id}",
        headers=headers,
    )
    assert del_card_res.status_code == 409

    del_c_res = await client.delete(
        f"/api/v1/projects/{proj_uuid}/contract-analyses/{analysis_id}",
        headers=headers,
    )
    assert del_c_res.status_code == 409


# ---------------------------------------------------------------------------
# Test 3: Material Rates and BOQ Analysis with Decimal Arithmetic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_material_rates_and_boq_items(
    engineering_client: AsyncClient,
    test_session_factory,
):
    client = engineering_client
    token = await register_and_login(client, "qs@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Askari Heights")

    # Seed a verified material rate in DB
    from datetime import datetime, timezone
    async with test_session_factory() as session:
        mat_rate = MaterialRate(
            city="Lahore",
            category="steel",
            name="Deformed Steel Bars Grade 60",
            spec="ASTM A615 Grade 60",
            unit="ton",
            rate_pkr=Decimal("260000.00"),
            change_pct=Decimal("2.50"),
            trend="up",
            primary_brands="Mughal, Amreli",
            observed_at=datetime.now(timezone.utc),
            source_name="Pakistan Steel Mills / Market Survey",
            verification_status="verified",
        )
        session.add(mat_rate)
        await session.commit()
        await session.refresh(mat_rate)
        mat_rate_id = str(mat_rate.id)

    # 1. Query material rates endpoint
    mat_res = await client.get("/api/v1/material-rates?city=Lahore", headers=headers)
    assert mat_res.status_code == 200
    rates = mat_res.json()
    assert len(rates) == 1
    assert rates[0]["city"] == "Lahore"
    assert rates[0]["ratePkr"] == 260000.0

    # 2. Create draft BOQ analysis
    boq_payload = {
        "projectBudget": 15000000.0,
        "estimatedCost": 16500000.0,
        "currentCost": 16500000.0,
        "riskIndicator": "Medium",
        "summary": "Initial BOQ schedule review",
    }
    boq_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json=boq_payload,
        headers=headers,
    )
    assert boq_res.status_code == 201
    boq = boq_res.json()
    assert boq["status"] == "unprocessed"
    assert boq["costVariance"] == 1500000.0
    assert boq["variancePercentage"] == 10.0
    boq_id = boq["id"]

    # 3. Create BOQ line item with exact Decimal arithmetic
    # Qty = 50.0 ton, base_rate = 240,000.00, current_price = 260,000.00
    # Expected Budget = 50 * 240,000 = 12,000,000.00
    # Expected Estimated = 50 * 260,000 = 13,000,000.00
    # Expected Overrun = 1,000,000.00
    # Expected Variance = (1,000,000 / 12,000,000) * 100 = 8.33%
    item_payload = {
        "phase": "Superstructure",
        "itemCode": "BOQ-STR-01",
        "description": "Reinforcement Steel Bars Gr-60 in Beams and Columns",
        "unit": "ton",
        "quantity": 50.0,
        "boqBaseRate": 240000.0,
        "currentPrice": 260000.0,
        "materialRateId": mat_rate_id,
    }
    item_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json=item_payload,
        headers=headers,
    )
    assert item_res.status_code == 201
    item = item_res.json()
    assert item["budgetAmount"] == 12000000.0
    assert item["estimatedAmount"] == 13000000.0
    assert item["overrunAmount"] == 1000000.0
    assert item["variancePct"] == 8.33
    assert item["riskLevel"] == "medium"
    item_id = item["id"]

    # Verify parent BOQ analysis aggregates dynamically recalculated from items
    boq_after = (await client.get(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}",
        headers=headers,
    )).json()
    assert boq_after["projectBudget"] == 12000000.0
    assert boq_after["estimatedCost"] == 13000000.0
    assert boq_after["costVariance"] == 1000000.0
    assert boq_after["variancePercentage"] == 8.33
    assert boq_after["riskIndicator"] == "Medium"

    # 4. Negative values rejection
    neg_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={**item_payload, "quantity": -5.0},
        headers=headers,
    )
    assert neg_res.status_code in {422, 400}

    # 5. List items and retrieve single item
    list_items = await client.get(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        headers=headers,
    )
    assert list_items.status_code == 200
    assert len(list_items.json()) == 1

    get_item_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items/{item_id}",
        headers=headers,
    )
    assert get_item_res.status_code == 200
    assert get_item_res.json()["phase"] == "Superstructure"

    # 6. Deletion safety returns 409 Conflict
    del_item_res = await client.delete(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items/{item_id}",
        headers=headers,
    )
    assert del_item_res.status_code == 409

    del_boq_res = await client.delete(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}",
        headers=headers,
    )
    assert del_boq_res.status_code == 409


# ---------------------------------------------------------------------------
# Test 4: Consulting Reports Lifecycle and Code Allocation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_consulting_reports_lifecycle(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "consultant@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Rawalpindi Logistics Hub")

    # 1. Create draft report
    rep_payload = {
        "title": "Comprehensive Structural & Egress Audit Report",
        "category": "compliance",
        "status": "in_review",
        "pageCount": 18,
        "executiveSummary": "Full regulatory assessment against BCP 2021 standards.",
        "keyMetric": "Score: 84% - 3 Critical Non-Compliances",
    }
    rep_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/reports",
        json=rep_payload,
        headers=headers,
    )
    assert rep_res.status_code == 201
    report = rep_res.json()
    assert report["id"] == "RPT-001"
    assert report["category"] == "compliance"
    assert report["categoryLabel"] == "Building Code & Structural Compliance"
    assert "file_path" not in report
    assert "filePath" not in report
    rep_code = report["id"]

    # 2. List reports
    list_rep = await client.get(
        f"/api/v1/projects/{proj_uuid}/reports",
        headers=headers,
    )
    assert list_rep.status_code == 200
    assert len(list_rep.json()) == 1

    # 3. Get report by code
    get_rep = await client.get(
        f"/api/v1/projects/{proj_uuid}/reports/{rep_code}",
        headers=headers,
    )
    assert get_rep.status_code == 200
    assert get_rep.json()["id"] == "RPT-001"

    # 4. Deletion safety returns 409 Conflict
    del_rep = await client.delete(
        f"/api/v1/projects/{proj_uuid}/reports/{rep_code}",
        headers=headers,
    )
    assert del_rep.status_code == 409


# ---------------------------------------------------------------------------
# Test 5: Cross-Project Isolation & Anti-Enumeration (404)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_project_isolation(engineering_client: AsyncClient):
    client = engineering_client
    token_a = await register_and_login(client, "owner_a@tameerai.pk")
    token_b = await register_and_login(client, "owner_b@tameerai.pk")

    proj_a_uuid, _ = await create_test_project(client, token_a, name="Project Alpha")
    proj_b_uuid, _ = await create_test_project(client, token_b, name="Project Beta")

    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to access Project A's audits -> 404 Not Found (anti-enumeration)
    res = await client.get(
        f"/api/v1/projects/{proj_a_uuid}/compliance-audits",
        headers=headers_b,
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Project not found."

    # User B attempts to access Project A's contract analyses -> 404
    res_c = await client.get(
        f"/api/v1/projects/{proj_a_uuid}/contract-analyses",
        headers=headers_b,
    )
    assert res_c.status_code == 404

    # User B attempts to access Project A's BOQ analyses -> 404
    res_boq = await client.get(
        f"/api/v1/projects/{proj_a_uuid}/boq-analyses",
        headers=headers_b,
    )
    assert res_boq.status_code == 404


# ---------------------------------------------------------------------------
# Test 6: Cross-Project Document Attachment Rejection (400)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_project_document_attachment_rejected(
    engineering_client: AsyncClient,
    test_session_factory,
):
    client = engineering_client
    token_a = await register_and_login(client, "proj_owner@tameerai.pk")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    proj_1_uuid, _ = await create_test_project(client, token_a, name="Project 1")
    proj_2_uuid, _ = await create_test_project(client, token_a, name="Project 2")

    # Manually create a Document in Project 2
    from datetime import datetime, timezone
    async with test_session_factory() as session:
        # Fetch user
        u = (await session.execute(select(User).where(User.email == "proj_owner@tameerai.pk"))).scalar_one()
        doc = Document(
            project_id=UUID(proj_2_uuid),
            user_id=u.id,
            code="DOC-001",
            name="Foreign Drawing.pdf",
            file_type="PDF Document",
            document_category="blueprint",
            file_size_bytes=1024,
            file_size_human="1.0 KB",
            storage_path="project-documents/proj2/file.pdf",
            mime_type="application/pdf",
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        foreign_doc_id = str(doc.id)

    # Attempt to attach Project 2's document to Project 1's compliance audit
    res = await client.post(
        f"/api/v1/projects/{proj_1_uuid}/compliance-audits",
        json={"documentId": foreign_doc_id},
        headers=headers_a,
    )
    assert res.status_code == 400
    assert "does not belong to this project" in res.json()["detail"]


# ---------------------------------------------------------------------------
# Test 7: Role-Based Access Control (Viewer 403 on Write, 200 on Read)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rbac_viewer_permissions(
    engineering_client: AsyncClient,
    test_session_factory,
):
    client = engineering_client
    owner_token = await register_and_login(client, "lead_owner@tameerai.pk")
    viewer_token = await register_and_login(client, "auditor_viewer@tameerai.pk", full_name="Viewer Inspector")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    proj_uuid, _ = await create_test_project(client, owner_token, name="High Security Complex")

    # Add viewer to project
    async with test_session_factory() as session:
        viewer_u = (await session.execute(select(User).where(User.email == "auditor_viewer@tameerai.pk"))).scalar_one()
        member = ProjectMember(
            project_id=UUID(proj_uuid),
            user_id=viewer_u.id,
            role="viewer",
        )
        session.add(member)
        await session.commit()

    # 1. Viewer can read/list compliance audits -> 200 OK
    read_res = await client.get(
        f"/api/v1/projects/{proj_uuid}/compliance-audits",
        headers=viewer_headers,
    )
    assert read_res.status_code == 200

    # 2. Viewer attempts to create compliance audit -> 403 Forbidden
    create_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits",
        json={"governingCode": "BCP-2021"},
        headers=viewer_headers,
    )
    assert create_res.status_code == 403
    assert "Viewers cannot create or modify" in create_res.json()["detail"]

    # 3. Viewer attempts to create BOQ analysis -> 403 Forbidden
    boq_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 1000000.0},
        headers=viewer_headers,
    )
    assert boq_res.status_code == 403

    # 4. Viewer attempts to create Report -> 403 Forbidden
    rep_res = await client.post(
        f"/api/v1/projects/{proj_uuid}/reports",
        json={"title": "Unauthorized Report"},
        headers=viewer_headers,
    )
    assert rep_res.status_code == 403


# ---------------------------------------------------------------------------
# Test 8: Nonexistent Resource Queries Return 404
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_nonexistent_resources_return_404(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "tester404@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Empty Workspace")

    fake_id = str(uuid4())

    # Compliance audit
    r1 = await client.get(f"/api/v1/projects/{proj_uuid}/compliance-audits/{fake_id}", headers=headers)
    assert r1.status_code == 404

    # Contract analysis
    r2 = await client.get(f"/api/v1/projects/{proj_uuid}/contract-analyses/{fake_id}", headers=headers)
    assert r2.status_code == 404

    # BOQ analysis
    r3 = await client.get(f"/api/v1/projects/{proj_uuid}/boq-analyses/{fake_id}", headers=headers)
    assert r3.status_code == 404

    # Report
    r4 = await client.get(f"/api/v1/projects/{proj_uuid}/reports/{fake_id}", headers=headers)
    assert r4.status_code == 404

    # Material rate
    r5 = await client.get(f"/api/v1/material-rates/{fake_id}", headers=headers)
    assert r5.status_code == 404


# ---------------------------------------------------------------------------
# Test 9: Reports Cross-Project Linkage Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_report_cross_project_linkage_rejected(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "multiproject@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    proj_a, _ = await create_test_project(client, token, name="Project Alpha")
    proj_b, _ = await create_test_project(client, token, name="Project Beta")

    # Create audit in Project B
    b_audit_res = await client.post(
        f"/api/v1/projects/{proj_b}/compliance-audits",
        json={"governingCode": "BCP-2021"},
        headers=headers,
    )
    assert b_audit_res.status_code == 201
    b_audit_id = b_audit_res.json()["id"]

    # Attempt to create report in Project A linking Project B's audit
    bad_rep = await client.post(
        f"/api/v1/projects/{proj_a}/reports",
        json={
            "title": "Cross Project Leaked Report",
            "category": "compliance",
            "complianceAuditId": b_audit_id,
        },
        headers=headers,
    )
    assert bad_rep.status_code == 400
    assert "does not belong to this project" in bad_rep.json()["detail"]


# ---------------------------------------------------------------------------
# Test 10: Spatial Pin Coordinates Boundary Enforcement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pin_coordinates_boundary_enforcement(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "coords@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Coordinates Project")

    # Create audit
    audit = (await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits",
        json={"governingCode": "BCP-2021"},
        headers=headers,
    )).json()
    audit_id = audit["id"]

    finding_base = {
        "category": "fire",
        "categoryName": "Fire Safety",
        "title": "Fire exit clearance",
        "status": "violation",
        "requiredValue": "2.0 m",
        "currentValue": "1.2 m",
        "referenceCode": "BCP-2021",
        "referenceClause": "9.1",
        "locationGrid": "Grid F-1",
        "description": "Insufficient clearance",
        "remedy": "Clear exit path",
    }

    # x > 100 in normalized space -> 422
    res_high = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings",
        json={**finding_base, "pinCoordinates": {"x": 150.0, "y": 50.0, "space": "normalized_percentage"}},
        headers=headers,
    )
    assert res_high.status_code == 422

    # y < 0 in normalized space -> 422
    res_neg = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings",
        json={**finding_base, "pinCoordinates": {"x": 50.0, "y": -10.0, "space": "normalized_percentage"}},
        headers=headers,
    )
    assert res_neg.status_code == 422

    # Invalid category enum -> 422
    res_cat = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits/{audit_id}/findings",
        json={**finding_base, "category": "nonexistent_domain"},
        headers=headers,
    )
    assert res_cat.status_code == 422


# ---------------------------------------------------------------------------
# Test 11: Privilege & Status Mass-Assignment Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_privilege_status_mass_assignment_rejected(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "massassign@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Status Defense")

    # Reject creating compliance audit with status 'completed'
    bad_audit = await client.post(
        f"/api/v1/projects/{proj_uuid}/compliance-audits",
        json={"status": "completed"},
        headers=headers,
    )
    assert bad_audit.status_code == 422

    # Reject creating contract analysis with status 'completed'
    bad_contract = await client.post(
        f"/api/v1/projects/{proj_uuid}/contract-analyses",
        json={"contractTitle": "Pre-Completed Contract", "status": "completed"},
        headers=headers,
    )
    assert bad_contract.status_code == 422

    # Reject creating BOQ analysis with status 'completed'
    bad_boq = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"status": "completed"},
        headers=headers,
    )
    assert bad_boq.status_code == 422

    # Reject creating report with status 'certified' or 'approved'
    bad_rep1 = await client.post(
        f"/api/v1/projects/{proj_uuid}/reports",
        json={"title": "Falsely Certified", "status": "certified"},
        headers=headers,
    )
    assert bad_rep1.status_code == 422

    bad_rep2 = await client.post(
        f"/api/v1/projects/{proj_uuid}/reports",
        json={"title": "Falsely Approved", "status": "approved"},
        headers=headers,
    )
    assert bad_rep2.status_code == 422


# ---------------------------------------------------------------------------
# Test 12: Decimal Precision Boundaries & Non-Finite Numbers Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_decimal_boundaries_and_non_finite_rejection(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "precision@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Financial Defense")

    boq = (await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 5000000.0},
        headers=headers,
    )).json()
    boq_id = boq["id"]

    base_item = {
        "phase": "Substructure",
        "description": "Excavation in ordinary soil",
        "unit": "cu m",
        "quantity": 100.0,
        "boqBaseRate": 500.0,
        "currentPrice": 550.0,
    }

    # Overflow quantity beyond Numeric(12, 3) (max 999,999,999.999) -> 422
    res_overflow = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={**base_item, "quantity": 10000000000.0},
        headers=headers,
    )
    assert res_overflow.status_code == 422

    # Overflow rate beyond Numeric(12, 2) -> 422
    res_rate_overflow = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={**base_item, "boqBaseRate": 100000000000.0},
        headers=headers,
    )
    assert res_rate_overflow.status_code == 422


# ---------------------------------------------------------------------------
# Test 13: Zero-Baseline Variance Policy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_zero_baseline_variance_policy(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "zerobaseline@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Zero Baseline Testing")

    # 1. Zero budget and zero estimated cost -> 0.00% variance, Low risk
    b1 = (await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 0.0, "estimatedCost": 0.0},
        headers=headers,
    )).json()
    assert b1["costVariance"] == 0.0
    assert b1["variancePercentage"] == 0.0
    assert b1["riskIndicator"] == "Low"

    # 2. Zero budget and positive estimated cost -> None (undefined) variance, High risk alert
    b2 = (await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 0.0, "estimatedCost": 500000.0},
        headers=headers,
    )).json()
    assert b2["costVariance"] == 500000.0
    assert b2["variancePercentage"] is None  # Undefined division preserved as null
    assert b2["riskIndicator"] == "High"  # Unbudgeted expenditure escalation

    # 3. Missing budget (null) -> None variance, default risk
    b3 = (await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"estimatedCost": 250000.0},
        headers=headers,
    )).json()
    assert b3["projectBudget"] is None
    assert b3["costVariance"] is None
    assert b3["variancePercentage"] is None


# ---------------------------------------------------------------------------
# Test 14: Bottom-Up BOQ Baseline Derivation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bottom_up_boq_baseline_derivation(engineering_client: AsyncClient):
    client = engineering_client
    token = await register_and_login(client, "bottomup@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Bottom Up Estimation")

    # Create BOQ without baseline budget
    boq = (await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"summary": "Bottom up schedule aggregation"},
        headers=headers,
    )).json()
    assert boq["projectBudget"] is None
    boq_id = boq["id"]

    # Add item 1: 10 units @ 1000 base, 1100 current -> budget 10,000, est 11,000
    await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={
            "phase": "Substructure",
            "description": "Item 1",
            "unit": "sq m",
            "quantity": 10.0,
            "boqBaseRate": 1000.0,
            "currentPrice": 1100.0,
        },
        headers=headers,
    )

    # Add item 2: 20 units @ 500 base, 600 current -> budget 10,000, est 12,000
    await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={
            "phase": "Superstructure",
            "description": "Item 2",
            "unit": "sq m",
            "quantity": 20.0,
            "boqBaseRate": 500.0,
            "currentPrice": 600.0,
        },
        headers=headers,
    )

    # Total budget = 10,000 + 10,000 = 20,000
    # Total estimated = 11,000 + 12,000 = 23,000
    # Variance = +3,000 (+15.00%) -> High risk
    boq_after = (await client.get(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}",
        headers=headers,
    )).json()
    assert boq_after["projectBudget"] == 20000.0  # Derived bottom-up
    assert boq_after["estimatedCost"] == 23000.0
    assert boq_after["costVariance"] == 3000.0
    assert boq_after["variancePercentage"] == 15.0
    assert boq_after["riskIndicator"] == "High"


# ---------------------------------------------------------------------------
# Test 15: BOQ Percentage Accuracy, Extreme Variance Overflow & Baseline Semantics
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_boq_percentage_accuracy_and_overflow(
    engineering_client: AsyncClient,
    test_session_factory,
):
    """
    Verifies financial percentage accuracy and overflow handling:
    1. Normal variance percentage calculation.
    2. Extreme positive variance (> 9999.99%) sets variance_percentage to None (NULL)
       rather than silently clamping to 9999.99%, while preserving exact rupee cost_variance
       and maintaining 'High' risk indicator.
    3. Negative variance (cost savings) correctly represented.
    4. Zero budget with zero cost yields 0.00% variance.
    5. Zero budget with positive cost yields None percentage and High risk indicator.
    6. Missing budget / estimated cost gracefully handled as None.
    7. BOQ line-item with variance > 9999.99% is rejected with HTTP 422 because
       boq_items.variance_pct is NOT NULL and cannot store unrepresentable percentages.
    8. BOQ line-item with zero budget and positive estimated cost is rejected with HTTP 422.
    9. Authoritative bottom-up aggregation preserves item overruns into parent cost_variance.
    """
    client = engineering_client
    token = await register_and_login(client, "precision_qs@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}
    proj_uuid, _ = await create_test_project(client, token, name="Precision Heights")

    # 1. Normal variance (+10.00%)
    res_normal = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 1000000.0, "estimatedCost": 1100000.0},
        headers=headers,
    )
    assert res_normal.status_code == 201
    d_normal = res_normal.json()
    assert d_normal["costVariance"] == 100000.0
    assert d_normal["variancePercentage"] == 10.0
    assert d_normal["riskIndicator"] == "Medium"

    # 2. Extreme positive variance (> 9999.99%)
    # Budget = 100, Estimated = 1,000,000 -> Variance = 999,900 (+999,900.00%)
    # Must NOT clamp to 9999.99; must store None (NULL) and maintain High risk
    res_extreme = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 100.0, "estimatedCost": 1000000.0},
        headers=headers,
    )
    assert res_extreme.status_code == 201
    d_extreme = res_extreme.json()
    assert d_extreme["costVariance"] == 999900.0
    assert d_extreme["variancePercentage"] is None
    assert d_extreme["riskIndicator"] == "High"

    # 3. Negative variance (cost savings: -20.00%)
    res_savings = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 1000000.0, "estimatedCost": 800000.0},
        headers=headers,
    )
    assert res_savings.status_code == 201
    d_savings = res_savings.json()
    assert d_savings["costVariance"] == -200000.0
    assert d_savings["variancePercentage"] == -20.0
    assert d_savings["riskIndicator"] == "Low"

    # 4. Zero budget with zero cost
    res_zero = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 0.0, "estimatedCost": 0.0},
        headers=headers,
    )
    assert res_zero.status_code == 201
    d_zero = res_zero.json()
    assert d_zero["costVariance"] == 0.0
    assert d_zero["variancePercentage"] == 0.0
    assert d_zero["riskIndicator"] == "Low"

    # 5. Zero budget with positive cost (unbudgeted project)
    res_unbudgeted = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"projectBudget": 0.0, "estimatedCost": 500000.0},
        headers=headers,
    )
    assert res_unbudgeted.status_code == 201
    d_unbudgeted = res_unbudgeted.json()
    assert d_unbudgeted["costVariance"] == 500000.0
    assert d_unbudgeted["variancePercentage"] is None
    assert d_unbudgeted["riskIndicator"] == "High"

    # 6. Missing budget / cost (unestimated draft)
    res_none = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses",
        json={"summary": "Unestimated draft BOQ"},
        headers=headers,
    )
    assert res_none.status_code == 201
    d_none = res_none.json()
    assert d_none["projectBudget"] is None
    assert d_none["estimatedCost"] is None
    assert d_none["costVariance"] is None
    assert d_none["variancePercentage"] is None
    assert d_none["riskIndicator"] == "Low"

    # 7. BOQ Item extreme variance (> 9999.99%) rejection with HTTP 422
    # Base rate = 10, current = 1,000,000 -> 9,999,900%
    boq_id = d_none["id"]
    res_item_extreme = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={
            "phase": "Finishing",
            "description": "Extreme escalation marble",
            "unit": "sq ft",
            "quantity": 1.0,
            "boqBaseRate": 10.0,
            "currentPrice": 1000000.0,
        },
        headers=headers,
    )
    assert res_item_extreme.status_code == 422
    detail_msg = res_item_extreme.json()["detail"]
    assert "exceeds allowable database column capacity" in detail_msg
    assert "schema migration" in detail_msg

    # 8. BOQ Item zero budget with positive cost rejection with HTTP 422
    res_item_zero_budget = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={
            "phase": "Finishing",
            "description": "Zero baseline unbudgeted item",
            "unit": "sq ft",
            "quantity": 10.0,
            "boqBaseRate": 0.0,
            "currentPrice": 500.0,
        },
        headers=headers,
    )
    assert res_item_zero_budget.status_code == 422
    assert "zero baseline budget" in res_item_zero_budget.json()["detail"]

    # 9. Item vs parent mathematical consistency with offsetting items
    res_item_a = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={
            "phase": "Substructure",
            "description": "Item Overrun",
            "unit": "cu m",
            "quantity": 10.0,
            "boqBaseRate": 1000.0,
            "currentPrice": 1200.0,  # budget 10k, est 12k -> overrun +2k (+20%)
        },
        headers=headers,
    )
    assert res_item_a.status_code == 201

    res_item_b = await client.post(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}/items",
        json={
            "phase": "Substructure",
            "description": "Item Underrun",
            "unit": "cu m",
            "quantity": 10.0,
            "boqBaseRate": 2000.0,
            "currentPrice": 1800.0,  # budget 20k, est 18k -> underrun -2k (-10%)
        },
        headers=headers,
    )
    assert res_item_b.status_code == 201

    # Total budget = 10,000 + 20,000 = 30,000
    # Total estimated = 12,000 + 18,000 = 30,000
    # Cost variance = 0.00, variance pct = 0.00%, risk = Low
    boq_recalc = (await client.get(
        f"/api/v1/projects/{proj_uuid}/boq-analyses/{boq_id}",
        headers=headers,
    )).json()
    assert boq_recalc["projectBudget"] == 30000.0
    assert boq_recalc["estimatedCost"] == 30000.0
    assert boq_recalc["costVariance"] == 0.0
    assert boq_recalc["variancePercentage"] == 0.0
    assert boq_recalc["riskIndicator"] == "Low"




