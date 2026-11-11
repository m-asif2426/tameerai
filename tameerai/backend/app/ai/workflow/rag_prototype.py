"""
TameerAI - Synthetic End-to-End RAG Pipeline Prototype (Phase 03C)
Connects extraction, chunking, mock embeddings, hybrid retrieval, and citation validation
into a deterministic, offline, multi-tenant-safe execution workflow.
Zero network access; zero external API calls.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai.chunking.service import DocumentChunkingService
from app.ai.contracts.chunking import ChunkingConfig
from app.ai.contracts.extraction import ExtractedDocument
from app.ai.contracts.retrieval import RetrievalQuery, ScopeType
from app.ai.contracts.validation import CitationValidationReport
from app.ai.embedding.mock import MockEmbeddingProvider
from app.ai.retrieval.service import ScopedRetrievalService
from app.ai.validation.citation import CitationValidator


class RAGGenerationResponse(BaseModel):
    """Structured response from the end-to-end RAG workflow."""
    query: str
    project_id: Optional[UUID] = None
    answer_text: str
    retrieved_chunks_count: int
    citations: List[Dict[str, Any]]
    validation_report: CitationValidationReport
    is_grounded: bool
    is_synthetic_test: bool = True
    grounding_disclaimer: str
    execution_time_ms: float


class SyntheticRAGPipeline:
    """
    Offline End-to-End RAG prototype pipeline.
    Demonstrates ingestion, indexing, retrieval, synthesis, and citation auditing.
    """

    def __init__(
        self,
        chunking_service: Optional[DocumentChunkingService] = None,
        embedding_provider: Optional[MockEmbeddingProvider] = None,
        retrieval_service: Optional[ScopedRetrievalService] = None,
        citation_validator: Optional[CitationValidator] = None,
    ):
        self.chunking_service = chunking_service or DocumentChunkingService()
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.retrieval_service = retrieval_service or ScopedRetrievalService(
            embedding_provider=self.embedding_provider
        )
        self.citation_validator = citation_validator or CitationValidator()

    async def ingest_document(
        self,
        document: ExtractedDocument,
        project_id: Optional[UUID] = None,
        knowledge_source_id: Optional[UUID] = None,
        source_title: Optional[str] = None,
        source_code: Optional[str] = None,
        config: Optional[ChunkingConfig] = None,
    ) -> int:
        """Chunks and indexes an extracted document into the retrieval engine."""
        chunk_result = self.chunking_service.chunk_extracted_document(
            document=document,
            config=config,
            project_id=project_id,
            knowledge_source_id=knowledge_source_id,
            source_title=source_title,
            source_code=source_code,
            is_synthetic=True,
        )

        await self.retrieval_service.ingest_chunks(chunk_result.chunks)
        return chunk_result.total_chunks

    async def execute_query(
        self,
        query_text: str,
        project_id: Optional[UUID] = None,
        requesting_user_id: Optional[UUID] = None,
        scope: ScopeType = ScopeType.HYBRID,
        top_k: int = 5,
    ) -> RAGGenerationResponse:
        """
        Executes an end-to-end RAG question-answering workflow with strict citation verification.
        """
        start_time = time.monotonic()

        # 1. Scoped retrieval
        retrieval_query = RetrievalQuery(
            query_text=query_text,
            project_id=project_id,
            scope=scope,
            top_k=top_k,
            minimum_score=0.1,
        )

        retrieval_result = await self.retrieval_service.retrieve(
            query=retrieval_query,
            requesting_user_id=requesting_user_id,
            allow_synthetic=True,  # Synthetic prototype mode
        )

        # 2. Formulate grounded synthetic response and extracted citations
        generated_citations: List[Dict[str, Any]] = []
        answer_parts: List[str] = []

        if retrieval_result.chunks:
            answer_parts.append(
                f"[SYNTHETIC RAG ANSWER] Based on {len(retrieval_result.chunks)} retrieved evidence passage(s):"
            )
            for c in retrieval_result.chunks:
                answer_parts.append(f"- ({c.source_code}, Page {c.page_number}): {c.content[:120]}...")
                generated_citations.append({
                    "title": c.source_title,
                    "source_code": c.source_code,
                    "page_number": c.page_number,
                    "section_or_clause": c.clause_or_section,
                    "chunk_id": str(c.chunk_id),
                    "document_id": str(c.document_id) if c.document_id else None,
                    "project_id": str(c.project_id) if c.project_id else None,
                    "claim_text": c.content[:80],
                })
        else:
            answer_parts.append(
                "[SYNTHETIC RAG ANSWER] No verified evidence passages satisfied the scoped query criteria."
            )

        answer_text = "\n".join(answer_parts)

        # 3. Citation validation
        validation_report = self.citation_validator.validate_citations(
            citations=generated_citations,
            evidence_chunks=retrieval_result.chunks,
            project_id=project_id,
        )

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return RAGGenerationResponse(
            query=query_text,
            project_id=project_id,
            answer_text=answer_text,
            retrieved_chunks_count=len(retrieval_result.chunks),
            citations=generated_citations,
            validation_report=validation_report,
            is_grounded=validation_report.is_fully_grounded,
            is_synthetic_test=True,
            grounding_disclaimer=(
                "THIS IS A SYNTHETIC TEST PIPELINE RESULT. "
                "Evidence chunks are generated from synthetic test fixtures and have NOT been verified "
                "against real building codes (PBC, LDA, CDA, SBCA) or FIDIC contract forms."
            ),
            execution_time_ms=elapsed_ms,
        )

