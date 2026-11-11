"""
TameerAI - In-Memory Vector Similarity Retrieval Engine (Phase 03C)
Computes cosine similarity between query embeddings and stored chunk embeddings
with dimension validation and finite value guarantees.
"""

import math
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.ai.contracts.chunking import StructuredChunk


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    if len(v1) != len(v2):
        raise ValueError(f"Vector dimension mismatch: {len(v1)} vs {len(v2)}")

    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))

    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0

    sim = dot_product / (norm_v1 * norm_v2)
    # Clamp to [-1.0, 1.0] for precision bounds
    return max(-1.0, min(1.0, sim))


class InMemoryVectorRetriever:
    """
    In-memory semantic vector similarity retrieval engine.
    Stores chunk embedding vectors and performs dense cosine similarity search.
    """

    def __init__(self, expected_dimensions: int = 384):
        self.expected_dimensions = expected_dimensions
        # Mapping: chunk_id -> (StructuredChunk, embedding_vector)
        self._index: Dict[UUID, Tuple[StructuredChunk, List[float]]] = {}

    def index_chunks(self, chunks: List[StructuredChunk], vectors: List[List[float]]) -> None:
        """Indexes structured chunks alongside their pre-generated embedding vectors."""
        if len(chunks) != len(vectors):
            raise ValueError(f"Count mismatch between chunks ({len(chunks)}) and vectors ({len(vectors)}).")

        for chunk, vec in zip(chunks, vectors):
            if len(vec) != self.expected_dimensions:
                raise ValueError(
                    f"Vector dimension mismatch for chunk {chunk.id}: expected {self.expected_dimensions}, got {len(vec)}."
                )
            if any(math.isnan(x) or math.isinf(x) for x in vec):
                raise ValueError(f"Non-finite numeric value in embedding vector for chunk {chunk.id}.")
            self._index[chunk.id] = (chunk, vec)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        minimum_score: float = 0.0,
        filter_chunks: Optional[List[StructuredChunk]] = None,
    ) -> List[Tuple[StructuredChunk, float]]:
        """
        Computes cosine similarity against query vector.
        Optional filter_chunks restricts candidate pool for multi-tenant pre-filtering.
        Returns ranked list of (StructuredChunk, normalized_score in [0.0, 1.0]).
        """
        if len(query_vector) != self.expected_dimensions:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.expected_dimensions}, got {len(query_vector)}."
            )

        if not self._index:
            return []

        # If pre-filtering is provided, restrict candidate IDs
        allowed_ids: Optional[set] = {c.id for c in filter_chunks} if filter_chunks is not None else None

        scored_pairs: List[Tuple[StructuredChunk, float]] = []

        for chunk_id, (chunk, chunk_vec) in self._index.items():
            if allowed_ids is not None and chunk_id not in allowed_ids:
                continue

            sim = cosine_similarity(query_vector, chunk_vec)
            # Map [-1.0, 1.0] to [0.0, 1.0] for probability-like relevance scoring
            norm_score = max(0.0, (sim + 1.0) / 2.0)

            if norm_score >= minimum_score:
                scored_pairs.append((chunk, round(norm_score, 4)))

        # Sort descending by score
        scored_pairs.sort(key=lambda pair: pair[1], reverse=True)
        return scored_pairs[:top_k]

    def clear(self) -> None:
        """Clears the in-memory index."""
        self._index.clear()

