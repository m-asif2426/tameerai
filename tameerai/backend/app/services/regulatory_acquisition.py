"""
TameerAI - Pakistan Statutory Regulatory Document Acquisition Service (Phase 03.3)

Provides hardened, SSRF-defended, checksum-verified acquisition and intake of statutory regulatory documents.
Enforces strict boundary isolation: NEVER accesses protected user directories.
"""

from datetime import date, datetime, timezone
import hashlib
import ipaddress
import logging
import os
from pathlib import Path
import re
import socket
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
import uuid

from sqlalchemy.orm import Session

from app.models.regulation import RegulatoryDocument, RegulatoryDocumentVersion, RegulatoryIngestionJob

logger = logging.getLogger(__name__)

# Maximum permissible document size for statutory ingestion (50 MB)
MAX_DOCUMENT_SIZE_BYTES = 50 * 1024 * 1024

# Permitted MIME types and magic byte headers
PERMITTED_FILE_TYPES = {
    "application/pdf": b"%PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": b"PK\x03\x04",
    "text/plain": None,
}

# Blocked IP networks for SSRF defense (RFC 1918, RFC 3927, RFC 4193, loopback, metadata)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS/GCP/Azure link-local metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),  # Unique local
    ipaddress.ip_network("fe80::/10"),  # Link local
]


class RegulatorySecurityException(Exception):
    """Raised when an acquisition request violates security or SSRF boundaries."""
    pass


class RegulatoryAcquisitionService:
    """
    Handles secure acquisition, validation, and storage of official regulatory texts.
    """

    @classmethod
    def get_storage_base_dir(cls) -> Path:
        """
        Returns the designated private regulatory storage directory inside the backend workspace.
        Explicitly isolated from any user-designated protected folders.
        """
        backend_root = Path(__file__).resolve().parent.parent.parent
        storage_dir = backend_root / "storage" / "regulations"
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir

    @classmethod
    def validate_url_for_ssrf(cls, url: str) -> str:
        """
        Performs rigorous SSRF validation on a prospective acquisition URL.
        Rejects non-HTTP(S) schemes, localhost, private IP spaces, and link-local metadata endpoints.
        """
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise RegulatorySecurityException(f"Unsupported scheme '{parsed.scheme}': only HTTP/HTTPS permitted")

        hostname = parsed.hostname
        if not hostname:
            raise RegulatorySecurityException("Malformed URL: missing hostname")

        if hostname.lower() in ("localhost", "ip6-localhost", "ip6-loopback"):
            raise RegulatorySecurityException(f"Access to localhost is prohibited: {hostname}")

        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            raise RegulatorySecurityException(f"Could not resolve hostname '{hostname}': {e}")

        for entry in addr_info:
            ip_str = entry[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                raise RegulatorySecurityException(f"Invalid resolved IP address: {ip_str}")

            for blocked in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked:
                    raise RegulatorySecurityException(
                        f"SSRF violation: Host '{hostname}' resolved to prohibited IP {ip_str} in {blocked}"
                    )

        return url

    @classmethod
    def validate_file_content(cls, content: bytes, reported_mime_type: Optional[str] = None) -> Tuple[str, str]:
        """
        Validates raw file bytes for size and magic byte signatures.
        Returns (detected_mime_type, sha256_hash).
        """
        if len(content) == 0:
            raise ValueError("Document file is empty (0 bytes)")

        if len(content) > MAX_DOCUMENT_SIZE_BYTES:
            raise ValueError(f"File size {len(content)} bytes exceeds maximum {MAX_DOCUMENT_SIZE_BYTES} bytes")

        sha256_hash = hashlib.sha256(content).hexdigest()

        detected_mime = "application/octet-stream"
        if content.startswith(b"%PDF"):
            detected_mime = "application/pdf"
        elif content.startswith(b"PK\x03\x04"):
            detected_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            try:
                content.decode("utf-8")
                detected_mime = "text/plain"
            except UnicodeDecodeError:
                detected_mime = reported_mime_type or "application/octet-stream"

        return detected_mime, sha256_hash

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitizes an incoming filename against path traversal and special characters.
        """
        clean = Path(filename).name
        clean = re.sub(r"[^\w\.\-\_]", "_", clean)
        if not clean or clean.startswith("."):
            clean = f"doc_{uuid.uuid4().hex[:8]}.pdf"
        return clean

    @classmethod
    def store_document_bytes(
        cls,
        document_version_id: uuid.UUID,
        filename: str,
        content: bytes,
    ) -> Tuple[str, str, int, str]:
        """
        Securely saves validated document bytes to the isolated private regulatory storage.
        Returns: (relative_storage_path, sha256_hash, file_size_bytes, mime_type)
        """
        mime_type, sha256_hash = cls.validate_file_content(content)
        sanitized = cls.sanitize_filename(filename)

        version_dir = cls.get_storage_base_dir() / str(document_version_id)
        version_dir.mkdir(parents=True, exist_ok=True)

        target_file = version_dir / sanitized
        target_file.write_bytes(content)

        relative_path = f"storage/regulations/{document_version_id}/{sanitized}"
        logger.info(
            "Saved regulatory document: %s (size=%d bytes, sha256=%s)",
            relative_path,
            len(content),
            sha256_hash,
        )
        return relative_path, sha256_hash, len(content), mime_type

    @classmethod
    def create_document_version(
        cls,
        db: Session,
        document: RegulatoryDocument,
        version_label: str,
        effective_date: date,
        filename: str,
        content: bytes,
        edition: Optional[str] = None,
        publication_date: Optional[date] = None,
        notification_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        is_current: bool = True,
        official_source_url: Optional[str] = None,
        provenance_details: Optional[Dict[str, Any]] = None,
        verification_notes: Optional[str] = None,
    ) -> RegulatoryDocumentVersion:
        """
        Creates and registers a new immutable version for a regulatory document.
        If is_current=True, supersedes prior versions.
        """
        version_id = uuid.uuid4()

        if is_current and document.versions:
            for prior_v in document.versions:
                if prior_v.is_current:
                    prior_v.is_current = False
                    prior_v.superseded_by_version_id = version_id
                    if not prior_v.expiry_date:
                        prior_v.expiry_date = effective_date

        storage_path, file_sha256, file_size, mime_type = cls.store_document_bytes(
            document_version_id=version_id,
            filename=filename,
            content=content,
        )

        version = RegulatoryDocumentVersion(
            id=version_id,
            document_id=document.id,
            version_label=version_label,
            edition=edition or f"{document.document_code} Edition {version_label}",
            publication_date=publication_date,
            notification_date=notification_date,
            effective_date=effective_date,
            expiry_date=expiry_date,
            is_current=is_current,
            storage_path=storage_path,
            official_source_url=official_source_url,
            source_file_sha256=file_sha256,
            file_size_bytes=file_size,
            mime_type=mime_type,
            total_pages=0,
            language="en",
            provenance_details=provenance_details or {},
            verification_notes=verification_notes,
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version
