"""
TameerAI - Background Job Database Model & State Machine (Phase 02G)

Defines:
- BackgroundJob: Persistent, durable background job state model for multi-worker asynchronous processing.
- JobStatusEnum: Standard state machine states (queued, running, retrying, completed, failed, cancelled).
- JobTypeEnum: Registered, authorized background workload identifiers.
- Transition rules and validations for state machine integrity.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    JSON,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    SYNTHETIC_TEST = "synthetic_test"
    COMPLIANCE_AUDIT = "compliance_audit"
    CONTRACT_ANALYSIS = "contract_analysis"
    BOQ_EXTRACTION = "boq_extraction"
    REPORT_GENERATION = "report_generation"
    MATERIAL_RATE_SOURCE_SYNC = "material_rate_source_sync"
    PBS_WEEKLY_SYNC = "pbs_weekly_sync"
    PBS_MONTHLY_SYNC = "pbs_monthly_sync"
    DEALER_QUOTE_EXPIRY = "dealer_quote_expiry"
    MATERIAL_RATE_VERIFICATION = "material_rate_verification"
    MATERIAL_RATE_SNAPSHOT_REFRESH = "material_rate_snapshot_refresh"


# Valid state machine transitions
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    JobStatus.QUEUED.value: {JobStatus.RUNNING.value, JobStatus.CANCELLED.value},
    JobStatus.RUNNING.value: {
        JobStatus.COMPLETED.value,
        JobStatus.RETRYING.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    },
    JobStatus.RETRYING.value: {JobStatus.RUNNING.value, JobStatus.CANCELLED.value},
    JobStatus.COMPLETED.value: set(),  # Terminal
    JobStatus.FAILED.value: set(),     # Terminal
    JobStatus.CANCELLED.value: set(),  # Terminal
}


class BackgroundJob(Base):
    """
    Durable Background Processing Job Model.
    Tracks state, leases, retries, and results for asynchronous workloads.
    Uses PostgreSQL FOR UPDATE SKIP LOCKED in production to guarantee atomic,
    non-blocking distributed worker job claiming.
    """

    __tablename__ = "background_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'retrying', 'completed', 'failed', 'cancelled')",
            name="ck_background_jobs_status",
        ),
        CheckConstraint(
            "priority >= -10 AND priority <= 10",
            name="ck_background_jobs_priority_range",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_background_jobs_attempt_count_non_negative",
        ),
        CheckConstraint(
            "max_retries >= 0",
            name="ck_background_jobs_max_retries_non_negative",
        ),
        CheckConstraint(
            "lease_timeout_seconds >= 10 AND lease_timeout_seconds <= 3600",
            name="ck_background_jobs_lease_timeout_range",
        ),
        CheckConstraint(
            "((project_id IS NOT NULL AND user_id IS NOT NULL) OR (project_id IS NULL AND user_id IS NULL))",
            name="ck_background_jobs_scope_consistency",
        ),
        UniqueConstraint(
            "project_id", "job_type", "idempotency_key",
            name="uq_background_jobs_project_type_idempotency",
        ),
        Index(
            "uq_background_jobs_system_idempotency",
            "job_type", "idempotency_key",
            unique=True,
            postgresql_where=text("project_id IS NULL AND idempotency_key IS NOT NULL"),
            sqlite_where=text("project_id IS NULL AND idempotency_key IS NOT NULL"),
        ),
        Index(
            "ix_background_jobs_claim",
            "status", "scheduled_at", "priority",
        ),
        Index(
            "ix_background_jobs_project_status",
            "project_id", "status", "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent project workspace UUID (null for global system jobs)",
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Initiating user UUID (null for global system jobs)",
    )
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Approved background workload type identifier",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.QUEUED.value,
        server_default=JobStatus.QUEUED.value,
        index=True,
        comment="Job lifecycle state: queued, running, retrying, completed, failed, cancelled",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Scheduling priority: higher values claim before lower values (-10 to 10)",
    )
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        default=dict,
        comment="Safe parameter dictionary (document references, configuration; strictly no credentials)",
    )
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Execution result references and safe summary metrics",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Redacted, safe error summary for terminal or retry failures",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of execution attempts completed or in-progress",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
        comment="Maximum retry attempts permitted before terminal failure",
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
        comment="Timestamp when job becomes eligible for worker claim (supports exponential backoff)",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when worker first claimed the job",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of terminal completion, failure, or cancellation",
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of most recent worker heartbeat/lease renewal",
    )
    locked_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Unique identifier of the worker currently holding the execution lease",
    )
    lease_timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        server_default="300",
        comment="Lease expiration window in seconds (default 5 minutes)",
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Client-supplied or caller deduplication token",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Job creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project")
    user: Mapped[Optional["User"]] = relationship("User")

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs:
            kwargs["status"] = JobStatus.QUEUED.value
        if "priority" not in kwargs:
            kwargs["priority"] = 0
        if "attempt_count" not in kwargs:
            kwargs["attempt_count"] = 0
        if "max_retries" not in kwargs:
            kwargs["max_retries"] = 3
        if "lease_timeout_seconds" not in kwargs:
            kwargs["lease_timeout_seconds"] = 300
        if "scheduled_at" not in kwargs:
            kwargs["scheduled_at"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def can_transition_to(self, new_status: str) -> bool:
        """Returns True if transition from current status to new_status is valid."""
        return new_status in VALID_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status: str) -> None:
        """
        Transitions the job to new_status.
        Raises ValueError if the transition violates the state machine.
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Invalid job state transition from '{self.status}' to '{new_status}'."
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        if new_status in {JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value}:
            self.completed_at = datetime.now(timezone.utc)
            self.locked_by = None
            self.locked_at = None

    def is_lease_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Returns True if the job is running and its worker lease has expired."""
        if self.status != JobStatus.RUNNING.value or self.locked_at is None:
            return False
        now = current_time or datetime.now(timezone.utc)
        elapsed = (now - self.locked_at).total_seconds()
        return elapsed > self.lease_timeout_seconds

    def __repr__(self) -> str:
        return f"<BackgroundJob(id={self.id}, type='{self.job_type}', status='{self.status}', attempts={self.attempt_count}/{self.max_retries})>"

