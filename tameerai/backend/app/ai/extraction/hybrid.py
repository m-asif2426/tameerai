"""
TameerAI - Hybrid Multi-Page Document Extractor (Phase 03B)
Intelligently inspects individual PDF pages: routes readable native text pages to
NativePDFExtractor and scanned/image pages to the OCR adapter.
Prevents redundant OCR while preserving strict page ordering and metadata.
"""

import time
from pathlib import Path
from typing import List, Optional, Union
from uuid import UUID, uuid4

import pypdfium2
from PIL import Image

from app.ai.contracts.extraction import (
    BoundingBox,
    DocumentExtractor,
    ExtractedDocument,
    ExtractedPage,
    ExtractionRequest,
    OCRExecutableNotFoundError,
)
from app.core.config import settings
from app.ai.extraction.native import NativePDFExtractor
from app.ai.extraction.ocr import (
    MockOCRExtractor,
    TesseractOCRExtractor,
    find_tesseract_binary,
)
from app.ai.extraction.safety import (
    MAX_RASTER_DIMENSION,
    validate_file_size,
    validate_page_count,
    validate_safe_path,
)

# Text length threshold below which an image-containing page is routed to OCR
DEFAULT_NATIVE_TEXT_THRESHOLD_CHARS = 40


class HybridDocumentExtractor(DocumentExtractor):
    """
    Intelligent hybrid document intelligence pipeline.
    Combines high-speed native extraction with selective per-page OCR fallback.
    """
    def __init__(
        self,
        native_extractor: Optional[NativePDFExtractor] = None,
        ocr_extractor: Optional[DocumentExtractor] = None,
        use_mock_ocr_fallback: Optional[bool] = None,
        min_chars_for_native: int = DEFAULT_NATIVE_TEXT_THRESHOLD_CHARS,
    ):
        self.native_extractor = native_extractor or NativePDFExtractor()
        self.min_chars_for_native = min_chars_for_native

        # Production safety guardrail: NEVER silently fabricate mock OCR in production
        is_prod = (getattr(settings, "ENVIRONMENT", "").lower() == "production")
        if use_mock_ocr_fallback is None:
            allow_mock = not is_prod
        else:
            if is_prod and use_mock_ocr_fallback:
                raise ValueError("Mock OCR fallback cannot be enabled in production environment.")
            allow_mock = use_mock_ocr_fallback

        # If OCR extractor explicitly given (including None)
        if ocr_extractor is not None:
            self.ocr_extractor = ocr_extractor
        elif find_tesseract_binary():
            self.ocr_extractor = TesseractOCRExtractor()
        elif allow_mock:
            self.ocr_extractor = MockOCRExtractor()
        else:
            self.ocr_extractor = None

    async def extract_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "document.pdf",
        project_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        **kwargs,
    ) -> ExtractedDocument:
        req = ExtractionRequest(
            document_id=document_id or uuid4(),
            project_id=project_id or uuid4(),
            file_bytes=pdf_bytes,
            **kwargs,
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
        **kwargs,
    ) -> ExtractedDocument:
        resolved = validate_safe_path(file_path)
        req = ExtractionRequest(
            document_id=document_id or uuid4(),
            project_id=project_id or uuid4(),
            file_path=str(resolved),
            **kwargs,
        )
        doc = await self.extract_document(req)
        doc.filename = filename or resolved.name
        return doc

    async def extract_document(self, request: ExtractionRequest) -> ExtractedDocument:
        start_time = time.monotonic()

        # 1. First run native extraction pass
        native_result = await self.native_extractor.extract_document(request)

        # If OCR fallback is disabled, return native result directly
        if not request.perform_ocr_fallback:
            return native_result

        # Resolve PDF bytes for rasterization if needed
        pdf_bytes = request.file_bytes
        if pdf_bytes is None and request.file_path:
            pdf_bytes = validate_safe_path(request.file_path).read_bytes()

        processed_pages: List[ExtractedPage] = []
        ocr_pages_count = 0
        native_pages_count = 0
        pdf_doc = None

        for page in native_result.pages:
            # Check if this page requires OCR:
            # Condition: Page has image elements, and native text is below threshold
            needs_ocr = page.is_scanned and (len(page.raw_text.strip()) < self.min_chars_for_native)

            if not needs_ocr:
                native_pages_count += 1
                processed_pages.append(page)
                continue

            # Page needs OCR: check if OCR extractor is available
            if self.ocr_extractor is None:
                raise OCRExecutableNotFoundError(
                    f"OCR is required for page {page.page_number} (scanned image with no native text), "
                    "but no OCR extractor is configured or available."
                )

            # Route this specific page to OCR
            if pdf_doc is None and pdf_bytes:
                try:
                    pdf_doc = pypdfium2.PdfDocument(pdf_bytes)
                except Exception:
                    pdf_doc = None

            ocr_text = ""
            ocr_conf = None
            ocr_err = None
            bboxes: List[BoundingBox] = []

            if isinstance(self.ocr_extractor, MockOCRExtractor):
                # Mock OCR execution
                p_idx = page.page_number - 1
                if self.ocr_extractor.simulated_page_texts and p_idx < len(self.ocr_extractor.simulated_page_texts):
                    ocr_text = self.ocr_extractor.simulated_page_texts[p_idx]
                elif self.ocr_extractor.custom_ocr_text:
                    ocr_text = self.ocr_extractor.custom_ocr_text
                else:
                    ocr_text = f"[OCR EXTRACTED] Scanned text recognized on page {page.page_number}."

                ocr_conf = self.ocr_extractor.simulated_confidence
                bboxes.append(
                    BoundingBox(
                        x_min=0.1,
                        y_min=0.1,
                        x_max=0.9,
                        y_max=0.3,
                        page_number=page.page_number,
                        text_snippet=ocr_text[:40],
                        confidence=ocr_conf,
                    )
                )

            elif isinstance(self.ocr_extractor, TesseractOCRExtractor):
                if not self.ocr_extractor.is_available:
                    raise OCRExecutableNotFoundError(
                        "Tesseract OCR executable is not installed or available on this system."
                    )
                if pdf_doc is not None:
                    try:
                        p_idx = page.page_number - 1
                        if p_idx < len(pdf_doc):
                            pil_img: Image.Image = pdf_doc[p_idx].render(scale=2.0).to_pil()
                            if pil_img.width > MAX_RASTER_DIMENSION or pil_img.height > MAX_RASTER_DIMENSION:
                                pil_img.thumbnail((MAX_RASTER_DIMENSION, MAX_RASTER_DIMENSION))

                            import pytesseract
                            data = pytesseract.image_to_data(
                                pil_img,
                                lang=request.ocr_language,
                                output_type=pytesseract.Output.DICT
                            )
                            words = [w.strip() for w in data.get("text", []) if w.strip()]
                            ocr_text = " ".join(words)
                            confs = [float(c) for c in data.get("conf", []) if float(c) > 0]
                            ocr_conf = (sum(confs) / len(confs)) / 100.0 if confs else 0.0

                            w_img, h_img = float(pil_img.width), float(pil_img.height)
                            for i in range(len(data.get("text", []))):
                                w_text = data["text"][i].strip()
                                w_conf = float(data["conf"][i])
                                if w_text and w_conf > 0:
                                    x = float(data["left"][i])
                                    y = float(data["top"][i])
                                    w = float(data["width"][i])
                                    h = float(data["height"][i])
                                    bboxes.append(
                                        BoundingBox(
                                            x_min=min(max(x / w_img, 0.0), 1.0),
                                            y_min=min(max(y / h_img, 0.0), 1.0),
                                            x_max=min(max((x + w) / w_img, 0.0), 1.0),
                                            y_max=min(max((y + h) / h_img, 0.0), 1.0),
                                            page_number=page.page_number,
                                            text_snippet=w_text,
                                            confidence=round(w_conf / 100.0, 4),
                                        )
                                    )
                    except Exception as e:
                        ocr_err = f"OCR fallback failed on page {page.page_number}: {e}"

            ocr_pages_count += 1
            updated_warnings = list(page.warnings)
            updated_warnings.append(
                f"Page {page.page_number} routed to OCR fallback due to scanned image content."
            )
            updated_errors = list(page.errors)
            if ocr_err:
                updated_errors.append(ocr_err)

            processed_pages.append(
                ExtractedPage(
                    page_number=page.page_number,
                    raw_text=ocr_text if ocr_text else page.raw_text,
                    extraction_method="ocr" if ocr_text else "native_pdf",
                    ocr_confidence=round(ocr_conf, 4) if ocr_conf is not None else None,
                    tables=page.tables,
                    bounding_boxes=bboxes,
                    is_scanned=True,
                    is_empty=(len(ocr_text.strip()) == 0 and len(page.raw_text.strip()) == 0),
                    rotation=page.rotation,
                    width=page.width,
                    height=page.height,
                    language_hints=page.language_hints,
                    warnings=updated_warnings,
                    errors=updated_errors,
                    metadata={"routed_to_ocr": True, "original_native_length": len(page.raw_text)},
                )
            )

        # Determine overall extraction method
        if ocr_pages_count > 0 and native_pages_count > 0:
            overall_method = "hybrid"
        elif ocr_pages_count > 0:
            overall_method = "ocr"
        else:
            overall_method = "native_pdf"

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return ExtractedDocument(
            document_id=request.document_id,
            total_pages=native_result.total_pages,
            pages=processed_pages,
            overall_method=overall_method,
            is_encrypted=native_result.is_encrypted,
            is_scanned_only=(native_pages_count == 0 and ocr_pages_count > 0),
            processing_time_ms=elapsed_ms,
            warnings=native_result.warnings,
            errors=native_result.errors,
            metadata={
                "extractor": "HybridDocumentExtractor",
                "native_pages_count": native_pages_count,
                "ocr_pages_count": ocr_pages_count,
            },
        )
