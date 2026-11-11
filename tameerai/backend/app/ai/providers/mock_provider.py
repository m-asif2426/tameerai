"""
TameerAI - Deterministic Mock AI Provider (Phase 03A)
Provides a fully isolated, zero-network mock provider for local testing,
validation, and CI/CD pipelines.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.ai.contracts.provider import (
    AIProvider,
    AIProviderError,
    AITimeoutError,
    AIInputLimitExceededError,
    AIRateLimitError,
    StructuredOutputValidationError,
    ModelRequest,
    ModelResponse,
    TokenUsage,
    FinishReason,
)
from app.ai.schemas.response import (
    AIResponse,
    SourceCitation,
    EvidenceExcerpt,
    ConfidenceLevel,
    AnalysisType,
    HumanReviewRequirement,
    WarningCard,
    AIProviderMetadata,
    ENGINEERING_DISCLAIMER_TEXT,
)

T = TypeVar("T", bound=BaseModel)


class MockAIProvider:
    """
    Deterministic mock AI provider for testing without API keys or network calls.
    Supports controllable success, simulated timeout, rate limit, and malformed outputs.
    """
    def __init__(
        self,
        default_model: str = "mock-tameerai-v1",
        simulated_latency_seconds: float = 0.0,
        should_fail: bool = False,
        fail_with_timeout: bool = False,
        fail_with_rate_limit: bool = False,
        fail_with_input_limit: bool = False,
        fail_with_malformed_json: bool = False,
        custom_text_response: Optional[str] = None,
        custom_structured_response: Optional[BaseModel] = None,
    ):
        self._provider_name = "mock"
        self._default_model = default_model
        self.simulated_latency_seconds = simulated_latency_seconds
        self.should_fail = should_fail
        self.fail_with_timeout = fail_with_timeout
        self.fail_with_rate_limit = fail_with_rate_limit
        self.fail_with_input_limit = fail_with_input_limit
        self.fail_with_malformed_json = fail_with_malformed_json
        self.custom_text_response = custom_text_response
        self.custom_structured_response = custom_structured_response
        self.call_history: List[ModelRequest] = []

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def default_model(self) -> str:
        return self._default_model

    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        """Generates synthetic deterministic text response."""
        self.call_history.append(request)
        start_time = time.monotonic()

        # Input limit check
        total_input_chars = sum(len(m.content) for m in request.messages)
        if self.fail_with_input_limit or total_input_chars > 32000:
            raise AIInputLimitExceededError(
                f"Input length ({total_input_chars} chars) exceeds the maximum allowed bound (32000 chars)."
            )

        # Simulated latency
        if self.simulated_latency_seconds > 0:
            await asyncio.sleep(self.simulated_latency_seconds)

        # Simulated failure scenarios
        if self.fail_with_timeout:
            raise AITimeoutError(
                f"Mock provider request timed out after {request.timeout_seconds} seconds."
            )
        if self.fail_with_rate_limit:
            raise AIRateLimitError("Mock provider simulated rate limit (HTTP 429).")
        if self.should_fail:
            raise AIProviderError("Mock provider simulated upstream failure.")

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        last_user_message = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "Hello"
        )

        content = self.custom_text_response or self._synthesize_engineering_response(last_user_message)

        prompt_tokens = max(1, total_input_chars // 4)
        completion_tokens = max(1, len(content) // 4)

        return ModelResponse(
            content=content,
            finish_reason=FinishReason.STOP,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            model_identifier=request.model or self._default_model,
            provider_name=self._provider_name,
            latency_ms=elapsed_ms,
            metadata={"mock_execution": True, "call_count": len(self.call_history)},
        )

    def _synthesize_engineering_response(self, prompt: str) -> str:
        """Synthesizes high-fidelity, context-aware civil engineering responses for offline testing."""
        lower = prompt.lower()
        is_roman = any(w in lower for w in ["kya", "kia", "kaise", "kese", "kitna", "kitni", "bunyaad", "saria", "tarai", "dhalai", "lanter", "deewar"])

        # High-risk structural decisions
        if any(w in lower for w in ["remove column", "pillar tor", "pillar hatana", "remove load bearing"]):
            if is_roman:
                return (
                    "Kisi bhi load-bearing column ya deewar ko baghair structural calculations ke hatana intehai khatarnaak hai. "
                    "Is se structural collapse ka shadeed khatra hota hai. Barah-e-karam Professional Engineer (PEC) se site inspection karwayen."
                )
            return (
                "Removing any load-bearing column or wall without professional structural calculations poses a severe collapse hazard. "
                "A certified Professional Engineer (PEC) must conduct an on-site structural investigation."
            )

        # Curing questions
        if "curing" in lower or "tarai" in lower:
            if is_roman:
                return (
                    "Concrete ki curing (tarai) aam taur par kam az kam 7 se 14 din tak karni chahiye. "
                    "Curing ki muddat cement ki qisam (OPC ya SRC), mausam ke darja hararat aur project specifications par munhasir hoti hai. "
                    "Garmi ke mausam mein nami barqarar rakhna intehai zaroori hai taakay shrinkage cracks na aain."
                )
            return (
                "Concrete curing typically requires a minimum duration of 7 to 14 days under standard conditions. "
                "The duration depends on cement type (OPC vs blended), ambient temperature, exposure conditions, and structural specifications."
            )

        # Foundation depth & soil
        if any(w in lower for w in ["foundation", "bunyaad", "bearing capacity", "gehri"]):
            if is_roman:
                return (
                    "Bunyaad (foundation) ki gehrai is baat par depend karti hai ke zameen ki bearing capacity kitni hai aur building ka total load kitna hai. "
                    "Sirf plot size (jaise 5 marla) dekh kar gehrai tay nahi ki ja sakti; iske liye soil test (mitti ki janch) aur structural loading analysis zaroori hota hai."
                )
            return (
                "Foundation depth is determined by soil bearing capacity, total superstructure loads, groundwater table, and allowable settlement. "
                "Plot dimensions alone are insufficient; geotechnical site investigation is necessary to determine footing depth."
            )

        # Rebar / Saria weight
        if any(w in lower for w in ["saria", "sariya", "rebar", "weight"]) and any(w in lower for w in ["formula", "calculate", "wazan", "weight"]):
            if is_roman:
                return (
                    "Saria (rebar) ka wazan calculate karne ka standard formula D^2 / 162 (kg per meter) hai, jahan D saria ka diameter millimeter (mm) mein hota hai. "
                    "Imperial units mein sooter (1/8 inch) ke liye formula D^2 / 24 (lbs per foot) use hota hai."
                )
            return (
                "Rebar unit weight is calculated using the standard formula Weight = D^2 / 162 kg per meter, where D is the bar diameter in millimeters. "
                "In imperial units where bar size is in eighths of an inch (sooter), the weight is D^2 / 24 lbs per foot."
            )

        # Concrete quantity / Slab volume
        if "slab" in lower or "1000" in lower or "quantity" in lower:
            if is_roman:
                return (
                    "1000 sqft slab ke liye agar thickness 6 inch (0.5 feet) farz karein to wet volume 500 cft banta hai. "
                    "Dry volume factor 1.54 apply karne par 770 cft volume hota hai. Standard 1:2:4 ratio mein lagbhag 110 se 120 cement bags, 240 cft ret aur 480 cft bajri darkar hoti hai."
                )
            return (
                "For a 1000 sqft slab assuming a 6-inch (0.5 ft) thickness, the wet concrete volume is 500 cft. "
                "Applying a dry conversion factor of 1.54 yields 770 cft. In a nominal 1:2:4 ratio, this requires approximately 110-120 cement bags, 240 cft sand, and 480 cft coarse aggregate."
            )

        # Formwork / Shuttering
        if "shuttering" in lower or "shutraing" in lower or "formwork" in lower:
            if is_roman:
                return (
                    "Shuttering remove karne ka waqt structural element par depend karta hai: vertical sides 24 se 48 ghante baad, "
                    "slab soffits 7 se 14 din baad, aur beam spans 14 se 21 din baad props ke sath remove kiye ja sakte hain."
                )
            return (
                "Formwork stripping times depend on structural elements: vertical forms (columns, walls) after 24-48 hours, "
                "slab soffits after 7-14 days with props undisturbed, and long-span beams after 14-21 days."
            )

        # Building regulations / Setbacks
        if any(w in lower for w in ["setback", "bylaw", "byelaw", "lda", "cda", "sbca"]):
            if is_roman:
                return (
                    "Building setbacks aur rules mutaliqa development authority (LDA, CDA, ya SBCA) ke bylaws par munhasir hote hain. "
                    "Exact setback dimensions plot size aur road width par depend karti hain. Barah-e-karam verified official authority bylaw document refer karein."
                )
            return (
                "Building setbacks and height limits are governed by the relevant municipal development authority (such as LDA, CDA, or SBCA). "
                "Exact dimensional requirements depend on plot area, street width, and zoning classification. Consult verified regulatory documents."
            )

        # Generic civil engineering response
        if is_roman:
            return (
                f"Aap ke civil engineering sawal se mutaliq: Yeh masla standard construction practices aur structural engineering principles ke teht hal hota hai. "
                "Is mein standard materials, safe load distribution, aur proper workmanship ka khayal rakhna zaroori hota hai."
            )
        return (
            f"Regarding your civil engineering inquiry: This requires adherence to standard construction specifications and structural engineering principles, "
            "accounting for material quality, load distribution, and on-site workmanship."
        )

    async def generate_structured(self, request: ModelRequest, schema: Type[T]) -> T:
        """Generates synthetic deterministic structured response conforming to schema."""
        self.call_history.append(request)
        start_time = time.monotonic()

        # Input limit check
        total_input_chars = sum(len(m.content) for m in request.messages)
        if self.fail_with_input_limit or total_input_chars > 32000:
            raise AIInputLimitExceededError(
                f"Input length ({total_input_chars} chars) exceeds the maximum allowed bound (32000 chars)."
            )

        # Simulated latency
        if self.simulated_latency_seconds > 0:
            await asyncio.sleep(self.simulated_latency_seconds)

        # Simulated failure scenarios
        if self.fail_with_timeout:
            raise AITimeoutError(f"Mock provider request timed out after {request.timeout_seconds}s.")
        if self.fail_with_rate_limit:
            raise AIRateLimitError("Mock provider simulated rate limit (HTTP 429).")
        if self.should_fail:
            raise AIProviderError("Mock provider simulated upstream failure.")
        if self.fail_with_malformed_json:
            raise StructuredOutputValidationError(
                "Mock provider failed to parse structured output: Invalid JSON syntax at position 42."
            )

        # Return custom structured response if supplied
        if self.custom_structured_response is not None:
            if isinstance(self.custom_structured_response, schema):
                return self.custom_structured_response
            try:
                return schema.model_validate(self.custom_structured_response.model_dump())
            except Exception as e:
                raise StructuredOutputValidationError(f"Custom response does not match target schema: {e}")

        # If schema is AIResponse, build a rich deterministic mock response
        if issubclass(schema, AIResponse):
            last_user_message = next(
                (m.content for m in reversed(request.messages) if m.role == "user"),
                "Building regulation query"
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000.0

            mock_res = AIResponse(
                answer=(
                    f"Based on Pakistani building regulations, for '{last_user_message}': "
                    "Commercial G+12 structures require a minimum front setback of 30 feet and dual independent "
                    "fire staircases under Pakistan Building Code 2021 Section 4.2."
                ),
                answer_urdu="پاکستان بلڈنگ کوڈ 2021 کے سیکشن 4.2 کے تحت کمرشل عمارتوں کے لیے فرنٹ سیٹ بیک کم از کم 30 فٹ ہونا ضروری ہے۔",
                analysis_type=AnalysisType.COMPLIANCE_AUDIT,
                confidence=ConfidenceLevel.HIGH,
                human_review_required=HumanReviewRequirement.RECOMMENDED,
                citations=[
                    SourceCitation(
                        source_type="regulatory",
                        source_code="PBC-2021",
                        title="Building Code of Pakistan 2021",
                        section_or_clause="Section 4.2: Means of Egress & Setbacks",
                        page_number=45,
                        verified_against_retrieval=True,
                    )
                ],
                evidence_excerpts=[
                    EvidenceExcerpt(
                        source_code="PBC-2021",
                        page_number=45,
                        clause_or_section="Section 4.2",
                        exact_text="All commercial multi-storey buildings exceeding G+8 floors shall provide a front setback not less than 30 feet.",
                        relevance_score=0.92,
                    )
                ],
                warning_cards=[
                    WarningCard(
                        title="Setback Verification Notice",
                        severity="info",
                        description="Verify municipal zoning clearance with local development authority (LDA/CDA/SBCA).",
                        recommendation="Submit revised CAD architectural site plan to municipal desk prior to structural excavation.",
                        code_reference="PBC-2021 Sec 4.2",
                    )
                ],
                disclaimer=ENGINEERING_DISCLAIMER_TEXT,
                metadata=AIProviderMetadata(
                    provider="mock",
                    model_identifier=request.model or self._default_model,
                    latency_ms=elapsed_ms,
                    usage=TokenUsage(prompt_tokens=42, completion_tokens=85, total_tokens=127),
                    finish_reason=FinishReason.STOP,
                )
            )
            return mock_res  # type: ignore

        # Generic schema fallback: attempt model_validate on empty/default dict or construct
        try:
            return schema.model_validate({})
        except Exception:
            raise StructuredOutputValidationError(
                f"Mock provider cannot synthesize arbitrary schema '{schema.__name__}' without custom fixture."
            )

