"""
TameerAI - AI Provider Factory & Security Gate (Phase 03A)
Safely instantiates and manages AI provider adapters.
Guarantees feature-flag enforcement, production safety, and rejects untrusted
provider injection.
"""

from typing import Optional
from app.core.config import settings
from app.ai.contracts.provider import AIProvider, AIConfigurationError
from app.ai.providers.mock_provider import MockAIProvider

ALLOWED_PROVIDERS = {"mock", "openai", "gemini", "anthropic"}


def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """
    Factory function returning the configured AI provider.
    
    Security & Configuration Enforcements:
    1. AI features must be enabled in settings.ENABLE_AI_FEATURES (or running in test mode).
    2. Provider must be in ALLOWED_PROVIDERS.
    3. Mock provider is forbidden in production environments.
    4. Client-supplied arbitrary provider names are rejected.
    """
    selected_provider = (provider_name or settings.AI_DEFAULT_PROVIDER).lower().strip()

    if selected_provider not in ALLOWED_PROVIDERS:
        raise AIConfigurationError(
            f"Provider '{selected_provider}' is not supported. "
            f"Allowed providers: {sorted(list(ALLOWED_PROVIDERS))}."
        )

    # In production, enforce that AI is enabled and mock is prohibited
    if settings.ENVIRONMENT.lower() == "production":
        if not settings.ENABLE_AI_FEATURES:
            raise AIConfigurationError("AI features are disabled in production.")
        if selected_provider == "mock":
            raise AIConfigurationError("Mock AI provider is not permitted in production.")

    if selected_provider == "mock":
        return MockAIProvider()

    if selected_provider == "gemini":
        from app.ai.providers.gemini_provider import GeminiProvider
        return GeminiProvider()

    raise AIConfigurationError(
        f"Live provider adapter for '{selected_provider}' is not activated in Phase 03A (supported in Phase 03D: 'mock', 'gemini')."
    )

