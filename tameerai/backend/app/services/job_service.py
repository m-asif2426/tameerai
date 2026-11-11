"""
TameerAI - Background Job Management Service (Phase 02G)

Implements business logic for:
- Enqueuing background jobs with role validation and idempotency
- Scoping jobs strictly to project workspaces
- Enforcing viewer read-only restrictions
- Validating document references within project boundaries
- Listing and inspecting project job execution statuses
- Cancelling queued, retrying, and running jobs
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.models.job import BackgroundJob, JobStatus, JobType
from app.models.project import Project
from app.schemas.job import BackgroundJobCreate
from app.services.project_service import ROLE_LEVELS, get_user_project_role
from app.workers.job_worker import sanitize_error_message

logger = logging.getLogger("tameerai.job_service")

# Approved registered job types
APPROVED_JOB_TYPES = {t.value for t in JobType}


async def verify_project_job_access(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    min_role_level: int = 1,
) -> tuple[Project, str]:
    """
    Verifies that the project exists and that the user holds at least min_role_level.
    Returns (project, role).
    Raises:
    - 404 if project not found or caller has no membership (anti-enumeration).
    - 403 if caller is a project member but lacks required role level.
    """
    project = await db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access.",
        )

    role = await get_user_project_role(db, project, user_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access.",
        )

    user_level = ROLE_LEVELS.get(role, 0)
    if user_level < min_role_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role level is {min_role_level}, your role is '{role}'.",
        )

    return project, role


async def enqueue_project_job(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    data: BackgroundJobCreate,
) -> BackgroundJob:
    """
    Enqueues a background job within a project workspace.
    Enforces:
    1. Project access: requires contractor (2), architect (3), lead_engineer (4), or owner (5).
       Viewer (1) is rejected with HTTP 403.
    2. Validated job type: must be one of the approved registered job types.
    3. Document containment: referenced documents in payload must belong to project_id.
    4. Idempotency deduplication: returns existing job if idempotency_key matches.
    """
    # 1. Verify project permission (viewers rejected)
    await verify_project_job_access(db, project_id, user_id, min_role_level=2)

    # 2. Validate job type against approved registry
    if data.job_type not in APPROVED_JOB_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Job type '{data.job_type}' is not recognized. Approved job types are: {sorted(list(APPROVED_JOB_TYPES))}.",
        )

    # 2b. Synthetic handler security guard: reject in production or when disabled
    if data.job_type == JobType.SYNTHETIC_TEST.value:
        is_dev_or_test = settings.ENVIRONMENT.lower() in {"development", "test", "local"}
        if not (is_dev_or_test and settings.ENABLE_SYNTHETIC_JOBS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Synthetic test jobs are disabled in this environment.",
            )

    # 3. Validate document containment if payload references a document
    payload = data.payload or {}
    doc_id_val = payload.get("document_id") or payload.get("documentId")
    if doc_id_val:
        try:
            doc_uuid = UUID(str(doc_id_val).strip())
            doc = await db.scalar(select(Document).where(Document.id == doc_uuid))
            if doc is None or doc.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced document does not belong to this project or could not be found.",
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed document identifier in payload.",
            )

    # 4. Check idempotency deduplication if key is provided
    if data.idempotency_key:
        clean_key = data.idempotency_key.strip()
        existing = await db.scalar(
            select(BackgroundJob).where(
                BackgroundJob.project_id == project_id,
                BackgroundJob.job_type == data.job_type,
                BackgroundJob.idempotency_key == clean_key,
            )
        )
        if existing is not None:
            logger.info("Idempotent hit for job key '%s' in project %s", clean_key, project_id)
            return existing

    # 5. Create durable job record
    job = BackgroundJob(
        project_id=project_id,
        user_id=user_id,
        job_type=data.job_type,
        status=JobStatus.QUEUED.value,
        priority=data.priority,
        max_retries=data.max_retries,
        payload=payload,
        idempotency_key=data.idempotency_key.strip() if data.idempotency_key else None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    logger.info("Enqueued job %s (type: %s, priority: %d) for project %s", job.id, job.job_type, job.priority, project_id)
    return job


async def list_project_jobs(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    status_filter: Optional[str] = None,
    job_type_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[BackgroundJob]:
    """
    Lists jobs scoped to a project workspace. Accessible to all project members including viewers.
    """
    await verify_project_job_access(db, project_id, user_id, min_role_level=1)

    stmt = select(BackgroundJob).where(BackgroundJob.project_id == project_id)
    if status_filter:
        stmt = stmt.where(BackgroundJob.status == status_filter)
    if job_type_filter:
        stmt = stmt.where(BackgroundJob.job_type == job_type_filter)

    stmt = stmt.order_by(BackgroundJob.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_project_job(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    job_id: UUID,
) -> BackgroundJob:
    """
    Retrieves a single job by UUID scoped to the specified project.
    """
    await verify_project_job_access(db, project_id, user_id, min_role_level=1)

    stmt = select(BackgroundJob).where(
        BackgroundJob.id == job_id,
        BackgroundJob.project_id == project_id,
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found.",
        )
    return job


async def cancel_project_job(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    job_id: UUID,
    reason: Optional[str] = None,
) -> BackgroundJob:
    """
    Cancels a pending, retrying, or running background job.
    Permission: requires lead_engineer (4) or owner (5), OR being the job creator.
    Viewers cannot cancel jobs.
    """
    _, role = await verify_project_job_access(db, project_id, user_id, min_role_level=1)
    user_level = ROLE_LEVELS.get(role, 0)

    # Lock job record
    stmt = (
        select(BackgroundJob)
        .where(
            BackgroundJob.id == job_id,
            BackgroundJob.project_id == project_id,
        )
        .with_for_update()
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found.",
        )

    # Authorization check: owner, lead engineer, or job creator
    if user_level < 4 and job.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners, lead engineers, or the job creator can cancel this job.",
        )

    # State transition validation
    if job.status == JobStatus.CANCELLED.value:
        return job

    if job.status in {JobStatus.COMPLETED.value, JobStatus.FAILED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job in terminal state '{job.status}'.",
        )

    job.transition_to(JobStatus.CANCELLED.value)
    job.error_message = sanitize_error_message(f"Cancelled by user: {reason or 'No reason provided'}")
    await db.commit()
    await db.refresh(job)
    logger.info("Cancelled job %s in project %s", job_id, project_id)
    return job

