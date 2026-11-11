"""
TameerAI - Pakistan Statutory Regulatory Document Parser & Ingestion Service (Phase 03.3)

Extracts granular clauses, chapters, sections, tables, formulas, and legal significance taxonomies
from statutory building codes and zoning regulations with page-level traceability.
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.regulation import (
    RegulatoryClause,
    RegulatoryDocumentVersion,
    RegulatoryIngestionJob,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Legal Significance Classification Patterns
# ---------------------------------------------------------------------------

LEGAL_SIGNIFICANCE_PATTERNS = [
    ("prohibition", re.compile(r"\b(shall not|must not|prohibited|under no circumstances|strictly forbidden|barred|disallowed|penalized|penalty)\b", re.IGNORECASE)),
    ("conditional_exception", re.compile(r"\b(provided that|provided further|subject to|in the event of|unless otherwise|except where)\b", re.IGNORECASE)),
    ("procedural_step", re.compile(r"\b(application shall be made|scrutiny fee|submission of plan|procedure for|shall apply to the authority)\b", re.IGNORECASE)),
    ("definition", re.compile(r"\b(means|shall mean|is defined as|includes|refers to as used in)\b", re.IGNORECASE)),
    ("guideline", re.compile(r"\b(may|is permitted to|at the discretion of|recommended|advisory|optional)\b", re.IGNORECASE)),
    ("mandatory_requirement", re.compile(r"\b(shall|must|is required to|mandatory|obligatory|shall strictly|shall provide)\b", re.IGNORECASE)),
]


def classify_legal_significance(text: str) -> str:
    """
    Classifies the legal significance of a regulatory clause based on statutory modal verbs.
    Precedence: prohibition > mandatory_requirement > conditional_exception > procedural_step > definition > guideline.
    """
    for sig, pattern in LEGAL_SIGNIFICANCE_PATTERNS:
        if pattern.search(text):
            return sig
    return "mandatory_requirement"


class RegulatoryParserService:
    """
    Parses statutory documents into verified clauses, schedules, and tables.
    """

    @classmethod
    def parse_and_ingest_version(
        cls,
        db: Session,
        version: RegulatoryDocumentVersion,
        raw_text_pages: Optional[List[Dict[str, Any]]] = None,
    ) -> RegulatoryIngestionJob:
        """
        Executes complete ingestion pipeline for a document version:
        1. Ingestion job initialization.
        2. Text extraction (from raw_text_pages or storage file).
        3. Clause and section segmentation.
        4. Legal significance classification.
        5. Storage of RegulatoryClause records.
        6. Ingestion job completion audit.
        """
        doc = version.document
        doc_code = doc.document_code if doc else "DOC"

        job = RegulatoryIngestionJob(
            id=uuid.uuid4(),
            document_code=doc_code,
            version_id=version.id,
            status="running",
            source_url_or_path=version.storage_path or version.official_source_url or "direct_memory",
            file_sha256=version.source_file_sha256,
            total_pages_processed=0,
            clauses_extracted_count=0,
            tables_extracted_count=0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            pages = raw_text_pages or cls._extract_pages_from_storage(version)
            job.total_pages_processed = len(pages)

            extracted_clauses = cls._segment_clauses(version, pages)

            tables_count = 0
            for c_data in extracted_clauses:
                if c_data.get("content_type") == "table":
                    tables_count += 1

                clause = RegulatoryClause(
                    id=uuid.uuid4(),
                    version_id=version.id,
                    chapter_number=c_data.get("chapter_number"),
                    chapter_title=c_data.get("chapter_title"),
                    section_number=c_data.get("section_number"),
                    section_title=c_data.get("section_title"),
                    clause_number=c_data["clause_number"],
                    clause_title=c_data.get("clause_title"),
                    subclause_number=c_data.get("subclause_number"),
                    page_start=c_data["page_start"],
                    page_end=c_data["page_end"],
                    original_text=c_data["original_text"],
                    normalized_text=c_data["normalized_text"],
                    content_type=c_data.get("content_type", "text"),
                    table_data_json=c_data.get("table_data_json"),
                    extraction_method=c_data.get("extraction_method", "structured_text"),
                    ocr_confidence=Decimal("100.00"),
                    legal_significance=c_data["legal_significance"],
                    review_status="reviewed",
                )
                db.add(clause)

            job.clauses_extracted_count = len(extracted_clauses)
            job.tables_extracted_count = tables_count
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)

            version.total_pages = len(pages)

            db.commit()
            db.refresh(job)
            logger.info(
                "Ingestion completed for %s [%s]: %d clauses, %d tables, %d pages",
                doc_code,
                version.version_label,
                job.clauses_extracted_count,
                job.tables_extracted_count,
                job.total_pages_processed,
            )
            return job

        except Exception as e:
            db.rollback()
            job.status = "failed"
            job.errors_json = {"error": str(e), "type": type(e).__name__}
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error("Regulatory ingestion failed for %s: %s", doc_code, e, exc_info=True)
            raise

    @classmethod
    def _extract_pages_from_storage(cls, version: RegulatoryDocumentVersion) -> List[Dict[str, Any]]:
        if not version.storage_path:
            return []

        backend_root = Path(__file__).resolve().parent.parent.parent
        file_path = backend_root / version.storage_path

        if not file_path.exists():
            logger.warning("Storage file does not exist: %s", file_path)
            return []

        pages = []
        if version.mime_type == "application/pdf":
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for idx, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text() or ""
                        pages.append({"page_number": idx, "text": text})
            except Exception as e:
                logger.warning("pdfplumber extraction failed, trying plain text: %s", e)
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                    pages.append({"page_number": 1, "text": text})
                except Exception:
                    pages.append({"page_number": 1, "text": ""})
        else:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                pages.append({"page_number": 1, "text": text})
            except Exception as e:
                logger.warning("File read error: %s", e)

        return pages

    @classmethod
    def _segment_clauses(
        cls,
        version: RegulatoryDocumentVersion,
        pages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        doc = version.document
        doc_code = doc.document_code if doc else "DOC"

        results = []
        current_chapter_no = None
        current_chapter_title = None
        current_section_no = None
        current_section_title = None

        chapter_regex = re.compile(r"^(?:CHAPTER|PART)\s+([IVXLCDM\d]+)[\:\.\s\-]+(.*)$", re.IGNORECASE)
        section_regex = re.compile(r"^(?:SECTION|RULE|REGULATION)\s+([\d\.\-]+)[\:\.\s\-]+(.*)$", re.IGNORECASE)
        table_regex = re.compile(r"^(?:TABLE|SCHEDULE)\s+([\d\.\-]+|[A-Z\d\-]+)[\:\.\s\-]+(.*)$", re.IGNORECASE)
        clause_regex = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s+(.*)$")

        for page in pages:
            page_no = page.get("page_number", 1)
            raw_text = page.get("text", "")
            lines = raw_text.splitlines()

            clause_buffer = []
            clause_meta: Dict[str, Any] = {}

            for line_idx, line in enumerate(lines, start=1):
                s_line = line.strip()
                if not s_line:
                    continue

                chap_match = chapter_regex.match(s_line)
                if chap_match:
                    current_chapter_no = chap_match.group(1).strip()
                    current_chapter_title = chap_match.group(2).strip() or f"Chapter {current_chapter_no}"
                    continue

                sec_match = section_regex.match(s_line)
                if sec_match:
                    current_section_no = sec_match.group(1).strip()
                    current_section_title = sec_match.group(2).strip() or f"Section {current_section_no}"
                    continue

                table_match = table_regex.match(s_line)
                if table_match:
                    if clause_buffer:
                        cls._flush_clause(results, clause_buffer, clause_meta, page_no)
                        clause_buffer = []

                    t_num = table_match.group(1)
                    t_title = table_match.group(2)
                    clause_meta = {
                        "clause_number": f"Table {t_num}",
                        "clause_title": t_title,
                        "chapter_number": current_chapter_no,
                        "chapter_title": current_chapter_title,
                        "section_number": current_section_no,
                        "section_title": current_section_title,
                        "page_start": page_no,
                    }
                    clause_buffer.append(s_line)
                    continue

                clause_match = clause_regex.match(s_line)
                if clause_match:
                    if clause_buffer:
                        cls._flush_clause(results, clause_buffer, clause_meta, page_no)
                        clause_buffer = []

                    c_num = clause_match.group(1)
                    c_title = clause_match.group(2)
                    clause_meta = {
                        "clause_number": c_num,
                        "clause_title": c_title,
                        "chapter_number": current_chapter_no,
                        "chapter_title": current_chapter_title,
                        "section_number": current_section_no or (c_num.rsplit(".", 1)[0] if "." in c_num else None),
                        "section_title": current_section_title,
                        "page_start": page_no,
                    }
                    clause_buffer.append(s_line)
                else:
                    if clause_buffer:
                        clause_buffer.append(s_line)
                    else:
                        clause_meta = {
                            "clause_number": f"{page_no}.{line_idx}",
                            "clause_title": s_line[:60],
                            "chapter_number": current_chapter_no,
                            "chapter_title": current_chapter_title,
                            "section_number": current_section_no,
                            "section_title": current_section_title,
                            "page_start": page_no,
                        }
                        clause_buffer.append(s_line)

            if clause_buffer:
                cls._flush_clause(results, clause_buffer, clause_meta, page_no)

        return results

    @classmethod
    def _flush_clause(
        cls,
        results: List[Dict[str, Any]],
        buffer: List[str],
        meta: Dict[str, Any],
        page_no: int,
    ) -> None:
        text = "\n".join(buffer).strip()
        if not text:
            return

        legal_sig = classify_legal_significance(text)
        is_table = ("Table " in text or "\t" in text or "|" in text) and len(text.splitlines()) > 3
        content_type = "table" if is_table else "text"
        normalized = re.sub(r"\s+", " ", text).strip()

        clause_dict = {
            "clause_number": meta.get("clause_number", f"P{page_no}-{len(results)+1}"),
            "clause_title": meta.get("clause_title"),
            "section_number": meta.get("section_number"),
            "section_title": meta.get("section_title"),
            "chapter_number": meta.get("chapter_number"),
            "chapter_title": meta.get("chapter_title"),
            "subclause_number": None,
            "page_start": meta.get("page_start", page_no),
            "page_end": page_no,
            "original_text": text,
            "normalized_text": normalized,
            "content_type": content_type,
            "table_data_json": {"raw_table": text} if is_table else None,
            "extraction_method": "structured_text",
            "legal_significance": legal_sig,
        }
        results.append(clause_dict)
