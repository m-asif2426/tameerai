"""
TameerAI - Construction Cost Intelligence Pydantic Schemas (Phase 01C.4)

Defines Pydantic v2 schemas for MaterialRate, BOQAnalysis, and BOQItem.
Matches frontend TypeScript contracts (src/types/cost.ts) with camelCase serialization,
exact Decimal financial precision, non-negative rate validation, and localized unit labels.
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

class MaterialTrendEnum(str, Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class RateVerificationStatusEnum(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    STALE = "stale"


class BOQAnalysisStatusEnum(str, Enum):
    UNPROCESSED = "unprocessed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# MaterialRate Schemas
# ---------------------------------------------------------------------------

class MaterialRateBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    city: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50, description="steel, cement, bricks, aggregates, labor, general")
    name: str = Field(..., min_length=2, max_length=150)
    name_urdu: Optional[str] = Field(default=None, alias="nameUrdu", serialization_alias="nameUrdu")
    spec: Optional[str] = Field(default=None, max_length=200)
    spec_urdu: Optional[str] = Field(default=None, alias="specUrdu", serialization_alias="specUrdu")
    unit: str = Field(..., max_length=50)
    unit_urdu: Optional[str] = Field(default=None, alias="unitUrdu", serialization_alias="unitUrdu")
    rate_pkr: float = Field(..., ge=0.0, alias="ratePkr", serialization_alias="ratePkr")
    change_pct: float = Field(default=0.0, alias="changePct", serialization_alias="changePct")
    trend: str = Field(default="neutral")
    primary_brands: Optional[str] = Field(default=None, alias="primaryBrands", serialization_alias="primaryBrands")
    observed_at: datetime = Field(..., alias="observedAt", serialization_alias="observedAt")
    source_name: str = Field(..., alias="sourceName", serialization_alias="sourceName")
    source_url: Optional[str] = Field(default=None, alias="sourceUrl", serialization_alias="sourceUrl")
    verification_status: str = Field(default="unverified", alias="verificationStatus", serialization_alias="verificationStatus")


class MaterialRateCreate(MaterialRateBase):
    pass


class MaterialRateRead(BaseModel):
    """
    Material rate response matching `MaterialCostCard` (src/types/cost.ts).
    Exposes numeric pricing and formatted display fields.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    city: str
    category: str
    name: str
    name_urdu: Optional[str] = Field(default=None, alias="nameUrdu", serialization_alias="nameUrdu")
    spec: Optional[str] = None
    unit: str
    unit_urdu: Optional[str] = Field(default=None, alias="unitUrdu", serialization_alias="unitUrdu")
    rate_pkr: float = Field(..., alias="ratePkr", serialization_alias="ratePkr")
    current_price: str = Field(..., alias="currentPrice", serialization_alias="currentPrice")
    change_pct: float = Field(default=0.0, alias="changePct", serialization_alias="changePct")
    trend: str
    primary_brands: Optional[str] = Field(default=None, alias="primaryBrands", serialization_alias="primaryBrands")
    observed_at: datetime = Field(..., alias="observedAt", serialization_alias="observedAt")
    source_name: str = Field(..., alias="sourceName", serialization_alias="sourceName")
    source_url: Optional[str] = Field(default=None, alias="sourceUrl", serialization_alias="sourceUrl")
    verification_status: str = Field(..., alias="verificationStatus", serialization_alias="verificationStatus")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_material(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            rate = float(data.rate_pkr) if data.rate_pkr is not None else 0.0
            return {
                "id": data.id,
                "city": data.city,
                "category": data.category,
                "name": data.name,
                "nameUrdu": data.name_urdu or data.name,
                "spec": data.spec,
                "unit": data.unit,
                "unitUrdu": data.unit_urdu or data.unit,
                "ratePkr": rate,
                "rate_pkr": rate,
                "currentPrice": f"PKR {rate:,.2f} / {data.unit}",
                "current_price": f"PKR {rate:,.2f} / {data.unit}",
                "changePct": float(data.change_pct) if data.change_pct is not None else 0.0,
                "change_pct": float(data.change_pct) if data.change_pct is not None else 0.0,
                "trend": data.trend,
                "primaryBrands": data.primary_brands or "",
                "primary_brands": data.primary_brands or "",
                "observedAt": data.observed_at,
                "observed_at": data.observed_at,
                "sourceName": data.source_name,
                "source_name": data.source_name,
                "sourceUrl": data.source_url,
                "source_url": data.source_url,
                "verificationStatus": data.verification_status,
                "verification_status": data.verification_status,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data


# ---------------------------------------------------------------------------
# BOQItem Schemas
# ---------------------------------------------------------------------------

class BOQItemBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    phase: str
    phase_urdu: Optional[str] = Field(default=None, alias="phaseUrdu", serialization_alias="phaseUrdu")
    item_code: Optional[str] = Field(default=None, alias="itemCode", serialization_alias="itemCode")
    description: str
    description_urdu: Optional[str] = Field(default=None, alias="descriptionUrdu", serialization_alias="descriptionUrdu")
    spec: Optional[str] = None
    unit: str
    unit_urdu: Optional[str] = Field(default=None, alias="unitUrdu", serialization_alias="unitUrdu")
    quantity: Decimal = Field(default=Decimal("0.000"), ge=Decimal("0.000"), le=Decimal("999999999.999"))
    boq_base_rate: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("9999999999.99"), alias="boqBaseRate", serialization_alias="boqBaseRate")
    current_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("9999999999.99"), alias="currentPrice", serialization_alias="currentPrice")
    budget_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("999999999999.99"), alias="budgetAmount", serialization_alias="budgetAmount")
    estimated_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("999999999999.99"), alias="estimatedAmount", serialization_alias="estimatedAmount")
    overrun_amount: Decimal = Field(default=Decimal("0.00"), alias="overrunAmount", serialization_alias="overrunAmount")
    variance_pct: Decimal = Field(default=Decimal("0.00"), alias="variancePct", serialization_alias="variancePct")
    risk_level: Optional[str] = Field(default=None, alias="riskLevel", serialization_alias="riskLevel")


class BOQItemCreate(BOQItemBase):
    analysis_id: Optional[UUID] = Field(default=None, alias="analysisId", serialization_alias="analysisId")
    material_rate_id: Optional[UUID] = Field(default=None, alias="materialRateId", serialization_alias="materialRateId")


class BOQItemRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    analysis_id: UUID = Field(..., alias="analysisId", serialization_alias="analysisId")
    material_rate_id: Optional[UUID] = Field(default=None, alias="materialRateId", serialization_alias="materialRateId")
    phase: str
    phase_urdu: Optional[str] = Field(default=None, alias="phaseUrdu", serialization_alias="phaseUrdu")
    item_code: Optional[str] = Field(default=None, alias="itemCode", serialization_alias="itemCode")
    description: str
    description_urdu: Optional[str] = Field(default=None, alias="descriptionUrdu", serialization_alias="descriptionUrdu")
    spec: Optional[str] = None
    unit: str
    unit_urdu: Optional[str] = Field(default=None, alias="unitUrdu", serialization_alias="unitUrdu")
    quantity: float = Field(default=0.0)
    boq_base_rate: float = Field(default=0.0, alias="boqBaseRate", serialization_alias="boqBaseRate")
    current_price: float = Field(default=0.0, alias="currentPrice", serialization_alias="currentPrice")
    budget_amount: float = Field(default=0.0, alias="budgetAmount", serialization_alias="budgetAmount")
    estimated_amount: float = Field(default=0.0, alias="estimatedAmount", serialization_alias="estimatedAmount")
    overrun_amount: float = Field(default=0.0, alias="overrunAmount", serialization_alias="overrunAmount")
    variance_pct: float = Field(default=0.0, alias="variancePct", serialization_alias="variancePct")
    risk_level: Optional[str] = Field(default=None, alias="riskLevel", serialization_alias="riskLevel")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_boq_item(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            return {
                "id": data.id,
                "analysisId": data.analysis_id,
                "analysis_id": data.analysis_id,
                "materialRateId": data.material_rate_id,
                "material_rate_id": data.material_rate_id,
                "phase": data.phase,
                "phaseUrdu": data.phase_urdu,
                "itemCode": data.item_code,
                "item_code": data.item_code,
                "description": data.description,
                "descriptionUrdu": data.description_urdu,
                "spec": data.spec,
                "unit": data.unit,
                "unitUrdu": data.unit_urdu,
                "quantity": float(data.quantity) if data.quantity is not None else 0.0,
                "boqBaseRate": float(data.boq_base_rate) if data.boq_base_rate is not None else 0.0,
                "boq_base_rate": float(data.boq_base_rate) if data.boq_base_rate is not None else 0.0,
                "currentPrice": float(data.current_price) if data.current_price is not None else 0.0,
                "current_price": float(data.current_price) if data.current_price is not None else 0.0,
                "budgetAmount": float(data.budget_amount) if data.budget_amount is not None else 0.0,
                "budget_amount": float(data.budget_amount) if data.budget_amount is not None else 0.0,
                "estimatedAmount": float(data.estimated_amount) if data.estimated_amount is not None else 0.0,
                "estimated_amount": float(data.estimated_amount) if data.estimated_amount is not None else 0.0,
                "overrunAmount": float(data.overrun_amount) if data.overrun_amount is not None else 0.0,
                "overrun_amount": float(data.overrun_amount) if data.overrun_amount is not None else 0.0,
                "variancePct": float(data.variance_pct) if data.variance_pct is not None else 0.0,
                "variance_pct": float(data.variance_pct) if data.variance_pct is not None else 0.0,
                "riskLevel": data.risk_level,
                "risk_level": data.risk_level,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data


# ---------------------------------------------------------------------------
# BOQAnalysis Schemas
# ---------------------------------------------------------------------------

class BOQAnalysisBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    project_id: Optional[UUID] = Field(default=None, alias="projectId", serialization_alias="projectId")
    document_id: Optional[UUID] = Field(default=None, alias="documentId", serialization_alias="documentId")
    status: str = Field(default="unprocessed")
    project_budget: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("999999999999.99"), alias="projectBudget", serialization_alias="projectBudget")
    estimated_cost: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("999999999999.99"), alias="estimatedCost", serialization_alias="estimatedCost")
    current_cost: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("999999999999.99"), alias="currentCost", serialization_alias="currentCost")
    risk_indicator: str = Field(default="Low", alias="riskIndicator", serialization_alias="riskIndicator")
    summary: Optional[str] = None
    summary_urdu: Optional[str] = Field(default=None, alias="summaryUrdu", serialization_alias="summaryUrdu")


class BOQAnalysisCreate(BOQAnalysisBase):
    pass


class BOQAnalysisRead(BaseModel):
    """
    BOQ analysis overview matching `ProjectCostOverview` (src/types/cost.ts).
    Exposes exact numeric values (or null if unestimated).
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
    project_budget: Optional[float] = Field(default=None, alias="projectBudget", serialization_alias="projectBudget")
    estimated_cost: Optional[float] = Field(default=None, alias="estimatedCost", serialization_alias="estimatedCost")
    current_cost: Optional[float] = Field(default=None, alias="currentCost", serialization_alias="currentCost")
    cost_variance: Optional[float] = Field(default=None, alias="costVariance", serialization_alias="costVariance")
    variance_percentage: Optional[float] = Field(default=None, alias="variancePercentage", serialization_alias="variancePercentage")
    risk_indicator: str = Field(default="Low", alias="riskIndicator", serialization_alias="riskIndicator")
    summary: Optional[str] = None
    summary_urdu: Optional[str] = Field(default=None, alias="summaryUrdu", serialization_alias="summaryUrdu")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt", serialization_alias="completedAt")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt", serialization_alias="updatedAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_boq_analysis(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            pb = float(data.project_budget) if data.project_budget is not None else None
            ec = float(data.estimated_cost) if data.estimated_cost is not None else None
            cc = float(data.current_cost) if data.current_cost is not None else None
            cv = float(data.cost_variance) if data.cost_variance is not None else None
            vp = float(data.variance_percentage) if data.variance_percentage is not None else None
            return {
                "id": data.id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "documentId": data.document_id,
                "document_id": data.document_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "status": data.status,
                "projectBudget": pb,
                "project_budget": pb,
                "estimatedCost": ec,
                "estimated_cost": ec,
                "currentCost": cc,
                "current_cost": cc,
                "costVariance": cv,
                "cost_variance": cv,
                "variancePercentage": vp,
                "variance_percentage": vp,
                "riskIndicator": data.risk_indicator,
                "risk_indicator": data.risk_indicator,
                "summary": data.summary,
                "summaryUrdu": data.summary_urdu,
                "completedAt": data.completed_at,
                "completed_at": data.completed_at,
                "createdAt": data.created_at,
                "created_at": data.created_at,
                "updatedAt": data.updated_at,
                "updated_at": data.updated_at,
            }
        return data
