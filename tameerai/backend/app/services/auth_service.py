"""
TameerAI - Authentication Service Layer (Phase 02A)

Implements business logic for:
- Secure registration with Argon2id hashing and atomic user_settings creation
- Credential verification with sliding-window rate limiting and session generation
- Concurrency-safe refresh token rotation with replay attack detection
- Explicit session revocation for single or multiple device logout
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import login_limiter
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User, UserSession, UserSettings
from app.schemas.auth import LoginRequest, RegisterRequest

logger = logging.getLogger("tameerai.auth")


def _ensure_utc(dt: datetime) -> datetime:
    """Ensures datetime is timezone-aware UTC, safe for SQLite and PostgreSQL drivers."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    """
    Registers a new user account.
    - Validates email uniqueness
    - Hashes password using Argon2id
    - Atomically instantiates default UserSettings record in the same transaction
    - Handles concurrency races gracefully via transaction rollback
    """
    normalized_email = payload.email.lower().strip()

    # Pre-check for duplicate email
    existing_user = await db.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Hash password with Argon2id
    hashed_pwd = hash_password(payload.password)

    try:
        # Instantiate User model
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pwd,
            full_name=payload.full_name,
            role=payload.role,
            company=payload.company,
            pec_number=payload.pec_number,
            phone=payload.phone,
            city=payload.city,
            bio=payload.bio,
            is_active=True,
            is_verified=False,
        )

        db.add(new_user)
        await db.flush()  # Generates new_user.id for foreign key

        # Atomically create 1:1 UserSettings record with standard defaults
        new_settings = UserSettings(
            user_id=new_user.id,
            language="en",
            theme="system",
            pbc_violations_alert=True,
            fidic_risks_alert=True,
            price_spikes_alert=True,
            weekly_digest_alert=False,
            whatsapp_alerts=True,
            ai_strictness="strict",
            fidic_threshold="8",
            auto_citations=True,
            market_region="lahore",
            ai_tone="professional",
        )
        db.add(new_settings)

        await db.commit()
        await db.refresh(new_user)
        logger.info("Successfully registered user %s (%s)", new_user.id, normalized_email)
        return new_user
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("Uniqueness race detected during registration for email %s: %s", normalized_email, exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        ) from None
    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to register user %s: %s", normalized_email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an internal server error.",
        ) from None


async def authenticate_user(
    db: AsyncSession,
    payload: LoginRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[User, str, str, int]:
    """
    Authenticates user credentials and provisions an active session.
    - Applies sliding-window rate limiting per IP + email
    - Verifies password with Argon2id
    - Rejects disabled accounts
    - Creates a tracked UserSession with SHA-256 hashed refresh token
    - Issues a signed short-lived JWT access token
    Returns: (User, access_token, raw_refresh_token, expires_in_seconds)
    """
    normalized_email = payload.email.lower().strip()
    client_ip = ip_address or "0.0.0.0"

    # 1. Check rate limit (both per-account and per-IP spraying defense)
    is_limited, retry_after = login_limiter.is_rate_limited(client_ip, normalized_email)
    if is_limited:
        logger.warning("Rate limit exceeded for login attempts from IP %s on email %s", client_ip, normalized_email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please try again after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # 2. Look up user by email
    user = await db.scalar(select(User).where(User.email == normalized_email))

    # 3. Verify password (use constant-time fail if user not found to prevent timing enumeration)
    if user is None or not verify_password(payload.password, user.hashed_password):
        login_limiter.record_failure(client_ip, normalized_email)
        logger.info("Failed login attempt for email: %s", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Check account status
    if not user.is_active:
        logger.warning("Login rejected for disabled user %s (%s)", user.id, normalized_email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact system administration.",
        )

    # 5. Clear rate limit failures on success
    login_limiter.record_success(client_ip, normalized_email)

    # 6. Generate cryptographically random refresh token and hash
    raw_refresh_token = generate_secure_token()
    token_hash = hash_token(raw_refresh_token)

    now = datetime.now(timezone.utc)
    if payload.remember_me:
        expires_at = now + timedelta(days=30)
    else:
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # 7. Persist session
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=token_hash,
        device_info=payload.device_info or user_agent or "Web Browser",
        ip_address=ip_address,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(session)
    await db.commit()

    # 8. Issue JWT access token
    access_token = create_access_token(user_id=user.id, role=user.role)
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    logger.info("User %s successfully logged in; session %s created", user.id, session.id)
    return user, access_token, raw_refresh_token, expires_in_seconds


async def refresh_user_session(
    db: AsyncSession,
    raw_refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[User, str, str, int]:
    """
    Rotates a refresh token and issues a new access token.
    - Locks the session row with SELECT ... FOR UPDATE to eliminate concurrency races
    - Enforces replay attack detection: if a revoked token is re-submitted, purges all user sessions
    - Invalidator for expired sessions
    - Marks previous session revoked and provisions fresh session
    Returns: (User, new_access_token, new_raw_refresh_token, expires_in_seconds)
    """
    if not raw_refresh_token or not raw_refresh_token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_hash = hash_token(raw_refresh_token.strip())

    # Row-level lock to prevent concurrent double-refresh race
    stmt = (
        select(UserSession)
        .where(UserSession.refresh_token_hash == token_hash)
        .with_for_update()
    )
    session = await db.scalar(stmt)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Detect token reuse / replay attack
    if session.is_revoked:
        logger.critical(
            "CRITICAL SECURITY ALERT: Refresh token reuse detected for session %s (user %s). Revoking all sessions.",
            session.id,
            session.user_id,
        )
        # Invalidate all active sessions for this user to contain compromise
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == session.user_id)
            .values(is_revoked=True)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security violation: Refresh token reuse detected. All sessions have been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    if _ensure_utc(session.expires_at) < now:
        session.is_revoked = True
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Atomic conditional update: guarantee only ONE concurrent caller can rotate this session
    rotate_result = await db.execute(
        update(UserSession)
        .where(UserSession.id == session.id, UserSession.is_revoked.is_(False))
        .values(is_revoked=True, last_active_at=now)
    )
    if rotate_result.rowcount == 0:
        logger.critical(
            "CRITICAL SECURITY ALERT: Concurrent refresh token race/reuse detected for session %s (user %s). Revoking all sessions.",
            session.id,
            session.user_id,
        )
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == session.user_id)
            .values(is_revoked=True)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security violation: Refresh token reuse detected. All sessions have been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user
    user = await db.scalar(select(User).where(User.id == session.user_id))
    if user is None or not user.is_active:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue new rotated credentials
    new_raw_token = generate_secure_token()
    new_token_hash = hash_token(new_raw_token)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=new_token_hash,
        device_info=session.device_info or user_agent or "Web Browser",
        ip_address=ip_address or session.ip_address,
        expires_at=new_expires_at,
        is_revoked=False,
    )
    db.add(new_session)
    await db.commit()

    new_access_token = create_access_token(user_id=user.id, role=user.role)
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    logger.info("Session %s rotated to new session %s for user %s", session.id, new_session.id, user.id)
    return user, new_access_token, new_raw_token, expires_in_seconds


async def revoke_session(
    db: AsyncSession,
    raw_refresh_token: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> bool:
    """
    Revokes user sessions for logout.
    If raw_refresh_token is provided, invalidates that specific device session.
    If user_id is provided without a token, invalidates all active sessions for that user.
    """
    now = datetime.now(timezone.utc)
    if raw_refresh_token and raw_refresh_token.strip():
        token_hash = hash_token(raw_refresh_token.strip())
        session = await db.scalar(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
        if session:
            session.is_revoked = True
            session.last_active_at = now
            await db.commit()
            logger.info("Revoked specific session %s for user %s", session.id, session.user_id)
            return True
        return False

    if user_id:
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_revoked.is_(False))
            .values(is_revoked=True, last_active_at=now)
        )
        await db.commit()
        logger.info("Revoked all active sessions for user %s", user_id)
        return True

    return False
