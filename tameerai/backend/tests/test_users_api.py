"""
TameerAI - Phase 02B Automated User Profile & Settings Test Suite

Comprehensive tests for:
1. Authenticated profile read (GET /api/v1/users/me)
2. Authenticated profile update (PATCH /api/v1/users/me)
3. Valid partial updates (omitted fields preserve existing values)
4. Invalid profile inputs (length validation on fullName, etc.)
5. Forbidden administrative field updates (mass-assignment defense: role, email, isActive, etc.)
6. Authenticated settings read (GET /api/v1/users/me/settings)
7. Authenticated settings update (PATCH /api/v1/users/me/settings)
8. Missing settings row behavior (automatic safe recovery/instantiation)
9. Invalid language and theme validation (enum checks)
10. Sensitive field exclusion (no password hashes, no internal secrets)
11. User ownership isolation (User A cannot access or mutate User B)
12. Unauthorized requests rejection (401 without Bearer token)
13. Invalid, forged, or expired token rejection (401)
14. Deactivated / disabled user rejection (403 Forbidden)
15. Transaction rollback on update failure
"""

from datetime import datetime, timedelta, timezone
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
from app.core.config import settings
from app.core.rate_limit import login_limiter
from app.core.security import create_access_token
from app.db.base import Base
from app.main import app
from app.models.user import User, UserSettings


# ---------------------------------------------------------------------------
# Isolated In-Memory SQLite Test Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_session_factory():
    """Isolated SQLite database per test."""
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
async def user_client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
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
async def create_and_login_user(client: AsyncClient, email: str, role: str = "engineer", full_name: str = "Test User"):
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
# 1. Authenticated Profile Read
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_my_profile_authenticated(user_client: AsyncClient):
    token, user_data = await create_and_login_user(
        user_client,
        email="engr.ali@tameerai.pk",
        full_name="Engr. Ali Raza",
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await user_client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "engr.ali@tameerai.pk"
    assert data["fullName"] == "Engr. Ali Raza"
    assert data["role"] == "engineer"
    assert data["city"] == "Lahore"
    assert data["isActive"] is True
    assert "hashed_password" not in data
    assert "password" not in data


# ---------------------------------------------------------------------------
# 2. Authenticated Profile Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_my_profile(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="update.test@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "fullName": "Engr. Ali Raza, Senior Structural Lead",
        "company": "NESPAK Pvt Ltd",
        "pecNumber": "CIVIL-998877",
        "phone": "+92 300 9876543",
        "city": "Islamabad",
        "bio": "15+ years leading high-rise seismic compliance.",
    }
    res = await user_client.patch("/api/v1/users/me", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["fullName"] == "Engr. Ali Raza, Senior Structural Lead"
    assert data["company"] == "NESPAK Pvt Ltd"
    assert data["pecNumber"] == "CIVIL-998877"
    assert data["phone"] == "+92 300 9876543"
    assert data["city"] == "Islamabad"
    assert data["bio"] == "15+ years leading high-rise seismic compliance."


# ---------------------------------------------------------------------------
# 3. Valid Partial Profile Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_partial_profile_update(user_client: AsyncClient):
    token, _ = await create_and_login_user(
        user_client,
        email="partial.test@tameer.pk",
        full_name="Initial Name",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Update only city
    res = await user_client.patch("/api/v1/users/me", json={"city": "Karachi"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["city"] == "Karachi"
    assert data["fullName"] == "Initial Name"  # Preserved
    assert data["email"] == "partial.test@tameer.pk"  # Preserved


# ---------------------------------------------------------------------------
# 4. Invalid Profile Inputs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_profile_inputs(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="invalid.input@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}

    # Too short full_name (< 2 chars)
    res = await user_client.patch("/api/v1/users/me", json={"fullName": "A"}, headers=headers)
    assert res.status_code == 422

    # Explicit null full_name
    res_null_name = await user_client.patch("/api/v1/users/me", json={"fullName": None}, headers=headers)
    assert res_null_name.status_code == 422

    # Explicit null city
    res_null_city = await user_client.patch("/api/v1/users/me", json={"city": None}, headers=headers)
    assert res_null_city.status_code == 422

    # Empty string city
    res_empty_city = await user_client.patch("/api/v1/users/me", json={"city": ""}, headers=headers)
    assert res_empty_city.status_code == 422

    # Single char city
    res_short_city = await user_client.patch("/api/v1/users/me", json={"city": "K"}, headers=headers)
    assert res_short_city.status_code == 422

    # Valid city update
    res_valid_city = await user_client.patch("/api/v1/users/me", json={"city": "Islamabad"}, headers=headers)
    assert res_valid_city.status_code == 200
    assert res_valid_city.json()["city"] == "Islamabad"

    # Omitted city preserves previous value
    res_omit_city = await user_client.patch("/api/v1/users/me", json={"bio": "Updated bio only"}, headers=headers)
    assert res_omit_city.status_code == 200
    assert res_omit_city.json()["city"] == "Islamabad"
    assert res_omit_city.json()["bio"] == "Updated bio only"


# ---------------------------------------------------------------------------
# 5. Forbidden Administrative Field Updates (Mass-Assignment Protection)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forbidden_field_updates_rejected(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="mass.assign@tameer.pk", role="engineer")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt to escalate role
    res1 = await user_client.patch("/api/v1/users/me", json={"role": "company"}, headers=headers)
    assert res1.status_code == 422

    # 2. Attempt to alter email
    res2 = await user_client.patch("/api/v1/users/me", json={"email": "hacked@domain.com"}, headers=headers)
    assert res2.status_code == 422

    # 3. Attempt to set is_verified
    res3 = await user_client.patch("/api/v1/users/me", json={"isVerified": True}, headers=headers)
    assert res3.status_code == 422

    # 4. Attempt to pass password/hash
    res4 = await user_client.patch("/api/v1/users/me", json={"hashed_password": "evil"}, headers=headers)
    assert res4.status_code == 422


# ---------------------------------------------------------------------------
# 6. Authenticated Settings Read
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_my_settings_authenticated(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="settings.read@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}

    res = await user_client.get("/api/v1/users/me/settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "en"
    assert data["theme"] == "system"
    assert data["pbcViolations"] is True
    assert data["fidicRisks"] is True
    assert data["strictness"] == "strict"
    assert data["fidicThreshold"] == "8"
    assert data["marketRegion"] == "lahore"
    assert data["aiTone"] == "professional"
    assert "userId" in data


# ---------------------------------------------------------------------------
# 7. Authenticated Settings Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_my_settings(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="settings.update@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "language": "ur",
        "theme": "dark",
        "pbcViolations": False,
        "whatsappAlerts": False,
        "strictness": "consultative",
        "fidicThreshold": "9",
        "marketRegion": "karachi",
        "aiTone": "practical",
    }
    res = await user_client.patch("/api/v1/users/me/settings", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "ur"
    assert data["theme"] == "dark"
    assert data["pbcViolations"] is False
    assert data["whatsappAlerts"] is False
    assert data["strictness"] == "consultative"
    assert data["fidicThreshold"] == "9"
    assert data["marketRegion"] == "karachi"
    assert data["aiTone"] == "practical"
    # Unmodified fields should retain defaults
    assert data["fidicRisks"] is True


# ---------------------------------------------------------------------------
# 8. Missing Settings Row Safe Recovery
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_settings_row_recovery(user_client: AsyncClient, async_db: AsyncSession):
    """
    If a user's settings row is deleted or missing, the endpoint recovers
    transparently by instantiating and committing standard defaults.
    """
    token, user_data = await create_and_login_user(user_client, email="missing.settings@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}
    user_id = UUID(user_data["id"])

    # Simulate missing row by manually deleting settings from DB
    from sqlalchemy import delete
    await async_db.execute(delete(UserSettings).where(UserSettings.user_id == user_id))
    await async_db.commit()

    # GET /settings should recover and return fresh defaults
    res = await user_client.get("/api/v1/users/me/settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "en"
    assert data["strictness"] == "strict"


# ---------------------------------------------------------------------------
# 9. Invalid Language and Theme Validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_settings_validation(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="invalid.settings@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid language
    res1 = await user_client.patch("/api/v1/users/me/settings", json={"language": "fr"}, headers=headers)
    assert res1.status_code == 422

    # Invalid theme
    res2 = await user_client.patch("/api/v1/users/me/settings", json={"theme": "neon-blue"}, headers=headers)
    assert res2.status_code == 422

    # Invalid AI strictness
    res3 = await user_client.patch("/api/v1/users/me/settings", json={"strictness": "ultra-hard"}, headers=headers)
    assert res3.status_code == 422

    # Extra forbidden field
    res4 = await user_client.patch("/api/v1/users/me/settings", json={"adminPrivilege": True}, headers=headers)
    assert res4.status_code == 422


# ---------------------------------------------------------------------------
# 10. Sensitive Field Exclusion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sensitive_field_exclusion(user_client: AsyncClient):
    token, _ = await create_and_login_user(user_client, email="sensitive.check@tameer.pk")
    headers = {"Authorization": f"Bearer {token}"}

    prof_res = await user_client.get("/api/v1/users/me", headers=headers)
    data = prof_res.json()
    assert "hashed_password" not in data
    assert "password" not in data
    assert "refresh_token" not in data

    sett_res = await user_client.get("/api/v1/users/me/settings", headers=headers)
    sett_data = sett_res.json()
    assert "hashed_password" not in sett_data


# ---------------------------------------------------------------------------
# 11. User Ownership Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_ownership_isolation(user_client: AsyncClient):
    """
    Verifies that User A's token cannot read or mutate User B's profile or settings.
    Endpoints bind strictly to current_user from the verified JWT.
    """
    token_a, user_a = await create_and_login_user(user_client, email="user.a@tameer.pk", full_name="User Alpha")
    token_b, user_b = await create_and_login_user(user_client, email="user.b@tameer.pk", full_name="User Beta")

    # User A updates their profile
    await user_client.patch(
        "/api/v1/users/me",
        json={"fullName": "User Alpha Modified"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B reads their profile: must remain User Beta unchanged
    b_profile = await user_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_profile.json()["fullName"] == "User Beta"

    # User A updates settings to Urdu
    await user_client.patch(
        "/api/v1/users/me/settings",
        json={"language": "ur"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B's settings must remain untouched ('en')
    b_settings = await user_client.get(
        "/api/v1/users/me/settings",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_settings.json()["language"] == "en"


# ---------------------------------------------------------------------------
# 12. Unauthorized Requests Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthorized_endpoints_rejection(user_client: AsyncClient):
    # GET /users/me without token -> 401
    res1 = await user_client.get("/api/v1/users/me")
    assert res1.status_code == 401

    # PATCH /users/me without token -> 401
    res2 = await user_client.patch("/api/v1/users/me", json={"fullName": "No Token"})
    assert res2.status_code == 401

    # GET /users/me/settings without token -> 401
    res3 = await user_client.get("/api/v1/users/me/settings")
    assert res3.status_code == 401

    # PATCH /users/me/settings without token -> 401
    res4 = await user_client.patch("/api/v1/users/me/settings", json={"language": "ur"})
    assert res4.status_code == 401


# ---------------------------------------------------------------------------
# 13. Invalid and Expired Tokens Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_and_expired_tokens(user_client: AsyncClient):
    # Expired token
    expired_token = create_access_token(
        user_id=uuid4(),
        role="engineer",
        expires_delta=timedelta(seconds=-30),
    )
    res1 = await user_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res1.status_code == 401
    assert "expired" in res1.json()["detail"].lower()

    # Forged signature
    res2 = await user_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.e30.fake_signature"},
    )
    assert res2.status_code == 401


# ---------------------------------------------------------------------------
# 14. Disabled User Access Denied
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disabled_user_access_denied(user_client: AsyncClient, async_db: AsyncSession):
    token, user_data = await create_and_login_user(user_client, email="disabled.user@tameer.pk")
    user_id = UUID(user_data["id"])

    # Disable user in DB
    user = await async_db.scalar(select(User).where(User.id == user_id))
    user.is_active = False
    await async_db.commit()

    # Attempts to read profile or settings must return 403 Forbidden
    res1 = await user_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 403

    res2 = await user_client.get("/api/v1/users/me/settings", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403


# ---------------------------------------------------------------------------
# 15. Transaction Rollback on Update Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transaction_rollback_on_update_failure():
    """
    Verifies that if a database commit fails during profile update,
    the transaction is rolled back and an HTTP 500 is safely raised.
    """
    from unittest.mock import AsyncMock
    from app.services.user_service import update_user_profile
    from app.schemas.user import UserUpdate
    from fastapi import HTTPException

    mock_db = AsyncMock()
    mock_db.commit.side_effect = RuntimeError("Simulated DB Commit failure")

    test_user = User(
        id=uuid4(),
        email="rollback@test.pk",
        full_name="Original Name",
        hashed_password="hash",
    )
    payload = UserUpdate(fullName="Should Be Rolled Back")

    with pytest.raises(HTTPException) as exc_info:
        await update_user_profile(db=mock_db, user=test_user, payload=payload)

    assert exc_info.value.status_code == 500
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_rollback_preserves_database(async_db: AsyncSession):
    """
    Verifies that executing rollback on a real database session reverts
    uncommitted dirty in-memory modifications.
    """
    user = User(
        email="persisted@tameer.pk",
        hashed_password="hash",
        full_name="Original Name",
    )
    async_db.add(user)
    await async_db.commit()
    target_id = user.id

    # Mutate in-memory
    user.full_name = "Dirty Edit"
    await async_db.rollback()

    # Re-query from database using preserved ID
    refreshed = await async_db.scalar(select(User).where(User.id == target_id))
    assert refreshed.full_name == "Original Name"


# ---------------------------------------------------------------------------
# 16. Persona Role Consistency Across Registration and Profile
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("persona_role", ["engineer", "contractor", "architect", "company"])
@pytest.mark.asyncio
async def test_persona_roles_registration_and_profile_consistency(
    user_client: AsyncClient,
    persona_role: str,
):
    """
    Verifies that all 4 approved persona roles (engineer, contractor, architect, company)
    can be registered, stored in the database, and retrieved identically via
    both /api/v1/users/me and /api/v1/auth/me endpoints.
    """
    email = f"persona.{persona_role}@tameerai.pk"
    token, user_info = await create_and_login_user(
        user_client,
        email=email,
        role=persona_role,
        full_name=f"Test {persona_role.capitalize()}",
    )
    headers = {"Authorization": f"Bearer {token}"}

    assert user_info["role"] == persona_role

    # 1. Check GET /api/v1/users/me
    users_me_res = await user_client.get("/api/v1/users/me", headers=headers)
    assert users_me_res.status_code == 200
    assert users_me_res.json()["role"] == persona_role

    # 2. Check GET /api/v1/auth/me
    auth_me_res = await user_client.get("/api/v1/auth/me", headers=headers)
    assert auth_me_res.status_code == 200
    assert auth_me_res.json()["role"] == persona_role


@pytest.mark.parametrize("invalid_role", ["admin", "user", "superadmin", "manager", "root"])
@pytest.mark.asyncio
async def test_unauthorized_persona_roles_rejected(
    user_client: AsyncClient,
    invalid_role: str,
):
    """
    Verifies that arbitrary, unapproved, or administrative role names are
    strictly rejected with 422 Unprocessable Entity during registration.
    """
    payload = {
        "fullName": "Unauthorized Role Attempt",
        "email": f"invalid.{invalid_role}@tameerai.pk",
        "password": "Password12345!",
        "role": invalid_role,
        "city": "Lahore",
    }
    res = await user_client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422
    assert "role" in str(res.json()).lower()


# ---------------------------------------------------------------------------
# 17. Settings UUID vs User UUID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_settings_uuid_distinct_from_user_uuid(user_client: AsyncClient):
    """
    Verifies that settings.id is the actual primary key of user_settings and
    is distinct from settings.userId (which references the owner user.id).
    Ensures user UUID is never incorrectly reused as settings UUID.
    """
    token, user_data = await create_and_login_user(
        user_client,
        email="uuid.check@tameerai.pk",
        full_name="UUID Check User",
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await user_client.get("/api/v1/users/me/settings", headers=headers)
    assert res.status_code == 200
    settings_data = res.json()

    settings_id = UUID(settings_data["id"])
    owner_user_id = UUID(settings_data["userId"])
    user_id = UUID(user_data["id"])

    # Owner user id in settings must match user id
    assert owner_user_id == user_id
    # Settings primary key must NOT be equal to user primary key
    assert settings_id != owner_user_id


# ---------------------------------------------------------------------------
# 18. Strict CamelCase Serialization & No Snake_Case Leakage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_strict_camel_case_serialization_and_no_snake_case_leakage(user_client: AsyncClient):
    """
    Verifies that JSON responses from both /api/v1/users/me and /api/v1/users/me/settings
    strictly follow camelCase naming and contain zero snake_case keys with underscores.
    """
    token, _ = await create_and_login_user(
        user_client,
        email="camelcase.check@tameerai.pk",
        full_name="Camel Case Check",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Profile response
    prof_res = await user_client.get("/api/v1/users/me", headers=headers)
    assert prof_res.status_code == 200
    prof_data = prof_res.json()
    for key in prof_data.keys():
        assert "_" not in key, f"Snake_case key '{key}' leaked in UserRead response: {prof_data}"

    # Required camelCase keys present in UserRead
    assert "fullName" in prof_data
    assert "isActive" in prof_data
    assert "isVerified" in prof_data
    assert "createdAt" in prof_data
    assert "updatedAt" in prof_data

    # Settings response
    sett_res = await user_client.get("/api/v1/users/me/settings", headers=headers)
    assert sett_res.status_code == 200
    sett_data = sett_res.json()
    for key in sett_data.keys():
        assert "_" not in key, f"Snake_case key '{key}' leaked in UserSettingsRead response: {sett_data}"

    # Required camelCase keys present in UserSettingsRead
    expected_camel_keys = {
        "id", "userId", "language", "theme",
        "pbcViolations", "fidicRisks", "priceSpikes", "weeklyDigest", "whatsappAlerts",
        "strictness", "fidicThreshold", "autoCitations", "marketRegion", "aiTone",
        "createdAt", "updatedAt",
    }
    assert set(sett_data.keys()) == expected_camel_keys


# ---------------------------------------------------------------------------
# 19. User Settings Full Update Roundtrip
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_settings_full_update_roundtrip(user_client: AsyncClient):
    """
    Tests updating every single one of the 12 configurable user preferences
    via PATCH /api/v1/users/me/settings and asserts full persistence and retrieval.
    """
    token, _ = await create_and_login_user(user_client, email="roundtrip@tameerai.pk")
    headers = {"Authorization": f"Bearer {token}"}

    full_update = {
        "language": "ur",
        "theme": "dark",
        "pbcViolations": False,
        "fidicRisks": False,
        "priceSpikes": False,
        "weeklyDigest": True,
        "whatsappAlerts": False,
        "strictness": "consultative",
        "fidicThreshold": "6",
        "autoCitations": False,
        "marketRegion": "islamabad",
        "aiTone": "legal",
    }
    patch_res = await user_client.patch("/api/v1/users/me/settings", json=full_update, headers=headers)
    assert patch_res.status_code == 200
    patch_data = patch_res.json()

    for k, v in full_update.items():
        assert patch_data[k] == v, f"Field '{k}' mismatch: expected {v}, got {patch_data[k]}"

    # Verify subsequent GET returns identical values
    get_res = await user_client.get("/api/v1/users/me/settings", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()

    for k, v in full_update.items():
        assert get_data[k] == v, f"Persisted field '{k}' mismatch on GET: expected {v}, got {get_data[k]}"


# ---------------------------------------------------------------------------
# 20. Concurrent Settings Creation Race Handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_settings_creation_integrity_error_recovery():
    """
    Tests get_or_create_user_settings when an IntegrityError occurs on the insert
    commit (simulating a concurrent race where another transaction created the row
    first). Asserts rollback is executed and the existing row is cleanly returned.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from sqlalchemy.exc import IntegrityError
    from app.services.user_service import get_or_create_user_settings

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    user_id = uuid4()
    existing_settings = UserSettings(user_id=user_id, language="en")

    # First scalar call (check if exists): returns None
    # Second scalar call (after rollback): returns existing_settings
    mock_db.scalar.side_effect = [None, existing_settings]
    mock_db.commit.side_effect = IntegrityError("Unique constraint violation", params=None, orig=Exception())

    result = await get_or_create_user_settings(db=mock_db, user_id=user_id)

    assert result == existing_settings
    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# 21. Settings Update Transaction Rollback on Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_settings_update_transaction_rollback_on_failure():
    """
    Verifies that if a database commit fails during update_user_settings,
    the transaction is rolled back and an HTTP 500 is safely raised.
    """
    from unittest.mock import AsyncMock
    from fastapi import HTTPException
    from app.services.user_service import update_user_settings
    from app.schemas.user import UserSettingsUpdate

    mock_db = AsyncMock()
    user_id = uuid4()
    existing_settings = UserSettings(user_id=user_id, language="en")
    mock_db.scalar.return_value = existing_settings
    mock_db.commit.side_effect = RuntimeError("Database IO failure during settings commit")

    payload = UserSettingsUpdate(language="ur")

    with pytest.raises(HTTPException) as exc_info:
        await update_user_settings(db=mock_db, user_id=user_id, payload=payload)

    assert exc_info.value.status_code == 500
    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# 22. ORM to Expected Column Parity
# ---------------------------------------------------------------------------

def test_orm_models_column_parity():
    """
    Verifies that SQLAlchemy User and UserSettings models declare exactly the
    columns present in the deployed schema, with zero missing or extra fields.
    """
    user_cols = set(User.__table__.columns.keys())
    expected_user_cols = {
        "id", "email", "hashed_password", "full_name", "role",
        "company", "pec_number", "phone", "city", "bio",
        "is_active", "is_verified", "created_at", "updated_at",
    }
    assert user_cols == expected_user_cols, f"User ORM column mismatch: {user_cols ^ expected_user_cols}"

    settings_cols = set(UserSettings.__table__.columns.keys())
    expected_settings_cols = {
        "id", "user_id", "language", "theme",
        "pbc_violations_alert", "fidic_risks_alert", "price_spikes_alert",
        "weekly_digest_alert", "whatsapp_alerts",
        "ai_strictness", "fidic_threshold", "auto_citations",
        "market_region", "ai_tone",
        "created_at", "updated_at",
    }
    assert settings_cols == expected_settings_cols, f"UserSettings ORM column mismatch: {settings_cols ^ expected_settings_cols}"

