"""
TameerAI - Construction Intent Detection Engine (Phase 03F)
Layer 2 of the Intelligent Construction Intent Architecture.
Identifies the communicative goal of the user query across 9 core engineering intents,
distinguishing technical explanations, quantity estimates, mathematical calculations,
troubleshooting, and compliance requirements.
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.ai.guardrails.normalizer import NormalizedQuery


class ConstructionIntent(str, Enum):
    """Categorization of what the user is asking TameerAI to do."""
    EXPLANATION = "explanation"
    CALCULATION = "calculation"
    MATERIAL_RECOMMENDATION = "material_recommendation"
    QUANTITY_ESTIMATE = "quantity_estimate"
    PROCEDURE = "procedure"
    TROUBLESHOOTING = "troubleshooting"
    COMPARISON = "comparison"
    COMPLIANCE = "compliance"
    PLANNING = "planning"
    MATERIAL_RATE_INQUIRY = "material_rate_inquiry"
    GENERAL_INQUIRY = "general_inquiry"
    AMBIGUOUS = "ambiguous"
    OFF_TOPIC = "off_topic"


class IntentDetectionResult(BaseModel):
    """Result of Layer 2 intent classification."""
    primary_intent: ConstructionIntent
    confidence: float = Field(..., ge=0.0, le=1.0)
    secondary_intents: List[ConstructionIntent] = Field(default_factory=list)
    matched_intent_signals: List[str] = Field(default_factory=list)
    rationale: str


# Regex patterns and signals for each construction intent
INTENT_SIGNALS: Dict[ConstructionIntent, List[re.Pattern]] = {
    ConstructionIntent.COMPARISON: [
        re.compile(r"\b(?:difference\s+between|vs|versus|compare|comparison|recommended\s+over)\b", re.IGNORECASE),
        re.compile(r"\b(?:faraq|farq|kya\s+farq\s+hai|behtar\s+hai\s+ya|konsa\s+zyada\s+mazboot)\b", re.IGNORECASE),
    ],
    ConstructionIntent.TROUBLESHOOTING: [
        re.compile(r"\b(?:crack|cracks|seepage|leakage|honeycombing|settlement|defect|failure|damage|repair|bleeding|segregation)\b", re.IGNORECASE),
        re.compile(r"\b(?:darar|seep|shora|efflorescence|deemak|kharab|masla|problem|kyun\s+aati\s+hai|theek\s+karein)\b", re.IGNORECASE),
        re.compile(r"\b(?:structural\s+crack|plaster\s+falling|water\s+leakage|settlement\s+damage)\b", re.IGNORECASE),
    ],
    ConstructionIntent.CALCULATION: [
        re.compile(r"\b(?:calculate|calculation|formula|derive|solve|compute|d\^2/162|d2/162|determine|thickness\s+of)\b", re.IGNORECASE),
        re.compile(r"\b(?:calculate\s+karain|calculate\s+karein|hisab|formula\s+kya\s+hai|weight\s+kaise\s+nikalein)\b", re.IGNORECASE),
        re.compile(r"\b(?:how\s+to\s+calculate|how\s+is\s+.*?\s+calculated|deflection\s+calculation|area\s+required)\b", re.IGNORECASE),
        re.compile(r"(?:حساب|فارمولا|کیلکولیٹ)", re.IGNORECASE),
    ],
    ConstructionIntent.QUANTITY_ESTIMATE: [
        re.compile(r"\b(?:how\s+many|quantity|estimate|estimation|bags\s+required|total\s+number\s+of\s+bricks|labor\s+rate|rate\s+per)\b", re.IGNORECASE),
        re.compile(r"\b(?:kitna|kitni|kitne|bags\s+chahiye|kitna\s+cement|kitna\s+saria|wastage|boq|rate\s+per\s+square\s+foot)\b", re.IGNORECASE),
        re.compile(r"\b(?:1000\s*(?:sqft|sft)|5\s*marla|10\s*marla|1\s*kanal|covered\s+area\s+estimate)\b", re.IGNORECASE),
        re.compile(r"(?:کتنی|کتنا|کتنے|مقدار|حساب\s+کتاب)", re.IGNORECASE),
    ],
    ConstructionIntent.MATERIAL_RECOMMENDATION: [
        re.compile(r"\b(?:which\s+is\s+better|recommend|best\s+material|grade\s+60|grade\s+40|opc|src|ideal\s+size|advantages\s+of)\b", re.IGNORECASE),
        re.compile(r"\b(?:kaunsa\s+achha|kaunsa\s+behtar|konsa\s+cement|konsa\s+saria|recommendation)\b", re.IGNORECASE),
        re.compile(r"\b(?:which\s+cement|which\s+steel|which\s+pipe|which\s+brick)\b", re.IGNORECASE),
    ],
    ConstructionIntent.PROCEDURE: [
        re.compile(r"\b(?:how\s+to\s+perform|how\s+to\s+inspect|procedure|steps|method|execution|sequence|casting|curing|slump\s+test)\b", re.IGNORECASE),
        re.compile(r"\b(?:kaise\s+karte|kaise\s+dhalai|kaise\s+karna|tareeqa|tarika|step\s+by\s+step|checklist)\b", re.IGNORECASE),
        re.compile(r"\b(?:curing\s+procedure|compaction\s+method|soil\s+testing\s+procedure|shuttering\s+removal)\b", re.IGNORECASE),
        re.compile(r"(?:طریقہ|کیسے\s+کریں|کیسے\s+بڑھائیں|مراحل|کیسے\s+ہوتی\s+ہے)", re.IGNORECASE),
    ],
    ConstructionIntent.COMPLIANCE: [
        re.compile(r"\b(?:bylaw|bylaws|byelaws|regulation|code|permit|noc|lda|cda|sbca|setback|height\s+limit|far)\b", re.IGNORECASE),
        re.compile(r"\b(?:rule|rules|qanoon|approval|completion\s+certificate|building\s+code\s+of\s+pakistan|bcp)\b", re.IGNORECASE),
        re.compile(r"(?:قانون|بائی\s*لاز|ضوابط)", re.IGNORECASE),
    ],
    ConstructionIntent.PLANNING: [
        re.compile(r"\b(?:schedule|planning|gantt|duration|timeline|milestone|project\s+management|running\s+bill|critical\s+path|cpm|lead\s+time|dpr|delays|weather\s+delays)\b", re.IGNORECASE),
        re.compile(r"\b(?:kitna\s+time|kitne\s+din|schedule\s+kaise|thekedar\s+agreement|contract|fidic|daily\s+progress|approval\s+workflow)\b", re.IGNORECASE),
    ],
    ConstructionIntent.MATERIAL_RATE_INQUIRY: [
        re.compile(r"\b(?:rate|rates|price|prices|cost|qeemat|bhao|bhav|today['\s]*s\s+rate|latest\s+rate|current\s+rate|aaj\s+ka\s+rate|kitne\s+ka|kitnay\s+ka|kitne\s+ki|kitnay\s+ki)\b.*?\b(?:cement|saria|sariya|steel|rebar|brick|bricks|eent|eentein|eenton|sand|ret|bajri|crush|block|blocks|tile|tiles)\b", re.IGNORECASE),
        re.compile(r"\b(?:cement|saria|sariya|steel|rebar|brick|bricks|eent|eentein|eenton|sand|ret|bajri|crush|block|blocks|tile|tiles)\b.*?\b(?:rate|rates|price|prices|cost|qeemat|bhao|bhav|today['\s]*s\s+rate|latest\s+rate|current\s+rate|aaj\s+ka\s+rate|kitne\s+ka|kitnay\s+ka|kitne\s+ki|kitnay\s+ki|per\s+bag|per\s+ton|per\s+kg|per\s+cft|per\s+1000)\b", re.IGNORECASE),
        re.compile(r"(?:سیمنٹ|سریا|سریہ|سریے|اینٹ|اینٹیں|اینٹوں|ریت|بجری|کرش|بلاک|ٹائل).*?(?:ریٹ|قیمت|بھاؤ|نرخ|کتنے\s+کا|کتنے\s+کی)", re.IGNORECASE),
        re.compile(r"(?:ریٹ|قیمت|بھاؤ|نرخ).*?(?:سیمنٹ|سریا|سریہ|سریے|اینٹ|اینٹیں|اینٹوں|ریت|بجری|کرش|بلاک|ٹائل)", re.IGNORECASE),
    ],
    ConstructionIntent.EXPLANATION: [
        re.compile(r"\b(?:why|what\s+is|explain|explanation|concept|purpose|reason|meaning|define|effect\s+of|factor|dry\s+volume)\b", re.IGNORECASE),
        re.compile(r"\b(?:kyun|kiun|kya\s+hota\s+hai|kya\s+matlab|wajah|batao|samjhao|kitni\s+zaroori)\b", re.IGNORECASE),
        re.compile(r"(?:کیا\s+ہوتا\s+ہے|کیا\s+ہے|وضاحت|وجہ|بتائیں|سمجھائیں|کیا\s+ہوتی\s+ہے)", re.IGNORECASE),
    ],
}


class ConstructionIntentDetector:
    """
    Deterministic rule-and-heuristic engine for construction intent classification.
    Evaluates normalized tokens and query structure to determine intent with confidence score.
    """

    @classmethod
    def detect_intent(cls, normalized: NormalizedQuery) -> IntentDetectionResult:
        """
        Classifies the primary and secondary construction intent of the query.
        """
        text = normalized.normalized_query
        raw = normalized.raw_query

        # Score all candidate intents based on signal pattern hits
        scores: Dict[ConstructionIntent, Tuple[float, List[str]]] = {}

        for intent, patterns in INTENT_SIGNALS.items():
            matched_signals = []
            score = 0.0
            for pat in patterns:
                matches = pat.findall(text)
                if matches:
                    score += len(matches) * 2.0
                    matched_signals.extend(matches)
            if score > 0:
                scores[intent] = (score, matched_signals)

        # 1. Comparison Dominance
        if re.search(r"\b(?:difference\s+between|vs|versus|compare|comparison|recommended\s+over|faraq|farq|behtar\s+hai\s+ya)\b", text):
            c_score, sigs = scores.get(ConstructionIntent.COMPARISON, (0.0, []))
            scores[ConstructionIntent.COMPARISON] = (c_score + 6.0, sigs + ["comparison_marker"])

        # 2. Defect / Troubleshooting Dominance
        if re.search(r"\b(?:crack|cracks|seepage|leakage|honeycombing|settlement|darar|seep|shora|efflorescence|bleeding|segregation|defect|damage)\b", text):
            t_score, sigs = scores.get(ConstructionIntent.TROUBLESHOOTING, (0.0, []))
            scores[ConstructionIntent.TROUBLESHOOTING] = (t_score + 5.0, sigs + ["defect_marker"])

        # 3. Calculation Specificity
        if re.search(r"\b(?:calculate|how\s+is\s+.*?calculated|formula|derive|d\^2/162|weight\s+kaise\s+nikalein)\b", text):
            c_score, sigs = scores.get(ConstructionIntent.CALCULATION, (0.0, []))
            scores[ConstructionIntent.CALCULATION] = (c_score + 5.0, sigs + ["calculation_marker"])

        # 4. Quantity Estimate Specificity
        if re.search(r"\b(?:bags\s+cement|total\s+number\s+of\s+bricks|steel\s+wastage|sariya\s+kitna\s+ton|covered\s+area\s+estimate|tile\s+quantity)\b", text):
            q_score, sigs = scores.get(ConstructionIntent.QUANTITY_ESTIMATE, (0.0, []))
            scores[ConstructionIntent.QUANTITY_ESTIMATE] = (q_score + 5.5, sigs + ["quantity_estimate_marker"])

        # 4.5 Material Rate Inquiry Specificity
        if not re.search(r"\blabor\s+rate\b", text, re.IGNORECASE):
            is_mat_rate = (
                re.search(r"\b(?:rate|rates|price|prices|qeemat|cost|bhao|bhav|today['\s]*s\s+rate|latest\s+rate|current\s+rate|aaj\s+ka\s+rate|kitne\s+ka|kitnay\s+ka|kitne\s+ki|kitnay\s+ki)\b.*?\b(?:cement|saria|sariya|steel|rebar|brick|bricks|eent|eentein|eenton|sand|ret|bajri|crush|block|blocks|tile|tiles)\b", text, re.IGNORECASE) or
                re.search(r"\b(?:cement|saria|sariya|steel|rebar|brick|bricks|eent|eentein|eenton|sand|ret|bajri|crush|block|blocks|tile|tiles)\b.*?\b(?:rate|rates|price|prices|cost|qeemat|bhao|bhav|today['\s]*s\s+rate|latest\s+rate|current\s+rate|aaj\s+ka\s+rate|kitne\s+ka|kitnay\s+ka|kitne\s+ki|kitnay\s+ki|per\s+bag|per\s+ton|per\s+kg|per\s+cft|per\s+1000)\b", text, re.IGNORECASE) or
                re.search(r"(?:سیمنٹ|سریا|سریہ|سریے|اینٹ|اینٹیں|اینٹوں|ریت|بجری|کرش|بلاک|ٹائل).*?(?:ریٹ|قیمت|بھاؤ|نرخ|کتنے\s+کا|کتنے\s+کی)", text, re.IGNORECASE) or
                re.search(r"(?:ریٹ|قیمت|بھاؤ|نرخ).*?(?:سیمنٹ|سریا|سریہ|سریے|اینٹ|اینٹیں|اینٹوں|ریت|بجری|کرش|بلاک|ٹائل)", text, re.IGNORECASE)
            )
            if is_mat_rate:
                mr_score, sigs = scores.get(ConstructionIntent.MATERIAL_RATE_INQUIRY, (0.0, []))
                scores[ConstructionIntent.MATERIAL_RATE_INQUIRY] = (mr_score + 8.0, sigs + ["material_rate_marker"])

        # 5. Planning Specificity
        if re.search(r"\b(?:schedule|critical\s+path|gantt|procurement|lead\s+time|dpr|daily\s+progress|thekedar\s+agreement|contract|fidic)\b", text):
            p_score, sigs = scores.get(ConstructionIntent.PLANNING, (0.0, []))
            scores[ConstructionIntent.PLANNING] = (p_score + 5.0, sigs + ["planning_marker"])

        # 6. Procedure Specificity
        if re.search(r"\b(?:how\s+to\s+perform|how\s+to\s+inspect|procedure|checklist|sample\s+lene\s+ka\s+tareeqa|dori\s+aur\s+level|removal\s+times|shuttering\s+kholni)\b", text):
            pr_score, sigs = scores.get(ConstructionIntent.PROCEDURE, (0.0, []))
            scores[ConstructionIntent.PROCEDURE] = (pr_score + 5.0, sigs + ["procedure_marker"])

        # 7. Material Recommendation Specificity
        if re.search(r"\b(?:which\s+cement|which\s+is\s+better|ideal\s+size|advantages\s+of|chemicals\s+for|mortar\s+mix\s+ratio)\b", text) and ConstructionIntent.COMPARISON not in scores:
            mr_score, sigs = scores.get(ConstructionIntent.MATERIAL_RECOMMENDATION, (0.0, []))
            scores[ConstructionIntent.MATERIAL_RECOMMENDATION] = (mr_score + 4.0, sigs + ["material_recommendation_marker"])

        # 8. Explanation Specificity
        if re.search(r"\b(?:why|kyun|kiun|depend|munhasir|purpose\s+of|shelf\s+life|compressive\s+strength\s+kitna|spacing\s+.*?\s+kitni|bunyaad\s+kitni\s+gehri|depth\s+kitni)\b", text):
            e_score, sigs = scores.get(ConstructionIntent.EXPLANATION, (0.0, []))
            scores[ConstructionIntent.EXPLANATION] = (e_score + 4.5, sigs + ["explanation_marker"])

        if not scores:
            if len(normalized.tokens) <= 3:
                return IntentDetectionResult(
                    primary_intent=ConstructionIntent.AMBIGUOUS,
                    confidence=0.50,
                    rationale="Short query lacking actionable construction intent markers.",
                )
            return IntentDetectionResult(
                primary_intent=ConstructionIntent.GENERAL_INQUIRY,
                confidence=0.65,
                rationale="General civil engineering context without a specific specialized intent verb.",
            )

        # Sort intents by score descending
        sorted_intents = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
        top_intent, (top_score, top_signals) = sorted_intents[0]

        conf = min(0.98, max(0.65, 0.55 + (top_score * 0.10)))
        secondary = [intent for intent, _ in sorted_intents[1:3]]

        return IntentDetectionResult(
            primary_intent=top_intent,
            confidence=conf,
            secondary_intents=secondary,
            matched_intent_signals=list(set(top_signals)),
            rationale=f"Classified as {top_intent.value} based on signals: {top_signals[:3]}.",
        )
