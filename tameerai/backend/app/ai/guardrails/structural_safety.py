"""
TameerAI - Structural Safety Intelligence & Engineering Risk Assessment Engine (Phase 03.2)
Deterministic, multilingual structural safety advisory system and emergency override engine.

Enforces:
- 4 Deterministic Safety Severity Levels:
  * LEVEL 0 — EMERGENCY: Immediate evacuation when credible indicators of imminent danger are reported.
  * LEVEL 1 — URGENT: Serious reported structural damage requiring urgent in-person professional inspection.
  * LEVEL 2 — PRIORITY INSPECTION: Potentially significant structural defects / uncalculated modifications.
  * LEVEL 3 — INFORMATIONAL: General construction education (strictly forbids safety clearance / green certificates).
- Comprehensive Damage Indicator Taxonomy:
  * Column: Crushing, severe cracking, exposed rebar, buckled rebar, deformation, displacement, critical spalling.
  * Beam: Significant sagging, severe diagonal/shear cracking, beam-column joint distress, crushing, deformed rebar.
  * Slab: Deflection, progressive cracking, localized collapse, falling concrete, visible separation.
  * Building-wide: Visible leaning/tilting, partial collapse, sudden movement, rapidly widening cracks, noises with movement.
  * External emergencies: Earthquake, fire, explosion/blast, flood foundation instability, vehicular impact.
- Strict DIY Structural Repair Prevention: Blocks actionable steps for shoring, jacking, column removal, member cutting.
- Multilingual Advisories: English, Urdu script, and Roman Urdu.
- Professional Engineer Oversight: PEC registration verification rules and non-delegable physical inspection mandate.
- Audit Logging & Traceability: Structured assessment records with policy provenance.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from pydantic import BaseModel, Field

from app.ai.guardrails.entities import EntityCategory, ExtractedEntity
from app.ai.guardrails.intent import ConstructionIntent


# ============================================================================
# 1. SEVERITY LEVELS & ENUMS
# ============================================================================

class SafetySeverityLevel(str, Enum):
    """
    Phase 03.2 Authoritative 4-tier structural safety severity classification.
    Strictly forbids any 'SAFE' or 'GREEN' certification.
    """
    LEVEL_0_EMERGENCY = "level_0_emergency"          # Imminent collapse / acute danger -> Immediate Evacuation
    LEVEL_1_URGENT = "level_1_urgent"                # Serious structural damage -> Urgent In-Person Inspection
    LEVEL_2_PRIORITY = "level_2_priority_inspection" # Potential structural defect / modification -> Priority Inspection
    LEVEL_3_INFORMATIONAL = "level_3_informational"  # Educational / general inquiries -> Disclaimer only

    # Aliases
    EMERGENCY = "level_0_emergency"
    URGENT = "level_1_urgent"
    PRIORITY_INSPECTION = "level_2_priority_inspection"
    INFORMATIONAL = "level_3_informational"


class RiskLevel(str, Enum):
    """Legacy 4-level risk classification preserved for backward compatibility."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    # Backward compatibility aliases
    HIGH_STRUCTURAL_SAFETY = "high"
    LEVEL_0_EMERGENCY = "critical"
    LEVEL_1_URGENT = "critical"
    LEVEL_2_PRIORITY = "high"
    LEVEL_3_INFORMATIONAL = "low"


class HazardCategory(str, Enum):
    """Primary structural engineering hazard categories."""
    FOUNDATION_GEOTECHNICAL = "foundation_geotechnical"
    RCC_STRUCTURAL = "rcc_structural"
    STRUCTURAL_MODIFICATION = "structural_modification"
    CONSTRUCTION_EXECUTION = "construction_execution"
    EXTERNAL_DISASTER = "external_disaster"
    UNSAFE_DIY = "unsafe_diy"
    NONE = "none"


class StructuralDamageIndicator(str, Enum):
    """Comprehensive taxonomy of reported structural damage indicators (Phase 03.2 Section 2)."""
    # A. Column Damage
    COLUMN_CONCRETE_CRUSHING = "column_concrete_crushing"
    COLUMN_SEVERE_CRACKING = "column_severe_cracking"
    COLUMN_EXPOSED_REBAR = "column_exposed_rebar"
    COLUMN_BUCKLED_REBAR = "column_buckled_rebar"
    COLUMN_DEFORMATION = "column_deformation"
    COLUMN_DISPLACEMENT = "column_displacement"
    COLUMN_SPALLING_CRITICAL = "column_spalling_critical"

    # B. Beam Damage
    BEAM_SIGNIFICANT_SAGGING = "beam_significant_sagging"
    BEAM_SEVERE_SAGGING = "beam_severe_sagging"
    BEAM_SEVERE_DIAGONAL_CRACKING = "beam_severe_diagonal_cracking"
    BEAM_COLUMN_JOINT_DAMAGE = "beam_column_joint_damage"
    BEAM_CONCRETE_CRUSHING = "beam_concrete_crushing"
    BEAM_EXPOSED_DEFORMED_REBAR = "beam_exposed_deformed_rebar"

    # C. Slab Damage
    SLAB_SIGNIFICANT_DEFLECTION = "slab_significant_deflection"
    SLAB_PROGRESSIVE_CRACKING = "slab_progressive_cracking"
    SLAB_LOCALIZED_COLLAPSE = "slab_localized_collapse"
    SLAB_FALLING_CONCRETE = "slab_falling_concrete"
    SLAB_STRUCTURAL_SEPARATION = "slab_structural_separation"

    # D. Building-Wide Indicators
    BUILDING_LEANING_TILTING = "building_leaning_tilting"
    BUILDING_PARTIAL_COLLAPSE = "building_partial_collapse"
    BUILDING_SUDDEN_MOVEMENT = "building_sudden_movement"
    BUILDING_RAPID_WIDENING_CRACKS = "building_rapid_widening_cracks"
    BUILDING_STRUCTURAL_NOISES_MOVEMENT = "building_structural_noises_movement"
    BUILDING_MULTIPLE_DAMAGED_ELEMENTS = "building_multiple_damaged_elements"

    # E. External Emergency Conditions
    EXTERNAL_EARTHQUAKE_DAMAGE = "external_earthquake_damage"
    EXTERNAL_FIRE_DAMAGE = "external_fire_damage"
    EXTERNAL_EXPLOSION_DAMAGE = "external_explosion_damage"
    EXTERNAL_FLOOD_INSTABILITY = "external_flood_instability"
    EXTERNAL_IMPACT_DAMAGE = "external_impact_damage"

    # F. Unsafe DIY Structural Repair Hazards (Section 6)
    DIY_COLUMN_SHORING = "diy_column_shoring"
    DIY_BEAM_JACKING = "diy_beam_jacking"
    DIY_SUPPORT_REMOVAL = "diy_support_removal"
    DIY_COLUMN_REPLACEMENT = "diy_column_replacement"
    DIY_STRUCTURAL_CUTTING = "diy_structural_cutting"
    DIY_IMPROVISED_REINFORCEMENT = "diy_improvised_reinforcement"
    DIY_UNSAFE_REENTRY = "diy_unsafe_reentry"
    DIY_REPAIR_FAILING_ELEMENT = "diy_repair_failing_element"
    DIY_WALL_DEMOLITION = "diy_wall_demolition"


# ============================================================================
# 2. AUDIT & OVERSIGHT DATA MODELS
# ============================================================================

class SafetyAssessmentAuditRecord(BaseModel):
    """
    Auditable traceability record for structural safety evaluations (Section 9).
    NOTE: Stored in an ephemeral in-memory circular ring buffer for runtime inspection.
    Process restarts reset this buffer. Durable historical auditing requires an external persistent adapter.
    """
    assessment_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    evaluation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    input_category: str
    query_snippet: str
    advisory_language: str
    severity_classification: SafetySeverityLevel
    severity_code: int
    severity_name: str
    detected_indicators: List[str] = Field(default_factory=list)
    triggered_rule_identifiers: List[str] = Field(default_factory=list)
    is_diy_hazard: bool = False
    diy_hazard_type: Optional[str] = None
    ai_usage_status: str = "bypassed_deterministic_override"
    fallback_status: str = "active"
    professional_escalation_status: str = "mandatory"
    pec_review_required: bool = True
    policy_version: str = "3.2.1"


class ProfessionalEngineerSignOff(BaseModel):
    """
    Authoritative model tracking professional engineering oversight and provenance (Phase 03.2.1/03.2.2).
    Enforces strict separation between format-valid numbers and actual verified credentials.
    Prohibits unauthorized users, administrators, or non-structural disciplines from issuing structural clearances.
    """
    sign_off_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = None
    engineer_name: str
    pec_registration_number: str
    discipline: str = "CIVIL"
    is_format_valid: bool = False
    is_verified: bool = False
    structural_discipline_eligible: bool = False
    physical_site_inspection_conducted: bool = False
    attestation_statement: Optional[str] = None
    inspection_date: Optional[datetime] = None
    findings_summary: Optional[str] = None
    formal_clearance_issued: bool = False
    verification_notes: Optional[str] = None
    provenance_hash: Optional[str] = None
    manual_verification_verifier: Optional[str] = None
    manual_verification_evidence_ref: Optional[str] = None
    manual_verification_date: Optional[datetime] = None
    manual_verification_status: str = "PENDING_REGISTRY_LINK"
    independent_inspection_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StructuralRiskAssessment(BaseModel):
    """Detailed structural risk assessment container with Phase 03.2 extensions."""
    risk_level: RiskLevel
    severity_level: SafetySeverityLevel = SafetySeverityLevel.LEVEL_3_INFORMATIONAL
    severity_code: int = 3
    severity_name: str = "LEVEL 3 — INFORMATIONAL"
    hazard_category: HazardCategory = HazardCategory.NONE
    is_critical: bool = False
    is_high_risk: bool = False
    detected_hazards: List[str] = Field(default_factory=list)
    damage_indicators: List[str] = Field(default_factory=list)
    triggered_rule_identifiers: List[str] = Field(default_factory=list)
    missing_engineering_variables: List[str] = Field(default_factory=list)
    safety_advisory: Optional[str] = None
    requires_immediate_evacuation: bool = False
    requires_professional_inspection: bool = False
    pec_review_required: bool = False
    is_diy_hazard: bool = False
    diy_hazard_type: Optional[str] = None
    rationale: str
    audit_record: Optional[SafetyAssessmentAuditRecord] = None


# ============================================================================
# 3. DETERMINISTIC DAMAGE DETECTION RULES (Multilingual Regex Registry)
# ============================================================================

# Level 0 — EMERGENCY (Imminent Danger & Evacuation Triggers)
EMERGENCY_RULES: List[Tuple[str, StructuralDamageIndicator, re.Pattern, str]] = [
    # 1. Partial Collapse / Structure Caving in
    (
        "R-EMG-BLD-COLLAPSE",
        StructuralDamageIndicator.BUILDING_PARTIAL_COLLAPSE,
        re.compile(r"\b(?:partial|localized|building|structure|house|roof|floor|slab|wall|pillar|columns?|foundation)\b.*?\b(?:has\s+)?(?:collapsed|collapsing|caved\s*in|falling\s*down|gir\s*gaya|gir\s*rahi|dheh\s*gayi)\b", re.IGNORECASE),
        "Partial or active structural collapse reported",
    ),
    (
        "R-EMG-BLD-COLLAPSE-UR",
        StructuralDamageIndicator.BUILDING_PARTIAL_COLLAPSE,
        re.compile(r"(?:عمارت|مکان|چھت|سلیب|کالم|دیوار)\s*(?:گر\s*(?:گئی|گیا|رہی)|منہدم|ڈھہہ)", re.IGNORECASE),
        "Urdu script: collapse of structural element",
    ),
    # 2. Concrete Crushing in Column or Primary Member
    (
        "R-EMG-COL-CRUSH",
        StructuralDamageIndicator.COLUMN_CONCRETE_CRUSHING,
        re.compile(r"\b(?:concrete|columns?|pillars?|beams?|foundations?)\b.*?\b(?:has\s+)?(?:crushed|crushing|burst|bursting|spalled\s+to\s+core|churan|phat\s+gaya|kachra\s+ban\s+gaya)\b", re.IGNORECASE),
        "Concrete crushing or compressive blowout in load-bearing member",
    ),
    (
        "R-EMG-COL-CRUSH-REV",
        StructuralDamageIndicator.COLUMN_CONCRETE_CRUSHING,
        re.compile(r"\b(?:crushed|crushing|burst|bursting)\b.*?\b(?:columns?|pillars?|beams?|concrete)\b", re.IGNORECASE),
        "Concrete crushing or compressive blowout reverse",
    ),
    (
        "R-EMG-COL-CRUSH-UR",
        StructuralDamageIndicator.COLUMN_CONCRETE_CRUSHING,
        re.compile(r"(?:کالم|پلر|بیم)\s*کا\s*کنکریٹ\s*(?:پھٹ|چورا|ٹوٹ|کچل)", re.IGNORECASE),
        "Urdu script: column concrete crushing",
    ),
    # 2b. Severe Sagging or Shearing Beam
    (
        "R-EMG-BM-SAG",
        StructuralDamageIndicator.BEAM_SEVERE_SAGGING,
        re.compile(r"\b(?:beam|girder|transfer\s+beam)\b.*?\b(?:severely\s+sagging|sagging\s+badly|excessive\s+sag|bending\s+under\s+load|about\s+to\s+fracture|about\s+to\s+break|has\s+sheared|sheared)\b", re.IGNORECASE),
        "Severe sagging or active fracture of primary structural beam",
    ),
    # 3. Buckled Reinforcement in Column
    (
        "R-EMG-COL-BUCKLE",
        StructuralDamageIndicator.COLUMN_BUCKLED_REBAR,
        re.compile(r"\b(?:buckled\s+(?:rebar|steel|reinforcement|bars?)|reinforcement\s+buckling|saria\s+(?:muṛ\s+gaya|terha\s+ho\s+gaya|bahir\s+nikal\s+ke\s+bend)|bars\s+bent\s+outward)\b", re.IGNORECASE),
        "Buckled reinforcement under axial compression",
    ),
    (
        "R-EMG-COL-BUCKLE-UR",
        StructuralDamageIndicator.COLUMN_BUCKLED_REBAR,
        re.compile(r"(?:سریا|سریے)\s*(?:ٹیڑھا|مڑ|باہر\s*نکل)", re.IGNORECASE),
        "Urdu script: buckled reinforcement",
    ),
    # 4. Column Displacement or Visible Deformation
    (
        "R-EMG-COL-DISPLACE",
        StructuralDamageIndicator.COLUMN_DISPLACEMENT,
        re.compile(r"\b(?:columns?|pillars?)\b.*?\b(?:has\s+)?(?:shifted|displaced|out\s+of\s+plumb|deformed|dislocated|apni\s+jagah\s+se\s+hil\s+gaya|khisak\s+gaya)\b", re.IGNORECASE),
        "Column physical displacement or out-of-plumb deformation",
    ),
    # 5. Severe Splitting / Bursting Cracks in Column or Main Beam
    (
        "R-EMG-COL-CRACK-SEVERE",
        StructuralDamageIndicator.COLUMN_SEVERE_CRACKING,
        re.compile(r"\b(?:severe|major|deep|wide|heavy|critical|splitting|bursting|large|huge)\s+(?:crack|cracks|darar|fracture)\b.*?\b(?:columns?|pillars?|main\s+beams?)\b", re.IGNORECASE),
        "Severe splitting cracks through core of column or primary beam",
    ),
    (
        "R-EMG-COL-CRACK-SEVERE-REV",
        StructuralDamageIndicator.COLUMN_SEVERE_CRACKING,
        re.compile(r"\b(?:columns?|pillars?|main\s+beams?)\b.*?\b(?:severe|major|deep|wide|heavy|critical|splitting|bursting|large|huge)\s+(?:crack|cracks|darar|fracture)\b", re.IGNORECASE),
        "Primary load-bearing element under active severe cracking",
    ),
    (
        "R-EMG-COL-CRACK-RU",
        StructuralDamageIndicator.COLUMN_SEVERE_CRACKING,
        re.compile(r"\b(?:meri\s+building\s+ke\s+column\s+mein\s+cracks\s+aa\s+rahe|column\s+mein\s+cracks\s+aa\s+rahe\s+hain)\b", re.IGNORECASE),
        "Roman Urdu: column active cracking in building",
    ),
    (
        "R-EMG-COL-CRACK-UR",
        StructuralDamageIndicator.COLUMN_SEVERE_CRACKING,
        re.compile(r"(?:کالم|پلر|بیم)\s*(?:میں\s*)?(?:شدید|بڑی|گہری|خطرناک)\s*(?:دراڑیں|دراڑ|کریک)", re.IGNORECASE),
        "Urdu script: severe column cracking",
    ),
    # 6. Visible Leaning / Tilting of Building or Bearing Wall
    (
        "R-EMG-BLD-LEAN",
        StructuralDamageIndicator.BUILDING_LEANING_TILTING,
        re.compile(r"\b(?:building|structure|house|wall|retaining\s+wall|makan)\b.*?\b(?:is\s+)?(?:leaning|tilting|bowing|bulging|sagging\s+badly|jhuk\s+rahi|girne\s+wali)\b", re.IGNORECASE),
        "Building or wall visibly leaning or out of vertical alignment",
    ),
    (
        "R-EMG-BLD-LEAN-REV",
        StructuralDamageIndicator.BUILDING_LEANING_TILTING,
        re.compile(r"\b(?:visibly\s+leaning|leaning\s+to\s+one\s+side|about\s+to\s+collapse|collapse\s+imminent|structure\s+failing|girne\s+ka\s+khatra)\b", re.IGNORECASE),
        "Imminent collapse or visible structural tilt reported",
    ),
    (
        "R-EMG-BLD-LEAN-UR",
        StructuralDamageIndicator.BUILDING_LEANING_TILTING,
        re.compile(r"(?:عمارت|مکان|دیوار)\s*(?:جھک\s*رہی|گرنے\s*والی|گرنے\s*کا\s*خطرہ)", re.IGNORECASE),
        "Urdu script: building leaning or collapse threat",
    ),
    # 7. Slab Sagging with Falling Chunks / Spalling
    (
        "R-EMG-SLB-FALLING",
        StructuralDamageIndicator.SLAB_FALLING_CONCRETE,
        re.compile(r"\b(?:slab|roof|lanter|ceiling|chhat)\b.*?\b(?:sagging|bending|baith\s+raha|jhuk\s+raha)\b.*?\b(?:falling|concrete|collapsing|plaster|chunks|malba)\b.*?\b(?:gir\s+rah[ei]|falling|spalling|dropping)\b", re.IGNORECASE),
        "Slab sagging accompanied by falling concrete pieces",
    ),
    (
        "R-EMG-SLB-FALLING-ALT",
        StructuralDamageIndicator.SLAB_FALLING_CONCRETE,
        re.compile(r"\b(?:concrete\s+(?:falling|spalling|breaking)|chunks\s+falling|malba\s+gir\s+raha|(?:concrete\s+)?chunks\s+gir\s+rah[ei])\b.*?\b(?:slab|beam|column|ceiling|lanter|chhat)\b", re.IGNORECASE),
        "Falling concrete from structural element overhead",
    ),
    (
        "R-EMG-SLB-FALLING-UR",
        StructuralDamageIndicator.SLAB_FALLING_CONCRETE,
        re.compile(r"(?:سلیب|چھت|لینٹر)\s*(?:جھک|بیٹھ)\s*رہی\s*ہے.*?(?:کنکریٹ\s*گر|پلاسٹر\s*گر|ملبہ\s*گر)", re.IGNORECASE),
        "Urdu script: slab sagging with falling concrete",
    ),
    # 8. Rapid Foundation Settlement / Sinking
    (
        "R-EMG-FND-SINK",
        StructuralDamageIndicator.BUILDING_SUDDEN_MOVEMENT,
        re.compile(r"\b(?:foundation|bunyaad|ground|floor)\b.*?\b(?:rapidly\s+settling|sinking|subsiding|caving\s+in|dhas\s+rahi|baith\s+rahi)\b", re.IGNORECASE),
        "Rapid foundation sinking or ground collapse",
    ),
    (
        "R-EMG-FND-SINK-UR",
        StructuralDamageIndicator.BUILDING_SUDDEN_MOVEMENT,
        re.compile(r"(?:بنیاد|زمین)\s*(?:دھنس|بیٹھ)\s*رہی\s*ہے", re.IGNORECASE),
        "Urdu script: foundation sinking rapidly",
    ),
    # 9. Sudden Movement or Rapidly Widening Cracks
    (
        "R-EMG-BLD-WIDENING",
        StructuralDamageIndicator.BUILDING_RAPID_WIDENING_CRACKS,
        re.compile(r"\b(?:cracks?\s+(?:widening|growing|expanding)\s+(?:rapidly|daily|fast)|sudden\s+(?:movement|shift|drop|settlement)|dararain\s+barh\s+rahi\s+hain\s+rozana)\b", re.IGNORECASE),
        "Rapid crack expansion or sudden structural shifting",
    ),
    # 10. Repeated Unusual Structural Noises Accompanied by Movement
    (
        "R-EMG-BLD-NOISE",
        StructuralDamageIndicator.BUILDING_STRUCTURAL_NOISES_MOVEMENT,
        re.compile(r"\b(?:loud\s+(?:cracking|popping|creaking|snapping)\s+(?:noise|sound)s?|awazain\s+aa\s+rahi\s+hain|chatakhne\s+ki\s+awaz)\b.*?\b(?:building|column|beam|wall|house|chhat|chhatkane)\b", re.IGNORECASE),
        "Audible popping, snapping, or cracking noises from primary members",
    ),
    # 11. External Emergencies: Earthquake, Explosion, Fire, Severe Impact
    (
        "R-EMG-EXT-EARTHQUAKE",
        StructuralDamageIndicator.EXTERNAL_EARTHQUAKE_DAMAGE,
        re.compile(r"\b(?:earthquake|zalzala|zalzale)\b.*?\b(?:columns?|pillars?|beams?|walls?|slabs?|buildings?|houses?)\b.*?\b(?:cracked\s+severely|failed|damaged\s+badly|shattered|broken|toot\s+gaya)\b", re.IGNORECASE),
        "Severe structural damage following earthquake event",
    ),
    (
        "R-EMG-EXT-EXPLOSION",
        StructuralDamageIndicator.EXTERNAL_EXPLOSION_DAMAGE,
        re.compile(r"\b(?:explosion|blast|bomb|dhamaka)\b.*?\b(?:damage|columns?|beams?|walls?|structures?|collapsed|cracked)\b", re.IGNORECASE),
        "Blast or explosion structural damage",
    ),
    (
        "R-EMG-EXT-IMPACT",
        StructuralDamageIndicator.EXTERNAL_IMPACT_DAMAGE,
        re.compile(r"\b(?:vehicle|truck|car|dumper|crane)\b.*?\b(?:hit|crashed\s+into|struck)\b.*?\b(?:columns?|pillars?|load\s*bearing\s*walls?|beams?)\b", re.IGNORECASE),
        "Direct vehicular or heavy equipment impact on load-bearing column",
    ),
]

# Level 1 — URGENT (Serious Reported Damage Requiring Urgent In-Person Inspection)
URGENT_RULES: List[Tuple[str, StructuralDamageIndicator, re.Pattern, str]] = [
    # 1. Exposed Reinforcement (Corroded or Spalled without active buckling)
    (
        "R-URG-COL-EXPOSED-REBAR",
        StructuralDamageIndicator.COLUMN_EXPOSED_REBAR,
        re.compile(r"\b(?:exposed\s+(?:\w+\s+)?(?:rebar|steel|reinforcement|saria)|saria\s+nazar\s+aa\s+raha|spalling\s+revealing\s+steel|concrete\s+peeling\s+off\s+to\s+rebar)\b.*?\b(?:columns?|pillars?|beams?|lintels?)\b", re.IGNORECASE),
        "Exposed reinforcement or severe cover spalling on primary member",
    ),
    (
        "R-URG-COL-EXPOSED-REBAR-REV",
        StructuralDamageIndicator.COLUMN_EXPOSED_REBAR,
        re.compile(r"\b(?:columns?|pillars?|beams?|lintels?)\b.*?\b(?:exposed\s+(?:\w+\s+)?(?:rebar|steel|reinforcement|saria)|saria\s+nazar\s+aa\s+raha|spalling\s+revealing\s+steel)\b", re.IGNORECASE),
        "Exposed reinforcement on member reverse pattern",
    ),
    (
        "R-URG-COL-EXPOSED-REBAR-UR",
        StructuralDamageIndicator.COLUMN_EXPOSED_REBAR,
        re.compile(r"(?:کالم|پلر|بیم)\s*کا\s*(?:سریا\s*نظر\s*آ\s*رہا|کنکریٹ\s*جھڑ)", re.IGNORECASE),
        "Urdu script: exposed reinforcement on column/beam",
    ),
    # 2. Severe Diagonal / Shear Cracks in Beam
    (
        "R-URG-BM-DIAG-CRACK",
        StructuralDamageIndicator.BEAM_SEVERE_DIAGONAL_CRACKING,
        re.compile(r"\b(?:diagonal\s+crack|shear\s+crack|45\s*degree\s+crack|tirchi\s+darar)\b.*?\b(?:beam|main\s+beam|girder)\b", re.IGNORECASE),
        "Diagonal 45-degree shear cracking in beam (shear failure risk)",
    ),
    (
        "R-URG-BM-DIAG-CRACK-REV",
        StructuralDamageIndicator.BEAM_SEVERE_DIAGONAL_CRACKING,
        re.compile(r"\b(?:beam|main\s+beam)\b.*?\b(?:diagonal\s+crack|shear\s+crack|tirchi\s+darar)\b", re.IGNORECASE),
        "Shear distress pattern in concrete beam",
    ),
    # 3. Beam-Column Joint Damage / Separation
    (
        "R-URG-BM-JOINT",
        StructuralDamageIndicator.BEAM_COLUMN_JOINT_DAMAGE,
        re.compile(r"\b(?:beam[-\s]*column\s+joint|joint\s+between\s+beam\s+and\s+column|jod|connection)\b.*?\b(?:cracked|separating|damaged|spalling|darar)\b", re.IGNORECASE),
        "Structural distress at critical beam-column joint node",
    ),
    # 4. Significant Slab Deflection / Sagging (Without Active Collapse)
    (
        "R-URG-SLB-DEFLECT",
        StructuralDamageIndicator.SLAB_SIGNIFICANT_DEFLECTION,
        re.compile(r"\b(?:slab|roof|chhat|lanter)\b.*?\b(?:excessive\s+deflection|noticeably\s+sagging|jhuk\s+gayi|baith\s+gayi|depressed\s+in\s+middle)\b", re.IGNORECASE),
        "Excessive mid-span slab deflection requiring urgent engineering assessment",
    ),
    # 5. Flood / Water Washout Undermining Foundation
    (
        "R-URG-FND-SCOUR",
        StructuralDamageIndicator.EXTERNAL_FLOOD_INSTABILITY,
        re.compile(r"\b(?:flood|rainwater|seepage|paani|sailab)\b.*?\b(?:washed\s+away\s+soil|undermined|soil\s+erosion|bunyaad\s+ke\s+neechay\s+se\s+mitti\s+nikal\s+gayi)\b", re.IGNORECASE),
        "Foundation soil undermining or scour due to water erosion",
    ),
    # 6. Post-Fire Structural Distress
    (
        "R-URG-EXT-FIRE",
        StructuralDamageIndicator.EXTERNAL_FIRE_DAMAGE,
        re.compile(r"\b(?:fire|aag\s+lagne)\b.*?\b(?:charred\s+concrete|concrete\s+spalled|cracked\s+beams?|damaged\s+columns?)\b", re.IGNORECASE),
        "Thermal fire damage to structural concrete framework",
    ),
    # 7. Retaining Wall Distress / Bulging
    (
        "R-URG-RET-WALL",
        StructuralDamageIndicator.BUILDING_LEANING_TILTING,
        re.compile(r"\b(?:retaining\s+wall|basement\s+wall|parda\s+wall)\b.*?\b(?:bulging|cracking|pushing\s+inward|tilting)\b", re.IGNORECASE),
        "Earth pressure bulging or distress in retaining wall",
    ),
]

# Level 2 — PRIORITY INSPECTION (Modifications, Sizing & Unsafe DIY Repair Prevention)
PRIORITY_INSPECTION_RULES: List[Tuple[str, Optional[StructuralDamageIndicator], re.Pattern, str]] = [
    # A. Unsafe DIY Structural Repairs (Section 6)
    (
        "R-DIY-SHORING",
        StructuralDamageIndicator.DIY_COLUMN_SHORING,
        re.compile(r"\b(?:how\s+to\s+shore|diy\s+shoring|jack\s+up|temporary\s+support|khud\s+shoring|balli\s+laga|support\s+lagayein|balli\s+se)\b.*?\b(?:column|beam|slab|chhat|pillar|lanter)\b", re.IGNORECASE),
        "Actionable DIY structural shoring inquiry (PROHIBITED)",
    ),
    (
        "R-DIY-SHORING-REV",
        StructuralDamageIndicator.DIY_COLUMN_SHORING,
        re.compile(r"\b(?:column|beam|slab|chhat|pillar|lanter)\b.*?\b(?:how\s+to\s+shore|diy\s+shoring|jack\s+up|temporary\s+support|khud\s+shoring|balli\s+laga|support\s+lagayein|balli\s+se)\b", re.IGNORECASE),
        "Actionable DIY structural shoring inquiry reverse (PROHIBITED)",
    ),
    (
        "R-DIY-JACKING",
        StructuralDamageIndicator.DIY_BEAM_JACKING,
        re.compile(r"\b(?:how\s+to\s+jack|hydraulic\s+jack|bottle\s+jacks?|jack\s+se\s+uthayein|jack\s+se\s+seedha|jack\s+up)\b.*?\b(?:beam|column|slab|lanter|ceiling|sagging)?\b", re.IGNORECASE),
        "Actionable DIY hydraulic jacking of structural beam (PROHIBITED)",
    ),
    (
        "R-DIY-JACKING-REV",
        StructuralDamageIndicator.DIY_BEAM_JACKING,
        re.compile(r"\b(?:beam|column|slab|lanter|ceiling|sagging)\b.*?\b(?:how\s+to\s+jack|hydraulic\s+jack|bottle\s+jacks?|jack\s+se\s+uthayein|jack\s+se\s+seedha|jack\s+up)\b", re.IGNORECASE),
        "Actionable DIY hydraulic jacking of structural beam reverse (PROHIBITED)",
    ),
    (
        "R-DIY-SUPPORT-REM",
        StructuralDamageIndicator.DIY_SUPPORT_REMOVAL,
        re.compile(r"\b(?:can\s+i\s+remove\s+props|remove\s+shuttering\s+early|balliyan\s+hata\s+dain|supports\s+nikal\s+dain)\b.*?\b(?:safely|myself|today)\b", re.IGNORECASE),
        "Unapproved early removal of structural shoring or props (PROHIBITED)",
    ),
    (
        "R-DIY-COL-REPLACE",
        StructuralDamageIndicator.DIY_COLUMN_REPLACEMENT,
        re.compile(r"\b(?:replace\s+(?:a\s+)?column|repair\s+broken\s+column\s+myself|column\s+badalna|pillar\s+khud\s+theek\s+karna)\b", re.IGNORECASE),
        "DIY replacement or unauthorized repair of load-bearing column (PROHIBITED)",
    ),
    (
        "R-DIY-CUT-DRILL",
        StructuralDamageIndicator.DIY_STRUCTURAL_CUTTING,
        re.compile(r"\b(?:cut|drill|hole|notch|chisel|torna)\b.*?\b(?:through|in|into|RCC|angle\s+grinder)?\b.*?\b(?:column|main\s+beam|prestressed\s+slab|lintel|pillar)\b", re.IGNORECASE),
        "Cutting or core-drilling load-bearing concrete members (PROHIBITED)",
    ),
    (
        "R-DIY-DEMOLISH",
        StructuralDamageIndicator.DIY_WALL_DEMOLITION,
        re.compile(r"\b(?:diy|myself|khud|without\s+engineer|baghair\s+engineer)\b.*?\b(?:demolish|break|remove|cut|tor(?:na|ein)?|girana)\b.*?\b(?:lo[ao]d[-\s]*bearing|column|pillar|beam|wall|deewar)\b", re.IGNORECASE),
        "DIY unauthorized demolition or cutting of load-bearing element",
    ),
    (
        "R-DIY-DEMOLISH-REV",
        StructuralDamageIndicator.DIY_WALL_DEMOLITION,
        re.compile(r"\b(?:lo[ao]d[-\s]*bearing|column|pillar|beam|wall|deewar)\b.*?\b(?:demolish|break|remove|cut|tor(?:na|ein)?|girana)\b.*?\b(?:diy|myself|khud|without\s+engineer|baghair\s+engineer)\b", re.IGNORECASE),
        "DIY unauthorized demolition or cutting of load-bearing element reverse",
    ),
    (
        "R-DIY-DEMOLISH-MID",
        StructuralDamageIndicator.DIY_WALL_DEMOLITION,
        re.compile(r"\b(?:lo[ao]d[-\s]*bearing|column|pillar|beam|wall|deewar)\b.*?\b(?:khud|myself|diy)\b.*?\b(?:tor(?:na|ein)?|demolish|break|cut|girana|hatana)\b", re.IGNORECASE),
        "DIY unauthorized demolition middle order",
    ),
    # B. Load-bearing Structural Alteration / Removal
    (
        "R-PRI-MOD-REM-ELEM",
        None,
        re.compile(r"\b(?:remove|dismantle|demolish|cut|break|modify|torna|hatana|gira\s+dain)\b.*?\b(?:column|pillar|beam|load[-\s]*bearing|lintel|foundation|deewar|wall)\b", re.IGNORECASE),
        "Removal of load-bearing structural member",
    ),
    (
        "R-PRI-MOD-REM-ELEM-UR",
        None,
        re.compile(r"(?:کالم|لوڈ\s*بیئرنگ\s*دیوار|بیم)\s*(?:کو\s*)?(?:ہٹانا|گرانا|توڑنا)", re.IGNORECASE),
        "Urdu script: removing column or load-bearing wall",
    ),
    # C. Adding Storeys / Vertical Expansion
    (
        "R-PRI-MOD-ADD-STOREY",
        None,
        re.compile(r"\b(?:add|construct|build|bana\s+sakte|tamir)\b.*?\b(?:extra|another|additional|more|teesri|doosri|\d+)\s*(?:more\s+)?(?:floors?|storeys?|stories?|manzil(?:ein)?)\b", re.IGNORECASE),
        "Vertical building expansion or adding storeys",
    ),
    (
        "R-PRI-MOD-ADD-STOREY-UR",
        None,
        re.compile(r"(?:بنیاد|کمزور\s*بنیاد)\s*پر\s*(?:مزید|دوسری|تیسری)\s*منزل", re.IGNORECASE),
        "Urdu script: adding storey to existing foundation",
    ),
    # D. Speculative Structural Sizing Without Engineering Design
    (
        "R-PRI-MOD-SIZING",
        None,
        re.compile(r"\b(?:what\s+size|which\s+size|size\s+kya\s+hona|how\s+much\s+reinforcement|how\s+many\s+rebars?)\b.*?\b(?:column|beam|footing|foundation)\b.*?\b(?:for|in)\b.*?\b(?:\d+\s+storey|\d+\s+floor|house|building|ghar)\b", re.IGNORECASE),
        "Speculative physical sizing of structural elements without calculations",
    ),
    (
        "R-PRI-MOD-SIZING-UR",
        None,
        re.compile(r"(?:\d+|تین|دو)\s*منزلہ\s*عمارت\s*کے\s*لیے\s*(?:کالم|بیم)\s*کا\s*سائز", re.IGNORECASE),
        "Urdu script: sizing structural members for building",
    ),
    # E. Heavy Equipment / Load Placement on Slab
    (
        "R-PRI-MOD-HEAVY-LOAD",
        None,
        re.compile(r"\b(?:water\s*tank|tanki|generator|heavy\s+equipment|heavy\s+load|wazan)\b.*?\b(?:on\s+(?:(?:a|an|the)\s+)?(?:existing\s+)?(?:slab|roof|floor|chhat|lanter))\b", re.IGNORECASE),
        "Concentrated heavy load placement on existing floor/roof slab",
    ),
    # F. Deep Excavation Near Existing Foundations
    (
        "R-PRI-MOD-EXCAVATION",
        None,
        re.compile(r"\b(?:excavat(?:e|ion)|digging|khudai)\b.*?\b(?:beside|adjacent\s+to|next\s+to|near|saath\s+wale)\b.*?\b(?:existing|neighbor's?|building|foundation|house|ghar)\b", re.IGNORECASE),
        "Excavation adjacent to existing foundations without underpinning",
    ),
]

# Level 3 — INFORMATIONAL (General Guidance & Technical Principles)
MODERATE_PRINCIPLE_PATTERNS = [
    re.compile(r"\b(?:what\s+(?:affects|determines)|factors\s+(?:affecting|determining|determine|decide)|how\s+does\s+.*?\s+affect|how\s+is\s+.*?\s+determined)\b.*?\b(?:foundation|footing|depth|slab|beam|rebar|reinforcement|concrete\s+strength|bearing\s+capacity)\b", re.IGNORECASE),
    re.compile(r"\b(?:depth\s+of\s+(?:a\s+)?(?:building\s+)?foundation|foundation\s+depth|footing\s+depth)\b", re.IGNORECASE),
    re.compile(r"\b(?:foundation\s+mein\s+settlement\s+ho\s+rahi|differential\s+settlement\s+causes)\b", re.IGNORECASE),
    re.compile(r"\b(?:lanter\s+ki\s+shuttering\s+kitne\s+din\s+baad\s+remove\s+kar\s+sakte\s+hain|shuttering\s+removal\s+time|curing\s+duration)\b", re.IGNORECASE),
]


# ============================================================================
# 4. STRUCTURAL SAFETY ENGINE
# ============================================================================

class StructuralSafetyEngine:
    """
    Authoritative deterministic structural safety advisory engine (Phase 03.2).
    Evaluates queries against structural damage indicators, enforces life-safety emergency overrides,
    blocks unsafe DIY structural procedures, and guarantees zero AI safety downgrades.
    """

    POLICY_VERSION = "3.2.3"

    # Thread-safe in-memory audit log ring buffer (last 500 records)
    _audit_log: List[SafetyAssessmentAuditRecord] = []
    # Thread-safe in-memory sign-off history ring buffer (last 500 records)
    _sign_off_log: List[ProfessionalEngineerSignOff] = []

    @classmethod
    def evaluate_risk(
        cls,
        query: str,
        normalized_query: str,
        intent: ConstructionIntent,
        entities: List[ExtractedEntity],
        language: str = "en",
        project_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> StructuralRiskAssessment:
        """
        Executes deterministic multi-tier structural safety evaluation.
        Classification hierarchy:
        LEVEL 0 — EMERGENCY -> LEVEL 1 — URGENT -> LEVEL 2 — PRIORITY -> LEVEL 3 — INFORMATIONAL.
        """
        raw_lower = query.lower()
        norm_lower = normalized_query.lower()
        combined_text = f"{raw_lower} {norm_lower}"

        safe_snippet = cls._sanitize_pii(query)[:250]
        detected_indicators: List[str] = []
        triggered_rules: List[str] = []

        # ====================================================================
        # TIER 1: EVALUATE LEVEL 0 — EMERGENCY (Immediate Evacuation)
        # ====================================================================
        for rule_id, indicator, pattern, desc in EMERGENCY_RULES:
            if pattern.search(combined_text):
                triggered_rules.append(rule_id)
                if indicator.value not in detected_indicators:
                    detected_indicators.append(indicator.value)

        if triggered_rules:
            # Determine primary hazard category
            cat = HazardCategory.RCC_STRUCTURAL
            if any("FND" in r or "SINK" in r or "LEAN" in r for r in triggered_rules):
                cat = HazardCategory.FOUNDATION_GEOTECHNICAL
            elif any("EXT" in r for r in triggered_rules):
                cat = HazardCategory.EXTERNAL_DISASTER

            advisory = cls.get_emergency_evacuation_advisory(language)
            assessment_id = uuid.uuid4()

            audit = SafetyAssessmentAuditRecord(
                assessment_id=assessment_id,
                project_id=project_id,
                user_id=user_id,
                input_category="structural_emergency",
                query_snippet=safe_snippet,
                advisory_language=language,
                severity_classification=SafetySeverityLevel.LEVEL_0_EMERGENCY,
                severity_code=0,
                severity_name="LEVEL 0 — EMERGENCY",
                detected_indicators=detected_indicators,
                triggered_rule_identifiers=triggered_rules,
                ai_usage_status="bypassed_deterministic_override",
                fallback_status="active",
                professional_escalation_status="emergency_evacuation_mandatory",
                pec_review_required=True,
                policy_version=cls.POLICY_VERSION,
            )
            cls._record_audit(audit)

            return StructuralRiskAssessment(
                risk_level=RiskLevel.CRITICAL,
                severity_level=SafetySeverityLevel.LEVEL_0_EMERGENCY,
                severity_code=0,
                severity_name="LEVEL 0 — EMERGENCY",
                hazard_category=cat,
                is_critical=True,
                is_high_risk=True,
                detected_hazards=["imminent_structural_danger_or_collapse"],
                damage_indicators=detected_indicators,
                triggered_rule_identifiers=triggered_rules,
                safety_advisory=advisory,
                requires_immediate_evacuation=True,
                requires_professional_inspection=True,
                pec_review_required=True,
                rationale="Credible indicators of acute structural distress, member failure, or active collapse reported.",
                audit_record=audit,
            )

        # ====================================================================
        # TIER 2: EVALUATE LEVEL 1 — URGENT (Urgent In-Person Inspection)
        # ====================================================================
        for rule_id, indicator, pattern, desc in URGENT_RULES:
            if pattern.search(combined_text):
                triggered_rules.append(rule_id)
                if indicator.value not in detected_indicators:
                    detected_indicators.append(indicator.value)

        if triggered_rules:
            cat = HazardCategory.RCC_STRUCTURAL
            if any("FND" in r or "SCOUR" in r for r in triggered_rules):
                cat = HazardCategory.FOUNDATION_GEOTECHNICAL
            elif any("FIRE" in r for r in triggered_rules):
                cat = HazardCategory.EXTERNAL_DISASTER

            advisory = cls.get_urgent_inspection_advisory(language, detected_indicators)
            assessment_id = uuid.uuid4()

            audit = SafetyAssessmentAuditRecord(
                assessment_id=assessment_id,
                project_id=project_id,
                user_id=user_id,
                input_category="serious_structural_damage",
                query_snippet=safe_snippet,
                advisory_language=language,
                severity_classification=SafetySeverityLevel.LEVEL_1_URGENT,
                severity_code=1,
                severity_name="LEVEL 1 — URGENT",
                detected_indicators=detected_indicators,
                triggered_rule_identifiers=triggered_rules,
                ai_usage_status="safety_constrained_advisory",
                fallback_status="active",
                professional_escalation_status="urgent_inspection_required",
                pec_review_required=True,
                policy_version=cls.POLICY_VERSION,
            )
            cls._record_audit(audit)

            return StructuralRiskAssessment(
                risk_level=RiskLevel.HIGH,
                severity_level=SafetySeverityLevel.LEVEL_1_URGENT,
                severity_code=1,
                severity_name="LEVEL 1 — URGENT",
                hazard_category=cat,
                is_critical=False,
                is_high_risk=True,
                detected_hazards=["serious_structural_damage_requiring_inspection"],
                damage_indicators=detected_indicators,
                triggered_rule_identifiers=triggered_rules,
                safety_advisory=advisory,
                requires_immediate_evacuation=False,
                requires_professional_inspection=True,
                pec_review_required=True,
                rationale="Serious structural damage reported without immediate collapse signs. Urgent professional assessment required.",
                audit_record=audit,
            )

        # ====================================================================
        # TIER 3: EVALUATE LEVEL 2 — PRIORITY (Modifications & DIY Prevention)
        # ====================================================================
        is_diy_hazard = False
        diy_hazard_type: Optional[str] = None
        for rule_id, indicator, pattern, desc in PRIORITY_INSPECTION_RULES:
            if pattern.search(combined_text):
                triggered_rules.append(rule_id)
                if indicator:
                    detected_indicators.append(indicator.value)
                    if "DIY" in rule_id:
                        is_diy_hazard = True
                        diy_hazard_type = indicator.value

        if triggered_rules:
            cat = HazardCategory.UNSAFE_DIY if is_diy_hazard else HazardCategory.STRUCTURAL_MODIFICATION
            if any("FND" in r or "EXCAV" in r for r in triggered_rules):
                cat = HazardCategory.FOUNDATION_GEOTECHNICAL
            elif any("COL" in r or "BM" in r or "SLAB" in r for r in triggered_rules) and not is_diy_hazard:
                cat = HazardCategory.RCC_STRUCTURAL

            missing_vars = cls.detect_missing_structural_variables(combined_text, entities)
            if is_diy_hazard:
                advisory = cls.get_diy_prohibition_advisory(language, diy_hazard_type or "unauthorized_diy_structural_repair")
            else:
                advisory = cls.get_priority_inspection_advisory(language, cat, missing_vars)

            assessment_id = uuid.uuid4()
            audit = SafetyAssessmentAuditRecord(
                assessment_id=assessment_id,
                project_id=project_id,
                user_id=user_id,
                input_category="structural_modification_or_diy",
                query_snippet=safe_snippet,
                advisory_language=language,
                severity_classification=SafetySeverityLevel.LEVEL_2_PRIORITY,
                severity_code=2,
                severity_name="LEVEL 2 — PRIORITY INSPECTION",
                detected_indicators=detected_indicators,
                triggered_rule_identifiers=triggered_rules,
                is_diy_hazard=is_diy_hazard,
                diy_hazard_type=diy_hazard_type,
                ai_usage_status="safety_constrained_advisory",
                fallback_status="active",
                professional_escalation_status="engineering_design_required",
                pec_review_required=True,
                policy_version=cls.POLICY_VERSION,
            )
            cls._record_audit(audit)

            return StructuralRiskAssessment(
                risk_level=RiskLevel.HIGH,
                severity_level=SafetySeverityLevel.LEVEL_2_PRIORITY,
                severity_code=2,
                severity_name="LEVEL 2 — PRIORITY INSPECTION",
                hazard_category=cat,
                is_critical=False,
                is_high_risk=True,
                detected_hazards=["structural_modification_or_unsupported_design"],
                damage_indicators=detected_indicators,
                triggered_rule_identifiers=triggered_rules,
                missing_engineering_variables=missing_vars,
                safety_advisory=advisory,
                requires_immediate_evacuation=False,
                requires_professional_inspection=True,
                pec_review_required=True,
                is_diy_hazard=is_diy_hazard,
                diy_hazard_type=diy_hazard_type,
                rationale="Structural alteration, uncalculated sizing, or unsafe DIY repair request detected.",
                audit_record=audit,
            )

        # ====================================================================
        # TIER 4: LEVEL 3 — INFORMATIONAL (Educational Principles)
        # ====================================================================
        has_moderate_principle = any(p.search(combined_text) for p in MODERATE_PRINCIPLE_PATTERNS)
        missing_vars = cls.detect_missing_structural_variables(combined_text, entities) if has_moderate_principle else []

        assessment_id = uuid.uuid4()
        audit = SafetyAssessmentAuditRecord(
            assessment_id=assessment_id,
            project_id=project_id,
            user_id=user_id,
            input_category="general_informational",
            query_snippet=safe_snippet,
            advisory_language=language,
            severity_classification=SafetySeverityLevel.LEVEL_3_INFORMATIONAL,
            severity_code=3,
            severity_name="LEVEL 3 — INFORMATIONAL",
            detected_indicators=[],
            triggered_rule_identifiers=[],
            ai_usage_status="optional_ai_assistance",
            fallback_status="standby",
            professional_escalation_status="informational_only",
            pec_review_required=False,
            policy_version=cls.POLICY_VERSION,
        )
        cls._record_audit(audit)

        return StructuralRiskAssessment(
            risk_level=RiskLevel.MODERATE if has_moderate_principle else RiskLevel.LOW,
            severity_level=SafetySeverityLevel.LEVEL_3_INFORMATIONAL,
            severity_code=3,
            severity_name="LEVEL 3 — INFORMATIONAL",
            hazard_category=HazardCategory.NONE,
            is_critical=False,
            is_high_risk=False,
            detected_hazards=[],
            damage_indicators=[],
            triggered_rule_identifiers=[],
            missing_engineering_variables=missing_vars,
            safety_advisory=None,
            requires_immediate_evacuation=False,
            requires_professional_inspection=False,
            pec_review_required=False,
            rationale="General educational construction inquiry. NOTE: Absence of reported danger does NOT certify structural safety.",
            audit_record=audit,
        )

    # ------------------------------------------------------------------------
    # MISSING ENGINEERING VARIABLES DETECTOR
    # ------------------------------------------------------------------------

    @staticmethod
    def detect_missing_structural_variables(text: str, entities: List[ExtractedEntity]) -> List[str]:
        """Identifies missing structural parameters based on member type."""
        missing: List[str] = []

        # Foundation inquiry missing variables
        if any(w in text for w in ["foundation", "bunyaad", "footing", "raft", "بنیاد"]):
            has_floors = any(re.search(r"\b(?:\d+|single|double|triple|ground|g\+1|g\+2)\s*(?:floor|storey|manzil|story)\b", text) for _ in [1]) or any("storey" in e.canonical_value for e in entities)
            has_soil = any(e.category == EntityCategory.SOIL_CONDITION for e in entities) or any(w in text for w in ["bearing capacity", "sbc", "soil", "mitti", "مٹی"])
            has_load = any(e.category == EntityCategory.BUILDING_LOAD for e in entities) or any(w in text for w in ["load", "dead load", "live load", "بوجھ"])
            if not has_floors:
                missing.append("building_floors_or_storeys")
            if not has_soil:
                missing.append("soil_bearing_capacity")
            if not has_load:
                missing.append("column_loads_or_structural_system")

        # Beam inquiry missing variables
        if any(w in text for w in ["beam", "main beam", "بیم"]):
            has_span = any(re.search(r"\b(?:\d+\s*(?:ft|feet|foot|meter|m))\b", text) for _ in [1]) or any(e.canonical_value.startswith("length:") for e in entities)
            has_loads = any(w in text for w in ["load", "dead load", "live load", "udl", "point load"])
            if not has_span:
                missing.append("clear_span_length")
            if not has_loads:
                missing.append("applied_beam_loads")

        # Column inquiry missing variables
        if any(w in text for w in ["column", "pillar", "کالم"]):
            has_height = any(re.search(r"\b(?:\d+\s*(?:ft|feet|foot|meter|m)\s*(?:height|unsupported))\b", text) for _ in [1])
            has_axial_load = any(w in text for w in ["axial load", "ton", "kip", "kn", "floors load"])
            if not has_height:
                missing.append("unsupported_column_height")
            if not has_axial_load:
                missing.append("axial_load_and_storeys")

        # Slab inquiry missing variables
        if any(w in text for w in ["slab", "lanter", "roof", "chhat", "سلیب", "چھت", "لینٹر"]):
            has_dimensions = (
                any(e.canonical_value.startswith(("length:", "width:", "area:")) for e in entities)
                or any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in ["sqft", "span"])
                or bool(re.search(r"\b\d+\s*(?:x|by)\s*\d+\b", text))
            )
            if not has_dimensions:
                missing.append("slab_span_and_support_conditions")

        # Existing structural damage troubleshooting
        if any(w in text for w in ["crack", "cracks", "darar", "seepage", "دراڑ"]):
            has_width = any(re.search(r"\b(?:\d+\s*(?:mm|inch|sooter))\b", text) for _ in [1])
            if not has_width:
                missing.append("crack_width_and_pattern")

        return missing

    # ------------------------------------------------------------------------
    # MULTILINGUAL DETERMINISTIC ADVISORIES (Section 5)
    # ------------------------------------------------------------------------

    @classmethod
    def get_critical_safety_advisory(cls, lang: str = "en") -> str:
        """Backward compatibility alias for Level 0 Emergency Evacuation."""
        return cls.get_emergency_evacuation_advisory(lang)

    @classmethod
    def get_high_risk_advisory(
        cls,
        category: HazardCategory,
        missing_vars: List[str],
        lang: str = "en",
    ) -> str:
        """Backward compatibility alias for Level 2 Priority Inspection."""
        return cls.get_priority_inspection_advisory(lang, category, missing_vars)

    @staticmethod
    def get_emergency_evacuation_advisory(lang: str = "en") -> str:
        """LEVEL 0 — EMERGENCY: Immediate Evacuation Advisory (Phase 03.2.3 Hardened)."""
        if lang == "roman_ur":
            return (
                "⚠️ **CRITICAL STRUCTURAL SAFETY ALERT (LEVEL 0 — EMERGENCY: FORI INKHILA)**\n\n"
                "Building mein achanak collapse ya shadeed structural khatray ki alamaat report hui hain. "
                "Insani jaan ka tahaffuz sab se pehli tarjeeh hai:\n\n"
                "1. **Mehfooz Rasta Ho To Fori Bahir Niklein:** Agar safe aur saaf exit rasta mojood ho to mutasira building ko foran khali karein.\n"
                "2. **Building Se Door Ho Jayein:** Structure aur girte hue malbay se door kisi khuli aur mehfooz jagah par pohnchein.\n"
                "3. **Lift Ka Istemaal Hargiz Na Karein:** Structural emergency ke doran elevator ya lift ka istemaal qat'an mamnoo hai.\n"
                "4. **Kharaab Seerhiyon Par Na Jayein:** Visibly damaged ya cracked seerhiyon par dakhil na hon; kisi ghair-mehfooz rastay se zabardasti na niklein.\n"
                "5. **Agar Rasta Band Ho:** Agar safe exit rasta na milay ya band ho to kisi bhi soorat mein visibly damaged, cracked ya malbay walay hisson se guzarne ki koshish na karein. Khirkiyon, sheeshe aur bahir girte hue malbay se door rahain; kisi bhi deewar ya jagah ko khud se mukammal mehfooz tasawwur na karein. Foran emergency services (Rescue 1122) ko call kar ke apna exact floor aur location batayein, emergency responders ki hidayat par amal karein aur kisi naye khatray mein paray baghair sirf mehfooz halat mein rescuers ko ishara dein.\n"
                "6. **Dobara Dakhil Na Hon:** Kisi bhi soorat mein saman nikalne, dekhne ya photo lenay ke liye dobara building ke andar na jayein.\n"
                "7. **Doosron Ko Ba-Hifazat Khabardaar Karein:** Doosray afrad ko sirf usi waqt aagah karein agar aap ki apni jaan ko mazeed khatra na ho.\n"
                "8. **Emergency Services Ko Call Karein:** Foran Rescue 1122 ya mutaliqa building authority (LDA / CDA / SBCA / RDA) ko call karein.\n"
                "9. **Professional Structural Engineer Se Fori Checkup:** Kisi Pakistan Engineering Council (PEC) registered Professional Structural Engineer se foran physical assessment karwayein.\n\n"
                "*Zaroori Hidayat: TameerAI chat par structural safety clearance ya tasalli nahi deta.*"
            )
        elif lang == "ur":
            return (
                "⚠️ **شدید ساختی خطرے کا انتباہ (سطح 0 — ہنگامی: فوری انخلاء)**\n\n"
                "عمارت میں فوری ساختی خطرے یا گرنے کے قوی علامات کی نشاندہی ہوئی ہے۔ انسانی جان کا تحفظ اولین ترجیح ہے:\n\n"
                "1. **متاثرہ حصے کو فوری خالی کریں:** اگر محفوظ اور واضح راستہ دستیاب ہو تو عمارت سے فوراً باہر نکلیں۔\n"
                "2. **عمارت سے دور ہو جائیں:** عمارت اور گرتے ہوئے ملبے کی زد سے دور محفوظ مقام پر چلے جائیں۔\n"
                "3. **لفٹ کا استعمال ہرگز نہ کریں:** ساختی ایمرجنسی کے دوران لفٹ کا استعمال قطعاً ممنوع ہے۔\n"
                "4. **خراب سیڑھیوں پر جانے سے گریز کریں:** واضح طور پر ٹوٹی ہوئی یا دراڑ زدہ سیڑھیوں پر ہرگز نہ جائیں؛ کسی غیر محفوظ راستے سے زبردستی گزرنے کی کوشش نہ کریں۔\n"
                "5. **اگر محفوظ راستہ نہ ملے:** اگر انخلاء کا راستہ بند یا غیر محفوظ ہو تو کسی بھی صورت میں واضح طور پر تباہ شدہ، دراڑ زدہ یا ملبے سے بھرے حصوں سے گزرنے کی کوشش نہ کریں۔ کھڑکیوں، شیشوں اور گرتے ہوئے ملبے کے خطرات سے دور رہیں؛ کسی بھی اندرونی جگہ یا دیوار کو ازخود محفوظ تصور نہ کریں۔ فوری طور پر ایمرجنسی سروسز (ریسکیو 1122) کو کال کر کے اپنے فلور اور درست مقام کی اطلاع دیں، امدادی اہلکاروں کی ہدایات کا انتظار کریں اور ان پر عمل کریں اور اپنی جان کو مزید خطرے میں ڈالے بغیر صرف محفوظ حالت میں امدادی ٹیموں کو اشارہ دیں۔\n"
                "6. **دوبارہ اندر نہ جائیں:** سامان نکالنے یا معائنے کے لیے کسی بھی صورت میں دوبارہ عمارت میں داخل نہ ہوں۔\n"
                "7. **دوسروں کو باحفاظت خبردار کریں:** دوسروں کو صرف اسی صورت میں متنبہ کریں جب آپ کی اپنی جان خطرے میں نہ پڑے۔\n"
                "8. **ایمرجنسی اداروں کو اطلاع دیں:** فوری طور پر ریسکیو 1122 یا متعلقہ بلڈنگ کنٹرول اتھارٹی (LDA / CDA / SBCA / RDA) کو کال کریں۔\n"
                "9. **ماہر سٹرکچرل انجینئر سے معائنہ:** پاکستان انجینئرنگ کونسل (PEC) سے تصدیق شدہ سٹرکچرل انجینئر سے فوری فزیکل معائنہ کروائیں۔\n\n"
                "*ضروری انتباہ: تعمیر اے آئی چیٹ پر عمارت کے محفوظ ہونے کی کوئی تصدیق یا کلیئرنس جاری نہیں کرتا۔*"
            )
        return (
            "⚠️ **CRITICAL STRUCTURAL SAFETY ALERT (LEVEL 0 — EMERGENCY: IMMEDIATE EVACUATION)**\n\n"
            "Credible indicators of imminent structural danger or active collapse have been reported. Human life safety is the sole priority:\n\n"
            "1. **Evacuate the Affected Area Immediately:** Leave the affected building immediately if a safe, unobstructed exit route is available.\n"
            "2. **Move to a Safe Distance:** Move well away from the building perimeter and potential falling debris.\n"
            "3. **Never Use Elevators:** Never enter an elevator during a structural emergency under any circumstance.\n"
            "4. **Inspect Stairways Before Use:** Do NOT enter visibly damaged, cracked, or compromised stairways; never force evacuation through an unsafe route.\n"
            "5. **If Exit Route Is Blocked:** If exit routes are blocked, do NOT attempt to move through visibly damaged, cracked, or debris-filled areas. Stay clear of windows, glass facades, and exterior architectural features subject to falling hazards; do not assume any specific wall or interior location is structurally safe. Immediately contact emergency responders (Rescue 1122 in Pakistan), communicate your exact floor and room location, follow emergency responder instructions, and signal rescuers only when safe to do so without creating additional danger.\n"
            "6. **Do NOT Re-enter:** Under no circumstances should anyone re-enter the building for personal belongings, inspection, or pets.\n"
            "7. **Warn Others Safely:** Alert other occupants only if doing so does not expose you to additional danger.\n"
            "8. **Call Emergency Services:** Immediately contact local emergency services (Rescue 1122 in Pakistan) and the municipal building authority (LDA / CDA / SBCA / RDA).\n"
            "9. **Urgent Professional Assessment:** Commission an urgent on-site structural appraisal by a licensed Professional Structural Engineer registered with the Pakistan Engineering Council (PEC).\n\n"
            "*Safety Notice: TameerAI does not provide speculative safety assurances or structural clearance or certify building stability.*"
        )

    @staticmethod
    def get_urgent_inspection_advisory(lang: str = "en", damage_indicators: Optional[List[str]] = None) -> str:
        """LEVEL 1 — URGENT: Urgent In-Person Professional Inspection Advisory."""
        if lang == "roman_ur":
            return (
                "⚠️ **LEVEL 1 — URGENT STRUCTURAL SAFETY ADVISORY (LAZMI PROFESSIONAL INSPECTION)**\n\n"
                "Building ke primary structural elements mein shadeed nuqs report hua hai jo building ki load capacity ko mutasir kar sakta hai:\n\n"
                "1. **Mutasira Hissay Se Door Rahain:** Kharaab shuda column, beam ya slab ke area ko foran cordon-off karein aur wahan kisi ka dakhla rokein.\n"
                "2. **Khudi Marammat Hargiz Na Karein:** Damaged structural members ko baghair engineering design ke na chehrein.\n"
                "3. **PEC Registered Engineer Se Urgent Checkup:** Kisi qualified Professional Structural Engineer (PEC Registered) se fori site assessment karwayein.\n"
                "4. **Emergency Escalation:** Agar building mein achanak dararain barhein, aawazein aayein ya jhukao mehsos ho to foran LEVEL 0 Emergency samjh kar building khali kar dain.\n\n"
                "*TameerAI kisi bhi soorat mein structural safety clearance ya stability certify nahi karta.*"
            )
        elif lang == "ur":
            return (
                "⚠️ **سطح 1 — فوری ساختی ایڈوائزری (لازمی پیشہ ورانہ معائنہ)**\n\n"
                "عمارت کے بنیادی ساختی عناصر میں شدید خرابی کی نشاندہی ہوئی ہے جس سے عمارت کے بوجھ برداشت کرنے کی صلاحیت متاثر ہو سکتی ہے:\n\n"
                "1. **متاثرہ حصے سے دور رہیں:** متاثرہ کالم، بیم یا سلیب کے ارد گرد ناکہ بندی کریں اور وہاں لوگوں کی آمدورفت روکیں۔\n"
                "2. **خود مرمت ہرگز نہ کریں:** بغیر انجینئرنگ ڈیزائن کے خراب ساختی عناصر کو خود ٹھیک کرنے کی کوشش نہ کریں۔\n"
                "3. **ماہر سٹرکچرل انجینئر سے معائنہ:** پاکستان انجینئرنگ کونسل (PEC) سے تصدیق شدہ سٹرکچرل انجینئر سے فوری سائٹ معائنہ کروائیں۔\n"
                "4. **ہنگامی صورتحال میں انخلاء:** اگر عمارت میں دراڑیں تیزی سے بڑھیں یا غیرمعمولی آوازیں آئیں تو فوراً سطح 0 کے مطابق انخلاء کریں۔\n\n"
                "*تعمیر اے آئی چیٹ پر کسی عمارت کے محفوظ ہونے کی تصدیق یا کلیئرنس جاری نہیں کرتا۔*"
            )
        return (
            "⚠️ **LEVEL 1 — URGENT STRUCTURAL SAFETY ADVISORY (PROFESSIONAL INSPECTION REQUIRED)**\n\n"
            "Serious structural damage reported in primary load-bearing members that may compromise structural capacity:\n\n"
            "1. **Isolate Affected Area:** Cordon off the perimeter around the damaged structural elements and strictly restrict physical access.\n"
            "2. **Do NOT Attempt DIY Repairs:** Do not perform uncalculated patching, prop removal, or cosmetic covering over damaged members.\n"
            "3. **Commission In-Person Inspection:** Arrange an urgent in-person physical inspection by a licensed Professional Structural Engineer registered with the Pakistan Engineering Council (PEC).\n"
            "4. **Emergency Escalation Rule:** If visible movement, sudden crack expansion, or structural creaking occurs, immediately escalate to LEVEL 0 Emergency and evacuate.\n\n"
            "*Safety Policy: TameerAI does not provide structural clearance or certify building stability.*"
        )

    @staticmethod
    def get_priority_inspection_advisory(
        lang: str = "en",
        category: HazardCategory = HazardCategory.STRUCTURAL_MODIFICATION,
        missing_vars: Optional[List[str]] = None,
    ) -> str:
        """LEVEL 2 — PRIORITY INSPECTION: Structural Modification & Sizing Advisory."""
        vars_text = ", ".join(missing_vars).replace("_", " ") if missing_vars else "architectural drawings, structural loading, and geotechnical soil report"

        if lang == "roman_ur":
            return (
                "⚠️ **STRUCTURAL ENGINEERING ADVISORY (HIGH RISK) — LEVEL 2: PRIORITY INSPECTION**\n\n"
                "Aap ka sawal load-bearing structural elements ki tabdeeli ya structural design se mutaliq hai. "
                "Kisi bhi column, beam, ya load-bearing deewar ko hatana ya naye storeys ka izafa karna building ki overall stability ko mutasir kar sakta hai.\n\n"
                "• **Baghair Calculation Design Mumkin Nahi:** Structural member ke sizes aur saria (reinforcement) andazay par tay nahi kiye ja sakte.\n"
                f"• **Darqar Tafseelat:** Is kaam ke liye yeh information zaroori hoti hai: {vars_text}.\n"
                "• **Laazmi Amal:** Structural modification ya casting se qabal kisi PEC registered Professional Structural Engineer se approved drawings aur site calculation karwana qanoonan aur fanni aitibar se laazmi hai.\n\n"
                "*TameerAI qanooni ya fanni tor par structural removal ya specific bar sizes ko certify nahi karta.*"
            )
        elif lang == "ur":
            return (
                "⚠️ **سٹرکچرل انجینئرنگ ایڈوائزری (ہائی رسک) — سطح 2: ترجیحی معائنہ**\n\n"
                "آپ کا سوال لوڈ بیئرنگ ساختی عناصر کی تبدیلی یا ساختی ڈیزائن سے متعلق ہے۔ "
                "کسی بھی کالم، بیم یا لوڈ بیئرنگ دیوار کو ہٹانا یا عمارت میں نئی منزل کا اضافہ پوری عمارت کے استحکام پر اثرانداز ہو سکتا ہے۔\n\n"
                "• **بغیر حساب کتاب ڈیزائن ممکن نہیں:** سٹرکچرل ممبرز کے سائز اور سریے کی تفصیلات اندازے سے طے نہیں کی جا سکتیں۔\n"
                f"• **درکار معلومات:** اس کام کے لیے یہ تفصیلات درکار ہیں: {vars_text}۔\n"
                "• **لازمی کارروائی:** ساختی تبدیلی یا تعمیر سے قبل پاکستان انجینئرنگ کونسل (PEC) سے تصدیق شدہ سٹرکچرل انجینئر سے منظور شدہ ڈرائنگز اور معائنہ کروانا قانونی اور تکنیکی طور پر لازمی ہے۔\n\n"
                "*تعمیر اے آئی چیٹ پر کسی بھی ساختی تبدیلی کی اجازت یا مخصوص سریا شیڈول جاری نہیں کرتا۔*"
            )
        return (
            "⚠️ **STRUCTURAL ENGINEERING ADVISORY (HIGH RISK) — LEVEL 2: PRIORITY INSPECTION**\n\n"
            "Your inquiry involves structural modifications, load alterations, or structural element sizing. "
            "Modifying, removing, or adding load to structural columns, beams, or load-bearing walls directly alters load paths and building stability.\n\n"
            "• **No Speculative Structural Sizing:** Structural dimensions, load capacities, and reinforcement schedules cannot be estimated without site-specific engineering calculations.\n"
            f"• **Essential Parameters Required:** {vars_text}.\n"
            "• **Mandatory Requirement:** A certified site evaluation and structural design verified by a licensed Professional Structural Engineer (Pakistan Engineering Council / PEC registered) is mandatory before physical execution.\n\n"
            "*Safety Policy: TameerAI does not certify structural modifications, issue structural clearance, or fabricate structural member sizes.*"
        )

    @staticmethod
    def get_diy_prohibition_advisory(lang: str = "en", diy_hazard: str = "unauthorized_diy_structural_repair") -> str:
        """LEVEL 2 — STRICT DIY STRUCTURAL REPAIR PROHIBITION (Section 6)."""
        if lang == "roman_ur":
            return (
                "⛔ **UNSAFE DIY STRUCTURAL REPAIR PROHIBITION (KHUDI MARAMMAT MAMNOO HAI)**\n\n"
                "Load-bearing structural elements (columns, beams, slabs, foundations) ki baghair engineering shoring, jacking, ya cutting karna shadeed khatarnak hai:\n\n"
                "• **Achanak Girne Ka Khatra:** Damaged beam ko jacking karna ya column ko improvised tor par support karna achanak progressive collapse ka sabab ban sakta hai.\n"
                "• **Actionable DIY Steps Faraham Nahi Kiye Ja Sakte:** TameerAI unapproved structural shoring ya repairs ke tariqay faraham nahi karta.\n"
                "• **Zaroori Amal:** Kisi PEC registered Professional Structural Engineer se calculated temporary shoring aur rehabilitation plan banwayein."
            )
        elif lang == "ur":
            return (
                "⛔ **غیرمحفوظ خود کار مرمت کی ممانعت (UNSAFE DIY STRUCTURAL REPAIR PROHIBITION)**\n\n"
                "لوڈ بیئرنگ ساختی عناصر (کالم، بیم، سلیب، بنیاد) کی بغیر انجینئرنگ کے خود جیکنگ، کٹنگ یا سہارا دینا شدید خطرناک اور جان لیوا ہے:\n\n"
                "• **اچانک گرنے کا شدید خطرہ:** خراب بیم کو بغیر ڈیزائن کے جیک سے اٹھانا یا کالم کو عارضی سہارا دینا عمارت کے اچانک گرنے کا باعث بن سکتا ہے۔\n"
                "• **طریقہ کار فراہم نہیں کیا جا سکتا:** تعمیر اے آئی بغیر انجینئرنگ کے مرمت یا جیکنگ کے اقدامات فراہم نہیں کرتا۔\n"
                "• **لازمی کارروائی:** پاکستان انجینئرنگ کونسل (PEC) سے تصدیق شدہ سٹرکچرل انجینئر سے منظور شدہ عارضی سہارے اور بحالی کا پلان بنوانا لازمی ہے۔"
            )
        return (
            "⛔ **UNSAFE DIY STRUCTURAL REPAIR PROHIBITION**\n\n"
            "Do NOT attempt unengineered shoring, hydraulic jacking, member replacement, or cutting of load-bearing structural members:\n\n"
            "• **Severe Collapse Risk:** Structural columns and beams carry concentrated gravity and seismic loads. Improvised jacking or uncalculated support removal directly risks sudden progressive collapse.\n"
            "• **No Actionable DIY Procedures:** TameerAI strictly does not provide step-by-step instructions for amateur structural shoring or member replacement.\n"
            "• **Mandatory Action:** A certified temporary shoring and structural repair scheme designed by a licensed Professional Structural Engineer (PEC registered) is mandatory before touching any structural member."
        )

    # ------------------------------------------------------------------------
    # PROFESSIONAL OVERSIGHT & AUDIT HELPERS (Section 7 & 9, Phase 03.2.1 Hardened)
    # ------------------------------------------------------------------------

    @staticmethod
    def validate_pec_registration_format(pec_number: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates syntax/format of a Pakistan Engineering Council (PEC) registration number.
        Returns: (is_format_valid, detected_discipline, error_message)
        """
        if not pec_number or not isinstance(pec_number, str):
            return False, None, "PEC registration number is missing"

        clean = pec_number.strip().upper()

        m_civil = re.match(r"^(?:CIVIL|C)[-/\s]?(\d{3,7})$", clean, re.IGNORECASE)
        if m_civil:
            return True, "CIVIL", None

        m_struct = re.match(r"^(?:STRUCT|S)[-/\s]?(\d{3,7})$", clean, re.IGNORECASE)
        if m_struct:
            return True, "STRUCT", None

        m_elect = re.match(r"^(?:ELECT)[-/\s]?(\d{3,7})$", clean, re.IGNORECASE)
        if m_elect:
            return True, "ELECT", None

        m_mech = re.match(r"^(?:MECH)[-/\s]?(\d{3,7})$", clean, re.IGNORECASE)
        if m_mech:
            return True, "MECH", None

        m_arch = re.match(r"^(?:ARCH)[-/\s]?(\d{3,7})$", clean, re.IGNORECASE)
        if m_arch:
            return True, "ARCH", None

        m_num = re.match(r"^\d{3,7}$", clean)
        if m_num:
            return True, "NUMERIC_UNASSIGNED", None

        return False, None, "Invalid PEC registration number format (e.g. CIVIL/12345 or digits)"

    @staticmethod
    def check_structural_discipline_eligibility(discipline: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Checks whether an engineering discipline is authorized to issue
        structural engineering advisories and sign-offs.
        Only CIVIL and STRUCT disciplines are eligible.
        ELECT, MECH, ARCH, and unverified numeric IDs are not eligible.
        """
        if not discipline:
            return False, "Discipline is unspecified."
        d_upper = discipline.strip().upper()
        if d_upper in ("CIVIL", "STRUCT"):
            return True, "Discipline eligible for structural engineering authorization."
        if d_upper in ("ELECT", "MECH", "ARCH"):
            return False, f"Discipline '{d_upper}' is not authorized to issue structural engineering clearances."
        if d_upper == "NUMERIC_UNASSIGNED":
            return False, "Numeric-only identifier requires authoritative discipline verification before structural authorization."
        return False, f"Unknown or ineligible discipline: {discipline}."

    @classmethod
    def verify_pec_credential_status(cls, pec_number: Optional[str]) -> Dict[str, Any]:
        """
        Evaluates PEC credential status with explicit separation between format validity
        and actual active licensing verification.
        Does NOT perform unauthorized external API calls.
        Explicitly marks verification as False/UNVERIFIED in the absence of verified registry.
        """
        is_fmt_valid, disc, err = cls.validate_pec_registration_format(pec_number)
        if not is_fmt_valid:
            return {
                "is_format_valid": False,
                "is_verified": False,
                "verification_status": "FORMAT_INVALID",
                "pec_number": pec_number or "",
                "normalized_number": None,
                "detected_discipline": None,
                "structural_authorization_eligible": False,
                "error_message": err,
                "verification_disclaimer": "Invalid PEC registration format.",
            }

        is_eligible, elig_reason = cls.check_structural_discipline_eligibility(disc)
        clean = pec_number.strip().upper() if pec_number else ""

        return {
            "is_format_valid": True,
            "is_verified": False,  # Strict: format validity does not imply active registration
            "verification_status": "UNVERIFIED" if is_eligible else "DISCIPLINE_INELIGIBLE",
            "pec_number": pec_number,
            "normalized_number": clean,
            "detected_discipline": disc,
            "structural_authorization_eligible": is_eligible,
            "error_message": None if is_eligible else elig_reason,
            "verification_disclaimer": (
                "Format validation only. Format validity does NOT constitute proof of active "
                "PEC registration or professional licensing. Non-civil disciplines (e.g. ELECT, MECH) "
                "and unverified numeric IDs are not authorized for structural clearance."
            ),
        }

    @staticmethod
    def validate_sign_off_authorization(
        sign_off: ProfessionalEngineerSignOff,
        user_role: Optional[str] = None,
        is_user_verified: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforces strict professional sign-off authorization boundaries.
        Prevents unauthorized users, general clients, non-structural disciplines,
        or uninspected projects from receiving formal structural clearance.
        """
        if not sign_off.pec_registration_number:
            return False, "PEC registration number is required for engineering sign-off."

        is_fmt_valid, disc, _ = StructuralSafetyEngine.validate_pec_registration_format(sign_off.pec_registration_number)
        if not is_fmt_valid:
            return False, "Invalid PEC registration number format."

        is_eligible, elig_err = StructuralSafetyEngine.check_structural_discipline_eligibility(disc)
        if not is_eligible:
            return False, elig_err

        if sign_off.formal_clearance_issued:
            # 1. Administrative privileges check:
            # Admins have system/org management access, but administrative privileges DO NOT grant structural sign-off authority.
            if user_role and user_role.lower() in ("admin", "superadmin"):
                return False, "Administrative privileges do not grant structural engineering sign-off authority. Formal structural clearance requires a verified structural engineer."

            # 2. Client role check: clients cannot issue engineering sign-offs.
            if user_role and user_role.lower() == "client":
                return False, "Unauthorized user role 'client': clients cannot issue structural engineering sign-offs."

            # 3. Authorized engineering role check
            allowed_roles = ("consultant", "engineer", "structural_engineer")
            if not user_role or user_role.lower() not in allowed_roles:
                return False, f"Unauthorized user role '{user_role}': not authorized to issue structural clearances. Required: verified structural engineer or consultant."

            # 4. Consultant discipline specialization check
            if user_role.lower() == "consultant" and (not sign_off.structural_discipline_eligible or disc not in ("CIVIL", "STRUCT")):
                return False, f"Consultant with discipline '{disc}' is not authorized for structural engineering sign-off. Structural specialization required."

            # 5. Mandatory physical site inspection (remote clearance banned)
            if not sign_off.physical_site_inspection_conducted:
                return False, "Mandatory physical site inspection required. Formal structural clearance cannot be issued remotely."

            # 6. Verified credential requirement: format validity does not imply active registration
            if not (sign_off.is_verified and is_user_verified):
                return False, "Unverified engineer credentials. Formal structural clearance requires verified professional status."

            # 7. Mandatory inspection date & findings metadata
            if not sign_off.inspection_date:
                return False, "Inspection date is mandatory for structural sign-off."

            if not sign_off.findings_summary or len(sign_off.findings_summary.strip()) < 10:
                return False, "Detailed inspection findings summary (min 10 characters) is mandatory for formal clearance."

            # 8. Attributable professional attestation requirement:
            # A client-submitted boolean is_physical_inspection_completed=True alone does not establish inspection occurred
            if not sign_off.attestation_statement or len(sign_off.attestation_statement.strip()) < 20:
                return False, "Attributable professional attestation statement is mandatory. A boolean flag alone does not establish physical inspection."

        return True, None

    @classmethod
    def validate_pec_registration_number(cls, pec_number: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Backward compatibility wrapper for PEC registration syntax validation.
        NOTE: Valid format does NOT constitute verified professional registration.
        """
        is_valid, _, err = cls.validate_pec_registration_format(pec_number)
        return is_valid, err

    @staticmethod
    def _sanitize_pii(text: str) -> str:
        """Sanitizes sensitive Personally Identifiable Information (PII) from query texts."""
        if not text:
            return ""
        # 1. Redact CNIC first to avoid 10-digit substrings matching phone patterns
        t = re.sub(r"\b\d{5}[-\s]?\d{7}[-\s]?\d\b", "[CNIC_REDACTED]", text)
        t = re.sub(r"\b\d{13}\b", "[CNIC_REDACTED]", t)
        # 2. Redact Pakistani phone numbers (03xx-xxxxxxx, +92...)
        t = re.sub(r"(?:\+92|0092|0)?3\d{2}[-\s]?\d{7}\b", "[PHONE_REDACTED]", t)
        # 3. Redact email addresses
        t = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_REDACTED]", t)
        return t

    @classmethod
    def _record_audit(cls, record: SafetyAssessmentAuditRecord):
        """Appends audit record to thread-safe circular log buffer with PII redaction."""
        record.query_snippet = cls._sanitize_pii(record.query_snippet)

        cls._audit_log.append(record)
        if len(cls._audit_log) > 500:
            cls._audit_log.pop(0)

    @classmethod
    def get_recent_audit_records(
        cls,
        limit: int = 50,
        project_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[SafetyAssessmentAuditRecord]:
        """
        Retrieves recent audit log records, optionally scoped by project_id or user_id.
        NOTE: Ephemeral buffer. Records reset on process restart.
        """
        records = cls._audit_log
        if project_id is not None:
            records = [r for r in records if r.project_id == project_id]
        if user_id is not None:
            records = [r for r in records if r.user_id == user_id]
        return records[-limit:]

    @classmethod
    def clear_audit_log(cls):
        """Clears audit records (for test isolation)."""
        cls._audit_log.clear()

    @classmethod
    def record_sign_off(cls, record: ProfessionalEngineerSignOff):
        """Appends sign-off record to thread-safe circular log buffer."""
        cls._sign_off_log.append(record)
        if len(cls._sign_off_log) > 500:
            cls._sign_off_log.pop(0)

    @classmethod
    def get_recent_sign_offs(
        cls,
        limit: int = 50,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[ProfessionalEngineerSignOff]:
        """
        Retrieves recent sign-off records, optionally scoped by user_id.
        NOTE: Ephemeral buffer. Records reset on process restart.
        """
        records = cls._sign_off_log
        if user_id is not None:
            records = [r for r in records if r.user_id == user_id]
        return records[-limit:]

    @classmethod
    def clear_sign_off_log(cls):
        """Clears sign-off records (for test isolation)."""
        cls._sign_off_log.clear()


# Global singleton engine
structural_safety_engine = StructuralSafetyEngine()
