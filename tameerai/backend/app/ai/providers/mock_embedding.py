"""
TameerAI - Deterministic Mock Embedding Provider (Phase 03A)
Provides synthetic, reproducible vector generation for unit tests and local verification.
"""

import hashlib
import math
import time
from typing import List

from app.ai.contracts.embedding import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    VectorEmbedding,
)


class MockEmbeddingProvider:
    """
    Deterministic mock embedding provider.
    Generates reproducible unit-normalized float vectors using SHA-256 hash seeds.
    Zero external network calls; safe for offline automated tests.
    """
    def __init__(self, default_dimensions: int = 768):
        self._provider_name = "mock"
        self._default_dimensions = default_dimensions

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def default_dimensions(self) -> int:
        return self._default_dimensions

    def _generate_vector(self, text: str, dim: int) -> List[float]:
        """Produces a deterministic normalized vector for a given text."""
        # Use SHA-256 hashes of text + index as pseudo-random seed values
        raw_vals: List[float] = []
        for i in range(dim):
            seed = f"{text}::{i}".encode("utf-8")
            h = int(hashlib.sha256(seed).hexdigest()[:8], 16)
            # Map to [-1.0, 1.0]
            val = (h / 0xFFFFFFFF) * 2.0 - 1.0
            raw_vals.append(val)

        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(v * v for v in raw_vals)) or 1.0
        return [round(v / norm, 6) for v in raw_vals]

    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        start = time.monotonic()
        dim = request.target_dimensions or self._default_dimensions

        embeddings: List[VectorEmbedding] = []
        for idx, text in enumerate(request.texts):
            vec = self._generate_vector(text, dim)
            embeddings.append(
                VectorEmbedding(index=idx, vector=vec, dimensions=dim)
            )

        elapsed_ms = (time.monotonic() - start) * 1000.0
        return EmbeddingResponse(
            embeddings=embeddings,
            model_identifier=request.model or "mock-embed-v1",
            provider_name=self._provider_name,
            total_tokens=sum(max(1, len(t) // 4) for t in request.texts),
            latency_ms=elapsed_ms,
        )

