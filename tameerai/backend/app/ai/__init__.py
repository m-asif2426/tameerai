"""
TameerAI - AI Core Architecture & Foundation (Phase 03A)
Provides provider-independent AI interfaces, structured response contracts,
citation validation, mock implementations, and engineering module blueprints.
"""

from app.ai.contracts.provider import AIProvider, ModelRequest, ModelResponse
from app.ai.contracts.embedding import EmbeddingProvider, EmbeddingRequest, EmbeddingResponse
from app.ai.contracts.retrieval import KnowledgeRetriever, RetrievalQuery, RetrievalResult
from app.ai.schemas.response import AIResponse, SourceCitation, EvidenceExcerpt, ConfidenceLevel, AnalysisType
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.factory import get_ai_provider
from app.ai.validation.citation import CitationValidator

__all__ = [
    "AIProvider",
    "ModelRequest",
    "ModelResponse",
    "EmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "KnowledgeRetriever",
    "RetrievalQuery",
    "RetrievalResult",
    "AIResponse",
    "SourceCitation",
    "EvidenceExcerpt",
    "ConfidenceLevel",
    "AnalysisType",
    "MockAIProvider",
    "get_ai_provider",
    "CitationValidator",
]

