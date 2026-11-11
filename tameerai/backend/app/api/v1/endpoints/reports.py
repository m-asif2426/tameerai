"""
TameerAI - Consulting Report Endpoints (Phase 02E)

Endpoints for:
- GET    /api/v1/projects/{project_id}/reports (List consulting reports)
- POST   /api/v1/projects/{project_id}/reports (Create draft report dossier)
- GET    /api/v1/projects/{project_id}/reports/{report_id} (Retrieve report details)
- DELETE /api/v1/projects/{project_id}/reports/{report_id} (Preserve audit trail - returns 409)
"""

import logging
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.compliance import get_project_with_engineering_edit_access
from app.api.v1.endpoints.projects import get_project_with_view_access
from app.models.project import Project
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead
from app.services.report_service import (
    create_report,
    get_report,
    list_reports,
)

logger = logging.getLogger("tameerai.api.reports")

router = APIRouter()


@router.get(
    "",
    response_model=List[ReportRead],
    summary="List project consulting reports",
    description="Returns all consulting reports compiled for the specified project. Requires project membership.",
)
async def list_project_reports(
    category: Optional[str] = Query(None, description="Filter by category: compliance, contract, cost, executive_comprehensive"),
    report_status: Optional[str] = Query(None, alias="status", description="Filter by status: certified, action_required, overrun_alert, in_review, approved"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await list_reports(
        db,
        project_id=project.id,
        category=category,
        report_status=report_status,
    )


@router.post(
    "",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft consulting report",
    description="Initializes a draft consulting report dossier. Cross-references are verified against project ownership.",
)
async def create_project_report(
    report_in: ReportCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_report(
        db,
        project_id=project.id,
        user_id=current_user.id,
        data=report_in,
    )


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    summary="Get consulting report details",
    description="Retrieves a specific report by UUID or public code (e.g. RPT-001). Internal storage keys are masked.",
)
async def get_project_report(
    report_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    report = await get_report(db, project_id=project.id, report_identifier=report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consulting report not found in this project.",
        )
    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete consulting report (Preservation Gate)",
    description="Public deletion of consulting reports is strictly prohibited to maintain permanent statutory engineering audit trails.",
)
async def delete_project_report(
    report_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    report = await get_report(db, project_id=project.id, report_identifier=report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consulting report not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of consulting reports is strictly prohibited to preserve official engineering audit records.",
    )

