"""
TameerAI - Native PDF Text & Structure Extraction Engine (Phase 03B)
Extracts readable text, page dimensions, rotation, empty page status, and tabular schedules
from text-based PDF documents without hallucination.
"""

import io
import time
from pathlib import Path
from typing import List, Optional, Union
from uuid import UUID, uuid4

import pypdf
import pypdf.errors
import pdfplumber

from app.ai.contracts.extraction import (
    BoundingBox,
    DocumentExtractor,
    EncryptedDocumentError,
    ExtractedDocument,
    ExtractedPage,
    ExtractedTable,
    ExtractionRequest,
    MalformedPDFError,
)
from app.ai.extraction.safety import (
    safe_temp_pdf_file,
    validate_file_size,
    validate_page_count,
    validate_safe_path,
)


class NativePDFExtractor(DocumentExtractor):
    """
    High-performance native PDF text and structure extractor.
    Uses pypdf for robust structural parsing and pdfplumber for tabular data extraction.
    Adheres strictly to the DocumentExtractor Protocol.
    """

    def __init__(self, extract_tables: bool = True, max_pages: int = 100):
        self.default_extract_tables = extract_tables
        self.default_max_pages = max_pages

    async def extract_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "document.pdf",
        project_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        extract_tables: Optional[bool] = None,
        max_pages: Optional[int] = None,
    ) -> ExtractedDocument:
        """Convenience method for direct in-memory bytes extraction."""
        req = ExtractionRequest(
            document_id=document_id or uuid4(),
            project_id=project_id or uuid4(),
            file_bytes=pdf_bytes,
            extract_tables=self.default_extract_tables if extract_tables is None else extract_tables,
            max_pages=self.default_max_pages if max_pages is None else max_pages,
        )
        doc = await self.extract_document(req)
        doc.filename = filename
        return doc

    async def extract_from_file(
        self,
        file_path: Union[str, Path],
        filename: Optional[str] = None,
        project_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        extract_tables: Optional[bool] = None,
        max_pages: Optional[int] = None,
    ) -> ExtractedDocument:
        """Convenience method for local file path extraction."""
        resolved = validate_safe_path(file_path)
        req = ExtractionRequest(
            document_id=document_id or uuid4(),
            project_id=project_id or uuid4(),
            file_path=str(resolved),
            extract_tables=self.default_extract_tables if extract_tables is None else extract_tables,
            max_pages=self.default_max_pages if max_pages is None else max_pages,
        )
        doc = await self.extract_document(req)
        doc.filename = filename or resolved.name
        return doc

    async def extract_document(self, request: ExtractionRequest) -> ExtractedDocument:
        start_time = time.monotonic()
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Resolve and validate input bytes / path
        pdf_bytes: bytes
        if request.file_bytes is not None:
            pdf_bytes = request.file_bytes
            validate_file_size(len(pdf_bytes))
        elif request.file_path is not None:
            resolved_path = validate_safe_path(request.file_path)
            validate_file_size(resolved_path.stat().st_size)
            pdf_bytes = resolved_path.read_bytes()
        else:
            raise ValueError("ExtractionRequest must supply either file_bytes or file_path.")

        # 2. Open and validate PDF with pypdf
        try:
            stream = io.BytesIO(pdf_bytes)
            reader = pypdf.PdfReader(stream)
        except pypdf.errors.PdfReadError as e:
            raise MalformedPDFError(f"Failed to parse PDF document: {e}")
        except Exception as e:
            raise MalformedPDFError(f"Corrupt or invalid PDF file stream: {e}")

        # Check encryption
        if reader.is_encrypted:
            # Attempt to decrypt with empty password (some PDFs are encrypted with blank user pass)
            try:
                decrypted = reader.decrypt("")
                if decrypted == pypdf.constants.PasswordResult.NOT_DECRYPTED:
                    raise EncryptedDocumentError(
                        "Document is password-protected or encrypted and cannot be processed."
                    )
            except EncryptedDocumentError:
                raise
            except Exception:
                raise EncryptedDocumentError(
                    "Document is encrypted with a required password."
                )

        try:
            total_pages = len(reader.pages)
        except Exception as e:
            raise MalformedPDFError(f"Could not count PDF pages: {e}")

        validate_page_count(total_pages, request.max_pages)

        if total_pages == 0:
            warnings.append("Document has 0 pages.")

        # 3. Extract text and layout metadata per page using pypdf
        extracted_pages: List[ExtractedPage] = []
        has_scanned_elements = False

        for idx, page in enumerate(reader.pages):
            page_number = idx + 1  # 1-based indexing
            page_warnings: List[str] = []
            page_errors: List[str] = []

            # Page dimensions and rotation
            width = float(page.mediabox.width) if page.mediabox else None
            height = float(page.mediabox.height) if page.mediabox else None
            rotation = int(page.rotation) if hasattr(page, "rotation") else 0

            # Image detection
            image_count = len(page.images)
            is_scanned = (image_count > 0)
            if is_scanned:
                has_scanned_elements = True

            # Text extraction
            try:
                text = page.extract_text() or ""
            except Exception as e:
                text = ""
                page_errors.append(f"Native text extraction failed on page {page_number}: {e}")

            clean_text = text.strip()
            is_empty = len(clean_text) == 0

            if is_empty:
                if is_scanned:
                    page_warnings.append(
                        f"Page {page_number} contains {image_count} image(s) but zero native text (scanned page)."
                    )
                else:
                    page_warnings.append(f"Page {page_number} is completely blank.")

            extracted_pages.append(
                ExtractedPage(
                    page_number=page_number,
                    raw_text=clean_text,
                    extraction_method="native_pdf",
                    is_scanned=is_scanned,
                    is_empty=is_empty,
                    rotation=rotation,
                    width=width,
                    height=height,
                    language_hints=["en"],
                    warnings=page_warnings,
                    errors=page_errors,
                    metadata={"image_count": image_count},
                )
            )

        # 4. Optional Table Extraction using pdfplumber
        if request.extract_tables and total_pages > 0:
            try:
                with safe_temp_pdf_file(pdf_bytes) as temp_pdf:
                    with pdfplumber.open(temp_pdf) as plum_doc:
                        for idx, plum_page in enumerate(plum_doc.pages):
                            if idx < len(extracted_pages):
                                tables = plum_page.extract_tables()
                                if tables:
                                    extracted_tables: List[ExtractedTable] = []
                                    for t_idx, raw_table in enumerate(tables):
                                        if not raw_table:
                                            continue
                                        headers = [str(col).strip() if col else "" for col in raw_table[0]]
                                        rows = [
                                            [str(cell).strip() if cell else "" for cell in row]
                                            for row in raw_table[1:]
                                        ]
                                        extracted_tables.append(
                                            ExtractedTable(
                                                table_index=t_idx,
                                                headers=headers,
                                                rows=rows,
                                                page_number=idx + 1,
                                                row_count=len(rows),
                                                col_count=len(headers) if headers else 0,
                                            )
                                        )
                                    extracted_pages[idx].tables = extracted_tables
            except Exception as e:
                warnings.append(f"Table extraction encountered non-fatal error: {e}")

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return ExtractedDocument(
            document_id=request.document_id,
            total_pages=total_pages,
            pages=extracted_pages,
            overall_method="native_pdf",
            is_encrypted=False,
            is_scanned_only=has_scanned_elements and all(p.is_empty for p in extracted_pages),
            processing_time_ms=elapsed_ms,
            warnings=warnings,
            errors=errors,
            metadata={
                "extractor": "NativePDFExtractor",
                "scanned_pages_detected": sum(1 for p in extracted_pages if p.is_scanned),
            },
        )
