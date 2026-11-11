"""
TameerAI - Document Extraction Safety & Resource Guardrails (Phase 03B)
Enforces file size limits, page count boundaries, path traversal prevention,
and automatic temporary file lifecycle management.
"""

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Generator, Optional, Union

from app.ai.contracts.extraction import (
    OversizedDocumentError,
    PageLimitExceededError,
)

# Safety Boundaries
MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_PAGE_COUNT = 100                    # Maximum synchronous page limit
MAX_RASTER_DIMENSION = 4096            # Maximum pixel width/height for OCR rasterization
DEFAULT_EXTRACTION_TIMEOUT = 60.0      # Seconds


def validate_file_size(size_bytes: int, max_bytes: int = MAX_PDF_SIZE_BYTES) -> None:
    """Validates that document byte size is within safe processing bounds."""
    if size_bytes > max_bytes:
        raise OversizedDocumentError(
            f"Document size ({size_bytes} bytes) exceeds maximum allowable limit of {max_bytes} bytes ({max_bytes // (1024 * 1024)} MB)."
        )


def validate_page_count(page_count: int, max_pages: int = MAX_PAGE_COUNT) -> None:
    """Validates that total page count does not exceed processing ceiling."""
    if page_count > max_pages:
        raise PageLimitExceededError(
            f"Document contains {page_count} pages, which exceeds the processing limit of {max_pages} pages."
        )


def validate_safe_path(path_input: Union[str, Path]) -> Path:
    """
    Validates filesystem path to prevent directory traversal attacks.
    Rejects relative navigation ('..'), null bytes, and non-pdf extensions.
    """
    raw_str = str(path_input)
    if not raw_str or "\x00" in raw_str:
        raise ValueError("Invalid filesystem path: null bytes or empty path detected.")

    if ".." in raw_str:
        raise ValueError("Directory traversal attempt ('..') detected.")

    path = Path(path_input).resolve()
    # Ensure resolved path exists
    if not path.exists():
        raise FileNotFoundError(f"Document file not found at path: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected .pdf extension, got: {path.suffix}")

    return path


@contextlib.contextmanager
def safe_temp_pdf_file(file_bytes: bytes, prefix: str = "tameerai_pdf_") -> Generator[Path, None, None]:
    """
    Context manager writing raw PDF bytes to a secure temporary file.
    Guarantees immediate cleanup upon exit even if exceptions are raised.
    """
    validate_file_size(len(file_bytes))
    temp_dir = tempfile.gettempdir()
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=prefix,
            suffix=".pdf",
            dir=temp_dir,
            delete=False
        ) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            temp_path = Path(tmp.name)
        yield temp_path
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
