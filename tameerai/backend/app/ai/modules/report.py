"""
TameerAI - Engineering Report Intelligence Architecture Contracts (Phase 03A)
Defines interfaces and domain contracts for synthesizing multi-source
engineering reports (compliance, contract risks, cost variations).
"""

from typing import List, Optional, Protocol, runtime_checkable
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.schemas.response import AIResponse


class ReportSectionDraft(BaseModel):
    """Draft content for a specific section of an engineering report."""
    section_title: str = Field(...)
    section_order: int = Field(default=1, ge=1)
    content: str = Field(...)
    content_urdu: Optional[str] = None
    citations: List[dict] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)


class ReportGenerationRequest(BaseModel):
    """Input payload for generating an engineering advisory report draft."""
    project_id: UUID = Field(...)
    report_title: str = Field(...)
    report_type: str = Field(..., pattern="^(compliance|contract|cost|executive_summary)$")
    include_urdu_summary: bool = Field(default=True)
    compliance_audit_id: Optional[UUID] = None
    contract_analysis_id: Optional[UUID] = None
    boq_analysis_id: Optional[UUID] = None


class ReportGenerationResult(BaseModel):
    """Structured report compilation result."""
    report_id: Optional[UUID] = None
    project_id: UUID = Field(...)
    executive_summary: str = Field(...)
    executive_summary_urdu: Optional[str] = None
    sections: List[ReportSectionDraft] = Field(default_factory=list)
    ai_advisory: Optional[AIResponse] = None
    is_signed_off: bool = Field(default=False, frozen=True)


@runtime_checkable
class ReportIntelligenceService(Protocol):
    """Protocol for future report generation implementations."""
    async def generate_engineering_report(
        self, request: ReportGenerationRequest
    ) -> ReportGenerationResult:
        ...

