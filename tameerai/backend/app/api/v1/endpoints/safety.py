"""
TameerAI - Structural Safety Engine API Endpoints (Phase 03.2.1)

Provides deterministic, multilingual safety evaluation services:
- POST /safety/evaluate: Evaluates structural queries for immediate hazard severity.
- POST /safety/verify-pec: Verifies Pakistan Engineering Council (PEC) registration formatting.
- POST /safety/sign-off: Enforces authenticated professional structural engineer sign-off authorization.
- GET /safety/indicators: Returns complete 38-indicator structural damage and DIY hazard taxonomy.
- GET /safety/audit-records: Returns recent safety assessment audit logs with project/user tenancy.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.guardrails.entities import ConstructionEntityExtractor
from app.ai.guardrails.intent import ConstructionIntent, ConstructionIntentDetector
from app.ai.guardrails.normalizer import TextNormalizer
from app.ai.guardrails.response_policy import detect_language
from app.ai.guardrails.structural_safety import (
    ProfessionalEngineerSignOff,
    SafetySeverityLevel,
    StructuralDamageIndicator,
    StructuralSafetyEngine,
    structural_safety_engine,
)
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.safety import (
    DamageIndicatorItem,
    PECSignOffRequest,
    PECSignOffResponse,
    PECVerificationRequest,
    PECVerificationResponse,
    SafetyAuditRecordRead,
    SafetyEvaluationRequest,
    SafetyEvaluationResponse,
)

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=SafetyEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Structural Safety & Life-Safety Hazards",
    description=(
        "Deterministically evaluates a construction query against structural damage indicators "
        "and assigns severity (Level 0 Emergency, Level 1 Urgent, Level 2 Priority, Level 3 Informational). "
        "Bypasses AI response generation for life-safety hazards and unsafe DIY structural procedures."
    ),
)
async def evaluate_safety(payload: SafetyEvaluationRequest) -> SafetyEvaluationResponse:
    raw_query = payload.query.strip()
    target_lang = payload.language or detect_language(raw_query)

    norm = TextNormalizer.normalize(raw_query)
    intent = ConstructionIntentDetector.detect_intent(norm).primary_intent
    entities = ConstructionEntityExtractor.extract_entities(norm)

    assessment = structural_safety_engine.evaluate_risk(
        query=raw_query,
        normalized_query=norm.normalized_query,
        intent=intent,
        entities=entities,
        language=target_lang,
        project_id=payload.project_id,
    )

    return SafetyEvaluationResponse(
        risk_level=assessment.risk_level,
        severity_level=assessment.severity_level,
        severity_code=assessment.severity_code,
        severity_name=assessment.severity_name,
        hazard_category=assessment.hazard_category,
        is_critical=assessment.is_critical,
        is_high_risk=assessment.is_high_risk,
        damage_indicators=assessment.damage_indicators,
        triggered_rule_identifiers=assessment.triggered_rule_identifiers,
        missing_engineering_variables=assessment.missing_engineering_variables,
        safety_advisory=assessment.safety_advisory,
        requires_immediate_evacuation=assessment.requires_immediate_evacuation,
        requires_professional_inspection=assessment.requires_professional_inspection,
        pec_review_required=assessment.pec_review_required,
        is_diy_hazard=assessment.is_diy_hazard,
        diy_hazard_type=assessment.diy_hazard_type,
        rationale=assessment.rationale,
        policy_version=structural_safety_engine.POLICY_VERSION,
    )


@router.post(
    "/verify-pec",
    response_model=PECVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Pakistan Engineering Council (PEC) Registration Format",
    description=(
        "Validates that a professional engineer's PEC number conforms to official registration syntax. "
        "Strictly separates format validity from active registration status. "
        "Discipline eligibility is evaluated (e.g. ELECT and MECH are not eligible for structural sign-off)."
    ),
)
async def verify_pec(payload: PECVerificationRequest) -> PECVerificationResponse:
    cred = structural_safety_engine.verify_pec_credential_status(payload.pec_number)
    return PECVerificationResponse(
        is_format_valid=cred["is_format_valid"],
        is_valid=cred["is_format_valid"],
        is_verified=cred["is_verified"],
        verification_status=cred["verification_status"],
        pec_number=payload.pec_number,
        normalized_number=cred["normalized_number"],
        detected_discipline=cred["detected_discipline"],
        structural_authorization_eligible=cred["structural_authorization_eligible"],
        error_message=cred["error_message"],
        verification_disclaimer=cred["verification_disclaimer"],
    )


def compute_canonical_fingerprint(data: dict) -> str:
    """
    Computes a deterministic SHA-256 integrity fingerprint over canonical JSON.
    Uses json.dumps with sort_keys=True, compact separators, and UTF-8 encoding.
    NOTE: In the absence of an asymmetric private signing key or append-only ledger,
    this digest serves as an in-memory integrity fingerprint, NOT an independently tamper-proof signature.
    """
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@router.post(
    "/sign-off",
    response_model=PECSignOffResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Professional Engineer Structural Sign-Off",
    description=(
        "Allows authenticated professional structural engineers to record attributable inspection observations. "
        "Under the Phase 03.2.3 Fail-Safe Policy, formal structural clearances via API remain disabled pending "
        "authoritative live PEC registry verification. Records attributable professional self-attestations only."
    ),
)
async def submit_sign_off(
    payload: PECSignOffRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PECSignOffResponse:
    sign_off_id = uuid.uuid4()

    user_role_str = str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role)

    # 1. Format and discipline check
    is_fmt_valid, disc, fmt_err = structural_safety_engine.validate_pec_registration_format(payload.pec_number)
    if not is_fmt_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=fmt_err or "Invalid PEC registration number format.",
        )

    is_eligible, elig_err = structural_safety_engine.check_structural_discipline_eligibility(disc)
    if not is_eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=elig_err or f"Discipline '{disc}' is not authorized for structural engineering sign-off.",
        )

    # 2. Administrative and client role restrictions
    if user_role_str.lower() in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges do not grant structural engineering sign-off authority. Formal structural clearance requires a verified structural engineer.",
        )
    if user_role_str.lower() == "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized user role 'client': clients cannot issue structural engineering sign-offs.",
        )

    # 3. Check inspection date if provided
    insp_date = None
    if payload.inspection_date:
        try:
            insp_date = datetime.fromisoformat(payload.inspection_date)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ISO format for inspection_date.",
            )

    # 4. Generate deterministic canonical integrity fingerprint (Task 1)
    timestamp_now = datetime.now(timezone.utc).isoformat()
    fingerprint_dict = {
        "attestation_statement": payload.attestation_statement or "",
        "created_at": timestamp_now,
        "discipline": disc or "CIVIL",
        "engineer_name": payload.engineer_name,
        "findings_summary": payload.findings_summary or "",
        "formal_clearance_issued": False,  # Strictly False under Task 4 Fail-Safe Policy
        "inspection_date": payload.inspection_date or "",
        "pec_number": payload.pec_number,
        "physical_site_inspection_conducted": payload.physical_site_inspection_conducted,
        "sign_off_id": str(sign_off_id),
        "user_id": str(current_user.id),
    }
    integrity_fingerprint = compute_canonical_fingerprint(fingerprint_dict)

    sign_off_model = ProfessionalEngineerSignOff(
        sign_off_id=sign_off_id,
        user_id=current_user.id,
        engineer_name=payload.engineer_name,
        pec_registration_number=payload.pec_number,
        discipline=disc or "CIVIL",
        is_format_valid=is_fmt_valid,
        is_verified=bool(current_user.is_verified),
        structural_discipline_eligible=is_eligible,
        physical_site_inspection_conducted=payload.physical_site_inspection_conducted,
        attestation_statement=payload.attestation_statement,
        inspection_date=insp_date,
        findings_summary=payload.findings_summary,
        formal_clearance_issued=payload.formal_clearance_issued,
        provenance_hash=integrity_fingerprint,
        manual_verification_status="PENDING_REGISTRY_LINK",
        independent_inspection_verified=False,
    )

    is_authorized, auth_err = structural_safety_engine.validate_sign_off_authorization(
        sign_off=sign_off_model,
        user_role=user_role_str,
        is_user_verified=bool(current_user.is_verified),
    )
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=auth_err,
        )

    # Under Task 4 Fail-Safe Policy: clearance remains False in the persisted record and response
    sign_off_model.formal_clearance_issued = False
    structural_safety_engine.record_sign_off(sign_off_model)

    has_attestation = bool(payload.attestation_statement and len(payload.attestation_statement.strip()) >= 20)

    return PECSignOffResponse(
        sign_off_id=sign_off_id,
        is_authorized=True,
        formal_clearance_issued=False,  # Unconditionally False under Fail-Safe Policy
        clearance_status="ADVISORY_ATTRIBUTABLE_RECORD_ONLY",
        engineer_name=payload.engineer_name,
        pec_registration_number=payload.pec_number,
        detected_discipline=disc,
        physical_site_inspection_conducted=payload.physical_site_inspection_conducted,
        attestation_submitted=has_attestation,
        submitted_by_authenticated_professional=True,
        independent_inspection_verified=False,
        attestation_verified=False,  # Strictly False: self-attestation is NOT independent verification
        provenance_hash=integrity_fingerprint,
        integrity_fingerprint=integrity_fingerprint,
    )


@router.get(
    "/indicators",
    response_model=List[DamageIndicatorItem],
    status_code=status.HTTP_200_OK,
    summary="List Structural Damage Indicators",
    description="Returns the comprehensive taxonomy of recognized structural damage indicators and hazard types.",
)
async def list_damage_indicators() -> List[DamageIndicatorItem]:
    items = []
    for indicator in StructuralDamageIndicator:
        val = indicator.value
        category = "general"
        if val.startswith("column_") or val.startswith("col_"):
            category = "column"
        elif val.startswith("beam_"):
            category = "beam"
        elif val.startswith("slab_"):
            category = "slab"
        elif val.startswith("building_") or val.startswith("bld_"):
            category = "building_wide"
        elif val.startswith("external_") or val.startswith("ext_"):
            category = "external_emergency"
        elif val.startswith("diy_"):
            category = "diy_repair_hazard"

        items.append(
            DamageIndicatorItem(
                code=val,
                category=category,
                description=val.replace("_", " ").title(),
            )
        )
    return items


@router.get(
    "/audit-records",
    response_model=List[SafetyAuditRecordRead],
    status_code=status.HTTP_200_OK,
    summary="Get Safety Assessment Audit Records",
    description=(
        "Retrieves recent audit log records. "
        "NOTE: Stored in an ephemeral in-memory circular ring buffer (max 500 items). "
        "Records reset on server restart. Scoped to authenticated user or specified project."
    ),
)
async def get_audit_records(
    limit: int = Query(default=50, ge=1, le=500),
    project_id: Optional[UUID] = Query(default=None, alias="projectId"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SafetyAuditRecordRead]:
    user_role_str = str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role)
    is_admin = user_role_str.lower() in ("admin", "superadmin")

    # If project_id is provided, enforce access control
    if project_id is not None and not is_admin:
        from app.services.chat_service import verify_project_chat_access
        await verify_project_chat_access(db=db, project_id=project_id, user_id=current_user.id)
        records = structural_safety_engine.get_recent_audit_records(limit=limit, project_id=project_id)
    elif not is_admin:
        # Non-admin users can only view their own user evaluations
        records = structural_safety_engine.get_recent_audit_records(limit=limit, user_id=current_user.id)
    else:
        records = structural_safety_engine.get_recent_audit_records(limit=limit, project_id=project_id)

    return [
        SafetyAuditRecordRead(
            assessment_id=r.assessment_id,
            timestamp=r.evaluation_timestamp.isoformat(),
            project_id=r.project_id,
            user_id=r.user_id,
            input_category=r.input_category,
            query_snippet=r.query_snippet,
            advisory_language=r.advisory_language,
            severity_classification=r.severity_classification.value,
            severity_code=r.severity_code,
            severity_name=r.severity_name,
            detected_indicators=r.detected_indicators,
            triggered_rule_identifiers=r.triggered_rule_identifiers,
            is_diy_hazard=r.is_diy_hazard,
            ai_usage_status=r.ai_usage_status,
            fallback_status=r.fallback_status,
            professional_escalation_status=r.professional_escalation_status,
            pec_review_required=r.pec_review_required,
            policy_version=r.policy_version,
        )
        for r in records
    ]
