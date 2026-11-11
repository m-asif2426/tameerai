"""
TameerAI - Phase 03.2 Comprehensive Structural Safety Test Suite

Validates all Phase 03.2 requirements:
- Group 1: Structural damage indicator detection across Column, Beam, Slab, Building-wide, External
- Group 2: Deterministic 4-level safety classification (Level 0 Emergency, Level 1 Urgent, Level 2 Priority, Level 3 Informational)
- Group 3: Unsafe DIY structural repair prohibitions (shoring, jacking, cutting, support removal)
- Group 4: Multilingual emergency and priority advisories in English, Roman Urdu, and Urdu script
- Group 5: Pakistan Engineering Council (PEC) registration number format validation
- Group 6: Safety assessment audit records and traceability
- Group 7: Fast-path API endpoints (/api/v1/safety/evaluate, /api/v1/safety/verify-pec, /api/v1/safety/indicators)
"""

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.ai.guardrails.structural_safety import (
    StructuralSafetyEngine,
    StructuralDamageIndicator,
    SafetySeverityLevel,
    RiskLevel,
    HazardCategory,
    structural_safety_engine,
)
from app.ai.guardrails.intent import ConstructionIntent
from app.ai.guardrails.normalizer import TextNormalizer


# ============================================================================
# GROUP 1: STRUCTURAL DAMAGE INDICATORS TAXONOMY
# ============================================================================

class TestGroup1DamageIndicators:
    """Verifies that structural damage indicators are deterministically detected."""

    def test_column_damage_indicators(self):
        # Column crushing
        q1 = "The concrete in the basement column has crushed and flaked away under load."
        res1 = structural_safety_engine.evaluate_risk(q1, q1.lower(), ConstructionIntent.PROCEDURE, [])
        assert res1.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.COLUMN_CONCRETE_CRUSHING.value in res1.damage_indicators

        # Column buckled rebar
        q2 = "Main ground floor pillar has buckled rebar bent outward under compression."
        res2 = structural_safety_engine.evaluate_risk(q2, q2.lower(), ConstructionIntent.PROCEDURE, [])
        assert res2.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.COLUMN_BUCKLED_REBAR.value in res2.damage_indicators

        # Column displacement
        q3 = "The corner column has shifted and moved out of plumb."
        res3 = structural_safety_engine.evaluate_risk(q3, q3.lower(), ConstructionIntent.PROCEDURE, [])
        assert res3.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.COLUMN_DISPLACEMENT.value in res3.damage_indicators

        # Column exposed rebar (Urgent, Level 1)
        q4 = "There is exposed rebar and concrete cover spalling on the perimeter column."
        res4 = structural_safety_engine.evaluate_risk(q4, q4.lower(), ConstructionIntent.PROCEDURE, [])
        assert res4.severity_level == SafetySeverityLevel.LEVEL_1_URGENT
        assert StructuralDamageIndicator.COLUMN_EXPOSED_REBAR.value in res4.damage_indicators

    def test_beam_damage_indicators(self):
        # Beam severe sagging
        q1 = "The main transfer beam is severely sagging and about to fracture."
        res1 = structural_safety_engine.evaluate_risk(q1, q1.lower(), ConstructionIntent.PROCEDURE, [])
        assert res1.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.BEAM_SEVERE_SAGGING.value in res1.damage_indicators

        # Beam diagonal shear crack (Urgent, Level 1)
        q2 = "Large 45 degree diagonal shear crack appeared near the beam support."
        res2 = structural_safety_engine.evaluate_risk(q2, q2.lower(), ConstructionIntent.PROCEDURE, [])
        assert res2.severity_level == SafetySeverityLevel.LEVEL_1_URGENT
        assert StructuralDamageIndicator.BEAM_SEVERE_DIAGONAL_CRACKING.value in res2.damage_indicators

        # Beam-column joint distress (Urgent, Level 1)
        q3 = "Cracks and spalling at the beam-column joint connection on the first floor."
        res3 = structural_safety_engine.evaluate_risk(q3, q3.lower(), ConstructionIntent.PROCEDURE, [])
        assert res3.severity_level == SafetySeverityLevel.LEVEL_1_URGENT
        assert StructuralDamageIndicator.BEAM_COLUMN_JOINT_DAMAGE.value in res3.damage_indicators

    def test_slab_damage_indicators(self):
        # Slab falling concrete / spalling (Level 0 Emergency)
        q1 = "Roof slab is sagging and large chunks of concrete are falling from the ceiling."
        res1 = structural_safety_engine.evaluate_risk(q1, q1.lower(), ConstructionIntent.PROCEDURE, [])
        assert res1.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.SLAB_FALLING_CONCRETE.value in res1.damage_indicators

        # Slab excessive deflection (Urgent, Level 1)
        q2 = "The dining hall slab shows excessive deflection and is noticeably sagging."
        res2 = structural_safety_engine.evaluate_risk(q2, q2.lower(), ConstructionIntent.PROCEDURE, [])
        assert res2.severity_level == SafetySeverityLevel.LEVEL_1_URGENT
        assert StructuralDamageIndicator.SLAB_SIGNIFICANT_DEFLECTION.value in res2.damage_indicators

    def test_building_wide_and_external_indicators(self):
        # Leaning building
        q1 = "The four-story building is visibly leaning to one side."
        res1 = structural_safety_engine.evaluate_risk(q1, q1.lower(), ConstructionIntent.PROCEDURE, [])
        assert res1.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.BUILDING_LEANING_TILTING.value in res1.damage_indicators

        # Sinking foundation
        q2 = "The foundation is rapidly sinking and wall is cracking wide."
        res2 = structural_safety_engine.evaluate_risk(q2, q2.lower(), ConstructionIntent.PROCEDURE, [])
        assert res2.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.BUILDING_SUDDEN_MOVEMENT.value in res2.damage_indicators

        # Earthquake severe damage
        q3 = "After the earthquake, several structural columns cracked severely and broke."
        res3 = structural_safety_engine.evaluate_risk(q3, q3.lower(), ConstructionIntent.PROCEDURE, [])
        assert res3.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.EXTERNAL_EARTHQUAKE_DAMAGE.value in res3.damage_indicators

        # Vehicle impact
        q4 = "A loaded dumper crashed into the ground floor corner column."
        res4 = structural_safety_engine.evaluate_risk(q4, q4.lower(), ConstructionIntent.PROCEDURE, [])
        assert res4.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert StructuralDamageIndicator.EXTERNAL_IMPACT_DAMAGE.value in res4.damage_indicators


# ============================================================================
# GROUP 2: DETERMINISTIC 4-LEVEL SEVERITY HIERARCHY
# ============================================================================

class TestGroup2SeverityHierarchy:
    """Verifies that all 4 severity levels are correctly and deterministically assigned."""

    def test_level_0_emergency_immediate_evacuation(self):
        q = "Building has loud popping sounds, sudden movement and is about to collapse!"
        res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])
        assert res.severity_level == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert res.severity_code == 0
        assert res.risk_level == RiskLevel.CRITICAL
        assert res.requires_immediate_evacuation is True
        assert res.is_critical is True
        assert "Rescue 1122" in res.safety_advisory

    def test_level_1_urgent_in_person_inspection(self):
        q = "We discovered exposed corroded rebar on two exterior structural columns."
        res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])
        assert res.severity_level == SafetySeverityLevel.LEVEL_1_URGENT
        assert res.severity_code == 1
        assert res.requires_immediate_evacuation is False
        assert res.requires_professional_inspection is True
        assert res.pec_review_required is True
        assert "LEVEL 1 — URGENT STRUCTURAL SAFETY ADVISORY" in res.safety_advisory

    def test_level_2_priority_modification_and_sizing(self):
        q = "Can we remove this ground floor column to create a larger drawing room?"
        res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])
        assert res.severity_level == SafetySeverityLevel.LEVEL_2_PRIORITY
        assert res.severity_code == 2
        assert res.risk_level == RiskLevel.HIGH
        assert res.requires_immediate_evacuation is False
        assert res.pec_review_required is True
        assert "STRUCTURAL ENGINEERING ADVISORY (HIGH RISK)" in res.safety_advisory

    def test_level_3_informational_educational_only(self):
        q = "What is the standard water-cement ratio for M20 grade concrete?"
        res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.EXPLANATION, [])
        assert res.severity_level == SafetySeverityLevel.LEVEL_3_INFORMATIONAL
        assert res.severity_code == 3
        assert res.risk_level == RiskLevel.LOW
        assert res.safety_advisory is None
        assert res.requires_immediate_evacuation is False
        assert "does NOT certify structural safety" in res.rationale


# ============================================================================
# GROUP 3: UNSAFE DIY STRUCTURAL REPAIR PROHIBITIONS
# ============================================================================

class TestGroup3DIYRepairProhibitions:
    """Verifies that unauthorized DIY structural repair requests are blocked."""

    def test_diy_hydraulic_jacking_blocked(self):
        queries = [
            "How can I jack up a sagging beam myself using bottle jacks?",
            "Can I use hydraulic jack to lift sinking column at home?",
            "Sagging lanter ko hydraulic jack se kaise seedha karein?",
        ]
        for q in queries:
            res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])
            assert res.severity_level == SafetySeverityLevel.LEVEL_2_PRIORITY
            assert res.is_diy_hazard is True
            assert "UNSAFE DIY STRUCTURAL REPAIR PROHIBITION" in res.safety_advisory

    def test_diy_load_bearing_wall_removal_blocked(self):
        queries = [
            "DIY guide to demolish load bearing wall without engineer",
            "Can I cut through RCC column with angle grinder myself?",
            "Lode bearing deewar ko khud kaise torein?",
        ]
        for q in queries:
            res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])
            assert res.severity_level == SafetySeverityLevel.LEVEL_2_PRIORITY
            assert res.is_diy_hazard is True

    def test_diy_propping_failing_column_blocked(self):
        q = "Cracked column ko lakri ki balli se temporary support kaise lagayein?"
        res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])
        assert res.severity_level == SafetySeverityLevel.LEVEL_2_PRIORITY
        assert res.is_diy_hazard is True


# ============================================================================
# GROUP 4: MULTILINGUAL DETERMINISTIC ADVISORIES
# ============================================================================

class TestGroup4MultilingualAdvisories:
    """Verifies localized directives in English, Roman Urdu, and native Urdu script."""

    def test_english_advisories(self):
        adv_emg = structural_safety_engine.get_emergency_evacuation_advisory("en")
        assert "LEVEL 0 — EMERGENCY" in adv_emg
        assert "Evacuate the Affected Area Immediately" in adv_emg
        assert "Rescue 1122" in adv_emg
        assert "Pakistan Engineering Council (PEC)" in adv_emg

        adv_urg = structural_safety_engine.get_urgent_inspection_advisory("en")
        assert "LEVEL 1 — URGENT" in adv_urg
        assert "Isolate Affected Area" in adv_urg

        adv_pri = structural_safety_engine.get_priority_inspection_advisory("en")
        assert "LEVEL 2: PRIORITY INSPECTION" in adv_pri
        assert "No Speculative Structural Sizing" in adv_pri

    def test_roman_urdu_advisories(self):
        adv_emg = structural_safety_engine.get_emergency_evacuation_advisory("roman_ur")
        assert "FORI INKHILA" in adv_emg
        assert "Rescue 1122" in adv_emg
        assert "Insani jaan ka tahaffuz" in adv_emg

        adv_urg = structural_safety_engine.get_urgent_inspection_advisory("roman_ur")
        assert "LEVEL 1 — URGENT" in adv_urg
        assert "Mutasira Hissay Se Door Rahain" in adv_urg

        adv_pri = structural_safety_engine.get_priority_inspection_advisory("roman_ur")
        assert "Baghair Calculation Design Mumkin Nahi" in adv_pri

    def test_urdu_script_advisories(self):
        adv_emg = structural_safety_engine.get_emergency_evacuation_advisory("ur")
        assert "شدید ساختی خطرے کا انتباہ" in adv_emg
        assert "متاثرہ حصے کو فوری خالی کریں" in adv_emg
        assert "ریسکیو 1122" in adv_emg

        adv_urg = structural_safety_engine.get_urgent_inspection_advisory("ur")
        assert "سطح 1 — فوری ساختی ایڈوائزری" in adv_urg

        adv_pri = structural_safety_engine.get_priority_inspection_advisory("ur")
        assert "سٹرکچرل انجینئرنگ ایڈوائزری" in adv_pri
        assert "بغیر حساب کتاب ڈیزائن ممکن نہیں" in adv_pri


# ============================================================================
# GROUP 5: PAKISTAN ENGINEERING COUNCIL (PEC) REGISTRATION VERIFICATION
# ============================================================================

class TestGroup5PECValidation:
    """Verifies PEC registration number syntax validation."""

    def test_valid_pec_formats(self):
        valid_numbers = [
            "CIVIL/12345",
            "STRUCT/67890",
            "ELECT/11223",
            "MECH/44556",
            "C/99999",
            "S/12345",
            "123456",
            "civil/45678",
            "STRUCT-88888",
        ]
        for num in valid_numbers:
            is_valid, err = structural_safety_engine.validate_pec_registration_number(num)
            assert is_valid is True, f"Failed for {num}: {err}"
            assert err is None

    def test_invalid_pec_formats(self):
        invalid_numbers = [
            "",
            "   ",
            "DOCTOR/12345",
            "ABC",
            "CIVIL/abc",
            "12",  # too short
            None,
        ]
        for num in invalid_numbers:
            is_valid, err = structural_safety_engine.validate_pec_registration_number(num)
            assert is_valid is False, f"Expected invalid for {num}"
            assert err is not None


# ============================================================================
# GROUP 6: AUDIT RECORDS & TRACEABILITY
# ============================================================================

class TestGroup6AuditRecords:
    """Verifies that evaluations create immutable audit records."""

    def test_audit_records_logged(self):
        structural_safety_engine.clear_audit_log()
        assert len(structural_safety_engine.get_recent_audit_records()) == 0

        # Run emergency query
        q = "The beam has sheared and is collapsing right now."
        res = structural_safety_engine.evaluate_risk(q, q.lower(), ConstructionIntent.PROCEDURE, [])

        logs = structural_safety_engine.get_recent_audit_records()
        assert len(logs) == 1
        rec = logs[0]
        assert rec.severity_classification == SafetySeverityLevel.LEVEL_0_EMERGENCY
        assert rec.severity_code == 0
        assert rec.ai_usage_status == "bypassed_deterministic_override"
        assert rec.pec_review_required is True
        assert rec.policy_version in ("3.2.0", "3.2.1", "3.2.2", "3.2.3")


# ============================================================================
# GROUP 7: FAST-PATH SAFETY API ENDPOINTS
# ============================================================================

class TestGroup7SafetyAPIEndpoints:
    """Verifies fast-path safety endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_api_evaluate_emergency(self, client):
        payload = {"query": "Building foundation is sinking and column has crushed."}
        resp = client.post("/api/v1/safety/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["severity_code"] == 0
        assert data["severity_name"] == "LEVEL 0 — EMERGENCY"
        assert data["requires_immediate_evacuation"] is True
        assert "Rescue 1122" in data["safety_advisory"]

    def test_api_evaluate_diy_hazard(self, client):
        payload = {"query": "How can I jack up my cracked beam myself?"}
        resp = client.post("/api/v1/safety/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["severity_code"] == 2
        assert data["is_diy_hazard"] is True
        assert "UNSAFE DIY STRUCTURAL REPAIR PROHIBITION" in data["safety_advisory"]

    def test_api_verify_pec_success(self, client):
        payload = {"pec_number": "CIVIL/12345"}
        resp = client.post("/api/v1/safety/verify-pec", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["normalized_number"] == "CIVIL/12345"

    def test_api_verify_pec_invalid(self, client):
        payload = {"pec_number": "NOT_AN_ENGINEER"}
        resp = client.post("/api/v1/safety/verify-pec", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["error_message"] is not None

    def test_api_damage_indicators(self, client):
        resp = client.get("/api/v1/safety/indicators")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 20
        codes = [d["code"] for d in data]
        assert "column_concrete_crushing" in codes
        assert "column_buckled_rebar" in codes
        assert "beam_severe_sagging" in codes
        assert "slab_falling_concrete" in codes
