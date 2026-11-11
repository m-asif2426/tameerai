"""
TameerAI - Consulting Report Pydantic Schemas (Phase 01C.4)

Defines Pydantic v2 schemas for Report model.
Matches frontend TypeScript contracts (src/types/report.ts) with camelCase serialization,
public code aliasing (RPT-001), private storage key masking, and localized status fields.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums matching frontend contracts
# ---------------------------------------------------------------------------

class ReportCategoryEnum(str, Enum):
    COMPLIANCE = "compliance"
    CONTRACT = "contract"
    COST = "cost"
    EXECUTIVE_COMPREHENSIVE = "executive_comprehensive"


class ReportStatusEnum(str, Enum):
    CERTIFIED = "certified"
    ACTION_REQUIRED = "action_required"
    OVERRUN_ALERT = "overrun_alert"
    IN_REVIEW = "in_review"
    APPROVED = "approved"


# ---------------------------------------------------------------------------
# Report Schemas
# ---------------------------------------------------------------------------

class ReportBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    project_id: Optional[UUID] = Field(default=None, alias="projectId", serialization_alias="projectId")
    compliance_audit_id: Optional[UUID] = Field(default=None, alias="complianceAuditId", serialization_alias="complianceAuditId")
    contract_analysis_id: Optional[UUID] = Field(default=None, alias="contractAnalysisId", serialization_alias="contractAnalysisId")
    boq_analysis_id: Optional[UUID] = Field(default=None, alias="boqAnalysisId", serialization_alias="boqAnalysisId")
    category: str = Field(default="executive_comprehensive", description="compliance, contract, cost, executive_comprehensive")
    category_label: Optional[str] = Field(default=None, alias="categoryLabel", serialization_alias="categoryLabel")
    title: str = Field(..., min_length=2, max_length=255)
    title_urdu: Optional[str] = Field(default=None, alias="titleUrdu", serialization_alias="titleUrdu")
    status: str = Field(default="in_review")
    status_label: Optional[str] = Field(default=None, alias="statusLabel", serialization_alias="statusLabel")
    status_label_urdu: Optional[str] = Field(default=None, alias="statusLabelUrdu", serialization_alias="statusLabelUrdu")
    page_count: int = Field(default=1, ge=1, alias="pageCount", serialization_alias="pageCount")
    author: str = Field(default="TameerAI Engineering Intelligence")
    executive_summary: Optional[str] = Field(default="Draft engineering report dossier.", alias="executiveSummary", serialization_alias="executiveSummary")
    executive_summary_urdu: Optional[str] = Field(default=None, alias="executiveSummaryUrdu", serialization_alias="executiveSummaryUrdu")
    key_metric: Optional[str] = Field(default="Pending Assessment", alias="keyMetric", serialization_alias="keyMetric")


class ReportCreate(ReportBase):
    code: Optional[str] = Field(default=None, description="Public report code (e.g. RPT-001). Auto-assigned if omitted.")


class ReportRead(BaseModel):
    """
    Consulting report response matching frontend `ConsultingReport` (src/types/report.ts).
    Exposes `id` containing the public code (e.g. 'RPT-001') and `uuid`.
    Internal private file_path is strictly excluded from public responses.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: str = Field(..., description="Public-facing report code (e.g. RPT-001)")
    uuid: UUID = Field(..., description="Internal UUID primary key")
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    compliance_audit_id: Optional[UUID] = Field(default=None, alias="complianceAuditId", serialization_alias="complianceAuditId")
    contract_analysis_id: Optional[UUID] = Field(default=None, alias="contractAnalysisId", serialization_alias="contractAnalysisId")
    boq_analysis_id: Optional[UUID] = Field(default=None, alias="boqAnalysisId", serialization_alias="boqAnalysisId")
    title: str
    title_urdu: Optional[str] = Field(default=None, alias="titleUrdu", serialization_alias="titleUrdu")
    category: str
    category_label: str = Field(..., alias="categoryLabel", serialization_alias="categoryLabel")
    projectName: Optional[str] = None
    projectNameUrdu: Optional[str] = None
    date: str
    status: str
    status_label: str = Field(..., alias="statusLabel", serialization_alias="statusLabel")
    status_label_urdu: Optional[str] = Field(default=None, alias="statusLabelUrdu", serialization_alias="statusLabelUrdu")
    file_size: str = Field(..., alias="fileSize", serialization_alias="fileSize")
    page_count: int = Field(..., alias="pageCount", serialization_alias="pageCount")
    author: str
    executive_summary: str = Field(..., alias="executiveSummary", serialization_alias="executiveSummary")
    key_metric: str = Field(..., alias="keyMetric", serialization_alias="keyMetric")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_report(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            proj_name = data.project.name if getattr(data, "project", None) else ""
            proj_name_urdu = data.project.name_urdu if getattr(data, "project", None) else proj_name
            return {
                "id": data.code,
                "uuid": data.id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "complianceAuditId": data.compliance_audit_id,
                "compliance_audit_id": data.compliance_audit_id,
                "contractAnalysisId": data.contract_analysis_id,
                "contract_analysis_id": data.contract_analysis_id,
                "boqAnalysisId": data.boq_analysis_id,
                "boq_analysis_id": data.boq_analysis_id,
                "title": data.title,
                "titleUrdu": data.title_urdu or data.title,
                "category": data.category,
                "categoryLabel": data.category_label,
                "category_label": data.category_label,
                "projectName": proj_name,
                "projectNameUrdu": proj_name_urdu,
                "date": data.created_at.strftime("%b %d, %Y") if data.created_at else "",
                "status": data.status,
                "statusLabel": data.status_label,
                "status_label": data.status_label,
                "statusLabelUrdu": data.status_label_urdu or data.status_label,
                "fileSize": data.file_size,
                "file_size": data.file_size,
                "pageCount": data.page_count,
                "page_count": data.page_count,
                "author": data.author,
                "executiveSummary": data.executive_summary,
                "executive_summary": data.executive_summary,
                "keyMetric": data.key_metric,
                "key_metric": data.key_metric,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data

