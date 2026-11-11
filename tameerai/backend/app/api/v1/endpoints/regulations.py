"""
TameerAI - Pakistan Statutory Regulatory Knowledge Base API Endpoints (Phase 03.3)

Endpoints:
- GET  /api/v1/regulations/authorities: List regulatory authorities
- GET  /api/v1/regulations/authorities/{code}: Get authority by code
- POST /api/v1/regulations/authorities/seed: Seed master authorities catalog
- GET  /api/v1/regulations/documents: List statutory documents
- GET  /api/v1/regulations/documents/{document_id}: Get document by ID
- GET  /api/v1/regulations/documents/{document_id}/versions: List versions
- GET  /api/v1/regulations/documents/{document_id}/clauses: List clauses for document
- GET  /api/v1/regulations/clauses/{clause_id}: Get clause by ID
- POST /api/v1/regulations/search: Jurisdiction-aware regulatory search (body)
- GET  /api/v1/regulations/search: Jurisdiction-aware search (query params)
- GET  /api/v1/regulations/safety-guidance: Statutory guidance for structural hazard codes
- GET  /api/v1/regulations/ingestion/{job_id}: Get ingestion job status
- POST /api/v1/regulations/reviews: Submit editorial/legal review
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user, get_db
from app.models.regulation import (
    RegulatoryAuthority,
    RegulatoryClause,
    RegulatoryDocument,
    RegulatoryDocumentVersion,
    RegulatoryIngestionJob,
    RegulatoryReviewRecord,
)
from app.models.user import User
from app.schemas.regulation import (
    RegulatoryAuthorityRead,
    RegulatoryClauseRead,
    RegulatoryDocumentRead,
    RegulatoryDocumentVersionRead,
    RegulatoryIngestionJobRead,
    RegulatoryReviewRecordCreate,
    RegulatoryReviewRecordRead,
    RegulatorySearchQuery,
    RegulatorySearchResponse,
)
from app.services.regulatory_discovery import RegulatoryDiscoveryService
from app.services.regulatory_retrieval import RegulatoryRetrievalService

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Regulatory Authorities Endpoints
# ---------------------------------------------------------------------------

@router.get("/authorities", response_model=List[RegulatoryAuthorityRead])
async def list_authorities(
    jurisdiction_level: Optional[str] = Query(None, description="federal, provincial, municipal, special_authority"),
    credibility_tier: Optional[str] = Query(None, description="tier_a_statutory, tier_b_official_regulatory, tier_c_recognized_technical, tier_d_secondary"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists active Pakistan regulatory authorities with optional jurisdiction and credibility filters.
    """
    return await RegulatoryDiscoveryService.list_authorities_async(
        db=db,
        jurisdiction_level=jurisdiction_level,
        credibility_tier=credibility_tier,
    )


@router.get("/authorities/{code}", response_model=RegulatoryAuthorityRead)
async def get_authority_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves authority details by short code (e.g. PEC, BCP_FED, LDA, SBCA, CDA).
    """
    authority = await RegulatoryDiscoveryService.get_authority_by_code_async(db=db, code=code)
    if not authority:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regulatory authority '{code.upper()}' not found.",
        )
    return authority


@router.post("/authorities/seed", response_model=List[RegulatoryAuthorityRead])
async def seed_authorities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Seeds standard master Pakistan regulatory authorities. Idempotent.
    """
    await RegulatoryDiscoveryService.seed_default_authorities_async(db=db)
    return await RegulatoryDiscoveryService.list_authorities_async(db=db)


# ---------------------------------------------------------------------------
# 2. Regulatory Documents Endpoints
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=List[RegulatoryDocumentRead])
async def list_documents(
    authority_code: Optional[str] = Query(None),
    jurisdiction_province: Optional[str] = Query(None),
    document_category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists statutory regulatory documents with optional filters.
    """
    stmt = (
        select(RegulatoryDocument)
        .options(joinedload(RegulatoryDocument.authority))
    )

    if authority_code:
        auth = await RegulatoryDiscoveryService.get_authority_by_code_async(db, authority_code)
        if auth:
            stmt = stmt.where(RegulatoryDocument.authority_id == auth.id)
        else:
            return []

    if jurisdiction_province:
        stmt = stmt.where(RegulatoryDocument.jurisdiction_province == jurisdiction_province)

    if document_category:
        stmt = stmt.where(RegulatoryDocument.document_category == document_category)

    if status_filter:
        stmt = stmt.where(RegulatoryDocument.status == status_filter)

    stmt = stmt.order_by(RegulatoryDocument.document_code.asc())
    res = await db.execute(stmt)
    return list(res.scalars().unique().all())


@router.get("/documents/{document_id}", response_model=RegulatoryDocumentRead)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves full details of a regulatory document.
    """
    stmt = (
        select(RegulatoryDocument)
        .options(joinedload(RegulatoryDocument.authority))
        .where(RegulatoryDocument.id == document_id)
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory document not found.",
        )
    return doc


@router.get("/documents/{document_id}/versions", response_model=List[RegulatoryDocumentVersionRead])
async def list_document_versions(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all editions and versions of a statutory document.
    """
    stmt = (
        select(RegulatoryDocumentVersion)
        .where(RegulatoryDocumentVersion.document_id == document_id)
        .order_by(RegulatoryDocumentVersion.created_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/documents/{document_id}/clauses", response_model=List[RegulatoryClauseRead])
async def list_document_clauses(
    document_id: uuid.UUID,
    version_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists parsed clauses for a document (defaults to current version).
    """
    target_version_id = version_id
    if not target_version_id:
        stmt_ver = select(RegulatoryDocumentVersion.id).where(
            RegulatoryDocumentVersion.document_id == document_id,
            RegulatoryDocumentVersion.is_current == True,
        )
        res_ver = await db.execute(stmt_ver)
        target_version_id = res_ver.scalars().first()

    if not target_version_id:
        return []

    stmt = (
        select(RegulatoryClause)
        .where(RegulatoryClause.version_id == target_version_id)
        .order_by(RegulatoryClause.page_start.asc(), RegulatoryClause.clause_number.asc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/clauses/{clause_id}", response_model=RegulatoryClauseRead)
async def get_clause(
    clause_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a single statutory clause with its metadata, tabular data, and formulas.
    """
    stmt = select(RegulatoryClause).where(RegulatoryClause.id == clause_id)
    res = await db.execute(stmt)
    clause = res.scalars().first()
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory clause not found.",
        )
    return clause


# ---------------------------------------------------------------------------
# 3. Regulatory Search & Retrieval Endpoints
# ---------------------------------------------------------------------------

@router.post("/search", response_model=RegulatorySearchResponse)
async def search_regulations_post(
    query_in: RegulatorySearchQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executes a jurisdiction-aware search across statutory regulations.
    Applies geographic boundaries (city, province) and legal significance ranking.
    """
    return await RegulatoryRetrievalService.search_async(db=db, query_in=query_in)


@router.get("/search", response_model=RegulatorySearchResponse)
async def search_regulations_get(
    q: str = Query(..., min_length=2, description="Search term"),
    city: Optional[str] = Query(None, description="e.g. Lahore, Karachi, Islamabad"),
    province: Optional[str] = Query(None, description="e.g. Punjab, Sindh, ICT"),
    authority: Optional[str] = Query(None, description="e.g. PEC, LDA, SBCA, CDA"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convenience GET endpoint for statutory search.
    """
    query_in = RegulatorySearchQuery(
        query=q,
        city=city,
        province=province,
        authority_codes=[authority] if authority else None,
        limit=limit,
        offset=offset,
    )
    return await RegulatoryRetrievalService.search_async(db=db, query_in=query_in)


@router.get("/safety-guidance")
async def get_regulatory_safety_guidance(
    hazard_code: str = Query(..., description="e.g. shear_cracks_columns, diy_column_removal"),
    city: Optional[str] = Query(None, description="Jurisdiction city"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves statutory regulatory provisions associated with a structural hazard code.
    Enforces strict structural safety boundary: does NOT override emergency advisories.
    """
    return await RegulatoryRetrievalService.get_regulatory_guidance_for_safety_async(
        db=db,
        hazard_code=hazard_code,
        city=city,
    )


# ---------------------------------------------------------------------------
# 4. Ingestion & Review Endpoints
# ---------------------------------------------------------------------------

@router.get("/ingestion/{job_id}", response_model=RegulatoryIngestionJobRead)
async def get_ingestion_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the status and metrics of a regulatory ingestion job.
    """
    stmt = select(RegulatoryIngestionJob).where(RegulatoryIngestionJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion job not found.",
        )
    return job


@router.post("/reviews", response_model=RegulatoryReviewRecordRead)
async def submit_regulatory_review(
    review_in: RegulatoryReviewRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits an attributable legal or engineering editorial review verdict.
    Requires engineer or admin role.
    """
    if current_user.role not in ("engineer", "admin", "consultant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only licensed engineers or authorized legal reviewers may submit regulatory review verdicts.",
        )

    review_record = RegulatoryReviewRecord(
        id=uuid.uuid4(),
        target_type=review_in.target_type,
        target_id=review_in.target_id,
        reviewer_id=current_user.id,
        review_verdict=review_in.review_verdict,
        notes=review_in.notes,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review_record)
    await db.commit()
    await db.refresh(review_record)
    return review_record
