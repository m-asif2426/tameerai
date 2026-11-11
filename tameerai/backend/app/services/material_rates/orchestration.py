"""
TameerAI - Automated Material Rate Collection Orchestrator (Stage 2C)

Implements:
1. CollectionOrchestrator: Dispatches, executes, and audits data adapter runs.
2. SourceScheduler: Timezone-aware schedules (daily, weekly, monthly, on-demand).
   Controlled by settings.ENABLE_MATERIAL_RATE_COLLECTION (default: False).
3. SourceExecutionManager: Concurrency limits, timeouts, and execution cooldowns.
4. SourceRunTracker: Durable telemetry accounting (discovered, accepted, rejected, duplicates).
5. Transaction Boundary Safety: No database row locks held during external HTTP network requests.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple, Type
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security_redaction import sanitize_sensitive_details
from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateObservation,
    MaterialRateSourceRun,
)
from app.services.material_rates.base_adapter import BaseSourceAdapter
from app.services.material_rates.contracts import (
    CollectionSourceType,
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
    SourceOperationalStatus,
    SourceRunSummary,
)
from app.services.material_rates.registry import (
    NationalSourceRegistry,
    SourceRegistryEntry,
    national_registry,
)
from app.services.material_rates.adapters.pbs_adapter import PbsStatisticalSourceAdapter
from app.services.material_rates.adapters.nha_schedule_adapter import NhaScheduleSourceAdapter
from app.services.material_rates.adapters.zarea_adapter import ZareaMarketplaceSourceAdapter
from app.services.material_rates.adapters.materialrate_adapter import MaterialRatePublisherSourceAdapter
from app.services.material_rates.adapters.steelratetoday_adapter import SteelRateTodaySourceAdapter
from app.services.material_rates.adapters.gharhub_adapter import GharHubPublisherSourceAdapter
from app.services.material_rates.adapters.dealer_connector import DirectDealerConnector

logger = logging.getLogger("tameerai.material_rates.orchestration")


# Map registered source codes to adapter implementations
ADAPTER_MAP: Dict[str, Type[BaseSourceAdapter]] = {
    "PBS_STATISTICAL_SPI": PbsStatisticalSourceAdapter,
    "NHA_CSR_SCHEDULE": NhaScheduleSourceAdapter,
    "ZAREA_B2B_MARKETPLACE": ZareaMarketplaceSourceAdapter,
    "MATERIALRATE_PK_PUBLISHER": MaterialRatePublisherSourceAdapter,
    "STEELRATETODAY_PK_PUBLISHER": SteelRateTodaySourceAdapter,
    "GHARHUB_PK_PUBLISHER": GharHubPublisherSourceAdapter,
    "DIRECT_DEALER_QUOTATION": DirectDealerConnector,
}


class SourceExecutionError(Exception):
    """Raised when an adapter run fails execution or safety checks."""
    pass


class SourceScheduler:
    """
    Evaluates whether a source collection is due based on update cadence.
    Strictly gates automated execution behind settings.ENABLE_MATERIAL_RATE_COLLECTION.
    """

    CADENCE_INTERVALS = {
        "Daily": timedelta(hours=20),
        "Weekly": timedelta(days=6),
        "Monthly": timedelta(days=25),
        "On-Demand / Transactional": None,
    }

    @classmethod
    def is_collection_globally_enabled(cls) -> bool:
        """Returns whether background collection is enabled via feature flag."""
        return getattr(settings, "ENABLE_MATERIAL_RATE_COLLECTION", False)

    @classmethod
    def is_run_due(
        cls,
        source_entry: SourceRegistryEntry,
        last_completed_at: Optional[datetime],
        force: bool = False,
    ) -> bool:
        """Determines if a collection run should be executed."""
        if force:
            return True

        if not cls.is_collection_globally_enabled():
            return False

        if source_entry.operational_status in (
            SourceOperationalStatus.INACCESSIBLE,
            SourceOperationalStatus.REJECTED,
            SourceOperationalStatus.RESTRICTED,
        ):
            return False

        if last_completed_at is None:
            return True

        interval = cls.CADENCE_INTERVALS.get(source_entry.update_cadence)
        if interval is None:
            return False

        now = datetime.now(timezone.utc)
        if last_completed_at.tzinfo is None:
            last_completed_at = last_completed_at.replace(tzinfo=timezone.utc)

        return (now - last_completed_at) >= interval


class SourceExecutionManager:
    """Manages runtime locks and timeouts to prevent concurrent duplicate executions."""

    def __init__(self):
        self._active_runs: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def acquire_source_lock(self, source_code: str) -> bool:
        """Attempts to acquire exclusive in-memory execution lock for a source."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            if source_code in self._active_runs:
                started_at = self._active_runs[source_code]
                # Stale lock timeout: 10 minutes
                if (now - started_at) < timedelta(minutes=10):
                    return False
            self._active_runs[source_code] = now
            return True

    async def release_source_lock(self, source_code: str) -> None:
        """Releases the execution lock for a source."""
        async with self._lock:
            self._active_runs.pop(source_code, None)


# Global singleton manager
execution_manager = SourceExecutionManager()


class SourceRunTracker:
    """Records and updates persistent execution telemetry for material rate source runs."""

    @staticmethod
    async def start_run(
        db: Any,
        source: MaterialRateSource,
        background_job_id: Optional[uuid.UUID] = None,
    ) -> MaterialRateSourceRun:
        """Creates an initial source run record in 'running' status."""
        run = MaterialRateSourceRun(
            id=uuid.uuid4(),
            source_id=source.id,
            background_job_id=background_job_id,
            status="running",
            records_discovered=0,
            records_accepted=0,
            records_rejected=0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(run)
        else:
            db.commit()
            db.refresh(run)
        return run

    @staticmethod
    async def finalize_run(
        db: Any,
        run_id: uuid.UUID,
        summary: SourceRunSummary,
    ) -> MaterialRateSourceRun:
        """Updates a source run with final metrics and status."""
        if isinstance(db, AsyncSession):
            res = await db.execute(select(MaterialRateSourceRun).where(MaterialRateSourceRun.id == run_id))
            run = res.scalar_one_or_none()
        else:
            run = db.query(MaterialRateSourceRun).filter(MaterialRateSourceRun.id == run_id).first()

        if not run:
            raise SourceExecutionError(f"Source run {run_id} not found for finalization")

        now = datetime.now(timezone.utc)
        duration = None
        started = run.started_at
        if started:
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            duration = Decimal(str(round((now - started).total_seconds(), 2)))

        run.status = summary.status
        run.records_discovered = summary.total_fetched
        run.records_accepted = summary.inserted_count
        run.records_rejected = summary.rejected_count + summary.duplicate_count
        run.duration_seconds = duration
        run.finished_at = now
        if summary.error_message:
            run.error_summary = sanitize_sensitive_details(summary.error_message)[:1000]

        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(run)
        else:
            db.commit()
            db.refresh(run)
        return run


class CollectionOrchestrator:
    """
    Coordinates end-to-end data extraction, normalization, and persistence.
    Enforces transaction boundary safety:
    - External HTTP calls are executed entirely OUTSIDE database transactions.
    - Database transactions are kept ultra-short (claiming, persisting observations, finalization).
    """

    def __init__(self, registry: Optional[NationalSourceRegistry] = None):
        self.registry = registry or national_registry

    def get_adapter_instance(self, source_code: str) -> BaseSourceAdapter:
        """Instantiates the appropriate source adapter for a registered source code."""
        adapter_cls = ADAPTER_MAP.get(source_code)
        if not adapter_cls:
            raise SourceExecutionError(f"No adapter implementation registered for '{source_code}'")

        entry = self.registry.get_source(source_code)
        base_url = entry.base_url if entry else None

        if base_url:
            return adapter_cls(base_url=base_url)
        return adapter_cls()

    async def get_or_create_source_db_record(
        self,
        db: Any,
        source_code: str,
    ) -> MaterialRateSource:
        """Ensures the source entity exists in the material_rate_sources database table."""
        if isinstance(db, AsyncSession):
            res = await db.execute(select(MaterialRateSource).where(MaterialRateSource.code == source_code))
            source = res.scalar_one_or_none()
        else:
            source = db.query(MaterialRateSource).filter(MaterialRateSource.code == source_code).first()

        if source:
            return source

        entry = self.registry.get_source(source_code)
        if not entry:
            raise SourceExecutionError(f"Source '{source_code}' is not in the national registry")

        source = MaterialRateSource(
            id=uuid.uuid4(),
            code=entry.source_code,
            name=entry.name,
            source_type=entry.category.value if hasattr(entry.category, "value") else str(entry.category),
            permission_status="permitted",
            reliability_tier="verified" if entry.operational_status == SourceOperationalStatus.VERIFIED_CURRENT else "indicative",
            refresh_cadence="daily" if entry.update_cadence == "Daily" else ("weekly" if entry.update_cadence == "Weekly" else "monthly"),
            freshness_ttl_days=30,
            base_url=entry.base_url,
            is_active=(entry.operational_status in (SourceOperationalStatus.VERIFIED_CURRENT, SourceOperationalStatus.VERIFIED_HISTORICAL)),
        )
        db.add(source)
        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(source)
        else:
            db.commit()
            db.refresh(source)
        return source

    async def execute_source_run(
        self,
        db: Any,
        source_code: str,
        *,
        background_job_id: Optional[uuid.UUID] = None,
        category_hint: Optional[str] = None,
        force: bool = False,
        raw_payload_override: Optional[Any] = None,
    ) -> SourceRunSummary:
        """
        Executes a complete collection run for a single source.
        1. Acquire in-memory concurrency lock.
        2. Ensure DB source record exists.
        3. Check schedule due status.
        4. Start run tracking record.
        5. Fetch raw data over HTTP (OUTSIDE DB transaction).
        6. Parse, normalize, deduplicate, and persist observations (in short DB transaction).
        7. Finalize run tracking record.
        8. Release lock.
        """
        entry = self.registry.get_source(source_code)
        if not entry:
            raise SourceExecutionError(f"Unknown source code '{source_code}'")

        # 1. Acquire runtime lock
        acquired = await execution_manager.acquire_source_lock(source_code)
        if not acquired and not force:
            logger.warning("Execution for source '%s' skipped: concurrent run active", source_code)
            return SourceRunSummary(
                source_id=uuid.uuid4(),
                source_code=source_code,
                status="skipped",
                error_message="Concurrent execution active",
            )

        try:
            # 2. Get/create source DB record (short transaction)
            source = await self.get_or_create_source_db_record(db, source_code)

            # 3. Schedule check
            if isinstance(db, AsyncSession):
                res = await db.execute(
                    select(MaterialRateSourceRun)
                    .where(MaterialRateSourceRun.source_id == source.id, MaterialRateSourceRun.status == "completed")
                    .order_by(desc(MaterialRateSourceRun.completed_at))
                )
                last_run = res.scalars().first()
            else:
                last_run = (
                    db.query(MaterialRateSourceRun)
                    .filter(MaterialRateSourceRun.source_id == source.id, MaterialRateSourceRun.status == "completed")
                    .order_by(desc(MaterialRateSourceRun.completed_at))
                    .first()
                )
            last_completed_at = last_run.completed_at if last_run else None

            if not SourceScheduler.is_run_due(entry, last_completed_at, force=force):
                logger.info("Source '%s' is not due for collection. Skipping.", source_code)
                return SourceRunSummary(
                    source_id=source.id,
                    source_code=source_code,
                    status="skipped",
                    error_message="Collection not due or globally disabled",
                )

            # 4. Start run record (short transaction)
            run_record = await SourceRunTracker.start_run(db, source, background_job_id=background_job_id)

            adapter = self.get_adapter_instance(source_code)

            # 5. Execute Run through Adapter
            try:
                summary = await adapter.execute_run(
                    db,
                    background_job_id=background_job_id,
                    category_hint=category_hint,
                    raw_payload_override=raw_payload_override,
                )
            except Exception as exc:
                sanitized_msg = sanitize_sensitive_details(str(exc))
                logger.error("Adapter '%s' execution failed: %s", source_code, sanitized_msg)
                summary = SourceRunSummary(
                    source_id=source.id,
                    source_code=source_code,
                    status="failed",
                    error_message=sanitized_msg,
                )

            # 6. Finalize run record (short transaction)
            await SourceRunTracker.finalize_run(db, run_record.id, summary)
            return summary

        finally:
            await execution_manager.release_source_lock(source_code)


class MaterialRateCollectionService:
    """High-level facade for collection management, manual triggers, and health monitoring."""

    def __init__(self, orchestrator: Optional[CollectionOrchestrator] = None):
        self.orchestrator = orchestrator or CollectionOrchestrator()

    async def run_source_collection(
        self,
        db: Any,
        source_code: str,
        *,
        background_job_id: Optional[uuid.UUID] = None,
        force: bool = False,
        raw_payload_override: Optional[Any] = None,
    ) -> SourceRunSummary:
        """Executes collection for a specified source."""
        return await self.orchestrator.execute_source_run(
            db,
            source_code,
            background_job_id=background_job_id,
            force=force,
            raw_payload_override=raw_payload_override,
        )

    async def run_all_due_collections(
        self,
        db: Any,
        *,
        force: bool = False,
    ) -> List[SourceRunSummary]:
        """Iterates all registered sources and executes due collections."""
        results: List[SourceRunSummary] = []
        sources = national_registry.list_sources()

        for s in sources:
            # Skip candidate/restricted/inaccessible sources in automated runs unless forced
            if not force and s.operational_status != SourceOperationalStatus.VERIFIED_CURRENT:
                continue

            try:
                summary = await self.orchestrator.execute_source_run(
                    db,
                    s.source_code,
                    force=force,
                )
                results.append(summary)
            except Exception as e:
                logger.error("Error executing collection for '%s': %s", s.source_code, str(e))
                results.append(
                    SourceRunSummary(
                        source_id=uuid.uuid4(),
                        source_code=s.source_code,
                        status="failed",
                        error_message=sanitize_sensitive_details(str(e)),
                    )
                )

        return results

    async def get_collection_telemetry(self, db: Any) -> Dict[str, Any]:
        """Computes aggregate collection run statistics and source health."""
        if isinstance(db, AsyncSession):
            total_runs = (await db.execute(select(func.count(MaterialRateSourceRun.id)))).scalar() or 0
            total_accepted = (await db.execute(select(func.sum(MaterialRateSourceRun.records_accepted)))).scalar() or 0
            total_rejected = (await db.execute(select(func.sum(MaterialRateSourceRun.records_rejected)))).scalar() or 0

            res = await db.execute(
                select(MaterialRateSourceRun)
                .order_by(desc(MaterialRateSourceRun.started_at))
                .limit(10)
            )
            recent_runs = res.scalars().all()
        else:
            total_runs = db.query(func.count(MaterialRateSourceRun.id)).scalar() or 0
            total_accepted = db.query(func.sum(MaterialRateSourceRun.records_accepted)).scalar() or 0
            total_rejected = db.query(func.sum(MaterialRateSourceRun.records_rejected)).scalar() or 0

            recent_runs = (
                db.query(MaterialRateSourceRun)
                .order_by(desc(MaterialRateSourceRun.started_at))
                .limit(10)
                .all()
            )

        return {
            "total_runs": total_runs,
            "total_records_accepted": int(total_accepted),
            "total_duplicates_detected": 0,
            "total_records_rejected": int(total_rejected),
            "collection_enabled": SourceScheduler.is_collection_globally_enabled(),
            "recent_runs": [
                {
                    "id": str(r.id),
                    "source_id": str(r.source_id),
                    "status": r.status,
                    "records_discovered": r.records_discovered,
                    "records_accepted": r.records_accepted,
                    "duration_seconds": float(r.duration_seconds) if r.duration_seconds else None,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                }
                for r in recent_runs
            ],
        }


# Global singleton service
collection_service = MaterialRateCollectionService()
