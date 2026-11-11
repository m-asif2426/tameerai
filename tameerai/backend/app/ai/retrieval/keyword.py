"""
TameerAI - Keyword Retrieval Engine (Phase 03C)
Implements BM25 / TF-IDF lexical search with exact clause and section boosting
for engineering codices, specifications, and BOQ schedules.
"""

import math
import re
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.ai.contracts.chunking import StructuredChunk
from app.ai.contracts.retrieval import RetrievedChunk, ScopeType


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric word tokens."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())


class KeywordRetriever:
    """
    In-memory BM25 lexical retrieval engine.
    Computes term frequency, inverse document frequency, and clause-specific boosts.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _compute_idf(self, corpus_tokenized: List[List[str]]) -> Dict[str, float]:
        """Computes inverse document frequency for all unique terms in corpus."""
        n_docs = len(corpus_tokenized)
        if n_docs == 0:
            return {}

        df: Dict[str, int] = {}
        for tokens in corpus_tokenized:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1

        idf: Dict[str, float] = {}
        for term, freq in df.items():
            # BM25 standard smoothed IDF formula
            idf[term] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))
        return idf

    def search(
        self,
        query: str,
        chunks: List[StructuredChunk],
        top_k: int = 10,
        minimum_score: float = 0.0,
    ) -> List[Tuple[StructuredChunk, float]]:
        """
        Executes lexical BM25 ranking against a collection of structured chunks.
        Returns ranked list of (StructuredChunk, normalized_score).
        """
        if not query.strip() or not chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Tokenize corpus chunks
        corpus_tokenized: List[List[str]] = []
        doc_lengths: List[int] = []
        for c in chunks:
            # Combine content, chapter, and section for lexical search
            combined_text = f"{c.content} {c.chapter or ''} {c.section or ''} {c.source_code or ''}"
            tokens = tokenize(combined_text)
            corpus_tokenized.append(tokens)
            doc_lengths.append(len(tokens))

        total_length = sum(doc_lengths)
        avg_doc_len = (total_length / len(chunks)) if chunks else 1.0
        if avg_doc_len == 0.0:
            avg_doc_len = 1.0

        idf = self._compute_idf(corpus_tokenized)

        scores: List[float] = []
        for idx, doc_tokens in enumerate(corpus_tokenized):
            d_len = doc_lengths[idx]
            tf: Dict[str, int] = {}
            for t in doc_tokens:
                tf[t] = tf.get(t, 0) + 1

            score = 0.0
            for q_term in query_tokens:
                if q_term in tf:
                    term_freq = tf[q_term]
                    term_idf = idf.get(q_term, 0.0)
                    numerator = term_freq * (self.k1 + 1.0)
                    denominator = term_freq + self.k1 * (1.0 - self.b + self.b * (d_len / avg_doc_len))
                    score += term_idf * (numerator / denominator)

            # Boost exact clause or section match
            chunk_obj = chunks[idx]
            q_clean = query.lower()
            if chunk_obj.section and chunk_obj.section.lower() in q_clean:
                score += 2.0
            if chunk_obj.source_code and chunk_obj.source_code.lower() in q_clean:
                score += 1.5

            scores.append(score)

        # Normalize scores to [0.0, 1.0]
        max_score = max(scores) if scores else 0.0
        scored_pairs: List[Tuple[StructuredChunk, float]] = []

        for idx, chunk in enumerate(chunks):
            raw = scores[idx]
            norm_score = (raw / max_score) if max_score > 0.0 else 0.0
            if norm_score >= minimum_score:
                scored_pairs.append((chunk, round(norm_score, 4)))

        # Sort descending by score
        scored_pairs.sort(key=lambda pair: pair[1], reverse=True)
        return scored_pairs[:top_k]

