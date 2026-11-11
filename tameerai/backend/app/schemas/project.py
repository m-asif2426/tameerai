"""
TameerAI - Project Workspace Pydantic Schemas (Phase 01C.3 / Phase 02C)

Defines Pydantic v2 schemas for Project, ProjectMember, and ProjectActivity.
Ensures camelCase serialization matching frontend TypeScript contracts
(src/types/project.ts), safe validation, mass-assignment protection,
and public code aliasing.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# ---------------------------------------------------------------------------
# Enums matching frontend contracts and DB check constraints
# ---------------------------------------------------------------------------

class ProjectCity(str, Enum):
    LAHORE = "Lahore"
    KARACHI = "Karachi"
    ISLAMABAD = "Islamabad"


class ProjectStatus(str, Enum):
    UNDER_ANALYSIS = "Under Analysis"
    ACTIVE = "Active"
    PLANNING = "Planning"
    COMPLETED = "Completed"


class ProjectRisk(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ProjectMemberRole(str, Enum):
    LEAD_ENGINEER = "lead_engineer"
    ARCHITECT = "architect"
    CONTRACTOR = "contractor"
    VIEWER = "viewer"


class ActivityType(str, Enum):
    COMPLIANCE = "compliance"
    CONTRACT = "contract"
    COST = "cost"
    UPLOAD = "upload"
    GENERAL = "general"


ALLOWED_STATUSES = {"Under Analysis", "Active", "Planning", "Completed"}
ALLOWED_RISKS = {"Low", "Medium", "High"}
ALLOWED_MEMBER_ROLES = {"lead_engineer", "architect", "contractor", "viewer"}

# Maximum supported monetary bounds matching PostgreSQL NUMERIC(15, 2)
# NUMERIC(15, 2) supports up to 13 digits before decimal: 999,999,999,999.99 PKR.
MAX_MONETARY_RAW = Decimal("999999999999.99")
# 1 Crore = 10,000,000 PKR.
# At max scale of 4 decimals, 99999.9999 Crore = 999,999,999,000.00 PKR <= MAX_MONETARY_RAW.
# 100,000 Crore = 1,000,000,000,000.00 PKR, which exceeds NUMERIC(15, 2).
MAX_MONETARY_CRORE = Decimal("99999.9999")


def validate_raw_amount(v: Optional[Decimal]) -> Optional[Decimal]:
    """Validates raw PKR currency values against NUMERIC(15,2) bounds, finiteness, and scale."""
    if v is None:
        return v
    if not v.is_finite():
        raise ValueError("Amount must be a finite number.")
    if v < Decimal("0.00"):
        raise ValueError("Amount cannot be negative.")
    if v > MAX_MONETARY_RAW:
        raise ValueError(f"Raw PKR amount exceeds maximum supported limit of {MAX_MONETARY_RAW} PKR.")
    if v.as_tuple().exponent < -2:
        raise ValueError("Raw PKR currency amounts cannot have more than 2 decimal places.")
    return v


def validate_crore_amount(v: Optional[Decimal]) -> Optional[Decimal]:
    """
    Validates Crore currency values:
    Converts Crore values to PKR using Decimal before comparing to the database maximum.
    Enforces maximum 4 decimal places and finiteness.
    """
    if v is None:
        return v
    if not v.is_finite():
        raise ValueError("Amount must be a finite number.")
    if v < Decimal("0.0000"):
        raise ValueError("Amount cannot be negative.")
    # Convert crore values to PKR using Decimal before comparing to database maximum
    raw_equivalent = v * Decimal("10000000")
    if raw_equivalent > MAX_MONETARY_RAW or v > MAX_MONETARY_CRORE:
        raise ValueError(
            f"Crore amount exceeds maximum supported limit of {MAX_MONETARY_CRORE} Crore ({MAX_MONETARY_RAW} PKR)."
        )
    if v.as_tuple().exponent < -4:
        raise ValueError("Crore currency amounts cannot have more than 4 decimal places.")
    return v


# ---------------------------------------------------------------------------
# Project Schemas
# ---------------------------------------------------------------------------

class ProjectBase(BaseModel):
    """Shared core project attributes."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    name: str = Field(..., min_length=2, max_length=200, description="Project name")
    name_urdu: Optional[str] = Field(
        default=None,
        max_length=200,
        alias="nameUrdu",
        serialization_alias="nameUrdu",
        description="Urdu project name",
    )
    description: Optional[str] = Field(
        default=None,
        description="Project scope description",
    )
    location: str = Field(..., min_length=2, max_length=255, description="Site location")
    location_urdu: Optional[str] = Field(
        default=None,
        max_length=255,
        alias="locationUrdu",
        serialization_alias="locationUrdu",
    )
    city: str = Field(default="Lahore", min_length=2, max_length=50, description="Jurisdictional city")
    city_urdu: Optional[str] = Field(
        default="لاہور",
        max_length=50,
        alias="cityUrdu",
        serialization_alias="cityUrdu",
    )
    type: str = Field(default="Commercial", max_length=100, description="Building typology")
    type_urdu: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="typeUrdu",
        serialization_alias="typeUrdu",
    )
    budget_crore: Decimal = Field(
        default=Decimal("0.0"),
        ge=Decimal("0.0"),
        le=MAX_MONETARY_CRORE,
        alias="budgetCrore",
        serialization_alias="budgetCrore",
        description="Budget in Crore PKR (1 Crore = 10,000,000 PKR)",
    )
    floors: int = Field(default=1, ge=1, le=150, description="Number of floors")
    area_sqft: str = Field(
        default="N/A",
        alias="areaSqft",
        serialization_alias="areaSqft",
        description="Covered area string",
    )
    engineer: Optional[str] = Field(default=None, max_length=150)
    governing_authority: Optional[str] = Field(
        default=None,
        max_length=150,
        alias="governingAuthority",
        serialization_alias="governingAuthority",
    )
    start_date: Optional[date] = Field(
        default=None,
        alias="startDate",
        serialization_alias="startDate",
    )
    expected_completion_date: Optional[date] = Field(
        default=None,
        alias="expectedCompletionDate",
        serialization_alias="expectedCompletionDate",
    )
    handover_date: Optional[str] = Field(
        default=None,
        alias="handoverDate",
        serialization_alias="handoverDate",
    )


class ProjectCreate(ProjectBase):
    """
    Payload for creating a project workspace.
    Mass-assignment protected: extra fields are forbidden.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional pre-assigned public code (e.g. PRJ-001). Auto-generated safely if omitted.",
    )
    budget_raw: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=MAX_MONETARY_RAW,
        alias="budgetRaw",
        serialization_alias="budgetRaw",
        description="Authoritative budget in exact raw PKR (takes precedence over budgetCrore)",
    )
    status: Optional[str] = Field(default="Planning")
    status_urdu: Optional[str] = Field(
        default="منصوبہ بندی (Planning)",
        alias="statusUrdu",
        serialization_alias="statusUrdu",
    )
    risk: Optional[str] = Field(default="Low")
    risk_urdu: Optional[str] = Field(
        default="کم (Low)",
        alias="riskUrdu",
        serialization_alias="riskUrdu",
    )

    @field_validator("budget_raw")
    @classmethod
    def validate_budget_raw_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return validate_raw_amount(v)

    @field_validator("budget_crore")
    @classmethod
    def validate_budget_crore_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return validate_crore_amount(v)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")
        return v

    @field_validator("risk")
    @classmethod
    def validate_risk(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_RISKS:
            raise ValueError(f"Invalid risk '{v}'. Allowed: {', '.join(sorted(ALLOWED_RISKS))}")
        return v

    def get_authoritative_budget_raw(self) -> Decimal:
        """Returns the authoritative raw PKR budget, converting budget_crore if budget_raw is omitted."""
        if self.budget_raw is not None:
            return Decimal(str(self.budget_raw)).quantize(Decimal("0.01"))
        if self.budget_crore is not None:
            return (Decimal(str(self.budget_crore)) * Decimal("10000000")).quantize(Decimal("0.01"))
        return Decimal("0.00")


class ProjectUpdate(BaseModel):
    """
    Payload for updating project metadata.
    Mass-assignment protected: extra fields (id, uuid, user_id, code, compliance_score, created_at) are forbidden.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    name_urdu: Optional[str] = Field(default=None, alias="nameUrdu", serialization_alias="nameUrdu")
    description: Optional[str] = None
    location: Optional[str] = Field(default=None, min_length=2, max_length=255)
    location_urdu: Optional[str] = Field(default=None, alias="locationUrdu", serialization_alias="locationUrdu")
    city: Optional[str] = Field(default=None, min_length=2, max_length=50)
    city_urdu: Optional[str] = Field(default=None, alias="cityUrdu", serialization_alias="cityUrdu")
    type: Optional[str] = Field(default=None, max_length=100)
    type_urdu: Optional[str] = Field(default=None, alias="typeUrdu", serialization_alias="typeUrdu")
    budget_crore: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=MAX_MONETARY_CRORE, alias="budgetCrore", serialization_alias="budgetCrore")
    budget_raw: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=MAX_MONETARY_RAW, alias="budgetRaw", serialization_alias="budgetRaw")
    spent_crore: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=MAX_MONETARY_CRORE, alias="spentCrore", serialization_alias="spentCrore")
    spent_raw: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=MAX_MONETARY_RAW, alias="spentRaw", serialization_alias="spentRaw")
    status: Optional[str] = None
    status_urdu: Optional[str] = Field(default=None, alias="statusUrdu", serialization_alias="statusUrdu")
    risk: Optional[str] = None
    risk_urdu: Optional[str] = Field(default=None, alias="riskUrdu", serialization_alias="riskUrdu")
    floors: Optional[int] = Field(default=None, ge=1, le=150)
    area_sqft: Optional[str] = Field(default=None, alias="areaSqft", serialization_alias="areaSqft")
    engineer: Optional[str] = None
    governing_authority: Optional[str] = Field(default=None, alias="governingAuthority", serialization_alias="governingAuthority")
    start_date: Optional[date] = Field(default=None, alias="startDate", serialization_alias="startDate")
    expected_completion_date: Optional[date] = Field(default=None, alias="expectedCompletionDate", serialization_alias="expectedCompletionDate")
    handover_date: Optional[str] = Field(default=None, alias="handoverDate", serialization_alias="handoverDate")

    @field_validator("name", "location", "city", mode="before")
    @classmethod
    def validate_not_null_strings(cls, v: Any) -> Any:
        if v is None:
            raise ValueError("Field cannot be null.")
        return v

    @field_validator("budget_raw", "spent_raw")
    @classmethod
    def validate_raw_scale(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return validate_raw_amount(v)

    @field_validator("budget_crore", "spent_crore")
    @classmethod
    def validate_crore_scale(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return validate_crore_amount(v)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")
        return v

    @field_validator("risk")
    @classmethod
    def validate_risk(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_RISKS:
            raise ValueError(f"Invalid risk '{v}'. Allowed: {', '.join(sorted(ALLOWED_RISKS))}")
        return v


class ProjectRead(ProjectBase):
    """
    Project response schema matching the frontend `Project` interface (src/types/project.ts).
    Exposes `id` containing the public human-readable code (e.g. 'PRJ-001') and internal `uuid`.
    """
    id: str = Field(..., description="Frontend-facing public project code (e.g. PRJ-001)")
    uuid: UUID = Field(..., description="Internal collision-free UUID")
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    budget_crore: float = Field(default=0.0, alias="budgetCrore", serialization_alias="budgetCrore")
    budget_raw: float = Field(default=0.0, alias="budgetRaw", serialization_alias="budgetRaw")
    spent_crore: float = Field(default=0.0, alias="spentCrore", serialization_alias="spentCrore")
    status: str = Field(default="Planning")
    status_urdu: str = Field(default="منصوبہ بندی (Planning)", alias="statusUrdu", serialization_alias="statusUrdu")
    risk: str = Field(default="Low")
    risk_urdu: str = Field(default="کم (Low)", alias="riskUrdu", serialization_alias="riskUrdu")
    compliance_score: Optional[int] = Field(default=None, alias="complianceScore", serialization_alias="complianceScore")
    last_update: str = Field(default="Just now", alias="lastUpdate", serialization_alias="lastUpdate")
    last_update_urdu: str = Field(default="ابھی ابھی", alias="lastUpdateUrdu", serialization_alias="lastUpdateUrdu")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt", serialization_alias="updatedAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_project(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):  # SQLAlchemy ORM model instance
            bc = float(data.budget_crore) if data.budget_crore is not None else 0.0
            br = float(data.budget_raw) if data.budget_raw is not None else (bc * 10000000.0)
            sc = float(data.spent_crore) if data.spent_crore is not None else 0.0
            return {
                "id": data.code,
                "uuid": data.id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "name": data.name,
                "nameUrdu": data.name_urdu or data.name,
                "description": data.description,
                "location": data.location,
                "locationUrdu": data.location_urdu,
                "city": data.city,
                "cityUrdu": data.city_urdu or "لاہور",
                "type": data.type,
                "typeUrdu": data.type_urdu or data.type,
                "budgetCrore": bc,
                "budget_crore": bc,
                "budgetRaw": br,
                "budget_raw": br,
                "spentCrore": sc,
                "spent_crore": sc,
                "status": data.status,
                "statusUrdu": data.status_urdu or "منصوبہ بندی (Planning)",
                "risk": data.risk,
                "riskUrdu": data.risk_urdu or "کم (Low)",
                "complianceScore": data.compliance_score,
                "compliance_score": data.compliance_score,
                "lastUpdate": "Recently updated",
                "lastUpdateUrdu": "حال ہی میں اپ ڈیٹ ہوا",
                "floors": data.floors,
                "areaSqft": data.area_sqft,
                "area_sqft": data.area_sqft,
                "engineer": data.engineer or "",
                "governingAuthority": data.governing_authority,
                "startDate": data.start_date,
                "expectedCompletionDate": data.expected_completion_date,
                "handoverDate": data.handover_date or "",
                "createdAt": data.created_at,
                "created_at": data.created_at,
                "updatedAt": data.updated_at,
                "updated_at": data.updated_at,
            }
        return data


class ProjectListResponse(BaseModel):
    """Paginated response matching frontend PaginatedResponse<Project>."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    items: List[ProjectRead]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize", serialization_alias="pageSize")
    has_more: bool = Field(..., alias="hasMore", serialization_alias="hasMore")


# ---------------------------------------------------------------------------
# ProjectMember Schemas
# ---------------------------------------------------------------------------

class ProjectMemberBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )
    role: str = Field(default="viewer", description="Role: lead_engineer, architect, contractor, viewer")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in ALLOWED_MEMBER_ROLES:
            raise ValueError(f"Invalid member role '{v}'. Allowed: {', '.join(sorted(ALLOWED_MEMBER_ROLES))}")
        return v_clean


class ProjectMemberCreate(ProjectMemberBase):
    """
    Invitation / addition payload.
    Supports referencing collaborator via userId (UUID) or email.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    user_id: Optional[UUID] = Field(default=None, alias="userId", serialization_alias="userId")
    email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def validate_identifier_provided(self) -> "ProjectMemberCreate":
        if self.user_id is None and self.email is None:
            raise ValueError("Either userId or email must be provided to add a member.")
        return self


class ProjectMemberUpdate(BaseModel):
    """Payload to update collaborative role of an existing member."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    role: str = Field(..., description="Role: lead_engineer, architect, contractor, viewer")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in ALLOWED_MEMBER_ROLES:
            raise ValueError(f"Invalid member role '{v}'. Allowed: {', '.join(sorted(ALLOWED_MEMBER_ROLES))}")
        return v_clean


class ProjectMemberRead(ProjectMemberBase):
    id: UUID
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    user_id: UUID = Field(..., alias="userId", serialization_alias="userId")
    user_name: Optional[str] = Field(default=None, alias="userName", serialization_alias="userName")
    user_email: Optional[str] = Field(default=None, alias="userEmail", serialization_alias="userEmail")
    user_persona: Optional[str] = Field(default=None, alias="userPersona", serialization_alias="userPersona")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_member(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            user_obj = getattr(data, "user", None)
            return {
                "id": data.id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "role": data.role,
                "userName": user_obj.full_name if user_obj else None,
                "user_name": user_obj.full_name if user_obj else None,
                "userEmail": user_obj.email if user_obj else None,
                "user_email": user_obj.email if user_obj else None,
                "userPersona": user_obj.role if user_obj else None,
                "user_persona": user_obj.role if user_obj else None,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data


# ---------------------------------------------------------------------------
# ProjectActivity Schemas
# ---------------------------------------------------------------------------

class ProjectActivityBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    action: str = Field(..., min_length=2, max_length=255)
    action_urdu: Optional[str] = Field(default=None, alias="actionUrdu", serialization_alias="actionUrdu")
    activity_type: str = Field(default="upload", alias="type", serialization_alias="type")
    detail: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, alias="metadata", serialization_alias="metadata")


class ProjectActivityCreate(ProjectActivityBase):
    pass


class ProjectActivityRead(ProjectActivityBase):
    """
    Project Activity matching the frontend `ProjectActivity` interface (src/types/project.ts).
    """
    id: UUID
    project_id: UUID = Field(..., alias="projectId", serialization_alias="projectId")
    user_id: Optional[UUID] = Field(default=None, alias="userId", serialization_alias="userId")
    actor_name: Optional[str] = Field(default=None, alias="user", serialization_alias="user")
    time: str = Field(default="Just now", alias="time", serialization_alias="time")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    @model_validator(mode="before")
    @classmethod
    def map_orm_activity(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            return {
                "id": data.id,
                "projectId": data.project_id,
                "project_id": data.project_id,
                "userId": data.user_id,
                "user_id": data.user_id,
                "user": data.actor_name or "TameerAI System",
                "actor_name": data.actor_name or "TameerAI System",
                "action": data.action,
                "actionUrdu": data.action_urdu,
                "type": data.activity_type,
                "activity_type": data.activity_type,
                "time": "Recently",
                "detail": data.detail,
                "metadata": data.metadata_json,
                "metadata_json": data.metadata_json,
                "createdAt": data.created_at,
                "created_at": data.created_at,
            }
        return data
