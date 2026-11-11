"""
TameerAI - User Profile & Settings Service Layer (Phase 02B)

Implements business logic for:
- Reading and updating authenticated user profile details
- Transaction-safe user settings retrieval with automatic 1:1 default instantiation
- Partial preference updates with strict validation and mass-assignment protection
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserSettings
from app.schemas.user import UserSettingsUpdate, UserUpdate

logger = logging.getLogger("tameerai.user_service")


async def update_user_profile(
    db: AsyncSession,
    user: User,
    payload: UserUpdate,
) -> User:
    """
    Applies partial profile updates to the authenticated user.
    Only approved fields (full_name, company, pec_number, phone, city, bio) are modifiable.
    Sensitive/administrative fields (id, email, role, is_active, is_verified, hashed_password)
    are strictly rejected by Pydantic mass-assignment guards.
    """
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return user

    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(user)
        logger.info("Successfully updated profile for user %s", user.id)
        return user
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to update profile for user %s: %s", user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile due to an internal error.",
        ) from None


async def get_or_create_user_settings(
    db: AsyncSession,
    user_id: UUID,
) -> UserSettings:
    """
    Retrieves the 1:1 UserSettings record for the specified user.
    If the settings record is missing (e.g. legacy/imported user), instantiates
    a default settings row atomically and safely handles uniqueness races.
    """
    settings = await db.scalar(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    if settings is not None:
        return settings

    # Missing row recovery: instantiate standard engineering defaults
    new_settings = UserSettings(
        user_id=user_id,
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

    try:
        await db.commit()
        await db.refresh(new_settings)
        logger.info("Provisioned default UserSettings for user %s", user_id)
        return new_settings
    except IntegrityError:
        # Another concurrent request already created the settings record
        await db.rollback()
        existing = await db.scalar(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        if existing is not None:
            return existing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize user settings.",
        ) from None
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to provision settings for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user settings.",
        ) from None


async def update_user_settings(
    db: AsyncSession,
    user_id: UUID,
    payload: UserSettingsUpdate,
) -> UserSettings:
    """
    Applies partial preference updates to the authenticated user's settings.
    Guarantees that omitted fields retain their existing database values.
    """
    settings = await get_or_create_user_settings(db, user_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return settings

    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(settings)
        logger.info("Successfully updated settings for user %s", user_id)
        return settings
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to update settings for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings.",
        ) from None

