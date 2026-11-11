"""
TameerAI - Contract Intelligence Pydantic Schemas (Phase 01C.4)

Defines Pydantic v2 schemas for ContractAnalysis and ContractRiskCard.
Matches frontend TypeScript contracts (src/types/contract.ts) with camelCase serialization,
nullable risk scores on 0.00-10.00 scale, clause page citations, and localized summaries.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums matching frontend contracts
# ---------------------------------------------------------------------------

class ContractRiskLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContractAnalysisStatusEnum(str, Enum):
    UNPROCESSED = "unprocessed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# ContractRiskCard Schemas
# ---------------------------------------------------------------------------

class ContractRiskCardBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    clause_title: str = Field(..., alias="clauseTitle", serialization_alias="clauseTitle")
    clause_title_urdu: Optional[str] = Field(default=None, alias="clauseTitleUrdu", serialization_alias="clauseTitleUrdu")
    fidic_reference: str = Field(..., alias="fidicReference", serialization_alias="fidicReference")
    page_number: Optional[int] = Field(default=None, ge=1, alias="pageNumber", serialization_alias="pageNumber")
    risk_level: ContractRiskLevelEnum = Field(..., alias="riskLevel", serialization_alias="riskLevel")
    risk_level_label: str = Field(..., alias="riskLevelLabel", serialization_alias="riskLevelLabel")
    risk_level_label_urdu: Optional[str] = Field(default=None, alias="riskLevelLabelUrdu", serialization_alias="riskLevelLabelUrdu")
    explanation: str = Field(...)
    explanation_urdu: Optional[str] = Field(default=None, alias="explanationUrdu", serialization_alias="explanationUrdu")
    recommendation: str = Field(...)
    recommendation_urdu: Optional[str] = Field(default=None, alias="recommendationUrdu", serialization_alias="recommendationUrdu")
    impact_metric: Optional[str] = Field(default=None, alias="impactMetric", serialization_alias="impactMetric")
    raw_clause_snippet: str = Field(..., alias="rawClauseSnippet", serialization_alias="rawClauseSnippet")
    citation_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="citationMetadata", serialization_alias="citationMetadata")


class ContractRiskCardCreate(ContractRiskCardBase):
    code: Optional[str] = Field(default=None, description="Public risk code (e.g. RISK-001)")
    analysis_id: Optional[UUID] = Field(default=None, alias="analysisId", serialization_alias="analysisId")


class ContractRiskCardRead(BaseModel):
    """
    Contract risk response matching frontend `ContractRiskCard` (src/types/contract.ts).
    Exposes `id` containing the public code (e.g. 'risk-delay' or 'RISK-001') and `uuid`.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: str = Field(..., description="Frontend-facing public risk card code")
    uuid: UUID = Field(..., description="Internal UUID primary key")
    analysis_id: UUID = Field(..., alias="analysisId", serialization_alias="analysisId")
    clause_title: str = Field(..., alias="clauseTitle", serialization_alias="clauseTitle")
    clause_title_urdu: Optional[str] = Field(default=None, alias="clauseTitleUrdu", serialization_alias="clauseTitleUrdu")
    fidic_reference: str = Field(..., alias="fidicReference", serialization_alias="fidicReference")
    page_number: Optional[int] = Field(default=None, alias="pageNumber", serialization_alias="pageNumber")
    risk_level: str = Field(..., alias="riskLevel", serialization_alias="riskLevel")
    risk_level_label: str = Field(..., alias="riskLevelLabel", serialization_alias="riskLevelLabel")
    risk_level_label_urdu: Optional[str] = Field(default=None, alias="riskLevelLabelUrdu", serialization_alias="riskLevelLabelUrdu")
    explanation: str
    explanation_urdu: Optional[str] = Field(default=None, alias="explanationUrdu", serialization_alias="explanationUrdu")
    recommendation: str
    recommendation_urdu: Optional[str] = Field(default=None, alias="recommendationUrdu", serialization_alias="recommendationUrdu")
    impact_metric: Optional[str] = Field(default=None, alias="impactMetric", serialization_alias="impactMetric")
    raw_clause_snippet: str = Field(..., alias="rawClauseSnippet", serialization_alias="rawClauseSnippet")
    citation_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="citationMetadata", serialization_alias="citationMetadata")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_risk_card(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            return {
                "id": data.code,
                "uuid": data.id,
                "analysisId": data.analysis_id,
                "analysis_id": data.analysis_id,
                "clauseTitle": data.clause_title,
                "clause_title": data.clause_title,
                "clauseTitleUrdu": data.clause_title_urdu or data.clause_title,
                "fidicReference": data.fidic_reference,
                "fidic_reference": data.fidic_reference,
                "pageNumber": data.page_number,
                "page_number": data.page_number,
                "riskLevel": data.risk_level,
                "risk_level": data.risk_level,
                "riskLevelLabel": data.risk_level_label,
                "risk_level_label": data.risk_level_label,
                "riskLevelLabelUrdu": data.risk_level_label_urdu or data.risk_level_label,
                "explanation": data.explanation,
                "explanationUrdu": data.explanation_urdu or data.explanation,
                "recommendation": data.recommendation,
                "recommendationUrdu": data.recommendation_urdu or data.recommendation,
                "impactMetric": data.impact_metric,
                "impact_metric": data.impact_metric,
                "rawClauseSnippet": data.raw_clause_snippet,
                "raw_clause_snippet": data.raw_clause_snippet,
                "citationMetadata": data.citation_metadata,
                "citation_metadata": data.citation_metadata,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data


# ---------------------------------------------------------------------------
# ContractAnalysis Schemas
# ---------------------------------------------------------------------------

class ContractAnalysisBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    project_id: Optional[UUID] = Field(default=None, alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")
    contract_title: str = Field(..., alias="contractTitle", serialization_alias="contractTitle")
    standard_format: str = Field(default="FIDIC Red Book 2017 & PEC", alias="standardFormat", serialization_alias="standardFormat")
    status: str = Field(default="unprocessed")
    summary: Optional[str] = None
    summary_urdu: Optional[str] = Field(default=None, alias="summaryUrdu", serialization_alias="summaryUrdu")


class ContractAnalysisCreate(ContractAnalysisBase):
    pass


class ContractAnalysisRead(BaseModel):
    """
    Contract analysis response matching `ContractAnalysisSummary` (src/types/contract.ts).
    Risk score is serialized as a JSON float (or null if unassessed).
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    contract_title: str = Field(..., alias="contractTitle", serialization_alias="contractTitle")
    standard_format: str = Field(..., alias="standardFormat", serialization_alias="standardFormat")
    status: str
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, alias="riskScore", serialization_alias="riskScore")
    risk_category: Optional[str] = Field(default=None, alias="riskCategory", serialization_alias="riskCategory")
    total_clauses_audited: int = Field(default=0, alias="totalClausesAudited", serialization_alias="totalClausesAudited")
    flagged_clauses_count: int = Field(default=0, alias="flaggedClausesCount", serialization_alias="flaggedClausesCount")
    summary: Optional[str] = None
    summary_urdu: Optional[str] = Field(default=None, alias="summaryUrdu", serialization_alias="summaryUrdu")
    last_audited: Optional[datetime] = Field(default=None, alias="lastAudited", serialization_alias="lastAudited")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt", serialization_alias="updatedAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_contract(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            rs = float(data.risk_score) if data.risk_score is not None else None
            return {
                "id": data.id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "documentId": data.document_id,
                "document_id": data.document_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "contractTitle": data.contract_title,
                "contract_title": data.contract_title,
                "standardFormat": data.standard_format,
                "standard_format": data.standard_format,
                "status": data.status,
                "riskScore": rs,
                "risk_score": rs,
                "riskCategory": data.risk_category,
                "risk_category": data.risk_category,
                "totalClausesAudited": data.total_clauses_audited,
                "total_clauses_audited": data.total_clauses_audited,
                "flaggedClausesCount": data.flagged_clauses_count,
                "flagged_clauses_count": data.flagged_clauses_count,
                "summary": data.summary,
                "summaryUrdu": data.summary_urdu,
                "lastAudited": data.completed_at,
                "completed_at": data.completed_at,
                "createdAt": data.created_at,
                "created_at": data.created_at,
                "updatedAt": data.updated_at,
                "updated_at": data.updated_at,
            }
        return data

