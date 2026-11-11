"""
TameerAI - Retrieval Re-Ranking Contracts & Mock Implementation (Phase 03C)
Defines protocol contracts and a deterministic local cross-encoder re-ranker
for second-stage precision filtering of candidate retrieval chunks.
"""

import math
import re
import time
from typing import List, Optional, Protocol, runtime_checkable

from app.ai.contracts.retrieval import RetrievedChunk


@runtime_checkable
class ReRankerProtocol(Protocol):
    """Protocol for re-ranking candidate retrieval chunks."""
    async def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        ...


class CrossEncoderMockReRanker(ReRankerProtocol):
    """
    Deterministic mock cross-encoder re-ranker.
    Simulates second-stage neural cross-attention re-ranking by computing
    exact token co-occurrence, proximity, and structural clause alignment.
    """

    def __init__(self, model_name: str = "mock-bge-reranker-large"):
        self.model_name = model_name

    def _score_candidate(self, query: str, chunk: RetrievedChunk) -> float:
        """Computes deep lexical and structural relevance score."""
        q_tokens = set(re.findall(r"\b\w+\b", query.lower()))
        if not q_tokens:
            return 0.0

        content_lower = chunk.content.lower()
        c_tokens = re.findall(r"\b\w+\b", content_lower)
        if not c_tokens:
            return 0.0

        # Term overlap
        matches = sum(1 for t in q_tokens if t in content_lower)
        overlap_ratio = matches / len(q_tokens)

        # Clause / section match boost
        clause_boost = 0.0
        if chunk.clause_or_section and any(t in chunk.clause_or_section.lower() for t in q_tokens):
            clause_boost = 0.25

        # Code match boost
        code_boost = 0.0
        if chunk.source_code and chunk.source_code.lower() in query.lower():
            code_boost = 0.20

        # Base retrieval score consideration
        base_weight = 0.3 * chunk.relevance_score

        # Combine
        raw_score = 0.5 * overlap_ratio + clause_boost + code_boost + base_weight
        return min(1.0, max(0.0, raw_score))

    async def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        start_time = time.monotonic()
        if not candidates:
            return []

        scored_candidates: List[RetrievedChunk] = []
        for cand in candidates:
            rerank_score = round(self._score_candidate(query, cand), 4)
            # Clone candidate with updated score and reranker metadata
            updated = cand.model_copy(deep=True)
            updated.relevance_score = rerank_score
            updated.metadata["reranked_by"] = self.model_name
            updated.metadata["pre_rerank_score"] = cand.relevance_score
            scored_candidates.append(updated)

        # Sort descending by re-ranked score
        scored_candidates.sort(key=lambda c: c.relevance_score, reverse=True)

        limit = top_k if top_k is not None else len(scored_candidates)
        return scored_candidates[:limit]

