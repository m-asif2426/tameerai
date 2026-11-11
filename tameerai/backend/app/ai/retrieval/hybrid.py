"""
TameerAI - Hybrid Retrieval Engine (Phase 03C)
Merges BM25 lexical search and semantic vector similarity using Reciprocal Rank Fusion (RRF)
and Weighted Score Fusion for superior regulatory and contract retrieval.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.ai.contracts.chunking import StructuredChunk
from app.ai.retrieval.keyword import KeywordRetriever
from app.ai.retrieval.vector import InMemoryVectorRetriever


class HybridRetriever:
    """
    Combines dense semantic vector retrieval with sparse BM25 lexical retrieval.
    Applies Reciprocal Rank Fusion (RRF) to eliminate scoring scale disparities.
    """

    def __init__(
        self,
        vector_retriever: InMemoryVectorRetriever,
        keyword_retriever: Optional[KeywordRetriever] = None,
        rrf_k: int = 60,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever or KeywordRetriever()
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    def retrieve_hybrid(
        self,
        query: str,
        query_vector: List[float],
        candidate_chunks: List[StructuredChunk],
        top_k: int = 10,
        minimum_score: float = 0.0,
        use_rrf: bool = True,
    ) -> List[Tuple[StructuredChunk, float]]:
        """
        Executes both lexical and semantic searches and fuses results.
        Returns ranked list of (StructuredChunk, fused_score).
        """
        if not candidate_chunks:
            return []

        # 1. Lexical retrieval
        keyword_results = self.keyword_retriever.search(
            query=query,
            chunks=candidate_chunks,
            top_k=len(candidate_chunks),
            minimum_score=0.0,
        )

        # 2. Vector retrieval
        vector_results = self.vector_retriever.search(
            query_vector=query_vector,
            top_k=len(candidate_chunks),
            minimum_score=0.0,
            filter_chunks=candidate_chunks,
        )

        # 3. Fusion
        chunk_map: Dict[UUID, StructuredChunk] = {c.id: c for c in candidate_chunks}
        fused_scores: Dict[UUID, float] = {}

        if use_rrf:
            # Reciprocal Rank Fusion
            # Rank is 1-based index
            for rank, (chunk, _) in enumerate(vector_results, start=1):
                fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + (
                    self.vector_weight / (self.rrf_k + rank)
                )

            for rank, (chunk, _) in enumerate(keyword_results, start=1):
                fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + (
                    self.keyword_weight / (self.rrf_k + rank)
                )

            # Normalize RRF scores by the maximum possible single-source score
            max_possible = (self.vector_weight + self.keyword_weight) / (self.rrf_k + 1)
            for cid in fused_scores:
                fused_scores[cid] = min(1.0, fused_scores[cid] / max_possible)
        else:
            # Weighted linear score fusion
            v_scores = {c.id: s for c, s in vector_results}
            k_scores = {c.id: s for c, s in keyword_results}
            all_ids = set(v_scores.keys()).union(set(k_scores.keys()))

            for cid in all_ids:
                v_s = v_scores.get(cid, 0.0)
                k_s = k_scores.get(cid, 0.0)
                fused_scores[cid] = (self.vector_weight * v_s) + (self.keyword_weight * k_s)

        # 4. Filter and sort
        scored_pairs: List[Tuple[StructuredChunk, float]] = []
        for cid, score in fused_scores.items():
            if cid in chunk_map and score >= minimum_score:
                scored_pairs.append((chunk_map[cid], round(score, 4)))

        scored_pairs.sort(key=lambda pair: pair[1], reverse=True)
        return scored_pairs[:top_k]

