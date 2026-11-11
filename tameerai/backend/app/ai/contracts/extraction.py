"""
TameerAI - Document Extraction Contracts (Phase 03B)
Defines protocol contracts, structured extraction containers, and safety exceptions
for native PDF and OCR document intelligence.
"""

from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Extraction Exceptions
# ---------------------------------------------------------------------------

class ExtractionError(Exception):
    """Base exception for all document extraction failures."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class OversizedDocumentError(ExtractionError):
    """Raised when file size exceeds maximum allowed bytes."""
    pass


class PageLimitExceededError(ExtractionError):
    """Raised when page count exceeds maximum processing bounds."""
    pass


class EncryptedDocumentError(ExtractionError):
    """Raised when PDF is encrypted or password-protected and cannot be decrypted."""
    pass


class MalformedPDFError(ExtractionError):
    """Raised when PDF bytes or structure are invalid or corrupted."""
    pass


class ExtractionTimeoutError(ExtractionError):
    """Raised when extraction exceeds the allocated processing timeout."""
    pass


class OCRExecutableNotFoundError(ExtractionError):
    """Raised when external OCR binary is unavailable."""
    pass


# ---------------------------------------------------------------------------
# Data Containers
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    """Normalized spatial coordinates on an engineering drawing or page [0.0 - 1.0]."""
    x_min: float = Field(..., ge=0.0, le=1.0)
    y_min: float = Field(..., ge=0.0, le=1.0)
    x_max: float = Field(..., ge=0.0, le=1.0)
    y_max: float = Field(..., ge=0.0, le=1.0)
    page_number: Optional[int] = Field(default=None, ge=1)
    text_snippet: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def map_legacy_coordinates(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Support x0, y0, x1, y1 mapping
            if "x0" in values and "x_min" not in values:
                # If values are in point units (>1.0), normalize or clamp
                x0 = float(values.pop("x0"))
                y0 = float(values.pop("y0"))
                x1 = float(values.pop("x1"))
                y1 = float(values.pop("y1"))
                # Clamp to 0.0 - 1.0 if normalized, or scale down if points
                if x1 > 1.0 or y1 > 1.0:
                    scale_x = max(x1, 612.0)
                    scale_y = max(y1, 792.0)
                    x0, y0 = min(max(x0 / scale_x, 0.0), 1.0), min(max(y0 / scale_y, 0.0), 1.0)
                    x1, y1 = min(max(x1 / scale_x, 0.0), 1.0), min(max(y1 / scale_y, 0.0), 1.0)
                values["x_min"] = x0
                values["y_min"] = y0
                values["x_max"] = x1
                values["y_max"] = y1
        return values

    @property
    def x0(self) -> float:
        return self.x_min

    @property
    def y0(self) -> float:
        return self.y_min

    @property
    def x1(self) -> float:
        return self.x_max

    @property
    def y1(self) -> float:
        return self.y_max


class ExtractedTable(BaseModel):
    """Structured tabular data extracted from a document (e.g., BOQ schedule, rate table)."""
    table_index: int = Field(default=0, ge=0)
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    page_number: int = Field(..., ge=1)
    bbox: Optional[BoundingBox] = None
    row_count: int = Field(default=0)
    col_count: int = Field(default=0)

    @model_validator(mode="before")
    @classmethod
    def compute_dimensions(cls, values: Any) -> Any:
        if isinstance(values, dict):
            rows = values.get("rows", [])
            headers = values.get("headers", [])
            if "row_count" not in values or values["row_count"] == 0:
                values["row_count"] = len(rows)
            if "col_count" not in values or values["col_count"] == 0:
                values["col_count"] = len(headers) if headers else (len(rows[0]) if rows else 0)
        return values


class ExtractedPage(BaseModel):
    """Individual extracted page with layout details."""
    page_number: int = Field(..., ge=1, description="1-based page index")
    raw_text: str = Field(default="")
    raw_text_urdu: Optional[str] = None
    extraction_method: str = Field(default="native_pdf")  # native_pdf, ocr, hybrid
    ocr_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tables: List[ExtractedTable] = Field(default_factory=list)
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    is_scanned: bool = Field(default=False)
    is_empty: bool = Field(default=False)
    rotation: int = Field(default=0, ge=0, le=360)
    width: Optional[float] = None
    height: Optional[float] = None
    language_hints: List[str] = Field(default_factory=lambda: ["en"])
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "text" in values and "raw_text" not in values:
                values["raw_text"] = values.pop("text")
        return values

    @property
    def text(self) -> str:
        return self.raw_text

    @property
    def character_count(self) -> int:
        return len(self.raw_text)

    @property
    def word_count(self) -> int:
        return len(self.raw_text.split())

    @property
    def has_text(self) -> bool:
        return not self.is_empty and len(self.raw_text.strip()) > 0


class ExtractedDocument(BaseModel):
    """Full extraction result for an engineering or contract document."""
    document_id: UUID = Field(default_factory=uuid4)
    filename: Optional[str] = None
    total_pages: int = Field(..., ge=0)
    pages: List[ExtractedPage] = Field(default_factory=list)
    overall_method: str = Field(default="native_pdf")  # native_pdf, ocr, hybrid
    is_encrypted: bool = Field(default=False)
    is_scanned_only: bool = Field(default=False)
    processing_time_ms: float = Field(default=0.0, ge=0.0)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def populate_doc_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "extraction_method" in values and "overall_method" not in values:
                values["overall_method"] = values.pop("extraction_method")
        return values

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.raw_text for p in self.pages if p.raw_text)

    @property
    def total_characters(self) -> int:
        return sum(len(p.raw_text) for p in self.pages)

    @property
    def total_words(self) -> int:
        return sum(len(p.raw_text.split()) for p in self.pages)

    @property
    def extraction_method(self) -> str:
        return self.overall_method


class ExtractionRequest(BaseModel):
    """Request for extracting text and structure from a stored document."""
    document_id: UUID = Field(default_factory=uuid4)
    project_id: UUID = Field(default_factory=uuid4)
    file_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    storage_path: Optional[str] = None
    perform_ocr_fallback: bool = Field(default=True)
    extract_tables: bool = Field(default=True)
    ocr_language: str = Field(default="eng+urd")
    max_pages: int = Field(default=100, ge=1, le=500)
    timeout_seconds: float = Field(default=60.0, ge=1.0, le=300.0)


@runtime_checkable
class DocumentExtractor(Protocol):
    """Protocol for extracting text, tables, and structural elements from documents."""
    async def extract_document(self, request: ExtractionRequest) -> ExtractedDocument:
        ...
