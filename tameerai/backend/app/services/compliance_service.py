"""
TameerAI - Compliance & Building Code Service Layer (Phase 02E)

Encapsulates data operations for:
- ComplianceAudit: Creation of draft audits, listing, retrieving by ID.
- ComplianceFinding: Creation of localized findings, coordinate pins, counter aggregation.
- Evidentiary integrity and cross-project document isolation enforcement.
"""

import logging
import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ComplianceAudit, ComplianceFinding
from app.models.document import Document
from app.schemas.compliance import ComplianceAuditCreate, ComplianceFindingCreate

logger = logging.getLogger("tameerai.services.compliance")


async def list_compliance_audits(
    db: AsyncSession,
    project_id: UUID,
    audit_status: Optional[str] = None,
) -> List[ComplianceAudit]:
    """
    Lists compliance audits for a specific project with optional status filter.
    Enforces project scoping.
    """
    stmt = (
        select(ComplianceAudit)
        .where(ComplianceAudit.project_id == project_id)
        .order_by(ComplianceAudit.created_at.desc())
    )
    if audit_status:
        stmt = stmt.where(ComplianceAudit.status == audit_status)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_compliance_audit(
    db: AsyncSession,
    project_id: UUID,
    audit_id: UUID,
) -> Optional[ComplianceAudit]:
    """
    Retrieves a single compliance audit by UUID within the specified project workspace.
    Returns None if not found or if it belongs to a different project.
    """
    stmt = select(ComplianceAudit).where(
        ComplianceAudit.id == audit_id,
        ComplianceAudit.project_id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_compliance_audit(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    data: ComplianceAuditCreate,
) -> ComplianceAudit:
    """
    Creates a new draft compliance audit record.
    Validates that any referenced document strictly belongs to this project.
    """
    if data.document_id:
        doc_stmt = select(Document).where(
            Document.id == data.document_id,
            Document.project_id == project_id,
        )
        doc_res = await db.execute(doc_stmt)
        if doc_res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced document does not belong to this project.",
            )

    if data.status and data.status not in {"pending", "in_progress"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Draft compliance audits must be created with status 'pending'.",
        )

    audit = ComplianceAudit(
        project_id=project_id,
        user_id=user_id,
        document_id=data.document_id,
        status="pending",
        overall_score=None,
        total_checks=0,
        passed_count=0,
        warning_count=0,
        violation_count=0,
        governing_code=data.governing_code or "Building Code of Pakistan (BCP 2021) / SBC",
        summary=data.summary or "Draft compliance audit created. Pending automated code rule evaluation.",
        summary_urdu=data.summary_urdu,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    logger.info("Created compliance audit %s for project %s", audit.id, project_id)
    return audit


async def list_compliance_findings(
    db: AsyncSession,
    project_id: UUID,
    audit_id: UUID,
    category: Optional[str] = None,
    finding_status: Optional[str] = None,
) -> List[ComplianceFinding]:
    """
    Lists compliance findings for an audit, optionally filtered by category and status.
    """
    stmt = (
        select(ComplianceFinding)
        .where(
            ComplianceFinding.project_id == project_id,
            ComplianceFinding.audit_id == audit_id,
        )
        .order_by(ComplianceFinding.code.asc(), ComplianceFinding.created_at.asc())
    )
    if category:
        stmt = stmt.where(ComplianceFinding.category == category)
    if finding_status:
        stmt = stmt.where(ComplianceFinding.status == finding_status)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_compliance_finding(
    db: AsyncSession,
    project_id: UUID,
    audit_id: UUID,
    finding_identifier: str,
) -> Optional[ComplianceFinding]:
    """
    Retrieves a compliance finding by either UUID or public code (e.g. FIND-001).
    """
    stmt = select(ComplianceFinding).where(
        ComplianceFinding.project_id == project_id,
        ComplianceFinding.audit_id == audit_id,
    )
    try:
        finding_uuid = UUID(finding_identifier)
        stmt = stmt.where(ComplianceFinding.id == finding_uuid)
    except (ValueError, AttributeError):
        stmt = stmt.where(ComplianceFinding.code == finding_identifier)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_compliance_finding(
    db: AsyncSession,
    project_id: UUID,
    audit_id: UUID,
    data: ComplianceFindingCreate,
) -> ComplianceFinding:
    """
    Creates a new compliance finding under an audit.
    Auto-assigns code if omitted (e.g. FIND-001) and updates parent audit check counters.
    """
    # Verify audit exists in this project and lock parent record to serialize counter updates
    audit_stmt = (
        select(ComplianceAudit)
        .where(
            ComplianceAudit.id == audit_id,
            ComplianceAudit.project_id == project_id,
        )
        .with_for_update()
    )
    audit_res = await db.execute(audit_stmt)
    audit = audit_res.scalar_one_or_none()
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance audit not found in this project.",
        )

    # Validate document attachment if provided
    doc_id = data.document_id or audit.document_id
    if doc_id:
        doc_stmt = select(Document).where(
            Document.id == doc_id,
            Document.project_id == project_id,
        )
        doc_res = await db.execute(doc_stmt)
        if doc_res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced document does not belong to this project.",
            )

    # Auto-generate finding code if not provided
    if not data.code:
        count_stmt = select(func.count(ComplianceFinding.id)).where(
            ComplianceFinding.audit_id == audit_id
        )
        count_res = await db.execute(count_stmt)
        current_count = count_res.scalar_one() or 0
        assigned_code = f"FIND-{current_count + 1:03d}"
    else:
        assigned_code = data.code

    # Extract pin coordinates
    pin_x = None
    pin_y = None
    coord_space = "normalized_percentage"
    if data.pin_coordinates:
        pin_x = data.pin_coordinates.x
        pin_y = data.pin_coordinates.y
        coord_space = data.pin_coordinates.space or "normalized_percentage"

    finding = ComplianceFinding(
        audit_id=audit_id,
        project_id=project_id,
        document_id=doc_id,
        code=assigned_code,
        category=data.category,
        category_name=data.category_name,
        category_name_urdu=data.category_name_urdu,
        title=data.title,
        title_urdu=data.title_urdu,
        status=data.status,
        required_value=data.required_value,
        current_value=data.current_value,
        variance=data.variance,
        reference_code=data.reference_code,
        reference_clause=data.reference_clause,
        location_grid=data.location_grid,
        sheet_number=data.sheet_number,
        description=data.description,
        description_urdu=data.description_urdu,
        remedy=data.remedy,
        remedy_urdu=data.remedy_urdu,
        coordinate_space=coord_space,
        pin_x=pin_x,
        pin_y=pin_y,
        is_resolved=False,
    )
    db.add(finding)

    # Update audit counters
    audit.total_checks += 1
    if data.status == "passed":
        audit.passed_count += 1
    elif data.status == "warning":
        audit.warning_count += 1
    elif data.status == "violation":
        audit.violation_count += 1

    await db.commit()
    await db.refresh(finding)
    logger.info("Created compliance finding %s (%s) for audit %s", finding.id, finding.code, audit_id)
    return finding

