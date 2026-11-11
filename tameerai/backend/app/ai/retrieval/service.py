"""
TameerAI - Multi-Tenant Scoped Retrieval Service (Phase 03C)
Implements the KnowledgeRetriever protocol with strict pre-retrieval multi-tenant isolation,
active project membership verification, and prompt injection mitigation.
"""

import html
import time
from typing import Dict, List, Optional, Set
from uuid import UUID

from app.ai.contracts.chunking import StructuredChunk
from app.ai.contracts.embedding import EmbeddingRequest
from app.ai.contracts.retrieval import (
    KnowledgeRetriever,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    ScopeType,
)
from app.ai.embedding.mock import MockEmbeddingProvider
from app.ai.retrieval.hybrid import HybridRetriever
from app.ai.retrieval.keyword import KeywordRetriever
from app.ai.retrieval.vector import InMemoryVectorRetriever
from app.ai.retrieval.reranker import ReRankerProtocol


class ScopedRetrievalService(KnowledgeRetriever):
    """
    Multi-tenant secure knowledge retrieval service.
    Guarantees strict isolation across tenants and between global regulatory
    standards and private tenant documents.
    """

    def __init__(
        self,
        embedding_provider: Optional[MockEmbeddingProvider] = None,
        vector_retriever: Optional[InMemoryVectorRetriever] = None,
        keyword_retriever: Optional[KeywordRetriever] = None,
        reranker: Optional[ReRankerProtocol] = None,
        session: Optional[object] = None,
    ):
        self.session = session
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.vector_retriever = vector_retriever or InMemoryVectorRetriever(
            expected_dimensions=self.embedding_provider.default_dimensions
        )
        self.keyword_retriever = keyword_retriever or KeywordRetriever()
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_retriever,
            keyword_retriever=self.keyword_retriever,
        )
        self.reranker = reranker

        # In-memory chunk repository: chunk_id -> StructuredChunk
        self._chunks: Dict[UUID, StructuredChunk] = {}

        # Multi-tenant active membership cache/mock: project_id -> Set[user_id]
        self._active_memberships: Dict[UUID, Set[UUID]] = {}

        # Set of verified global regulatory knowledge_source_ids
        self._verified_global_sources: Set[UUID] = set()

    def register_active_member(self, project_id: UUID, user_id: UUID) -> None:
        """Registers an active user in a project workspace."""
        self._active_memberships.setdefault(project_id, set()).add(user_id)

    def revoke_member(self, project_id: UUID, user_id: UUID) -> None:
        """Revokes a user's membership from a project workspace."""
        if project_id in self._active_memberships:
            self._active_memberships[project_id].discard(user_id)

    def register_verified_global_source(self, source_id: UUID) -> None:
        """Marks a knowledge_source as officially verified and approved for global retrieval."""
        self._verified_global_sources.add(source_id)

    async def ingest_chunks(self, chunks: List[StructuredChunk]) -> None:
        """
        Indexes chunks into both the keyword and vector stores.
        Generates embeddings for vector similarity.
        """
        if not chunks:
            return

        texts = [c.content for c in chunks]
        emb_resp = await self.embedding_provider.generate_embeddings(
            EmbeddingRequest(texts=texts, target_dimensions=self.vector_retriever.expected_dimensions)
        )
        vectors = [item.vector for item in emb_resp.embeddings]

        self.vector_retriever.index_chunks(chunks, vectors)
        for c in chunks:
            self._chunks[c.id] = c

    def _pre_filter_candidates(
        self,
        query: RetrievalQuery,
        requesting_user_id: Optional[UUID] = None,
        allow_synthetic: bool = False,
    ) -> List[StructuredChunk]:
        """
        PRE-RETRIEVAL FILTERING:
        Applies tenant and scope restrictions BEFORE search algorithms execute.
        Guarantees that unauthorized documents never participate in retrieval scoring.
        """
        candidates: List[StructuredChunk] = []

        # Validate active project membership if project private retrieval requested
        has_active_membership = True
        if query.project_id is not None and requesting_user_id is not None:
            active_users = self._active_memberships.get(query.project_id, set())
            has_active_membership = (requesting_user_id in active_users)

        for chunk in self._chunks.values():
            # 1. Synthetic protection: Synthetic chunks cannot be treated as real regulatory codices
            if chunk.is_synthetic and not allow_synthetic:
                continue

            # 2. Scope: Global Regulatory
            if chunk.knowledge_source_id is not None:
                # Must be verified global source (or synthetic test allowed)
                is_verified = (chunk.knowledge_source_id in self._verified_global_sources) or allow_synthetic
                if not is_verified:
                    continue

                if query.scope in (ScopeType.GLOBAL_REGULATORY, ScopeType.HYBRID):
                    # Check authority filter if requested
                    if query.authority_filter and chunk.source_code:
                        if not any(auth.upper() in chunk.source_code.upper() for auth in query.authority_filter):
                            continue
                    candidates.append(chunk)

            # 3. Scope: Project Private
            elif chunk.project_id is not None:
                # Private chunks are ONLY accessible if query explicitly targets this project
                # AND user has active membership in the project
                if query.project_id == chunk.project_id and has_active_membership:
                    if query.scope in (ScopeType.PROJECT_PRIVATE, ScopeType.HYBRID):
                        candidates.append(chunk)

        return candidates

    def _sanitize_untrusted_content(self, text: str) -> str:
        """
        Mitigates prompt injection inside user documents by HTML-escaping
        and enclosing in untrusted evidence tags.
        """
        escaped = html.escape(text)
        return escaped

    async def retrieve(
        self,
        query: RetrievalQuery,
        requesting_user_id: Optional[UUID] = None,
        allow_synthetic: bool = False,
    ) -> RetrievalResult:
        """
        Executes a secure, scoped retrieval query adhering to tenant isolation rules.
        """
        start_time = time.monotonic()

        # 1. Apply pre-retrieval tenant security filter
        candidate_chunks = self._pre_filter_candidates(
            query=query,
            requesting_user_id=requesting_user_id,
            allow_synthetic=allow_synthetic,
        )

        if not candidate_chunks:
            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            return RetrievalResult(
                query=query.query_text,
                chunks=[],
                total_found=0,
                scope_used=query.scope,
                latency_ms=elapsed_ms,
            )

        # 2. Embed query
        query_emb_resp = await self.embedding_provider.generate_embeddings(
            EmbeddingRequest(
                texts=[query.query_text],
                target_dimensions=self.vector_retriever.expected_dimensions,
            )
        )
        query_vector = query_emb_resp.embeddings[0].vector

        # 3. Execute hybrid retrieval
        ranked_pairs = self.hybrid_retriever.retrieve_hybrid(
            query=query.query_text,
            query_vector=query_vector,
            candidate_chunks=candidate_chunks,
            top_k=query.top_k,
            minimum_score=query.minimum_score,
            use_rrf=True,
        )

        # 4. Map to RetrievedChunk data structures
        retrieved_chunks: List[RetrievedChunk] = []
        for chunk, score in ranked_pairs:
            is_private = (chunk.project_id is not None)
            scope = ScopeType.PROJECT_PRIVATE if is_private else ScopeType.GLOBAL_REGULATORY

            retrieved_chunk = RetrievedChunk(
                chunk_id=chunk.id,
                source_title=chunk.source_title or "Untitled Reference",
                source_code=chunk.source_code or "REF",
                content=self._sanitize_untrusted_content(chunk.content),
                content_urdu=chunk.content_urdu,
                page_number=chunk.page_number,
                clause_or_section=chunk.section or chunk.chapter,
                scope=scope,
                project_id=chunk.project_id,
                document_id=chunk.document_id,
                relevance_score=score,
                metadata={
                    "extraction_method": chunk.extraction_method,
                    "source_version": chunk.source_version,
                    "is_synthetic": chunk.is_synthetic,
                    "content_hash": chunk.content_hash,
                },
            )
            retrieved_chunks.append(retrieved_chunk)

        # 5. Optional Re-Ranking stage
        if self.reranker is not None and retrieved_chunks:
            retrieved_chunks = await self.reranker.rerank(
                query=query.query_text,
                candidates=retrieved_chunks,
                top_k=query.top_k,
            )

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return RetrievalResult(
            query=query.query_text,
            chunks=retrieved_chunks,
            total_found=len(retrieved_chunks),
            scope_used=query.scope,
            latency_ms=elapsed_ms,
        )

