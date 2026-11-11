"""
TameerAI - Stage 2C Automated Collection Orchestration & Worker Tests
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.job import BackgroundJob, JobStatus, JobType
from app.models.material_rate import (
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateSourceRun,
)
from app.services.material_rates.contracts import (
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
    SourceOperationalStatus,
    SourceRunSummary,
)
from app.services.material_rates.orchestration import (
    ADAPTER_MAP,
    CollectionOrchestrator,
    MaterialRateCollectionService,
    SourceExecutionManager,
    SourceRunTracker,
    SourceScheduler,
)
from app.services.material_rates.registry import SourceRegistryEntry, national_registry
from app.workers.job_worker import (
    get_handler,
    material_rate_source_sync_handler,
    pbs_weekly_sync_handler,
    pbs_monthly_sync_handler,
    dealer_quote_expiry_handler,
    material_rate_verification_handler,
    material_rate_snapshot_refresh_handler,
)


@pytest.fixture
def sync_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class TestSourceSchedulerAndExecution:
    def test_scheduler_respects_global_gate(self):
        """Verifies automated collection is disabled by default."""
        assert SourceScheduler.is_collection_globally_enabled() is False
        entry = national_registry.get_source("PBS_STATISTICAL_SPI")
        assert entry is not None
        # When disabled and force is False, run is not due
        assert SourceScheduler.is_run_due(entry, None, force=False) is False
        # When force is True, run is due
        assert SourceScheduler.is_run_due(entry, None, force=True) is True

    def test_scheduler_cadence_calculation(self):
        """Verifies interval checks for daily, weekly, monthly sources."""
        entry = national_registry.get_source("STEELRATETODAY_PK_PUBLISHER")
        assert entry is not None

        # Simulate globally enabled
        orig_gate = getattr(settings, "ENABLE_MATERIAL_RATE_COLLECTION", False)
        try:
            settings.ENABLE_MATERIAL_RATE_COLLECTION = True
            # Never run before -> due
            assert SourceScheduler.is_run_due(entry, None) is True

            # Run 5 hours ago (Daily cadence requires 20 hours) -> not due
            recent = datetime.now(timezone.utc) - timedelta(hours=5)
            assert SourceScheduler.is_run_due(entry, recent) is False

            # Run 25 hours ago -> due
            stale = datetime.now(timezone.utc) - timedelta(hours=25)
            assert SourceScheduler.is_run_due(entry, stale) is True
        finally:
            settings.ENABLE_MATERIAL_RATE_COLLECTION = orig_gate

    @pytest.mark.asyncio
    async def test_execution_manager_concurrency_lock(self):
        """Verifies that concurrent runs for the same source are locked out."""
        mgr = SourceExecutionManager()
        source_code = "TEST_SOURCE_LOCK"

        # First acquisition succeeds
        acquired_1 = await mgr.acquire_source_lock(source_code)
        assert acquired_1 is True

        # Second acquisition fails
        acquired_2 = await mgr.acquire_source_lock(source_code)
        assert acquired_2 is False

        # Release and re-acquire
        await mgr.release_source_lock(source_code)
        acquired_3 = await mgr.acquire_source_lock(source_code)
        assert acquired_3 is True
        await mgr.release_source_lock(source_code)


class TestSourceRunTelemetry:
    @pytest.mark.asyncio
    async def test_run_tracker_lifecycle(self, sync_db_session: Session):
        """Verifies that SourceRunTracker logs execution duration, counts, and statuses."""
        source = MaterialRateSource(
            id=uuid.uuid4(),
            code="PBS_STATISTICAL_SPI",
            name="Pakistan Bureau of Statistics",
            source_type="official",
            base_url="https://pbs.gov.pk",
            is_active=True,
        )
        sync_db_session.add(source)
        sync_db_session.commit()

        # Start run
        run_record = await SourceRunTracker.start_run(sync_db_session, source)
        assert run_record.status == "running"
        assert run_record.records_discovered == 0

        # Finalize run
        summary = SourceRunSummary(
            source_id=source.id,
            source_code=source.code,
            status="completed",
            total_fetched=15,
            inserted_count=12,
            rejected_count=1,
            duplicate_count=2,
            metadata_snapshot={"test": "ok"},
        )
        finalized = await SourceRunTracker.finalize_run(sync_db_session, run_record.id, summary)

        assert finalized.status == "completed"
        assert finalized.records_discovered == 15
        assert finalized.records_accepted == 12
        assert finalized.records_rejected == 3  # rejected + duplicates
        assert finalized.finished_at is not None


class TestWorkerHandlerRegistrations:
    def test_all_handlers_registered(self):
        """Verifies that all Phase 02 job types have registered worker handlers."""
        assert get_handler(JobType.MATERIAL_RATE_SOURCE_SYNC.value) is not None
        assert get_handler(JobType.PBS_WEEKLY_SYNC.value) is not None
        assert get_handler(JobType.PBS_MONTHLY_SYNC.value) is not None
        assert get_handler(JobType.DEALER_QUOTE_EXPIRY.value) is not None
        assert get_handler(JobType.MATERIAL_RATE_VERIFICATION.value) is not None
        assert get_handler(JobType.MATERIAL_RATE_SNAPSHOT_REFRESH.value) is not None

    @pytest.mark.asyncio
    async def test_source_sync_handler_skips_when_gated(self, sync_db_session: Session):
        """Verifies that worker handler skips cleanly when feature gate is False."""
        job = BackgroundJob(
            id=uuid.uuid4(),
            job_type=JobType.MATERIAL_RATE_SOURCE_SYNC.value,
            status=JobStatus.RUNNING.value,
            payload={"source_code": "PBS_STATISTICAL_SPI", "force": False},
        )
        result = await material_rate_source_sync_handler(job, sync_db_session)
        assert result["status"] == "skipped"
        assert "disabled" in result["message"].lower()
