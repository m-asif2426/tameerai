"""
TameerAI - AI Provider Interface & Request/Response Contracts (Phase 03A)
Defines protocol contracts, structured request/response containers, and safe
exception classes for provider-independent AI model interaction.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, runtime_checkable
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Safe Exception Hierarchy
# ---------------------------------------------------------------------------

class AIError(Exception):
    """Base exception for all TameerAI AI-layer errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AIProviderError(AIError):
    """Raised when an AI provider returns an upstream error or unexpected status."""
    pass


class AITimeoutError(AIError):
    """Raised when an AI provider request exceeds the configured timeout."""
    pass


class AIConfigurationError(AIError):
    """Raised when AI settings, provider credentials, or model configurations are invalid."""
    pass


class AIInputLimitExceededError(AIError):
    """Raised when request text or tokens exceed safe processing bounds."""
    pass


class AIRateLimitError(AIError):
    """Raised when upstream provider rate limits are encountered."""
    pass


class StructuredOutputValidationError(AIError):
    """Raised when provider output cannot be parsed into the expected structured schema."""
    pass


# ---------------------------------------------------------------------------
# Enums and Value Objects
# ---------------------------------------------------------------------------

class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"
    UNKNOWN = "unknown"


class TokenUsage(BaseModel):
    """Tracks token consumption without exposing sensitive cost or account info."""
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class ChatMessageInput(BaseModel):
    """Single input dialogue turn for prompt preparation."""
    role: str = Field(..., pattern="^(system|user|assistant|tool)$")
    content: str = Field(..., min_length=1)
    name: Optional[str] = None


# ---------------------------------------------------------------------------
# Request & Response Contracts
# ---------------------------------------------------------------------------

class ModelRequest(BaseModel):
    """
    Normalized, provider-independent model execution request.
    Carries bounded input parameters and generation constraints.
    """
    messages: List[ChatMessageInput] = Field(..., min_length=1)
    model: Optional[str] = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    system_instruction: Optional[str] = None
    response_schema: Optional[Type[BaseModel]] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """
    Normalized, provider-independent model execution response.
    Returns generated content, usage telemetry, and safe metadata.
    """
    content: str = Field(default="")
    structured_data: Optional[Dict[str, Any]] = None
    finish_reason: FinishReason = FinishReason.STOP
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model_identifier: str = Field(default="unknown")
    provider_name: str = Field(default="unknown")
    latency_ms: float = Field(default=0.0, ge=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# AI Provider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class AIProvider(Protocol):
    """
    Provider-agnostic interface for executing AI text and structured generation.
    Implementations must support async non-blocking execution, timeout adherence,
    and safe error mapping.
    """
    @property
    def provider_name(self) -> str:
        """Returns the canonical provider identifier (e.g., 'mock', 'openai', 'gemini')."""
        ...

    @property
    def default_model(self) -> str:
        """Returns the default model identifier for this provider."""
        ...

    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        """Executes a standard conversational or completion generation."""
        ...

    async def generate_structured(self, request: ModelRequest, schema: Type[T]) -> T:
        """
        Executes a constrained generation guaranteed to conform to the supplied
        Pydantic schema, or raises StructuredOutputValidationError.
        """
        ...

