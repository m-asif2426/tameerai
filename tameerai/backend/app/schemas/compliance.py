"""
TameerAI - Compliance & Building Code Pydantic Schemas (Phase 01C.4)

Defines Pydantic v2 schemas for ComplianceAudit and ComplianceFinding.
Matches frontend TypeScript contracts (src/types/compliance.ts) with camelCase serialization,
nullable unassessed scores, coordinate pin models, and regulatory source citations.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums matching frontend contracts
# ---------------------------------------------------------------------------

class ComplianceCategoryEnum(str, Enum):
    EGRESS = "egress"
    STRUCTURAL = "structural"
    ZONING = "zoning"
    FIRE = "fire"


class ComplianceStatusEnum(str, Enum):
    VIOLATION = "violation"
    WARNING = "warning"
    PASSED = "passed"


class AuditStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Pin Coordinates Schema
# ---------------------------------------------------------------------------

class CompliancePinCoordinates(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    x: Optional[float] = Field(default=None, description="Horizontal coordinate on drawing sheet")
    y: Optional[float] = Field(default=None, description="Vertical coordinate on drawing sheet")
    space: str = Field(default="normalized_percentage", description="Coordinate space: normalized_percentage, sheet_mm, pixel")

    @model_validator(mode="after")
    def validate_coordinates(self) -> "CompliancePinCoordinates":
        if self.space == "normalized_percentage":
            if self.x is not None and not (0.0 <= self.x <= 100.0):
                raise ValueError("Pin x coordinate in normalized_percentage space must be between 0.0 and 100.0")
            if self.y is not None and not (0.0 <= self.y <= 100.0):
                raise ValueError("Pin y coordinate in normalized_percentage space must be between 0.0 and 100.0")
        elif self.space in {"sheet_mm", "pixel"}:
            if self.x is not None and self.x < 0.0:
                raise ValueError("Pin x coordinate must be non-negative")
            if self.y is not None and self.y < 0.0:
                raise ValueError("Pin y coordinate must be non-negative")
        else:
            raise ValueError(f"Invalid coordinate space: '{self.space}'. Must be 'normalized_percentage', 'sheet_mm', or 'pixel'")
        return self


# ---------------------------------------------------------------------------
# ComplianceFinding Schemas
# ---------------------------------------------------------------------------

class ComplianceFindingBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    category: ComplianceCategoryEnum = Field(..., description="egress, structural, zoning, fire")
    category_name: str = Field(..., alias="categoryName", serialization_alias="categoryName")
    category_name_urdu: Optional[str] = Field(default=None, alias="categoryNameUrdu", serialization_alias="categoryNameUrdu")
    title: str = Field(..., min_length=2, max_length=200)
    title_urdu: Optional[str] = Field(default=None, alias="titleUrdu", serialization_alias="titleUrdu")
    status: ComplianceStatusEnum = Field(..., description="violation, warning, passed")
    required_value: str = Field(..., alias="requiredValue", serialization_alias="requiredValue")
    current_value: str = Field(..., alias="currentValue", serialization_alias="currentValue")
    variance: Optional[str] = Field(default=None)
    reference_code: str = Field(..., alias="referenceCode", serialization_alias="referenceCode")
    reference_clause: str = Field(..., alias="referenceClause", serialization_alias="referenceClause")
    location_grid: str = Field(..., alias="locationGrid", serialization_alias="locationGrid")
    sheet_number: Optional[str] = Field(default=None, alias="sheetNumber", serialization_alias="sheetNumber")
    description: str = Field(...)
    description_urdu: Optional[str] = Field(default=None, alias="descriptionUrdu", serialization_alias="descriptionUrdu")
    remedy: str = Field(...)
    remedy_urdu: Optional[str] = Field(default=None, alias="remedyUrdu", serialization_alias="remedyUrdu")
    pin_coordinates: Optional[CompliancePinCoordinates] = Field(default=None, alias="pinCoordinates", serialization_alias="pinCoordinates")


class ComplianceFindingCreate(ComplianceFindingBase):
    code: Optional[str] = Field(default=None, description="Public finding code (e.g. FIND-001)")
    audit_id: Optional[UUID] = Field(default=None, alias="auditId", serialization_alias="auditId")
    project_id: Optional[UUID] = Field(default=None, alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")


class ComplianceFindingRead(BaseModel):
    """
    Finding response matching frontend `ComplianceRuleItem` (src/types/compliance.ts).
    Exposes `id` containing the public code (e.g. 'FIND-001') and `uuid` for database joins.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: str = Field(..., description="Frontend-facing finding code (e.g. FIND-001)")
    uuid: UUID = Field(..., description="Internal UUID primary key")
    audit_id: UUID = Field(..., alias="auditId", serialization_alias="auditId")
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")
    category: str
    category_name: str = Field(..., alias="categoryName", serialization_alias="categoryName")
    category_name_urdu: Optional[str] = Field(default=None, alias="categoryNameUrdu", serialization_alias="categoryNameUrdu")
    title: str
    title_urdu: Optional[str] = Field(default=None, alias="titleUrdu", serialization_alias="titleUrdu")
    status: str
    required_value: str = Field(..., alias="requiredValue", serialization_alias="requiredValue")
    current_value: str = Field(..., alias="currentValue", serialization_alias="currentValue")
    variance: Optional[str] = None
    reference_code: str = Field(..., alias="referenceCode", serialization_alias="referenceCode")
    reference_clause: str = Field(..., alias="referenceClause", serialization_alias="referenceClause")
    location_grid: str = Field(..., alias="locationGrid", serialization_alias="locationGrid")
    description: str
    description_urdu: Optional[str] = Field(default=None, alias="descriptionUrdu", serialization_alias="descriptionUrdu")
    remedy: str
    remedy_urdu: Optional[str] = Field(default=None, alias="remedyUrdu", serialization_alias="remedyUrdu")
    pin_coordinates: CompliancePinCoordinates = Field(..., alias="pinCoordinates", serialization_alias="pinCoordinates")
    is_resolved: bool = Field(default=False, alias="isResolved", serialization_alias="isResolved")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_finding(cls, data: any) -> any:
        if hasattr(data, "__table__"):
            pin_x = float(data.pin_x) if data.pin_x is not None else 0.0
            pin_y = float(data.pin_y) if data.pin_y is not None else 0.0
            return {
                "id": data.code,
                "uuid": data.id,
                "auditId": data.audit_id,
                "audit_id": data.audit_id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "documentId": data.document_id,
                "document_id": data.document_id,
                "category": data.category,
                "categoryName": data.category_name,
                "category_name": data.category_name,
                "categoryNameUrdu": data.category_name_urdu or data.category_name,
                "title": data.title,
                "titleUrdu": data.title_urdu or data.title,
                "status": data.status,
                "requiredValue": data.required_value,
                "required_value": data.required_value,
                "currentValue": data.current_value,
                "current_value": data.current_value,
                "variance": data.variance,
                "referenceCode": data.reference_code,
                "reference_code": data.reference_code,
                "referenceClause": data.reference_clause,
                "reference_clause": data.reference_clause,
                "locationGrid": data.location_grid,
                "location_grid": data.location_grid,
                "description": data.description,
                "descriptionUrdu": data.description_urdu or data.description,
                "remedy": data.remedy,
                "remedyUrdu": data.remedy_urdu or data.remedy,
                "pinCoordinates": {
                    "x": pin_x,
                    "y": pin_y,
                    "space": data.coordinate_space or "normalized_percentage",
                },
                "isResolved": data.is_resolved,
                "is_resolved": data.is_resolved,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data


# ---------------------------------------------------------------------------
# ComplianceAudit Schemas
# ---------------------------------------------------------------------------

class ComplianceAuditBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    project_id: Optional[UUID] = Field(default=None, alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")
    status: str = Field(default="pending")
    governing_code: Optional[str] = Field(default=None, alias="governingCode", serialization_alias="governingCode")
    summary: Optional[str] = None
    summary_urdu: Optional[str] = Field(default=None, alias="summaryUrdu", serialization_alias="summaryUrdu")


class ComplianceAuditCreate(ComplianceAuditBase):
    pass


class ComplianceAuditRead(BaseModel):
    """
    Compliance audit response matching `ComplianceAuditSummary` (src/types/compliance.ts).
    Overall score is nullable (None if unassessed).
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    status: str
    overall_score: Optional[int] = Field(default=None, ge=0, le=100, alias="overallScore", serialization_alias="overallScore")
    total_checks: int = Field(default=0, alias="totalChecks", serialization_alias="totalChecks")
    passed_count: int = Field(default=0, alias="passedCount", serialization_alias="passedCount")
    warning_count: int = Field(default=0, alias="warningCount", serialization_alias="warningCount")
    violation_count: int = Field(default=0, alias="violationCount", serialization_alias="violationCount")
    governing_code: Optional[str] = Field(default=None, alias="governingCode", serialization_alias="governingCode")
    summary: Optional[str] = None
    summary_urdu: Optional[str] = Field(default=None, alias="summaryUrdu", serialization_alias="summaryUrdu")
    assessed_at: Optional[datetime] = Field(default=None, alias="lastAudited", serialization_alias="lastAudited")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt", serialization_alias="updatedAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_audit(cls, data: any) -> any:
        if hasattr(data, "__table__"):
            return {
                "id": data.id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "documentId": data.document_id,
                "document_id": data.document_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "status": data.status,
                "overallScore": data.overall_score,
                "overall_score": data.overall_score,
                "totalChecks": data.total_checks,
                "total_checks": data.total_checks,
                "passedCount": data.passed_count,
                "passed_count": data.passed_count,
                "warningCount": data.warning_count,
                "warning_count": data.warning_count,
                "violationCount": data.violation_count,
                "violation_count": data.violation_count,
                "governingCode": data.governing_code,
                "governing_code": data.governing_code,
                "summary": data.summary,
                "summaryUrdu": data.summary_urdu,
                "lastAudited": data.assessed_at,
                "assessed_at": data.assessed_at,
                "createdAt": data.created_at,
                "created_at": data.created_at,
                "updatedAt": data.updated_at,
                "updated_at": data.updated_at,
            }
        return data
