"""
TameerAI - Engineering Consulting Report Service Layer (Phase 02E)

Encapsulates data operations for:
- Report: Creation of draft report dossiers, metadata compilation, public code mapping (RPT-001).
- Cross-project linkage verification for compliance, contract, and BOQ analyses.
- Storage key masking to prevent direct exposure of cloud URLs.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.compliance import ComplianceAudit
from app.models.contract import ContractAnalysis
from app.models.cost import BOQAnalysis
from app.models.report import Report
from app.schemas.report import ReportCreate

logger = logging.getLogger("tameerai.services.report")

CATEGORY_LABEL_DEFAULTS = {
    "compliance": "Building Code & Structural Compliance",
    "contract": "FIDIC Contract & Legal Risk Review",
    "cost": "Bill of Quantities & Cost Variance Dossier",
    "executive_comprehensive": "Executive Comprehensive Engineering Brief",
}

STATUS_LABEL_DEFAULTS = {
    "certified": "Certified Compliant",
    "action_required": "Action Required - Redesign",
    "overrun_alert": "Budget Overrun Warning",
    "in_review": "Draft Under Technical Review",
    "approved": "Approved for Tender/Construction",
}


async def list_reports(
    db: AsyncSession,
    project_id: UUID,
    category: Optional[str] = None,
    report_status: Optional[str] = None,
) -> List[Report]:
    """
    Lists engineering consulting reports for a project workspace.
    Eagerly loads parent project for title and metadata formatting.
    """
    stmt = (
        select(Report)
        .options(selectinload(Report.project))
        .where(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
    )
    if category:
        stmt = stmt.where(Report.category == category)
    if report_status:
        stmt = stmt.where(Report.status == report_status)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_report(
    db: AsyncSession,
    project_id: UUID,
    report_identifier: str,
) -> Optional[Report]:
    """
    Retrieves a report by either internal UUID or public code (e.g. RPT-001).
    Eagerly loads parent project.
    """
    stmt = (
        select(Report)
        .options(selectinload(Report.project))
        .where(Report.project_id == project_id)
    )
    try:
        report_uuid = UUID(report_identifier)
        stmt = stmt.where(Report.id == report_uuid)
    except (ValueError, AttributeError):
        stmt = stmt.where(Report.code == report_identifier)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_report(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    data: ReportCreate,
) -> Report:
    """
    Creates a new draft engineering report record.
    Verifies that any linked compliance, contract, or BOQ analyses strictly belong to this project.
    Auto-assigns public code (e.g. RPT-001) if not provided.
    """
    # Cross-project reference validations
    if data.compliance_audit_id:
        audit_res = await db.execute(
            select(ComplianceAudit).where(
                ComplianceAudit.id == data.compliance_audit_id,
                ComplianceAudit.project_id == project_id,
            )
        )
        if audit_res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced compliance audit does not belong to this project.",
            )

    if data.contract_analysis_id:
        contract_res = await db.execute(
            select(ContractAnalysis).where(
                ContractAnalysis.id == data.contract_analysis_id,
                ContractAnalysis.project_id == project_id,
            )
        )
        if contract_res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced contract analysis does not belong to this project.",
            )

    if data.boq_analysis_id:
        boq_res = await db.execute(
            select(BOQAnalysis).where(
                BOQAnalysis.id == data.boq_analysis_id,
                BOQAnalysis.project_id == project_id,
            )
        )
        if boq_res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced BOQ analysis does not belong to this project.",
            )

    # Auto-generate public code if omitted
    if not data.code:
        count_stmt = select(func.count(Report.id)).where(Report.project_id == project_id)
        count_res = await db.execute(count_stmt)
        current_count = count_res.scalar_one() or 0
        assigned_code = f"RPT-{current_count + 1:03d}"
    else:
        assigned_code = data.code

    cat = data.category or "executive_comprehensive"
    stat = data.status or "in_review"
    if stat in {"certified", "approved"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Draft consulting reports cannot be initialized with certified or approved status.",
        )
    cat_label = data.category_label or CATEGORY_LABEL_DEFAULTS.get(cat, "Engineering Report")
    stat_label = data.status_label or STATUS_LABEL_DEFAULTS.get(stat, "In Review")

    report = Report(
        code=assigned_code,
        project_id=project_id,
        user_id=user_id,
        compliance_audit_id=data.compliance_audit_id,
        contract_analysis_id=data.contract_analysis_id,
        boq_analysis_id=data.boq_analysis_id,
        category=cat,
        category_label=cat_label,
        title=data.title,
        title_urdu=data.title_urdu,
        status=stat,
        status_label=stat_label,
        status_label_urdu=data.status_label_urdu,
        file_size="0 MB",
        page_count=max(1, data.page_count),
        author=data.author or "TameerAI Engineering Intelligence",
        file_path=None,  # Storage key masked in draft state
        executive_summary=data.executive_summary or "Draft engineering report pending final sign-off.",
        executive_summary_urdu=data.executive_summary_urdu,
        key_metric=data.key_metric or "Pending Assessment",
        metadata_json=None,
        generated_at=None,
    )
    db.add(report)
    await db.commit()

    # Re-fetch with eager loaded project for Pydantic serializer
    stmt = (
        select(Report)
        .options(selectinload(Report.project))
        .where(Report.id == report.id)
    )
    res = await db.execute(stmt)
    refreshed_report = res.scalar_one()

    logger.info("Created report %s (%s) for project %s", refreshed_report.id, refreshed_report.code, project_id)
    return refreshed_report

