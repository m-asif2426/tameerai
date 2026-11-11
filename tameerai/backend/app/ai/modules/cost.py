"""
TameerAI - BOQ & Cost Intelligence Architecture Contracts (Phase 03A)
Defines interfaces and domain contracts for construction quantity and cost analysis.
Enforces Decimal-based arithmetic to prevent floating-point rounding errors in financial estimations.
"""

from decimal import Decimal
from typing import List, Optional, Protocol, runtime_checkable
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.schemas.response import AIResponse


class BOQItemEvaluation(BaseModel):
    """Detailed rate evaluation for an individual Bill of Quantities item."""
    item_code: str = Field(...)
    description: str = Field(...)
    unit: str = Field(..., description="e.g. sq ft, cu ft, ton, running ft, bag")
    quantity: Decimal = Field(..., ge=0)
    contract_unit_rate: Decimal = Field(..., ge=0)
    market_benchmark_rate: Optional[Decimal] = Field(None, ge=0)
    variance_percentage: Optional[Decimal] = None
    rate_status: str = Field(..., pattern="^(standard|above_market|below_market|outlier)$")
    recommendation: Optional[str] = None


class BOQAnalysisRequest(BaseModel):
    """Input payload for bill of quantities rate verification."""
    project_id: UUID = Field(...)
    document_id: UUID = Field(...)
    market_region: str = Field(default="lahore", description="e.g. lahore, karachi, islamabad, rawalpindi")
    price_date: Optional[str] = None


class BOQAnalysisResult(BaseModel):
    """Structured outcome for BOQ extraction and rate benchmarking."""
    analysis_id: Optional[UUID] = None
    project_id: UUID = Field(...)
    document_id: UUID = Field(...)
    total_evaluated_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    market_benchmark_cost: Optional[Decimal] = Field(None, ge=0)
    items: List[BOQItemEvaluation] = Field(default_factory=list)
    ai_advisory: Optional[AIResponse] = None


@runtime_checkable
class CostIntelligenceService(Protocol):
    """Protocol for future BOQ and cost intelligence implementations."""
    async def analyze_boq_rates(
        self, request: BOQAnalysisRequest
    ) -> BOQAnalysisResult:
        ...

