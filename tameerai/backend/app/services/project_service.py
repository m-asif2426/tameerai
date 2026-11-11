"""
TameerAI - Project Workspace & Membership Service Layer (Phase 02C)

Implements business logic for:
- Safe transactional public code generation (PRJ-001) with row locking on owner
- Project workspace CRUD with strict mass-assignment protection
- Project role-based access control (RBAC) and membership management
- Exact financial precision (raw PKR Numeric and dynamic Crore conversions)
- Project activity audit logging
- Safe project deletion controls protecting cascading engineering intelligence
"""

import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.identifiers import format_project_code, is_valid_project_code
from app.models.project import Project, ProjectActivity, ProjectMember
from app.models.user import User
from app.schemas.project import (
    ALLOWED_MEMBER_ROLES,
    ALLOWED_RISKS,
    ALLOWED_STATUSES,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectUpdate,
)

logger = logging.getLogger("tameerai.project_service")

# Role capability hierarchy
# Higher index means strictly higher privileges
ROLE_LEVELS = {
    "viewer": 1,
    "contractor": 2,
    "architect": 3,
    "lead_engineer": 4,
    "owner": 5,
}


async def allocate_project_code(db: AsyncSession, user_id: UUID) -> str:
    """
    Safely allocates the next public code (e.g. PRJ-001, PRJ-002) for the given owner.
    Locks the owner's user row with with_for_update() to prevent race conditions
    under concurrent project creation requests. Uniqueness is scoped per owner
    (UNIQUE (user_id, code)).
    """
    # 1. Lock the user's row exclusively for the duration of this transaction
    await db.execute(
        select(User.id).where(User.id == user_id).with_for_update()
    )

    # 2. Query all existing codes for this user
    result = await db.execute(
        select(Project.code).where(Project.user_id == user_id)
    )
    existing_codes = result.scalars().all()

    # 3. Find highest numeric suffix among existing PRJ-XXX codes
    max_num = 0
    pattern = re.compile(r"^PRJ-(\d+)$")
    for code in existing_codes:
        match = pattern.match(code.strip())
        if match:
            try:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    next_num = max_num + 1
    return format_project_code(next_num, prefix="PRJ")


async def create_project(
    db: AsyncSession,
    user: User,
    payload: ProjectCreate,
) -> Project:
    """
    Creates a new project workspace owned by the current authenticated user.
    Serializes concurrent project creations by taking an exclusive row lock on the user record.
    Allocates a safe sequential public code if omitted.
    """
    # 1. Exclusively lock the owner's user row to serialize concurrent creations for this owner
    await db.execute(
        select(User.id).where(User.id == user.id).with_for_update()
    )

    if payload.code is not None:
        clean_code = payload.code.strip()
        if not is_valid_project_code(clean_code):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid project code format '{payload.code}'. Expected format like 'PRJ-001'.",
            )
        # Check uniqueness under this user
        existing = await db.scalar(
            select(Project.id).where(
                Project.user_id == user.id,
                Project.code == clean_code,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with code '{clean_code}' already exists in your workspace.",
            )
        project_code = clean_code
    else:
        project_code = await allocate_project_code(db, user.id)

    # Calculate authoritative raw PKR budget
    authoritative_budget_raw = payload.get_authoritative_budget_raw()
    if authoritative_budget_raw < Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Budget amount cannot be negative.",
        )

    project = Project(
        code=project_code,
        user_id=user.id,
        name=payload.name,
        name_urdu=payload.name_urdu,
        description=payload.description,
        location=payload.location,
        location_urdu=payload.location_urdu,
        city=payload.city,
        city_urdu=payload.city_urdu,
        type=payload.type,
        type_urdu=payload.type_urdu,
        budget_raw=authoritative_budget_raw,
        spent_raw=Decimal("0.00"),
        status=payload.status or "Planning",
        status_urdu=payload.status_urdu or "منصوبہ بندی (Planning)",
        risk=payload.risk or "Low",
        risk_urdu=payload.risk_urdu or "کم (Low)",
        floors=payload.floors,
        area_sqft=payload.area_sqft,
        engineer=payload.engineer,
        governing_authority=payload.governing_authority,
        start_date=payload.start_date,
        expected_completion_date=payload.expected_completion_date,
        handover_date=payload.handover_date,
    )
    db.add(project)

    # Activity logging
    activity = ProjectActivity(
        project_id=project.id,
        user_id=user.id,
        actor_name=user.full_name,
        action="Project workspace created",
        action_urdu="پروجیکٹ ورک اسپیس تشکیل دی گئی",
        activity_type="general",
        metadata_json={
            "code": project.code,
            "city": project.city,
            "type": project.type,
            "budgetRaw": str(project.budget_raw),
        },
    )
    db.add(activity)

    try:
        await db.commit()
        await db.refresh(project)
        logger.info("Project created successfully: %s (code=%s, owner=%s)", project.id, project.code, user.id)
        return project
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("Uniqueness conflict creating project for user %s: %s", user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project code '{project_code}' conflict. Please retry.",
        ) from None
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to create project: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project workspace due to an internal error.",
        ) from None


async def get_project_by_identifier(
    db: AsyncSession,
    identifier: str,
    user_id: UUID,
) -> Optional[Project]:
    """
    Looks up a project by internal UUID or public code (e.g. PRJ-001)
    strictly within the user's authorized project set (as owner or member).
    
    Guarantees strict tenant isolation and ambiguity detection:
    1. If identifier is a UUID, enforces authorization by verifying the user
       is either the owner or an active collaborative member.
    2. If identifier is a public code (e.g. PRJ-001):
       - If 0 accessible projects match: returns None (caller raises 404).
       - If exactly 1 accessible project matches: returns that project.
       - If multiple accessible projects match (e.g. user is a collaborator on
         multiple workspaces that share the same owner-scoped code):
         raises HTTP 409 Conflict demanding the caller reference the unique UUID.
    Never chooses an arbitrary match (.first()) and never leaks unauthorized projects.
    """
    clean_id = identifier.strip()
    try:
        uuid_val = UUID(clean_id)
        # Directly enforce access authorization on UUID lookups
        membership_subquery = (
            select(ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
        )
        stmt = select(Project).where(
            Project.id == uuid_val,
            or_(
                Project.user_id == user_id,
                Project.id.in_(membership_subquery),
            ),
        )
        return await db.scalar(stmt)
    except (ValueError, TypeError):
        # Query by public code scoped strictly to accessible projects (owner or member)
        membership_subquery = (
            select(ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
        )
        stmt = select(Project).where(
            Project.code == clean_id,
            or_(
                Project.user_id == user_id,
                Project.id.in_(membership_subquery),
            ),
        )
        result = await db.execute(stmt)
        accessible_projects = list(result.scalars().all())

        if not accessible_projects:
            return None

        if len(accessible_projects) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Ambiguous project code '{clean_id}'. Multiple accessible projects match this code. "
                    "Please reference the project using its unique UUID."
                ),
            )

        return accessible_projects[0]


async def _get_project_unscoped_admin(
    db: AsyncSession,
    project_id: UUID,
) -> Optional[Project]:
    """
    Private administrative resolver for unscoped lookup by internal UUID only.
    Strictly forbidden in public tenant routes.
    """
    return await db.scalar(select(Project).where(Project.id == project_id))


async def get_user_project_role(
    db: AsyncSession,
    project: Project,
    user_id: UUID,
) -> Optional[str]:
    """
    Resolves the user's role in the specified project.
    Returns: 'owner', 'lead_engineer', 'architect', 'contractor', 'viewer', or None.
    """
    if project.user_id == user_id:
        return "owner"

    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
        )
    )
    if member is not None:
        return member.role
    return None


async def list_user_projects(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    city: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[Project], int]:
    """
    Lists projects the user has access to (either as owner or as project member).
    Supports pagination, filtering, and search.
    """
    # Base accessibility condition: owner OR member
    membership_subquery = (
        select(ProjectMember.project_id)
        .where(ProjectMember.user_id == user_id)
    )
    access_filter = or_(
        Project.user_id == user_id,
        Project.id.in_(membership_subquery),
    )

    conditions = [access_filter]

    if city:
        conditions.append(Project.city.ilike(city.strip()))
    if status_filter:
        conditions.append(Project.status == status_filter.strip())
    if search:
        search_term = f"%{search.strip()}%"
        conditions.append(
            or_(
                Project.name.ilike(search_term),
                Project.code.ilike(search_term),
                Project.location.ilike(search_term),
            )
        )

    # Count query
    count_stmt = select(func.count(Project.id)).where(*conditions)
    total = (await db.scalar(count_stmt)) or 0

    # Paginated select query with deterministic ordering
    stmt = (
        select(Project)
        .where(*conditions)
        .order_by(Project.created_at.desc(), Project.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    return projects, total


async def update_project(
    db: AsyncSession,
    project: Project,
    user: User,
    payload: ProjectUpdate,
) -> Project:
    """
    Updates editable project fields with financial validation and activity logging.
    """
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return project

    # Handle financial updates with precision
    if "budget_raw" in update_data and update_data["budget_raw"] is not None:
        raw_val = Decimal(str(update_data["budget_raw"])).quantize(Decimal("0.01"))
        if raw_val < Decimal("0.00"):
            raise HTTPException(status_code=422, detail="budgetRaw cannot be negative.")
        project.budget_raw = raw_val
    elif "budget_crore" in update_data and update_data["budget_crore"] is not None:
        crore_val = Decimal(str(update_data["budget_crore"]))
        if crore_val < Decimal("0.00"):
            raise HTTPException(status_code=422, detail="budgetCrore cannot be negative.")
        project.budget_raw = (crore_val * Decimal("10000000")).quantize(Decimal("0.01"))

    if "spent_raw" in update_data and update_data["spent_raw"] is not None:
        raw_spent = Decimal(str(update_data["spent_raw"])).quantize(Decimal("0.01"))
        if raw_spent < Decimal("0.00"):
            raise HTTPException(status_code=422, detail="spentRaw cannot be negative.")
        project.spent_raw = raw_spent
    elif "spent_crore" in update_data and update_data["spent_crore"] is not None:
        crore_spent = Decimal(str(update_data["spent_crore"]))
        if crore_spent < Decimal("0.00"):
            raise HTTPException(status_code=422, detail="spentCrore cannot be negative.")
        project.spent_raw = (crore_spent * Decimal("10000000")).quantize(Decimal("0.01"))

    # Remove financial keys from direct setattr loop
    for key in ("budget_raw", "budget_crore", "spent_raw", "spent_crore"):
        update_data.pop(key, None)

    # Apply remaining attributes
    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)

    # Log activity
    changed_keys = list(payload.model_dump(exclude_unset=True).keys())
    activity = ProjectActivity(
        project_id=project.id,
        user_id=user.id,
        actor_name=user.full_name,
        action=f"Project details updated: {', '.join(changed_keys)}",
        action_urdu="پروجیکٹ کی تفصیلات اپ ڈیٹ کی گئیں",
        activity_type="general",
        metadata_json={"updatedFields": changed_keys},
    )
    db.add(activity)

    try:
        await db.commit()
        await db.refresh(project)
        logger.info("Project %s updated successfully by user %s", project.id, user.id)
        return project
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to update project %s: %s", project.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project details.",
        ) from None


async def list_project_members(
    db: AsyncSession,
    project: Project,
) -> List[ProjectMember]:
    """
    Returns all collaborative members of a project with user metadata loaded.
    """
    stmt = (
        select(ProjectMember)
        .where(ProjectMember.project_id == project.id)
        .options(selectinload(ProjectMember.user))
        .order_by(ProjectMember.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_project_member(
    db: AsyncSession,
    project: Project,
    actor_user: User,
    actor_role: str,
    payload: ProjectMemberCreate,
) -> ProjectMember:
    """
    Adds a collaborative member to the project.
    Validates permissions, role hierarchy, uniqueness, and records activity.
    """
    target_role = payload.role.strip().lower()
    if target_role not in ALLOWED_MEMBER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{target_role}'. Allowed: {', '.join(sorted(ALLOWED_MEMBER_ROLES))}",
        )

    # Role capability hierarchy check:
    # A user cannot grant privileges higher than or equal to their own unless they are the owner.
    actor_level = ROLE_LEVELS.get(actor_role, 0)
    target_level = ROLE_LEVELS.get(target_role, 0)

    if actor_role != "owner" and target_level >= actor_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role escalation forbidden: cannot grant role '{target_role}' which is equal to or higher than your own role ('{actor_role}').",
        )

    # Resolve target user by userId or email
    target_user: Optional[User] = None
    if payload.user_id is not None:
        target_user = await db.scalar(select(User).where(User.id == payload.user_id))
    elif payload.email is not None:
        norm_email = str(payload.email).lower().strip()
        target_user = await db.scalar(select(User).where(User.email == norm_email))

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator user does not exist.",
        )

    # Check 1: Owner cannot be added as a member of their own project
    if target_user.id == project.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The project owner is already the primary workspace administrator and cannot be added as a member.",
        )

    # Check 2: Uniqueness check
    existing_member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == target_user.id,
        )
    )
    if existing_member is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{target_user.full_name}' ({target_user.email}) is already a member of this project.",
        )

    new_member = ProjectMember(
        project_id=project.id,
        user_id=target_user.id,
        role=target_role,
    )
    db.add(new_member)

    # Log activity
    activity = ProjectActivity(
        project_id=project.id,
        user_id=actor_user.id,
        actor_name=actor_user.full_name,
        action=f"Member added: {target_user.full_name} as {target_role}",
        action_urdu=f"ممبر شامل کیا گیا: {target_user.full_name} بطور {target_role}",
        activity_type="general",
        metadata_json={
            "memberUserId": str(target_user.id),
            "memberEmail": target_user.email,
            "role": target_role,
        },
    )
    db.add(activity)

    try:
        await db.commit()
        await db.refresh(new_member)
        # Load user relationship for serialization
        new_member.user = target_user
        logger.info("Added member %s (%s) to project %s with role %s", target_user.id, target_user.email, project.id, target_role)
        return new_member
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership conflict: user is already a member.",
        ) from None
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to add project member: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add member to project.",
        ) from None


async def update_project_member(
    db: AsyncSession,
    project: Project,
    actor_user: User,
    actor_role: str,
    member_id: UUID,
    payload: ProjectMemberUpdate,
) -> ProjectMember:
    """
    Updates the collaborative role of an existing project member.
    """
    member = await db.scalar(
        select(ProjectMember)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project.id,
        )
        .options(selectinload(ProjectMember.user))
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found.",
        )

    # Member cannot self-escalate or modify their own role
    if member.user_id == actor_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-escalation forbidden: members cannot modify their own role.",
        )

    new_role = payload.role.strip().lower()
    actor_level = ROLE_LEVELS.get(actor_role, 0)
    current_target_level = ROLE_LEVELS.get(member.role, 0)
    new_target_level = ROLE_LEVELS.get(new_role, 0)

    # Actor cannot modify a member with equal or higher role unless actor is owner
    if actor_role != "owner" and current_target_level >= actor_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot modify member with equal or higher role ('{member.role}').",
        )

    # Actor cannot promote someone to equal or higher role than actor unless actor is owner
    if actor_role != "owner" and new_target_level >= actor_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot escalate member to role '{new_role}'.",
        )

    old_role = member.role
    member.role = new_role

    # Log activity
    member_name = member.user.full_name if member.user else "Collaborator"
    activity = ProjectActivity(
        project_id=project.id,
        user_id=actor_user.id,
        actor_name=actor_user.full_name,
        action=f"Member role updated: {member_name} from {old_role} to {new_role}",
        action_urdu=f"ممبر کا کردار تبدیل کیا گیا: {member_name}",
        activity_type="general",
        metadata_json={
            "memberUserId": str(member.user_id),
            "oldRole": old_role,
            "newRole": new_role,
        },
    )
    db.add(activity)

    try:
        await db.commit()
        await db.refresh(member)
        logger.info("Updated role for member %s in project %s: %s -> %s", member.id, project.id, old_role, new_role)
        return member
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to update project member %s: %s", member.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project member role.",
        ) from None


async def remove_project_member(
    db: AsyncSession,
    project: Project,
    actor_user: User,
    actor_role: str,
    member_id: UUID,
) -> None:
    """
    Removes a collaborative member from the project.
    """
    member = await db.scalar(
        select(ProjectMember)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project.id,
        )
        .options(selectinload(ProjectMember.user))
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found.",
        )

    # Lead engineer cannot remove themselves via member management endpoint
    if member.user_id == actor_user.id and actor_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove own membership record via member management endpoint.",
        )

    # Project owner cannot be removed as a member
    if member.user_id == project.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner cannot be removed as a member.",
        )

    actor_level = ROLE_LEVELS.get(actor_role, 0)
    target_level = ROLE_LEVELS.get(member.role, 0)

    # Actor cannot remove a member with equal or higher role unless actor is owner
    if actor_role != "owner" and target_level >= actor_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot remove member with equal or higher role ('{member.role}').",
        )

    member_name = member.user.full_name if member.user else "Collaborator"
    member_user_id = member.user_id

    await db.delete(member)

    # Log activity
    activity = ProjectActivity(
        project_id=project.id,
        user_id=actor_user.id,
        actor_name=actor_user.full_name,
        action=f"Member removed: {member_name}",
        action_urdu=f"ممبر کو ہٹا دیا گیا: {member_name}",
        activity_type="general",
        metadata_json={"memberUserId": str(member_user_id)},
    )
    db.add(activity)

    try:
        await db.commit()
        logger.info("Removed member %s from project %s by %s", member_id, project.id, actor_user.id)
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to remove project member %s: %s", member_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove project member.",
        ) from None


async def list_project_activities(
    db: AsyncSession,
    project: Project,
    limit: int = 50,
) -> List[ProjectActivity]:
    """
    Returns recent activity audit trail entries for the project.
    """
    stmt = (
        select(ProjectActivity)
        .where(ProjectActivity.project_id == project.id)
        .order_by(ProjectActivity.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

