"""
TameerAI - Document Extraction & OCR Pipeline Tests (Phase 03B)

Comprehensive test suite verifying:
1. Native PDF text extraction (single-page, multi-page, rotated, empty).
2. Tabular data extraction via pdfplumber.
3. OCR extraction with MockOCRExtractor & TesseractOCRExtractor availability checks.
4. HybridDocumentExtractor intelligent routing between native and OCR.
5. Safety controls: size limits, page count limits, malformed files, encrypted files, path traversal.
6. Structured schemas and Pydantic validation.
7. Zero network dependency and complete offline operation.
"""

import pytest
import io
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from app.ai.contracts.extraction import (
    BoundingBox,
    ExtractedTable,
    ExtractedPage,
    ExtractedDocument,
    MalformedPDFError,
    EncryptedDocumentError,
    PageLimitExceededError,
    OversizedDocumentError,
    OCRExecutableNotFoundError,
)
from app.ai.extraction.safety import (
    MAX_PDF_SIZE_BYTES,
    MAX_PAGE_COUNT,
    validate_file_size,
    validate_page_count,
    validate_safe_path,
    safe_temp_pdf_file,
)
from app.ai.extraction.native import NativePDFExtractor
from app.ai.extraction.ocr import MockOCRExtractor, TesseractOCRExtractor
from app.ai.extraction.hybrid import HybridDocumentExtractor

from tests.fixtures.pdf_fixtures import (
    generate_single_page_text_pdf,
    generate_multi_page_text_pdf,
    generate_scanned_image_pdf,
    generate_mixed_pdf,
    generate_rotated_page_pdf,
    generate_empty_page_pdf,
    generate_malformed_pdf,
    generate_encrypted_pdf,
    generate_table_pdf,
    generate_oversized_page_count_pdf,
)


# =====================================================================
# 1. Native PDF Extractor Tests
# =====================================================================

class TestNativePDFExtractor:
    """Tests for native PDF text, metadata, and table extraction."""

    async def test_single_page_text_extraction(self):
        pdf_bytes = generate_single_page_text_pdf("TameerAI Structural Column C-1 Rebar Schedule.")
        extractor = NativePDFExtractor()

        result = await extractor.extract_from_bytes(pdf_bytes, filename="column_spec.pdf")

        assert isinstance(result, ExtractedDocument)
        assert result.filename == "column_spec.pdf"
        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert result.extraction_method == "native_pdf"

        page = result.pages[0]
        assert page.page_number == 1
        assert "TameerAI Structural Column C-1 Rebar Schedule." in page.text
        assert "General Requirements" in page.text
        assert page.character_count > 0
        assert page.word_count > 0
        assert page.has_text is True
        assert page.width > 0
        assert page.height > 0
        assert page.extraction_method == "native_pdf"

    async def test_multi_page_text_extraction(self):
        pages_content = [
            "Sheet A-101: Ground Floor Architectural Plan.",
            "Sheet S-201: Foundation Footing Detailing.",
            "Sheet M-301: HVAC Ducting and Ventilation Schedule.",
        ]
        pdf_bytes = generate_multi_page_text_pdf(pages_content)
        extractor = NativePDFExtractor()

        result = await extractor.extract_from_bytes(pdf_bytes, filename="composite_drawing.pdf")

        assert result.total_pages == 3
        assert len(result.pages) == 3
        for idx, expected in enumerate(pages_content, start=1):
            p = result.pages[idx - 1]
            assert p.page_number == idx
            assert expected in p.text
            assert p.has_text is True
            assert p.extraction_method == "native_pdf"

        assert "Ground Floor Architectural Plan" in result.full_text
        assert "HVAC Ducting and Ventilation" in result.full_text

    async def test_rotated_page_metadata(self):
        pdf_bytes = generate_rotated_page_pdf(rotation=90)
        extractor = NativePDFExtractor()

        result = await extractor.extract_from_bytes(pdf_bytes, filename="rotated_sheet.pdf")

        assert result.total_pages == 1
        page = result.pages[0]
        assert page.rotation == 90
        assert "Rotated engineering drawing" in page.text

    async def test_empty_page_extraction(self):
        pdf_bytes = generate_empty_page_pdf()
        extractor = NativePDFExtractor()

        result = await extractor.extract_from_bytes(pdf_bytes, filename="empty_drawing.pdf")

        assert result.total_pages == 1
        page = result.pages[0]
        assert page.text == ""
        assert page.character_count == 0
        assert page.word_count == 0
        assert page.has_text is False

    async def test_table_extraction(self):
        headers = ["Item No.", "Description", "Unit", "Qty", "Rate"]
        rows = [
            ["1.01", "Site Excavation", "Cu.Ft", "15000", "45.00"],
            ["1.02", "PCC 1:4:8", "Cu.Ft", "3500", "280.00"],
            ["1.03", "RCC 1:2:4", "Cu.Ft", "8200", "520.00"],
        ]
        pdf_bytes = generate_table_pdf(headers, rows)
        extractor = NativePDFExtractor(extract_tables=True)

        result = await extractor.extract_from_bytes(pdf_bytes, filename="boq.pdf")

        assert result.total_pages == 1
        page = result.pages[0]
        assert len(page.tables) >= 1
        table = page.tables[0]
        assert isinstance(table, ExtractedTable)
        assert table.row_count >= 3
        assert table.col_count >= 5

        # Check table contents
        flat_cells = [cell for r in table.rows for cell in r if cell]
        assert any("Excavation" in cell for cell in flat_cells)
        assert any("RCC" in cell for cell in flat_cells)

    async def test_extract_from_file_path(self, tmp_path):
        pdf_bytes = generate_single_page_text_pdf("Local file path extraction test.")
        test_file = tmp_path / "valid_test.pdf"
        test_file.write_bytes(pdf_bytes)

        extractor = NativePDFExtractor()
        result = await extractor.extract_from_file(test_file)

        assert result.filename == "valid_test.pdf"
        assert result.total_pages == 1
        assert "Local file path extraction test." in result.pages[0].text


# =====================================================================
# 2. Safety Controls & Exception Handling Tests
# =====================================================================

class TestExtractionSafety:
    """Tests for document bounds, corruption, encryption, and path security."""

    async def test_malformed_pdf_rejection(self):
        pdf_bytes = generate_malformed_pdf()
        extractor = NativePDFExtractor()

        with pytest.raises(MalformedPDFError) as exc_info:
            await extractor.extract_from_bytes(pdf_bytes, filename="corrupt.pdf")
        assert "corrupt" in str(exc_info.value).lower() or "malformed" in str(exc_info.value).lower() or "fail" in str(exc_info.value).lower()

    async def test_encrypted_pdf_rejection(self):
        pdf_bytes = generate_encrypted_pdf(password="secret_pass_123")
        extractor = NativePDFExtractor()

        with pytest.raises(EncryptedDocumentError) as exc_info:
            await extractor.extract_from_bytes(pdf_bytes, filename="protected.pdf")
        assert "encrypted" in str(exc_info.value).lower() or "password" in str(exc_info.value).lower()

    async def test_oversized_page_count_rejection(self):
        # Default safety limit is 100 pages, fixture has 105
        pdf_bytes = generate_oversized_page_count_pdf(num_pages=105)
        extractor = NativePDFExtractor(max_pages=100)

        with pytest.raises(PageLimitExceededError) as exc_info:
            await extractor.extract_from_bytes(pdf_bytes, filename="massive_drawing_set.pdf")
        assert "105" in str(exc_info.value)
        assert "100" in str(exc_info.value)

    def test_validate_file_size_exceeded(self):
        huge_size = MAX_PDF_SIZE_BYTES + 1024
        with pytest.raises(OversizedDocumentError) as exc_info:
            validate_file_size(huge_size)
        assert "exceeds maximum allowable limit" in str(exc_info.value)

    def test_validate_file_size_valid(self):
        # 10 MB should pass
        validate_file_size(10 * 1024 * 1024)

    def test_safe_path_validation(self, tmp_path):
        valid_pdf = tmp_path / "normal_drawing.pdf"
        valid_pdf.write_text("dummy")

        # Valid path returns resolved path
        resolved = validate_safe_path(valid_pdf)
        assert resolved.name == "normal_drawing.pdf"

        # Traversal attempt with non-existent or disallowed characters
        with pytest.raises(ValueError):
            validate_safe_path(str(tmp_path) + "/../../nonexistent/path/outside/test.pdf")

        # Disallowed extension
        not_pdf = tmp_path / "executable.exe"
        not_pdf.write_text("not a pdf")
        with pytest.raises(ValueError, match="Expected .pdf extension"):
            validate_safe_path(not_pdf)

    def test_safe_temp_pdf_context_cleanup(self):
        pdf_bytes = generate_single_page_text_pdf("Temp file lifecycle test.")
        temp_path = None

        with safe_temp_pdf_file(pdf_bytes, prefix="test_lifecycle_") as tf:
            temp_path = tf
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0

        # After context exit, the file must be cleaned up
        assert not temp_path.exists()


# =====================================================================
# 3. OCR Extractor Tests
# =====================================================================

class TestOCRExtractors:
    """Tests for MockOCRExtractor and TesseractOCRExtractor adapter."""

    async def test_mock_ocr_extractor(self):
        mock_ocr = MockOCRExtractor(default_confidence=0.96)
        assert mock_ocr.is_available is True

        pdf_bytes = generate_scanned_image_pdf("SYNTHETIC PERMIT NUMBER 48291-B")
        result = await mock_ocr.extract_from_bytes(pdf_bytes, filename="permit_scan.pdf")

        assert isinstance(result, ExtractedDocument)
        assert result.total_pages == 1
        assert result.extraction_method == "ocr"

        page = result.pages[0]
        assert page.page_number == 1
        assert page.extraction_method == "ocr"
        assert page.ocr_confidence == 0.96
        assert len(page.bounding_boxes) > 0
        assert "OCR" in page.text or "PERMIT" in page.text

        box = page.bounding_boxes[0]
        assert isinstance(box, BoundingBox)
        assert box.confidence == 0.96
        assert box.page_number == 1

    async def test_mock_ocr_custom_simulation(self):
        simulated_pages = [
            "OCR Page 1: Municipal Approval Stamp No. 9012.",
            "OCR Page 2: Foundation Inspection Sign-off.",
        ]
        mock_ocr = MockOCRExtractor(simulated_page_texts=simulated_pages, default_confidence=0.92)

        pdf_bytes = generate_multi_page_text_pdf(["Dummy 1", "Dummy 2"])
        result = await mock_ocr.extract_from_bytes(pdf_bytes, filename="inspections.pdf")

        assert result.total_pages == 2
        assert "Municipal Approval Stamp" in result.pages[0].text
        assert "Foundation Inspection" in result.pages[1].text
        assert result.pages[0].ocr_confidence == 0.92

    async def test_tesseract_ocr_availability_on_host(self):
        """
        Verifies that TesseractOCRExtractor accurately detects host binary availability.
        In this local Windows environment without Tesseract installed, is_available must be False,
        and calling extract() must raise OCRExecutableNotFoundError rather than an unhandled crash.
        """
        tesseract = TesseractOCRExtractor(tesseract_cmd="nonexistent_tesseract_binary_path_xyz")
        assert tesseract.is_available is False

        pdf_bytes = generate_single_page_text_pdf("Tesseract availability check.")
        with pytest.raises(OCRExecutableNotFoundError) as exc_info:
            await tesseract.extract_from_bytes(pdf_bytes, filename="check.pdf")
        assert "not found" in str(exc_info.value).lower() or "not installed" in str(exc_info.value).lower()


# =====================================================================
# 4. Hybrid Extractor Routing Tests
# =====================================================================

class TestHybridDocumentExtractor:
    """Tests for intelligent routing between native text extraction and OCR."""

    async def test_hybrid_routes_native_text_document(self):
        """A text-dense document routes fully via native_pdf without invoking OCR."""
        pdf_bytes = generate_single_page_text_pdf("High density native text specification document.")
        mock_ocr = MockOCRExtractor()
        hybrid = HybridDocumentExtractor(ocr_extractor=mock_ocr)

        result = await hybrid.extract_from_bytes(pdf_bytes, filename="spec.pdf")

        assert result.extraction_method == "native_pdf"
        assert result.total_pages == 1
        assert result.pages[0].extraction_method == "native_pdf"
        assert result.pages[0].ocr_confidence is None
        assert "High density native text" in result.pages[0].text

    async def test_hybrid_routes_scanned_image_page_to_ocr(self):
        """A raster scanned page with < 40 chars routes to OCR."""
        pdf_bytes = generate_scanned_image_pdf("SCANNED BUILDING PERMIT APPROVAL")
        mock_ocr = MockOCRExtractor(
            simulated_page_texts=["MUNICIPAL AUTHORITY BUILDING CONTROL DEPARTMENT: APPROVED"],
            default_confidence=0.94,
        )
        hybrid = HybridDocumentExtractor(ocr_extractor=mock_ocr, min_chars_for_native=40)

        result = await hybrid.extract_from_bytes(pdf_bytes, filename="scanned_permit.pdf")

        assert result.extraction_method == "ocr"
        assert result.total_pages == 1
        page = result.pages[0]
        assert page.extraction_method == "ocr"
        assert page.ocr_confidence == 0.94
        assert "BUILDING CONTROL DEPARTMENT" in page.text

    async def test_hybrid_routes_mixed_document(self):
        """
        A 2-page document where:
        - Page 1 has native text -> native_pdf
        - Page 2 is scanned image -> ocr
        Overall document extraction_method is 'hybrid'.
        """
        pdf_bytes = generate_mixed_pdf()
        mock_ocr = MockOCRExtractor(
            simulated_page_texts=["Page 1 unused", "PAGE 2 SCANNED DRAWING OCR TEXT"],
            default_confidence=0.88,
        )
        hybrid = HybridDocumentExtractor(ocr_extractor=mock_ocr, min_chars_for_native=40)

        result = await hybrid.extract_from_bytes(pdf_bytes, filename="mixed_set.pdf")

        assert result.total_pages == 2
        assert result.extraction_method == "hybrid"

        # Page 1 must be native
        p1 = result.pages[0]
        assert p1.page_number == 1
        assert p1.extraction_method == "native_pdf"
        assert "Native engineering specification" in p1.text

        # Page 2 must be OCR
        p2 = result.pages[1]
        assert p2.page_number == 2
        assert p2.extraction_method == "ocr"
        assert p2.ocr_confidence == 0.88
        assert "SCANNED DRAWING OCR TEXT" in p2.text

    async def test_hybrid_raises_on_scanned_page_when_no_ocr_available(self):
        """When a scanned page requires OCR but no OCR adapter is configured, it raises OCRExecutableNotFoundError."""
        pdf_bytes = generate_scanned_image_pdf("SCANNED DRAWING NO OCR")
        # Explicit None OCR extractor
        hybrid = HybridDocumentExtractor(ocr_extractor=None, use_mock_ocr_fallback=False)

        with pytest.raises(OCRExecutableNotFoundError) as exc_info:
            await hybrid.extract_from_bytes(pdf_bytes, filename="unsupported_scan.pdf")
        assert "ocr is required" in str(exc_info.value).lower()


# =====================================================================
# 5. Schema Validation & Contract Tests
# =====================================================================

class TestExtractionContracts:
    """Verifies Pydantic schema validation, serialization, and structure."""

    def test_bounding_box_schema(self):
        bbox = BoundingBox(
            x_min=0.1,
            y_min=0.2,
            x_max=0.8,
            y_max=0.9,
            page_number=1,
            text_snippet="Column C-1",
            confidence=0.98,
        )
        assert bbox.x0 == 0.1
        assert bbox.y0 == 0.2
        assert bbox.x1 == 0.8
        assert bbox.y1 == 0.9
        assert bbox.page_number == 1
        data = bbox.model_dump()
        assert data["confidence"] == 0.98

    def test_extracted_table_schema(self):
        table = ExtractedTable(
            page_number=1,
            headers=["Rebar Mark", "Diameter (mm)", "Spacing (mm)"],
            rows=[["T-1", "16", "150"], ["T-2", "20", "200"]],
            row_count=2,
            col_count=3,
        )
        assert table.row_count == 2
        assert table.col_count == 3
        assert len(table.headers) == 3
        assert table.rows[0] == ["T-1", "16", "150"]

    def test_extracted_document_full_text_property(self):
        doc = ExtractedDocument(
            document_id=uuid4(),
            filename="composite.pdf",
            total_pages=2,
            pages=[
                ExtractedPage(page_number=1, raw_text="First page clause.", extraction_method="native_pdf"),
                ExtractedPage(page_number=2, raw_text="Second page schedule.", extraction_method="native_pdf"),
            ],
            overall_method="native_pdf",
        )
        assert "First page clause." in doc.full_text
        assert "Second page schedule." in doc.full_text
        assert doc.total_characters == len("First page clause.") + len("Second page schedule.")
        assert doc.total_words == 6
