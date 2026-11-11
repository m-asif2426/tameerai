"""
TameerAI - Google Gemini AI Provider Adapter (Phase 03D)
Integrates the official Google Gen AI Python SDK (google-genai) with
async execution, structured outputs, strict cost controls, rate limiting,
safe retry backoff, and credential redaction.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.ai.contracts.provider import (
    AIProvider,
    AIConfigurationError,
    AIError,
    AIInputLimitExceededError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    FinishReason,
    ModelRequest,
    ModelResponse,
    StructuredOutputValidationError,
    TokenUsage,
)

logger = logging.getLogger("tameerai.ai.gemini")

T = TypeVar("T", bound=BaseModel)

# Currently officially supported active Gemini models
SUPPORTED_GEMINI_MODELS = {
    "gemini-3.5-flash-lite",  # Preferred initial model for affordable testing
    "gemini-2.5-flash",
    "gemini-2.5-pro",
}

# Explicitly rejected deprecated models
DEPRECATED_GEMINI_MODELS = {
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
}


class GeminiRateLimiter:
    """
    In-memory rate limiter and quota guard for Google Gemini.
    Enforces application-side operational guardrails (RPM, daily request cap, and concurrency).
    
    IMPORTANT ARCHITECTURAL NOTICE:
    These counters are client-side application guardrails designed to prevent accidental runaway
    request loops. They are NOT guaranteed Google platform billing limits. Quotas, tier status,
    and billing policies must be verified independently in the Google Cloud / AI Studio console.
    """

    def __init__(
        self,
        rpm_limit: int = 15,
        daily_cap: int = 1500,
        concurrent_limit: int = 3,
    ):
        self.rpm_limit = rpm_limit
        self.daily_cap = daily_cap
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self._minute_timestamps: List[float] = []
        self._daily_count: int = 0
        self._current_day: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Checks and updates request counters. Raises AIRateLimitError if limits are breached."""
        async with self._lock:
            now = time.monotonic()
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # Reset daily counter on date rollover
            if today != self._current_day:
                self._current_day = today
                self._daily_count = 0

            # Daily cap check
            if self._daily_count >= self.daily_cap:
                raise AIRateLimitError(
                    f"Application-side Gemini daily request cap of {self.daily_cap} requests reached for today ({self._current_day}). "
                    "Service paused to prevent quota overruns. (Note: This is an internal guardrail, not a Google billing guarantee)."
                )

            # Purge minute timestamps older than 60 seconds
            self._minute_timestamps = [t for t in self._minute_timestamps if now - t < 60.0]

            # RPM limit check
            if len(self._minute_timestamps) >= self.rpm_limit:
                raise AIRateLimitError(
                    f"Application-side Gemini rate limit exceeded ({self.rpm_limit} requests/minute). "
                    "Please wait a few seconds before retrying."
                )

            # Record this request
            self._minute_timestamps.append(now)
            self._daily_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """Returns non-sensitive usage metrics for diagnostics."""
        now = time.monotonic()
        active_minute = len([t for t in self._minute_timestamps if now - t < 60.0])
        return {
            "current_day": self._current_day,
            "daily_requests": self._daily_count,
            "daily_cap": self.daily_cap,
            "minute_requests": active_minute,
            "rpm_limit": self.rpm_limit,
        }

    def reset_for_test(self) -> None:
        """Resets counters during automated test teardown."""
        self._minute_timestamps.clear()
        self._daily_count = 0


# Global singleton rate limiter for the process
_rate_limiter = GeminiRateLimiter(
    rpm_limit=settings.GEMINI_RPM_LIMIT,
    daily_cap=settings.GEMINI_DAILY_REQUEST_CAP,
    concurrent_limit=settings.GEMINI_CONCURRENT_REQUEST_LIMIT,
)


from app.core.security_redaction import (
    mask_credential_repr,
    sanitize_exception,
    sanitize_sensitive_details,
)


class GeminiProvider(AIProvider):
    """
    Google Gemini AI Provider utilizing the google-genai SDK.
    Implements the AIProvider protocol with strict rate limits, exponential backoff,
    and schema validation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        model: Optional[str] = None,
        rate_limiter: Optional[GeminiRateLimiter] = None,
        genai_client: Optional[Any] = None,
    ):
        chosen_model = model or model_name or settings.GEMINI_MODEL
        self._validate_model(chosen_model)
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self._model_name = chosen_model
        self._rate_limiter = rate_limiter or _rate_limiter
        self._client = genai_client

    def __repr__(self) -> str:
        key_repr = mask_credential_repr(self._api_key)
        return f"<GeminiProvider(model='{self._model_name}', api_key={key_repr})>"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._model_name

    @property
    def model(self) -> str:
        return self._model_name

    def _get_client(self) -> Any:
        """Lazily instantiates the google-genai Client if not pre-injected."""
        if self._client is not None:
            return self._client

        # Guard: Check if live Gemini API is enabled in settings
        if not settings.ENABLE_GEMINI_API:
            raise AIConfigurationError(
                "Google Gemini API is disabled by configuration (ENABLE_GEMINI_API=False). "
                "Enable ENABLE_GEMINI_API in configuration and provide GEMINI_API_KEY to activate."
            )

        if not self._api_key or not self._api_key.strip():
            raise AIConfigurationError(
                "GEMINI_API_KEY is not configured. Set the GEMINI_API_KEY environment variable."
            )

        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key.strip())
            return self._client
        except Exception as e:
            sanitized = sanitize_sensitive_details(str(e))
            raise AIConfigurationError(f"Failed to initialize google-genai client: {sanitized}")

    def _build_contents_and_system(self, request: ModelRequest) -> tuple[str, Optional[str]]:
        """Extracts user content and system instruction from ModelRequest."""
        # Calculate total input character size
        total_input_chars = sum(len(m.content) for m in request.messages)
        if request.system_instruction:
            total_input_chars += len(request.system_instruction)

        if total_input_chars > settings.GEMINI_MAX_INPUT_CHARS:
            raise AIInputLimitExceededError(
                f"Input character count ({total_input_chars}) exceeds Gemini safety ceiling of {settings.GEMINI_MAX_INPUT_CHARS} characters."
            )

        # Separate system message if present in messages
        system_inst = request.system_instruction
        prompt_parts: List[str] = []

        for msg in request.messages:
            if msg.role == "system":
                if system_inst:
                    system_inst = f"{system_inst}\n\n{msg.content}"
                else:
                    system_inst = msg.content
            elif msg.role in ("user", "assistant"):
                prompt_parts.append(f"{msg.role.upper()}: {msg.content}")

        combined_prompt = "\n\n".join(prompt_parts)
        return combined_prompt, system_inst

    async def _execute_with_retry(self, client: Any, model: str, contents: str, config: Any, timeout: float) -> Any:
        """Executes generate_content with concurrency control and safe exponential backoff."""
        max_retries = settings.GEMINI_MAX_RETRIES

        for attempt in range(max_retries + 1):
            try:
                # Concurrency bounding
                async with self._rate_limiter.semaphore:
                    # RPM and RPD checks
                    await self._rate_limiter.acquire()

                    # Execute with async timeout
                    return await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model,
                            contents=contents,
                            config=config,
                        ),
                        timeout=timeout,
                    )
            except asyncio.TimeoutError:
                if attempt == max_retries:
                    raise AITimeoutError(f"Gemini request timed out after {timeout} seconds.")
                await asyncio.sleep(1.0 * (2 ** attempt))
            except AIRateLimitError:
                raise
            except Exception as e:
                err_str = str(e).lower()
                # Check for rate limit status codes (429 / RESOURCE_EXHAUSTED)
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    if attempt == max_retries:
                        raise AIRateLimitError(
                            "Gemini upstream rate limit reached. Please wait before retrying."
                        )
                    await asyncio.sleep(2.0 * (2 ** attempt))
                    continue

                # Non-retryable configuration or block error
                sanitized_msg = sanitize_sensitive_details(str(e))
                if attempt == max_retries:
                    raise AIProviderError(f"Gemini upstream error: {sanitized_msg}")
                await asyncio.sleep(1.0 * (2 ** attempt))

    def _validate_model(self, model: str) -> None:
        """Validates that the requested model is currently active and not deprecated."""
        if model in DEPRECATED_GEMINI_MODELS:
            raise AIConfigurationError(
                f"Gemini model '{model}' is deprecated and no longer supported. "
                "Please configure an active model such as 'gemini-3.5-flash-lite' or 'gemini-2.5-flash'."
            )

    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        """Executes a standard conversational or text generation request."""
        model = request.model or self._model_name
        self._validate_model(model)

        client = self._get_client()
        prompt, system_inst = self._build_contents_and_system(request)
        timeout = min(request.timeout_seconds, settings.GEMINI_TIMEOUT_SECONDS)

        from google.genai import types
        gen_config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=min(request.max_tokens, settings.GEMINI_MAX_OUTPUT_TOKENS),
            system_instruction=system_inst,
            stop_sequences=request.stop_sequences,
        )

        start_time = time.monotonic()
        response = await self._execute_with_retry(
            client=client,
            model=model,
            contents=prompt,
            config=gen_config,
            timeout=timeout,
        )
        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        # Extract text and usage
        output_text = getattr(response, "text", "") or ""
        token_usage = TokenUsage()
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            token_usage = TokenUsage(
                prompt_tokens=getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                completion_tokens=getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
                total_tokens=getattr(response.usage_metadata, "total_token_count", 0) or 0,
            )

        return ModelResponse(
            content=output_text,
            finish_reason=FinishReason.STOP,
            usage=token_usage,
            model_identifier=model,
            provider_name=self.provider_name,
            latency_ms=elapsed_ms,
            metadata={"gemini_model": model},
        )

    async def generate_structured(self, request: ModelRequest, schema: Type[T]) -> T:
        """Executes a structured generation request constrained to the specified Pydantic schema."""
        model = request.model or self._model_name
        self._validate_model(model)

        client = self._get_client()
        prompt, system_inst = self._build_contents_and_system(request)
        timeout = min(request.timeout_seconds, settings.GEMINI_TIMEOUT_SECONDS)

        from google.genai import types
        gen_config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=min(request.max_tokens, settings.GEMINI_MAX_OUTPUT_TOKENS),
            system_instruction=system_inst,
            response_mime_type="application/json",
            response_schema=schema,
        )

        response = await self._execute_with_retry(
            client=client,
            model=model,
            contents=prompt,
            config=gen_config,
            timeout=timeout,
        )

        raw_json = getattr(response, "text", "") or "{}"
        try:
            parsed_data = json.loads(raw_json)
            return schema.model_validate(parsed_data)
        except Exception as e:
            raise StructuredOutputValidationError(
                f"Failed to validate Gemini response against schema {schema.__name__}: {e}",
                details={"raw_output": raw_json[:300]},
            )
