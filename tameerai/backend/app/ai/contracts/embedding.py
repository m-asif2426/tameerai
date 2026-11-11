"""
TameerAI - Embedding Provider Contracts (Phase 03A)
Defines protocol contracts and data containers for future vector embedding generation.
"""

from typing import List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class VectorEmbedding(BaseModel):
    """Container for a single embedded text item."""
    index: int = Field(default=0, ge=0)
    vector: List[float] = Field(..., min_length=1)
    dimensions: int = Field(..., gt=0)


class EmbeddingRequest(BaseModel):
    """Normalized embedding generation request."""
    texts: List[str] = Field(..., min_length=1)
    model: Optional[str] = None
    target_dimensions: Optional[int] = Field(default=None, gt=0)
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)


class EmbeddingResponse(BaseModel):
    """Normalized embedding generation response."""
    embeddings: List[VectorEmbedding] = Field(..., min_length=1)
    model_identifier: str = Field(default="unknown")
    provider_name: str = Field(default="unknown")
    total_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for generating vector embeddings from text batches."""
    @property
    def provider_name(self) -> str:
        ...

    @property
    def default_dimensions(self) -> int:
        ...

    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...

