"""
TameerAI - User Profile & Settings Endpoints (Phase 02B)

Exposes:
- GET /api/v1/users/me: Read authenticated user profile details
- PATCH /api/v1/users/me: Apply partial profile updates with mass-assignment protection
- GET /api/v1/users/me/settings: Read authenticated user preferences and AI configuration
- PATCH /api/v1/users/me/settings: Apply partial preference updates with strict validation
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import (
    UserRead,
    UserSettingsRead,
    UserSettingsUpdate,
    UserUpdate,
)
from app.services.user_service import (
    get_or_create_user_settings,
    update_user_profile,
    update_user_settings,
)

logger = logging.getLogger("tameerai.api.users")

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns profile details for the currently authenticated user in frontend-compatible camelCase format.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Applies partial updates to the authenticated user profile. Administrative fields (role, email, is_active, is_verified) are strictly forbidden.",
)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    updated_user = await update_user_profile(
        db=db,
        user=current_user,
        payload=payload,
    )
    return UserRead.model_validate(updated_user)


@router.get(
    "/me/settings",
    response_model=UserSettingsRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user settings",
    description="Returns notification preferences, language, theme, and AI configuration for the authenticated user.",
)
async def get_my_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsRead:
    settings = await get_or_create_user_settings(db=db, user_id=current_user.id)
    return UserSettingsRead.model_validate(settings)


@router.patch(
    "/me/settings",
    response_model=UserSettingsRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user settings",
    description="Applies partial preference updates (language, theme, notification alerts, AI parameters) for the authenticated user.",
)
async def update_my_settings(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsRead:
    updated_settings = await update_user_settings(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )
    return UserSettingsRead.model_validate(updated_settings)

