"""
TameerAI - Compliance & Building Code Endpoints (Phase 02E)

Endpoints for:
- GET    /api/v1/projects/{project_id}/compliance-audits (List audits with optional status filter)
- POST   /api/v1/projects/{project_id}/compliance-audits (Create draft compliance audit)
- GET    /api/v1/projects/{project_id}/compliance-audits/{audit_id} (Retrieve audit details)
- DELETE /api/v1/projects/{project_id}/compliance-audits/{audit_id} (Preserve audit trail - returns 409)
- GET    /api/v1/projects/{project_id}/compliance-audits/{audit_id}/findings (List findings)
- POST   /api/v1/projects/{project_id}/compliance-audits/{audit_id}/findings (Add finding)
- GET    /api/v1/projects/{project_id}/compliance-audits/{audit_id}/findings/{finding_id} (Retrieve finding)
- DELETE /api/v1/projects/{project_id}/compliance-audits/{audit_id}/findings/{finding_id} (Preserve trail - returns 409)
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.projects import get_project_with_view_access
from app.models.project import Project
from app.models.user import User
from app.schemas.compliance import (
    ComplianceAuditCreate,
    ComplianceAuditRead,
    ComplianceFindingCreate,
    ComplianceFindingRead,
)
from app.services.compliance_service import (
    create_compliance_audit,
    create_compliance_finding,
    get_compliance_audit,
    get_compliance_finding,
    list_compliance_audits,
    list_compliance_findings,
)

logger = logging.getLogger("tameerai.api.compliance")

router = APIRouter()


async def get_project_with_engineering_edit_access(
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
) -> Tuple[Project, str]:
    """
    Ensures caller has permission to create or modify engineering records.
    Permitted: owner, lead_engineer, architect, contractor.
    Viewer role is strictly rejected with 403 Forbidden.
    """
    project, user_role = project_data
    if user_role not in {"owner", "lead_engineer", "architect", "contractor"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Viewers cannot create or modify compliance records.",
        )
    return project, user_role


# ---------------------------------------------------------------------------
# Compliance Audits
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[ComplianceAuditRead],
    summary="List project compliance audits",
    description="Returns all compliance audits for the specified project. Requires project membership.",
)
async def list_audits(
    audit_status: Optional[str] = Query(None, alias="status", description="Filter by status: pending, in_progress, completed, failed"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await list_compliance_audits(db, project_id=project.id, audit_status=audit_status)


@router.post(
    "",
    response_model=ComplianceAuditRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft compliance audit",
    description="Initializes a draft compliance audit record. Document references are validated against project ownership.",
)
async def create_audit(
    audit_in: ComplianceAuditCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_compliance_audit(
        db,
        project_id=project.id,
        user_id=current_user.id,
        data=audit_in,
    )


@router.get(
    "/{audit_id}",
    response_model=ComplianceAuditRead,
    summary="Get compliance audit details",
    description="Retrieves a specific compliance audit by UUID. Enforces project workspace boundary.",
)
async def get_audit(
    audit_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    audit = await get_compliance_audit(db, project_id=project.id, audit_id=audit_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance audit not found in this project.",
        )
    return audit


@router.delete(
    "/{audit_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete compliance audit (Preservation Gate)",
    description="Public deletion is prohibited to protect legal evidentiary integrity and statutory compliance audit trails.",
)
async def delete_audit(
    audit_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    audit = await get_compliance_audit(db, project_id=project.id, audit_id=audit_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance audit not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of compliance audits is strictly prohibited to preserve statutory engineering audit trails.",
    )


# ---------------------------------------------------------------------------
# Compliance Findings
# ---------------------------------------------------------------------------

@router.get(
    "/{audit_id}/findings",
    response_model=List[ComplianceFindingRead],
    summary="List findings for compliance audit",
    description="Lists all code findings, warnings, and violations for an audit.",
)
async def list_findings(
    audit_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category: egress, structural, zoning, fire"),
    finding_status: Optional[str] = Query(None, alias="status", description="Filter by status: violation, warning, passed"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    audit = await get_compliance_audit(db, project_id=project.id, audit_id=audit_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance audit not found in this project.",
        )
    return await list_compliance_findings(
        db,
        project_id=project.id,
        audit_id=audit_id,
        category=category,
        finding_status=finding_status,
    )


@router.post(
    "/{audit_id}/findings",
    response_model=ComplianceFindingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create finding for compliance audit",
    description="Records a new rule violation, warning, or passed check with spatial pin coordinates.",
)
async def create_finding(
    audit_id: UUID,
    finding_in: ComplianceFindingCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_compliance_finding(
        db,
        project_id=project.id,
        audit_id=audit_id,
        data=finding_in,
    )


@router.get(
    "/{audit_id}/findings/{finding_id}",
    response_model=ComplianceFindingRead,
    summary="Get finding details",
    description="Retrieves a specific finding by UUID or public code (e.g. FIND-001).",
)
async def get_finding(
    audit_id: UUID,
    finding_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    finding = await get_compliance_finding(
        db,
        project_id=project.id,
        audit_id=audit_id,
        finding_identifier=finding_id,
    )
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance finding not found in this audit.",
        )
    return finding


@router.delete(
    "/{audit_id}/findings/{finding_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete finding (Preservation Gate)",
    description="Public deletion of findings is prohibited to protect building safety evidence.",
)
async def delete_finding(
    audit_id: UUID,
    finding_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    finding = await get_compliance_finding(
        db,
        project_id=project.id,
        audit_id=audit_id,
        finding_identifier=finding_id,
    )
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance finding not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of compliance findings is strictly prohibited to preserve evidentiary audit integrity.",
    )

