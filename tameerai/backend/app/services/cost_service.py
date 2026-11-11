"""
TameerAI - Construction Cost Intelligence Service Layer (Phase 02E)

Encapsulates data operations for:
- MaterialRate: Market surveys across major Pakistani industrial hubs (Lahore, Karachi, Islamabad).
- BOQAnalysis: Project-scoped Bill of Quantities analysis and budget tracking.
- BOQItem: Line-item schedule costs, phase breakdown, and exact Decimal financial arithmetic.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import BOQAnalysis, BOQItem, MaterialRate
from app.models.document import Document
from app.schemas.cost import BOQAnalysisCreate, BOQItemCreate

logger = logging.getLogger("tameerai.services.cost")


# ---------------------------------------------------------------------------
# Material Rates (Global Market Survey Data)
# ---------------------------------------------------------------------------

async def list_material_rates(
    db: AsyncSession,
    city: Optional[str] = None,
    category: Optional[str] = None,
    trend: Optional[str] = None,
    verification_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[MaterialRate]:
    """
    Lists published commodity and labor market rates.
    Supports filtering by city (Lahore, Karachi, Islamabad), category, trend, and status.
    """
    stmt = select(MaterialRate).order_by(MaterialRate.observed_at.desc())
    if city:
        stmt = stmt.where(MaterialRate.city.ilike(f"%{city}%"))
    if category:
        stmt = stmt.where(MaterialRate.category.ilike(f"%{category}%"))
    if trend:
        stmt = stmt.where(MaterialRate.trend == trend)
    if verification_status:
        stmt = stmt.where(MaterialRate.verification_status == verification_status)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_material_rate(
    db: AsyncSession,
    rate_id: UUID,
) -> Optional[MaterialRate]:
    """
    Retrieves a single material rate record by UUID.
    """
    stmt = select(MaterialRate).where(MaterialRate.id == rate_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# BOQ Analyses (Project Workspace Scoped)
# ---------------------------------------------------------------------------

async def list_boq_analyses(
    db: AsyncSession,
    project_id: UUID,
    analysis_status: Optional[str] = None,
) -> List[BOQAnalysis]:
    """
    Lists BOQ analyses for a specific project with optional status filter.
    Enforces project workspace isolation.
    """
    stmt = (
        select(BOQAnalysis)
        .where(BOQAnalysis.project_id == project_id)
        .order_by(BOQAnalysis.created_at.desc())
    )
    if analysis_status:
        stmt = stmt.where(BOQAnalysis.status == analysis_status)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_boq_analysis(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
) -> Optional[BOQAnalysis]:
    """
    Retrieves a single BOQ analysis by UUID within the specified project.
    Returns None if not found or if belonging to another project.
    """
    stmt = select(BOQAnalysis).where(
        BOQAnalysis.id == analysis_id,
        BOQAnalysis.project_id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_boq_analysis(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    data: BOQAnalysisCreate,
) -> BOQAnalysis:
    """
    Creates a new draft BOQ analysis record.
    Validates that any referenced BOQ document strictly belongs to this project.
    Enforces non-negative financial values via Decimal conversion.
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

    budget = Decimal(str(data.project_budget)) if data.project_budget is not None else None
    estimated = Decimal(str(data.estimated_cost)) if data.estimated_cost is not None else None
    current = Decimal(str(data.current_cost)) if data.current_cost is not None else None

    # Calculate variance handling zero-baseline and boundaries properly
    cost_variance = None
    variance_percentage = None
    risk_ind = data.risk_indicator or "Low"

    if budget is not None and estimated is not None:
        cost_variance = estimated - budget
        if budget > Decimal("0.00"):
            raw_pct = ((cost_variance / budget) * Decimal("100.00")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            # PostgreSQL NUMERIC(6, 2) can represent values from -9999.99 to 9999.99.
            # Never silently clamp an actual financial percentage to 9999.99.
            # Since boq_analyses.variance_percentage is nullable, store None (NULL) when unrepresentable.
            if Decimal("-9999.99") <= raw_pct <= Decimal("9999.99"):
                variance_percentage = raw_pct
            else:
                variance_percentage = None

            # Risk indicator derivation uses true un-truncated raw_pct
            if raw_pct >= Decimal("15.00"):
                risk_ind = "High"
            elif raw_pct >= Decimal("5.00"):
                risk_ind = "Medium"
            else:
                risk_ind = "Low"
        elif budget == Decimal("0.00") and estimated == Decimal("0.00"):
            variance_percentage = Decimal("0.00")
            risk_ind = "Low"
        elif budget == Decimal("0.00") and estimated > Decimal("0.00"):
            # Zero baseline with positive expenditure: undefined variance, high escalation alert
            variance_percentage = None
            risk_ind = "High"

    if data.status and data.status not in {"unprocessed", "processing"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Draft BOQ analyses must be created with status 'unprocessed'.",
        )

    analysis = BOQAnalysis(
        project_id=project_id,
        user_id=user_id,
        document_id=data.document_id,
        status="unprocessed",
        project_budget=budget,
        estimated_cost=estimated,
        current_cost=current,
        cost_variance=cost_variance,
        variance_percentage=variance_percentage,
        risk_indicator=risk_ind,
        summary=data.summary or "Draft BOQ cost analysis initialized. Pending item schedule parsing.",
        summary_urdu=data.summary_urdu,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    logger.info("Created BOQ analysis %s for project %s", analysis.id, project_id)
    return analysis


# ---------------------------------------------------------------------------
# BOQ Items (Schedule Items with Decimal Math)
# ---------------------------------------------------------------------------

async def list_boq_items(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
    phase: Optional[str] = None,
) -> List[BOQItem]:
    """
    Lists line-item schedule entries for a BOQ analysis, optionally filtered by phase.
    """
    stmt = (
        select(BOQItem)
        .join(BOQAnalysis, BOQItem.analysis_id == BOQAnalysis.id)
        .where(
            BOQAnalysis.project_id == project_id,
            BOQItem.analysis_id == analysis_id,
        )
        .order_by(BOQItem.phase.asc(), BOQItem.created_at.asc())
    )
    if phase:
        stmt = stmt.where(BOQItem.phase.ilike(f"%{phase}%"))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_boq_item(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
    item_id: UUID,
) -> Optional[BOQItem]:
    """
    Retrieves a single BOQ item by UUID, scoped to parent analysis and project.
    """
    stmt = (
        select(BOQItem)
        .join(BOQAnalysis, BOQItem.analysis_id == BOQAnalysis.id)
        .where(
            BOQAnalysis.project_id == project_id,
            BOQItem.analysis_id == analysis_id,
            BOQItem.id == item_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_boq_item(
    db: AsyncSession,
    project_id: UUID,
    analysis_id: UUID,
    data: BOQItemCreate,
) -> BOQItem:
    """
    Creates a new BOQ schedule item under a parent analysis.
    Applies exact Decimal financial calculations for amounts and escalation variances.
    Enforces non-negative physical quantities and rates.
    """
    # Verify parent analysis exists and lock record to serialize concurrent item additions
    stmt = (
        select(BOQAnalysis)
        .where(
            BOQAnalysis.id == analysis_id,
            BOQAnalysis.project_id == project_id,
        )
        .with_for_update()
    )
    analysis_res = await db.execute(stmt)
    analysis = analysis_res.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOQ analysis not found in this project.",
        )

    # Validate material rate link if provided
    if data.material_rate_id:
        rate = await get_material_rate(db, data.material_rate_id)
        if rate is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced material rate not found in market registry.",
            )

    # Precise Decimal arithmetic
    qty = Decimal(str(data.quantity)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    base_rate = Decimal(str(data.boq_base_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    curr_price = Decimal(str(data.current_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if qty < Decimal("0.000") or base_rate < Decimal("0.00") or curr_price < Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Quantity and unit rates must be non-negative.",
        )

    # Compute budget and estimated totals with overflow boundary protection
    budget_amt = (qty * base_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    estimated_amt = (qty * curr_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    MAX_BOQ_AMOUNT = Decimal("999999999999.99")
    if budget_amt > MAX_BOQ_AMOUNT or estimated_amt > MAX_BOQ_AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Item calculated budget amount or estimated amount exceeds allowable column limit of PKR 999,999,999,999.99.",
        )

    overrun_amt = estimated_amt - budget_amt

    if budget_amt > Decimal("0.00"):
        raw_item_var = ((overrun_amt / budget_amt) * Decimal("100.00")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if raw_item_var < Decimal("-9999.99") or raw_item_var > Decimal("9999.99"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Line item variance percentage ({raw_item_var:+.2f}%) exceeds allowable database "
                    f"column capacity for NUMERIC(6, 2) (-9999.99% to +9999.99%). "
                    f"A schema migration to make boq_items.variance_pct nullable is required "
                    f"before unrepresentable line-item escalation percentages can be recorded."
                ),
            )
        variance_pct = raw_item_var
    elif budget_amt == Decimal("0.00") and estimated_amt == Decimal("0.00"):
        variance_pct = Decimal("0.00")
    else:
        # Zero budget baseline with positive expenditure:
        # Line item variance is mathematically undefined / infinite and cannot be represented in NUMERIC(6, 2) NOT NULL.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Line item variance percentage is undefined for zero baseline budget with positive estimated cost. "
                "A schema migration to make boq_items.variance_pct nullable is required "
                "before unbudgeted items with positive estimated expenditure can be recorded."
            ),
        )

    # Assess risk level based on cost escalation
    if data.risk_level and data.risk_level.lower() in {"low", "medium", "high"}:
        assigned_risk = data.risk_level.lower()
    else:
        if variance_pct >= Decimal("15.00"):
            assigned_risk = "high"
        elif variance_pct >= Decimal("5.00"):
            assigned_risk = "medium"
        else:
            assigned_risk = "low"

    item = BOQItem(
        analysis_id=analysis_id,
        material_rate_id=data.material_rate_id,
        phase=data.phase,
        phase_urdu=data.phase_urdu,
        item_code=data.item_code,
        description=data.description,
        description_urdu=data.description_urdu,
        spec=data.spec,
        unit=data.unit,
        unit_urdu=data.unit_urdu,
        quantity=qty,
        boq_base_rate=base_rate,
        current_price=curr_price,
        budget_amount=budget_amt,
        estimated_amount=estimated_amt,
        overrun_amount=overrun_amt,
        variance_pct=variance_pct,
        risk_level=assigned_risk,
    )
    db.add(item)
    await db.flush()

    # Recalculate parent BOQ analysis aggregate financial metrics
    sum_stmt = select(
        func.coalesce(func.sum(BOQItem.budget_amount), 0),
        func.coalesce(func.sum(BOQItem.estimated_amount), 0),
    ).where(BOQItem.analysis_id == analysis_id)
    sum_res = await db.execute(sum_stmt)
    items_total_budget, items_total_estimated = sum_res.one()

    total_budget_dec = Decimal(str(items_total_budget)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_estimated_dec = Decimal(str(items_total_estimated)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if total_budget_dec > MAX_BOQ_AMOUNT or total_estimated_dec > MAX_BOQ_AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parent BOQ analysis aggregate totals exceed allowable column maximum of PKR 999,999,999,999.99.",
        )

    # In BOQ schedule architecture, parent analysis metrics represent the authoritative sum of schedule items
    analysis.project_budget = total_budget_dec
    analysis.estimated_cost = total_estimated_dec
    analysis.current_cost = total_estimated_dec
    analysis.cost_variance = analysis.estimated_cost - analysis.project_budget

    if analysis.project_budget > Decimal("0.00"):
        raw_pct = (
            (analysis.cost_variance / analysis.project_budget) * Decimal("100.00")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # Never silently clamp percentage. Since boq_analyses.variance_percentage is nullable, store None if out of bounds.
        if Decimal("-9999.99") <= raw_pct <= Decimal("9999.99"):
            analysis.variance_percentage = raw_pct
        else:
            analysis.variance_percentage = None

        if raw_pct >= Decimal("15.00"):
            analysis.risk_indicator = "High"
        elif raw_pct >= Decimal("5.00"):
            analysis.risk_indicator = "Medium"
        else:
            analysis.risk_indicator = "Low"
    elif analysis.project_budget == Decimal("0.00") and analysis.estimated_cost == Decimal("0.00"):
        analysis.variance_percentage = Decimal("0.00")
        analysis.risk_indicator = "Low"
    elif analysis.project_budget == Decimal("0.00") and analysis.estimated_cost > Decimal("0.00"):
        # Zero baseline with positive expenditure: undefined variance, high escalation alert
        analysis.variance_percentage = None
        analysis.risk_indicator = "High"
    elif analysis.project_budget == Decimal("0.00") and analysis.estimated_cost > Decimal("0.00"):
        # Zero baseline with positive expenditure: undefined variance, high escalation alert
        analysis.variance_percentage = None
        analysis.risk_indicator = "High"

    await db.commit()
    await db.refresh(item)
    logger.info("Created BOQ item %s (%s) for analysis %s", item.id, item.phase, analysis_id)
    return item

