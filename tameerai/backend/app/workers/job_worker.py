"""
TameerAI - Background Job Worker Engine & Concurrency Handler (Phase 02G)

Implements:
- Standalone asynchronous worker process with bounded concurrency
- Atomic job claiming via PostgreSQL FOR UPDATE SKIP LOCKED
- Crash recovery and expired lease reclamation
- Worker heartbeats and lease renewal
- Bounded exponential backoff retries for transient failures
- Terminal state handling for permanent failures
- Sensitive information redaction in error messages
- Graceful shutdown signal handling
"""

import asyncio
import logging
import os
import re
import socket
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.job import BackgroundJob, JobStatus, JobType

logger = logging.getLogger("tameerai.job_worker")


# ---------------------------------------------------------------------------
# Exceptions & Failure Classes
# ---------------------------------------------------------------------------

class JobExecutionError(Exception):
    """Standard retryable job execution failure."""
    pass


class NonRetryableJobError(Exception):
    """Permanent job failure that should not be retried."""
    pass


# ---------------------------------------------------------------------------
# Sensitive Error Redaction
# ---------------------------------------------------------------------------

REDACTION_PATTERNS = [
    # Database URIs
    (re.compile(r"(?:postgresql|postgres|sqlite|mysql)\+?[a-z]*://[^\s@]+@[^\s/]+/[^\s]+", re.IGNORECASE), "[REDACTED_DB_URI]"),
    (re.compile(r"(?:postgresql|postgres|sqlite|mysql)\+?[a-z]*://[^\s]+", re.IGNORECASE), "[REDACTED_DB_URI]"),
    # Windows absolute paths (including paths with spaces)
    (re.compile(r"[A-Za-z]:\\(?:[^<>:\"/|?*\r\n]+\\)*[^<>:\"/|?*;\r\n.]+\.[a-zA-Z0-9]+", re.IGNORECASE), "[REDACTED_PATH]"),
    (re.compile(r"[A-Za-z]:\\[^\r\n:;,\"]+", re.IGNORECASE), "[REDACTED_PATH]"),
    # Unix absolute paths
    (re.compile(r"/(?:Users|home|var|tmp|etc|app|root)[^\r\n:;,\"]+"), "[REDACTED_PATH]"),
    # Secrets, tokens, passwords, keys
    (re.compile(r"(?:password|secret|token|bearer|api_key|service_role)[=:\s]+[^\s,;]+", re.IGNORECASE), "[REDACTED_CREDENTIAL]"),
    # Python traceback line references
    (re.compile(r'File ".*?", line \d+.*'), "[STACK_TRACE_LINE_REDACTED]"),
]


from app.core.security_redaction import sanitize_sensitive_details


def sanitize_error_message(raw_error: str) -> str:
    """
    Strips file paths, credentials, connection strings, and stack trace lines
    from error descriptions to prevent information leakage in job records.
    Uses centralized multi-pass security redaction.
    """
    if not raw_error:
        return "Unknown error"
    return sanitize_sensitive_details(raw_error)[:1000]


# ---------------------------------------------------------------------------
# Handler Registry
# ---------------------------------------------------------------------------

JobHandler = Callable[[BackgroundJob, AsyncSession], Awaitable[Dict[str, Any]]]
_HANDLERS: Dict[str, JobHandler] = {}


def register_handler(job_type: str, handler: JobHandler) -> None:
    """Registers an approved asynchronous execution handler for a job type."""
    _HANDLERS[job_type] = handler
    logger.info("Registered background job handler for '%s'", job_type)


def get_handler(job_type: str) -> Optional[JobHandler]:
    """Retrieves the execution handler for the specified job type."""
    return _HANDLERS.get(job_type)


# ---------------------------------------------------------------------------
# Default Synthetic Test Handler (Safe for local/test verification)
# ---------------------------------------------------------------------------

async def synthetic_test_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """
    Deterministic synthetic test handler for verifying worker mechanics:
    - Supports simulated duration: payload.get('sleep_seconds')
    - Supports simulated retryable error: payload.get('fail_retryable')
    - Supports simulated permanent error: payload.get('fail_permanent')
    """
    payload = job.payload or {}

    if payload.get("fail_permanent"):
        raise NonRetryableJobError(
            f"Permanent failure simulated for job {job.id}: {payload.get('error_reason', 'Corrupt payload')}"
        )

    if payload.get("fail_retryable"):
        raise JobExecutionError(
            f"Transient network glitch simulated for job {job.id} (attempt {job.attempt_count})"
        )

    sleep_sec = payload.get("sleep_seconds", 0)
    if sleep_sec > 0:
        await asyncio.sleep(min(sleep_sec, 5))

    return {
        "processed": True,
        "job_id": str(job.id),
        "job_type": job.job_type,
        "attempts": job.attempt_count,
        "message": "Synthetic test workload completed successfully.",
    }

# Register default synthetic handler only in test/development environments if enabled
if settings.ENVIRONMENT.lower() in {"development", "test", "local"} and settings.ENABLE_SYNTHETIC_JOBS:
    register_handler(JobType.SYNTHETIC_TEST.value, synthetic_test_handler)


# ---------------------------------------------------------------------------
# Material Rate Intelligence Background Job Handlers (Phase 02 Stage 2C-2G)
# ---------------------------------------------------------------------------

async def material_rate_source_sync_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """
    Executes automated or manual material rate source collection for a single source.
    Safely gates automated runs behind settings.ENABLE_MATERIAL_RATE_COLLECTION.
    """
    from app.services.material_rates.orchestration import collection_service, SourceScheduler
    
    payload = job.payload or {}
    source_code = payload.get("source_code")
    force = payload.get("force", False)
    category_hint = payload.get("category_hint")

    if not source_code:
        raise NonRetryableJobError(f"Missing mandatory 'source_code' in job payload for job {job.id}")

    if not SourceScheduler.is_collection_globally_enabled() and not force:
        return {
            "status": "skipped",
            "source_code": source_code,
            "message": "Material rate collection is globally disabled (ENABLE_MATERIAL_RATE_COLLECTION=False)",
        }

    try:
        summary = await collection_service.run_source_collection(
            db,
            source_code,
            background_job_id=job.id,
            force=force,
        )
        return {
            "status": summary.status,
            "source_code": summary.source_code,
            "records_discovered": summary.total_fetched,
            "records_accepted": summary.inserted_count,
            "records_rejected": summary.rejected_count,
            "duplicates_detected": summary.duplicate_count,
            "error_message": summary.error_message,
        }
    except Exception as exc:
        raise JobExecutionError(f"Source sync failed for '{source_code}': {str(exc)}") from exc


async def pbs_weekly_sync_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """Syncs weekly statistical price index from Pakistan Bureau of Statistics."""
    payload = dict(job.payload or {})
    payload["source_code"] = "PBS_STATISTICAL_SPI"
    job.payload = payload
    return await material_rate_source_sync_handler(job, db)


async def pbs_monthly_sync_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """Syncs monthly construction item statistics from Pakistan Bureau of Statistics."""
    payload = dict(job.payload or {})
    payload["source_code"] = "PBS_STATISTICAL_SPI"
    payload["category_hint"] = "cement"
    job.payload = payload
    return await material_rate_source_sync_handler(job, db)


async def dealer_quote_expiry_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """Sweeps and transitions expired dealer quotations past their validity window."""
    from app.services.material_rates.dealer_service import dealer_service
    expired_count = await dealer_service.sweep_expired_quotes(db)
    return {
        "status": "completed",
        "expired_quotes_count": expired_count,
        "message": f"Successfully swept and marked {expired_count} expired quotations",
    }


async def material_rate_verification_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """Executes multi-source cross-checking and verification rules across candidate observations."""
    from app.services.material_rates.verification import verification_engine
    result = await verification_engine.verify_unverified_observations(db)
    return {
        "status": "completed",
        "verified_count": result.get("verified_count", 0),
        "conflicted_count": result.get("conflicted_count", 0),
        "details": result,
    }


async def material_rate_snapshot_refresh_handler(job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
    """Refreshes canonical market rate benchmarks and publishes updated snapshots."""
    from app.services.material_rates.canonical_engine import canonical_engine
    snapshots = await canonical_engine.refresh_all_snapshots(db)
    return {
        "status": "completed",
        "snapshots_refreshed": len(snapshots),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Register all production Material Rate job handlers
register_handler(JobType.MATERIAL_RATE_SOURCE_SYNC.value, material_rate_source_sync_handler)
register_handler(JobType.PBS_WEEKLY_SYNC.value, pbs_weekly_sync_handler)
register_handler(JobType.PBS_MONTHLY_SYNC.value, pbs_monthly_sync_handler)
register_handler(JobType.DEALER_QUOTE_EXPIRY.value, dealer_quote_expiry_handler)
register_handler(JobType.MATERIAL_RATE_VERIFICATION.value, material_rate_verification_handler)
register_handler(JobType.MATERIAL_RATE_SNAPSHOT_REFRESH.value, material_rate_snapshot_refresh_handler)


# ---------------------------------------------------------------------------
# Job Worker Implementation
# ---------------------------------------------------------------------------

class JobWorker:
    """
    Standalone background job worker.
    Continuously polls for eligible jobs using FOR UPDATE SKIP LOCKED, executes
    them with bounded concurrency, and manages state transitions and retries.
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: float = 1.0,
        lease_timeout_seconds: int = 300,
        base_backoff_seconds: int = 2,
    ):
        hostname = socket.gethostname()
        pid = os.getpid()
        rand_token = uuid.uuid4().hex[:6]
        self.worker_id = worker_id or f"worker-{hostname}-{pid}-{rand_token}"
        self.poll_interval = poll_interval
        self.lease_timeout_seconds = lease_timeout_seconds
        self.base_backoff_seconds = base_backoff_seconds
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        """Signals the worker to finish the current iteration and gracefully shut down."""
        logger.info("Worker %s received shutdown signal.", self.worker_id)
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    def compute_backoff_seconds(self, attempt: int, max_backoff: float = 300.0) -> float:
        """Calculates exponential backoff delay for a given retry attempt."""
        delay = float(self.base_backoff_seconds * (2 ** max(0, attempt - 1)))
        return min(delay, max_backoff)

    async def claim_next_job(self, db: AsyncSession) -> Optional[BackgroundJob]:
        """
        Atomically claims the next eligible job using PostgreSQL FOR UPDATE SKIP LOCKED.
        Eligible jobs:
        1. status IN ('queued', 'retrying') AND scheduled_at <= NOW()
        2. status = 'running' AND locked_at + lease_timeout < NOW() (Worker crash recovery)
        Ordered by priority DESC, scheduled_at ASC, created_at ASC.
        """
        now = datetime.now(timezone.utc)
        lease_cutoff = now - timedelta(seconds=self.lease_timeout_seconds)

        # Build eligibility predicate
        eligibility = or_(
            BackgroundJob.status.in_([JobStatus.QUEUED.value, JobStatus.RETRYING.value])
            & (BackgroundJob.scheduled_at <= now),
            (BackgroundJob.status == JobStatus.RUNNING.value)
            & (BackgroundJob.locked_at <= lease_cutoff),
        )

        stmt = (
            select(BackgroundJob)
            .where(eligibility)
            .order_by(
                BackgroundJob.priority.desc(),
                BackgroundJob.scheduled_at.asc(),
                BackgroundJob.created_at.asc(),
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if job is None:
            return None

        # Atomically transition to RUNNING and establish worker lease
        job.status = JobStatus.RUNNING.value
        job.locked_by = self.worker_id
        job.locked_at = now
        job.attempt_count += 1
        job.updated_at = now
        if not job.started_at:
            job.started_at = now

        await db.commit()
        await db.refresh(job)
        logger.info("Worker %s claimed job %s (type: %s, attempt: %d)", self.worker_id, job.id, job.job_type, job.attempt_count)
        return job

    async def renew_lease(self, db: AsyncSession, job_id: UUID) -> bool:
        """
        Heartbeat method: updates locked_at to prevent lease expiration during long workloads.
        Returns False if the job was cancelled or claimed by another worker.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(BackgroundJob)
            .where(
                BackgroundJob.id == job_id,
                BackgroundJob.status == JobStatus.RUNNING.value,
                BackgroundJob.locked_by == self.worker_id,
            )
            .with_for_update()
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if job is None:
            return False

        job.locked_at = now
        job.updated_at = now
        await db.commit()
        return True

    async def process_job(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        job_id: UUID,
    ) -> None:
        """
        Executes the registered handler for the claimed job and records the outcome.
        Handles success, transient retryable failures with exponential backoff,
        permanent non-retryable failures, and graceful cancellations.
        """
        async with session_factory() as db:
            job = await db.scalar(select(BackgroundJob).where(BackgroundJob.id == job_id))
            if job is None:
                return

            # Check if job was cancelled prior to execution
            if job.status == JobStatus.CANCELLED.value:
                logger.info("Job %s was cancelled before execution.", job_id)
                return

            handler = get_handler(job.job_type)
            if handler is None:
                # Unregistered handler -> Terminal failure
                job.transition_to(JobStatus.FAILED.value)
                job.error_message = sanitize_error_message(f"No registered worker handler for job type '{job.job_type}'.")
                await db.commit()
                return

            now = datetime.now(timezone.utc)
            try:
                result_data = await handler(job, db)

                # Re-fetch job under lock to prevent overwriting cancellation or stale completion
                job_ref = await db.scalar(
                    select(BackgroundJob)
                    .where(BackgroundJob.id == job_id)
                    .with_for_update()
                )
                if not job_ref:
                    return

                # Fencing check: if another worker reclaimed the job or status is no longer RUNNING by this worker, discard
                if job_ref.status == JobStatus.CANCELLED.value:
                    logger.info("Job %s was cancelled during execution. Preserving CANCELLED state.", job_id)
                    await db.commit()
                    return

                if job_ref.locked_by != self.worker_id or job_ref.status != JobStatus.RUNNING.value:
                    logger.warning("Fencing rejection: Worker %s completed job %s, but lease was lost to '%s' (status: %s). Discarding result.",
                                   self.worker_id, job_id, job_ref.locked_by, job_ref.status)
                    await db.rollback()
                    return

                # Record successful completion
                job_ref.transition_to(JobStatus.COMPLETED.value)
                job_ref.result = result_data
                job_ref.error_message = None
                job_ref.locked_by = None
                job_ref.locked_at = None
                await db.commit()
                logger.info("Job %s completed successfully by worker %s", job_id, self.worker_id)

            except NonRetryableJobError as exc:
                # Permanent failure -> do not retry
                logger.warning("Permanent failure on job %s: %s", job_id, exc)
                job_ref = await db.scalar(
                    select(BackgroundJob).where(BackgroundJob.id == job_id).with_for_update()
                )
                if job_ref and job_ref.status == JobStatus.CANCELLED.value:
                    await db.commit()
                    return

                if job_ref and (job_ref.locked_by != self.worker_id or job_ref.status != JobStatus.RUNNING.value):
                    logger.warning("Fencing rejection on error: Worker %s for job %s lost lease to '%s'.", self.worker_id, job_id, job_ref.locked_by)
                    await db.rollback()
                    return

                if job_ref:
                    job_ref.transition_to(JobStatus.FAILED.value)
                    job_ref.error_message = sanitize_error_message(str(exc))
                    job_ref.locked_by = None
                    job_ref.locked_at = None
                    await db.commit()

            except Exception as exc:
                # Transient failure -> evaluate retry attempts and exponential backoff
                logger.warning("Error processing job %s (attempt %d/%d): %s", job_id, job.attempt_count, job.max_retries, exc)
                job_ref = await db.scalar(
                    select(BackgroundJob).where(BackgroundJob.id == job_id).with_for_update()
                )
                if job_ref and job_ref.status == JobStatus.CANCELLED.value:
                    await db.commit()
                    return

                if job_ref and (job_ref.locked_by != self.worker_id or job_ref.status != JobStatus.RUNNING.value):
                    logger.warning("Fencing rejection on retry: Worker %s for job %s lost lease to '%s'.", self.worker_id, job_id, job_ref.locked_by)
                    await db.rollback()
                    return

                if job_ref:
                    if job_ref.attempt_count < job_ref.max_retries:
                        # Exponential backoff: base_backoff * 2^(attempt - 1)
                        backoff_seconds = self.base_backoff_seconds * (2 ** (job_ref.attempt_count - 1))
                        next_scheduled = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                        job_ref.transition_to(JobStatus.RETRYING.value)
                        job_ref.scheduled_at = next_scheduled
                        job_ref.error_message = sanitize_error_message(str(exc))
                        job_ref.locked_by = None
                        job_ref.locked_at = None
                        logger.info("Job %s scheduled for retry in %d seconds (at %s)", job_id, backoff_seconds, next_scheduled)
                    else:
                        # Retries exhausted -> Terminal failure
                        job_ref.transition_to(JobStatus.FAILED.value)
                        job_ref.error_message = sanitize_error_message(
                            f"Max retries ({job_ref.max_retries}) exhausted. Last error: {str(exc)}"
                        )
                        job_ref.locked_by = None
                        job_ref.locked_at = None
                        logger.error("Job %s exhausted all retries. Terminal state: FAILED", job_id)

                    await db.commit()

    async def run_once(self, session_factory: async_sessionmaker[AsyncSession]) -> bool:
        """
        Attempts to claim and execute one eligible job.
        Returns True if a job was claimed and executed, False if no jobs were eligible.
        """
        async with session_factory() as db:
            job = await self.claim_next_job(db)
            if job is None:
                return False
            job_id = job.id

        await self.process_job(session_factory, job_id)
        return True

    async def run(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """
        Continuous worker loop. Polls for eligible jobs until stop() is called.
        """
        logger.info("Worker %s started processing loop.", self.worker_id)
        while not self._stop_event.is_set():
            try:
                processed = await self.run_once(session_factory)
                if not processed:
                    # Queue is empty or no jobs eligible; sleep poll interval
                    await asyncio.sleep(self.poll_interval)
            except Exception as exc:
                logger.error("Worker %s encountered loop error: %s", self.worker_id, exc, exc_info=True)
                await asyncio.sleep(self.poll_interval)
        logger.info("Worker %s stopped processing loop.", self.worker_id)


# Alias for compatibility
BackgroundJobWorker = JobWorker

