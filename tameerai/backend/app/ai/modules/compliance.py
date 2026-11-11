"""
TameerAI - Compliance Intelligence Architecture Contracts (Phase 03A)
Defines interfaces and domain contracts for Pakistani building code compliance analysis.
Supports PBC 2021, LDA, CDA, SBCA, and local municipal bylaws.
"""

from enum import Enum
from typing import List, Optional, Protocol, runtime_checkable
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.schemas.response import AIResponse, WarningCard


class ViolationSeverity(str, Enum):
    CRITICAL = "critical"      # Life-safety, structural deficit, missing egress
    MAJOR = "major"            # Significant setback, FAR, or height limit breach
    MINOR = "minor"            # Documentation or labeling non-conformity
    ADVISORY = "advisory"      # Recommended best-practice improvement


class ComplianceRuleEvaluation(BaseModel):
    """Evaluation result of a single regulatory rule against project parameters."""
    rule_code: str = Field(..., description="e.g. PBC-2021-CH4-SEC2")
    rule_title: str = Field(...)
    authority: str = Field(..., description="e.g. PBC, LDA, CDA, SBCA")
    clause_reference: str = Field(...)
    page_number: Optional[int] = None
    severity: ViolationSeverity = Field(default=ViolationSeverity.MAJOR)
    passed: bool = Field(...)
    observed_value: Optional[str] = None
    required_value: Optional[str] = None
    finding_summary: str = Field(...)
    recommendation: str = Field(...)
    cad_pin_coordinates: Optional[dict] = None  # {sheet_index, x, y}


class ComplianceAnalysisRequest(BaseModel):
    """Input payload for building compliance evaluation."""
    project_id: UUID = Field(...)
    building_type: str = Field(..., description="e.g. Commercial G+12, Residential, Industrial")
    city: str = Field(..., description="e.g. Lahore, Islamabad, Karachi")
    governing_authority: str = Field(..., description="e.g. LDA, CDA, SBCA")
    total_floors: int = Field(..., ge=1)
    plot_area_sqft: float = Field(..., gt=0)
    covered_area_sqft: float = Field(..., gt=0)
    front_setback_ft: Optional[float] = None
    rear_setback_ft: Optional[float] = None
    side_setbacks_ft: Optional[List[float]] = None
    document_ids: List[UUID] = Field(default_factory=list)


class ComplianceAnalysisResult(BaseModel):
    """Structured compliance assessment outcome."""
    audit_id: Optional[UUID] = None
    project_id: UUID = Field(...)
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    total_rules_checked: int = Field(default=0, ge=0)
    passed_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    violation_count: int = Field(default=0, ge=0)
    evaluations: List[ComplianceRuleEvaluation] = Field(default_factory=list)
    ai_advisory: Optional[AIResponse] = None


@runtime_checkable
class ComplianceIntelligenceService(Protocol):
    """Protocol for future compliance intelligence implementations."""
    async def evaluate_project_compliance(
        self, request: ComplianceAnalysisRequest
    ) -> ComplianceAnalysisResult:
        ...

