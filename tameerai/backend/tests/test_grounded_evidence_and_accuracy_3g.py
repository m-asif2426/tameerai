"""
TameerAI - Phase 03G Stage B3 Grounded Evidence, Citation Validation & Technical Accuracy Tests

Comprehensive test suite verifying all 23 mandatory Stage B3 requirements:
1. Valid retrieved citation acceptance.
2. Fabricated citation rejection.
3. Invalid document ID rejection.
4. Invalid chunk ID rejection.
5. Cross-project citation rejection.
6. Mismatched document/chunk relationship.
7. Invalid regulatory clause rejection.
8. Unsupported structural claim handling.
9. Missing evidence response.
10. Partially supported response.
11. Verified calculation acceptance.
12. Incorrect numerical result detection.
13. Unit mismatch detection.
14. Missing material rate handling.
15. Stale material rate handling.
16. Roman Urdu evidence-aware response.
17. English evidence-aware response.
18. Urdu evidence-aware response.
19. Citation sanitization.
20. Existing tenant isolation preservation.
21. Existing high-risk structural routing preservation.
22. No fabricated source metadata.
23. No unauthorized document leakage.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID, uuid4
import pytest

from app.ai.contracts.provider import (
    FinishReason,
    ModelRequest,
    ModelResponse,
    TokenUsage,
)
from app.ai.contracts.retrieval import RetrievalQuery, RetrievalResult, RetrievedChunk, ScopeType
from app.ai.contracts.validation import ValidationStatus
from app.ai.guardrails.context_engine import ConstructionContextEngine, RiskLevel
from app.ai.guardrails.domain_guard import ConstructionDomainGuard, DomainCategory
from app.ai.guardrails.entities import ConstructionEntityExtractor
from app.ai.guardrails.intent import ConstructionIntent, ConstructionIntentDetector
from app.ai.guardrails.normalizer import TextNormalizer
from app.ai.guardrails.response_policy import detect_language
from app.ai.validation.citation import CitationValidator
from app.ai.validation.grounded_policy import (
    EvidenceTier,
    GroundedResponsePolicy,
)
from app.ai.validation.technical_accuracy import (
    EngineeringFormulaVerifier,
    MaterialRateReliabilityVerifier,
    UngroundedClaimDetector,
    UnitConsistencyAuditor,
)
from app.ai.workflow.construction_chat import ConstructionChatWorkflow


# =====================================================================
# TEST SPIES & SYNTHETIC FIXTURES
# =====================================================================

class RecordingAIProvider:
    """Test spy that returns canned technical answers."""

    def __init__(self, response_text: str = "Standard 1:2:4 nominal concrete requires approximately 8.8 bags of cement per 50 cft."):
        self.response_text = response_text
        self.recorded_requests: List[ModelRequest] = []

    @property
    def provider_name(self) -> str:
        return "recording_spy"

    @property
    def default_model(self) -> str:
        return "mock-model"

    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        self.recorded_requests.append(request)
        return ModelResponse(
            content=self.response_text,
            provider_name="recording_spy",
            model_identifier="mock-model",
            finish_reason=FinishReason.STOP,
            usage=TokenUsage(prompt_tokens=20, completion_tokens=30, total_tokens=50),
        )

    async def generate_structured(self, request: ModelRequest, schema: object) -> object:
        raise NotImplementedError()


class RecordingRetrievalService:
    """Test spy providing controlled evidence chunks."""

    def __init__(self, chunks: Optional[List[RetrievedChunk]] = None):
        self.chunks = chunks or []
        self.recorded_queries: List[RetrievalQuery] = []

    async def retrieve(
        self,
        query: RetrievalQuery,
        requesting_user_id: Optional[object] = None,
        allow_synthetic: bool = True,
    ) -> RetrievalResult:
        self.recorded_queries.append(query)
        return RetrievalResult(query=query.query_text, chunks=self.chunks, scope_used=query.scope)


class MockMaterialRate:
    """Mock MaterialRate record matching app.models.cost.MaterialRate."""

    def __init__(
        self,
        name: str,
        category: str,
        city: str,
        rate_pkr: float,
        unit: str,
        observed_at: datetime,
        source_name: str = "Pakistan Bureau of Statistics",
        verification_status: str = "verified",
    ):
        self.id = uuid4()
        self.name = name
        self.category = category
        self.city = city
        self.rate_pkr = rate_pkr
        self.unit = unit
        self.observed_at = observed_at
        self.source_name = source_name
        self.verification_status = verification_status


# =====================================================================
# DEDICATED STAGE B3 TEST SUITE (Items 1 to 23)
# =====================================================================

class TestGroundedEvidenceAndAccuracy3G:
    """Verifies all 23 Stage B3 requirements."""

    def setup_method(self):
        self.validator = CitationValidator()
        self.proj_a = uuid4()
        self.proj_b = uuid4()
        self.doc_a = uuid4()
        self.doc_b = uuid4()
        self.chunk_global_id = uuid4()
        self.chunk_proj_id = uuid4()

        self.global_chunk = RetrievedChunk(
            chunk_id=self.chunk_global_id,
            source_title="Building Code of Pakistan 2021",
            source_code="PBC-2021",
            content="Section 5.1: Minimum specified compressive strength for reinforced concrete columns shall be 3000 psi.",
            page_number=45,
            clause_or_section="Section 5.1",
            scope=ScopeType.GLOBAL_REGULATORY,
        )

        self.project_chunk = RetrievedChunk(
            chunk_id=self.chunk_proj_id,
            source_title="Approved Structural Drawings Plaza",
            source_code="PRJ-DOC-01",
            content="Clause 3.2: General Notes specify column C1 dimensions as 12x12 inches with 4 #6 bars.",
            page_number=3,
            clause_or_section="Clause 3.2",
            scope=ScopeType.PROJECT_PRIVATE,
            project_id=self.proj_a,
            document_id=self.doc_a,
        )

    # 1. Valid retrieved citation acceptance
    def test_01_valid_retrieved_citation_acceptance(self):
        citations = [{
            "source_code": "PBC-2021",
            "title": "Building Code of Pakistan 2021",
            "page_number": 45,
            "section_or_clause": "Section 5.1",
            "chunk_id": str(self.chunk_global_id),
            "claim_text": "compressive strength 3000 psi",
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.is_fully_grounded is True
        assert rep.valid_citations == 1
        assert rep.unsupported_citations == 0
        assert rep.items[0].status == ValidationStatus.VALID

    # 2. Fabricated citation rejection
    def test_02_fabricated_citation_rejection(self):
        citations = [{
            "source_code": "LDA-9999",  # Completely fabricated source
            "title": "Imaginary Byelaw",
            "page_number": 1,
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.is_fully_grounded is False
        assert rep.unsupported_citations == 1
        assert rep.items[0].status == ValidationStatus.UNSUPPORTED_CITATION
        assert "not present in the retrieved evidence" in rep.items[0].explanation

    # 3. Invalid document ID rejection
    def test_03_invalid_document_id_rejection(self):
        citations = [{
            "source_code": "PRJ-DOC-01",
            "chunk_id": str(self.chunk_proj_id),
            "document_id": str(self.doc_b),  # Wrong document ID! (belongs to doc_a)
            "title": "Plaza Drawing",
        }]
        rep = self.validator.validate_citations(citations, [self.project_chunk], project_id=self.proj_a)
        assert rep.is_fully_grounded is False
        assert rep.unsupported_citations == 1
        assert rep.items[0].status == ValidationStatus.DOCUMENT_MISMATCH

    # 4. Invalid chunk ID rejection
    def test_04_invalid_chunk_id_rejection(self):
        fake_chunk_id = uuid4()
        citations = [{
            "source_code": "PBC-2021",
            "chunk_id": str(fake_chunk_id),  # Fabricated chunk ID!
            "title": "Building Code",
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.is_fully_grounded is False
        assert rep.unsupported_citations == 1
        assert rep.items[0].status == ValidationStatus.INVALID_CHUNK_ID

    # 5. Cross-project citation rejection
    def test_05_cross_project_citation_rejection(self):
        # User querying in project_b attempts to cite project_a private chunk
        citations = [{
            "source_code": "PRJ-DOC-01",
            "chunk_id": str(self.chunk_proj_id),
            "project_id": str(self.proj_a),
            "title": "Foreign Plaza Drawing",
        }]
        rep = self.validator.validate_citations(citations, [self.project_chunk], project_id=self.proj_b)
        assert rep.is_fully_grounded is False
        assert rep.unsupported_citations == 1
        assert rep.items[0].status == ValidationStatus.UNAUTHORIZED_PROJECT_REFERENCE

    # 6. Mismatched document/chunk relationship
    def test_06_mismatched_document_chunk_relationship(self):
        citations = [{
            "source_code": "PRJ-DOC-01",
            "chunk_id": str(self.chunk_proj_id),
            "document_id": str(uuid4()),  # Random forged doc ID
            "project_id": str(self.proj_a),
        }]
        rep = self.validator.validate_citations(citations, [self.project_chunk], project_id=self.proj_a)
        assert rep.items[0].status == ValidationStatus.DOCUMENT_MISMATCH
        assert rep.is_fully_grounded is False

    # 7. Invalid regulatory clause rejection
    def test_07_invalid_regulatory_clause_rejection(self):
        # Chunk has "Section 5.1", but citation claims "Section 99.8"
        citations = [{
            "source_code": "PBC-2021",
            "chunk_id": str(self.chunk_global_id),
            "section_or_clause": "Section 99.8",  # Non-existent clause
            "page_number": 45,
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.is_fully_grounded is False
        assert rep.items[0].status == ValidationStatus.INVALID_CLAUSE
        assert "not found in retrieved evidence" in rep.items[0].explanation

    # 8. Unsupported structural claim handling
    def test_08_unsupported_structural_claim_handling(self):
        text = "For your foundation, the depth must be 6 feet and you should provide 8 bars of 25mm for your column."
        issues = UngroundedClaimDetector.detect_ungrounded_claims(text, has_verified_evidence=False)
        assert len(issues) >= 1
        assert any(i.category == "ungrounded_claim" for i in issues)

    # 9. Missing evidence response
    def test_09_missing_evidence_response(self):
        query = "What is the specified concrete slump for the foundation in our project drawings?"
        response_text = "Standard foundation concrete slump typically ranges from 3 to 4 inches depending on placement method."
        norm = TextNormalizer.normalize(query)
        intent = ConstructionIntentDetector.detect_intent(norm).primary_intent
        entities = ConstructionEntityExtractor.extract_entities(norm)
        context = ConstructionContextEngine.analyze_context(norm, intent, entities, "en")

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=context,
            retrieved_chunks=[],  # Zero evidence!
            citations=[],
            language="en",
        )
        assert eval_rep.tier == EvidenceTier.INSUFFICIENT_EVIDENCE
        assert "Documentary Note" in eval_rep.annotated_answer

    # 10. Partially supported response
    def test_10_partially_supported_response(self):
        query = "Plaza column schedule details"
        response_text = "According to drawing PRJ-DOC-01, column C1 is 12x12 inches with 4 #6 bars, but you can also add 4 bars of 16mm for your column without calculations."
        norm = TextNormalizer.normalize(query)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.EXPLANATION, [], "en")

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=context,
            retrieved_chunks=[self.project_chunk],
            citations=[{
                "source_code": "PRJ-DOC-01",
                "chunk_id": str(self.chunk_proj_id),
                "section_or_clause": "Clause 3.2",
            }],
            project_id=self.proj_a,
            language="en",
        )
        assert eval_rep.tier == EvidenceTier.PARTIALLY_SUPPORTED
        assert "Partially Supported" in eval_rep.annotated_answer

    # 11. Verified calculation acceptance
    def test_11_verified_calculation_acceptance(self):
        # 12mm rebar theoretical weight = 12^2 / 162 = 0.8888 kg/m
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_rebar_weight(12.0, 0.889)
        assert is_valid is True
        assert math.isclose(exp, 0.88888, rel_tol=1e-3)
        assert "Verified" in expl

    # 12. Incorrect numerical result detection
    def test_12_incorrect_numerical_result_detection(self):
        # 12mm rebar asserted as 2.5 kg/m (wildly incorrect)
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_rebar_weight(12.0, 2.5)
        assert is_valid is False
        assert "Calculation mismatch" in expl

        # Text audit detection
        bad_text = "For 12mm rebar weight is 2.5 kg/m on site."
        audits = EngineeringFormulaVerifier.audit_response_calculations(bad_text)
        assert len(audits) == 1
        assert audits[0].is_valid is False
        assert "Calculation mismatch" in audits[0].explanation

    # 13. Unit mismatch detection
    def test_13_unit_mismatch_detection(self):
        bad_dim_text = "The calculated concrete volume of the footing is 250 sqft with a slab thickness of 6 sqft."
        issues = UnitConsistencyAuditor.audit_unit_consistency(bad_dim_text)
        assert len(issues) >= 1
        assert any("area units" in iss.explanation for iss in issues)

    # 14. Missing material rate handling
    def test_14_missing_material_rate_handling(self):
        text = "Current cement price is PKR 1,500 per bag in Multan."
        # No rates provided in database
        rate_rep = MaterialRateReliabilityVerifier.audit_material_rates(text, available_rates=[])
        assert rate_rep.has_price_claims is True
        assert rate_rep.is_reliable is False
        assert len(rate_rep.unverified_estimates) >= 1
        assert "Cement" in rate_rep.missing_sources[0]

    # 15. Stale material rate handling
    def test_15_stale_material_rate_handling(self):
        stale_date = datetime.now(timezone.utc) - timedelta(days=120)  # 4 months old
        stale_rate = MockMaterialRate(
            name="Ordinary Portland Cement",
            category="cement",
            city="Lahore",
            rate_pkr=1450.0,
            unit="bag",
            observed_at=stale_date,
            verification_status="stale",
        )
        text = "Cement rate is PKR 1,450 per bag in Lahore."
        rate_rep = MaterialRateReliabilityVerifier.audit_material_rates(text, available_rates=[stale_rate])
        assert rate_rep.has_price_claims is True
        assert rate_rep.is_reliable is False
        assert len(rate_rep.stale_rates_detected) >= 1

    # 16. Roman Urdu evidence-aware response
    def test_16_roman_urdu_evidence_aware_response(self):
        query = "CDA bylaws ke mutabiq commercial plot ka setback kitna hona chahiye?"
        response_text = "CDA regulations ke mutabiq commercial plot ka setback standard hota hai."
        norm = TextNormalizer.normalize(query)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.COMPLIANCE, [], "roman_ur")

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=context,
            retrieved_chunks=[],
            citations=[],
            language="roman_ur",
        )
        assert eval_rep.tier == EvidenceTier.REGULATORY_UNVERIFIED
        assert "Qawaneen Ki Hidayat" in eval_rep.annotated_answer
        assert "LDA / CDA / SBCA" in eval_rep.annotated_answer

    # 17. English evidence-aware response
    def test_17_english_evidence_aware_response(self):
        query = "What is the concrete compressive strength for columns under PBC?"
        response_text = "PBC Section 5.1 specifies minimum compressive strength as 3000 psi."
        norm = TextNormalizer.normalize(query)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.COMPLIANCE, [], "en")

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=context,
            retrieved_chunks=[self.global_chunk],
            citations=[{
                "source_code": "PBC-2021",
                "chunk_id": str(self.chunk_global_id),
                "section_or_clause": "Section 5.1",
            }],
            language="en",
        )
        assert eval_rep.tier == EvidenceTier.VERIFIED_ANSWER
        assert eval_rep.is_grounded is True

    # 18. Urdu evidence-aware response
    def test_18_urdu_evidence_aware_response(self):
        query = "سی ڈی اے ضوابط کے تحت سیٹ بیک کیا ہے؟"
        response_text = "کمرشل پلاٹ کے لیے سیٹ بیک کے اصول لاگو ہوتے ہیں۔"
        norm = TextNormalizer.normalize(query)
        context = ConstructionContextEngine.analyze_context(norm, ConstructionIntent.COMPLIANCE, [], "ur")

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=context,
            retrieved_chunks=[],
            citations=[],
            language="ur",
        )
        assert eval_rep.tier == EvidenceTier.REGULATORY_UNVERIFIED
        assert "تکنیکی انتباہ" in eval_rep.annotated_answer

    # 19. Citation sanitization
    def test_19_citation_sanitization(self):
        malformed_citation = [{
            "source_code": "",  # Empty
            "title": "No Code Doc",
            "page_number": -5,  # Negative page
        }]
        rep = self.validator.validate_citations(malformed_citation, [self.global_chunk])
        assert rep.is_fully_grounded is False
        assert rep.items[0].status == ValidationStatus.MALFORMED_IDENTIFIER

    # 20. Existing tenant isolation preservation
    @pytest.mark.asyncio
    async def test_20_existing_tenant_isolation_preservation(self):
        # Ensure private project documents are strictly isolated in the workflow
        ai_spy = RecordingAIProvider(response_text="General reply.")
        retrieval_spy = RecordingRetrievalService(chunks=[self.project_chunk])
        workflow = ConstructionChatWorkflow(ai_provider=ai_spy, retrieval_service=retrieval_spy)

        # Query executed in project_b should fail citation validation if referencing project_a chunk
        resp = await workflow.process_user_query(
            query="What is the column size in our project drawings?",
            project_id=self.proj_b,  # Different project
        )
        assert resp.validation_report is not None
        assert resp.validation_report.unsupported_citations >= 1
        assert resp.validation_report.items[0].status == ValidationStatus.UNAUTHORIZED_PROJECT_REFERENCE

    # 21. Existing high-risk structural routing preservation
    @pytest.mark.asyncio
    async def test_21_existing_high_risk_structural_routing_preservation(self):
        ai_spy = RecordingAIProvider()
        retrieval_spy = RecordingRetrievalService(chunks=[self.global_chunk])
        workflow = ConstructionChatWorkflow(ai_provider=ai_spy, retrieval_service=retrieval_spy)

        # Level 4 CRITICAL query must still bypass AI & retrieval completely
        resp = await workflow.process_user_query("Column mein cracks aa rahe hain, kya building safe hai?")
        assert len(ai_spy.recorded_requests) == 0
        assert len(retrieval_spy.recorded_queries) == 0
        assert resp.context.risk_level == RiskLevel.CRITICAL
        assert "CRITICAL STRUCTURAL SAFETY ALERT" in resp.answer

    # 22. No fabricated source metadata
    def test_22_no_fabricated_source_metadata(self):
        text = "According to LDA Byelaws 2020 Clause 99.4, you must build 10 feet setback."
        items = CitationValidator.validate_inline_regulatory_references(text, evidence_chunks=[self.global_chunk])
        assert len(items) == 1
        assert items[0].status == ValidationStatus.INVALID_CLAUSE
        assert items[0].matched_chunk_id is None

    # 23. No unauthorized document leakage
    def test_23_no_unauthorized_document_leakage(self):
        # A private project chunk must never be validated without the matching project_id
        citations = [{
            "source_code": "PRJ-DOC-01",
            "chunk_id": str(self.chunk_proj_id),
            "project_id": str(self.proj_a),
        }]
        rep = self.validator.validate_citations(citations, [self.project_chunk], project_id=None)
        assert rep.is_fully_grounded is False
        assert rep.unsupported_citations == 1
        assert rep.items[0].status == ValidationStatus.UNAUTHORIZED_PROJECT_REFERENCE
