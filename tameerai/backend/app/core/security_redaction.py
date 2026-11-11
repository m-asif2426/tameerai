"""
TameerAI - Centralized Security Redaction & Credential Defense Module (Phase 03E)

Provides multi-layered protection against accidental credential exposure:
1. Legacy Google API keys (AIza...)
2. Modern Google AI Studio Authorization keys (AQ... / AQ- / AQ_ / AQ.)
3. Google OAuth 2.0 Access Tokens (ya29...)
4. Generic Bearer tokens, x-goog-api-key headers, and URI key parameters
5. Database connection strings and host filesystem paths
6. Exception tracing and Python stack trace sanitization

IMPORTANT SECURITY NOTICE:
While regex masking provides strong automated defense, no single regex or set of patterns
can guarantee 100% prevention of all potential data leakage. TameerAI implements multi-layer
defense: strict environment segregation, non-logging of secret values, object representation
masking, and explicit client-side sanitization.
"""

import re
from typing import List, Optional, Tuple


# Ordered redaction patterns (Pattern, Replacement)
CREDENTIAL_REDACTION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # 1. Database Connection URIs (with credentials)
    (
        re.compile(r"(?:postgresql|postgres|sqlite|mysql)\+?[a-z]*://[^\s@]+@[^\s/]+/[^\s]+", re.IGNORECASE),
        "[REDACTED_DB_URI]",
    ),
    (
        re.compile(r"(?:postgresql|postgres|sqlite|mysql)\+?[a-z]*://[^\s]+", re.IGNORECASE),
        "[REDACTED_DB_URI]",
    ),

    # 2. Legacy Google API Keys (AIzaSy... / AIza...)
    (
        re.compile(r"AIza[0-9A-Za-z\-_]{20,}", re.ASCII),
        "[REDACTED_API_KEY]",
    ),

    # 3. Modern Google AI Studio Authorization Keys (AQ... / AQ- / AQ_ / AQ.)
    (
        re.compile(r"\bAQ[\.\-_A-Za-z0-9]{20,}", re.ASCII),
        "[REDACTED_AUTH_KEY]",
    ),

    # 4. Google OAuth 2.0 Access Tokens
    (
        re.compile(r"\bya29\.[0-9A-Za-z\-_]{20,}", re.ASCII),
        "[REDACTED_OAUTH_TOKEN]",
    ),

    # 5. Authorization Bearer Tokens
    (
        re.compile(r"(?:Bearer\s+)[A-Za-z0-9_\-\.]{16,}", re.IGNORECASE),
        "Bearer [REDACTED_TOKEN]",
    ),

    # 6. HTTP Headers and Query String Credentials
    (
        re.compile(r"(?:x-goog-api-key[\s:=]+)(?!\[REDACTED)[A-Za-z0-9_\-\.]{16,}", re.IGNORECASE),
        "x-goog-api-key: [REDACTED]",
    ),
    (
        re.compile(r"(?:api[_\-]?key|auth_token|secret_key|private_key)[\s:=]+(?!\[REDACTED)['\"]?[A-Za-z0-9_\-\.]{16,}['\"]?", re.IGNORECASE),
        "api_key=[REDACTED]",
    ),
    (
        re.compile(r"(?:[\?&]key=)(?!\[REDACTED)[A-Za-z0-9_\-\.]{16,}", re.IGNORECASE),
        "?key=[REDACTED]",
    ),

    # 7. Generic Secret, Password, Token, Bearer, and Service Role keywords
    (
        re.compile(r"(?:password|secret|token|bearer|bearer_token|api_key|service_role)[=:\s]+(?!\[REDACTED)['\"]?[^\s,;'\"<>]+['\"]?", re.IGNORECASE),
        "[REDACTED_CREDENTIAL]",
    ),

    # 8. Host Paths (Windows and Unix)
    (
        re.compile(r"[A-Za-z]:\\(?:[^<>:\"/|?*\r\n]+\\)*[^<>:\"/|?*;\r\n.]+\.[a-zA-Z0-9]+", re.IGNORECASE),
        "[REDACTED_PATH]",
    ),
    (
        re.compile(r"[A-Za-z]:\\[^\r\n:;,\"]{8,}", re.IGNORECASE),
        "[REDACTED_PATH]",
    ),
    (
        re.compile(r"/(?:Users|home|var|tmp|etc|app|root)/[^\r\n:;,\"]{6,}"),
        "[REDACTED_PATH]",
    ),

    # 9. Python Traceback Line References
    (
        re.compile(r'File ".*?", line \d+.*'),
        "[STACK_TRACE_LINE_REDACTED]",
    ),
]


def sanitize_sensitive_details(text: Optional[str]) -> str:
    """
    Sanitizes raw text, error messages, and telemetry strings to redact credentials,
    secrets, database URIs, file system paths, and stack traces.
    Multi-pass scrubbing guarantees comprehensive scrubbing of chained or embedded tokens.
    """
    if not text:
        return ""

    sanitized = str(text)
    for pattern, replacement in CREDENTIAL_REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    # Collapse repeated newlines and excessive whitespace
    sanitized = re.sub(r"\n\s*\n", "\n", sanitized)
    return sanitized.strip()


def sanitize_exception(exc: BaseException) -> str:
    """
    Extracts and sanitizes the exception message without exposing internal paths or keys.
    """
    if exc is None:
        return "Unknown error"
    raw_str = f"{type(exc).__name__}: {str(exc)}"
    return sanitize_sensitive_details(raw_str)[:1000]


def mask_credential_repr(key: Optional[str]) -> str:
    """
    Returns a safe string representation for an API key or credential object.
    Never exposes the raw string or prefix/suffix.
    """
    if not key or not str(key).strip():
        return "[NOT CONFIGURED]"
    return "[CONFIGURED_SECRET]"


def is_potential_credential(text: Optional[str]) -> bool:
    """
    Detects if a string matches known Google credential or token formats.
    Used for pre-validation and test auditing.
    """
    if not text or not isinstance(text, str):
        return False
    clean = text.strip()
    if clean.startswith("AIza") and len(clean) >= 20:
        return True
    if clean.startswith("AQ") and len(clean) >= 20:
        return True
    if clean.startswith("ya29.") and len(clean) >= 20:
        return True
    return False
