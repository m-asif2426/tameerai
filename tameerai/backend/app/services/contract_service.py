"""
TameerAI - Contract Intelligence Service Layer (Phase 02E)

Encapsulates data operations for:
- ContractAnalysis: Creation of draft analyses, listing, retrieving by ID.
- ContractRiskCard: Creation of clause risk cards, FIDIC citations, flagged clause counts.
- Cross-project document isolation and audit trail preservation.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import ContractAnalysis, ContractRiskCard
from app.models.document import Document
from app.schemas.contract import ContractAnalysisCreate, ContractRiskCardCreate

logger = logging.getLogger("tameerai.services.contract")


async def list_contract_analyses(
    db: AsyncSession,
    project_id: UUID,
    analysis_status: Optional[str] = None,
) -> List[ContractAnalysis]:
    """
    Lists contract analyses for a specific project with optional status filter.
    Enforces project workspace isolation.
    """
    stmt = (
        select(ContractAnalysis)
        .where(ContractAnalysis.project_id == project_id)
        .order_by(ContractAnalysis.created_at.desc())
    )
    if analysis_status:
        stmt = stmt.where(ContractAnalysis.status == analysis_status)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contract_analysis(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
) -> Optional[ContractAnalysis]:
    """
    Retrieves a single contract analysis by UUID within the specified project.
    Returns None if not found or if belonging to another project.
    """
    stmt = select(ContractAnalysis).where(
        ContractAnalysis.id == analysis_id,
        ContractAnalysis.project_id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_contract_analysis(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    data: ContractAnalysisCreate,
) -> ContractAnalysis:
    """
    Creates a new draft contract analysis record.
    Validates that any referenced contract document strictly belongs to this project.
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

    if data.status and data.status not in {"unprocessed", "processing"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Draft contract analyses must be created with status 'unprocessed'.",
        )

    analysis = ContractAnalysis(
        project_id=project_id,
        user_id=user_id,
        document_id=data.document_id,
        contract_title=data.contract_title,
        standard_format=data.standard_format or "FIDIC Red Book 2017 & PEC",
        status="unprocessed",
        risk_score=None,
        risk_category=None,
        total_clauses_audited=0,
        flagged_clauses_count=0,
        summary=data.summary or "Draft contract analysis initialized. Pending clause extraction.",
        summary_urdu=data.summary_urdu,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    logger.info("Created contract analysis %s for project %s", analysis.id, project_id)
    return analysis


async def list_contract_risk_cards(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
    risk_level: Optional[str] = None,
) -> List[ContractRiskCard]:
    """
    Lists risk cards for a contract analysis, optionally filtered by risk level.
    """
    stmt = (
        select(ContractRiskCard)
        .join(ContractAnalysis, ContractRiskCard.analysis_id == ContractAnalysis.id)
        .where(
            ContractAnalysis.project_id == project_id,
            ContractRiskCard.analysis_id == analysis_id,
        )
        .order_by(ContractRiskCard.code.asc(), ContractRiskCard.created_at.asc())
    )
    if risk_level:
        stmt = stmt.where(ContractRiskCard.risk_level == risk_level)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contract_risk_card(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
    card_identifier: str,
) -> Optional[ContractRiskCard]:
    """
    Retrieves a contract risk card by either UUID or public code (e.g. RISK-001).
    """
    stmt = (
        select(ContractRiskCard)
        .join(ContractAnalysis, ContractRiskCard.analysis_id == ContractAnalysis.id)
        .where(
            ContractAnalysis.project_id == project_id,
            ContractRiskCard.analysis_id == analysis_id,
        )
    )
    try:
        card_uuid = UUID(card_identifier)
        stmt = stmt.where(ContractRiskCard.id == card_uuid)
    except (ValueError, AttributeError):
        stmt = stmt.where(ContractRiskCard.code == card_identifier)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_contract_risk_card(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
    data: ContractRiskCardCreate,
) -> ContractRiskCard:
    """
    Creates a new risk card under a contract analysis.
    Auto-assigns code if omitted (e.g. RISK-001) and updates clause counters.
    """
    # Verify analysis exists and lock record to serialize clause updates
    stmt = (
        select(ContractAnalysis)
        .where(
            ContractAnalysis.id == analysis_id,
            ContractAnalysis.project_id == project_id,
        )
        .with_for_update()
    )
    analysis_res = await db.execute(stmt)
    analysis = analysis_res.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract analysis not found in this project.",
        )

    # Auto-generate risk code if omitted
    if not data.code:
        count_stmt = select(func.count(ContractRiskCard.id)).where(
            ContractRiskCard.analysis_id == analysis_id
        )
        count_res = await db.execute(count_stmt)
        current_count = count_res.scalar_one() or 0
        assigned_code = f"RISK-{current_count + 1:03d}"
    else:
        assigned_code = data.code

    card = ContractRiskCard(
        analysis_id=analysis_id,
        code=assigned_code,
        clause_title=data.clause_title,
        clause_title_urdu=data.clause_title_urdu,
        fidic_reference=data.fidic_reference,
        page_number=data.page_number,
        risk_level=data.risk_level,
        risk_level_label=data.risk_level_label,
        risk_level_label_urdu=data.risk_level_label_urdu,
        explanation=data.explanation,
        explanation_urdu=data.explanation_urdu,
        recommendation=data.recommendation,
        recommendation_urdu=data.recommendation_urdu,
        impact_metric=data.impact_metric,
        raw_clause_snippet=data.raw_clause_snippet,
        citation_metadata=data.citation_metadata,
    )
    db.add(card)

    # Update flagged clause counter without falsely inflating total_clauses_audited
    if data.risk_level in {"high", "medium"}:
        analysis.flagged_clauses_count += 1

    await db.commit()
    await db.refresh(card)
    logger.info("Created contract risk card %s (%s) for analysis %s", card.id, card.code, analysis_id)
    return card

