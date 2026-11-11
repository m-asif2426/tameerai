"""
TameerAI - Storage Provider Abstraction (Phase 02D)

Provides a unified interface for private object storage supporting:
- Private object upload
- Secure object access and existence verification
- Safe signed download URLs (short-lived, non-public)
- Controlled object deletion for rollback and compensating transactions
- Zero leakage of storage credentials or internal paths
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from urllib.parse import quote

import httpx

from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger("tameerai.storage")


class StorageError(Exception):
    """Base exception for storage provider operations."""
    pass


class StorageFileNotFoundError(StorageError):
    """Raised when an object does not exist in storage."""
    pass


class StorageConfigurationError(StorageError):
    """Raised when the configured storage provider lacks required credentials."""
    pass


class StorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        """Uploads content bytes to the specified private object path."""
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """Downloads and returns object content bytes."""
        pass

    @abstractmethod
    async def get_signed_url(self, path: str, expires_in_seconds: int = 300) -> str:
        """Generates a temporary signed URL for downloading the private object."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Checks if the object exists in storage."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Deletes the object at the specified path. Returns True if deleted or did not exist."""
        pass


class InMemoryStorageProvider(StorageProvider):
    """
    In-memory storage provider for isolated tests, local development,
    and offline execution without external cloud dependencies.
    """

    def __init__(self) -> None:
        # Maps path -> (content_bytes, content_type)
        self._objects: Dict[str, Tuple[bytes, str]] = {}

    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        self._objects[path] = (content, content_type)
        logger.debug("InMemoryStorage: Uploaded %s (%d bytes, %s)", path, len(content), content_type)

    async def download(self, path: str) -> bytes:
        if path not in self._objects:
            raise StorageFileNotFoundError(f"Storage object not found: {path}")
        return self._objects[path][0]

    async def get_signed_url(self, path: str, expires_in_seconds: int = 300) -> str:
        if path not in self._objects:
            raise StorageFileNotFoundError(f"Storage object not found: {path}")
        expiry = int(time.time()) + expires_in_seconds
        # Return a simulated signed URL with non-disclosing signature token
        safe_path = quote(path, safe="")
        return f"https://storage.tameerai.pk/signed/{safe_path}?token=mock_signed_sec_{expiry}&expires={expiry}"

    async def exists(self, path: str) -> bool:
        return path in self._objects

    async def delete(self, path: str) -> bool:
        if path in self._objects:
            del self._objects[path]
            logger.debug("InMemoryStorage: Deleted %s", path)
            return True
        return False

    def clear(self) -> None:
        """Utility for test fixtures to reset storage state."""
        self._objects.clear()


class SupabaseStorageProvider(StorageProvider):
    """
    Production storage provider integrating with private Supabase Storage REST API.
    Employs signed URLs with strictly bounded TTLs and no public bucket exposure.
    """

    def __init__(
        self,
        base_url: str,
        service_key: str,
        bucket: str = "project-documents",
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_key = service_key
        self.bucket = bucket
        self.timeout = timeout

    def _headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{quote(path, safe='/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    content=content,
                    headers=self._headers(content_type),
                )
                if response.status_code not in (200, 201):
                    logger.error("Supabase Storage upload failed [%d]: %s", response.status_code, response.text)
                    raise StorageError(f"Storage upload failed with status {response.status_code}")
            except httpx.RequestError as exc:
                logger.error("Supabase Storage request network error during upload: %s", exc)
                raise StorageError(f"Storage network error: {exc}") from exc

    async def download(self, path: str) -> bytes:
        url = f"{self.base_url}/storage/v1/object/authenticated/{self.bucket}/{quote(path, safe='/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._headers())
                if response.status_code == 404:
                    raise StorageFileNotFoundError(f"Storage object not found: {path}")
                if response.status_code != 200:
                    raise StorageError(f"Storage download failed with status {response.status_code}")
                return response.content
            except httpx.RequestError as exc:
                raise StorageError(f"Storage network error: {exc}") from exc

    async def get_signed_url(self, path: str, expires_in_seconds: int = 300) -> str:
        url = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{quote(path, safe='/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    json={"expiresIn": expires_in_seconds},
                    headers=self._headers("application/json"),
                )
                if response.status_code == 404:
                    raise StorageFileNotFoundError(f"Storage object not found: {path}")
                if response.status_code != 200:
                    raise StorageError(f"Failed to sign storage URL: status {response.status_code}")
                data = response.json()
                signed_rel = data.get("signedURL")
                if not signed_rel:
                    raise StorageError("Malformed signed URL response from storage provider.")
                if signed_rel.startswith("/storage/v1/"):
                    return f"{self.base_url}{signed_rel}"
                elif signed_rel.startswith("/"):
                    return f"{self.base_url}/storage/v1{signed_rel}"
                else:
                    return f"{self.base_url}/storage/v1/{signed_rel}"
            except httpx.RequestError as exc:
                raise StorageError(f"Storage network error: {exc}") from exc

    async def exists(self, path: str) -> bool:
        url = f"{self.base_url}/storage/v1/object/info/authenticated/{self.bucket}/{quote(path, safe='/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._headers())
                return response.status_code == 200
            except httpx.RequestError:
                return False

    async def delete(self, path: str) -> bool:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    "DELETE",
                    url,
                    json={"prefixes": [path]},
                    headers=self._headers("application/json"),
                )
                return response.status_code in (200, 204)
            except httpx.RequestError as exc:
                logger.warning("Failed to delete storage object %s: %s", path, exc)
                return False


# Dedicated in-memory provider for explicitly configured test/local mode
_default_in_memory_storage = InMemoryStorageProvider()


def get_storage_provider() -> StorageProvider:
    """
    FastAPI dependency resolving the active storage provider.

    Security Policy:
    - If STORAGE_BACKEND is 'supabase' (default for development and production),
      requires both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to be configured.
      Missing credentials raise an explicit HTTP 503 Service Unavailable error
      to prevent silent uploads into transient volatile memory.
    - InMemoryStorageProvider is strictly restricted to STORAGE_BACKEND='in_memory'
      (deliberate local test mode) or explicit test dependency overrides.
    - Storage secrets are never leaked in error messages.
    """
    backend = settings.STORAGE_BACKEND.lower().strip()

    if backend == "in_memory":
        return _default_in_memory_storage

    if backend == "supabase":
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.error("Storage misconfiguration: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cloud storage service is not configured. Document operations are currently unavailable.",
            )
        return SupabaseStorageProvider(
            base_url=settings.SUPABASE_URL,
            service_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            bucket=settings.SUPABASE_STORAGE_BUCKET,
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported storage backend configuration: '{settings.STORAGE_BACKEND}'.",
    )

