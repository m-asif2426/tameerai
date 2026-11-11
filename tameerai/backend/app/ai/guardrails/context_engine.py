"""
TameerAI - Construction Context Engine (Phase 03F)
Task B of the Construction Intelligence & Response Quality Foundation.
Analyzes extracted entities, detected intent, and domain category to determine:
- Available technical variables vs. missing critical variables.
- Whether a question is theoretical or an active physical project.
- Whether safety-critical structural decisions are involved.
- The optimal engineering response strategy (Direct, Explanatory, Calculation, Clarification, High-Risk, Evidence-Dependent).
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.guardrails.entities import EntityCategory, ExtractedEntity
from app.ai.guardrails.intent import ConstructionIntent
from app.ai.guardrails.normalizer import NormalizedQuery
from app.ai.guardrails.structural_safety import (
    HazardCategory,
    RiskLevel,
    StructuralRiskAssessment,
    StructuralSafetyEngine,
)


class ResponseStrategy(str, Enum):
    DIRECT_ANSWER = "direct_answer"
    CONCEPT_EXPLANATION = "concept_explanation"
    CALCULATION_STEPWISE = "calculation_stepwise"
    CLARIFICATION_REQUIRED = "clarification_required"
    HIGH_RISK_ADVISORY = "high_risk_advisory"
    EVIDENCE_DEPENDENT = "evidence_dependent"
    OFF_TOPIC_REDIRECTION = "off_topic_redirection"


class TechnicalVariable(BaseModel):
    """A known engineering variable provided in the query or conversation history."""
    name: str
    value: str
    unit: Optional[str] = None
    source: str = "user_provided"


class MissingVariable(BaseModel):
    """A technical parameter required to formulate a definitive engineering solution."""
    name: str
    importance: str = "critical"  # critical or recommended
    rationale: str
    suggested_prompt: str


class ConstructionContext(BaseModel):
    """Rich conversational and engineering context of a construction inquiry."""
    topic: str
    intent: ConstructionIntent
    entities: List[ExtractedEntity] = Field(default_factory=list)
    available_variables: List[TechnicalVariable] = Field(default_factory=list)
    missing_variables: List[MissingVariable] = Field(default_factory=list)
    is_calculation_required: bool = False
    is_safety_critical: bool = False
    requires_supporting_evidence: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    recommended_strategy: ResponseStrategy = ResponseStrategy.DIRECT_ANSWER
    clarification_question: Optional[str] = None
    safety_assessment: Optional[StructuralRiskAssessment] = None


class ConstructionContextEngine:
    """
    Evaluates engineering requirements, safety boundaries, and information completeness.
    """

    @classmethod
    def analyze_context(
        cls,
        normalized: NormalizedQuery,
        intent: ConstructionIntent,
        entities: List[ExtractedEntity],
        language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> ConstructionContext:
        """
        Builds a comprehensive ConstructionContext and determines the appropriate response strategy.
        Supports multi-turn context tracking, missing variable identification, and context drift prevention.
        """
        import re
        text = normalized.normalized_query
        lower_text = text.lower()
        
        # 1. Identify primary civil topic from current query
        topic = "General Civil Engineering"
        has_foundation = any(e.canonical_value in ("foundation", "raft_foundation", "footing", "soil_bearing_capacity") for e in entities) or any(w in lower_text for w in ["foundation", "bunyaad", "bunyad", "footing", "raft", "بنیاد"])
        has_concrete = any(e.canonical_value in ("concrete", "cement", "ordinary_portland_cement", "mix_ratio") for e in entities) or any(w in lower_text for w in ["concrete", "concreet", "cement", "lanter", "کنکریٹ", "سیمنٹ", "لینٹر"])
        has_steel = any(e.canonical_value in ("steel_rebar", "rebar", "main_reinforcement") for e in entities) or any(w in lower_text for w in ["steel", "rebar", "saria", "sariya", "سریہ"])
        has_compliance = any(e.category == EntityCategory.LOCATION_JURISDICTION for e in entities) or any(w in lower_text for w in ["bylaw", "byelaw", "setback", "cda", "lda", "sbca", "قانون", "ضوابط"])
        has_defect = any(e.canonical_value in ("crack", "cracks", "seepage", "efflorescence") for e in entities) or any(w in lower_text for w in ["crack", "darar", "seepage", "shora", "دراڑ", "سیپج"])
        has_finishing = any(w in lower_text for w in ["plaster", "paint", "tiles", "marble", "granite", "putty", "پلستر"])

        has_explicit_component = has_foundation or has_concrete or has_steel or has_compliance or has_defect or has_finishing

        # Context Drift Prevention: Inherit from history ONLY if current turn lacks explicit component
        if not has_explicit_component and conversation_history and len(conversation_history) > 0:
            for past_turn in reversed(conversation_history):
                past_content = past_turn.get("content", "").lower()
                if any(w in past_content for w in ["foundation", "bunyaad", "footing", "raft", "بنیاد"]):
                    has_foundation = True
                    break
                elif any(w in past_content for w in ["concrete", "cement", "lanter", "کنکریٹ", "سیمنٹ"]):
                    has_concrete = True
                    break
                elif any(w in past_content for w in ["steel", "rebar", "saria", "سریہ"]):
                    has_steel = True
                    break
                elif any(w in past_content for w in ["plaster", "paint", "tiles", "پلستر"]):
                    has_finishing = True
                    break

        if has_finishing:
            topic = "Finishing & Architectural Materials"
        elif has_foundation:
            topic = "Foundation & Geotechnical Engineering"
        elif has_steel and has_concrete:
            topic = "Reinforced Concrete & Structural Elements"
        elif has_concrete:
            topic = "Concrete Technology & Mix Design"
        elif has_steel:
            topic = "Reinforcement & Structural Steel"
        elif has_compliance:
            topic = "Building Codes & Regulatory Compliance"
        elif has_defect:
            topic = "Building Defects & Maintenance"

        # 2. Extract available technical variables
        avail_vars: List[TechnicalVariable] = []
        for ent in entities:
            if ent.category == EntityCategory.MEASUREMENT:
                avail_vars.append(
                    TechnicalVariable(name=ent.canonical_value.split(":")[0], value=ent.value, unit=ent.unit)
                )

        # 3. Deterministic Structural Risk Evaluation (Phase 03G Stage B2)
        safety_assessment = StructuralSafetyEngine.evaluate_risk(
            query=normalized.raw_query,
            normalized_query=normalized.normalized_query,
            intent=intent,
            entities=entities,
            language=language,
        )
        risk_level = safety_assessment.risk_level
        is_safety_critical = safety_assessment.is_critical or safety_assessment.is_high_risk

        if safety_assessment.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            if safety_assessment.hazard_category == HazardCategory.FOUNDATION_GEOTECHNICAL:
                topic = "Foundation & Geotechnical Engineering"
            elif safety_assessment.hazard_category in (HazardCategory.RCC_STRUCTURAL, HazardCategory.STRUCTURAL_MODIFICATION):
                topic = "Reinforced Concrete & Structural Elements"

        # 4. Check missing variables for specialized questions
        missing_vars: List[MissingVariable] = []
        clarification_q: Optional[str] = None

        has_floors = (
            any(re.search(r"\b(?:\d+|single|double|triple|ground|g\+1|g\+2)\s*(?:floor|storey|manzil|story)\b", lower_text) for _ in [1])
            or any("storey" in e.canonical_value for e in entities)
            or any(w in lower_text for w in ["منزل", "منزلیں"])
        )
        has_soil = (
            any(e.category == EntityCategory.SOIL_CONDITION for e in entities)
            or any(w in lower_text for w in ["soil", "sbc", "bearing capacity", "mitti", "مٹی", "برداشت کی صلاحیت"])
        )
        has_load = (
            any(e.category == EntityCategory.BUILDING_LOAD for e in entities)
            or any(w in lower_text for w in ["load", "dead load", "live load", "بوجھ"])
        )
        has_dimensions = (
            any(e.canonical_value.startswith(("length:", "width:", "thickness:", "area:", "volume:")) for e in entities)
            or any(w in lower_text for w in ["dimension", "length", "width", "thickness", "cft", "cum", "لمبائی", "چوڑائی", "موٹائی", "پیمائش"])
        )

        # Case A: Foundation design or depth inquiry lacking critical variables
        if has_foundation and (intent in (ConstructionIntent.PLANNING, ConstructionIntent.CALCULATION, ConstructionIntent.QUANTITY_ESTIMATE) or any(w in lower_text for w in ["design", "depth", "gehri", "kitni", "size", "گہرائی", "ڈیزائن"])):
            if not has_floors:
                missing_vars.append(
                    MissingVariable(
                        name="building_floors",
                        importance="critical",
                        rationale="Number of storeys or floors directly determines column loads on foundation.",
                        suggested_prompt="How many storeys or floors are proposed?",
                    )
                )
            if not has_soil:
                missing_vars.append(
                    MissingVariable(
                        name="soil_bearing_capacity",
                        importance="critical",
                        rationale="Foundation depth and footing size require geotechnical soil bearing capacity.",
                        suggested_prompt="What is the soil bearing capacity or soil condition at the site?",
                    )
                )
            if not has_load:
                missing_vars.append(
                    MissingVariable(
                        name="structural_load",
                        importance="critical",
                        rationale="Total dead and live loads dictate whether isolated, strip, or raft foundation is needed.",
                        suggested_prompt="What are the approximate structural loads or structural system?",
                    )
                )

        # Case B: Concrete calculation lacking dimensions or mix ratio
        if has_concrete and (intent in (ConstructionIntent.CALCULATION, ConstructionIntent.QUANTITY_ESTIMATE) or any(w in lower_text for w in ["calculation", "calculate", "hisab", "quantity", "kitna", "volume", "malum", "حساب", "مقدار"])):
            if not has_dimensions:
                missing_vars.append(
                    MissingVariable(
                        name="dimensions",
                        importance="critical",
                        rationale="Concrete volume calculation requires length, width, and thickness/depth.",
                        suggested_prompt="What are the dimensions (length, width, thickness) of the concrete element?",
                    )
                )

        # Case C: Steel rebar calculation lacking diameter or length
        if has_steel and (intent in (ConstructionIntent.CALCULATION, ConstructionIntent.QUANTITY_ESTIMATE) or any(w in lower_text for w in ["weight", "wazan", "calculate", "hisab", "وزن"])):
            has_rebar_diameter = any(e.canonical_value.startswith("diameter:") for e in entities) or any(w in lower_text for w in ["mm", "sooter", "gauge", "#3", "#4", "#5", "#6", "#8", "12mm", "10mm", "16mm", "bar size", "قطر", "سوتر"])
            if not has_rebar_diameter:
                missing_vars.append(
                    MissingVariable(
                        name="rebar_diameter",
                        importance="critical",
                        rationale="Rebar weight requires bar diameter (D^2/162 formula).",
                        suggested_prompt="What is the diameter or size of the steel rebar?",
                    )
                )

        # Integrate any missing structural engineering variables from the safety assessment
        if safety_assessment.missing_engineering_variables:
            for m_var in safety_assessment.missing_engineering_variables:
                if not any(mv.name == m_var for mv in missing_vars):
                    missing_vars.append(
                        MissingVariable(
                            name=m_var,
                            importance="critical" if is_safety_critical else "recommended",
                            rationale=f"Structural engineering safety parameter: {m_var.replace('_', ' ')}.",
                            suggested_prompt=f"Please specify {m_var.replace('_', ' ')}.",
                        )
                    )

        # 5. Determine Response Strategy
        strategy = ResponseStrategy.DIRECT_ANSWER

        if intent == ConstructionIntent.OFF_TOPIC:
            strategy = ResponseStrategy.OFF_TOPIC_REDIRECTION
        elif is_safety_critical or risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.HIGH_STRUCTURAL_SAFETY):
            strategy = ResponseStrategy.HIGH_RISK_ADVISORY
        elif intent == ConstructionIntent.COMPLIANCE:
            strategy = ResponseStrategy.EVIDENCE_DEPENDENT
        elif intent in (ConstructionIntent.CALCULATION, ConstructionIntent.QUANTITY_ESTIMATE):
            strategy = ResponseStrategy.CALCULATION_STEPWISE
        elif intent in (ConstructionIntent.EXPLANATION, ConstructionIntent.COMPARISON, ConstructionIntent.PROCEDURE):
            strategy = ResponseStrategy.CONCEPT_EXPLANATION
        elif intent == ConstructionIntent.AMBIGUOUS:
            strategy = ResponseStrategy.CLARIFICATION_REQUIRED
            if language == "roman_ur":
                clarification_q = "Aap ka sawal mukhtasir hai. Kiya aap building construction ke hawalay se mazeed tafseelat bata sakte hain?"
            elif language == "ur":
                clarification_q = "آپ کا سوال مختصر ہے۔ کیا آپ عمارت کی تعمیر کے حوالے سے مزید تفصیلات فراہم کر سکتے ہیں؟"
            else:
                clarification_q = "Could you please provide more context or specific details regarding your construction query?"

        # If missing critical variables for specific applied engineering queries, route to CLARIFICATION_REQUIRED
        # NOTE: HIGH_RISK_ADVISORY must NOT be overridden by CLARIFICATION_REQUIRED
        if missing_vars and (has_foundation or has_concrete or has_steel) and strategy not in (ResponseStrategy.HIGH_RISK_ADVISORY, ResponseStrategy.OFF_TOPIC_REDIRECTION):
            strategy = ResponseStrategy.CLARIFICATION_REQUIRED

        return ConstructionContext(
            topic=topic,
            intent=intent,
            entities=entities,
            available_variables=avail_vars,
            missing_variables=missing_vars,
            is_calculation_required=(intent in (ConstructionIntent.CALCULATION, ConstructionIntent.QUANTITY_ESTIMATE)),
            is_safety_critical=is_safety_critical,
            requires_supporting_evidence=(intent == ConstructionIntent.COMPLIANCE),
            risk_level=risk_level,
            recommended_strategy=strategy,
            clarification_question=clarification_q,
            safety_assessment=safety_assessment,
        )
