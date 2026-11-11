"""
TameerAI - Project Workspace & Collaboration Endpoints (Phase 02C)

Exposes:
- POST /api/v1/projects: Create new project workspace
- GET /api/v1/projects: List accessible projects (owned + collaborative memberships)
- GET /api/v1/projects/{project_id}: Get workspace details
- PATCH /api/v1/projects/{project_id}: Update project metadata
- DELETE /api/v1/projects/{project_id}: Protected deletion handler (rejects cascading data loss)
- GET /api/v1/projects/{project_id}/members: List collaborative team members
- POST /api/v1/projects/{project_id}/members: Invite/add new team member
- PATCH /api/v1/projects/{project_id}/members/{member_id}: Update member role
- DELETE /api/v1/projects/{project_id}/members/{member_id}: Remove member
- GET /api/v1/projects/{project_id}/activities: List project activity audit trail
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectActivityRead,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import (
    add_project_member,
    create_project,
    get_project_by_identifier,
    get_user_project_role,
    list_project_activities,
    list_project_members,
    list_user_projects,
    remove_project_member,
    update_project,
    update_project_member,
)

logger = logging.getLogger("tameerai.api.projects")

router = APIRouter()


# ---------------------------------------------------------------------------
# Authorization Dependencies
# ---------------------------------------------------------------------------

async def get_project_with_view_access(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Project, str]:
    """
    Validates that current_user has view access to the project workspace.
    Resolves project by internal UUID or public code (e.g. PRJ-001).
    Returns (project, role).
    Raises 404 on nonexistent or unauthorized project to prevent project enumeration.
    """
    project = await get_project_by_identifier(db, project_id, user_id=current_user.id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    user_role = await get_user_project_role(db, project, current_user.id)
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project, user_role


async def get_project_with_edit_access(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> Tuple[Project, str]:
    """
    Validates that current_user has edit access (owner or lead_engineer).
    Raises 403 Forbidden for view-only members or lower roles.
    """
    project, user_role = project_data
    if user_role not in {"owner", "lead_engineer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit project workspace.",
        )
    return project, user_role


async def get_project_with_member_manage_access(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> Tuple[Project, str]:
    """
    Validates that current_user has member management privileges (owner or lead_engineer).
    """
    project, user_role = project_data
    if user_role not in {"owner", "lead_engineer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage project members.",
        )
    return project, user_role


async def get_project_with_delete_access(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> Tuple[Project, str]:
    """
    Validates that current_user is the workspace owner.
    """
    project, user_role = project_data
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can request project deletion.",
        )
    return project, user_role


# ---------------------------------------------------------------------------
# Project CRUD Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project workspace",
    description="Creates a project workspace owned by the authenticated user with a safe sequential public code (e.g. PRJ-001).",
)
async def create_new_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    project = await create_project(
        db=db,
        user=current_user,
        payload=payload,
    )
    return ProjectRead.model_validate(project)


@router.get(
    "",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List accessible project workspaces",
    description="Returns a paginated list of project workspaces the authenticated user owns or participates in.",
)
async def list_projects(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="Items per page"),
    city: Optional[str] = Query(default=None, description="Filter by jurisdictional city"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    search: Optional[str] = Query(default=None, description="Search by name, code, or location"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    projects, total = await list_user_projects(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        city=city,
        status_filter=status,
        search=search,
    )
    items = [ProjectRead.model_validate(p) for p in projects]
    has_more = (page * page_size) < total

    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        pageSize=page_size,
        hasMore=has_more,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Get project workspace details",
    description="Retrieves full project details for authorized owners or team members.",
)
async def get_project(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> ProjectRead:
    project, _ = project_data
    return ProjectRead.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Update project workspace metadata",
    description="Updates editable project fields with financial precision and activity logging. Requires Owner or Lead Engineer privileges.",
)
@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Update project workspace metadata (PUT/PATCH compatibility)",
    description="Updates editable project fields with financial precision and activity logging. Requires Owner or Lead Engineer privileges.",
)
async def update_project_endpoint(
    payload: ProjectUpdate,
    project_data: Tuple[Project, str] = Depends(get_project_with_edit_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    project, _ = project_data
    updated = await update_project(
        db=db,
        project=project,
        user=current_user,
        payload=payload,
    )
    return ProjectRead.model_validate(updated)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete project workspace (Protected)",
    description="Raw cascading deletion is restricted to protect associated engineering intelligence, audits, and legal documents. Soft-delete archival schema is pending authorization.",
)
async def delete_project(
    project_data: Tuple[Project, str] = Depends(get_project_with_delete_access),
):
    # Enforces Task 8 safety: cascading deletion is rejected to protect intelligence records.
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Cascading project deletion is restricted to protect associated engineering intelligence, audits, and legal documents. Soft-delete archival schema is pending authorization.",
    )


# ---------------------------------------------------------------------------
# Project Membership Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}/members",
    response_model=List[ProjectMemberRead],
    status_code=status.HTTP_200_OK,
    summary="List project team members",
    description="Returns all collaborative team members assigned to the project workspace.",
)
async def list_members(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
) -> List[ProjectMemberRead]:
    project, _ = project_data
    members = await list_project_members(db, project)
    return [ProjectMemberRead.model_validate(m) for m in members]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a collaborator to project workspace",
    description="Assigns a collaborative role (lead_engineer, architect, contractor, viewer) to a user in this workspace. Requires Owner or Lead Engineer role.",
)
async def add_member(
    payload: ProjectMemberCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_member_manage_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberRead:
    project, actor_role = project_data
    new_member = await add_project_member(
        db=db,
        project=project,
        actor_user=current_user,
        actor_role=actor_role,
        payload=payload,
    )
    return ProjectMemberRead.model_validate(new_member)


@router.patch(
    "/{project_id}/members/{member_id}",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_200_OK,
    summary="Update project member role",
    description="Updates the collaborative role of an existing team member with role hierarchy checks.",
)
async def update_member(
    member_id: UUID,
    payload: ProjectMemberUpdate,
    project_data: Tuple[Project, str] = Depends(get_project_with_member_manage_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberRead:
    project, actor_role = project_data
    updated_member = await update_project_member(
        db=db,
        project=project,
        actor_user=current_user,
        actor_role=actor_role,
        member_id=member_id,
        payload=payload,
    )
    return ProjectMemberRead.model_validate(updated_member)


@router.delete(
    "/{project_id}/members/{member_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove collaborator from project workspace",
    description="Removes a collaborative member from the workspace with role capability checks.",
)
async def remove_member(
    member_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_member_manage_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    project, actor_role = project_data
    await remove_project_member(
        db=db,
        project=project,
        actor_user=current_user,
        actor_role=actor_role,
        member_id=member_id,
    )
    return {"message": "Collaborator removed successfully.", "success": True}


# ---------------------------------------------------------------------------
# Project Activity Audit Trail Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}/activities",
    response_model=List[ProjectActivityRead],
    status_code=status.HTTP_200_OK,
    summary="List project activity audit trail",
    description="Returns chronological event log entries for actions performed in the workspace.",
)
async def list_activities(
    limit: int = Query(default=50, ge=1, le=100, description="Max activities to return"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
) -> List[ProjectActivityRead]:
    project, _ = project_data
    activities = await list_project_activities(db, project, limit=limit)
    return [ProjectActivityRead.model_validate(a) for a in activities]

