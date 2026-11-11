"""
Phase 02G - Create Background Jobs Table

Revision ID: 005_background_jobs_infrastructure
Revises: 004_chat_rag_foundation
Create Date: 2026-11-04 16:30:00.000000

Durable, reliable background job queue table supporting distributed worker
execution via PostgreSQL FOR UPDATE SKIP LOCKED.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_background_jobs_infrastructure"
down_revision: Union[str, None] = "004_chat_rag_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create background_jobs table
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Collision-free internal UUID primary key"),
        sa.Column("project_id", sa.Uuid(), nullable=False, comment="Parent project workspace UUID"),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Initiating user UUID"),
        sa.Column("job_type", sa.String(length=50), nullable=False, comment="Approved background workload type identifier"),
        sa.Column("status", sa.String(length=20), server_default="queued", nullable=False, comment="Job lifecycle state: queued, running, retrying, completed, failed, cancelled"),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False, comment="Scheduling priority (-10 to 10)"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True, comment="Safe parameter dictionary"),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True, comment="Execution result references"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Redacted, safe error summary"),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False, comment="Execution attempt counter"),
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False, comment="Maximum retry attempts permitted"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Eligible execution timestamp"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True, comment="Initial execution timestamp"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="Terminal completion timestamp"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True, comment="Worker heartbeat timestamp"),
        sa.Column("locked_by", sa.String(length=100), nullable=True, comment="Worker instance identity"),
        sa.Column("lease_timeout_seconds", sa.Integer(), server_default="300", nullable=False, comment="Lease expiration window in seconds"),
        sa.Column("idempotency_key", sa.String(length=100), nullable=True, comment="Deduplication key"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Last modification timestamp"),
        # Foreign Key Constraints
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_background_jobs_project_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_background_jobs_user_id", ondelete="CASCADE"),
        # Primary Key Constraint
        sa.PrimaryKeyConstraint("id", name="pk_background_jobs"),
        # Check Constraints
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'retrying', 'completed', 'failed', 'cancelled')",
            name="ck_background_jobs_status",
        ),
        sa.CheckConstraint(
            "priority >= -10 AND priority <= 10",
            name="ck_background_jobs_priority_range",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_background_jobs_attempt_count_non_negative",
        ),
        sa.CheckConstraint(
            "max_retries >= 0",
            name="ck_background_jobs_max_retries_non_negative",
        ),
        sa.CheckConstraint(
            "lease_timeout_seconds >= 10 AND lease_timeout_seconds <= 3600",
            name="ck_background_jobs_lease_timeout_range",
        ),
        # Unique Deduplication Constraint
        sa.UniqueConstraint(
            "project_id", "job_type", "idempotency_key",
            name="uq_background_jobs_project_type_idempotency",
        ),
    )

    # 2. Indexes for O(1) claim performance and project filtering
    op.create_index("ix_background_jobs_project_id", "background_jobs", ["project_id"], unique=False)
    op.create_index("ix_background_jobs_user_id", "background_jobs", ["user_id"], unique=False)
    op.create_index("ix_background_jobs_job_type", "background_jobs", ["job_type"], unique=False)
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"], unique=False)
    op.create_index("ix_background_jobs_scheduled_at", "background_jobs", ["scheduled_at"], unique=False)
    op.create_index("ix_background_jobs_idempotency_key", "background_jobs", ["idempotency_key"], unique=False)
    op.create_index("ix_background_jobs_claim", "background_jobs", ["status", "scheduled_at", "priority"], unique=False)
    op.create_index("ix_background_jobs_project_status", "background_jobs", ["project_id", "status", "created_at"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_background_jobs_project_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_claim", table_name="background_jobs")
    op.drop_index("ix_background_jobs_idempotency_key", table_name="background_jobs")
    op.drop_index("ix_background_jobs_scheduled_at", table_name="background_jobs")
    op.drop_index("ix_background_jobs_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_job_type", table_name="background_jobs")
    op.drop_index("ix_background_jobs_user_id", table_name="background_jobs")
    op.drop_index("ix_background_jobs_project_id", table_name="background_jobs")

    # Drop table
    op.drop_table("background_jobs")

