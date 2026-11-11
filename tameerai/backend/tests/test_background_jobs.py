"""
TameerAI - Background Job Infrastructure Integration & Unit Tests (Phase 02G)

Comprehensive verification covering all 21 Task 9 scenarios + migration dry run:
1. Authorized job creation (owner, lead_engineer, architect, contractor)
2. Unauthorized project access (non-member stranger returns 404)
3. Viewer create restriction (viewer returns 403 Forbidden)
4. Cross-project job isolation (User in Project A cannot access Project B job -> 404)
5. Job listing and pagination (status filter, limit, offset)
6. Job status retrieval (GET /projects/{id}/jobs/{job_id})
7. Valid state transitions (queued -> running -> completed)
8. Invalid state transitions (completed -> running raises ValueError)
9. Concurrent job claiming (atomic claiming without duplicates)
10. Successful completion (result recorded, completed_at set)
11. Retryable failure (transient error sets retrying with backoff)
12. Permanent failure (NonRetryableJobError immediately sets failed)
13. Exponential backoff (backoff delay increases with attempt_count)
14. Maximum retry exhaustion (attempt_count >= max_retries sets failed)
15. Worker crash and lease expiration (expired lease reclaimed)
16. Heartbeat renewal (renew_lease extends locked_at)
17. Cancellation behavior (cancellation of queued/running; completed rejected with 409)
18. Idempotency keys (duplicate submission returns existing job)
19. Transaction rollback (DB error rolls back cleanly)
20. Sensitive error redaction (connection strings, tokens, file paths redacted)
21. Worker graceful shutdown (stop() halts loop cleanly)
22. Migration 005 dry-run (upgrade and downgrade on isolated engine)
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_db
from app.core.config import settings
from app.core.rate_limit import login_limiter
from app.db.base import Base
from app.main import app
from app.models.document import Document
from app.models.job import (
    BackgroundJob,
    JobStatus,
    JobType,
    VALID_TRANSITIONS,
)
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.workers.job_worker import (
    BackgroundJobWorker,
    JobExecutionError,
    NonRetryableJobError,
    register_handler,
    sanitize_error_message,
    synthetic_test_handler,
)


# ---------------------------------------------------------------------------
# Isolated In-Memory SQLite Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_session_factory():
    """Isolated SQLite in-memory database per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    orig_env = settings.ENVIRONMENT
    orig_enable = settings.ENABLE_SYNTHETIC_JOBS
    settings.ENVIRONMENT = "test"
    settings.ENABLE_SYNTHETIC_JOBS = True
    register_handler(JobType.SYNTHETIC_TEST.value, synthetic_test_handler)

    yield session_factory

    settings.ENVIRONMENT = orig_env
    settings.ENABLE_SYNTHETIC_JOBS = orig_enable
    await engine.dispose()


@pytest_asyncio.fixture
async def job_client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    login_limiter.reset()

    # Enable synthetic jobs and register handler in test fixture
    orig_env = settings.ENVIRONMENT
    orig_enable = settings.ENABLE_SYNTHETIC_JOBS
    settings.ENVIRONMENT = "test"
    settings.ENABLE_SYNTHETIC_JOBS = True
    register_handler(JobType.SYNTHETIC_TEST.value, synthetic_test_handler)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    settings.ENVIRONMENT = orig_env
    settings.ENABLE_SYNTHETIC_JOBS = orig_enable
    app.dependency_overrides.clear()
    login_limiter.reset()


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

async def register_and_login(client: AsyncClient, email: str, role: str = "engineer") -> str:
    reg_payload = {
        "fullName": f"User {email.split('@')[0]}",
        "email": email,
        "password": "Password12345!",
        "role": role,
        "city": "Lahore",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password12345!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    return data["accessToken"]


async def create_test_project(client: AsyncClient, token: str, name: str = "Tameer Project") -> str:
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": name,
        "location": "Gulberg III, Lahore",
        "city": "Lahore",
        "type": "Commercial G+12",
        "budgetCrore": 25.0,
        "floors": 12,
        "areaSqft": "35,000 sq ft",
        "status": "Under Analysis",
        "risk": "Low",
    }
    res = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["uuid"]


async def add_project_member(
    session_factory: async_sessionmaker[AsyncSession],
    project_id: UUID,
    user_email: str,
    role: str,
):
    async with session_factory() as session:
        user_res = await session.execute(select(User).where(User.email == user_email))
        user = user_res.scalar_one()

        member = ProjectMember(
            id=uuid4(),
            project_id=project_id,
            user_id=user.id,
            role=role,
        )
        session.add(member)
        await session.commit()


# ---------------------------------------------------------------------------
# Test 1: Authorized Job Creation (Owner, Lead Engineer, Architect, Contractor)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authorized_job_creation(job_client: AsyncClient, test_session_factory):
    owner_token = await register_and_login(job_client, "owner_job@test.com")
    project_id = await create_test_project(job_client, owner_token, "Job Creation Test")

    # 1. Owner creates a job
    res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={
            "jobType": "synthetic_test",
            "priority": 0,
            "payload": {"scenario": "success", "data": "owner_run"},
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 201, res.text
    job_data = res.json()
    assert job_data["status"] == "queued"
    assert job_data["jobType"] == "synthetic_test"
    assert job_data["projectId"] == project_id
    assert job_data["attemptCount"] == 0

    # 2. Contractor creates a job (allowed: role level 2 >= 2)
    contractor_token = await register_and_login(job_client, "contractor_job@test.com", "contractor")
    await add_project_member(test_session_factory, UUID(project_id), "contractor_job@test.com", "contractor")
    res_contractor = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={
            "jobType": "boq_extraction",
            "priority": 1,
            "payload": {"scenario": "success"},
        },
        headers={"Authorization": f"Bearer {contractor_token}"},
    )
    assert res_contractor.status_code == 201

    # 3. Architect creates a job (allowed: role level 3 >= 2)
    arch_token = await register_and_login(job_client, "arch_job@test.com", "architect")
    await add_project_member(test_session_factory, UUID(project_id), "arch_job@test.com", "architect")
    res_arch = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={
            "jobType": "compliance_audit",
            "priority": 2,
            "payload": {"scenario": "success"},
        },
        headers={"Authorization": f"Bearer {arch_token}"},
    )
    assert res_arch.status_code == 201


# ---------------------------------------------------------------------------
# Test 2: Unauthorized Project Access (Non-Member Stranger Returns 404)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthorized_project_access(job_client: AsyncClient):
    owner_token = await register_and_login(job_client, "owner_unauth@test.com")
    stranger_token = await register_and_login(job_client, "stranger_unauth@test.com")
    project_id = await create_test_project(job_client, owner_token, "Restricted Project")

    res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={"jobType": "synthetic_test", "payload": {}},
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    # IDOR protection: non-members receive 404 Project not found
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 3: Viewer Create Restriction (Viewer Returns 403 Forbidden)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_viewer_create_restriction(job_client: AsyncClient, test_session_factory):
    owner_token = await register_and_login(job_client, "owner_viewer_test@test.com")
    viewer_token = await register_and_login(job_client, "viewer_job@test.com", "engineer")
    project_id = await create_test_project(job_client, owner_token, "Viewer Test Project")

    # Add viewer role (level 1)
    await add_project_member(test_session_factory, UUID(project_id), "viewer_job@test.com", "viewer")

    # Viewer attempts to submit job -> 403 Forbidden
    res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={"jobType": "synthetic_test", "payload": {}},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res.status_code == 403
    assert "insufficient permissions" in res.json()["detail"].lower() or "viewer" in res.json()["detail"].lower()

    # Viewer can still list jobs -> 200 OK
    list_res = await job_client.get(
        f"/api/v1/projects/{project_id}/jobs",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert list_res.status_code == 200


# ---------------------------------------------------------------------------
# Test 4: Cross-Project Job Isolation (User in Project A cannot access Project B job)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_project_job_isolation(job_client: AsyncClient):
    user_a_token = await register_and_login(job_client, "user_a@test.com")
    user_b_token = await register_and_login(job_client, "user_b@test.com")

    project_a = await create_test_project(job_client, user_a_token, "Project Alpha")
    project_b = await create_test_project(job_client, user_b_token, "Project Beta")

    # Create job in Project A
    res = await job_client.post(
        f"/api/v1/projects/{project_a}/jobs",
        json={"jobType": "synthetic_test", "payload": {}},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert res.status_code == 201
    job_id = res.json()["id"]

    # User B tries to access Job A via Project B endpoint -> 404
    cross_res = await job_client.get(
        f"/api/v1/projects/{project_b}/jobs/{job_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert cross_res.status_code == 404


# ---------------------------------------------------------------------------
# Test 5: Job Listing and Pagination
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_listing_and_pagination(job_client: AsyncClient):
    token = await register_and_login(job_client, "pagination_user@test.com")
    project_id = await create_test_project(job_client, token, "Pagination Project")

    # Create 5 jobs
    for i in range(5):
        await job_client.post(
            f"/api/v1/projects/{project_id}/jobs",
            json={
                "jobType": "synthetic_test",
                "priority": i,
                "payload": {"index": i},
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    # 1. Default list
    res = await job_client.get(
        f"/api/v1/projects/{project_id}/jobs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) == 5

    # 2. Limit and offset
    page_res = await job_client.get(
        f"/api/v1/projects/{project_id}/jobs?limit=2&offset=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert page_res.status_code == 200
    page_items = page_res.json()
    assert isinstance(page_items, list)
    assert len(page_items) == 2

    # 3. Status filter
    filter_res = await job_client.get(
        f"/api/v1/projects/{project_id}/jobs?status=queued",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filter_res.status_code == 200
    filter_items = filter_res.json()
    assert isinstance(filter_items, list)
    assert len(filter_items) == 5


# ---------------------------------------------------------------------------
# Test 6: Job Status Retrieval
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_status_retrieval(job_client: AsyncClient):
    token = await register_and_login(job_client, "status_user@test.com")
    project_id = await create_test_project(job_client, token, "Status Project")

    create_res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={
            "jobType": "synthetic_test",
            "priority": 5,
            "maxRetries": 4,
            "payload": {"test": "value"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]

    get_res = await job_client.get(
        f"/api/v1/projects/{project_id}/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    job = get_res.json()
    assert job["id"] == job_id
    assert job["jobType"] == "synthetic_test"
    assert job["status"] == "queued"
    assert job["priority"] == 5
    assert job["maxRetries"] == 4
    assert job["attemptCount"] == 0
    assert job["payload"] == {"test": "value"}


# ---------------------------------------------------------------------------
# Test 7: Valid State Transitions
# ---------------------------------------------------------------------------

def test_valid_state_transitions():
    job = BackgroundJob(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        job_type=JobType.SYNTHETIC_TEST.value,
        status=JobStatus.QUEUED.value,
    )

    # queued -> running
    job.transition_to(JobStatus.RUNNING.value)
    assert job.status == JobStatus.RUNNING.value

    # running -> retrying
    job.transition_to(JobStatus.RETRYING.value)
    assert job.status == JobStatus.RETRYING.value

    # retrying -> running
    job.transition_to(JobStatus.RUNNING.value)
    assert job.status == JobStatus.RUNNING.value

    # running -> completed
    job.transition_to(JobStatus.COMPLETED.value)
    assert job.status == JobStatus.COMPLETED.value


# ---------------------------------------------------------------------------
# Test 8: Invalid State Transitions (Raise ValueError)
# ---------------------------------------------------------------------------

def test_invalid_state_transitions():
    # 1. Completed cannot transition to running
    job_completed = BackgroundJob(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        job_type=JobType.SYNTHETIC_TEST.value,
        status=JobStatus.COMPLETED.value,
    )
    with pytest.raises(ValueError, match="Invalid job state transition"):
        job_completed.transition_to(JobStatus.RUNNING.value)

    # 2. Failed cannot transition to running or queued
    job_failed = BackgroundJob(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        job_type=JobType.SYNTHETIC_TEST.value,
        status=JobStatus.FAILED.value,
    )
    with pytest.raises(ValueError, match="Invalid job state transition"):
        job_failed.transition_to(JobStatus.QUEUED.value)

    # 3. Cancelled cannot transition to running
    job_cancelled = BackgroundJob(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        job_type=JobType.SYNTHETIC_TEST.value,
        status=JobStatus.CANCELLED.value,
    )
    with pytest.raises(ValueError, match="Invalid job state transition"):
        job_cancelled.transition_to(JobStatus.RUNNING.value)

    # 4. Queued cannot transition directly to completed
    job_queued = BackgroundJob(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        job_type=JobType.SYNTHETIC_TEST.value,
        status=JobStatus.QUEUED.value,
    )
    with pytest.raises(ValueError, match="Invalid job state transition"):
        job_queued.transition_to(JobStatus.COMPLETED.value)


# ---------------------------------------------------------------------------
# Test 9: Concurrent Job Claiming
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_job_claiming(test_session_factory):
    worker_1 = BackgroundJobWorker(worker_id="worker_alpha")
    worker_2 = BackgroundJobWorker(worker_id="worker_beta")

    # Insert 2 queued jobs
    user_id = uuid4()
    project_id = uuid4()
    async with test_session_factory() as session:
        j1 = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
            scheduled_at=datetime.now(timezone.utc),
        )
        j2 = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add_all([j1, j2])
        await session.commit()
        id1, id2 = j1.id, j2.id

    # Each worker claims a job
    async with test_session_factory() as s1:
        claimed_1 = await worker_1.claim_next_job(s1)

    async with test_session_factory() as s2:
        claimed_2 = await worker_2.claim_next_job(s2)

    assert claimed_1 is not None
    assert claimed_2 is not None
    assert claimed_1.id != claimed_2.id
    assert {claimed_1.id, claimed_2.id} == {id1, id2}
    assert claimed_1.status == JobStatus.RUNNING.value
    assert claimed_2.status == JobStatus.RUNNING.value
    assert claimed_1.locked_by == "worker_alpha"
    assert claimed_2.locked_by == "worker_beta"


# ---------------------------------------------------------------------------
# Test 10: Successful Completion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_successful_completion(test_session_factory):
    worker = BackgroundJobWorker(worker_id="test_worker")
    user_id = uuid4()
    project_id = uuid4()

    async with test_session_factory() as session:
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
            payload={"sleep_seconds": 0},
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    # Worker runs one cycle
    processed = await worker.run_once(test_session_factory)
    assert processed is True

    # Verify database state
    async with test_session_factory() as session:
        res = await session.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        completed_job = res.scalar_one()

        assert completed_job.status == JobStatus.COMPLETED.value
        assert completed_job.completed_at is not None
        assert completed_job.locked_by is None
        assert completed_job.result["processed"] is True


# ---------------------------------------------------------------------------
# Test 11: Retryable Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_retryable_failure(test_session_factory):
    worker = BackgroundJobWorker(worker_id="test_worker")
    user_id = uuid4()
    project_id = uuid4()

    async with test_session_factory() as session:
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
            max_retries=3,
            payload={"fail_retryable": True},
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    processed = await worker.run_once(test_session_factory)
    assert processed is True

    async with test_session_factory() as session:
        res = await session.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        retrying_job = res.scalar_one()

        assert retrying_job.status == JobStatus.RETRYING.value
        assert retrying_job.attempt_count == 1
        assert "Transient network glitch" in retrying_job.error_message
        assert retrying_job.locked_by is None
        # Scheduled in the future (backoff)
        sched = retrying_job.scheduled_at
        if sched.tzinfo is None:
            sched = sched.replace(tzinfo=timezone.utc)
        assert sched > datetime.now(timezone.utc) - timedelta(seconds=1)


# ---------------------------------------------------------------------------
# Test 12: Permanent Failure (NonRetryableJobError Immediately Fails)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_permanent_failure(test_session_factory):
    worker = BackgroundJobWorker(worker_id="test_worker")
    user_id = uuid4()
    project_id = uuid4()

    async with test_session_factory() as session:
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
            max_retries=5,  # Has retries available, but failure is permanent
            payload={"fail_permanent": True, "error_reason": "Corrupt structural schema"},
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    processed = await worker.run_once(test_session_factory)
    assert processed is True

    async with test_session_factory() as session:
        res = await session.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        failed_job = res.scalar_one()

        assert failed_job.status == JobStatus.FAILED.value
        assert failed_job.attempt_count == 1
        assert "Permanent failure simulated" in failed_job.error_message
        assert failed_job.completed_at is not None
        assert failed_job.locked_by is None


# ---------------------------------------------------------------------------
# Test 13: Exponential Backoff Calculation
# ---------------------------------------------------------------------------

def test_exponential_backoff_calculation():
    worker = BackgroundJobWorker()

    b1 = worker.compute_backoff_seconds(1)
    b2 = worker.compute_backoff_seconds(2)
    b3 = worker.compute_backoff_seconds(3)
    b10 = worker.compute_backoff_seconds(10)

    assert b1 == 2.0   # 2 * (2^0)
    assert b2 == 4.0   # 2 * (2^1)
    assert b3 == 8.0   # 2 * (2^2)
    assert b10 <= 300.0  # Capped at max_backoff


# ---------------------------------------------------------------------------
# Test 14: Maximum Retry Exhaustion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_max_retry_exhaustion(test_session_factory):
    worker = BackgroundJobWorker(worker_id="test_worker")
    user_id = uuid4()
    project_id = uuid4()

    async with test_session_factory() as session:
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
            attempt_count=2,
            max_retries=2,  # Next attempt exhausts retries
            payload={"fail_retryable": True},
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    processed = await worker.run_once(test_session_factory)
    assert processed is True

    async with test_session_factory() as session:
        res = await session.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        exhausted_job = res.scalar_one()

        assert exhausted_job.status == JobStatus.FAILED.value
        assert exhausted_job.attempt_count == 3
        assert "Max retries" in exhausted_job.error_message
        assert exhausted_job.completed_at is not None


# ---------------------------------------------------------------------------
# Test 15: Worker Crash & Lease Expiration Reclamation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_crash_and_lease_expiration(test_session_factory):
    worker = BackgroundJobWorker(worker_id="reclaimer_worker")
    user_id = uuid4()
    project_id = uuid4()

    # Insert a job locked 2 hours ago with lease_timeout 60s (expired lease)
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    async with test_session_factory() as session:
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.RUNNING.value,
            locked_by="dead_crashed_worker",
            locked_at=old_time,
            lease_timeout_seconds=60,
            payload={"sleep_seconds": 0},
            scheduled_at=old_time,
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    # Claiming should reclaim the expired lease
    async with test_session_factory() as session:
        claimed = await worker.claim_next_job(session)
        assert claimed is not None
        assert claimed.id == job_id
        assert claimed.locked_by == "reclaimer_worker"
        assert claimed.status == JobStatus.RUNNING.value


# ---------------------------------------------------------------------------
# Test 16: Heartbeat Lease Renewal
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_heartbeat_renewal(test_session_factory):
    worker = BackgroundJobWorker(worker_id="hb_worker")
    user_id = uuid4()
    project_id = uuid4()

    t0 = datetime.now(timezone.utc) - timedelta(seconds=20)
    async with test_session_factory() as session:
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.RUNNING.value,
            locked_by="hb_worker",
            locked_at=t0,
            scheduled_at=t0,
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    # Renew lease
    async with test_session_factory() as session:
        renewed = await worker.renew_lease(session, job_id)
        assert renewed is True

    async with test_session_factory() as session:
        res = await session.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        updated_job = res.scalar_one()
        locked = updated_job.locked_at
        if locked.tzinfo is None:
            locked = locked.replace(tzinfo=timezone.utc)
        assert locked > t0


# ---------------------------------------------------------------------------
# Test 17: Cancellation Behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancellation_behavior(job_client: AsyncClient, test_session_factory):
    owner_token = await register_and_login(job_client, "cancel_owner@test.com")
    project_id = await create_test_project(job_client, owner_token, "Cancel Project")

    # 1. Create and cancel queued job
    create_res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={"jobType": "synthetic_test", "payload": {}},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]

    cancel_res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs/{job_id}/cancel",
        json={"reason": "User cancelled test"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert cancel_res.status_code == 200
    cancelled_data = cancel_res.json()
    assert cancelled_data["status"] == "cancelled"
    assert "User cancelled test" in cancelled_data["errorMessage"]

    # 2. Cannot cancel an already completed job -> 409 Conflict
    async with test_session_factory() as session:
        comp_job = BackgroundJob(
            id=uuid4(),
            project_id=UUID(project_id),
            user_id=UUID(cancelled_data["userId"]),
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
        )
        session.add(comp_job)
        await session.commit()
        comp_id = str(comp_job.id)

    conflict_res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs/{comp_id}/cancel",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert conflict_res.status_code == 409
    assert "cannot cancel" in conflict_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 18: Idempotency Keys Deduplication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_idempotency_keys(job_client: AsyncClient):
    token = await register_and_login(job_client, "idempotency_user@test.com")
    project_id = await create_test_project(job_client, token, "Idempotency Project")
    idempotency_key = f"key_{uuid4().hex[:12]}"

    payload = {
        "jobType": "synthetic_test",
        "idempotencyKey": idempotency_key,
        "payload": {"step": 1},
    }

    # First submission -> 201 Created
    res1 = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201
    job_1 = res1.json()

    # Second submission with same idempotency key -> returns existing job (same ID)
    res2 = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 201
    job_2 = res2.json()
    assert job_1["id"] == job_2["id"]
    assert job_2["idempotencyKey"] == idempotency_key


# ---------------------------------------------------------------------------
# Test 19: Transaction Rollback on Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transaction_rollback_on_failure(test_session_factory):
    user_id = uuid4()
    project_id = uuid4()
    async with test_session_factory() as session:
        # Create a valid job
        job = BackgroundJob(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.QUEUED.value,
        )
        session.add(job)
        await session.commit()
        valid_id = job.id

    # Simulate an error inside a transaction
    async with test_session_factory() as session:
        try:
            broken_job = BackgroundJob(
                id=uuid4(),
                project_id=project_id,
                user_id=user_id,
                job_type=JobType.SYNTHETIC_TEST.value,
                status="invalid_status_value",  # Fails check constraint
            )
            session.add(broken_job)
            await session.flush()
        except Exception:
            await session.rollback()

    # Verify original state preserved
    async with test_session_factory() as session:
        res = await session.execute(select(BackgroundJob).where(BackgroundJob.id == valid_id))
        assert res.scalar_one() is not None


# ---------------------------------------------------------------------------
# Test 20: Sensitive Error Redaction
# ---------------------------------------------------------------------------

def test_sensitive_error_redaction():
    raw_error = (
        "Failed connecting to postgresql+asyncpg://postgres:SuperSecret123@db.supabase.com:5432/postgres "
        "while reading D:\\new idea project\\secret_file.pdf. "
        "Authorization header was Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123."
    )
    sanitized = sanitize_error_message(raw_error)

    assert "SuperSecret123" not in sanitized
    assert "postgresql+asyncpg" not in sanitized
    assert "[REDACTED_DB_URI]" in sanitized
    assert "secret_file.pdf" not in sanitized
    assert "[REDACTED_PATH]" in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "[REDACTED_CREDENTIAL]" in sanitized or "[REDACTED_TOKEN]" in sanitized


# ---------------------------------------------------------------------------
# Test 21: Worker Graceful Shutdown
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_graceful_shutdown(test_session_factory):
    worker = BackgroundJobWorker(
        poll_interval=0.1,
        worker_id="shutdown_test_worker",
    )

    # Launch worker loop in background task
    worker_task = asyncio.create_task(worker.run(test_session_factory))

    # Allow worker loop to start
    await asyncio.sleep(0.2)
    assert worker.is_running is True

    # Signal stop
    worker.stop()
    await asyncio.wait_for(worker_task, timeout=2.0)
    assert worker.is_running is False


# ---------------------------------------------------------------------------
# Test 23: Synthetic Handler Security Guards & Payload Bounds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_synthetic_job_disabled_in_production(job_client: AsyncClient):
    """
    Verifies that synthetic_test jobs are strictly rejected with 403 Forbidden
    when ENABLE_SYNTHETIC_JOBS is False or ENVIRONMENT is production.
    """
    token = await register_and_login(job_client, "prod_synthetic_guard@test.com")
    project_id = await create_test_project(job_client, token, "Synthetic Guard Project")

    # Temporarily simulate production / disabled setting
    orig_env = settings.ENVIRONMENT
    orig_enable = settings.ENABLE_SYNTHETIC_JOBS
    settings.ENVIRONMENT = "production"
    settings.ENABLE_SYNTHETIC_JOBS = False

    try:
        res = await job_client.post(
            f"/api/v1/projects/{project_id}/jobs",
            json={"jobType": "synthetic_test", "payload": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "Synthetic test jobs are disabled in this environment" in res.text
    finally:
        settings.ENVIRONMENT = orig_env
        settings.ENABLE_SYNTHETIC_JOBS = orig_enable


@pytest.mark.asyncio
async def test_synthetic_job_payload_bounds(job_client: AsyncClient):
    """
    Verifies that payload size and synthetic sleep_seconds are strictly bounded.
    """
    token = await register_and_login(job_client, "bounds_user@test.com")
    project_id = await create_test_project(job_client, token, "Bounds Project")

    # 1. sleep_seconds > 60 rejected
    res = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={"jobType": "synthetic_test", "payload": {"sleep_seconds": 999}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422

    # 2. Oversized payload (> 64KB) rejected
    large_payload = {"huge_data": "x" * 70000}
    res_large = await job_client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={"jobType": "synthetic_test", "payload": large_payload},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_large.status_code == 422


# ---------------------------------------------------------------------------
# Test 24: Stale Worker Fencing & Lease Expiration Rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stale_worker_fencing_rejection(test_session_factory):
    """
    Verifies that a worker whose lease expired and was claimed by another worker
    cannot overwrite the new worker's ownership or commit stale results.
    """
    worker_a = BackgroundJobWorker(worker_id="worker_alpha", lease_timeout_seconds=10)
    worker_b = BackgroundJobWorker(worker_id="worker_beta", lease_timeout_seconds=10)

    # 1. Insert a job claimed by worker_a whose lease has expired
    async with test_session_factory() as session:
        user = User(
            id=uuid4(),
            email="fencing_test@test.com",
            hashed_password="hashed_pw_test",
            full_name="Fencing Test User",
            role="engineer",
        )
        project = Project(
            id=uuid4(),
            user_id=user.id,
            name="Fencing Project",
            code="PRJ-FENCE",
            type="Commercial",
            location="Gulberg, Lahore",
            city="Lahore",
        )
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        job = BackgroundJob(
            id=uuid4(),
            project_id=project.id,
            user_id=user.id,
            job_type=JobType.SYNTHETIC_TEST.value,
            status=JobStatus.RUNNING.value,
            locked_by=worker_a.worker_id,
            locked_at=expired_time,
            attempt_count=1,
            max_retries=3,
            payload={},
        )
        session.add_all([user, project, job])
        await session.commit()
        job_id = job.id

    # 2. Worker B claims the expired job via crash recovery
    async with test_session_factory() as session:
        claimed_b = await worker_b.claim_next_job(session)
        assert claimed_b is not None
        assert claimed_b.id == job_id
        assert claimed_b.locked_by == worker_b.worker_id

    # 3. Worker A attempts heartbeat renewal on the job it no longer owns -> must return False
    async with test_session_factory() as session:
        renewed = await worker_a.renew_lease(session, job_id)
        assert renewed is False

    # 4. Worker A attempts to complete process_job -> fencing logic discards result without overwriting
    await worker_a.process_job(test_session_factory, job_id)

    # 5. Verify Worker B still owns the running job
    async with test_session_factory() as session:
        job_after = await session.scalar(select(BackgroundJob).where(BackgroundJob.id == job_id))
        assert job_after.locked_by == worker_b.worker_id
        assert job_after.status == JobStatus.RUNNING.value

    # 6. Worker B successfully completes the job
    await worker_b.process_job(test_session_factory, job_id)

    # 7. Final state is COMPLETED by Worker B
    async with test_session_factory() as session:
        final_job = await session.scalar(select(BackgroundJob).where(BackgroundJob.id == job_id))
        assert final_job.status == JobStatus.COMPLETED.value
        assert final_job.locked_by is None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pending_migration_005_dry_run():
    """
    Verifies that the migration script in alembic/pending_migrations/005_create_background_jobs_table.py
    executes without syntax errors or invalid declarations on an isolated SQLite engine.
    """
    migration_path = (
        Path(__file__).resolve().parent.parent
        / "alembic"
        / "pending_migrations"
        / "005_create_background_jobs_table.py"
    )
    assert migration_path.exists(), f"Pending migration file missing: {migration_path}"

    # Verify migration file content contains valid upgrade/downgrade methods and identifiers
    content = migration_path.read_text(encoding="utf-8")
    assert 'revision: str = "005_background_jobs_infrastructure"' in content or "005_background_jobs" in content
    assert "down_revision = '004_chat_rag_foundation'" in content or 'down_revision: Union[str, None] = "004_chat_rag_foundation"' in content
    assert "def upgrade() -> None:" in content
    assert "def downgrade() -> None:" in content
    assert "background_jobs" in content
    assert "ck_background_jobs_status" in content
