"""
TameerAI - Mock Embedding Provider (Phase 03C)
Generates deterministic, normalized mock vector embeddings for offline testing and RAG development.
Zero external network calls; fully reproducible.
"""

import hashlib
import math
import random
import time
from typing import List, Optional

from app.ai.contracts.embedding import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    VectorEmbedding,
)

MAX_EMBEDDING_BATCH_SIZE = 128


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic mock embedding provider.
    Implements the EmbeddingProvider protocol with L2-normalized float vectors.
    """

    def __init__(
        self,
        dimensions: int = 384,
        model_name: str = "mock-bge-small-en-v1.5",
        max_batch_size: int = MAX_EMBEDDING_BATCH_SIZE,
    ):
        if dimensions <= 0:
            raise ValueError(f"dimensions must be a positive integer, got: {dimensions}")
        self._dimensions = dimensions
        self._model_name = model_name
        self._max_batch_size = max_batch_size

    @property
    def provider_name(self) -> str:
        return "MockEmbeddingProvider"

    @property
    def default_dimensions(self) -> int:
        return self._dimensions

    def _generate_deterministic_vector(self, text: str, dim: int) -> List[float]:
        """
        Generates a deterministic float vector seeded from text SHA-256,
        normalized to unit L2 Euclidean length (norm = 1.0).
        """
        # Create integer seed from sha256 hash
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], byteorder="big")

        rng = random.Random(seed)
        # Generate raw gaussian-like floats
        raw_values = [rng.gauss(0.0, 1.0) for _ in range(dim)]

        # Calculate L2 norm
        norm = math.sqrt(sum(x * x for x in raw_values))
        if norm == 0.0:
            norm = 1.0

        # Normalize to unit length
        unit_vec = [round(x / norm, 6) for x in raw_values]

        # Ensure exact unit normalization after rounding
        re_norm = math.sqrt(sum(x * x for x in unit_vec))
        if re_norm > 0.0 and abs(re_norm - 1.0) > 1e-4:
            unit_vec = [x / re_norm for x in unit_vec]

        return unit_vec

    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        start_time = time.monotonic()

        if not request.texts:
            raise ValueError("EmbeddingRequest.texts cannot be empty.")

        if len(request.texts) > self._max_batch_size:
            raise ValueError(
                f"Batch size ({len(request.texts)}) exceeds maximum allowed limit of {self._max_batch_size}."
            )

        dim = request.target_dimensions or self._dimensions
        if dim <= 0:
            raise ValueError(f"target_dimensions must be positive, got {dim}")

        embeddings: List[VectorEmbedding] = []
        total_tokens = 0

        for idx, text in enumerate(request.texts):
            clean = text.strip() if text else ""
            if not clean:
                raise ValueError(f"Empty or whitespace-only text at index {idx} is not allowed.")

            vec = self._generate_deterministic_vector(clean, dim)

            # Validate finiteness
            if any(math.isnan(v) or math.isinf(v) for v in vec):
                raise ValueError(f"Generated non-finite float vector at index {idx}")

            embeddings.append(
                VectorEmbedding(
                    index=idx,
                    vector=vec,
                    dimensions=dim,
                )
            )
            # Estimate token count
            total_tokens += max(1, int(len(clean.split()) * 1.33))

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return EmbeddingResponse(
            embeddings=embeddings,
            model_identifier=request.model or self._model_name,
            provider_name=self.provider_name,
            total_tokens=total_tokens,
            latency_ms=elapsed_ms,
        )

