"""
TameerAI - Authentication API Endpoints (Phase 02A)

Exposes:
- POST /api/v1/auth/register: User account creation with automatic 1:1 settings
- POST /api/v1/auth/login: Credential verification, session creation, and dual token issuance
- POST /api/v1/auth/refresh: Concurrency-safe refresh token rotation and session renewal
- POST /api/v1/auth/logout: Session invalidation and cookie clearing
- GET /api/v1/auth/me: Current authenticated user profile identity
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    AuthMessageResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import (
    authenticate_user,
    refresh_user_session,
    register_user,
    revoke_session,
)

logger = logging.getLogger("tameerai.api.auth")

router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str, max_age_days: int = 7) -> None:
    """Configures secure, HttpOnly, SameSite-aware cookie for refresh token transport."""
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age_days * 24 * 3600,
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=f"{settings.API_V1_STR}/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clears the refresh token cookie."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path=f"{settings.API_V1_STR}/auth",
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def _verify_csrf_origin(request: Request) -> None:
    """
    Verifies that cookie-authenticated state-changing requests originate from a trusted Origin.
    Provides defense-in-depth against cross-site request forgery (CSRF).
    """
    origin = request.headers.get("origin")
    if not origin:
        referer = request.headers.get("referer")
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}"

    if origin:
        allowed = set(settings.BACKEND_CORS_ORIGINS)
        # Allow same host if available
        host = request.headers.get("host")
        if host:
            allowed.add(f"http://{host}")
            allowed.add(f"https://{host}")
        allowed.add("http://testserver")

        if origin not in allowed:
            logger.warning("CSRF cross-origin request rejected from origin: %s", origin)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-origin request forbidden.",
            )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers an engineer, contractor, architect, or company account with Argon2id password hashing and automatic default settings.",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await register_user(db=db, payload=payload)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain access/refresh tokens",
    description="Authenticates credentials, records active device session, sets HttpOnly refresh cookie, and returns signed JWT access token.",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, access_token, refresh_token, expires_in = await authenticate_user(
        db=db,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Set secure HttpOnly cookie for web browsers
    cookie_days = 30 if payload.remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
    _set_refresh_cookie(response, refresh_token, max_age_days=cookie_days)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue fresh access token",
    description="Rotates the refresh token (detecting replay attacks) and generates a fresh JWT access token.",
)
async def refresh_token(
    request: Request,
    response: Response,
    payload: Optional[RefreshRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # Accept token either from JSON body or from HttpOnly cookie
    raw_token = None
    if payload and payload.refresh_token:
        raw_token = payload.refresh_token
    elif settings.AUTH_COOKIE_NAME in request.cookies:
        raw_token = request.cookies[settings.AUTH_COOKIE_NAME]
        # Cookie-authenticated state change: enforce trusted Origin check
        _verify_csrf_origin(request)

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token must be provided via request body or cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, new_access_token, new_refresh_token, expires_in = await refresh_user_session(
        db=db,
        raw_refresh_token=raw_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Update HttpOnly cookie with rotated token
    _set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=expires_in,
        refresh_token=new_refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke active session and log out",
    description="Invalidates the provided refresh token session in the database and purges the authentication cookie.",
)
async def logout(
    request: Request,
    response: Response,
    payload: Optional[LogoutRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> AuthMessageResponse:
    raw_token = None
    if payload and payload.refresh_token:
        raw_token = payload.refresh_token
    elif settings.AUTH_COOKIE_NAME in request.cookies:
        raw_token = request.cookies[settings.AUTH_COOKIE_NAME]
        _verify_csrf_origin(request)

    if raw_token:
        await revoke_session(db=db, raw_refresh_token=raw_token)

    _clear_refresh_cookie(response)
    return AuthMessageResponse(message="Successfully logged out.", success=True)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user identity",
    description="Returns the profile and account details of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead.model_validate(current_user)

