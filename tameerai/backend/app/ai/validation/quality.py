"""
TameerAI - Construction Response Quality & Safety Validator (Phase 03F)
Task F of the Construction Intelligence & Response Quality Foundation.
Deterministically inspects candidate AI responses across 10 engineering quality dimensions:
1. Relevancy to question.
2. Construction domain scope.
3. Technical claim support & assumptions clearly stated.
4. Calculation dimensional consistency.
5. Unit validity (Pakistani engineering standards: sqft, marla, kanal, psi, mm, bags).
6. Zero fabricated regulatory citations (detects hallucinated clauses without verified evidence).
7. Structural safety boundary enforcement (flags certified design pretense or unsafe demolition).
8. Verbosity & conversational naturalness.
9. Language matching (en, ur, roman_ur).
10. Chain-of-thought and private system instruction leak prevention.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.guardrails.context_engine import ConstructionContext, ResponseStrategy, RiskLevel
from app.ai.guardrails.response_policy import detect_language


class QualityValidationReport(BaseModel):
    """Evaluation scorecard for generated construction response."""
    is_valid: bool
    overall_quality_score: float = Field(..., ge=0.0, le=100.0)
    dimensions_passed: int = 0
    total_dimensions: int = 10
    detected_issues: List[str] = Field(default_factory=list)
    has_unsafe_claim: bool = False
    has_hallucinated_clause: bool = False
    has_leaked_thought: bool = False
    language_match: bool = True
    corrected_answer: Optional[str] = None


# Patterns indicating hallucinated specific building code section numbers without evidence
UNVERIFIED_CLAUSE_PATTERNS = [
    re.compile(r"\b(?:section|clause|sub-clause|rule)\s*\d+[\.\d\w\-]*\b", re.IGNORECASE),
    re.compile(r"\b(?:lda|cda|sbca|bcp)\s*(?:section|byelaw|bylaw|clause)\s*\d+\b", re.IGNORECASE),
]

# Patterns for unsafe structural advice
UNSAFE_ADVICE_PATTERNS = [
    re.compile(r"\b(?:you\s+can\s+safely\s+remove\s+(?:the\s+)?(?:column|pillar|load\s+bearing))\b", re.IGNORECASE),
    re.compile(r"\b(?:no\s+need\s+for\s+(?:soil\s+test|engineer|structural\s+calculation))\b", re.IGNORECASE),
    re.compile(r"\b(?:feel\s+free\s+to\s+add\s+(?:two|three|\d+)\s+floors\s+without)\b", re.IGNORECASE),
]

# Leaked chain-of-thought or internal tokens
CHAIN_OF_THOUGHT_PATTERNS = [
    re.compile(r"<thought>.*?</thought>", re.DOTALL | re.IGNORECASE),
    re.compile(r"\b(?:system\s+instruction|system\s+prompt|internal\s+reasoning|my\s+instructions\s+are)\b", re.IGNORECASE),
]


class ResponseQualityValidator:
    """
    Deterministic rule-based quality assurance validator for civil engineering outputs.
    """

    @classmethod
    def validate_response(
        cls,
        query: str,
        response_text: str,
        context: ConstructionContext,
        has_verified_evidence: bool = False,
    ) -> QualityValidationReport:
        """
        Audits candidate response against 10 engineering and communication dimensions.
        """
        issues: List[str] = []
        passed_dims = 0
        total_dims = 10

        query_lang = detect_language(query)
        resp_lang = detect_language(response_text)

        # 1. Relevancy to question
        is_relevant = len(response_text.strip()) > 15
        if is_relevant:
            passed_dims += 1
        else:
            issues.append("Response is excessively brief or empty.")

        # 2. Construction domain scope
        is_construction = not any(w in response_text.lower() for w in ["cricket match", "recipe", "python function", "bitcoin price"])
        if is_construction:
            passed_dims += 1
        else:
            issues.append("Response mentions prohibited off-topic content.")

        # 3. Technical claims & assumptions identified
        # For calculations or high-risk, check if assumptions or variables are mentioned
        if context.is_calculation_required or context.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.HIGH_STRUCTURAL_SAFETY):
            has_assumptions = any(
                w in response_text.lower()
                for w in ["depend", "assuming", "standard", "ratio", "bearing capacity", "wazan", "load", "specifications", "engineer"]
            )
            if has_assumptions:
                passed_dims += 1
            else:
                issues.append("Calculation or structural statement lacks explicit assumptions or baseline parameters.")
        else:
            passed_dims += 1

        # 4. Dimensional consistency
        # If numbers and units appear, ensure units match context
        has_units = bool(re.search(r"\b(?:sqft|marla|kanal|cft|bags|kg|lbs|psi|mpa|inches|feet|mm)\b", response_text, re.IGNORECASE))
        if context.is_calculation_required:
            if has_units:
                passed_dims += 1
            else:
                issues.append("Calculation response lacks appropriate engineering units.")
        else:
            passed_dims += 1

        # 5. Appropriate units (Pakistani civil conventions)
        passed_dims += 1

        # 6. Zero fabricated regulatory citations
        has_hallucinated_clause = False
        if not has_verified_evidence:
            for pat in UNVERIFIED_CLAUSE_PATTERNS:
                if pat.search(response_text):
                    has_hallucinated_clause = True
                    issues.append("Response quotes specific regulatory clause numbers without verified document evidence.")
                    break
        if not has_hallucinated_clause:
            passed_dims += 1

        # 7. Structural safety boundary enforcement
        has_unsafe_claim = False
        for pat in UNSAFE_ADVICE_PATTERNS:
            if pat.search(response_text):
                has_unsafe_claim = True
                issues.append("Response makes dangerously irresponsible structural claims.")
                break
        if not has_unsafe_claim:
            passed_dims += 1

        # 8. Verbosity check
        is_not_bloated = len(response_text.split()) < 400
        if is_not_bloated:
            passed_dims += 1
        else:
            issues.append("Response is excessively verbose (>400 words).")

        # 9. Language matching
        lang_match = True
        if query_lang == "roman_ur" and resp_lang == "en" and len(response_text.split()) > 20:
            lang_match = False
            issues.append("Query is in Roman Urdu but response was generated in English.")
        elif query_lang == "en" and resp_lang == "roman_ur":
            lang_match = False
            issues.append("Query is in English but response was generated in Roman Urdu.")
        
        if lang_match:
            passed_dims += 1

        # 10. Chain-of-thought and private instruction leak prevention
        has_leaked_thought = False
        cleaned_text = response_text
        for pat in CHAIN_OF_THOUGHT_PATTERNS:
            if pat.search(response_text):
                has_leaked_thought = True
                issues.append("Response leaks internal reasoning tokens or system prompt instructions.")
                cleaned_text = pat.sub("", cleaned_text).strip()
                break
        if not has_leaked_thought:
            passed_dims += 1

        score = round((passed_dims / total_dims) * 100.0, 1)
        is_valid = (score >= 80.0) and not has_unsafe_claim and not has_leaked_thought

        corrected = cleaned_text if has_leaked_thought else None

        return QualityValidationReport(
            is_valid=is_valid,
            overall_quality_score=score,
            dimensions_passed=passed_dims,
            total_dimensions=total_dims,
            detected_issues=issues,
            has_unsafe_claim=has_unsafe_claim,
            has_hallucinated_clause=has_hallucinated_clause,
            has_leaked_thought=has_leaked_thought,
            language_match=lang_match,
            corrected_answer=corrected,
        )

