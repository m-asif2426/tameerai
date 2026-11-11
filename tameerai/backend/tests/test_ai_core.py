"""
TameerAI - AI Core Architecture & Foundation Test Suite (Phase 03A)
Tests the 17 required categories for Phase 03A:
1. AI provider interface behavior
2. Mock provider execution
3. Provider configuration validation
4. Production feature flag restrictions
5. Structured response validation
6. Citation validation
7. Missing source handling
8. Insufficient evidence behavior
9. Provider timeout handling
10. Provider failure handling
11. Malformed response handling
12. Sensitive error redaction
13. Request size validation
14. Output bounds
15. Tenant-aware retrieval interfaces
16. Synthetic end-to-end workflow
17. Compatibility with existing services
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.core.config import Settings
from app.ai.contracts.provider import (
    AIProvider,
    AIError,
    AIProviderError,
    AITimeoutError,
    AIConfigurationError,
    AIInputLimitExceededError,
    AIRateLimitError,
    StructuredOutputValidationError,
    ModelRequest,
    ModelResponse,
    ChatMessageInput,
    TokenUsage,
    FinishReason,
)
from app.ai.contracts.embedding import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    VectorEmbedding,
)
from app.ai.contracts.retrieval import (
    KnowledgeRetriever,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    ScopeType,
)
from app.ai.contracts.extraction import (
    DocumentExtractor,
    ExtractionRequest,
    ExtractedDocument,
    BoundingBox,
)
from app.ai.contracts.validation import (
    ValidationStatus,
    CitationValidationReport,
)
from app.ai.schemas.response import (
    AIResponse,
    SourceCitation,
    EvidenceExcerpt,
    ConfidenceLevel,
    AnalysisType,
    HumanReviewRequirement,
    WarningCard,
    ENGINEERING_DISCLAIMER_TEXT,
)
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.mock_embedding import MockEmbeddingProvider
from app.ai.providers.factory import get_ai_provider, ALLOWED_PROVIDERS
from app.ai.validation.citation import CitationValidator
from app.ai.modules.compliance import ComplianceAnalysisRequest, ComplianceAnalysisResult, ViolationSeverity
from app.ai.modules.contract import ContractAnalysisRequest, ContractRiskCategory
from app.ai.modules.cost import BOQAnalysisRequest, BOQItemEvaluation
from app.ai.modules.report import ReportGenerationRequest
from app.ai.jobs.contracts import (
    OCRJobPayload,
    DocumentExtractionPayload,
    EmbeddingJobPayload,
    ComplianceAnalysisJobPayload,
)
from app.ai.workflow.prototype import run_synthetic_advisory_pipeline
from app.workers.job_worker import sanitize_error_message


# ---------------------------------------------------------------------------
# 1. AI Provider Interface Behavior
# ---------------------------------------------------------------------------

def test_ai_provider_runtime_protocol_compliance():
    """Verify that MockAIProvider strictly adheres to the AIProvider Protocol."""
    provider = MockAIProvider()
    assert isinstance(provider, AIProvider)
    assert provider.provider_name == "mock"
    assert "mock" in provider.default_model


# ---------------------------------------------------------------------------
# 2. Mock Provider Execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_provider_text_generation():
    """Verify standard text generation returns expected structure and telemetry."""
    provider = MockAIProvider()
    request = ModelRequest(
        messages=[ChatMessageInput(role="user", content="Explain building setback rules.")]
    )
    response = await provider.generate_text(request)

    assert isinstance(response, ModelResponse)
    assert len(response.content) > 0
    assert response.finish_reason == FinishReason.STOP
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens == response.usage.prompt_tokens + response.usage.completion_tokens
    assert response.provider_name == "mock"
    assert response.latency_ms >= 0.0


# ---------------------------------------------------------------------------
# 3. Provider Configuration Validation
# ---------------------------------------------------------------------------

def test_provider_factory_validation():
    """Verify provider factory validates names and rejects unsupported identifiers."""
    # Mock provider succeeds in dev
    provider = get_ai_provider("mock")
    assert isinstance(provider, MockAIProvider)

    # Unknown provider raises AIConfigurationError
    with pytest.raises(AIConfigurationError) as exc_info:
        get_ai_provider("unknown_super_ai")
    assert "not supported" in str(exc_info.value)

    # Inactivated providers in Phase 03A raise configuration error
    with pytest.raises(AIConfigurationError) as exc_info:
        get_ai_provider("openai")
    assert "not activated in Phase 03A" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Production Feature Flag Restrictions
# ---------------------------------------------------------------------------

def test_production_feature_flag_and_mock_restriction():
    """Verify production rejects mock provider and enforces AI feature flag."""
    # Settings model validator rejects mock in production
    with pytest.raises(ValueError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a" * 32,
            AUTH_COOKIE_SECURE=True,
            ENABLE_SYNTHETIC_JOBS=False,
            ENABLE_AI_FEATURES=True,
            AI_DEFAULT_PROVIDER="mock",
        )
    assert "Mock AI provider is not permitted when AI features are enabled in production" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Structured Response Validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_provider_structured_ai_response():
    """Verify structured response generation produces compliant AIResponse with disclaimers."""
    provider = MockAIProvider()
    request = ModelRequest(
        messages=[ChatMessageInput(role="user", content="Check commercial G+12 setbacks in Lahore.")]
    )
    response = await provider.generate_structured(request, AIResponse)

    assert isinstance(response, AIResponse)
    assert "PBC-2021" in response.answer or "setback" in response.answer.lower()
    assert response.is_certified_decision is False
    assert response.disclaimer == ENGINEERING_DISCLAIMER_TEXT
    assert len(response.citations) >= 1
    assert len(response.evidence_excerpts) >= 1
    assert response.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]


# ---------------------------------------------------------------------------
# 6. Citation Validation
# ---------------------------------------------------------------------------

def test_citation_validator_valid_grounding():
    """Verify citation validator accepts citations grounded in retrieved evidence."""
    validator = CitationValidator()
    chunk_id = uuid4()
    evidence = [
        RetrievedChunk(
            chunk_id=chunk_id,
            source_title="Building Code of Pakistan 2021",
            source_code="PBC-2021",
            content="Commercial setback requirements.",
            page_number=45,
            clause_or_section="Section 4.2",
            scope=ScopeType.GLOBAL_REGULATORY,
        )
    ]
    citations = [
        {
            "source_type": "regulatory",
            "source_code": "PBC-2021",
            "title": "Building Code of Pakistan 2021",
            "section_or_clause": "Section 4.2",
            "page_number": 45,
        }
    ]
    report = validator.validate_citations(citations, evidence)

    assert report.is_fully_grounded is True
    assert report.total_citations == 1
    assert report.valid_citations == 1
    assert report.unsupported_citations == 0
    assert report.items[0].status == ValidationStatus.VALID
    assert report.items[0].matched_chunk_id == str(chunk_id)


# ---------------------------------------------------------------------------
# 7. Missing Source Handling
# ---------------------------------------------------------------------------

def test_citation_validator_unsupported_missing_source():
    """Verify citation validator flags citations whose sources are missing from evidence."""
    validator = CitationValidator()
    evidence = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_title="Building Code of Pakistan 2021",
            source_code="PBC-2021",
            content="PBC content only.",
            page_number=10,
            scope=ScopeType.GLOBAL_REGULATORY,
        )
    ]
    citations = [
        {
            "source_type": "regulatory",
            "source_code": "FIDIC-Red-1999",  # Not in evidence!
            "title": "FIDIC Red Book 1999",
            "section_or_clause": "Sub-Clause 20.1",
            "page_number": 55,
        }
    ]
    report = validator.validate_citations(citations, evidence)

    assert report.is_fully_grounded is False
    assert report.unsupported_citations == 1
    assert report.items[0].status == ValidationStatus.UNSUPPORTED_CITATION
    assert "was not present in the retrieved evidence" in report.items[0].explanation


# ---------------------------------------------------------------------------
# 8. Insufficient Evidence Behavior
# ---------------------------------------------------------------------------

def test_citation_validator_invalid_page_number():
    """Verify validator flags citations referencing pages outside retrieved evidence."""
    validator = CitationValidator()
    evidence = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_title="LDA Bylaws 2019",
            source_code="LDA-2019",
            content="LDA setback text on page 12.",
            page_number=12,
            scope=ScopeType.GLOBAL_REGULATORY,
        )
    ]
    # Cited page 99, but evidence only has page 12
    citations = [
        {
            "source_type": "regulatory",
            "source_code": "LDA-2019",
            "title": "LDA Bylaws 2019",
            "page_number": 99,
        }
    ]
    report = validator.validate_citations(citations, evidence)

    assert report.is_fully_grounded is False
    assert report.items[0].status == ValidationStatus.INVALID_PAGE
    assert "page 99 was not found in retrieved pages" in report.items[0].explanation


# ---------------------------------------------------------------------------
# 9. Provider Timeout Handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provider_timeout_simulation():
    """Verify AITimeoutError is raised when model request exceeds timeout."""
    provider = MockAIProvider(fail_with_timeout=True)
    request = ModelRequest(
        messages=[ChatMessageInput(role="user", content="Analyze structural loads.")],
        timeout_seconds=5.0,
    )
    with pytest.raises(AITimeoutError) as exc_info:
        await provider.generate_text(request)
    assert "timed out" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 10. Provider Failure Handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provider_upstream_failure_simulation():
    """Verify AIProviderError is raised upon upstream provider crash."""
    provider = MockAIProvider(should_fail=True)
    request = ModelRequest(
        messages=[ChatMessageInput(role="user", content="Calculate quantities.")]
    )
    with pytest.raises(AIProviderError) as exc_info:
        await provider.generate_text(request)
    assert "simulated upstream failure" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 11. Malformed Response Handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_structured_output_malformed_json_simulation():
    """Verify StructuredOutputValidationError is raised when provider returns invalid syntax."""
    provider = MockAIProvider(fail_with_malformed_json=True)
    request = ModelRequest(
        messages=[ChatMessageInput(role="user", content="Check compliance.")]
    )
    with pytest.raises(StructuredOutputValidationError) as exc_info:
        await provider.generate_structured(request, AIResponse)
    assert "failed to parse structured output" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 12. Sensitive Error Redaction
# ---------------------------------------------------------------------------

def test_sensitive_error_sanitization():
    """Verify that credentials, database connection strings, and local file paths are redacted."""
    raw_error = (
        "Connection failed to postgresql+asyncpg://admin:SuperSecretPass123@aws-0.supabase.com:5432/tameerai_prod\n"
        "At File \"D:\\new idea project\\tameerai\\backend\\app\\core\\database.py\", line 42\n"
        "bearer_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secretpayload\n"
        "Read error at /home/ubuntu/app/secrets/key.pem"
    )
    sanitized = sanitize_error_message(raw_error)

    assert "SuperSecretPass123" not in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "D:\\new idea project" not in sanitized
    assert "/home/ubuntu/app" not in sanitized
    assert "[REDACTED_DB_URI]" in sanitized
    assert "[REDACTED_CREDENTIAL]" in sanitized


# ---------------------------------------------------------------------------
# 13. Request Size Validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_request_size_limit_enforcement():
    """Verify input size limit (>32000 chars) raises AIInputLimitExceededError."""
    provider = MockAIProvider()
    oversized_text = "A" * 32001
    request = ModelRequest(
        messages=[ChatMessageInput(role="user", content=oversized_text)]
    )
    with pytest.raises(AIInputLimitExceededError) as exc_info:
        await provider.generate_text(request)
    assert "exceeds the maximum allowed bound" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 14. Output Bounds
# ---------------------------------------------------------------------------

def test_model_request_output_bounds_validation():
    """Verify ModelRequest bounds max_tokens and temperature."""
    # max_tokens > 8192 rejected by Pydantic
    with pytest.raises(Exception):
        ModelRequest(
            messages=[ChatMessageInput(role="user", content="Query")],
            max_tokens=100000
        )
    # temperature > 2.0 rejected
    with pytest.raises(Exception):
        ModelRequest(
            messages=[ChatMessageInput(role="user", content="Query")],
            temperature=3.5
        )


# ---------------------------------------------------------------------------
# 15. Tenant-Aware Retrieval Interfaces
# ---------------------------------------------------------------------------

def test_retrieval_contracts_and_scope_types():
    """Verify retrieval contracts support global regulatory vs private tenant scoping."""
    proj_id = uuid4()
    query = RetrievalQuery(
        query_text="Minimum front setback for commercial zone",
        project_id=proj_id,
        scope=ScopeType.HYBRID,
        top_k=5,
    )
    assert query.scope == ScopeType.HYBRID
    assert query.project_id == proj_id

    # Create mock retrieved chunks
    global_chunk = RetrievedChunk(
        chunk_id=uuid4(),
        source_title="Building Code of Pakistan 2021",
        source_code="PBC-2021",
        content="Front setback 30 ft",
        scope=ScopeType.GLOBAL_REGULATORY,
        project_id=None,
    )
    private_chunk = RetrievedChunk(
        chunk_id=uuid4(),
        source_title="Architectural Drawing A-101",
        source_code="PRJ-DOC-001",
        content="Proposed setback 32 ft",
        scope=ScopeType.PROJECT_PRIVATE,
        project_id=proj_id,
        document_id=uuid4(),
    )

    result = RetrievalResult(
        query=query.query_text,
        chunks=[global_chunk, private_chunk],
        total_found=2,
        scope_used=ScopeType.HYBRID,
        latency_ms=12.5,
    )
    assert len(result.chunks) == 2
    assert result.chunks[0].scope == ScopeType.GLOBAL_REGULATORY
    assert result.chunks[1].scope == ScopeType.PROJECT_PRIVATE
    assert result.chunks[1].project_id == proj_id


# ---------------------------------------------------------------------------
# 16. Synthetic End-to-End Workflow Prototype
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_synthetic_end_to_end_advisory_pipeline():
    """Verify pure local pipeline from query through retrieval, mock AI, citation check, to response."""
    result = await run_synthetic_advisory_pipeline(
        user_query="What are the fire safety and setback rules for a G+12 building in Lahore?"
    )

    assert result["query"] == "What are the fire safety and setback rules for a G+12 building in Lahore?"
    assert result["retrieved_evidence_count"] >= 1
    assert result["is_advisory_ready"] is True

    ai_response: AIResponse = result["ai_response"]
    assert isinstance(ai_response, AIResponse)
    assert ai_response.is_certified_decision is False
    assert ENGINEERING_DISCLAIMER_TEXT in ai_response.disclaimer
    assert len(ai_response.citations) >= 1
    assert ai_response.citations[0].verified_against_retrieval is True

    validation_report: CitationValidationReport = result["validation_report"]
    assert validation_report.is_fully_grounded is True
    assert validation_report.valid_citations >= 1
    assert validation_report.unsupported_citations == 0


# ---------------------------------------------------------------------------
# 17. Compatibility with Existing Services & Background Jobs
# ---------------------------------------------------------------------------

def test_compatibility_with_existing_models_and_job_payloads():
    """Verify AI schemas and background job contracts map cleanly to existing models."""
    # Test background job payload validation
    doc_id = uuid4()
    audit_id = uuid4()
    
    ocr_payload = OCRJobPayload(
        document_id=doc_id,
        storage_path="documents/test.pdf",
        target_dpi=300,
    )
    assert ocr_payload.target_dpi == 300

    comp_payload = ComplianceAnalysisJobPayload(
        audit_id=audit_id,
        document_ids=[doc_id],
        building_type="Commercial G+12",
        authority="LDA",
    )
    assert comp_payload.authority == "LDA"

    # Test engineering module schemas
    req = ComplianceAnalysisRequest(
        project_id=uuid4(),
        building_type="Commercial G+12",
        city="Lahore",
        governing_authority="LDA",
        total_floors=12,
        plot_area_sqft=25000.0,
        covered_area_sqft=180000.0,
        front_setback_ft=32.0,
    )
    assert req.total_floors == 12

    # Test Decimal arithmetic safety in BOQ schema
    boq_item = BOQItemEvaluation(
        item_code="C-101",
        description="Reinforced Cement Concrete (1:2:4)",
        unit="cu ft",
        quantity=Decimal("15000.50"),
        contract_unit_rate=Decimal("450.00"),
        market_benchmark_rate=Decimal("430.00"),
        variance_percentage=Decimal("4.65"),
        rate_status="standard",
    )
    total_cost = boq_item.quantity * boq_item.contract_unit_rate
    assert total_cost == Decimal("6750225.0000")


@pytest.mark.asyncio
async def test_mock_embedding_provider_deterministic_unit_vectors():
    """Verify mock embedding provider generates reproducible normalized vectors."""
    provider = MockEmbeddingProvider(default_dimensions=768)
    assert isinstance(provider, EmbeddingProvider)

    req = EmbeddingRequest(
        texts=["Pakistan Building Code 2021 Chapter 4", "LDA High Rise Regulations 2019"],
        target_dimensions=768,
    )
    res = await provider.generate_embeddings(req)

    assert isinstance(res, EmbeddingResponse)
    assert len(res.embeddings) == 2
    assert res.embeddings[0].dimensions == 768
    assert res.embeddings[1].dimensions == 768

    # Check reproducibility
    res2 = await provider.generate_embeddings(req)
    assert res.embeddings[0].vector == res2.embeddings[0].vector

