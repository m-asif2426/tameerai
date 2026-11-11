"""
TameerAI - Construction Domain Guard (Phase 03F)
Implements a 5-layer classification architecture:
- Layer 1: Text Normalization (spelling variants, Roman Urdu phonetics, abbreviations)
- Layer 2: Construction Intent Detection (explanation, calculation, estimate, procedure, etc.)
- Layer 3: Entity Extraction (materials, components, measurements, units, loads, soil)
- Layer 4: Context Analysis (missing variables, structural risks, engineering dependencies)
- Layer 5: Confidence & Routing (high, medium, low confidence categories)

Enforces that TameerAI operates exclusively as a specialized civil engineering & construction assistant.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.ai.guardrails.entities import (
    ConstructionEntityExtractor,
    EntityCategory,
    ExtractedEntity,
)
from app.ai.guardrails.intent import (
    ConstructionIntent,
    ConstructionIntentDetector,
    IntentDetectionResult,
)
from app.ai.guardrails.normalizer import NormalizedQuery, TextNormalizer
from app.ai.guardrails.context_engine import (
    ConstructionContext,
    ConstructionContextEngine,
    ResponseStrategy,
)
from app.ai.guardrails.response_policy import detect_language
from app.ai.guardrails.vocabulary import (
    CONSTRUCTION_KEYWORDS,
    OFF_TOPIC_EXACT_INDICATORS,
    PROMPT_INJECTION_INDICATORS,
)


class DomainCategory(str, Enum):
    CONSTRUCTION_RELATED = "construction_related"
    OFF_TOPIC = "off_topic"
    AMBIGUOUS = "ambiguous"
    MIXED_TOPIC = "mixed_topic"


class ConfidenceCategory(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


MIN_CONFIDENCE_THRESHOLD: float = 0.60


class DomainClassificationResult(BaseModel):
    """Result of multi-layer domain classification."""
    category: DomainCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_category: ConfidenceCategory = ConfidenceCategory.HIGH
    matched_keywords: List[str] = Field(default_factory=list)
    is_jailbreak_attempt: bool = Field(default=False)
    reasoning: str
    sanitized_construction_query: Optional[str] = None
    separation_reliable: bool = True
    
    # Phase 03F Enriched Fields
    intent: Optional[ConstructionIntent] = None
    detected_entities: List[ExtractedEntity] = Field(default_factory=list)
    normalized_query: Optional[str] = None
    context_analysis: Optional[ConstructionContext] = None


# Follow-up anaphoric indicators in English and Roman Urdu
FOLLOW_UP_INDICATORS = [
    re.compile(r"^(?:aur|and|or|what\s+about|agar|if|how\s+about|phir|then|iska|iski|inke)\b", re.IGNORECASE),
    re.compile(r"\b(?:kitna|kitni|kitne|how\s+much|how\s+many|depth|thickness|rate|cost|size)\b", re.IGNORECASE),
]

# Non-construction idioms that misuse construction words
FIGURATIVE_MISUSES = [
    re.compile(r"\bcivil\s+rights\b", re.IGNORECASE),
    re.compile(r"\bconcrete\s+(?:evidence|proof|example|jungle)\b", re.IGNORECASE),
    re.compile(r"\bfoundation\s+of\s+(?:love|life|relationship|friendship)\b", re.IGNORECASE),
    re.compile(r"\bbuilding\s+a\s+(?:career|relationship|future|character)\b", re.IGNORECASE),
]

# Delimiters and coordinators used for bidirectional clause segmentation (English, Roman Urdu, Urdu script)
CLAUSE_BOUNDARY_REGEX = re.compile(
    r"(?:[\?!;\n؟؛]+|,\s*(?:and|also|but|aur|or|lekin|magar|as\s+well\s+as)\b|،\s*(?:اور|لیکن|مگر|یا)\b|\b(?:and\s+also|as\s+well\s+as|and|also|but|aur|lekin|magar)\b|\b(?:اور|لیکن|مگر|یا)\b)",
    re.IGNORECASE,
)


class ConstructionDomainGuard:
    """
    Production-grade multi-layer guardrail enforcing construction-only boundaries.
    """

    def __init__(self, confidence_threshold: float = MIN_CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold

    def _check_jailbreak(self, text: str) -> bool:
        """Detects prompt injection and jailbreak overrides."""
        lower = text.lower()
        return any(indicator in lower for indicator in PROMPT_INJECTION_INDICATORS)

    def _clean_tokens(self, text: str) -> List[str]:
        """Extracts normalized lowercase tokens across languages."""
        return re.findall(r"[\w\-.:/]+", text.lower())

    def _extract_construction_matches(self, text: str, normalized_text: str = "") -> List[str]:
        """Finds matching construction terms across raw and normalized tokens."""
        lower = text.lower()
        for pattern in FIGURATIVE_MISUSES:
            lower = pattern.sub("", lower)

        norm_lower = normalized_text.lower() if normalized_text else lower
        for pattern in FIGURATIVE_MISUSES:
            norm_lower = pattern.sub("", norm_lower)

        matches: List[str] = []
        for kw in CONSTRUCTION_KEYWORDS:
            if " " in kw or any('\u0600' <= c <= '\u06FF' for c in kw):
                if kw in lower or kw in norm_lower:
                    matches.append(kw)
            else:
                regex = r"\b" + re.escape(kw) + r"\b"
                if re.search(regex, lower) or re.search(regex, norm_lower):
                    matches.append(kw)
        return list(set(matches))

    def _extract_off_topic_matches(self, text: str) -> List[str]:
        """Finds matching off-topic keywords."""
        lower = text.lower()
        matches: List[str] = []
        for kw in OFF_TOPIC_EXACT_INDICATORS:
            if " " in kw or any('\u0600' <= c <= '\u06FF' for c in kw):
                if kw in lower:
                    matches.append(kw)
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                    matches.append(kw)
        return list(set(matches))

    def _segment_and_classify_clauses(
        self,
        raw_text: str,
        normalized_text: str = "",
    ) -> Tuple[List[str], List[str], bool]:
        """
        Splits input text along punctuation and coordinator conjunctions bidirectionally.
        Classifies each segment into construction vs off-topic.
        Returns:
            (construction_clauses, off_topic_clauses, separation_reliable)
        """
        raw_segments = CLAUSE_BOUNDARY_REGEX.split(raw_text)
        cleaned_segments = [s.strip(" ,?!;.\n\t") for s in raw_segments if s.strip(" ,?!;.\n\t")]

        if not cleaned_segments:
            return ([], [], False)

        c_clauses: List[str] = []
        ot_clauses: List[str] = []
        has_entangled_segment = False

        for seg in cleaned_segments:
            norm_seg = TextNormalizer.normalize(seg).normalized_query
            seg_c_matches = self._extract_construction_matches(seg, norm_seg)
            seg_ot_matches = self._extract_off_topic_matches(seg)

            if seg_c_matches and seg_ot_matches:
                has_entangled_segment = True
                c_clauses.append(seg)
                ot_clauses.append(seg)
            elif seg_c_matches:
                c_clauses.append(seg)
            elif seg_ot_matches:
                ot_clauses.append(seg)

        if has_entangled_segment or len(cleaned_segments) <= 1:
            return (c_clauses, ot_clauses, False)

        if c_clauses and ot_clauses:
            return (c_clauses, ot_clauses, True)

        return (c_clauses, ot_clauses, True)

    def _is_anaphoric_follow_up(self, text: str) -> bool:
        """Checks if question is structurally a follow-up."""
        t_clean = text.strip()
        return any(pattern.search(t_clean) for pattern in FOLLOW_UP_INDICATORS)

    def classify(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> DomainClassificationResult:
        """
        Executes 5-layer classification of user query:
        Normalization -> Intent Detection -> Entity Extraction -> Context Analysis -> Confidence & Routing.
        """
        raw_text = query.strip()
        if not raw_text:
            return DomainClassificationResult(
                category=DomainCategory.AMBIGUOUS,
                confidence=0.5,
                confidence_category=ConfidenceCategory.LOW,
                reasoning="Empty query provided.",
                separation_reliable=False,
            )

        # Layer 1: Text Normalization
        normalized: NormalizedQuery = TextNormalizer.normalize(raw_text)
        lang = detect_language(raw_text)

        # Pre-Check: Prompt Injection & Adversarial Jailbreak Detection
        if self._check_jailbreak(raw_text) or self._check_jailbreak(normalized.normalized_query):
            return DomainClassificationResult(
                category=DomainCategory.OFF_TOPIC,
                confidence=1.0,
                confidence_category=ConfidenceCategory.HIGH,
                is_jailbreak_attempt=True,
                reasoning="Adversarial prompt injection attempt detected. Overriding to OFF_TOPIC.",
                normalized_query=normalized.normalized_query,
            )

        # Layer 2 & 3: Intent Detection and Entity Extraction
        intent_res: IntentDetectionResult = ConstructionIntentDetector.detect_intent(normalized)
        entities: List[ExtractedEntity] = ConstructionEntityExtractor.extract_entities(normalized)

        # Layer 4: Context Analysis with multi-turn history
        context: ConstructionContext = ConstructionContextEngine.analyze_context(
            normalized=normalized,
            intent=intent_res.primary_intent,
            entities=entities,
            language=lang,
            conversation_history=conversation_history,
        )

        # Keyword extractions
        construction_matches = self._extract_construction_matches(raw_text, normalized.normalized_query)
        off_topic_matches = self._extract_off_topic_matches(raw_text)

        # Add technical civil engineering entities to matched keywords
        direct_categories = {
            EntityCategory.MATERIAL,
            EntityCategory.BUILDING_COMPONENT,
            EntityCategory.STRUCTURAL_ELEMENT,
            EntityCategory.CONSTRUCTION_ACTIVITY,
        }
        for ent in entities:
            if ent.category in direct_categories and ent.value.lower() not in construction_matches:
                construction_matches.append(ent.value.lower())

        # Check for mixed topic: both construction and off-topic present
        if construction_matches and off_topic_matches:
            c_clauses, ot_clauses, separation_reliable = self._segment_and_classify_clauses(
                raw_text, normalized.normalized_query
            )

            if separation_reliable and c_clauses:
                sanitized_c = ", and ".join(c_clauses)
                if not sanitized_c.endswith(("?", ".", "!", "؟")):
                    sanitized_c += "؟" if "؟" in raw_text else ("?" if "?" in raw_text else ".")

                return DomainClassificationResult(
                    category=DomainCategory.MIXED_TOPIC,
                    confidence=0.85,
                    confidence_category=ConfidenceCategory.HIGH,
                    matched_keywords=construction_matches,
                    sanitized_construction_query=sanitized_c,
                    separation_reliable=True,
                    reasoning=f"Query combines construction concepts ({construction_matches[:2]}) with unrelated topics ({off_topic_matches[:2]}), cleanly separated.",
                    intent=intent_res.primary_intent,
                    detected_entities=entities,
                    normalized_query=normalized.normalized_query,
                    context_analysis=context,
                )
            else:
                return DomainClassificationResult(
                    category=DomainCategory.AMBIGUOUS,
                    confidence=0.50,
                    confidence_category=ConfidenceCategory.LOW,
                    matched_keywords=construction_matches,
                    sanitized_construction_query=None,
                    separation_reliable=False,
                    reasoning="Query combines construction concepts with unrelated topics in an inseparable or entangled form.",
                    intent=ConstructionIntent.AMBIGUOUS,
                    detected_entities=entities,
                    normalized_query=normalized.normalized_query,
                    context_analysis=context,
                )

        # Pure off-topic match
        if off_topic_matches and not construction_matches:
            return DomainClassificationResult(
                category=DomainCategory.OFF_TOPIC,
                confidence=0.95,
                confidence_category=ConfidenceCategory.HIGH,
                matched_keywords=off_topic_matches,
                reasoning=f"Identified clear non-construction topic ({off_topic_matches}).",
                intent=ConstructionIntent.OFF_TOPIC,
                normalized_query=normalized.normalized_query,
            )

        # Strong construction match
        if construction_matches:
            conf = min(0.98, 0.70 + (len(construction_matches) * 0.10))
            conf_cat = (
                ConfidenceCategory.HIGH
                if conf >= 0.80
                else (ConfidenceCategory.MEDIUM if conf >= MIN_CONFIDENCE_THRESHOLD else ConfidenceCategory.LOW)
            )
            return DomainClassificationResult(
                category=DomainCategory.CONSTRUCTION_RELATED,
                confidence=conf,
                confidence_category=conf_cat,
                matched_keywords=construction_matches,
                reasoning=f"Recognized construction concepts: {sorted(construction_matches)[:4]}.",
                intent=intent_res.primary_intent,
                detected_entities=entities,
                normalized_query=normalized.normalized_query,
                context_analysis=context,
            )

        # Follow-up context awareness & anaphora
        if conversation_history and len(conversation_history) > 0:
            last_turn = conversation_history[-1]
            last_content = last_turn.get("content", "")
            prev_construction_matches = self._extract_construction_matches(last_content)

            if prev_construction_matches and self._is_anaphoric_follow_up(raw_text):
                return DomainClassificationResult(
                    category=DomainCategory.CONSTRUCTION_RELATED,
                    confidence=0.80,
                    confidence_category=ConfidenceCategory.HIGH,
                    matched_keywords=prev_construction_matches[:3],
                    reasoning=f"Follow-up contextually linked to prior construction topic ({prev_construction_matches[:2]}).",
                    intent=intent_res.primary_intent,
                    detected_entities=entities,
                    normalized_query=normalized.normalized_query,
                    context_analysis=context,
                )

        # Ambiguous detection
        tokens = normalized.tokens
        if len(tokens) <= 4 or intent_res.primary_intent == ConstructionIntent.AMBIGUOUS:
            return DomainClassificationResult(
                category=DomainCategory.AMBIGUOUS,
                confidence=0.50,
                confidence_category=ConfidenceCategory.LOW,
                reasoning="Short or underspecified query without clear technical domain markers.",
                intent=ConstructionIntent.AMBIGUOUS,
                normalized_query=normalized.normalized_query,
                context_analysis=context,
            )

        # Default fallback
        return DomainClassificationResult(
            category=DomainCategory.OFF_TOPIC,
            confidence=0.75,
            confidence_category=ConfidenceCategory.MEDIUM,
            reasoning="Query contains zero recognized construction, civil engineering, or building code concepts.",
            intent=ConstructionIntent.OFF_TOPIC,
            normalized_query=normalized.normalized_query,
        )
