"""
TameerAI - Phase 03F Construction Intelligence & Response Quality Unit Tests
Comprehensive test suite verifying:
- Layer 1: Text Normalizer (spelling variants, Roman Urdu phonetics, abbreviations)
- Layer 2: Construction Intent Detector (9 core intents)
- Layer 3: Entity Extractor (materials, structural elements, measurements, soil, loads)
- Layer 4 & Task B: Construction Context Engine (missing variables, risk levels, strategy selection)
- Task F: Response Quality Validator (10 engineering quality dimensions)
- Task D: Natural, context-aware workflow response generation
"""

import pytest
from app.ai.guardrails.context_engine import (
    ConstructionContext,
    ConstructionContextEngine,
    ResponseStrategy,
    RiskLevel,
)
from app.ai.guardrails.domain_guard import (
    ConfidenceCategory,
    ConstructionDomainGuard,
    DomainCategory,
)
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
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.validation.quality import QualityValidationReport, ResponseQualityValidator
from app.ai.workflow.construction_chat import ConstructionChatWorkflow


class TestTextNormalizer:
    """Verifies Layer 1 normalization of text, spelling, abbreviations, and Roman Urdu."""

    def test_spelling_variation_normalization(self):
        variations = [
            ("5 marla bunyad kitni gehri ho?", "bunyaad"),
            ("sariya ka weight formula", "saria"),
            ("cemnt aur bajree ka mix", "cement"),
            ("shutraing kab remove karni chahiye?", "shuttering"),
            ("concrete ki tarai kitne din?", "curing"),
            ("lanter dalne ka tareeqa", "lanter"),
            ("ret aur crush ratio", "ret"),
            ("khudai ki depth kitni hai?", "khudai"),
        ]
        for query, expected_token in variations:
            norm = TextNormalizer.normalize(query)
            assert expected_token in norm.normalized_query or expected_token in norm.normalized_terms.values()

    def test_abbreviation_expansion(self):
        query = "RCC slab casting under LDA bylaws with 3000 PSI concrete"
        norm = TextNormalizer.normalize(query)
        assert "rcc" in norm.detected_abbreviations
        assert "lda" in norm.detected_abbreviations
        assert "psi" in norm.detected_abbreviations
        assert norm.detected_abbreviations["rcc"] == "reinforced cement concrete"
        assert norm.detected_abbreviations["lda"] == "lahore development authority"


class TestIntentDetection:
    """Verifies Layer 2 construction intent classification across 9 specialized intents."""

    def test_explanation_intent(self):
        norm = TextNormalizer.normalize("Why does foundation depth depend on soil bearing capacity?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.EXPLANATION

    def test_calculation_intent(self):
        norm = TextNormalizer.normalize("Saria ka weight kaise calculate hota hai formula batao?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.CALCULATION

    def test_quantity_estimate_intent(self):
        norm = TextNormalizer.normalize("1000 square feet slab ke liye kitne bags cement lagenge?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.QUANTITY_ESTIMATE

    def test_material_recommendation_intent(self):
        norm = TextNormalizer.normalize("Which cement is best for basement water retaining structure OPC or SRC?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.MATERIAL_RECOMMENDATION

    def test_procedure_intent(self):
        norm = TextNormalizer.normalize("What are the step by step procedures for concrete slump test?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.PROCEDURE

    def test_troubleshooting_intent(self):
        norm = TextNormalizer.normalize("Plaster mein darar kyun aati hai aur seepage kaise theek karein?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.TROUBLESHOOTING

    def test_comparison_intent(self):
        norm = TextNormalizer.normalize("What is the difference between raft foundation and isolated footing?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.COMPARISON

    def test_compliance_intent(self):
        norm = TextNormalizer.normalize("What are the setback requirements under LDA building bylaws?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.COMPLIANCE

    def test_planning_intent(self):
        norm = TextNormalizer.normalize("Construction project ka timeline schedule aur running bill kaise banaya jata hai?")
        res = ConstructionIntentDetector.detect_intent(norm)
        assert res.primary_intent == ConstructionIntent.PLANNING


class TestEntityExtraction:
    """Verifies Layer 3 technical entity extraction."""

    def test_materials_and_components(self):
        norm = TextNormalizer.normalize("1:2:4 ratio concrete with OPC cement, aggregate and Grade 60 saria")
        entities = ConstructionEntityExtractor.extract_entities(norm)
        canonical_vals = {e.canonical_value for e in entities}
        assert "concrete" in canonical_vals
        assert "steel_rebar" in canonical_vals
        assert "ordinary_portland_cement" in canonical_vals or "cement" in canonical_vals
        assert any("mix_ratio:1:2:4" in c for c in canonical_vals)

    def test_dimensions_and_plot_sizes(self):
        norm = TextNormalizer.normalize("5 marla double storey residential building on 1000 sqft with 6 inch slab")
        entities = ConstructionEntityExtractor.extract_entities(norm)
        cats = [e.category for e in entities]
        assert EntityCategory.MEASUREMENT in cats
        # Verify 5 marla extracted
        marla_ent = next((e for e in entities if "5 marla" in e.value.lower()), None)
        assert marla_ent is not None
        assert marla_ent.numeric_quantity == 5.0
        assert marla_ent.unit == "marla"


class TestConstructionContextEngine:
    """Verifies Task B context analysis, missing variables, and safety risk evaluation."""

    def test_missing_variables_for_foundation_depth(self):
        norm = TextNormalizer.normalize("5 marla ghar ki bunyaad kitni gehri honi chahiye?")
        intent = ConstructionIntent.EXPLANATION
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, intent, entities, language="roman_ur")

        assert context.topic == "Foundation & Geotechnical Engineering"
        missing_names = [mv.name for mv in context.missing_variables]
        assert "soil_bearing_capacity" in missing_names
        assert "structural_load" in missing_names

    def test_safety_critical_column_removal_detection(self):
        norm = TextNormalizer.normalize("Can we safely remove the ground floor center column to open up space?")
        intent = ConstructionIntent.PROCEDURE
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, intent, entities, language="en")

        assert context.is_safety_critical is True
        assert context.risk_level == RiskLevel.HIGH_STRUCTURAL_SAFETY
        assert context.recommended_strategy == ResponseStrategy.HIGH_RISK_ADVISORY


class TestResponseQualityValidator:
    """Verifies Task F 10-dimension response validation."""

    def test_valid_engineering_response_passes(self):
        query = "Concrete ki curing kitne din karni chahiye?"
        response = (
            "Concrete ki curing (tarai) aam taur par kam az kam 7 se 14 din tak karni chahiye. "
            "Curing ki muddat cement ki qisam (OPC ya SRC), mausam ke darja hararat aur project specifications par munhasir hoti hai. "
            "Garmi ke mausam mein nami barqarar rakhna zaroori hai taakay shrinkage cracks na aain."
        )
        norm = TextNormalizer.normalize(query)
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.EXPLANATION, entities, "roman_ur")

        report = ResponseQualityValidator.validate_response(query, response, context)
        assert report.is_valid is True
        assert report.overall_quality_score >= 80.0
        assert report.has_unsafe_claim is False
        assert report.has_hallucinated_clause is False

    def test_hallucinated_bylaw_clause_detected_without_evidence(self):
        query = "What is the setback rule for 10 marla plot?"
        response = (
            "According to LDA Building Byelaws Section 99.4.2 Clause 7b, the minimum rear setback is strictly 7 feet."
        )
        norm = TextNormalizer.normalize(query)
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.COMPLIANCE, entities, "en")

        report = ResponseQualityValidator.validate_response(query, response, context, has_verified_evidence=False)
        assert report.has_hallucinated_clause is True
        assert any("clause" in iss.lower() for iss in report.detected_issues)

    def test_unsafe_column_removal_claim_blocked(self):
        query = "Can I remove this column?"
        response = "Yes, you can safely remove the column without any engineering calculations if you put a small lintel."
        norm = TextNormalizer.normalize(query)
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.PROCEDURE, entities, "en")

        report = ResponseQualityValidator.validate_response(query, response, context)
        assert report.has_unsafe_claim is True
        assert report.is_valid is False

    def test_chain_of_thought_leak_scrubbed(self):
        query = "How to test slump?"
        response = "<thought>User wants slump test details.</thought>Slump test measures fresh concrete workability."
        norm = TextNormalizer.normalize(query)
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.PROCEDURE, entities, "en")

        report = ResponseQualityValidator.validate_response(query, response, context)
        assert report.has_leaked_thought is True
        assert report.corrected_answer == "Slump test measures fresh concrete workability."


@pytest.mark.asyncio
class TestWorkflowIntegrationWithIntelligence:
    """Verifies end-to-end flow with MockAIProvider adhering to Phase 03F enhancements."""

    async def test_end_to_end_context_and_quality_report(self):
        workflow = ConstructionChatWorkflow()
        query = "1000 square feet slab ke liye concrete quantity aur cement bags calculate karain"
        resp = await workflow.process_user_query(query)

        assert resp.domain_category == DomainCategory.CONSTRUCTION_RELATED
        assert resp.context is not None
        assert resp.context.intent in (ConstructionIntent.QUANTITY_ESTIMATE, ConstructionIntent.CALCULATION)
        assert resp.quality_report is not None
        assert resp.quality_report.is_valid is True
        assert "telemetry" in resp.model_dump()
        assert "quality_score" in resp.telemetry

