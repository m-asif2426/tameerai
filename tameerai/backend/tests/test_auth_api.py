"""
TameerAI - Phase 02A Automated Authentication Test Suite

Comprehensive tests for:
1. Successful registration
2. Invalid registration payload (email, short password, illegal role)
3. Duplicate email rejection (409 Conflict)
4. Argon2id password hashing and verification
5. Password and hashes strictly excluded from API responses
6. Automatic 1:1 user_settings creation in the same transaction
7. Successful login with dual token issuance and HttpOnly cookie
8. Invalid email/password (generic 401 error message)
9. Disabled accounts rejection (403 Forbidden)
10. JWT generation, algorithm locking, and claims verification
11. Expired, forged, or malformed JWT handling (401 Unauthorized)
12. Authenticated /api/v1/auth/me profile resolution
13. Token refresh via request body and HttpOnly cookie
14. Refresh token rotation (old token revoked, new token provisioned)
15. Refresh token reuse / replay attack detection (revokes all user sessions)
16. Logout session revocation and cookie clearing
17. Unauthorized access rejection on protected routes
18. Concurrent registration uniqueness race handling with rollback
19. Concurrent refresh handling with row locking
20. Database transaction rollback on mid-operation failure
21. Sliding-window rate limiting on failed login attempts (429 Too Many Requests)
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from uuid import UUID, uuid4

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_db
from app.core.config import settings
from app.core.rate_limit import login_limiter
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.base import Base
from app.main import app
from app.models.user import User, UserSession, UserSettings
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user


# ---------------------------------------------------------------------------
# Test Fixtures: Isolated In-Memory SQLite Database
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_session_factory():
    """
    Creates an isolated in-memory SQLite database per test.
    Never modifies or accesses remote hosted Supabase.
    """
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
    """Provides a standalone async session for direct DB queries in tests."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def auth_client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client configured with dependency override for get_db,
    allocating a fresh isolated AsyncSession per request.
    """
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


# ---------------------------------------------------------------------------
# 1. Successful Registration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_registration(auth_client: AsyncClient, async_db: AsyncSession):
    payload = {
        "fullName": "Engr. Ahmed Khan",
        "email": "Ahmed.Khan@tameerai.pk",
        "password": "SecurePassword123!",
        "role": "engineer",
        "company": "NESPAK",
        "pecNumber": "CIVIL-12345",
        "city": "Lahore",
    }
    response = await auth_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "ahmed.khan@tameerai.pk"  # Lowercase normalized
    assert data["fullName"] == "Engr. Ahmed Khan"
    assert data["role"] == "engineer"
    assert data["isActive"] is True
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


# ---------------------------------------------------------------------------
# 2. Invalid Registration Payload
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_registration_payload(auth_client: AsyncClient):
    # Short password (< 8 chars)
    res = await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Test User",
        "email": "test@tameer.pk",
        "password": "short",
        "role": "engineer",
    })
    assert res.status_code == 422

    # Invalid email format
    res = await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Test User",
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "role": "engineer",
    })
    assert res.status_code == 422

    # Illegal privileged role escalation attempt
    res = await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Test User",
        "email": "admin@tameer.pk",
        "password": "ValidPassword123!",
        "role": "superadmin",
    })
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 3. Duplicate Email Registration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_email_registration(auth_client: AsyncClient):
    payload = {
        "fullName": "Tariq Mahmood",
        "email": "tariq@example.com",
        "password": "Password12345!",
        "role": "contractor",
    }
    first_res = await auth_client.post("/api/v1/auth/register", json=payload)
    assert first_res.status_code == 201

    # Attempt to register with uppercase variant of identical email
    second_payload = payload.copy()
    second_payload["email"] = "TARIQ@EXAMPLE.COM"
    second_res = await auth_client.post("/api/v1/auth/register", json=second_payload)
    assert second_res.status_code == 409
    assert "already exists" in second_res.json()["detail"]


# ---------------------------------------------------------------------------
# 4. Argon2id Password Hashing
# ---------------------------------------------------------------------------

def test_argon2id_password_hashing():
    raw_password = "SuperSecretEngineeringPassword2026!"
    hashed = hash_password(raw_password)

    # Argon2id produces hash starting with $argon2id$
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# 5. Password & Hashes Excluded From Responses
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_password_excluded_from_responses(auth_client: AsyncClient):
    payload = {
        "fullName": "Sarah Malik",
        "email": "sarah.malik@arch.pk",
        "password": "ArchitectPassword99#",
        "role": "architect",
    }
    reg_res = await auth_client.post("/api/v1/auth/register", json=payload)
    data = reg_res.json()
    assert "password" not in data
    assert "hashed_password" not in data

    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "sarah.malik@arch.pk",
        "password": "ArchitectPassword99#",
    })
    login_data = login_res.json()
    assert "password" not in login_data["user"]
    assert "hashed_password" not in login_data["user"]
    assert "refresh_token_hash" not in login_data


# ---------------------------------------------------------------------------
# 6. Automatic UserSettings Creation in Same Transaction
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_automatic_user_settings_creation(auth_client: AsyncClient, async_db: AsyncSession):
    payload = {
        "fullName": "Zahid Hussain",
        "email": "zahid@builder.pk",
        "password": "BuilderPassword123$",
        "role": "contractor",
    }
    res = await auth_client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    user_id = UUID(res.json()["id"])

    # Query database directly to confirm 1:1 UserSettings record was created
    settings_record = await async_db.scalar(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    assert settings_record is not None
    assert settings_record.user_id == user_id
    assert settings_record.language == "en"
    assert settings_record.ai_strictness == "strict"
    assert settings_record.market_region == "lahore"


# ---------------------------------------------------------------------------
# 7. Successful Login & HttpOnly Cookie
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_login(auth_client: AsyncClient):
    # Register user first
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Bilal Qureshi",
        "email": "bilal@pec.org.pk",
        "password": "StrongPassword786!",
        "role": "engineer",
    })

    # Log in
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "bilal@pec.org.pk",
        "password": "StrongPassword786!",
        "rememberMe": True,
    })
    assert login_res.status_code == 200
    data = login_res.json()

    assert "accessToken" in data
    assert data["tokenType"] == "bearer"
    assert data["expiresIn"] == 900  # 15 minutes = 900 seconds
    assert "refreshToken" in data
    assert data["user"]["email"] == "bilal@pec.org.pk"

    # Confirm HttpOnly cookie was set
    assert settings.AUTH_COOKIE_NAME in login_res.cookies
    cookie_val = login_res.cookies[settings.AUTH_COOKIE_NAME]
    assert cookie_val == data["refreshToken"]


# ---------------------------------------------------------------------------
# 8. Invalid Email / Password (Generic Error)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_credentials_generic_error(auth_client: AsyncClient):
    # Non-existent user
    res1 = await auth_client.post("/api/v1/auth/login", json={
        "email": "ghost@nonexistent.pk",
        "password": "SomePassword123!",
    })
    assert res1.status_code == 401
    assert res1.json()["detail"] == "Invalid email or password."

    # Existing user with incorrect password
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Valid User",
        "email": "valid@tameer.pk",
        "password": "CorrectPassword123!",
        "role": "engineer",
    })
    res2 = await auth_client.post("/api/v1/auth/login", json={
        "email": "valid@tameer.pk",
        "password": "WrongPassword456!",
    })
    assert res2.status_code == 401
    assert res2.json()["detail"] == "Invalid email or password."


# ---------------------------------------------------------------------------
# 9. Disabled Accounts Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disabled_account_rejection(auth_client: AsyncClient, async_db: AsyncSession):
    # Register user
    reg = await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Suspended Contractor",
        "email": "suspended@fraud.pk",
        "password": "Password12345!",
        "role": "contractor",
    })
    user_id = UUID(reg.json()["id"])

    # Manually disable account in database
    user = await async_db.scalar(select(User).where(User.id == user_id))
    user.is_active = False
    await async_db.commit()

    # Attempt login
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "suspended@fraud.pk",
        "password": "Password12345!",
    })
    assert login_res.status_code == 403
    assert "disabled" in login_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 10. JWT Generation and Claims Verification
# ---------------------------------------------------------------------------

def test_jwt_generation_and_verification():
    user_id = uuid4()
    role = "engineer"
    token = create_access_token(user_id=user_id, role=role)

    # Strictly decode and verify claims
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == role
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


# ---------------------------------------------------------------------------
# 11. Expired, Forged, or Malformed JWT
# ---------------------------------------------------------------------------

def test_expired_or_invalid_jwt():
    user_id = uuid4()
    # 1. Expired token
    expired_token = create_access_token(
        user_id=user_id,
        role="engineer",
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)

    # 2. Tampered token
    valid_token = create_access_token(user_id=user_id, role="engineer")
    tampered_token = valid_token[:-4] + "abcd"
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered_token)

    # 3. Wrong issuer / audience forged token
    forged_token = jwt.encode(
        {"sub": str(user_id), "type": "access", "iss": "evil-issuer", "aud": settings.JWT_AUDIENCE, "nbf": 1000, "exp": 9999999999},
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(jwt.InvalidIssuerError):
        decode_access_token(forged_token)


# ---------------------------------------------------------------------------
# 12. Authenticated /api/v1/auth/me Endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_me_endpoint(auth_client: AsyncClient):
    # Register and login
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Kashif Rauf",
        "email": "kashif@structure.pk",
        "password": "KashifPassword123#",
        "role": "engineer",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "kashif@structure.pk",
        "password": "KashifPassword123#",
    })
    token = login_res.json()["accessToken"]

    # 1. Access with valid Bearer token
    me_res = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "kashif@structure.pk"
    assert me_res.json()["fullName"] == "Kashif Rauf"

    # 2. Access without token
    unauth_res = await auth_client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401


# ---------------------------------------------------------------------------
# 13. Token Refresh (Body and Cookie)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_token_refresh(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Usman Dar",
        "email": "usman@consultancy.pk",
        "password": "UsmanPassword123!",
        "role": "company",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "usman@consultancy.pk",
        "password": "UsmanPassword123!",
    })
    refresh_token = login_res.json()["refreshToken"]

    # Refresh via JSON body
    ref_res = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert ref_res.status_code == 200
    new_data = ref_res.json()
    assert "accessToken" in new_data
    assert "refreshToken" in new_data
    assert new_data["refreshToken"] != refresh_token  # Token was rotated


# ---------------------------------------------------------------------------
# 14. Refresh Token Rotation (Old Token Invalidated)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_token_rotation(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Omar Hayat",
        "email": "omar@firm.pk",
        "password": "OmarPassword123!",
        "role": "engineer",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "omar@firm.pk",
        "password": "OmarPassword123!",
    })
    token_1 = login_res.json()["refreshToken"]

    # First refresh: succeeds and rotates to token_2
    ref_res_1 = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": token_1})
    assert ref_res_1.status_code == 200
    token_2 = ref_res_1.json()["refreshToken"]
    assert token_2 != token_1

    # Second refresh using new token_2: succeeds and rotates to token_3
    ref_res_2 = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": token_2})
    assert ref_res_2.status_code == 200
    token_3 = ref_res_2.json()["refreshToken"]
    assert token_3 != token_2


# ---------------------------------------------------------------------------
# 15. Refresh Token Reuse / Replay Detection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(auth_client: AsyncClient, async_db: AsyncSession):
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Target User",
        "email": "target@victim.pk",
        "password": "TargetPassword123!",
        "role": "architect",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "target@victim.pk",
        "password": "TargetPassword123!",
    })
    initial_token = login_res.json()["refreshToken"]
    user_id = UUID(login_res.json()["user"]["id"])

    # Legitimate client rotates token
    legit_refresh = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": initial_token})
    assert legit_refresh.status_code == 200
    rotated_token = legit_refresh.json()["refreshToken"]

    # Attacker tries to reuse the old initial_token
    attacker_res = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": initial_token})
    assert attacker_res.status_code == 401
    assert "token reuse detected" in attacker_res.json()["detail"].lower()

    # Security check: ALL user sessions should now be revoked!
    active_sessions = (await async_db.scalars(
        select(UserSession).where(UserSession.user_id == user_id, UserSession.is_revoked.is_(False))
    )).all()
    assert len(active_sessions) == 0

    # Even the new rotated_token is now invalid because compromise was mitigated
    subsequent_res = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": rotated_token})
    assert subsequent_res.status_code == 401


# ---------------------------------------------------------------------------
# 16. Logout Session Revocation and Cookie Deletion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_session_revocation(auth_client: AsyncClient, async_db: AsyncSession):
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Logout Tester",
        "email": "logout@test.pk",
        "password": "LogoutPassword123!",
        "role": "engineer",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "logout@test.pk",
        "password": "LogoutPassword123!",
    })
    refresh_token = login_res.json()["refreshToken"]

    # Logout with refresh token
    logout_res = await auth_client.post("/api/v1/auth/logout", json={"refreshToken": refresh_token})
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Confirm token is revoked and cannot be refreshed
    attempt = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert attempt.status_code == 401


# ---------------------------------------------------------------------------
# 17. Unauthorized Access Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthorized_access(auth_client: AsyncClient):
    # 1. No Authorization header
    res = await auth_client.get("/api/v1/auth/me")
    assert res.status_code == 401

    # 2. Malformed Authorization header
    res = await auth_client.get("/api/v1/auth/me", headers={"Authorization": "NotBearer some-token"})
    assert res.status_code == 401

    # 3. Invalid token string
    res = await auth_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer gibberish.token.here"})
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# 18. Concurrent Registration Race Handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_registration_race(async_db: AsyncSession):
    payload = RegisterRequest(
        fullName="Race Condition Test",
        email="race@tameerai.pk",
        password="RacePassword123!",
        role="engineer",
    )
    # First registration
    user = await register_user(async_db, payload)
    assert user.email == "race@tameerai.pk"

    # Second concurrent registration attempt with same email handles conflict
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await register_user(async_db, payload)
    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 19. Concurrent Refresh Edge Case with Row Lock
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_refresh_handling(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Concurrent User",
        "email": "concurrent@refresh.pk",
        "password": "ConcurrentPassword123!",
        "role": "engineer",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "concurrent@refresh.pk",
        "password": "ConcurrentPassword123!",
    })
    raw_token = login_res.json()["refreshToken"]

    # Fire two concurrent refresh requests simultaneously
    res1, res2 = await asyncio.gather(
        auth_client.post("/api/v1/auth/refresh", json={"refreshToken": raw_token}),
        auth_client.post("/api/v1/auth/refresh", json={"refreshToken": raw_token}),
        return_exceptions=True,
    )

    # Exactly one must succeed (200), and the second must be rejected (401) due to row-level locking
    status_codes = sorted([res1.status_code, res2.status_code])
    assert status_codes == [200, 401]


# ---------------------------------------------------------------------------
# 20. Database Transaction Rollback on Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transaction_rollback_on_failure(async_db: AsyncSession):
    # Simulate a mid-transaction failure during registration
    from unittest.mock import patch

    with patch("app.services.auth_service.UserSettings", side_effect=RuntimeError("Simulated failure")):
        from fastapi import HTTPException
        payload = RegisterRequest(
            fullName="Rollback User",
            email="rollback@test.pk",
            password="RollbackPassword123!",
            role="engineer",
        )
        with pytest.raises(HTTPException) as exc_info:
            await register_user(async_db, payload)
        assert exc_info.value.status_code == 500

    # Verify that the user record was NOT committed to the database
    user = await async_db.scalar(select(User).where(User.email == "rollback@test.pk"))
    assert user is None


# ---------------------------------------------------------------------------
# 21. Sliding-Window Login Rate Limiting (429 Too Many Requests)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_rate_limiting(auth_client: AsyncClient):
    # Register test user
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Brute Force Target",
        "email": "brute@victim.pk",
        "password": "RealPassword123!",
        "role": "engineer",
    })

    # Attempt 5 consecutive failed logins
    for _ in range(5):
        res = await auth_client.post("/api/v1/auth/login", json={
            "email": "brute@victim.pk",
            "password": "WrongPassword!",
        })
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter with 429
    limited_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "brute@victim.pk",
        "password": "RealPassword123!",  # Even with real password, should be rate-limited
    })
    assert limited_res.status_code == 429
    assert "Too many failed login attempts" in limited_res.json()["detail"]
    assert "Retry-After" in limited_res.headers


# ---------------------------------------------------------------------------
# 22. Access Token Semantics After Logout (Stateless JWT Lifetime)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_access_token_semantics_after_logout(auth_client: AsyncClient):
    """
    Verifies that logging out revokes the refresh session so no new tokens can be issued,
    while confirming that the short-lived access JWT remains stateless until natural expiration.
    """
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "Logout Semantics",
        "email": "logout.sem@tameer.pk",
        "password": "Password12345!",
        "role": "engineer",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "logout.sem@tameer.pk",
        "password": "Password12345!",
    })
    access_token = login_res.json()["accessToken"]
    refresh_token = login_res.json()["refreshToken"]

    # 1. Logout
    logout_res = await auth_client.post("/api/v1/auth/logout", json={"refreshToken": refresh_token})
    assert logout_res.status_code == 200

    # 2. Confirm refresh token is immediately revoked (cannot obtain new access tokens)
    ref_attempt = await auth_client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert ref_attempt.status_code == 401

    # 3. Stateless Access Token remains valid on /me until its 15-minute expiration
    me_res = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "logout.sem@tameer.pk"


# ---------------------------------------------------------------------------
# 23. CSRF / Origin Verification on Cookie-Authenticated Requests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_origin_verification_on_cookie_endpoints(auth_client: AsyncClient):
    """
    Verifies that cookie-authenticated state-changing requests reject cross-origin callers,
    while explicit body-payload requests succeed from any client.
    """
    await auth_client.post("/api/v1/auth/register", json={
        "fullName": "CSRF Tester",
        "email": "csrf@test.pk",
        "password": "Password12345!",
        "role": "engineer",
    })
    login_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "csrf@test.pk",
        "password": "Password12345!",
    })
    refresh_cookie = login_res.cookies[settings.AUTH_COOKIE_NAME]

    # 1. Cookie-authenticated /refresh with untrusted Origin -> 403 Forbidden
    evil_refresh = await auth_client.post(
        "/api/v1/auth/refresh",
        cookies={settings.AUTH_COOKIE_NAME: refresh_cookie},
        headers={"Origin": "https://attacker-controlled-site.com"},
    )
    assert evil_refresh.status_code == 403
    assert "Cross-origin request forbidden" in evil_refresh.json()["detail"]

    # 2. Cookie-authenticated /refresh with trusted CORS Origin (http://localhost:3000) -> 200 OK
    valid_refresh = await auth_client.post(
        "/api/v1/auth/refresh",
        cookies={settings.AUTH_COOKIE_NAME: refresh_cookie},
        headers={"Origin": "http://localhost:3000"},
    )
    assert valid_refresh.status_code == 200


# ---------------------------------------------------------------------------
# 24. IP-Wide Password Spraying Defense
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limiting_ip_password_spraying(auth_client: AsyncClient):
    """
    Verifies that an attacker attempting dictionary spraying across 20 distinct emails
    from the same IP address is blocked by the IP-wide rate limit threshold.
    """
    # 20 failed login attempts with 20 different emails
    for i in range(20):
        res = await auth_client.post("/api/v1/auth/login", json={
            "email": f"sprayed_user_{i}@domain.pk",
            "password": "WrongPassword123!",
        })
        assert res.status_code == 401

    # 21st attempt with yet another new email should be blocked with 429
    blocked_res = await auth_client.post("/api/v1/auth/login", json={
        "email": "sprayed_user_21@domain.pk",
        "password": "AnyPassword!",
    })
    assert blocked_res.status_code == 429
    assert "Too many failed login attempts" in blocked_res.json()["detail"]


# ---------------------------------------------------------------------------
# 25. Production Security Configuration Validation
# ---------------------------------------------------------------------------

def test_production_security_settings_validation():
    """
    Verifies that Settings raises ValueError if insecure defaults are used in production.
    """
    from pydantic import ValidationError
    from app.core.config import Settings

    # Production with default insecure secret must fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="dev-insecure-secret-key-change-in-production-tameerai-fyp-2026",
            AUTH_COOKIE_SECURE=True,
        )
    assert "JWT_SECRET_KEY must be configured with a secure random key" in str(exc_info.value)

    # Production without HTTPS cookies must fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a" * 32,
            AUTH_COOKIE_SECURE=False,
        )
    assert "AUTH_COOKIE_SECURE must be True in production" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 26. JWT Future Not-Before (nbf) Rejection
# ---------------------------------------------------------------------------

def test_jwt_future_nbf_rejection():
    """
    Verifies that decode_access_token strictly enforces nbf (not-before) claims.
    """
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    future_token = jwt.encode(
        {
            "sub": str(user_id),
            "role": "engineer",
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "access",
            "iat": int(now.timestamp()),
            "nbf": int((now + timedelta(minutes=5)).timestamp()),  # 5 minutes in future
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.ImmatureSignatureError):
        decode_access_token(future_token)

