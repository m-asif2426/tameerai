"""
TameerAI - OCR Document Extraction Adapters (Phase 03B)
Provides Tesseract-based raster page OCR and a deterministic Mock OCR adapter
for testing environments where external OCR binaries are not installed.
"""

import shutil
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
from app.ai.extraction.safety import (
    MAX_RASTER_DIMENSION,
    safe_temp_pdf_file,
    validate_file_size,
    validate_page_count,
    validate_safe_path,
)

# Common Windows installation directories for Tesseract
WINDOWS_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]


def find_tesseract_binary() -> Optional[str]:
    """Discovers tesseract executable in PATH or standard Windows directories."""
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path
    for p in WINDOWS_TESSERACT_PATHS:
        if p.exists() and p.is_file():
            return str(p)
    return None


class TesseractOCRExtractor(DocumentExtractor):
    """
    Local Tesseract OCR adapter.
    Renders PDF pages to high-resolution images via pypdfium2, applies bounded DPI
    scaling, and executes pytesseract with confidence calculation.
    """
    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd if tesseract_cmd is not None else find_tesseract_binary()

    @property
    def is_available(self) -> bool:
        if not self.tesseract_cmd:
            return False
        # If path provided, verify file existence or executable status
        if Path(self.tesseract_cmd).is_file():
            return True
        return shutil.which(self.tesseract_cmd) is not None

    async def extract_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "scanned.pdf",
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
        if not self.is_available:
            raise OCRExecutableNotFoundError(
                "Tesseract executable is not installed or not found on PATH. "
                "For local testing without Tesseract, use MockOCRExtractor."
            )

        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        start_time = time.monotonic()
        warnings: List[str] = []
        errors: List[str] = []

        # Resolve bytes
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

        # Open with pypdfium2 for rasterization
        try:
            pdf = pypdfium2.PdfDocument(pdf_bytes)
        except Exception as e:
            raise ValueError(f"Failed to load PDF for OCR rasterization: {e}")

        total_pages = len(pdf)
        validate_page_count(total_pages, request.max_pages)

        extracted_pages: List[ExtractedPage] = []

        for idx in range(total_pages):
            page_number = idx + 1
            page_warnings: List[str] = []
            page_errors: List[str] = []

            # Render page to PIL image at 300 DPI (scale ~4.16x, default 72dpi * 4.16)
            # Bound scale to prevent explosive memory consumption
            page = pdf[idx]
            pil_image: Image.Image = page.render(scale=2.0).to_pil()

            # Bound image dimensions
            if pil_image.width > MAX_RASTER_DIMENSION or pil_image.height > MAX_RASTER_DIMENSION:
                pil_image.thumbnail((MAX_RASTER_DIMENSION, MAX_RASTER_DIMENSION))
                page_warnings.append(
                    f"Page {page_number} exceeded max raster dimension; resized to {MAX_RASTER_DIMENSION}px."
                )

            # Perform OCR with bounding data
            try:
                data = pytesseract.image_to_data(
                    pil_image,
                    lang=request.ocr_language,
                    output_type=pytesseract.Output.DICT
                )
                words = [w.strip() for w in data.get("text", []) if w.strip()]
                clean_text = " ".join(words)

                # Calculate average word confidence
                confs = [float(c) for c in data.get("conf", []) if float(c) > 0]
                avg_conf = (sum(confs) / len(confs)) / 100.0 if confs else None

                # Build bounding boxes for words
                bboxes: List[BoundingBox] = []
                w_img, h_img = float(pil_image.width), float(pil_image.height)
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
                                page_number=page_number,
                                text_snippet=w_text,
                                confidence=round(w_conf / 100.0, 4),
                            )
                        )
            except Exception as e:
                clean_text = ""
                avg_conf = None
                bboxes = []
                page_errors.append(f"Tesseract OCR failed on page {page_number}: {e}")

            extracted_pages.append(
                ExtractedPage(
                    page_number=page_number,
                    raw_text=clean_text,
                    extraction_method="ocr",
                    ocr_confidence=round(avg_conf, 4) if avg_conf is not None else None,
                    bounding_boxes=bboxes,
                    is_scanned=True,
                    is_empty=(len(clean_text) == 0),
                    width=float(pil_image.width),
                    height=float(pil_image.height),
                    language_hints=[request.ocr_language],
                    warnings=page_warnings,
                    errors=page_errors,
                    metadata={"ocr_engine": "tesseract"},
                )
            )

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return ExtractedDocument(
            document_id=request.document_id,
            total_pages=total_pages,
            pages=extracted_pages,
            overall_method="ocr",
            is_scanned_only=True,
            processing_time_ms=elapsed_ms,
            warnings=warnings,
            errors=errors,
            metadata={"ocr_engine": "tesseract", "executable": self.tesseract_cmd},
        )


class MockOCRExtractor(DocumentExtractor):
    """
    Deterministic Mock OCR adapter.
    Simulates OCR on synthetic scanned/image pages without needing an external Tesseract binary.
    Zero network access; safe for offline automated test suites.
    """
    def __init__(
        self,
        default_confidence: float = 0.94,
        simulated_confidence: Optional[float] = None,
        should_fail: bool = False,
        custom_ocr_text: Optional[str] = None,
        simulated_page_texts: Optional[List[str]] = None,
    ):
        self.simulated_confidence = simulated_confidence if simulated_confidence is not None else default_confidence
        self.should_fail = should_fail
        self.custom_ocr_text = custom_ocr_text
        self.simulated_page_texts = simulated_page_texts

    @property
    def is_available(self) -> bool:
        return not self.should_fail

    async def extract_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "mock_scanned.pdf",
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
        if self.should_fail:
            raise OCRExecutableNotFoundError("Simulated OCR engine failure: binary unavailable.")

        start_time = time.monotonic()

        # Open and count pages using pypdfium2 or fallback
        pdf_bytes = request.file_bytes
        if pdf_bytes is None and request.file_path:
            pdf_bytes = validate_safe_path(request.file_path).read_bytes()
        if not pdf_bytes:
            raise ValueError("Request must supply file_bytes or file_path.")

        try:
            pdf = pypdfium2.PdfDocument(pdf_bytes)
            total_pages = len(pdf)
        except Exception:
            total_pages = 1

        validate_page_count(total_pages, request.max_pages)

        pages: List[ExtractedPage] = []
        for idx in range(total_pages):
            page_no = idx + 1
            if self.simulated_page_texts and idx < len(self.simulated_page_texts):
                text = self.simulated_page_texts[idx]
            elif self.custom_ocr_text:
                text = self.custom_ocr_text
            else:
                text = (
                    f"[MOCK OCR TEXT] Page {page_no}: Synthetic scanned construction specification. "
                    "All structural concrete shall achieve minimum compressive strength of 3000 PSI at 28 days."
                )

            # Simulated bounding box
            box = BoundingBox(
                x_min=0.1,
                y_min=0.1,
                x_max=0.9,
                y_max=0.3,
                page_number=page_no,
                text_snippet=text[:40],
                confidence=self.simulated_confidence,
            )

            pages.append(
                ExtractedPage(
                    page_number=page_no,
                    raw_text=text,
                    extraction_method="ocr",
                    ocr_confidence=self.simulated_confidence,
                    bounding_boxes=[box],
                    is_scanned=True,
                    is_empty=False,
                    width=612.0,
                    height=792.0,
                    language_hints=["en"],
                    metadata={"mock_ocr": True},
                )
            )

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return ExtractedDocument(
            document_id=request.document_id,
            total_pages=total_pages,
            pages=pages,
            overall_method="ocr",
            is_scanned_only=True,
            processing_time_ms=elapsed_ms,
            metadata={"mock_ocr": True, "engine": "MockOCRExtractor"},
        )
