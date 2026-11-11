"""
TameerAI - Synthetic End-to-End AI Advisory Prototype (Phase 03A)
Executes a fully isolated, deterministic, in-memory pipeline:
User Query -> Mock Retrieval -> Mock AI Provider -> Structured AI Response -> Citation Validation -> Final Advisory
Validates architecture contracts and integration interfaces without network calls.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from app.ai.contracts.provider import ModelRequest, ChatMessageInput
from app.ai.contracts.retrieval import RetrievedChunk, ScopeType
from app.ai.schemas.response import (
    AIResponse,
    SourceCitation,
    EvidenceExcerpt,
    ConfidenceLevel,
    AnalysisType,
    HumanReviewRequirement,
    WarningCard,
)
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.validation.citation import CitationValidator


async def run_synthetic_advisory_pipeline(
    user_query: str,
    project_id: Optional[UUID] = None,
    mock_provider: Optional[MockAIProvider] = None,
    custom_evidence: Optional[List[RetrievedChunk]] = None,
) -> Dict[str, Any]:
    """
    Executes the deterministic prototype pipeline.
    
    Stages:
    1. Input validation.
    2. Synthetic grounded retrieval generation.
    3. AI provider execution requesting structured AIResponse schema.
    4. Citation validation against retrieved evidence.
    5. Final assembly with validation report.
    """
    if not user_query or not user_query.strip():
        raise ValueError("User query cannot be empty.")

    provider = mock_provider or MockAIProvider()
    validator = CitationValidator()

    # Stage 1: Synthetic Knowledge Retrieval
    # Uses explicitly designated fictional test fixtures to validate retrieval/citation mechanics
    chunk_1_id = uuid4()
    evidence = custom_evidence or [
        RetrievedChunk(
            chunk_id=chunk_1_id,
            source_title="[SYNTHETIC FIXTURE] Mock Pakistan Building Code 2021",
            source_code="PBC-2021",
            content="[SYNTHETIC FIXTURE] Commercial multi-storey test parameter: front setback not less than 30 feet.",
            page_number=45,
            clause_or_section="Section 4.2",
            scope=ScopeType.GLOBAL_REGULATORY,
            relevance_score=0.95,
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            source_title="[SYNTHETIC FIXTURE] Mock Municipal Bylaws 2019",
            source_code="LDA-2019",
            content="[SYNTHETIC FIXTURE] Commercial high-rise test parameter: mandatory side spaces of at least 15 feet.",
            page_number=18,
            clause_or_section="Bylaw 12.3",
            scope=ScopeType.GLOBAL_REGULATORY,
            relevance_score=0.88,
        )
    ]

    # Stage 2: AI Provider Execution
    request = ModelRequest(
        messages=[
            ChatMessageInput(
                role="system",
                content=(
                    "You are TameerAI's Building Code Advisory Assistant. Ground all answers strictly in the "
                    "provided retrieved evidence. Distinguish clearly between advisory guidance and certified decisions."
                )
            ),
            ChatMessageInput(
                role="user",
                content=user_query
            )
        ],
        temperature=0.2,
        max_tokens=2048,
    )

    ai_response = await provider.generate_structured(request, AIResponse)

    # Stage 3: Citation Validation
    citations_data = [c.model_dump() for c in ai_response.citations]
    validation_report = validator.validate_citations(citations_data, evidence)

    # Stage 4: Mark citations as verified if validation passed
    for cit in ai_response.citations:
        # Check if this citation is valid in report
        matching_report_item = next(
            (item for item in validation_report.items if item.source_code == cit.source_code),
            None
        )
        if matching_report_item and matching_report_item.status.value == "valid":
            cit.verified_against_retrieval = True

    return {
        "query": user_query,
        "retrieved_evidence_count": len(evidence),
        "ai_response": ai_response,
        "validation_report": validation_report,
        "is_advisory_ready": validation_report.is_fully_grounded,
        "is_synthetic_test": True,
        "grounding_disclaimer": (
            "Verification confirms structural matching against synthetic test fixtures only; "
            "it does not assert or imply official regulatory approval or professional engineering sign-off."
        ),
    }

