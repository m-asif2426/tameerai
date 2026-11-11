"""
TameerAI - Contract Intelligence Endpoints (Phase 02E)

Endpoints for:
- GET    /api/v1/projects/{project_id}/contract-analyses (List analyses)
- POST   /api/v1/projects/{project_id}/contract-analyses (Create draft contract analysis)
- GET    /api/v1/projects/{project_id}/contract-analyses/{analysis_id} (Retrieve analysis details)
- DELETE /api/v1/projects/{project_id}/contract-analyses/{analysis_id} (Preserve audit trail - returns 409)
- GET    /api/v1/projects/{project_id}/contract-analyses/{analysis_id}/risk-cards (List risk cards)
- POST   /api/v1/projects/{project_id}/contract-analyses/{analysis_id}/risk-cards (Add risk card)
- GET    /api/v1/projects/{project_id}/contract-analyses/{analysis_id}/risk-cards/{card_id} (Retrieve risk card)
- DELETE /api/v1/projects/{project_id}/contract-analyses/{analysis_id}/risk-cards/{card_id} (Preserve trail - returns 409)
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
from app.schemas.contract import (
    ContractAnalysisCreate,
    ContractAnalysisRead,
    ContractRiskCardCreate,
    ContractRiskCardRead,
)
from app.services.contract_service import (
    create_contract_analysis,
    create_contract_risk_card,
    get_contract_analysis,
    get_contract_risk_card,
    list_contract_analyses,
    list_contract_risk_cards,
)

logger = logging.getLogger("tameerai.api.contracts")

router = APIRouter()


# ---------------------------------------------------------------------------
# Contract Analyses
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[ContractAnalysisRead],
    summary="List project contract analyses",
    description="Returns all contract analyses for the specified project. Requires project membership.",
)
async def list_analyses(
    analysis_status: Optional[str] = Query(None, alias="status", description="Filter by status: unprocessed, processing, completed, failed"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await list_contract_analyses(db, project_id=project.id, analysis_status=analysis_status)


@router.post(
    "",
    response_model=ContractAnalysisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft contract analysis",
    description="Initializes a draft contract analysis record. Document references are validated against project ownership.",
)
async def create_analysis(
    analysis_in: ContractAnalysisCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_contract_analysis(
        db,
        project_id=project.id,
        user_id=current_user.id,
        data=analysis_in,
    )


@router.get(
    "/{analysis_id}",
    response_model=ContractAnalysisRead,
    summary="Get contract analysis details",
    description="Retrieves a specific contract analysis by UUID. Enforces project workspace boundary.",
)
async def get_analysis(
    analysis_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    analysis = await get_contract_analysis(db, project_id=project.id, analysis_id=analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract analysis not found in this project.",
        )
    return analysis


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete contract analysis (Preservation Gate)",
    description="Public deletion is prohibited to preserve legal evidentiary integrity under FIDIC contract terms.",
)
async def delete_analysis(
    analysis_id: UUID,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    analysis = await get_contract_analysis(db, project_id=project.id, analysis_id=analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract analysis not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of contract analyses is strictly prohibited to preserve FIDIC legal audit trails.",
    )


# ---------------------------------------------------------------------------
# Contract Risk Cards
# ---------------------------------------------------------------------------

@router.get(
    "/{analysis_id}/risk-cards",
    response_model=List[ContractRiskCardRead],
    summary="List risk cards for contract analysis",
    description="Lists all flagged clause risk cards for a contract analysis.",
)
async def list_risk_cards(
    analysis_id: UUID,
    risk_level: Optional[str] = Query(None, description="Filter by risk level: high, medium, low"),
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    analysis = await get_contract_analysis(db, project_id=project.id, analysis_id=analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract analysis not found in this project.",
        )
    return await list_contract_risk_cards(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        risk_level=risk_level,
    )


@router.post(
    "/{analysis_id}/risk-cards",
    response_model=ContractRiskCardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create risk card for contract analysis",
    description="Records a new legal clause risk card with FIDIC citations and recommendations.",
)
async def create_risk_card(
    analysis_id: UUID,
    card_in: ContractRiskCardCreate,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    return await create_contract_risk_card(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        data=card_in,
    )


@router.get(
    "/{analysis_id}/risk-cards/{card_id}",
    response_model=ContractRiskCardRead,
    summary="Get risk card details",
    description="Retrieves a specific risk card by UUID or public code (e.g. RISK-001).",
)
async def get_risk_card(
    analysis_id: UUID,
    card_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_view_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    card = await get_contract_risk_card(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        card_identifier=card_id,
    )
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract risk card not found in this analysis.",
        )
    return card


@router.delete(
    "/{analysis_id}/risk-cards/{card_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete risk card (Preservation Gate)",
    description="Public deletion of risk cards is prohibited to preserve FIDIC legal claims documentation.",
)
async def delete_risk_card(
    analysis_id: UUID,
    card_id: str,
    project_data: Tuple[Project, str] = Depends(get_project_with_engineering_edit_access),
    db: AsyncSession = Depends(get_db),
):
    project, _ = project_data
    card = await get_contract_risk_card(
        db,
        project_id=project.id,
        analysis_id=analysis_id,
        card_identifier=card_id,
    )
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract risk card not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Deletion of contract risk cards is strictly prohibited to preserve legal evidentiary audit integrity.",
    )

