"""
TameerAI - Structural Safety Schemas (Phase 03.2.1)

Defines data contracts for:
- Structural safety evaluation requests and responses
- Severity classifications (Level 0 Emergency, Level 1 Urgent, Level 2 Priority, Level 3 Informational)
- Pakistan Engineering Council (PEC) registration validation & credential verification separation
- Professional engineering sign-off requests & authorization
- Auditable safety records and damage indicator catalog
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.guardrails.structural_safety import (
    HazardCategory,
    RiskLevel,
    SafetySeverityLevel,
    StructuralDamageIndicator,
)


class SafetyEvaluationRequest(BaseModel):
    """Input payload for deterministic structural safety evaluation."""
    query: str = Field(..., min_length=2, description="Construction or structural query text")
    language: Optional[str] = Field(default="en", description="Target language ('en', 'ur', 'roman_ur')")
    project_id: Optional[UUID] = Field(default=None, description="Optional associated project workspace ID")


class SafetyEvaluationResponse(BaseModel):
    """Authoritative structural safety evaluation result."""
    risk_level: RiskLevel
    severity_level: SafetySeverityLevel
    severity_code: int = Field(..., description="0=Emergency, 1=Urgent, 2=Priority, 3=Informational")
    severity_name: str
    hazard_category: HazardCategory
    is_critical: bool
    is_high_risk: bool
    damage_indicators: List[str]
    triggered_rule_identifiers: List[str]
    missing_engineering_variables: List[str]
    safety_advisory: Optional[str] = None
    requires_immediate_evacuation: bool
    requires_professional_inspection: bool
    pec_review_required: bool
    is_diy_hazard: bool
    diy_hazard_type: Optional[str] = None
    rationale: str
    policy_version: str


class PECVerificationRequest(BaseModel):
    """Request to validate Pakistan Engineering Council (PEC) registration number."""
    pec_number: str = Field(..., min_length=3, max_length=30, description="PEC number e.g. CIVIL/12345 or STRUCT/67890")
    engineer_name: Optional[str] = Field(default=None, description="Engineer full name")


class PECVerificationResponse(BaseModel):
    """
    Validation response for Pakistan Engineering Council (PEC) credentials.
    Enforces strict separation between syntax validity and active registration verification.
    """
    is_format_valid: bool
    is_valid: bool = Field(default=False, description="Alias for is_format_valid (backward compatibility)")
    is_verified: bool = Field(default=False, description="False: Format validity does NOT imply verified registration")
    verification_status: str = Field(default="UNVERIFIED", description="UNVERIFIED, FORMAT_INVALID, or DISCIPLINE_INELIGIBLE")
    pec_number: str
    normalized_number: Optional[str] = None
    detected_discipline: Optional[str] = None
    structural_authorization_eligible: bool = False
    error_message: Optional[str] = None
    regulatory_body: str = "Pakistan Engineering Council (PEC)"
    verification_disclaimer: str = (
        "Format validation only. Format validity does NOT constitute proof of active "
        "PEC registration or professional licensing. Non-civil disciplines (e.g. ELECT, MECH) "
        "and unverified numeric IDs are not authorized for structural clearance."
    )


class PECSignOffRequest(BaseModel):
    """Request to submit a formal engineering inspection sign-off."""
    pec_number: str = Field(..., min_length=3, max_length=30, description="Engineer PEC registration number")
    engineer_name: str = Field(..., min_length=2, max_length=100, description="Engineer full legal name")
    project_id: Optional[UUID] = Field(default=None, description="Associated project workspace ID")
    physical_site_inspection_conducted: bool = Field(
        default=False,
        description="Mandatory True for structural clearance. Formal clearance cannot be issued remotely."
    )
    inspection_date: Optional[str] = Field(default=None, description="ISO format date of physical on-site inspection")
    findings_summary: Optional[str] = Field(default=None, description="Technical observations from physical inspection")
    formal_clearance_issued: bool = Field(
        default=False,
        description="Whether unconditional structural stability clearance is being certified."
    )
    attestation_statement: Optional[str] = Field(
        default=None,
        description=(
            "Mandatory professional attestation affirming that the engineer personally conducted "
            "an on-site physical inspection. A bare boolean cannot establish inspection occurrence."
        )
    )


class PECSignOffResponse(BaseModel):
    """Response contract for professional engineer sign-off authorization (Phase 03.2.3)."""
    sign_off_id: UUID
    is_authorized: bool
    formal_clearance_issued: bool = False
    clearance_status: str = "ADVISORY_ATTRIBUTABLE_RECORD_ONLY"
    engineer_name: str
    pec_registration_number: str
    detected_discipline: Optional[str] = None
    physical_site_inspection_conducted: bool
    attestation_submitted: bool = False
    submitted_by_authenticated_professional: bool = False
    independent_inspection_verified: bool = False
    attestation_verified: bool = False  # Strictly False: self-attestation is NOT independent verification
    provenance_hash: Optional[str] = None  # Integrity fingerprint
    integrity_fingerprint: Optional[str] = None
    error_message: Optional[str] = None
    regulatory_notice: str = (
        "Statutory Notice: TameerAI does NOT issue structural approvals or formal stability clearances. "
        "The platform records attributable professional inspection observations and self-attestations only. "
        "Formal structural clearance requires an official stamped and sealed PEC engineering report."
    )


class DamageIndicatorItem(BaseModel):
    """Catalog item for a structural damage indicator."""
    code: str
    category: str
    description: str


class SafetyAuditRecordRead(BaseModel):
    """Read representation of an auditable structural safety evaluation record."""
    assessment_id: UUID
    timestamp: str
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    input_category: str
    query_snippet: str
    advisory_language: str
    severity_classification: str
    severity_code: int
    severity_name: str
    detected_indicators: List[str]
    triggered_rule_identifiers: List[str]
    is_diy_hazard: bool
    ai_usage_status: str
    fallback_status: str
    professional_escalation_status: str
    pec_review_required: bool
    policy_version: str
