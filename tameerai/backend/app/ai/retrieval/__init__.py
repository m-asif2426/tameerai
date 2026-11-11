"""
TameerAI - Retrieval Engine Exports (Phase 03C)
"""

from app.ai.contracts.retrieval import (
    KnowledgeRetriever,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    ScopeType,
)
from app.ai.retrieval.keyword import KeywordRetriever, tokenize
from app.ai.retrieval.vector import InMemoryVectorRetriever, cosine_similarity
from app.ai.retrieval.hybrid import HybridRetriever
from app.ai.retrieval.reranker import ReRankerProtocol, CrossEncoderMockReRanker
from app.ai.retrieval.service import ScopedRetrievalService

__all__ = [
    "KnowledgeRetriever",
    "RetrievalQuery",
    "RetrievalResult",
    "RetrievedChunk",
    "ScopeType",
    "KeywordRetriever",
    "tokenize",
    "InMemoryVectorRetriever",
    "cosine_similarity",
    "HybridRetriever",
    "ReRankerProtocol",
    "CrossEncoderMockReRanker",
    "ScopedRetrievalService",
]

