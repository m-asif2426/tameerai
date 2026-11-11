"""
TameerAI - Contract Intelligence Architecture Contracts (Phase 03A)
Defines interfaces and domain contracts for construction contract risk analysis
and FIDIC clause alignment.
"""

from enum import Enum
from typing import List, Optional, Protocol, runtime_checkable
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.schemas.response import AIResponse


class ContractRiskCategory(str, Enum):
    DELAY_LIQUIDATED_DAMAGES = "delay_liquidated_damages"
    VARIATION_AND_CLAIM_PROCEDURE = "variation_and_claim_procedure"
    PAYMENT_AND_RETENTION = "payment_and_retention"
    INDEMNIFICATION_AND_LIABILITY = "indemnification_and_liability"
    TERMINATION_AND_SUSPENSION = "termination_and_suspension"
    DISPUTE_RESOLUTION_AND_ARBITRATION = "dispute_resolution_and_arbitration"


class ContractRiskCard(BaseModel):
    """Structured assessment of an identified contractual risk or unfavorable clause."""
    category: ContractRiskCategory = Field(...)
    clause_number: str = Field(...)
    clause_title: str = Field(...)
    risk_level: str = Field(..., pattern="^(critical|high|medium|low)$")
    standard_fidic_clause: Optional[str] = Field(None, description="e.g. FIDIC Red Book 1999 Sub-Clause 20.1")
    contract_text_excerpt: str = Field(...)
    risk_explanation: str = Field(...)
    suggested_amendment: str = Field(...)
    notice_window_days: Optional[int] = Field(None, ge=1)


class ContractAnalysisRequest(BaseModel):
    """Input payload for construction agreement risk review."""
    project_id: UUID = Field(...)
    document_id: UUID = Field(...)
    contract_type: str = Field(default="FIDIC_Red_Book", description="e.g. FIDIC_Red_Book, PEC_Standard, Custom")
    user_role: str = Field(default="contractor", description="contractor, employer, engineer, subcontractor")


class ContractAnalysisResult(BaseModel):
    """Structured contract analysis outcome."""
    analysis_id: Optional[UUID] = None
    project_id: UUID = Field(...)
    document_id: UUID = Field(...)
    overall_risk_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    risk_cards: List[ContractRiskCard] = Field(default_factory=list)
    ai_advisory: Optional[AIResponse] = None


@runtime_checkable
class ContractIntelligenceService(Protocol):
    """Protocol for future contract risk intelligence implementations."""
    async def analyze_contract(
        self, request: ContractAnalysisRequest
    ) -> ContractAnalysisResult:
        ...

