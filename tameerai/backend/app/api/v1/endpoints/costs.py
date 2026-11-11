"""
TameerAI - Construction Cost Intelligence Endpoints (Phase 02E)

Endpoints for:
- Material Rates (Market surveys across Lahore, Karachi, Islamabad):
  - GET /api/v1/material-rates
  - GET /api/v1/material-rates/{rate_id}
- BOQ Analyses & Line Items:
  - GET    /api/v1/projects/{project_id}/boq-analyses
  - POST   /api/v1/projects/{project_id}/boq-analyses
  - GET    /api/v1/projects/{project_id}/boq-analyses/{analysis_id}
  - DELETE /api/v1/projects/{project_id}/boq-analyses/{analysis_id} (Preserve audit trail - returns 409)
  - GET    /api/v1/projects/{project_id}/boq-analyses/{analysis_id}/items
  - POST   /api/v1/projects/{project_id}/boq-analyses/{analysis_id}/items
  - GET    /api/v1/projects/{project_id}/boq-analyses/{analysis_id}/items/{item_id}
  - DELETE /api/v1/projects/{project_id}/boq-analyses/{analysis_id}/items/{item_id} (Preserve trail - returns 409)
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.compliance import get_project_with_engineering_edit_access
from app.api.v1.endpoints.projects import get_project_with_view_access
from app.models.project import Project
from app.models.user import User
from app.schemas.cost import (
    BOQAnalysisCreate,
    BOQAnalysisRead,
    BOQItemCreate,
    BOQItemRead,
    MaterialRateRead,
)
from app.services.cost_service import (
    create_boq_analysis,
    create_boq_item,
    get_boq_analysis,
    get_boq_item,
    get_material_rate,
    list_boq_analyses,
    list_boq_items,
    list_material_rates,
)

logger = logging.getLogger("tameerai.api.costs")

router = APIRouter()
material_rates_router = APIRouter()


# ---------------------------------------------------------------------------
# Global Material Rates
# ---------------------------------------------------------------------------

@material_rates_router.get(
    "",
    response_model=List[MaterialRateRead],
    summary="List market survey material rates",
    description="Returns verified and surveyed material quotes for major cities (Lahore, Karachi, Islamabad).",
)
async def list_rates(
    city: Optional[str] = Query(None, description="Filter by city: Lahore, Karachi, Islamabad, Rawalpindi"),
    category: Optional[str] = Query(None, description="Filter by category: steel, cement, bricks, aggregates, labor"),
    trend: Optional[str] = Query(None, description="Filter by trend: up, down, neutral"),
    verification_status: Optional[str] = Query(None, alias="verificationStatus", description="Filter by status: verified, unverified, stale"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_material_rates(
        db,
        city=city,
        category=category,
        trend=trend,
        verification_status=verification_status,
        limit=limit,
        offset=offset,
    )


@material_rates_router.get(
    "/{rate_id}",
    response_model=MaterialRateRead,
    summary="Get material rate details",
    description="Retrieves a specific commodity or labor rate quote by UUID.",
)
async def get_rate(
    rate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rate = await get_material_rate(db, rate_id=rate_id)
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material rate quote not found.",
        )
    return rate


# ---------------------------------------------------------------------------
# BOQ Analyses (Project Workspace Scoped)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[BOQAnalysisRead],
    summary="List project BOQ analyses",
    description="Returns all Bill of Quantities analyses for the specified project. Requires project membership.",
)
async def list_analyses(
    analysis_status: Optional[str] = Query(None, alias="status", description="Filter by status: unprocessed, processing, completed, failed"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await list_boq_analyses(db, project_id=project.id, analysis_status=analysis_status)


@router.post(
    "",
    response_model=BOQAnalysisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft BOQ analysis",
    description="Initializes a draft BOQ cost analysis record. Document references are validated against project ownership.",
)
async def create_analysis(
    analysis_in: BOQAnalysisCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_boq_analysis(
        db,
        project_id=project.id,
        user_id=current_user.id,
        data=analysis_in,
    )


@router.get(
    "/{analysis_id}",
    response_model=BOQAnalysisRead,
    summary="Get BOQ analysis details",
    description="Retrieves a specific BOQ analysis by UUID. Enforces project workspace boundary.",
)
async def get_analysis(
    analysis_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    analysis = await get_boq_analysis(db, project_id=project.id, analysis_id=analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOQ analysis not found in this project.",
        )
    return analysis


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete BOQ analysis (Preservation Gate)",
    description="Public deletion is prohibited to preserve tender financial records and quantity surveying audit trails.",
)
async def delete_analysis(
    analysis_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    analysis = await get_boq_analysis(db, project_id=project.id, analysis_id=analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOQ analysis not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of BOQ analyses is strictly prohibited to preserve financial audit trails.",
    )


# ---------------------------------------------------------------------------
# BOQ Items
# ---------------------------------------------------------------------------

@router.get(
    "/{analysis_id}/items",
    response_model=List[BOQItemRead],
    summary="List line items for BOQ analysis",
    description="Lists all scheduled work items and materials for a BOQ analysis.",
)
async def list_items(
    analysis_id: UUID,
    phase: Optional[str] = Query(None, description="Filter by phase: Substructure, Superstructure, MEP, Finishing"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    analysis = await get_boq_analysis(db, project_id=project.id, analysis_id=analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOQ analysis not found in this project.",
        )
    return await list_boq_items(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        phase=phase,
    )


@router.post(
    "/{analysis_id}/items",
    response_model=BOQItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create line item for BOQ analysis",
    description="Adds an itemized schedule entry with automatic exact Decimal arithmetic calculation.",
)
async def create_item(
    analysis_id: UUID,
    item_in: BOQItemCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_boq_item(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        data=item_in,
    )


@router.get(
    "/{analysis_id}/items/{item_id}",
    response_model=BOQItemRead,
    summary="Get BOQ item details",
    description="Retrieves a specific BOQ schedule item by UUID.",
)
async def get_item(
    analysis_id: UUID,
    item_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    item = await get_boq_item(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        item_id=item_id,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOQ item not found in this analysis.",
        )
    return item


@router.delete(
    "/{analysis_id}/items/{item_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete BOQ item (Preservation Gate)",
    description="Public deletion of BOQ items is prohibited to preserve quantity surveying evidentiary audit trails.",
)
async def delete_item(
    analysis_id: UUID,
    item_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    item = await get_boq_item(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        item_id=item_id,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOQ item not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of BOQ schedule items is strictly prohibited to preserve financial audit integrity.",
    )

