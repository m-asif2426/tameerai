"""
TameerAI - Phase 03G Stage B3.1 Grounded Reliability Hardening & Independent Verification Tests

Deterministic test suite covering all 32 mandatory Stage B3.1 requirements across 6 groups:
Group A: Claim-Evidence Alignment (Tests 1-5)
Group B: Regulatory Verification (Tests 6-9)
Group C: Calculation Verification (Tests 10-19)
Group D: Independent Verification Dimensions (Tests 20-23)
Group E: Material Rate Reliability (Tests 24-27)
Group F: Security & Compatibility (Tests 28-32)
"""

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
from app.ai.contracts.validation import (
    CalculationStatus,
    CitationStatus,
    ClaimRelevanceStatus,
    EvidenceStatus,
    RegulatoryStatus,
    ValidationStatus,
)
from app.ai.guardrails.context_engine import ConstructionContextEngine, RiskLevel
from app.ai.guardrails.domain_guard import ConstructionDomainGuard, DomainCategory
from app.ai.guardrails.entities import ConstructionEntityExtractor
from app.ai.guardrails.intent import ConstructionIntent, ConstructionIntentDetector
from app.ai.guardrails.normalizer import TextNormalizer
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
        source_name: Optional[str] = "Pakistan Bureau of Statistics",
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
# DEDICATED STAGE B3.1 TEST SUITE (Tests 1 to 32)
# =====================================================================

class TestGroundedReliabilityHardening3G:
    """Comprehensive test suite verifying all 32 Stage B3.1 requirements."""

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

    # -----------------------------------------------------------------
    # GROUP A: CLAIM-EVIDENCE ALIGNMENT (Tests 1 to 5)
    # -----------------------------------------------------------------

    def test_01_relevant_evidence_supports_claim(self):
        """1. Relevant evidence genuinely supports the claim."""
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
        assert rep.items[0].claim_relevance_status == ClaimRelevanceStatus.CLAIM_SUPPORTED
        assert rep.items[0].claim_support_verified is True
        assert rep.citation_status == CitationStatus.VALID

    def test_02_valid_citation_with_unrelated_evidence(self):
        """2. Valid citation source exists, but evidence is completely unrelated to claim."""
        # Chunk is about compressive strength 3000 psi; citation claims front setback 10 feet
        citations = [{
            "source_code": "PBC-2021",
            "title": "Building Code of Pakistan 2021",
            "page_number": 45,
            "section_or_clause": "Section 5.1",
            "chunk_id": str(self.chunk_global_id),
            "claim_text": "Building front setback must be 10 feet clearance from the road boundary",
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.is_fully_grounded is False
        assert rep.unsupported_citations == 1
        item = rep.items[0]
        assert item.source_id_matches is True  # Source identity is valid!
        assert item.status == ValidationStatus.UNSUPPORTED_CLAIM
        assert item.claim_relevance_status == ClaimRelevanceStatus.CLAIM_UNSUPPORTED
        assert item.claim_support_verified is False
        assert "does not support" in item.explanation or "does not cover" in item.explanation

    def test_03_partially_supported_claim(self):
        """3. Claim is partially supported by retrieved evidence text."""
        citations = [{
            "source_code": "PRJ-DOC-01",
            "title": "Plaza Drawings",
            "chunk_id": str(self.chunk_proj_id),
            "claim_text": "Column C1 is 12x12 inches with 4 bars, but also requires 8mm stirrups at 4 inches spacing",
        }]
        rep = self.validator.validate_citations(citations, [self.project_chunk], project_id=self.proj_a)
        item = rep.items[0]
        assert item.status == ValidationStatus.VALID
        assert item.claim_relevance_status in (ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED, ClaimRelevanceStatus.CLAIM_SUPPORTED)
        assert rep.citation_status in (CitationStatus.PARTIALLY_SUPPORTED, CitationStatus.VALID)

    def test_04_unsupported_claim(self):
        """4. Claim directly contradicts or is unsupported by evidence parameters."""
        # Chunk has 3000 psi; claim asserts 6000 psi
        citations = [{
            "source_code": "PBC-2021",
            "title": "Building Code of Pakistan 2021",
            "page_number": 45,
            "section_or_clause": "Section 5.1",
            "chunk_id": str(self.chunk_global_id),
            "claim_text": "Minimum specified compressive strength is 6000 psi",
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.items[0].claim_relevance_status == ClaimRelevanceStatus.CLAIM_UNSUPPORTED
        assert rep.items[0].status == ValidationStatus.UNSUPPORTED_CLAIM

    def test_05_ambiguous_evidence_relevance(self):
        """5. Ambiguous claim text returns CLAIM_RELEVANCE_UNVERIFIED without inventing confidence."""
        citations = [{
            "source_code": "PBC-2021",
            "title": "Building Code of Pakistan 2021",
            "page_number": 45,
            "section_or_clause": "Section 5.1",
            "chunk_id": str(self.chunk_global_id),
            "claim_text": "general info",  # Ambiguous/non-technical text
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        item = rep.items[0]
        assert item.claim_relevance_status == ClaimRelevanceStatus.CLAIM_RELEVANCE_UNVERIFIED
        assert item.claim_support_verified is False
        assert rep.citation_status == CitationStatus.RELEVANCE_UNVERIFIED

    # -----------------------------------------------------------------
    # GROUP B: REGULATORY VERIFICATION (Tests 6 to 9)
    # -----------------------------------------------------------------

    def test_06_existing_clause_with_matching_content(self):
        """6. Existing clause matches retrieved content factually."""
        lda_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            source_title="LDA Building Regulations 2020",
            source_code="LDA-2020",
            content="Clause 15.2: Front setback of minimum 10 feet shall be left open to sky for residential plots above 10 marla.",
            page_number=18,
            clause_or_section="Clause 15.2",
            scope=ScopeType.GLOBAL_REGULATORY,
        )
        text = "Under LDA 2020 Clause 15.2, a front setback of minimum 10 feet is required for residential plots."
        items = CitationValidator.validate_inline_regulatory_references(text, [lda_chunk])
        assert len(items) == 1
        assert items[0].status == ValidationStatus.VALID
        assert items[0].claim_relevance_status == ClaimRelevanceStatus.CLAIM_SUPPORTED
        assert items[0].claim_support_verified is True

    def test_07_fabricated_clause_number(self):
        """7. Fabricated regulatory clause number is rejected as INVALID_CLAUSE."""
        lda_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            source_title="LDA Building Regulations 2020",
            source_code="LDA-2020",
            content="Clause 15.2: Front setback of minimum 10 feet.",
            page_number=18,
            clause_or_section="Clause 15.2",
            scope=ScopeType.GLOBAL_REGULATORY,
        )
        text = "As stated in LDA 2020 Clause 99.8, setback can be zero."
        items = CitationValidator.validate_inline_regulatory_references(text, [lda_chunk])
        assert len(items) == 1
        assert items[0].status == ValidationStatus.INVALID_CLAUSE
        assert items[0].claim_relevance_status == ClaimRelevanceStatus.CLAIM_UNSUPPORTED
        assert "not found in any retrieved evidence" in items[0].explanation

    def test_08_existing_clause_with_unsupported_interpretation(self):
        """8. Clause exists but interpretation asserts absolute legal approval without certification."""
        lda_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            source_title="LDA Building Regulations 2020",
            source_code="LDA-2020",
            content="Clause 15.2: Front setback of minimum 10 feet.",
            page_number=18,
            clause_or_section="Clause 15.2",
            scope=ScopeType.GLOBAL_REGULATORY,
        )
        text = "Under LDA 2020 Clause 15.2, this proposed drawing is fully compliant and guaranteed approved."
        items = CitationValidator.validate_inline_regulatory_references(text, [lda_chunk])
        assert len(items) == 1
        assert items[0].status == ValidationStatus.VALID
        # Not marked as fully verified claim because absolute legal compliance cannot be certified
        assert items[0].claim_relevance_status == ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED
        assert items[0].claim_support_verified is False
        assert "cannot be certified by automated text matching" in items[0].explanation

    def test_09_unsupported_compliance_guarantee(self):
        """9. Policy evaluates ungrounded compliance assertion as INTERPRETATION_UNVERIFIED."""
        lda_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            source_title="LDA Building Regulations 2020",
            source_code="LDA-2020",
            content="Clause 15.2: Front setback of minimum 10 feet.",
            page_number=18,
            clause_or_section="Clause 15.2",
            scope=ScopeType.GLOBAL_REGULATORY,
        )
        text = "Under LDA 2020 Clause 15.2, your building design is 100% compliant and certified legal."
        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query="Is my design compliant?",
            response_text=text,
            context=None,
            retrieved_chunks=[lda_chunk],
            citations=[],
            language="en",
        )
        assert eval_rep.regulatory_status == RegulatoryStatus.INTERPRETATION_UNVERIFIED
        assert "Regulatory Note" in eval_rep.annotated_answer

    # -----------------------------------------------------------------
    # GROUP C: CALCULATION VERIFICATION (Tests 10 to 19)
    # -----------------------------------------------------------------

    def test_10_correct_steel_weight(self):
        """10. Correct steel rebar weight matches D^2/162 within 5%."""
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_rebar_weight(12, 0.889)
        assert is_valid is True
        assert abs(exp - 0.8888) < 0.01

        text = "For 12mm rebar, the theoretical weight is 0.89 kg/m."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert audits[0].is_valid is True
        assert audits[0].calculation_status == CalculationStatus.VERIFIED

    def test_11_incorrect_steel_weight(self):
        """11. Incorrect steel rebar weight is flagged as MISMATCH."""
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_rebar_weight(12, 1.45)
        assert is_valid is False

        text = "For 12mm rebar, the theoretical weight is 1.45 kg/m."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert audits[0].is_valid is False
        assert audits[0].calculation_status == CalculationStatus.MISMATCH

    def test_12_correct_concrete_volume(self):
        """12. Correct concrete volume matches L * W * T."""
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_concrete_volume(10, 10, 0.5, 50.0)
        assert is_valid is True
        assert exp == 50.0

        text = "A 10ft x 10ft x 0.5ft concrete volume is 50.0 cft."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert audits[0].is_valid is True
        assert audits[0].calculation_status == CalculationStatus.VERIFIED

    def test_13_incorrect_concrete_volume(self):
        """13. Incorrect concrete volume is flagged as MISMATCH."""
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_concrete_volume(10, 10, 0.5, 85.0)
        assert is_valid is False

        text = "A 10ft x 10ft x 0.5ft concrete volume is 85.0 cft."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert audits[0].is_valid is False
        assert audits[0].calculation_status == CalculationStatus.MISMATCH

    def test_14_incompatible_units(self):
        """14. Incompatible physical units (e.g. volume in sqft) detected as NOT_VERIFIABLE."""
        text = "The total concrete volume is 500 sqft."
        issues = UnitConsistencyAuditor.audit_unit_consistency(text)
        assert len(issues) >= 1
        assert issues[0].is_valid is False
        assert issues[0].calculation_status == CalculationStatus.NOT_VERIFIABLE
        assert "sqft" in issues[0].explanation

    def test_15_missing_dimensions(self):
        """15. 2-dimension volume claim missing thickness flagged as NOT_VERIFIABLE."""
        text = "The 10x20 slab volume is 200 cft."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert any(a.calculation_status == CalculationStatus.NOT_VERIFIABLE for a in audits)
        assert any("Missing thickness" in a.explanation for a in audits)

    def test_16_ambiguous_numerical_parsing(self):
        """16. Ambiguous rebar diameter missing 'mm' unit returns NOT_VERIFIABLE."""
        text = "saria 12 weight is 0.89 kg/m."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert any(a.calculation_status == CalculationStatus.NOT_VERIFIABLE for a in audits)
        assert any("Missing explicit metric unit" in a.explanation for a in audits)

    def test_17_correct_boq_arithmetic(self):
        """17. Correct BOQ multiplication verified using Decimal precision."""
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_boq_arithmetic(100, 1400, 140000)
        assert is_valid is True
        assert exp == 140000.0

        text = "100 bags @ 1400 = PKR 140000."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert audits[0].is_valid is True
        assert audits[0].calculation_status == CalculationStatus.VERIFIED

    def test_18_incorrect_boq_arithmetic(self):
        """18. Incorrect BOQ multiplication flagged as MISMATCH."""
        is_valid, exp, expl = EngineeringFormulaVerifier.verify_boq_arithmetic(100, 1400, 200000)
        assert is_valid is False

        text = "100 bags @ 1400 = PKR 200000."
        audits = EngineeringFormulaVerifier.audit_response_calculations(text)
        assert len(audits) >= 1
        assert audits[0].is_valid is False
        assert audits[0].calculation_status == CalculationStatus.MISMATCH

    def test_19_nominal_mix_assumption_disclosure(self):
        """19. Nominal 1:2:4 formula assumptions and non-structural caveat explicitly documented."""
        assumptions = EngineeringFormulaVerifier.NOMINAL_124_ASSUMPTIONS
        assert "1.54" in assumptions
        assert "1 (cement) + 2 (sand) + 4 (coarse aggregate) = 7" in assumptions
        assert "1.25 cft" in assumptions
        assert "0.176" in assumptions
        assert "NOT a substitute for codified structural mix design" in assumptions

        is_valid, exp, expl = EngineeringFormulaVerifier.verify_cement_bags_nominal_124(50.0, 8.8)
        assert is_valid is True
        assert abs(exp - 8.8) < 0.1

    # -----------------------------------------------------------------
    # GROUP D: INDEPENDENT VERIFICATION DIMENSIONS (Tests 20 to 23)
    # -----------------------------------------------------------------

    def test_20_correct_calculation_with_insufficient_documentary_evidence(self):
        """20. Correct calculation with zero evidence chunks yields CALCULATION=VERIFIED and EVIDENCE=INSUFFICIENT."""
        query = "Calculate 12mm rebar weight"
        response_text = "For 12mm rebar, the theoretical weight is 0.89 kg/m."
        norm = TextNormalizer.normalize(query)
        intent = ConstructionIntentDetector.detect_intent(norm).primary_intent
        context = ConstructionContextEngine.analyze_context(norm, intent, [], "en")

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=context,
            retrieved_chunks=[],  # Zero documents!
            citations=[],
            language="en",
        )
        # Independent orthogonal statuses
        assert eval_rep.calculation_status == CalculationStatus.VERIFIED
        assert eval_rep.evidence_status == EvidenceStatus.INSUFFICIENT
        assert eval_rep.tier == EvidenceTier.CALCULATION_VERIFIED  # Backward compatibility

    def test_21_valid_citation_with_unsupported_calculation(self):
        """21. Valid citation but incorrect calculation yields CITATION=VALID and CALCULATION=MISMATCH."""
        query = "What is the cement cost for plaza?"
        response_text = "Drawing PRJ-DOC-01 indicates 100 bags @ 1400 = PKR 200000."
        citations = [{
            "source_code": "PRJ-DOC-01",
            "title": "Plaza Drawings",
            "chunk_id": str(self.chunk_proj_id),
            "claim_text": "General Notes specify column C1 dimensions",
        }]

        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query=query,
            response_text=response_text,
            context=None,
            retrieved_chunks=[self.project_chunk],
            citations=citations,
            project_id=self.proj_a,
            language="en",
        )
        assert eval_rep.citation_status == CitationStatus.VALID
        assert eval_rep.calculation_status == CalculationStatus.MISMATCH
        assert "Calculation Alert" in eval_rep.annotated_answer

    def test_22_valid_clause_with_unverified_compliance_interpretation(self):
        """22. Valid clause with ungrounded compliance guarantee yields REGULATORY=INTERPRETATION_UNVERIFIED."""
        lda_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            source_title="LDA Building Regulations 2020",
            source_code="LDA-2020",
            content="Clause 15.2: Front setback of minimum 10 feet shall be left open.",
            page_number=18,
            clause_or_section="Clause 15.2",
            scope=ScopeType.GLOBAL_REGULATORY,
        )
        text = "Under LDA 2020 Clause 15.2, your building design is guaranteed approved."
        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query="Check LDA compliance",
            response_text=text,
            context=None,
            retrieved_chunks=[lda_chunk],
            citations=[],
            language="en",
        )
        assert eval_rep.regulatory_status == RegulatoryStatus.INTERPRETATION_UNVERIFIED
        assert eval_rep.evidence_status == EvidenceStatus.PARTIALLY_SUPPORTED

    def test_23_independent_status_reporting(self):
        """23. GroundedResponseEvaluation provides all 4 orthogonal dimensions simultaneously."""
        eval_rep = GroundedResponsePolicy.evaluate_grounding(
            query="General civil advice",
            response_text="General construction without specific numbers.",
            context=None,
            retrieved_chunks=[],
            citations=[],
            language="en",
        )
        assert isinstance(eval_rep.evidence_status, EvidenceStatus)
        assert isinstance(eval_rep.calculation_status, CalculationStatus)
        assert isinstance(eval_rep.regulatory_status, RegulatoryStatus)
        assert isinstance(eval_rep.citation_status, CitationStatus)
        assert isinstance(eval_rep.tier, EvidenceTier)

    # -----------------------------------------------------------------
    # GROUP E: MATERIAL RATE RELIABILITY (Tests 24 to 27)
    # -----------------------------------------------------------------

    def test_24_fresh_verified_rate(self):
        """24. Fresh verified rate (<90 days, authoritative source) passes audit."""
        rate = MockMaterialRate(
            name="Ordinary Portland Cement",
            category="cement",
            city="Lahore",
            rate_pkr=1400.0,
            unit="per bag",
            observed_at=datetime.now(timezone.utc) - timedelta(days=15),
            source_name="Pakistan Bureau of Statistics",
            verification_status="verified",
        )
        text = "Current cement rate is PKR 1400 per bag in Lahore."
        rep = MaterialRateReliabilityVerifier.audit_material_rates(text, [rate])
        assert rep.has_price_claims is True
        assert rep.is_reliable is True
        assert len(rep.stale_rates_detected) == 0
        assert len(rep.missing_sources) == 0

    def test_25_stale_rate(self):
        """25. Stale material rate (>90 days old) flagged as unreliable."""
        rate = MockMaterialRate(
            name="Deformed Steel Bar",
            category="steel",
            city="Lahore",
            rate_pkr=260.0,
            unit="per kg",
            observed_at=datetime.now(timezone.utc) - timedelta(days=120),  # 120 days old!
            source_name="Pakistan Bureau of Statistics",
            verification_status="verified",
        )
        text = "Current steel rate is PKR 260 per kg."
        rep = MaterialRateReliabilityVerifier.audit_material_rates(text, [rate])
        assert rep.has_price_claims is True
        assert rep.is_reliable is False
        assert len(rep.stale_rates_detected) >= 1

    def test_26_missing_source(self):
        """26. Price claim lacking authoritative source flagged as unverified estimate."""
        rate = MockMaterialRate(
            name="Deformed Steel Bar",
            category="steel",
            city="Lahore",
            rate_pkr=260.0,
            unit="per kg",
            observed_at=datetime.now(timezone.utc) - timedelta(days=10),
            source_name=None,  # Missing source!
            verification_status="unverified",
        )
        text = "Current steel rate is PKR 260 per kg."
        rep = MaterialRateReliabilityVerifier.audit_material_rates(text, [rate])
        assert rep.is_reliable is False
        assert len(rep.missing_sources) >= 1

    def test_27_missing_currency_or_unit(self):
        """27. Price claim missing currency or standard measurement unit is flagged."""
        text = "The cement rate is 1400 in the local market."
        rep = MaterialRateReliabilityVerifier.audit_material_rates(text, [])
        assert rep.has_price_claims is True
        assert rep.is_reliable is False
        assert any("lacks explicit currency" in d.explanation for d in rep.details)

    # -----------------------------------------------------------------
    # GROUP F: SECURITY AND COMPATIBILITY (Tests 28 to 32)
    # -----------------------------------------------------------------

    def test_28_cross_project_citation_rejection(self):
        """28. Attempting to cite another project's private document is rejected."""
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

    def test_29_fabricated_chunk_rejection(self):
        """29. Fabricated chunk UUID not present in evidence is rejected."""
        fake_uuid = uuid4()
        citations = [{
            "source_code": "PBC-2021",
            "chunk_id": str(fake_uuid),
            "title": "Fabricated Chunk",
        }]
        rep = self.validator.validate_citations(citations, [self.global_chunk])
        assert rep.is_fully_grounded is False
        assert rep.items[0].status == ValidationStatus.INVALID_CHUNK_ID

    @pytest.mark.asyncio
    async def test_30_existing_high_risk_structural_routing_preservation(self):
        """30. Severe structural distress query safely triggers emergency advisory without AI call."""
        ai_spy = RecordingAIProvider()
        workflow = ConstructionChatWorkflow(ai_provider=ai_spy)
        query = "Main column burst ho gaya aur concrete gir raha hai"
        resp = await workflow.process_user_query(query)
        assert resp.domain_category == DomainCategory.CONSTRUCTION_RELATED
        assert len(ai_spy.recorded_requests) == 0  # No AI generation called
        assert "STRUCTURAL SAFETY ALERT" in resp.disclaimer.upper() or "PEC" in resp.disclaimer.upper()

    def test_31_existing_multilingual_response_preservation(self):
        """31. Localized disclosure notices in English, Roman Urdu, and Urdu script are correctly formatted."""
        en_note = GroundedResponsePolicy.get_unverified_calculation_note("en")
        ur_roman_note = GroundedResponsePolicy.get_unverified_calculation_note("roman_ur")
        ur_note = GroundedResponsePolicy.get_unverified_calculation_note("ur")

        assert "Calculation Note" in en_note
        assert "Hisab Ki Hidayat" in ur_roman_note
        assert "حساب کا انتباہ" in ur_note

    @pytest.mark.asyncio
    async def test_32_existing_api_contract_compatibility(self):
        """32. ConstructionChatResponse maintains all existing fields and telemetry while adding 4 dimensions."""
        ai_spy = RecordingAIProvider("For 12mm rebar, the weight is 0.89 kg/m.")
        workflow = ConstructionChatWorkflow(ai_provider=ai_spy)
        query = "What is the weight of 12mm rebar?"
        resp = await workflow.process_user_query(query)

        # Legacy fields
        assert hasattr(resp, "evidence_tier")
        assert resp.evidence_tier is not None
        assert hasattr(resp, "is_grounded")
        assert hasattr(resp, "citations")
        assert hasattr(resp, "disclaimer")

        # Phase 03G Stage B3.1 additions
        assert hasattr(resp, "evidence_status")
        assert hasattr(resp, "calculation_status")
        assert hasattr(resp, "regulatory_status")
        assert hasattr(resp, "citation_status")

        # Telemetry payload
        assert "evidence_status" in resp.telemetry
        assert "calculation_status" in resp.telemetry
        assert "regulatory_status" in resp.telemetry
        assert "citation_status" in resp.telemetry
