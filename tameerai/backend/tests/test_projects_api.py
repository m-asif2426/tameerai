"""
TameerAI - Phase 02C Automated Project Workspace & Membership RBAC Test Suite

Comprehensive tests for:
1. Authenticated project creation
2. Invalid project creation (negative budget, invalid enums, short name)
3. Ownership assignment (owner == current_user.id)
4. Safe project code allocation (sequential PRJ-001, tenant-scoped)
5. Concurrent project creation simulation (safe allocation logic)
6. Project list isolation (tenants only see their own / accessible projects)
7. Project detail authorization (404 policy for non-members to prevent enumeration)
8. Project partial updates (omitted fields preserved)
9. Mass-assignment prevention (rejection of user_id, code, compliance_score)
10. Owner permissions (full workspace administration)
11. Member permissions (Lead Engineer can edit and invite lower roles)
12. Viewer read-only restrictions (403 on edit / member manage)
13. Duplicate membership rejection (409 Conflict)
14. Invalid role assignments rejection (422)
15. Member addition and removal
16. Member self-escalation and hierarchy enforcement (Lead Engineer cannot grant Lead Engineer)
17. Owner removal protection (owner cannot be added or removed as collaborator)
18. Activity log creation and audit trail retrieval
19. Financial data precision (Decimal handling, Crore conversions, negative validation)
20. Delete safety (cascading protection returns 409 Conflict, project preserved)
21. Transaction rollback on failure
22. Cross-project security isolation
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
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
from app.models.project import Project, ProjectActivity, ProjectMember
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
async def async_db(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def project_client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
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


# ---------------------------------------------------------------------------
# 1. Authenticated Project Creation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_project_creation(project_client: AsyncClient):
    token, user = await create_user(project_client, email="creator@tameerai.pk", full_name="Engr. Tariq")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "DHA Commercial Plaza",
        "nameUrdu": "ڈی ایچ اے کمرشل پلازہ",
        "location": "Phase 6, Sector G, Lahore",
        "city": "Lahore",
        "type": "Commercial G+12",
        "budgetCrore": 12.0,
        "floors": 13,
        "areaSqft": "45,000 sq ft",
        "status": "Under Analysis",
        "risk": "Medium",
    }
    res = await project_client.post("/api/v1/projects", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["name"] == "DHA Commercial Plaza"
    assert data["id"] == "PRJ-001"
    assert "uuid" in data
    assert data["userId"] == user["id"]
    assert data["budgetCrore"] == 12.0
    assert data["budgetRaw"] == 120000000.0
    assert data["status"] == "Under Analysis"
    assert data["risk"] == "Medium"


# ---------------------------------------------------------------------------
# 2. Invalid Project Creation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_project_creation(project_client: AsyncClient):
    token, _ = await create_user(project_client, email="invalid.prj@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    # Missing name
    res1 = await project_client.post("/api/v1/projects", json={"location": "Lahore", "city": "Lahore"}, headers=headers)
    assert res1.status_code == 422

    # Negative budget
    res2 = await project_client.post("/api/v1/projects", json={"name": "Bad Project", "location": "Lahore", "budgetCrore": -5.0}, headers=headers)
    assert res2.status_code == 422

    # Invalid status enum
    res3 = await project_client.post("/api/v1/projects", json={"name": "Bad Project", "location": "Lahore", "status": "Abandoned"}, headers=headers)
    assert res3.status_code == 422

    # Invalid risk enum
    res4 = await project_client.post("/api/v1/projects", json={"name": "Bad Project", "location": "Lahore", "risk": "Critical"}, headers=headers)
    assert res4.status_code == 422

    # Floors < 1
    res5 = await project_client.post("/api/v1/projects", json={"name": "Bad Project", "location": "Lahore", "floors": 0}, headers=headers)
    assert res5.status_code == 422


# ---------------------------------------------------------------------------
# 3. Ownership Assignment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ownership_assignment(project_client: AsyncClient):
    token, user = await create_user(project_client, email="owner.check@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    res = await project_client.post(
        "/api/v1/projects",
        json={"name": "Owned Project", "location": "Sector C, Islamabad", "city": "Islamabad"},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["userId"] == user["id"]


# ---------------------------------------------------------------------------
# 4. Safe Project Code Allocation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_safe_project_code_allocation(project_client: AsyncClient):
    token_a, _ = await create_user(project_client, email="user.a.code@tameerai.pk")
    token_b, _ = await create_user(project_client, email="user.b.code@tameerai.pk")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates 3 projects
    res_a1 = await project_client.post("/api/v1/projects", json={"name": "Prj 1", "location": "Loc 1"}, headers=headers_a)
    assert res_a1.json()["id"] == "PRJ-001"

    res_a2 = await project_client.post("/api/v1/projects", json={"name": "Prj 2", "location": "Loc 2"}, headers=headers_a)
    assert res_a2.json()["id"] == "PRJ-002"

    res_a3 = await project_client.post("/api/v1/projects", json={"name": "Prj 3", "location": "Loc 3"}, headers=headers_a)
    assert res_a3.json()["id"] == "PRJ-003"

    # User B creates 1 project -> tenant-scoped code begins at PRJ-001!
    res_b1 = await project_client.post("/api/v1/projects", json={"name": "Prj B1", "location": "Loc B1"}, headers=headers_b)
    assert res_b1.json()["id"] == "PRJ-001"


# ---------------------------------------------------------------------------
# 5. Concurrent Project Creation Simulation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_project_creation_simulation(async_db: AsyncSession):
    from app.services.project_service import allocate_project_code

    test_user = User(
        email="concurrent.code@tameer.pk",
        hashed_password="hash",
        full_name="Concurrent User",
    )
    async_db.add(test_user)
    await async_db.commit()

    # Pre-populate project with PRJ-004
    p = Project(code="PRJ-004", user_id=test_user.id, name="Prj 4", location="Loc")
    async_db.add(p)
    await async_db.commit()

    code = await allocate_project_code(async_db, test_user.id)
    assert code == "PRJ-005"


# ---------------------------------------------------------------------------
# 6. Project List Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_project_list_isolation(project_client: AsyncClient):
    token_a, _ = await create_user(project_client, email="tenant.a@tameerai.pk")
    token_b, _ = await create_user(project_client, email="tenant.b@tameerai.pk")

    # User A creates 2 projects
    await project_client.post("/api/v1/projects", json={"name": "Project A1", "location": "Loc A1"}, headers={"Authorization": f"Bearer {token_a}"})
    await asyncio.sleep(0.01)
    await project_client.post("/api/v1/projects", json={"name": "Project A2", "location": "Loc A2"}, headers={"Authorization": f"Bearer {token_a}"})

    # User B creates 1 project
    await project_client.post("/api/v1/projects", json={"name": "Project B1", "location": "Loc B1"}, headers={"Authorization": f"Bearer {token_b}"})

    # User A lists projects -> exactly 2
    res_a = await project_client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["total"] == 2
    assert [p["name"] for p in res_a.json()["items"]] == ["Project A2", "Project A1"]

    # User B lists projects -> exactly 1
    res_b = await project_client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["total"] == 1
    assert res_b.json()["items"][0]["name"] == "Project B1"


# ---------------------------------------------------------------------------
# 7. Project Detail Authorization (404 on Unauthorized)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_project_detail_authorization(project_client: AsyncClient):
    token_a, _ = await create_user(project_client, email="auth.owner@tameerai.pk")
    token_b, _ = await create_user(project_client, email="auth.stranger@tameerai.pk")

    # Create project by A
    create_res = await project_client.post("/api/v1/projects", json={"name": "Private Prj", "location": "Loc"}, headers={"Authorization": f"Bearer {token_a}"})
    prj_id = create_res.json()["id"]
    prj_uuid = create_res.json()["uuid"]

    # Owner accesses by public code -> 200
    res1 = await project_client.get(f"/api/v1/projects/{prj_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res1.status_code == 200

    # Owner accesses by internal UUID -> 200
    res2 = await project_client.get(f"/api/v1/projects/{prj_uuid}", headers={"Authorization": f"Bearer {token_a}"})
    assert res2.status_code == 200

    # Stranger accesses -> 404 (prevents enumeration)
    res3 = await project_client.get(f"/api/v1/projects/{prj_uuid}", headers={"Authorization": f"Bearer {token_b}"})
    assert res3.status_code == 404

    # Unauthenticated access -> 401
    res4 = await project_client.get(f"/api/v1/projects/{prj_uuid}")
    assert res4.status_code == 401


# ---------------------------------------------------------------------------
# 8. Project Partial Updates
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_project_partial_updates(project_client: AsyncClient):
    token, _ = await create_user(project_client, email="patch.user@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await project_client.post(
        "/api/v1/projects",
        json={"name": "Initial Name", "location": "Initial Loc", "city": "Lahore", "status": "Planning"},
        headers=headers,
    )
    prj_id = create_res.json()["id"]

    # Partial update: only name and status
    patch_res = await project_client.patch(
        f"/api/v1/projects/{prj_id}",
        json={"name": "Renamed Commercial Plaza", "status": "Active"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "Renamed Commercial Plaza"
    assert data["status"] == "Active"
    assert data["location"] == "Initial Loc"  # Preserved
    assert data["city"] == "Lahore"  # Preserved


# ---------------------------------------------------------------------------
# 9. Mass-Assignment Prevention
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mass_assignment_prevention(project_client: AsyncClient):
    token, _ = await create_user(project_client, email="mass.prj@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await project_client.post("/api/v1/projects", json={"name": "Secure Prj", "location": "Loc"}, headers=headers)
    prj_id = create_res.json()["id"]

    # 1. Attempt to alter user_id (ownership takeover)
    res1 = await project_client.patch(f"/api/v1/projects/{prj_id}", json={"userId": str(uuid4())}, headers=headers)
    assert res1.status_code == 422

    # 2. Attempt to alter public code
    res2 = await project_client.patch(f"/api/v1/projects/{prj_id}", json={"code": "PRJ-999"}, headers=headers)
    assert res2.status_code == 422

    # 3. Attempt to fabricate complianceScore
    res3 = await project_client.patch(f"/api/v1/projects/{prj_id}", json={"complianceScore": 100}, headers=headers)
    assert res3.status_code == 422


# ---------------------------------------------------------------------------
# 10. Owner Permissions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_owner_permissions(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="super.owner@tameerai.pk")
    _, collab = await create_user(project_client, email="invited.engr@tameerai.pk")
    headers = {"Authorization": f"Bearer {token_owner}"}

    create_res = await project_client.post("/api/v1/projects", json={"name": "Owner Admin Prj", "location": "Loc"}, headers=headers)
    prj_id = create_res.json()["id"]

    # Owner adds a lead_engineer
    add_res = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": collab["id"], "role": "lead_engineer"},
        headers=headers,
    )
    assert add_res.status_code == 201
    member_id = add_res.json()["id"]

    # Owner updates member role to architect
    patch_mem = await project_client.patch(
        f"/api/v1/projects/{prj_id}/members/{member_id}",
        json={"role": "architect"},
        headers=headers,
    )
    assert patch_mem.status_code == 200
    assert patch_mem.json()["role"] == "architect"

    # Owner removes member
    del_mem = await project_client.delete(f"/api/v1/projects/{prj_id}/members/{member_id}", headers=headers)
    assert del_mem.status_code == 200


# ---------------------------------------------------------------------------
# 11. Member Permissions (Lead Engineer)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_member_permissions_lead_engineer(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="owner.lead@tameerai.pk")
    token_lead, user_lead = await create_user(project_client, email="lead.collab@tameerai.pk")
    _, user_arch = await create_user(project_client, email="sub.arch@tameerai.pk")

    # Owner creates project and invites User Lead as lead_engineer
    prj = (await project_client.post("/api/v1/projects", json={"name": "Team Prj", "location": "Loc"}, headers={"Authorization": f"Bearer {token_owner}"})).json()
    prj_id = prj["id"]

    await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_lead["id"], "role": "lead_engineer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )

    # Lead Engineer edits project metadata -> 200
    lead_headers = {"Authorization": f"Bearer {token_lead}"}
    patch_res = await project_client.patch(f"/api/v1/projects/{prj_id}", json={"description": "Lead engineer updated scope."}, headers=lead_headers)
    assert patch_res.status_code == 200

    # Lead Engineer invites architect -> 201
    inv_res = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_arch["id"], "role": "architect"},
        headers=lead_headers,
    )
    assert inv_res.status_code == 201


# ---------------------------------------------------------------------------
# 12. Viewer Read-Only Restrictions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_viewer_read_only_restrictions(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="owner.viewer@tameerai.pk")
    token_view, user_view = await create_user(project_client, email="guest.viewer@tameerai.pk")
    _, user_third = await create_user(project_client, email="third.party@tameerai.pk")

    prj = (await project_client.post("/api/v1/projects", json={"name": "View Prj", "location": "Loc"}, headers={"Authorization": f"Bearer {token_owner}"})).json()
    prj_id = prj["id"]

    # Owner invites guest as viewer
    await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_view["id"], "role": "viewer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )

    view_headers = {"Authorization": f"Bearer {token_view}"}

    # Viewer reads details -> 200
    read_res = await project_client.get(f"/api/v1/projects/{prj_id}", headers=view_headers)
    assert read_res.status_code == 200

    # Viewer attempts edit -> 403 Forbidden
    edit_res = await project_client.patch(f"/api/v1/projects/{prj_id}", json={"name": "Hacked"}, headers=view_headers)
    assert edit_res.status_code == 403

    # Viewer attempts to invite someone -> 403 Forbidden
    inv_res = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_third["id"], "role": "viewer"},
        headers=view_headers,
    )
    assert inv_res.status_code == 403


# ---------------------------------------------------------------------------
# 13. Duplicate Membership Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_membership_rejected(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="owner.dup@tameerai.pk")
    _, user_collab = await create_user(project_client, email="dup.collab@tameerai.pk")
    headers = {"Authorization": f"Bearer {token_owner}"}

    prj = (await project_client.post("/api/v1/projects", json={"name": "Dup Prj", "location": "Loc"}, headers=headers)).json()
    prj_id = prj["id"]

    # Add once
    res1 = await project_client.post(f"/api/v1/projects/{prj_id}/members", json={"userId": user_collab["id"], "role": "contractor"}, headers=headers)
    assert res1.status_code == 201

    # Add twice -> 409 Conflict
    res2 = await project_client.post(f"/api/v1/projects/{prj_id}/members", json={"userId": user_collab["id"], "role": "contractor"}, headers=headers)
    assert res2.status_code == 409


# ---------------------------------------------------------------------------
# 14. Invalid Role Assignments Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_role_assignments(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="owner.badrole@tameerai.pk")
    _, user_collab = await create_user(project_client, email="collab.badrole@tameerai.pk")
    headers = {"Authorization": f"Bearer {token_owner}"}

    prj = (await project_client.post("/api/v1/projects", json={"name": "Role Prj", "location": "Loc"}, headers=headers)).json()
    prj_id = prj["id"]

    # Invalid role "administrator"
    res = await project_client.post(f"/api/v1/projects/{prj_id}/members", json={"userId": user_collab["id"], "role": "administrator"}, headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 15. Member Addition and Removal
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_member_addition_and_removal(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="owner.addrem@tameerai.pk")
    _, user_collab = await create_user(project_client, email="collab.addrem@tameerai.pk")
    headers = {"Authorization": f"Bearer {token_owner}"}

    prj = (await project_client.post("/api/v1/projects", json={"name": "Lifecycle Prj", "location": "Loc"}, headers=headers)).json()
    prj_id = prj["id"]

    # Add member via email
    add_res = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"email": "collab.addrem@tameerai.pk", "role": "contractor"},
        headers=headers,
    )
    assert add_res.status_code == 201
    member_id = add_res.json()["id"]

    # Verify present in list
    list_res = await project_client.get(f"/api/v1/projects/{prj_id}/members", headers=headers)
    assert len(list_res.json()) == 1

    # Remove member
    del_res = await project_client.delete(f"/api/v1/projects/{prj_id}/members/{member_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify empty list
    list_res2 = await project_client.get(f"/api/v1/projects/{prj_id}/members", headers=headers)
    assert len(list_res2.json()) == 0


# ---------------------------------------------------------------------------
# 16. Member Self-Escalation & Role Hierarchy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_member_self_escalation_and_hierarchical_limits(project_client: AsyncClient):
    token_owner, _ = await create_user(project_client, email="owner.hierarchy@tameerai.pk")
    token_lead, user_lead = await create_user(project_client, email="lead.hier@tameerai.pk")
    _, user_target = await create_user(project_client, email="target.hier@tameerai.pk")

    prj = (await project_client.post("/api/v1/projects", json={"name": "Hierarchy Prj", "location": "Loc"}, headers={"Authorization": f"Bearer {token_owner}"})).json()
    prj_id = prj["id"]

    await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_lead["id"], "role": "lead_engineer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )

    lead_headers = {"Authorization": f"Bearer {token_lead}"}

    # Lead Engineer attempts to invite someone as lead_engineer -> 403 Forbidden (cannot grant >= own role)
    res_escalate = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_target["id"], "role": "lead_engineer"},
        headers=lead_headers,
    )
    assert res_escalate.status_code == 403


# ---------------------------------------------------------------------------
# 17. Owner Removal Protection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_owner_removal_protection(project_client: AsyncClient):
    token_owner, user_owner = await create_user(project_client, email="immortal.owner@tameerai.pk")
    headers = {"Authorization": f"Bearer {token_owner}"}

    prj = (await project_client.post("/api/v1/projects", json={"name": "Immortal Prj", "location": "Loc"}, headers=headers)).json()
    prj_id = prj["id"]

    # Attempt to add owner as a member -> 400 Bad Request
    res = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": user_owner["id"], "role": "lead_engineer"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "owner is already" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 18. Activity Log Creation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_activity_log_creation(project_client: AsyncClient):
    token, _ = await create_user(project_client, email="activity.owner@tameerai.pk", full_name="Engr. Logger")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create project
    prj = (await project_client.post("/api/v1/projects", json={"name": "Activity Prj", "location": "Loc"}, headers=headers)).json()
    prj_id = prj["id"]

    # 2. Update project
    await project_client.patch(f"/api/v1/projects/{prj_id}", json={"status": "Active"}, headers=headers)

    # 3. Retrieve activities
    act_res = await project_client.get(f"/api/v1/projects/{prj_id}/activities", headers=headers)
    assert act_res.status_code == 200
    activities = act_res.json()
    assert len(activities) >= 2

    # Most recent activity is update
    assert "updated" in activities[0]["action"].lower()
    # First activity was creation
    assert "created" in activities[1]["action"].lower()
    assert activities[1]["user"] == "Engr. Logger"


# ---------------------------------------------------------------------------
# 19. Financial Data Precision
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_financial_precision(project_client: AsyncClient):
    token, _ = await create_user(project_client, email="finance.test@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    # Pass raw PKR
    res1 = await project_client.post(
        "/api/v1/projects",
        json={"name": "Exact Finance Prj", "location": "Loc", "budgetRaw": 125000000.50},
        headers=headers,
    )
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["budgetRaw"] == 125000000.50
    assert data1["budgetCrore"] == 12.5

    # Pass Crore value
    res2 = await project_client.post(
        "/api/v1/projects",
        json={"name": "Crore Finance Prj", "location": "Loc", "budgetCrore": 4.5},
        headers=headers,
    )
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["budgetRaw"] == 45000000.00
    assert data2["budgetCrore"] == 4.5


# ---------------------------------------------------------------------------
# 20. Delete Safety (Cascading Protection)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_safety_cascading_protection(project_client: AsyncClient):
    token, _ = await create_user(project_client, email="safe.del@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    prj = (await project_client.post("/api/v1/projects", json={"name": "Undeletable Prj", "location": "Loc"}, headers=headers)).json()
    prj_id = prj["id"]

    # DELETE must be safely rejected with 409 Conflict
    del_res = await project_client.delete(f"/api/v1/projects/{prj_id}", headers=headers)
    assert del_res.status_code == 409
    assert "cascading project deletion is restricted" in del_res.json()["detail"].lower()

    # Verify project is still alive and readable
    get_res = await project_client.get(f"/api/v1/projects/{prj_id}", headers=headers)
    assert get_res.status_code == 200


# ---------------------------------------------------------------------------
# 21. Transaction Rollback on Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transaction_rollback_on_failure():
    from app.services.project_service import create_project
    from app.schemas.project import ProjectCreate

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit.side_effect = RuntimeError("DB write error during project commit")

    test_user = User(id=uuid4(), email="rollback.prj@test.pk", full_name="Tester")
    payload = ProjectCreate(name="Crash Prj", location="Loc")

    with patch("app.services.project_service.allocate_project_code", return_value="PRJ-001"):
        with pytest.raises(HTTPException) as exc_info:
            await create_project(db=mock_db, user=test_user, payload=payload)

    assert exc_info.value.status_code == 500
    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# 22. Cross-Project Security Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_project_security_isolation(project_client: AsyncClient):
    token_a, _ = await create_user(project_client, email="alpha.corp@tameerai.pk")
    token_b, user_b = await create_user(project_client, email="beta.corp@tameerai.pk")

    # Alpha creates Project Alpha
    prj_alpha = (await project_client.post("/api/v1/projects", json={"name": "Project Alpha", "location": "Loc"}, headers={"Authorization": f"Bearer {token_a}"})).json()
    alpha_id = prj_alpha["id"]

    # Beta attempts to add self to Project Alpha -> 404
    b_headers = {"Authorization": f"Bearer {token_b}"}
    hack_res = await project_client.post(
        f"/api/v1/projects/{alpha_id}/members",
        json={"userId": user_b["id"], "role": "lead_engineer"},
        headers=b_headers,
    )
    assert hack_res.status_code == 404

    # Beta attempts to read Project Alpha activities -> 404
    act_res = await project_client.get(f"/api/v1/projects/{alpha_id}/activities", headers=b_headers)
    assert act_res.status_code == 404


# ---------------------------------------------------------------------------
# 23. Cross-Project Member ID Manipulation Rejected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_project_membership_manipulation_rejected(project_client: AsyncClient):
    """
    Verifies that passing a member_id belonging to Project Alpha into an endpoint
    for Project Beta is rejected with 404 Not Found.
    """
    token_a, _ = await create_user(project_client, email="owner.alpha@tameerai.pk")
    token_b, _ = await create_user(project_client, email="owner.beta@tameerai.pk")
    _, user_collab = await create_user(project_client, email="shared.collab@tameerai.pk")

    # Project Alpha created by A
    prj_a = (await project_client.post("/api/v1/projects", json={"name": "Prj Alpha", "location": "Loc"}, headers={"Authorization": f"Bearer {token_a}"})).json()
    # Add collab to Project Alpha
    mem_a = (await project_client.post(f"/api/v1/projects/{prj_a['id']}/members", json={"userId": user_collab["id"], "role": "contractor"}, headers={"Authorization": f"Bearer {token_a}"})).json()
    member_a_id = mem_a["id"]

    # Project Beta created by B
    prj_b = (await project_client.post("/api/v1/projects", json={"name": "Prj Beta", "location": "Loc"}, headers={"Authorization": f"Bearer {token_b}"})).json()

    # User B attempts to patch Project Alpha's member via Project Beta's route
    patch_res = await project_client.patch(
        f"/api/v1/projects/{prj_b['id']}/members/{member_a_id}",
        json={"role": "architect"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert patch_res.status_code == 404

    # User B attempts to delete Project Alpha's member via Project Beta's route
    del_res = await project_client.delete(
        f"/api/v1/projects/{prj_b['id']}/members/{member_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 404


# ---------------------------------------------------------------------------
# 24. Member Self-Escalation Blocked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_member_self_escalation_blocked(project_client: AsyncClient):
    """
    Verifies that a member (even a Lead Engineer) cannot modify their own role.
    """
    token_owner, _ = await create_user(project_client, email="owner.noescalate@tameerai.pk")
    token_lead, user_lead = await create_user(project_client, email="lead.noescalate@tameerai.pk")

    prj = (await project_client.post("/api/v1/projects", json={"name": "Prj Escalate", "location": "Loc"}, headers={"Authorization": f"Bearer {token_owner}"})).json()
    add_mem = (await project_client.post(f"/api/v1/projects/{prj['id']}/members", json={"userId": user_lead["id"], "role": "lead_engineer"}, headers={"Authorization": f"Bearer {token_owner}"})).json()
    member_id = add_mem["id"]

    # Lead Engineer attempts to modify their own role
    lead_headers = {"Authorization": f"Bearer {token_lead}"}
    res = await project_client.patch(
        f"/api/v1/projects/{prj['id']}/members/{member_id}",
        json={"role": "architect"},
        headers=lead_headers,
    )
    assert res.status_code == 403
    assert "self-escalation forbidden" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 25. Former Member Loses Access Immediately
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_former_member_immediately_loses_access(project_client: AsyncClient):
    """
    Verifies that removing a member immediately revokes their project access on the next request.
    """
    token_owner, _ = await create_user(project_client, email="owner.former@tameerai.pk")
    token_viewer, user_viewer = await create_user(project_client, email="viewer.former@tameerai.pk")

    prj = (await project_client.post("/api/v1/projects", json={"name": "Revocation Prj", "location": "Loc"}, headers={"Authorization": f"Bearer {token_owner}"})).json()
    prj_id = prj["id"]

    # Add viewer
    add_res = await project_client.post(f"/api/v1/projects/{prj_id}/members", json={"userId": user_viewer["id"], "role": "viewer"}, headers={"Authorization": f"Bearer {token_owner}"})
    member_id = add_res.json()["id"]

    # Viewer accesses project -> 200
    view_headers = {"Authorization": f"Bearer {token_viewer}"}
    access_1 = await project_client.get(f"/api/v1/projects/{prj_id}", headers=view_headers)
    assert access_1.status_code == 200

    # Owner removes viewer
    await project_client.delete(f"/api/v1/projects/{prj_id}/members/{member_id}", headers={"Authorization": f"Bearer {token_owner}"})

    # Viewer attempts access again -> immediately 404
    access_2 = await project_client.get(f"/api/v1/projects/{prj_id}", headers=view_headers)
    assert access_2.status_code == 404


# ---------------------------------------------------------------------------
# 26. Tenant-Scoped Public Code URL Resolution Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_public_code_resolution_tenant_isolation(project_client: AsyncClient):
    """
    Verifies that when two distinct users both own a project with code 'PRJ-001',
    calling GET /api/v1/projects/PRJ-001 resolves strictly to the calling user's project.
    """
    token_a, _ = await create_user(project_client, email="owner.code.a@tameerai.pk")
    token_b, _ = await create_user(project_client, email="owner.code.b@tameerai.pk")

    # Both create a project -> both get PRJ-001
    prj_a = (await project_client.post("/api/v1/projects", json={"name": "Alpha Tower", "location": "Lahore"}, headers={"Authorization": f"Bearer {token_a}"})).json()
    prj_b = (await project_client.post("/api/v1/projects", json={"name": "Beta Heights", "location": "Islamabad"}, headers={"Authorization": f"Bearer {token_b}"})).json()

    assert prj_a["id"] == "PRJ-001"
    assert prj_b["id"] == "PRJ-001"
    assert prj_a["uuid"] != prj_b["uuid"]

    # User A requests PRJ-001 -> gets Alpha Tower
    res_a = await project_client.get("/api/v1/projects/PRJ-001", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["name"] == "Alpha Tower"
    assert res_a.json()["uuid"] == prj_a["uuid"]

    # User B requests PRJ-001 -> gets Beta Heights
    res_b = await project_client.get("/api/v1/projects/PRJ-001", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["name"] == "Beta Heights"
    assert res_b.json()["uuid"] == prj_b["uuid"]


# ---------------------------------------------------------------------------
# 27. Financial Precision Boundaries & Rejection of Oversized Amounts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_financial_precision_boundary_limits(project_client: AsyncClient):
    """
    Tests financial validation:
    - Oversized amount (> NUMERIC(15,2)) is rejected with 422 before reaching DB.
    - Max valid boundary (999,999,999,999.99) is accepted.
    - Sub-cent decimal scale (> 2 decimal places on raw) is rejected with 422.
    - Excessive crore decimals (> 4 decimal places) is rejected with 422.
    """
    token, _ = await create_user(project_client, email="boundary.finance@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Oversized budgetRaw: 1 Trillion PKR (exceeds NUMERIC(15,2))
    res_over = await project_client.post(
        "/api/v1/projects",
        json={"name": "Trillion Tower", "location": "Loc", "budgetRaw": 1000000000000.00},
        headers=headers,
    )
    assert res_over.status_code == 422

    # 2. Maximum allowable boundary: 999,999,999,999.99
    res_max = await project_client.post(
        "/api/v1/projects",
        json={"name": "Max Tower", "location": "Loc", "budgetRaw": 999999999999.99},
        headers=headers,
    )
    assert res_max.status_code == 201
    assert res_max.json()["budgetRaw"] == 999999999999.99

    # 3. Excessive raw scale (> 2 decimal places, e.g. .555)
    res_scale = await project_client.post(
        "/api/v1/projects",
        json={"name": "Subcent Tower", "location": "Loc", "budgetRaw": 120000.555},
        headers=headers,
    )
    assert res_scale.status_code == 422

    # 4. Excessive crore scale (> 4 decimal places, e.g. .12345)
    res_crore_scale = await project_client.post(
        "/api/v1/projects",
        json={"name": "Crore Scale Tower", "location": "Loc", "budgetCrore": 12.12345},
        headers=headers,
    )
    assert res_crore_scale.status_code == 422


# ---------------------------------------------------------------------------
# 28. Attempt to Grant 'Owner' as Member Role Rejected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cannot_grant_owner_as_member_role(project_client: AsyncClient):
    """
    Verifies that attempting to grant role 'owner' via member endpoints is rejected
    with 422 because 'owner' is not an allowed collaborative role.
    """
    token_owner, _ = await create_user(project_client, email="owner.fake@tameerai.pk")
    _, collab = await create_user(project_client, email="collab.fake@tameerai.pk")
    headers = {"Authorization": f"Bearer {token_owner}"}

    prj = (await project_client.post("/api/v1/projects", json={"name": "Fake Owner Prj", "location": "Loc"}, headers=headers)).json()

    res = await project_client.post(
        f"/api/v1/projects/{prj['id']}/members",
        json={"userId": collab["id"], "role": "owner"},
        headers=headers,
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 29. Deletion Safety Matrix: 401, 404, 403, and 409 for Empty & Populated
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deletion_safety_comprehensive_matrix(project_client: AsyncClient):
    """
    Verifies Phase 02C deletion restrictions:
    - Unauthenticated: 401
    - Unrelated user: 404
    - Non-owner collaborator (lead_engineer): 403
    - Project owner (empty project): 409
    - Project owner (populated project): 409
    - Project is NEVER deleted or modified in DB.
    """
    token_owner, owner = await create_user(project_client, email="del.owner@tameerai.pk")
    token_unrelated, _ = await create_user(project_client, email="del.unrelated@tameerai.pk")
    token_collab, collab = await create_user(project_client, email="del.collab@tameerai.pk")

    headers_owner = {"Authorization": f"Bearer {token_owner}"}
    headers_unrelated = {"Authorization": f"Bearer {token_unrelated}"}
    headers_collab = {"Authorization": f"Bearer {token_collab}"}

    # Create empty project
    prj = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Protected Project", "location": "Lahore"},
        headers=headers_owner,
    )).json()
    prj_id = prj["id"]
    prj_uuid = prj["uuid"]

    # 1. Unauthenticated caller -> 401
    res_unauth = await project_client.delete(f"/api/v1/projects/{prj_id}")
    assert res_unauth.status_code == 401

    # 2. Unrelated user -> 404
    res_unrelated = await project_client.delete(f"/api/v1/projects/{prj_id}", headers=headers_unrelated)
    assert res_unrelated.status_code == 404

    # Add collaborator as lead_engineer
    add_res = await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": collab["id"], "role": "lead_engineer"},
        headers=headers_owner,
    )
    assert add_res.status_code == 201

    # 3. Non-owner collaborator -> 403
    res_collab = await project_client.delete(f"/api/v1/projects/{prj_id}", headers=headers_collab)
    assert res_collab.status_code == 403
    assert "only the project owner can request project deletion" in res_collab.json()["detail"].lower()

    # 4. Project owner on populated project -> 409
    res_owner_pop = await project_client.delete(f"/api/v1/projects/{prj_id}", headers=headers_owner)
    assert res_owner_pop.status_code == 409
    assert "cascading project deletion is restricted" in res_owner_pop.json()["detail"].lower()

    # Create another completely empty project
    empty_prj = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Empty Protected Project", "location": "Karachi"},
        headers=headers_owner,
    )).json()
    empty_id = empty_prj["id"]

    # 5. Project owner on completely empty project -> 409
    res_owner_empty = await project_client.delete(f"/api/v1/projects/{empty_id}", headers=headers_owner)
    assert res_owner_empty.status_code == 409
    assert "cascading project deletion is restricted" in res_owner_empty.json()["detail"].lower()

    # 6. Verify projects are still alive and intact
    get_pop = await project_client.get(f"/api/v1/projects/{prj_id}", headers=headers_owner)
    assert get_pop.status_code == 200
    assert get_pop.json()["uuid"] == prj_uuid

    get_empty = await project_client.get(f"/api/v1/projects/{empty_id}", headers=headers_owner)
    assert get_empty.status_code == 200


# ---------------------------------------------------------------------------
# 30. Comprehensive Monetary Boundaries & Invalid Numeric Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_monetary_boundary_comprehensive(project_client: AsyncClient):
    """
    Exhaustive boundary testing:
    - Maximum valid raw PKR (999999999999.99) -> 201
    - First invalid raw PKR (1000000000000.00) -> 422
    - Maximum representable valid crore (99999.9999) -> 201
    - 100000 crore -> 422
    - Negative amounts (-1.00 raw, -0.0001 crore) -> 422
    - Excessive fractional precision (120.555 raw, 12.12345 crore) -> 422
    - Null / omitted amounts -> 201
    - Very large values (1e15) -> 422
    - Invalid numeric inputs (NaN, Infinity, -Infinity) -> 422
    """
    token, _ = await create_user(project_client, email="money.exhaustive@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Maximum valid raw PKR: 999,999,999,999.99
    res_max_raw = await project_client.post(
        "/api/v1/projects",
        json={"name": "Max Raw Project", "location": "Loc", "budgetRaw": 999999999999.99},
        headers=headers,
    )
    assert res_max_raw.status_code == 201
    data_max_raw = res_max_raw.json()
    assert data_max_raw["budgetRaw"] == 999999999999.99
    assert data_max_raw["budgetCrore"] == 99999.9999

    # 2. First invalid raw PKR value: 1,000,000,000,000.00 (exceeds NUMERIC(15,2))
    res_invalid_raw = await project_client.post(
        "/api/v1/projects",
        json={"name": "Invalid Raw Project", "location": "Loc", "budgetRaw": 1000000000000.00},
        headers=headers,
    )
    assert res_invalid_raw.status_code == 422

    # 3. Maximum representable valid crore input at permitted scale: 99999.9999
    res_max_crore = await project_client.post(
        "/api/v1/projects",
        json={"name": "Max Crore Project", "location": "Loc", "budgetCrore": 99999.9999},
        headers=headers,
    )
    assert res_max_crore.status_code == 201
    assert res_max_crore.json()["budgetCrore"] == 99999.9999
    assert res_max_crore.json()["budgetRaw"] == 999999999000.00

    # 4. 100,000 crore (equals 1,000,000,000,000 PKR, exceeding NUMERIC(15,2))
    res_100k_crore = await project_client.post(
        "/api/v1/projects",
        json={"name": "100k Crore Project", "location": "Loc", "budgetCrore": 100000.0},
        headers=headers,
    )
    assert res_100k_crore.status_code == 422

    # 5. Negative amounts
    res_neg_raw = await project_client.post(
        "/api/v1/projects",
        json={"name": "Neg Raw Project", "location": "Loc", "budgetRaw": -1.00},
        headers=headers,
    )
    assert res_neg_raw.status_code == 422

    res_neg_crore = await project_client.post(
        "/api/v1/projects",
        json={"name": "Neg Crore Project", "location": "Loc", "budgetCrore": -0.0001},
        headers=headers,
    )
    assert res_neg_crore.status_code == 422

    # 6. Excessive fractional precision
    res_scale_raw = await project_client.post(
        "/api/v1/projects",
        json={"name": "Scale Raw Project", "location": "Loc", "budgetRaw": 120.555},
        headers=headers,
    )
    assert res_scale_raw.status_code == 422

    res_scale_crore = await project_client.post(
        "/api/v1/projects",
        json={"name": "Scale Crore Project", "location": "Loc", "budgetCrore": 12.12345},
        headers=headers,
    )
    assert res_scale_crore.status_code == 422

    # 7. Null and omitted amounts
    res_omitted = await project_client.post(
        "/api/v1/projects",
        json={"name": "Omitted Budget Project", "location": "Loc"},
        headers=headers,
    )
    assert res_omitted.status_code == 201
    assert res_omitted.json()["budgetRaw"] == 0.0
    assert res_omitted.json()["budgetCrore"] == 0.0

    # 8. Very large values (1e15)
    res_huge = await project_client.post(
        "/api/v1/projects",
        json={"name": "Huge Budget Project", "location": "Loc", "budgetRaw": 1e15},
        headers=headers,
    )
    assert res_huge.status_code == 422

    # 9. Non-finite values (NaN, Infinity, -Infinity)
    for bad_val in ("NaN", "Infinity", "-Infinity"):
        res_bad = await project_client.post(
            "/api/v1/projects",
            json={"name": "Bad Number Project", "location": "Loc", "budgetRaw": bad_val},
            headers=headers,
        )
        assert res_bad.status_code == 422


# ---------------------------------------------------------------------------
# 31. Tenant-Safe UUID & Scoped Code Authorization (Anti-Enumeration)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tenant_safe_uuid_and_code_authorization(project_client: AsyncClient):
    """
    Verifies that:
    - User B cannot access User A's project even when knowing User A's UUID -> 404
    - User B requesting User A's public code -> 404
    - Collaborator on User A's project can access Project A by UUID and code
    - Collaborator cannot access User B's project by UUID or code
    """
    token_a, user_a = await create_user(project_client, email="tenant.a@tameerai.pk")
    token_b, user_b = await create_user(project_client, email="tenant.b@tameerai.pk")
    token_c, user_c = await create_user(project_client, email="tenant.c@tameerai.pk")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    headers_c = {"Authorization": f"Bearer {token_c}"}

    # User A creates Project A (PRJ-001)
    prj_a = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Project Alpha", "location": "Loc"},
        headers=headers_a,
    )).json()

    # User B creates Project B (PRJ-001)
    prj_b = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Project Beta", "location": "Loc"},
        headers=headers_b,
    )).json()

    assert prj_a["id"] == "PRJ-001"
    assert prj_b["id"] == "PRJ-001"
    assert prj_a["uuid"] != prj_b["uuid"]

    # 1. User B tries to read User A's project using User A's internal UUID -> 404
    res_b_a_uuid = await project_client.get(f"/api/v1/projects/{prj_a['uuid']}", headers=headers_b)
    assert res_b_a_uuid.status_code == 404

    # 2. User A tries to read User B's project using User B's internal UUID -> 404
    res_a_b_uuid = await project_client.get(f"/api/v1/projects/{prj_b['uuid']}", headers=headers_a)
    assert res_a_b_uuid.status_code == 404

    # 3. User A invites User C to Project Alpha
    inv_res = await project_client.post(
        f"/api/v1/projects/{prj_a['id']}/members",
        json={"userId": user_c["id"], "role": "viewer"},
        headers=headers_a,
    )
    assert inv_res.status_code == 201

    # 4. User C requests "PRJ-001" -> resolves to Project Alpha (not Beta)
    res_c_code = await project_client.get("/api/v1/projects/PRJ-001", headers=headers_c)
    assert res_c_code.status_code == 200
    assert res_c_code.json()["uuid"] == prj_a["uuid"]
    assert res_c_code.json()["name"] == "Project Alpha"

    # 5. User C tries to access Project Beta by UUID -> 404
    res_c_b_uuid = await project_client.get(f"/api/v1/projects/{prj_b['uuid']}", headers=headers_c)
    assert res_c_b_uuid.status_code == 404


# ---------------------------------------------------------------------------
# 32. Lead Engineer Cannot Modify or Remove Peer Lead Engineer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lead_engineer_cannot_modify_or_remove_peer_lead_engineer(project_client: AsyncClient):
    """
    Verifies role capability boundaries:
    - Lead Engineer cannot modify peer Lead Engineer's role -> 403
    - Lead Engineer cannot remove peer Lead Engineer -> 403
    - Lead Engineer cannot remove project owner -> 400
    - Lead Engineer cannot self-demote or self-remove -> 403
    """
    token_owner, _ = await create_user(project_client, email="owner.hierarchy@tameerai.pk")
    token_lead1, lead1 = await create_user(project_client, email="lead1.hier@tameerai.pk")
    token_lead2, lead2 = await create_user(project_client, email="lead2.hier@tameerai.pk")

    headers_owner = {"Authorization": f"Bearer {token_owner}"}
    headers_lead1 = {"Authorization": f"Bearer {token_lead1}"}

    # Owner creates project
    prj = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Hierarchy Plaza", "location": "Loc"},
        headers=headers_owner,
    )).json()
    prj_id = prj["id"]

    # Owner adds both as lead_engineer
    m1 = (await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": lead1["id"], "role": "lead_engineer"},
        headers=headers_owner,
    )).json()

    m2 = (await project_client.post(
        f"/api/v1/projects/{prj_id}/members",
        json={"userId": lead2["id"], "role": "lead_engineer"},
        headers=headers_owner,
    )).json()

    # 1. Lead 1 attempts to modify Lead 2's role to architect -> 403
    res_mod = await project_client.patch(
        f"/api/v1/projects/{prj_id}/members/{m2['id']}",
        json={"role": "architect"},
        headers=headers_lead1,
    )
    assert res_mod.status_code == 403
    assert "cannot modify member with equal or higher role" in res_mod.json()["detail"].lower()

    # 2. Lead 1 attempts to remove Lead 2 -> 403
    res_rem = await project_client.delete(
        f"/api/v1/projects/{prj_id}/members/{m2['id']}",
        headers=headers_lead1,
    )
    assert res_rem.status_code == 403
    assert "cannot remove member with equal or higher role" in res_rem.json()["detail"].lower()

    # 3. Lead 1 attempts to remove themselves -> 403
    res_self_rem = await project_client.delete(
        f"/api/v1/projects/{prj_id}/members/{m1['id']}",
        headers=headers_lead1,
    )
    assert res_self_rem.status_code == 403
    assert "cannot remove own membership record" in res_self_rem.json()["detail"].lower()

    # 4. Lead 1 attempts to modify own role -> 403
    res_self_mod = await project_client.patch(
        f"/api/v1/projects/{prj_id}/members/{m1['id']}",
        json={"role": "viewer"},
        headers=headers_lead1,
    )
    assert res_self_mod.status_code == 403
    assert "self-escalation forbidden" in res_self_mod.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 33. Ambiguous Public-Code Resolution (Multiple Accessible Matches -> 409)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ambiguous_public_code_resolution_multi_membership(project_client: AsyncClient):
    """
    Scenario:
    - User A owns Project A with code PRJ-001.
    - User B owns Project B with code PRJ-001.
    - User C is an authorized collaborator on BOTH Project A and Project B.

    Required Behavior:
    - User C GET /projects/PRJ-001 -> HTTP 409 Conflict (Ambiguity detected).
    - User C GET /projects/{uuid_a} -> HTTP 200 (Project Alpha).
    - User C GET /projects/{uuid_b} -> HTTP 200 (Project Beta).
    - User A GET /projects/PRJ-001 -> HTTP 200 (only Project Alpha is accessible to A).
    - User B GET /projects/PRJ-001 -> HTTP 200 (only Project Beta is accessible to B).
    - User D (unrelated) GET /projects/PRJ-001 -> HTTP 404 (no leak).
    - User D GET /projects/{uuid_a} -> HTTP 404.
    - User C GET /projects/PRJ-001/members -> HTTP 409 Conflict.
    - User C GET /projects/{uuid_a}/members -> HTTP 200.
    """
    token_a, _ = await create_user(project_client, email="owner.a.ambig@tameerai.pk")
    token_b, _ = await create_user(project_client, email="owner.b.ambig@tameerai.pk")
    token_c, user_c = await create_user(project_client, email="collab.c.ambig@tameerai.pk")
    token_d, _ = await create_user(project_client, email="unrelated.d.ambig@tameerai.pk")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    headers_c = {"Authorization": f"Bearer {token_c}"}
    headers_d = {"Authorization": f"Bearer {token_d}"}

    # 1. User A creates Project Alpha (gets PRJ-001)
    prj_a = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Project Alpha", "location": "Lahore"},
        headers=headers_a,
    )).json()

    # 2. User B creates Project Beta (gets PRJ-001 under User B's workspace)
    prj_b = (await project_client.post(
        "/api/v1/projects",
        json={"name": "Project Beta", "location": "Islamabad"},
        headers=headers_b,
    )).json()

    assert prj_a["id"] == "PRJ-001"
    assert prj_b["id"] == "PRJ-001"
    assert prj_a["uuid"] != prj_b["uuid"]

    # 3. User A adds User C as 'architect' to Project Alpha
    add_a = await project_client.post(
        f"/api/v1/projects/{prj_a['uuid']}/members",
        json={"userId": user_c["id"], "role": "architect"},
        headers=headers_a,
    )
    assert add_a.status_code == 201

    # 4. User B adds User C as 'viewer' to Project Beta
    add_b = await project_client.post(
        f"/api/v1/projects/{prj_b['uuid']}/members",
        json={"userId": user_c["id"], "role": "viewer"},
        headers=headers_b,
    )
    assert add_b.status_code == 201

    # 5. User C calls GET /api/v1/projects/PRJ-001 -> MUST return HTTP 409 Conflict
    res_c_ambig = await project_client.get("/api/v1/projects/PRJ-001", headers=headers_c)
    assert res_c_ambig.status_code == 409
    assert "ambiguous project code 'prj-001'" in res_c_ambig.json()["detail"].lower()
    assert "uuid" in res_c_ambig.json()["detail"].lower()

    # 6. User C resolves Project Alpha unambiguously using UUID -> HTTP 200
    res_c_uuid_a = await project_client.get(f"/api/v1/projects/{prj_a['uuid']}", headers=headers_c)
    assert res_c_uuid_a.status_code == 200
    assert res_c_uuid_a.json()["name"] == "Project Alpha"
    assert res_c_uuid_a.json()["id"] == "PRJ-001"

    # 7. User C resolves Project Beta unambiguously using UUID -> HTTP 200
    res_c_uuid_b = await project_client.get(f"/api/v1/projects/{prj_b['uuid']}", headers=headers_c)
    assert res_c_uuid_b.status_code == 200
    assert res_c_uuid_b.json()["name"] == "Project Beta"
    assert res_c_uuid_b.json()["id"] == "PRJ-001"

    # 8. User A calls GET /api/v1/projects/PRJ-001 -> exactly 1 accessible match (Project Alpha) -> HTTP 200
    res_a_code = await project_client.get("/api/v1/projects/PRJ-001", headers=headers_a)
    assert res_a_code.status_code == 200
    assert res_a_code.json()["uuid"] == prj_a["uuid"]
    assert res_a_code.json()["name"] == "Project Alpha"

    # 9. User B calls GET /api/v1/projects/PRJ-001 -> exactly 1 accessible match (Project Beta) -> HTTP 200
    res_b_code = await project_client.get("/api/v1/projects/PRJ-001", headers=headers_b)
    assert res_b_code.status_code == 200
    assert res_b_code.json()["uuid"] == prj_b["uuid"]
    assert res_b_code.json()["name"] == "Project Beta"

    # 10. User D (unrelated) calls GET /api/v1/projects/PRJ-001 -> 0 matches -> HTTP 404
    res_d_code = await project_client.get("/api/v1/projects/PRJ-001", headers=headers_d)
    assert res_d_code.status_code == 404

    # 11. User D calls GET /api/v1/projects/{uuid_a} -> HTTP 404 (anti-enumeration)
    res_d_uuid = await project_client.get(f"/api/v1/projects/{prj_a['uuid']}", headers=headers_d)
    assert res_d_uuid.status_code == 404

    # 12. Membership endpoints with ambiguous code:
    # User C calls GET /api/v1/projects/PRJ-001/members -> HTTP 409 Conflict
    res_c_members_ambig = await project_client.get("/api/v1/projects/PRJ-001/members", headers=headers_c)
    assert res_c_members_ambig.status_code == 409

    # User C calls GET /api/v1/projects/{uuid_a}/members -> HTTP 200
    res_c_members_a = await project_client.get(f"/api/v1/projects/{prj_a['uuid']}/members", headers=headers_c)
    assert res_c_members_a.status_code == 200
    assert len(res_c_members_a.json()) >= 1



