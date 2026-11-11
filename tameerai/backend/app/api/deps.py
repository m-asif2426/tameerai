"""
TameerAI - API Dependency Injection Utilities (Phase 02A)

Provides reusable FastAPI dependencies for:
- Database session management (get_db)
- Authenticated user resolution (get_current_user) via JWT Bearer token
"""

from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# HTTP Bearer scheme with automatic error suppression so we can return custom RFC 6750 responses
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates JWT Bearer access token and resolves the authenticated User model.
    Raises RFC 6750-compliant 401 Unauthorized errors on missing, expired, or forged tokens.
    """
    if auth is None or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth.credentials

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please refresh your session.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"The token has expired\""},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Invalid or malformed token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.scalar(select(User).where(User.id == user_uuid))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


async def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Optional user resolution for public or semi-public endpoints.
    Returns User if valid Bearer token provided; otherwise returns None without throwing 401.
    """
    if auth is None or not auth.credentials:
        return None

    token = auth.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError):
        return None

    user = await db.scalar(select(User).where(User.id == user_uuid))
    if user is None or not user.is_active:
        return None

    return user


