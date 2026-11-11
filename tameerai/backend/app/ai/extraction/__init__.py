"""
TameerAI - Document Extraction & OCR Pipeline (Phase 03B)
Provides native PDF extraction, OCR adapters, and hybrid routing for engineering documents.
"""

from app.ai.contracts.extraction import (
    BoundingBox,
    DocumentExtractor,
    EncryptedDocumentError,
    ExtractedDocument,
    ExtractedPage,
    ExtractedTable,
    ExtractionError,
    ExtractionRequest,
    ExtractionTimeoutError,
    MalformedPDFError,
    OCRExecutableNotFoundError,
    OversizedDocumentError,
    PageLimitExceededError,
)
from app.ai.extraction.native import NativePDFExtractor
from app.ai.extraction.ocr import TesseractOCRExtractor, MockOCRExtractor
from app.ai.extraction.hybrid import HybridDocumentExtractor

__all__ = [
    "BoundingBox",
    "DocumentExtractor",
    "EncryptedDocumentError",
    "ExtractedDocument",
    "ExtractedPage",
    "ExtractedTable",
    "ExtractionError",
    "ExtractionRequest",
    "ExtractionTimeoutError",
    "MalformedPDFError",
    "OCRExecutableNotFoundError",
    "OversizedDocumentError",
    "PageLimitExceededError",
    "NativePDFExtractor",
    "TesseractOCRExtractor",
    "MockOCRExtractor",
    "HybridDocumentExtractor",
]

