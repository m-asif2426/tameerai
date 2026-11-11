"""
TameerAI - Material Rate Intelligence Endpoints (Phase 02 Complete API)

Endpoints:
- Products:
  - GET /api/v1/material-rates/products
- Sources & Telemetry:
  - GET /api/v1/material-rates/sources
  - GET /api/v1/material-rates/sources/telemetry
  - GET /api/v1/material-rates/sources/{source_code}/runs
- Market Snapshots:
  - GET /api/v1/material-rates/snapshots
- Historical Intelligence:
  - GET /api/v1/material-rates/history
  - GET /api/v1/material-rates/compare
- Dealers & Quotations:
  - POST /api/v1/material-rates/dealers
  - GET  /api/v1/material-rates/dealers
  - POST /api/v1/material-rates/dealers/quotes
  - GET  /api/v1/material-rates/dealers/quotes
  - POST /api/v1/material-rates/dealers/quotes/{quote_id}/evidence
  - GET  /api/v1/material-rates/dealers/quotes/{quote_id}/evidence
- Verification Audit:
  - GET /api/v1/material-rates/verification/{observation_id}
- Automated Collection Orchestration:
  - POST /api/v1/material-rates/orchestration/trigger
- Backward-Compatible Market Survey Routes:
  - GET /api/v1/material-rates
  - GET /api/v1/material-rates/{rate_id}
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user, get_db
from app.models.cost import MaterialRate
from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateSourceRun,
    MaterialRateVerificationEvent,
)
from app.models.user import User
from app.schemas.cost import MaterialRateRead
from app.schemas.material_rate import (
    CanonicalRateSnapshotRead,
    CrossCityComparisonResponse,
    DealerCreate,
    DealerQuoteCreate,
    DealerQuoteRead,
    DealerRead,
    EvidenceUploadResponse,
    MaterialRateProductCreate,
    MaterialRateProductRead,
    MaterialRateSourceRead,
    MaterialRateSourceRunRead,
    MaterialRateTelemetryRead,
    OrchestrationTriggerRequest,
    OrchestrationTriggerResponse,
    PriceHistoryResponse,
    VerificationEventRead,
)
from app.services.cost_service import (
    get_material_rate,
    list_material_rates,
)
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.dealer_service import (
    EvidenceStorageError,
    dealer_service,
)
from app.services.material_rates.historical_service import historical_service
from app.services.material_rates.orchestration import (
    SourceExecutionError,
    collection_service,
)
from app.services.material_rates.registry import national_registry

logger = logging.getLogger("tameerai.api.material_rates")

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Product Catalog Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/products",
    response_model=List[MaterialRateProductRead],
    summary="List canonical construction material products",
    description="Returns canonical product specifications across Pakistani construction markets.",
)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category (cement, steel, bricks, sand, crush, blocks, tiles)"),
    is_active: bool = Query(True, description="Filter active products"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    stmt = select(MaterialRateProduct).where(MaterialRateProduct.is_active == is_active)
    if category:
        stmt = stmt.where(MaterialRateProduct.category == category.lower())
    stmt = stmt.order_by(MaterialRateProduct.category.asc(), MaterialRateProduct.canonical_name.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# 2. Source Registry & Telemetry Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/sources",
    response_model=List[MaterialRateSourceRead],
    summary="List registered construction material pricing sources",
    description="Returns registered official, marketplace, and publisher sources.",
)
async def list_sources(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    stmt = select(MaterialRateSource).order_by(MaterialRateSource.name.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get(
    "/sources/telemetry",
    response_model=MaterialRateTelemetryRead,
    summary="Get collection run telemetry and health metrics",
    description="Returns aggregate counts of runs, accepted, duplicate, and rejected observations.",
)
async def get_telemetry(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return await collection_service.get_collection_telemetry(db)


@router.get(
    "/sources/{source_code}/runs",
    response_model=List[MaterialRateSourceRunRead],
    summary="Get execution run history for a specific source",
    description="Returns recent execution telemetry and metrics for an individual data source.",
)
async def get_source_runs(
    source_code: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    stmt = (
        select(MaterialRateSourceRun)
        .join(MaterialRateSource, MaterialRateSourceRun.source_id == MaterialRateSource.id)
        .where(MaterialRateSource.code == source_code)
        .order_by(desc(MaterialRateSourceRun.started_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# 3. Market Snapshots & Benchmarks
# ---------------------------------------------------------------------------

@router.get(
    "/snapshots",
    response_model=List[CanonicalRateSnapshotRead],
    summary="Get canonical market rate snapshots across cities",
    description="Computes point-in-time benchmark market rates with multi-factor confidence and price spread.",
)
async def get_snapshots(
    city: Optional[str] = Query("Lahore", description="Target city: Lahore, Karachi, Islamabad, Rawalpindi, Peshawar, Multan"),
    category: Optional[str] = Query(None, description="Optional category filter: cement, steel, bricks, sand, crush"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    stmt = select(MaterialRateProduct).where(MaterialRateProduct.is_active.is_(True))
    if category:
        stmt = stmt.where(MaterialRateProduct.category == category.lower())
    stmt = stmt.order_by(MaterialRateProduct.canonical_name.asc())
    prod_res = await db.execute(stmt)
    products = list(prod_res.scalars().all())

    snapshots = []
    for prod in products:
        snap = await canonical_engine.compute_canonical_rate_for_product_and_city(db, prod, city)
        if snap:
            snapshots.append(snap.to_dict())

    return snapshots


# ---------------------------------------------------------------------------
# 4. Historical Market Intelligence Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=PriceHistoryResponse,
    summary="Get historical price time-series and volatility",
    description="Returns time-series aggregations (daily, weekly, monthly medians) and statistical volatility.",
)
async def get_price_history_endpoint(
    product_code: str = Query(..., description="Canonical product code (e.g. CEMENT_OPC_50KG, STEEL_REBAR_G60_TON)"),
    city: Optional[str] = Query(None, description="Target city filter"),
    interval: str = Query("daily", description="Aggregation interval: daily, weekly, monthly"),
    days: int = Query(90, ge=7, le=365, description="Lookback window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(days=days)
    try:
        return await historical_service.get_price_history(
            db,
            product_code=product_code,
            city=city,
            start_date=start_dt,
            end_date=now,
            interval=interval,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/compare",
    response_model=CrossCityComparisonResponse,
    summary="Compare product pricing across Pakistani cities",
    description="Calculates geographic price parity and city-specific variances against national median.",
)
async def compare_cities_endpoint(
    product_code: str = Query(..., description="Canonical product code"),
    cities: Optional[List[str]] = Query(None, description="List of cities to compare (defaults to provincial capitals)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    try:
        return await historical_service.compare_cities(
            db,
            product_code=product_code,
            cities=cities,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# 5. Dealers & Direct Quotations Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/dealers",
    response_model=DealerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new building material dealer",
    description="Registers a new verified merchant profile.",
)
async def register_dealer(
    payload: DealerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await dealer_service.register_dealer(
            db,
            business_name=payload.business_name,
            dealer_code=payload.dealer_code,
            city=payload.city,
            market_area=payload.market_area,
            address=payload.address,
            contact_person=payload.contact_person,
            contact_phone=payload.contact_phone,
            ntn_number=payload.ntn_number,
            user_id=current_user.id,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/dealers",
    response_model=List[DealerRead],
    summary="List registered dealers",
    description="Returns vetted building material merchants and distributors.",
)
async def list_dealers(
    city: Optional[str] = Query(None, description="Filter by city"),
    verification_state: Optional[str] = Query(None, description="Filter by state: unverified, verified, suspended"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(MaterialRateDealer).where(MaterialRateDealer.is_active.is_(True))
    if city:
        stmt = stmt.where(MaterialRateDealer.city.ilike(f"%{city}%"))
    if verification_state:
        stmt = stmt.where(MaterialRateDealer.verification_state == verification_state)
    stmt = stmt.order_by(MaterialRateDealer.business_name.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post(
    "/dealers/quotes",
    response_model=DealerQuoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a commercial dealer quotation",
    description="Records a merchant quotation with canonical unit/price normalization and immutable observation link.",
)
async def submit_quote(
    payload: DealerQuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await dealer_service.submit_quotation(
            db,
            dealer_id=payload.dealer_id,
            product_id=payload.product_id,
            quoted_price_pkr=payload.quoted_price_pkr,
            quoted_unit=payload.quoted_unit,
            city=payload.city,
            validity_days=payload.validity_days,
            minimum_order_quantity=payload.minimum_order_quantity,
            delivery_charges_pkr=payload.delivery_charges_pkr,
            tax_included=payload.tax_included,
            payment_terms=payload.payment_terms,
            vehicle_capacity_cft=payload.vehicle_capacity_cft,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/dealers/quotes",
    response_model=List[DealerQuoteRead],
    summary="List active dealer quotations",
    description="Returns recent merchant quotations across materials and cities.",
)
async def list_quotes(
    city: Optional[str] = Query(None, description="Filter by city"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending_review, verified, expired"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(MaterialRateDealerQuote)
    if city:
        stmt = stmt.where(MaterialRateDealerQuote.city.ilike(f"%{city}%"))
    if status_filter:
        stmt = stmt.where(MaterialRateDealerQuote.status == status_filter)
    stmt = stmt.order_by(desc(MaterialRateDealerQuote.created_at)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post(
    "/dealers/quotes/{quote_id}/evidence",
    response_model=EvidenceUploadResponse,
    summary="Upload documentary evidence for a quotation",
    description="Uploads quote slip, invoice, or receipt with SHA-256 integrity verification.",
)
async def upload_quote_evidence(
    quote_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = await db.scalar(
        select(MaterialRateDealerQuote).where(MaterialRateDealerQuote.id == quote_id)
    )
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found")

    content = await file.read()
    try:
        rel_path, sha_hash, fsize = dealer_service.evidence_manager.save_evidence_file(
            dealer_id=quote.dealer_id,
            quote_id=quote.id,
            filename=file.filename or "evidence.pdf",
            content_type=file.content_type or "application/pdf",
            file_bytes=content,
        )
    except EvidenceStorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    quote.evidence_file_path = rel_path
    quote.evidence_file_name = file.filename
    quote.evidence_content_type = file.content_type
    quote.evidence_file_size_bytes = fsize
    quote.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(quote)

    token = dealer_service.evidence_manager.generate_signed_token(rel_path)

    return EvidenceUploadResponse(
        quote_id=quote.id,
        filename=file.filename or "evidence",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=fsize,
        storage_path=rel_path,
        signed_download_token=token,
        message="Evidence uploaded and cryptographically hashed successfully.",
    )


@router.get(
    "/dealers/quotes/{quote_id}/evidence",
    summary="Download quotation evidence file",
    description="Securely streams private quotation evidence using a signed authorization token.",
)
async def download_quote_evidence(
    quote_id: UUID,
    token: str = Query(..., description="HMAC-SHA256 signed access token"),
    db: AsyncSession = Depends(get_db),
):
    quote = await db.scalar(
        select(MaterialRateDealerQuote).where(MaterialRateDealerQuote.id == quote_id)
    )
    if not quote or not quote.evidence_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found for quotation")

    if not dealer_service.evidence_manager.verify_signed_token(quote.evidence_file_path, token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired access token")

    full_path = dealer_service.evidence_manager.get_full_file_path(quote.evidence_file_path)
    if not full_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical evidence file missing")

    return FileResponse(
        path=str(full_path),
        media_type=quote.evidence_content_type or "application/octet-stream",
        filename=quote.evidence_file_name or "evidence",
    )


# ---------------------------------------------------------------------------
# 6. Verification Audit Trail Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/verification/{observation_id}",
    response_model=List[VerificationEventRead],
    summary="Get verification audit trail for an observation",
    description="Returns explainable verification events and deterministic decision rules for an observation.",
)
async def get_verification_events(
    observation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(MaterialRateVerificationEvent)
        .where(MaterialRateVerificationEvent.observation_id == observation_id)
        .order_by(desc(MaterialRateVerificationEvent.created_at))
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# 7. Automated Collection Orchestration Trigger
# ---------------------------------------------------------------------------

@router.post(
    "/orchestration/trigger",
    response_model=OrchestrationTriggerResponse,
    summary="Trigger on-demand data collection run for a source",
    description="Executes a controlled collection run with safe HTTP limits and immutable observation persistence.",
)
async def trigger_collection(
    payload: OrchestrationTriggerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        summary = await collection_service.run_source_collection(
            db,
            payload.source_code,
            force=payload.force,
        )
        return OrchestrationTriggerResponse(
            source_code=summary.source_code,
            status=summary.status,
            records_discovered=summary.total_fetched,
            records_accepted=summary.inserted_count,
            records_rejected=summary.rejected_count,
            duplicates_detected=summary.duplicate_count,
            error_message=summary.error_message,
        )
    except SourceExecutionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to execute collection trigger: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Collection execution failed")


# ---------------------------------------------------------------------------
# 8. Backward-Compatible Market Survey Routes
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[MaterialRateRead],
    summary="List market survey material rates",
    description="Returns verified and surveyed material quotes for major cities (Lahore, Karachi, Islamabad).",
)
async def list_rates_backward_compat(
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


@router.get(
    "/{rate_id}",
    response_model=MaterialRateRead,
    summary="Get material rate details",
    description="Retrieves a specific commodity or labor rate quote by UUID.",
)
async def get_rate_backward_compat(
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
