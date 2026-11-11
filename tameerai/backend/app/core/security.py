"""
TameerAI - Security and Cryptography Utilities (Phase 02A)

Provides:
- Argon2id password hashing and verification (OWASP recommended standard)
- Cryptographically secure refresh token generation and SHA-256 hashing
- JWT access token generation and strict verification (algorithm, issuer, audience)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.core.config import settings

# Initialize Argon2id password hasher with secure parameters
# Type.ID = Argon2id (hybrid data-dependent / data-independent memory access)
_password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id.
    Never returns or logs the plaintext password.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against an Argon2id hash in constant-time.
    Fails safely on corrupted or mismatched hashes.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_secure_token(length_bytes: int = 48) -> str:
    """
    Generates a cryptographically secure, URL-safe random string for refresh tokens.
    48 bytes of entropy produces ~64 base64url characters (> 384 bits entropy).
    """
    return secrets.token_urlsafe(length_bytes)


def hash_token(raw_token: str) -> str:
    """
    Computes the SHA-256 hex digest of a raw token.
    Only the hash is persisted to the database to prevent plain token leakage on DB dump.
    """
    if not raw_token:
        raise ValueError("Token string cannot be empty.")
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a signed, short-lived JWT access token.
    Claims include sub (user UUID), role, iss, aud, iat, nbf, exp, and type='access'.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "access",
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if extra_claims:
        # Prevent collision with reserved claims
        reserved = {"sub", "iss", "aud", "type", "iat", "nbf", "exp"}
        for k, v in extra_claims.items():
            if k not in reserved:
                payload[k] = v

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and strictly validates a JWT access token.
    Validates:
    - Signature using configured algorithm only (prevents algorithm confusion / 'none' attack)
    - Expiration (exp)
    - Issuer (iss)
    - Audience (aud)
    - Token type claim ('access')
    Raises jwt.PyJWTError subclasses on any validation failure.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
        options={
            "require": ["sub", "exp", "iss", "aud", "type", "nbf"],
            "verify_exp": True,
            "verify_iss": True,
            "verify_aud": True,
            "verify_nbf": True,
        },
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type: expected 'access' token.")

    return payload

