"""
TameerAI - Background Jobs API Endpoints (Phase 02G)

Provides project-scoped endpoints for:
- Enqueuing background jobs (POST)
- Listing and filtering project jobs (GET)
- Retrieving single job details and execution state (GET)
- Cancelling queued, retrying, or running jobs (POST .../cancel)
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.job import (
    BackgroundJobCancel,
    BackgroundJobCreate,
    BackgroundJobRead,
)
from app.services import job_service

router = APIRouter()


@router.post(
    "",
    response_model=BackgroundJobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enqueue Project Background Job",
    description="Enqueues a new background processing job scoped to the project. Requires collaborator access (viewers restricted).",
)
async def enqueue_job(
    project_id: UUID,
    payload: BackgroundJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BackgroundJobRead:
    job = await job_service.enqueue_project_job(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        data=payload,
    )
    return BackgroundJobRead.model_validate(job)


@router.get(
    "",
    response_model=List[BackgroundJobRead],
    status_code=status.HTTP_200_OK,
    summary="List Project Background Jobs",
    description="Retrieves a paginated list of background jobs for this project workspace.",
)
async def list_jobs(
    project_id: UUID,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    job_type_filter: Optional[str] = Query(default=None, alias="jobType"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BackgroundJobRead]:
    jobs = await job_service.list_project_jobs(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        status_filter=status_filter,
        job_type_filter=job_type_filter,
        limit=limit,
        offset=offset,
    )
    return [BackgroundJobRead.model_validate(j) for j in jobs]


@router.get(
    "/{job_id}",
    response_model=BackgroundJobRead,
    status_code=status.HTTP_200_OK,
    summary="Get Background Job Details",
    description="Retrieves status, attempt count, scheduling, and sanitized results for a specific job.",
)
async def get_job(
    project_id: UUID,
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BackgroundJobRead:
    job = await job_service.get_project_job(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        job_id=job_id,
    )
    return BackgroundJobRead.model_validate(job)


@router.post(
    "/{job_id}/cancel",
    response_model=BackgroundJobRead,
    status_code=status.HTTP_200_OK,
    summary="Cancel Background Job",
    description="Requests cancellation of a queued, retrying, or running job. Terminal states cannot be cancelled.",
)
async def cancel_job(
    project_id: UUID,
    job_id: UUID,
    payload: Optional[BackgroundJobCancel] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BackgroundJobRead:
    reason = payload.reason if payload else None
    job = await job_service.cancel_project_job(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        job_id=job_id,
        reason=reason,
    )
    return BackgroundJobRead.model_validate(job)

