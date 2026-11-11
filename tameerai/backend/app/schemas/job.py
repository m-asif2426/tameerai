"""
TameerAI - Background Job Pydantic Schemas (Phase 02G)

Defines request/response schemas for:
- Enqueuing background jobs with validated types and safe payloads
- Inspecting job status, execution attempts, and sanitized results
- Cancelling pending or running jobs
- Enforcing camelCase aliases for frontend compatibility
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.job import JobStatus, JobType


class BackgroundJobBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class BackgroundJobCreate(BackgroundJobBase):
    """Payload to enqueue a new project-scoped background job."""
    job_type: str = Field(
        ...,
        alias="jobType",
        serialization_alias="jobType",
        description="Approved job type identifier (e.g. synthetic_test, compliance_audit, contract_analysis, boq_extraction, report_generation)",
    )
    payload: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Safe parameter dictionary. Must NOT contain passwords, JWTs, or secrets.",
    )
    priority: int = Field(
        default=0,
        ge=-10,
        le=10,
        description="Execution priority (-10 to 10; higher numbers claim first)",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        alias="maxRetries",
        serialization_alias="maxRetries",
        description="Maximum retry attempts on transient failure",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="idempotencyKey",
        serialization_alias="idempotencyKey",
        description="Optional client token for deduplication and idempotent submission",
    )

    @field_validator("payload")
    @classmethod
    def validate_payload_safety_and_bounds(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return {}
        # Bound payload serialized size to 64KB
        try:
            serialized = json.dumps(v)
            if len(serialized.encode("utf-8")) > 65536:
                raise ValueError("Payload size exceeds maximum allowed limit of 64KB.")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid payload format: {exc}")

        # Check for simulated synthetic parameters bounds if present
        if "sleep_seconds" in v:
            sleep_sec = v.get("sleep_seconds")
            if not isinstance(sleep_sec, (int, float)) or sleep_sec < 0 or sleep_sec > 60:
                raise ValueError("Synthetic payload 'sleep_seconds' must be a numeric value between 0 and 60 seconds.")
        return v


class BackgroundJobCancel(BackgroundJobBase):
    """Optional payload when requesting job cancellation."""
    reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional cancellation rationale",
    )


class BackgroundJobRead(BackgroundJobBase):
    """Public read representation of a background job."""
    id: UUID
    project_id: UUID = Field(alias="projectId", serialization_alias="projectId")
    user_id: UUID = Field(alias="userId", serialization_alias="userId")
    job_type: str = Field(alias="jobType", serialization_alias="jobType")
    status: str
    priority: int
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = Field(default=None, alias="errorMessage", serialization_alias="errorMessage")
    attempt_count: int = Field(alias="attemptCount", serialization_alias="attemptCount")
    max_retries: int = Field(alias="maxRetries", serialization_alias="maxRetries")
    scheduled_at: datetime = Field(alias="scheduledAt", serialization_alias="scheduledAt")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt", serialization_alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt", serialization_alias="completedAt")
    idempotency_key: Optional[str] = Field(default=None, alias="idempotencyKey", serialization_alias="idempotencyKey")
    created_at: datetime = Field(alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt", serialization_alias="updatedAt")

