"""
TameerAI - Structured Document Chunking Service (Phase 03C)
Splits ExtractedDocuments, pages, and tabular schedules into schema-compliant chunks
with exact page provenance, heading detection, and regulatory clause boundary protection.
"""

import hashlib
import time
import uuid
from typing import Dict, List, Optional, Set
from uuid import UUID

from app.ai.contracts.chunking import (
    ChunkingConfig,
    ChunkingResult,
    DocumentChunkerProtocol,
    StructuredChunk,
)
from app.ai.contracts.extraction import (
    ExtractedDocument,
    ExtractedPage,
    ExtractedTable,
)
from app.ai.chunking.rules import (
    extract_headings,
    split_into_semantic_paragraphs,
)


class DocumentChunkingService(DocumentChunkerProtocol):
    """
    Production-grade document chunking service.
    Processes ExtractedDocument structures from Phase 03B with full page and scope provenance.
    """

    def __init__(self, default_config: Optional[ChunkingConfig] = None):
        self.default_config = default_config or ChunkingConfig()

    def _estimate_tokens(self, text: str) -> int:
        """Approximates token count based on whitespace word count scaled by 1.33."""
        if not text:
            return 0
        words = len(text.strip().split())
        return max(1, int(words * 1.33))

    def _format_table_content(self, table: ExtractedTable) -> str:
        """Formats an extracted table into a clean markdown-like text block."""
        lines = []
        if table.headers:
            lines.append(" | ".join(table.headers))
            lines.append(" | ".join(["---"] * len(table.headers)))
        for row in table.rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)

    def chunk_extracted_document(
        self,
        document: ExtractedDocument,
        config: Optional[ChunkingConfig] = None,
        knowledge_source_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        source_title: Optional[str] = None,
        source_code: Optional[str] = None,
        source_version: Optional[str] = "1.0",
        is_synthetic: bool = False,
    ) -> ChunkingResult:
        """
        Chunks an ExtractedDocument object page by page.
        Preserves page numbers, rotation, extraction method, and table schedules.
        """
        cfg = config or self.default_config
        start_time = time.monotonic()
        warnings: List[str] = []

        # Scope boundary check
        effective_doc_id = document_id or document.document_id
        if knowledge_source_id is not None and (project_id is not None or document_id is not None):
            raise ValueError(
                "Scope violation: Cannot assign both knowledge_source_id and project_id/document_id. "
                "Chunks must be either strictly global regulatory or strictly project-private."
            )

        chunks: List[StructuredChunk] = []
        seen_hashes: Set[str] = set()
        chunk_idx = 0
        total_chars = 0
        total_tokens = 0

        current_chapter: Optional[str] = None
        current_section: Optional[str] = None

        for page in document.pages:
            page_text = page.raw_text.strip()
            page_no = page.page_number
            method = page.extraction_method

            # Extract headings from page text if present
            c_head, s_head = extract_headings(page_text)
            if c_head:
                current_chapter = c_head
            if s_head:
                current_section = s_head

            # 1. Chunk native / OCR page text
            paragraphs = split_into_semantic_paragraphs(page_text)
            current_buffer: List[str] = []
            current_buffer_len = 0

            for para in paragraphs:
                p_len = len(para)

                # Check if paragraph by itself contains new clause/heading
                p_chap, p_sec = extract_headings(para)
                if p_chap:
                    current_chapter = p_chap
                if p_sec:
                    current_section = p_sec

                if current_buffer_len + p_len + 1 <= cfg.chunk_size:
                    current_buffer.append(para)
                    current_buffer_len += p_len + 1
                else:
                    if current_buffer:
                        combined = "\n\n".join(current_buffer).strip()
                        if len(combined) >= cfg.min_chunk_size:
                            c_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                            if c_hash not in seen_hashes:
                                seen_hashes.add(c_hash)
                                t_count = self._estimate_tokens(combined) if cfg.estimate_tokens else 0
                                c_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{effective_doc_id}_{page_no}_{chunk_idx}_{c_hash}")

                                chunk = StructuredChunk(
                                    id=c_uuid,
                                    knowledge_source_id=knowledge_source_id,
                                    project_id=project_id,
                                    document_id=effective_doc_id if project_id else None,
                                    chunk_index=chunk_idx,
                                    content=combined,
                                    chapter=current_chapter,
                                    section=current_section,
                                    page_number=page_no,
                                    token_count=t_count,
                                    content_hash=c_hash,
                                    extraction_method=method,
                                    source_title=source_title or document.filename or "Untitled Document",
                                    source_code=source_code or (f"DOC-{str(effective_doc_id)[:8]}" if project_id else "CODEX"),
                                    source_version=source_version or "1.0",
                                    is_synthetic=is_synthetic,
                                    metadata_json={
                                        "page_number": page_no,
                                        "rotation": page.rotation,
                                        "is_scanned": page.is_scanned,
                                        "ocr_confidence": page.ocr_confidence,
                                    },
                                )
                                chunks.append(chunk)
                                chunk_idx += 1
                                total_chars += len(combined)
                                total_tokens += t_count

                    # Handle overlap: take trailing paragraph if within overlap budget
                    if cfg.chunk_overlap > 0 and current_buffer:
                        last_p = current_buffer[-1]
                        if len(last_p) <= cfg.chunk_overlap:
                            current_buffer = [last_p, para]
                            current_buffer_len = len(last_p) + len(para) + 1
                        else:
                            current_buffer = [para]
                            current_buffer_len = len(para)
                    else:
                        current_buffer = [para]
                        current_buffer_len = len(para)

            # Flush remaining page text buffer
            if current_buffer:
                combined = "\n\n".join(current_buffer).strip()
                if len(combined) >= cfg.min_chunk_size:
                    c_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                    if c_hash not in seen_hashes:
                        seen_hashes.add(c_hash)
                        t_count = self._estimate_tokens(combined) if cfg.estimate_tokens else 0
                        c_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{effective_doc_id}_{page_no}_{chunk_idx}_{c_hash}")

                        chunk = StructuredChunk(
                            id=c_uuid,
                            knowledge_source_id=knowledge_source_id,
                            project_id=project_id,
                            document_id=effective_doc_id if project_id else None,
                            chunk_index=chunk_idx,
                            content=combined,
                            chapter=current_chapter,
                            section=current_section,
                            page_number=page_no,
                            token_count=t_count,
                            content_hash=c_hash,
                            extraction_method=method,
                            source_title=source_title or document.filename or "Untitled Document",
                            source_code=source_code or (f"DOC-{str(effective_doc_id)[:8]}" if project_id else "CODEX"),
                            source_version=source_version or "1.0",
                            is_synthetic=is_synthetic,
                            metadata_json={
                                "page_number": page_no,
                                "rotation": page.rotation,
                                "is_scanned": page.is_scanned,
                                "ocr_confidence": page.ocr_confidence,
                            },
                        )
                        chunks.append(chunk)
                        chunk_idx += 1
                        total_chars += len(combined)
                        total_tokens += t_count

            # 2. Chunk tabular schedules on this page as separate structured chunks
            for t_idx, table in enumerate(page.tables):
                table_str = self._format_table_content(table).strip()
                if len(table_str) >= cfg.min_chunk_size:
                    t_hash = hashlib.sha256(table_str.encode("utf-8")).hexdigest()
                    if t_hash not in seen_hashes:
                        seen_hashes.add(t_hash)
                        t_count = self._estimate_tokens(table_str) if cfg.estimate_tokens else 0
                        c_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{effective_doc_id}_{page_no}_tbl_{t_idx}_{t_hash}")

                        chunk = StructuredChunk(
                            id=c_uuid,
                            knowledge_source_id=knowledge_source_id,
                            project_id=project_id,
                            document_id=effective_doc_id if project_id else None,
                            chunk_index=chunk_idx,
                            content=table_str,
                            chapter=current_chapter,
                            section=f"Table Schedule {t_idx + 1}",
                            page_number=page_no,
                            token_count=t_count,
                            content_hash=t_hash,
                            extraction_method=method,
                            source_title=source_title or document.filename or "Untitled Document",
                            source_code=source_code or (f"DOC-{str(effective_doc_id)[:8]}" if project_id else "CODEX"),
                            source_version=source_version or "1.0",
                            is_synthetic=is_synthetic,
                            metadata_json={
                                "page_number": page_no,
                                "is_table": True,
                                "row_count": table.row_count,
                                "col_count": table.col_count,
                            },
                        )
                        chunks.append(chunk)
                        chunk_idx += 1
                        total_chars += len(table_str)
                        total_tokens += t_count

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return ChunkingResult(
            document_id=effective_doc_id if project_id else None,
            knowledge_source_id=knowledge_source_id,
            project_id=project_id,
            total_chunks=len(chunks),
            total_characters=total_chars,
            total_tokens=total_tokens,
            chunks=chunks,
            warnings=warnings,
            processing_time_ms=elapsed_ms,
        )

    def chunk_document(
        self,
        document_text: str,
        config: Optional[ChunkingConfig] = None,
        knowledge_source_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        source_title: Optional[str] = "Raw Document",
        source_code: Optional[str] = "DOC",
        page_number: int = 1,
        is_synthetic: bool = False,
        **kwargs,
    ) -> ChunkingResult:
        """Convenience method for chunking plain text string."""
        from app.ai.contracts.extraction import ExtractedDocument, ExtractedPage
        mock_doc = ExtractedDocument(
            document_id=document_id or uuid.uuid4(),
            filename=source_title,
            total_pages=1,
            pages=[
                ExtractedPage(
                    page_number=page_number,
                    raw_text=document_text,
                    extraction_method="native_pdf",
                )
            ],
            overall_method="native_pdf",
        )
        return self.chunk_extracted_document(
            document=mock_doc,
            config=config,
            knowledge_source_id=knowledge_source_id,
            project_id=project_id,
            document_id=document_id,
            source_title=source_title,
            source_code=source_code,
            is_synthetic=is_synthetic,
        )

