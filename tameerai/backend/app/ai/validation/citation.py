"""
TameerAI - Citation & Provenance Validation Engine (Phase 03A / Phase 03C / Phase 03G Stage B3.2)
Validates that generated citations correspond to real, retrieved evidence chunks.
Enforces multi-tenant authorization boundaries, page grounding, claim-evidence semantic alignment,
adversarial contradiction detection (negation, directional, conditional, comparative, unit mismatches),
and separates source-existence verification from claim-support and regulatory interpretation.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.ai.contracts.retrieval import RetrievedChunk, ScopeType
from app.ai.contracts.validation import (
    CitationValidatorProtocol,
    CitationValidationItem,
    CitationValidationReport,
    ClaimRelevanceStatus,
    CitationStatus,
    ValidationStatus,
)

# Standard recognized regulatory and contract prefixes for Pakistani engineering context
STANDARD_AUTHORITY_PATTERNS = [
    re.compile(r"^PBC(?:-\d{4})?", re.IGNORECASE),       # Pakistan Building Code
    re.compile(r"^LDA(?:-\d{4})?", re.IGNORECASE),       # Lahore Development Authority
    re.compile(r"^CDA(?:-\d{4})?", re.IGNORECASE),       # Capital Development Authority
    re.compile(r"^SBCA(?:-\d{4})?", re.IGNORECASE),      # Sindh Building Control Authority
    re.compile(r"^KDA(?:-\d{4})?", re.IGNORECASE),       # Karachi Development Authority
    re.compile(r"^PEC(?:-[A-Z0-9]+)?", re.IGNORECASE),   # Pakistan Engineering Council
    re.compile(r"^FIDIC(?:-[A-Za-z0-9]+)?", re.IGNORECASE),  # FIDIC contract forms
    re.compile(r"^PRJ-(?:DOC|DWG)-\d+", re.IGNORECASE),  # Tenant project documents
    re.compile(r"^DOC-[A-Za-z0-9\-]+", re.IGNORECASE),   # Generated project documents
    re.compile(r"^SYNTH(?:-[A-Za-z0-9\-]+)?", re.IGNORECASE),  # Synthetic test fixture codes
]

# Common English and Roman Urdu construction stop words to ignore during lexical overlap
STOP_WORDS: Set[str] = {
    "that", "this", "with", "from", "have", "been", "will", "must", "shall", "should",
    "karna", "hona", "hota", "hoti", "hote", "hoga", "hogi", "ke", "ki", "ka", "ko",
    "mein", "par", "se", "aur", "bhi", "liye", "gaya", "gayi", "about", "their", "which",
    "general", "info", "information", "details", "notes", "guidelines", "description",
    "document", "drawing", "drawings", "clause", "section", "project", "technical"
}

# Domain technical concept patterns for claim-evidence topical verification
CONSTRUCTION_TOPIC_CONCEPTS: Dict[str, List[re.Pattern]] = {
    "setback": [
        re.compile(r"\b(?:setback|clearance|front\s*space|rear\s*space|side\s*space|open\s*space|boundary|faasla|hadd)\b", re.IGNORECASE)
    ],
    "curing": [
        re.compile(r"\b(?:curing|tarai|moist\s*curing|water\s*curing|curing\s*days?)\b", re.IGNORECASE)
    ],
    "compressive_strength": [
        re.compile(r"\b(?:compressive\s*strength|psi|mpa|strength|taqat|grade\s*of\s*concrete)\b", re.IGNORECASE)
    ],
    "rebar_reinforcement": [
        re.compile(r"\b(?:rebar|steel|saria|reinforcement|mesh|ties|stirrups|deformed\s*bars?|bars?|grade\s*60)\b", re.IGNORECASE)
    ],
    "foundation": [
        re.compile(r"\b(?:foundation|footing|bunyaad|soil|bearing\s*capacity|excavation|depth\s*of\s*foundation)\b", re.IGNORECASE)
    ],
    "dimensions_cross_section": [
        re.compile(r"\b(?:column\s*size|columns?|beam\s*size|beams?|thickness|depth|span|section|dimensions?)\b", re.IGNORECASE)
    ],
    "fire_safety": [
        re.compile(r"\b(?:fire|extinguisher|egress|exit|aag|fire\s*rating)\b", re.IGNORECASE)
    ],
    "height_and_floors": [
        re.compile(r"\b(?:height|floors?|storeys?|tala|manzil|maximum\s*height)\b", re.IGNORECASE)
    ],
    "mix_ratio": [
        re.compile(r"\b(?:1:2:4|1:1\.5:3|1:3:6|mix\s*ratio|nominal\s*mix|batching)\b", re.IGNORECASE)
    ],
}

# Unit contradiction lookup map
UNIT_INCOMPATIBILITY_MAP: Dict[str, Set[str]] = {
    "mm": {"inch", "inches", "in", "feet", "ft", "meter", "m"},
    "inches": {"mm", "m.m.", "cm", "meter", "m", "feet", "ft"},
    "inch": {"mm", "m.m.", "cm", "meter", "m", "feet", "ft"},
    "psi": {"mpa", "cft", "sqft"},
    "mpa": {"psi"},
    "cft": {"sqft", "marla", "kanal"},
    "sqft": {"cft"},
}

QUANTITY_UNIT_PATTERN = re.compile(
    r"(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mm|m\.m\.|cm|meter|m|inches?|in\.?|feet|ft\.?|psi|mpa|kg|tons?|cft|sqft|marla|kanal)\b",
    re.IGNORECASE,
)

# Semantic polarity and contradiction patterns
NEGATION_PATTERN = re.compile(
    r"\b(?:not|never|no|cannot|can't|won't|does\s*not|is\s*not|shall\s*not|should\s*not|nahi|nahi\s*hai|nahi\s*hona)\b",
    re.IGNORECASE,
)

DIRECTIONAL_INC_TERMS: Set[str] = {"increase", "increases", "increasing", "higher", "greater", "more", "expand", "barhana", "barhta", "ziyada"}
DIRECTIONAL_DEC_TERMS: Set[str] = {"decrease", "decreases", "decreasing", "reduce", "reduces", "reducing", "lower", "less", "shrink", "kam", "ghatna"}

CONDITIONAL_RESTRICTION_PATTERN = re.compile(
    r"\b(?:only\s+if|only\s+when|only\s+for|subject\s+to|provided\s+that|conditional\s+on|strictly\s+when|sirf\s+tab|sirf)\b",
    re.IGNORECASE,
)
UNIVERSAL_GENERALIZATION_PATTERN = re.compile(
    r"\b(?:universally|always|in\s+all\s+cases|without\s+exception|regardless\s+of|har\s+surat|har\s+haal|hamesha)\b",
    re.IGNORECASE,
)

COMPARATIVE_PATTERN = re.compile(
    r"\b(?P<subj>[a-zA-Z\s]{3,30}?)\s+(?:has\s+greater|has\s+higher|is\s+stronger|has\s+more|has\s+less|is\s+weaker)\s+.*?\bthan\s+(?P<obj>[a-zA-Z\s]{3,30})\b",
    re.IGNORECASE,
)

SUPERSEDED_CODE_EDITIONS: Dict[str, str] = {
    "BCP-1986": "BCP-2021",
    "LDA-2007": "LDA-2020",
    "SBCA-2002": "SBCA-2020",
}

AUTHORITY_JURISDICTIONS: Dict[str, str] = {
    "LDA": "Lahore",
    "CDA": "Islamabad",
    "SBCA": "Karachi",
    "KDA": "Karachi",
}


class CitationValidator(CitationValidatorProtocol):
    """
    Validates AI-generated citations against provided retrieval evidence chunks.
    Ensures zero fabricated citations pass through to end engineers and verifies
    genuine semantic alignment between claimed assertions and cited source content.
    """

    def _is_known_format(self, code: str) -> bool:
        """Checks if code matches recognized Pakistani regulatory or project document pattern."""
        if not code:
            return False
        clean = code.strip()
        return any(p.match(clean) for p in STANDARD_AUTHORITY_PATTERNS)

    @classmethod
    def detect_evidence_contradictions(cls, evidence_chunks: List[RetrievedChunk]) -> List[str]:
        """
        Detects conflicting technical specifications across retrieved evidence chunks.
        Ensures the system does not arbitrarily select one conflicting chunk as authoritative.
        """
        conflicts: List[str] = []
        if len(evidence_chunks) < 2:
            return conflicts

        specs_by_topic: Dict[str, List[Tuple[RetrievedChunk, str]]] = {}
        for c in evidence_chunks:
            # Check compressive strength
            for v in re.findall(r"\b(\d{3,5})\s*(?:psi|mpa)\b", c.content, re.IGNORECASE):
                specs_by_topic.setdefault("compressive_strength", []).append((c, f"{v} psi/mpa"))
            # Check rebar diameter
            for v in re.findall(r"\b(\d{1,2})\s*mm\b", c.content, re.IGNORECASE):
                specs_by_topic.setdefault("rebar_diameter", []).append((c, f"{v} mm"))
            # Check setback
            for v in re.findall(r"\b(\d{1,2})\s*(?:feet|ft)\s*(?:setback|clearance)\b", c.content, re.IGNORECASE):
                specs_by_topic.setdefault("setback", []).append((c, f"{v} ft"))

        for topic, entries in specs_by_topic.items():
            if len(entries) >= 2:
                unique_vals = set(val for _, val in entries)
                if len(unique_vals) > 1:
                    sources = ", ".join(set(c.source_code for c, _ in entries))
                    conflicts.append(
                        f"Conflicting technical specifications for '{topic}' ({' vs '.join(unique_vals)}) detected across retrieved sources ({sources}). Human engineering resolution required."
                    )
        return conflicts

    @classmethod
    def verify_claim_alignment(
        cls,
        claim_text: Optional[str],
        chunk: RetrievedChunk,
    ) -> Tuple[ClaimRelevanceStatus, str]:
        """
        Determines whether a cited evidence chunk genuinely supports the factual/technical claim.
        Adversarially audits polarity (negation), directionality, conditions, comparatives, and units.
        """
        if not claim_text or not claim_text.strip():
            return (
                ClaimRelevanceStatus.VALID_SOURCE,
                "Source existence verified; no specific factual claim text provided to verify relevance.",
            )

        clean_claim = claim_text.strip()
        chunk_text = (chunk.content or "").strip()

        # 1. Identify active topics in claim and chunk
        claim_topics = set()
        chunk_topics = set()
        for topic_name, patterns in CONSTRUCTION_TOPIC_CONCEPTS.items():
            if any(p.search(clean_claim) for p in patterns):
                claim_topics.add(topic_name)
            if any(p.search(chunk_text) for p in patterns):
                chunk_topics.add(topic_name)

        # 2. Check for explicit topical mismatch
        if claim_topics and chunk_topics and not (claim_topics & chunk_topics):
            c_top = list(claim_topics)[0]
            k_top = list(chunk_topics)[0]
            return (
                ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                f"Claim addresses technical topic '{c_top}', but cited evidence discusses '{k_top}' and does not support this claim.",
            )

        # 3. Unit Contradiction Check (e.g. 12 inches vs 12 mm)
        claim_quants = [(m.group("val"), m.group("unit").lower()) for m in QUANTITY_UNIT_PATTERN.finditer(clean_claim)]
        chunk_quants = [(m.group("val"), m.group("unit").lower()) for m in QUANTITY_UNIT_PATTERN.finditer(chunk_text)]
        for c_val, c_u in claim_quants:
            for k_val, k_u in chunk_quants:
                if c_val == k_val and k_u in UNIT_INCOMPATIBILITY_MAP.get(c_u, set()):
                    return (
                        ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                        f"Unit contradiction detected: Claim specifies '{c_val} {c_u}', but evidence specifies incompatible unit '{k_val} {k_u}'.",
                    )

        # 4. Polarity / Negation Contradiction Check
        claim_has_neg = bool(NEGATION_PATTERN.search(clean_claim))
        chunk_has_neg = bool(NEGATION_PATTERN.search(chunk_text))
        if claim_has_neg != chunk_has_neg:
            # Check if substantial technical terms match (meaning assertion is inverted)
            claim_non_neg_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", clean_claim.lower()) if not NEGATION_PATTERN.match(w) and w not in STOP_WORDS]
            matched_non_neg = [w for w in claim_non_neg_words if w in chunk_text.lower()]
            if claim_non_neg_words and len(matched_non_neg) / len(claim_non_neg_words) >= 0.50:
                return (
                    ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                    "Semantic contradiction detected: Claim and evidence have opposing polarity (positive vs negative assertion).",
                )

        # 5. Directional Contradiction Check (e.g. increasing load decreases foundation demand)
        c_tokens = set(re.findall(r"\b[a-zA-Z]+\b", clean_claim.lower()))
        k_tokens = set(re.findall(r"\b[a-zA-Z]+\b", chunk_text.lower()))
        c_has_inc = bool(c_tokens & DIRECTIONAL_INC_TERMS)
        c_has_dec = bool(c_tokens & DIRECTIONAL_DEC_TERMS)
        k_has_inc = bool(k_tokens & DIRECTIONAL_INC_TERMS)
        k_has_dec = bool(k_tokens & DIRECTIONAL_DEC_TERMS)

        # If both discuss the same physical relationship but invert the effect:
        if (c_tokens & k_tokens) and len(c_tokens & k_tokens) >= 3:
            if (c_has_dec and not k_has_dec and k_has_inc) or (c_has_inc and not k_has_inc and k_has_dec):
                return (
                    ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                    "Directional contradiction detected: Claim asserts opposite directional effect compared to retrieved evidence.",
                )

        # 6. Conditional Restriction vs Universal Generalization
        if CONDITIONAL_RESTRICTION_PATTERN.search(chunk_text) and UNIVERSAL_GENERALIZATION_PATTERN.search(clean_claim):
            return (
                ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                "Conditional mismatch: Evidence applies only under specific conditional restrictions, but claim asserts universal applicability.",
            )

        # 7. Comparative Relationship Inversion Check
        m_c = COMPARATIVE_PATTERN.search(clean_claim)
        m_k = COMPARATIVE_PATTERN.search(chunk_text)
        if m_c and m_k:
            c_s = m_c.group("subj").strip().lower()
            c_o = m_c.group("obj").strip().lower()
            k_s = m_k.group("subj").strip().lower()
            k_o = m_k.group("obj").strip().lower()
            if (c_s in k_o or k_o in c_s) and (c_o in k_s or k_s in c_o):
                return (
                    ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                    "Comparative contradiction detected: Relative relationship between materials/parameters is inverted.",
                )

        # 8. Quantitative Value Check & Partial Breakdown
        claim_numbers = re.findall(r"\d+(?:\.\d+)?", clean_claim)
        chunk_numbers = set(re.findall(r"\d+(?:\.\d+)?", chunk_text))

        if claim_numbers:
            matched_nums = [n for n in claim_numbers if n in chunk_numbers]
            unmatched_nums = [n for n in claim_numbers if n not in chunk_numbers]

            if len(matched_nums) == len(claim_numbers) and (claim_topics & chunk_topics or not claim_topics):
                return (
                    ClaimRelevanceStatus.CLAIM_SUPPORTED,
                    "Cited evidence contains relevant supporting technical parameters and topical context.",
                )
            elif len(matched_nums) > 0:
                return (
                    ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED,
                    f"Claim partially supported: parameters {matched_nums} confirmed in evidence, but {unmatched_nums} require verification against site drawings.",
                )
            elif claim_topics & chunk_topics:
                # Same topic, but numbers completely differ (e.g. 4000 psi claimed vs 3000 psi in chunk)
                return (
                    ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                    "Cited evidence discusses this technical topic but specifies different numerical values or parameters than claimed.",
                )

        # 9. Lexical Overlap Check for Descriptive Claims
        claim_words = [
            w for w in re.findall(r"\b[a-zA-Z]{3,}\b", clean_claim.lower())
            if w not in STOP_WORDS
        ]
        if not claim_words:
            return (
                ClaimRelevanceStatus.CLAIM_RELEVANCE_UNVERIFIED,
                "Claim text contains insufficient distinct technical vocabulary to deterministically verify relevance.",
            )

        matched_words = [w for w in claim_words if w in chunk_text.lower()]
        overlap_ratio = len(matched_words) / len(claim_words)

        if overlap_ratio >= 0.60:
            return (
                ClaimRelevanceStatus.CLAIM_SUPPORTED,
                f"Substantive technical claim is supported by retrieved evidence text ({overlap_ratio * 100:.0f}% alignment).",
            )
        elif overlap_ratio >= 0.30:
            return (
                ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED,
                f"Claim is partially supported by retrieved evidence text ({overlap_ratio * 100:.0f}% alignment).",
            )
        elif claim_topics & chunk_topics:
            return (
                ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED,
                "Topical domain matches retrieved chunk, but specific assertion details require project verification.",
            )
        else:
            return (
                ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                f"Cited evidence does not contain sufficient matching text or facts to support the claim ({overlap_ratio * 100:.0f}% overlap).",
            )

    def validate_citations(
        self,
        citations: List[Dict[str, Any]],
        evidence_chunks: List[RetrievedChunk],
        project_id: Optional[UUID] = None,
    ) -> CitationValidationReport:
        items: List[CitationValidationItem] = []
        valid_count = 0
        unsupported_count = 0

        # Check for cross-chunk technical contradictions
        conflicts = self.detect_evidence_contradictions(evidence_chunks)

        # Build fast lookup indexes from retrieved evidence
        evidence_by_code: Dict[str, List[RetrievedChunk]] = {}
        evidence_by_chunk_id: Dict[str, RetrievedChunk] = {}

        for c in evidence_chunks:
            code_key = c.source_code.strip().upper()
            evidence_by_code.setdefault(code_key, []).append(c)
            evidence_by_chunk_id[str(c.chunk_id)] = c

        for cit in citations:
            raw_text = cit.get("title") or cit.get("citation_text") or "Untitled citation"
            source_code = (cit.get("source_code") or "").strip()
            page_no = cit.get("page_number")
            clause = cit.get("section_or_clause")
            cited_chunk_id = cit.get("chunk_id")
            cited_doc_id = cit.get("document_id")
            cited_proj_id = cit.get("project_id")
            claim_text = cit.get("claim_text") or cit.get("claim") or ""

            # 1. Check identifier format
            if not source_code:
                items.append(
                    CitationValidationItem(
                        citation_text=raw_text,
                        source_code="UNKNOWN",
                        clause_or_section=clause,
                        page_number=page_no,
                        status=ValidationStatus.MALFORMED_IDENTIFIER,
                        matched_chunk_id=None,
                        claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                        claim_text=claim_text,
                        explanation="Citation lacks a source_code identifier."
                    )
                )
                unsupported_count += 1
                continue

            # 2. Check page number validity
            if page_no is not None and page_no < 1:
                items.append(
                    CitationValidationItem(
                        citation_text=raw_text,
                        source_code=source_code,
                        clause_or_section=clause,
                        page_number=page_no,
                        status=ValidationStatus.INVALID_PAGE,
                        matched_chunk_id=None,
                        claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                        claim_text=claim_text,
                        explanation=f"Page number {page_no} is invalid (must be >= 1)."
                    )
                )
                unsupported_count += 1
                continue

            # 3. Check presence in retrieved evidence
            code_key = source_code.upper()
            matching_chunks = evidence_by_code.get(code_key, [])

            # Check by chunk_id if provided
            if cited_chunk_id:
                if str(cited_chunk_id) not in evidence_by_chunk_id:
                    items.append(
                        CitationValidationItem(
                            citation_text=raw_text,
                            source_code=source_code,
                            clause_or_section=clause,
                            page_number=page_no,
                            status=ValidationStatus.INVALID_CHUNK_ID,
                            matched_chunk_id=None,
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                            claim_text=claim_text,
                            explanation=(
                                f"Cited chunk ID '{cited_chunk_id}' does not exist in retrieved evidence chunks. "
                                "Rejecting fabricated or ungrounded chunk identifier."
                            )
                        )
                    )
                    unsupported_count += 1
                    continue
                else:
                    matching_chunks = [evidence_by_chunk_id[str(cited_chunk_id)]]

            if not matching_chunks:
                items.append(
                    CitationValidationItem(
                        citation_text=raw_text,
                        source_code=source_code,
                        clause_or_section=clause,
                        page_number=page_no,
                        status=ValidationStatus.UNSUPPORTED_CITATION,
                        matched_chunk_id=None,
                        claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                        claim_text=claim_text,
                        explanation=(
                            f"Cited source '{source_code}' was not present in the retrieved evidence. "
                            "Potential hallucination or ungrounded reference."
                        )
                    )
                )
                unsupported_count += 1
                continue

            best_chunk: Optional[RetrievedChunk] = matching_chunks[0]

            # 4. Multi-tenant security check: If citing a private project document, check project authorization
            if best_chunk.scope == ScopeType.PROJECT_PRIVATE or best_chunk.project_id is not None:
                if project_id is None or (best_chunk.project_id is not None and best_chunk.project_id != project_id):
                    items.append(
                        CitationValidationItem(
                            citation_text=raw_text,
                            source_code=source_code,
                            clause_or_section=clause,
                            page_number=page_no,
                            status=ValidationStatus.UNAUTHORIZED_PROJECT_REFERENCE,
                            matched_chunk_id=None,
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                            claim_text=claim_text,
                            explanation="Citation references private documents without valid project authorization. Access denied."
                        )
                    )
                    unsupported_count += 1
                    continue

                if cited_proj_id is not None and best_chunk.project_id is not None and str(cited_proj_id) != str(best_chunk.project_id):
                    items.append(
                        CitationValidationItem(
                            citation_text=raw_text,
                            source_code=source_code,
                            clause_or_section=clause,
                            page_number=page_no,
                            status=ValidationStatus.UNAUTHORIZED_PROJECT_REFERENCE,
                            matched_chunk_id=None,
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                            claim_text=claim_text,
                            explanation=f"Citation specifies project ID '{cited_proj_id}' which does not match evidence chunk project ID '{best_chunk.project_id}'."
                        )
                    )
                    unsupported_count += 1
                    continue

            # 5. Check page grounding if page was specified
            if page_no is not None:
                page_matched = any(c.page_number == page_no for c in matching_chunks if c.page_number is not None)
                if not page_matched:
                    items.append(
                        CitationValidationItem(
                            citation_text=raw_text,
                            source_code=source_code,
                            clause_or_section=clause,
                            page_number=page_no,
                            status=ValidationStatus.INVALID_PAGE,
                            matched_chunk_id=str(best_chunk.chunk_id),
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                            claim_text=claim_text,
                            explanation=(
                                f"Source '{source_code}' exists in evidence, but page {page_no} was not found "
                                f"in retrieved pages: {[c.page_number for c in matching_chunks]}."
                            )
                        )
                    )
                    unsupported_count += 1
                    continue
                for c in matching_chunks:
                    if c.page_number == page_no:
                        best_chunk = c
                        break

            # 6. Check document ID matches if provided
            doc_matches = (str(cited_doc_id) == str(best_chunk.document_id)) if (cited_doc_id and best_chunk.document_id) else True
            if cited_doc_id is not None and best_chunk.document_id is not None:
                if not doc_matches:
                    items.append(
                        CitationValidationItem(
                            citation_text=raw_text,
                            source_code=source_code,
                            clause_or_section=clause,
                            page_number=page_no,
                            status=ValidationStatus.DOCUMENT_MISMATCH,
                            matched_chunk_id=str(best_chunk.chunk_id),
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                            claim_text=claim_text,
                            explanation=f"Citation document ID '{cited_doc_id}' does not match evidence chunk document ID '{best_chunk.document_id}'."
                        )
                    )
                    unsupported_count += 1
                    continue

            # 7. Check section / clause exists in chunk
            if clause:
                clean_clause = clause.strip().lower()
                chunk_clause = (best_chunk.clause_or_section or "").strip().lower()
                clause_in_meta = (clean_clause in chunk_clause or chunk_clause in clean_clause) if chunk_clause else False
                clause_in_content = clean_clause in best_chunk.content.lower()
                if not (clause_in_meta or clause_in_content):
                    items.append(
                        CitationValidationItem(
                            citation_text=raw_text,
                            source_code=source_code,
                            clause_or_section=clause,
                            page_number=page_no,
                            status=ValidationStatus.INVALID_CLAUSE,
                            matched_chunk_id=str(best_chunk.chunk_id),
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                            claim_text=claim_text,
                            explanation=f"Cited clause/section '{clause}' was not found in retrieved evidence for source '{source_code}'."
                        )
                    )
                    unsupported_count += 1
                    continue

            # 8. Separate source-existence from claim-support verification
            claim_rel_status, rel_explanation = self.verify_claim_alignment(claim_text, best_chunk)
            snippet = best_chunk.content[:200]

            if claim_rel_status == ClaimRelevanceStatus.CLAIM_UNSUPPORTED:
                items.append(
                    CitationValidationItem(
                        citation_text=raw_text,
                        source_code=source_code,
                        clause_or_section=clause,
                        page_number=page_no,
                        status=ValidationStatus.UNSUPPORTED_CLAIM,
                        matched_chunk_id=str(best_chunk.chunk_id),
                        source_id_matches=True,
                        document_id_matches=doc_matches,
                        claim_support_verified=False,
                        claim_relevance_status=claim_rel_status,
                        claim_text=claim_text,
                        evidence_text_snippet=snippet,
                        explanation=(
                            f"Source exists ({source_code}), but cited evidence does not support the claim. "
                            f"{rel_explanation}"
                        ),
                        metadata={
                            "is_synthetic": best_chunk.metadata.get("is_synthetic", False),
                            "extraction_method": best_chunk.metadata.get("extraction_method"),
                        }
                    )
                )
                unsupported_count += 1
            else:
                is_supported = (claim_rel_status in (ClaimRelevanceStatus.CLAIM_SUPPORTED, ClaimRelevanceStatus.VALID_SOURCE))
                items.append(
                    CitationValidationItem(
                        citation_text=raw_text,
                        source_code=source_code,
                        clause_or_section=clause,
                        page_number=page_no,
                        status=ValidationStatus.VALID,
                        matched_chunk_id=str(best_chunk.chunk_id),
                        source_id_matches=True,
                        document_id_matches=doc_matches,
                        claim_support_verified=is_supported,
                        claim_relevance_status=claim_rel_status,
                        claim_text=claim_text,
                        evidence_text_snippet=snippet,
                        explanation=(
                            f"Verified against retrieved evidence chunk {best_chunk.chunk_id}. "
                            f"{rel_explanation}"
                        ),
                        metadata={
                            "is_synthetic": best_chunk.metadata.get("is_synthetic", False),
                            "extraction_method": best_chunk.metadata.get("extraction_method"),
                        }
                    )
                )
                valid_count += 1

        is_fully_grounded = (unsupported_count == 0) and (len(conflicts) == 0) and (len(citations) > 0 or len(evidence_chunks) == 0)
        warning_msg = None
        if unsupported_count > 0:
            warning_msg = (
                f"Warning: {unsupported_count} citation(s) could not be verified against retrieved evidence. "
                "Consult original codified documents before making engineering decisions."
            )
        elif conflicts:
            warning_msg = (
                f"Warning: Conflicting specifications detected between retrieved sources: {'; '.join(conflicts)}."
            )

        # Determine overall orthogonal CitationStatus
        if not citations:
            cit_status = CitationStatus.VALID if not evidence_chunks else None
        elif any(i.status in (
            ValidationStatus.UNSUPPORTED_CITATION,
            ValidationStatus.INVALID_CHUNK_ID,
            ValidationStatus.DOCUMENT_MISMATCH,
            ValidationStatus.UNAUTHORIZED_PROJECT_REFERENCE,
            ValidationStatus.INVALID_PAGE,
            ValidationStatus.MALFORMED_IDENTIFIER,
            ValidationStatus.INVALID_CLAUSE,
        ) for i in items):
            cit_status = CitationStatus.INVALID
        elif conflicts:
            cit_status = CitationStatus.PARTIALLY_SUPPORTED
        elif any(i.claim_relevance_status == ClaimRelevanceStatus.CLAIM_UNSUPPORTED for i in items):
            cit_status = CitationStatus.PARTIALLY_SUPPORTED if valid_count > 0 else CitationStatus.INVALID
        elif any(i.claim_relevance_status == ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED for i in items):
            cit_status = CitationStatus.PARTIALLY_SUPPORTED
        elif any(i.claim_relevance_status == ClaimRelevanceStatus.CLAIM_RELEVANCE_UNVERIFIED for i in items):
            cit_status = CitationStatus.RELEVANCE_UNVERIFIED
        else:
            cit_status = CitationStatus.VALID

        return CitationValidationReport(
            is_fully_grounded=is_fully_grounded,
            total_citations=len(citations),
            valid_citations=valid_count,
            unsupported_citations=unsupported_count,
            citation_status=cit_status,
            items=items,
            conflicting_evidence=conflicts,
            unsupported_warning=warning_msg,
        )

    @classmethod
    def extract_inline_regulatory_references(cls, text: str) -> List[Dict[str, str]]:
        """
        Extracts specific regulatory codex and clause references mentioned in the text.
        e.g., 'LDA 2020 Clause 15.2', 'BCP Section 4.1', 'CDA Bylaw 12'
        """
        results: List[Dict[str, str]] = []
        patterns = [
            re.compile(
                r"\b(?P<auth>LDA|CDA|SBCA|PBC|BCP|PEC|FIDIC)[-\s]*(?P<ver>\d{4})?\s*(?:building\s+(?:byelaws?|bylaws?|regulations?|code))?\s*(?:section|clause|rule|sub-clause|bylaw|byelaw)\s*(?P<clause>\d+[\.\d\w\-]*)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?:section|clause|rule|sub-clause)\s*(?P<clause>\d+[\.\d\w\-]*)\s*(?:of|under|in)\s*(?:the\s+)?(?P<auth>LDA|CDA|SBCA|PBC|BCP|PEC|FIDIC)[-\s]*(?P<ver>\d{4})?\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?P<auth>LDA|CDA|SBCA|PBC|BCP|PEC|FIDIC)[-\s]*(?P<ver>\d{4})?\s*(?:byelaws?|bylaws?|regulations?|code)\s*(?P<clause>\d+[\.\d\w\-]*)\b",
                re.IGNORECASE,
            ),
        ]
        seen: set = set()
        for pat in patterns:
            for m in pat.finditer(text):
                auth = m.group("auth").upper()
                ver = m.group("ver") if "ver" in m.groupdict() else None
                source_code = f"{auth}-{ver}" if ver else auth
                clause = m.group("clause")
                key = (source_code, clause.lower())
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "source_code": source_code,
                        "clause": clause,
                        "raw_match": m.group(0),
                    })
        return results

    @classmethod
    def validate_inline_regulatory_references(
        cls,
        text: str,
        evidence_chunks: List[RetrievedChunk],
        project_city: Optional[str] = None,
    ) -> List[CitationValidationItem]:
        """
        Audits inline regulatory clauses against retrieved evidence chunks.
        Distinguishes document existence, clause existence, jurisdiction applicability,
        superseded editions, and interpretation safety.
        Ensures AI outputs do not certify legal compliance based solely on regex matching.
        """
        refs = cls.extract_inline_regulatory_references(text)
        items: List[CitationValidationItem] = []

        unverified_compliance_pattern = re.compile(
            r"\b(?:guaranteed|100%|strictly|fully)\s*(?:compliant|approved|legal|certified)\b|"
            r"\b(?:meets\s+all\s+legal\s+requirements|approved\s+by\s+authority|guaranteed\s+approval)\b|"
            r"\b(?:statutory\s+approval|statutory\s+certification)\b|"
            r"\blegal\s+compliance\s+is\s+confirmed\b",
            re.IGNORECASE,
        )
        has_unverified_compliance_claim = bool(unverified_compliance_pattern.search(text))

        for ref in refs:
            src = ref["source_code"]
            clause = ref["clause"]
            clean_clause = clause.strip().lower()
            matched_chunk = None

            for c in evidence_chunks:
                auth_prefix = src.split("-")[0].upper()
                c_code = c.source_code.upper()
                if auth_prefix in c_code or c_code in auth_prefix:
                    c_clause = (c.clause_or_section or "").lower()
                    if clean_clause in c_clause or clean_clause in c.content.lower():
                        matched_chunk = c
                        break

            # Check jurisdiction applicability
            auth_key = src.split("-")[0].upper()
            jurisdiction_mismatch = False
            jurisdiction_note = ""
            if project_city and auth_key in AUTHORITY_JURISDICTIONS:
                expected_city = AUTHORITY_JURISDICTIONS[auth_key]
                if expected_city.lower() not in project_city.lower():
                    jurisdiction_mismatch = True
                    jurisdiction_note = f" (Jurisdiction note: '{src}' regulates {expected_city}, but project city is '{project_city}')"

            # Check superseded edition
            superseded_note = ""
            if src in SUPERSEDED_CODE_EDITIONS:
                superseded_note = f" (Superseded edition: '{src}' is superseded by '{SUPERSEDED_CODE_EDITIONS[src]}')"

            if matched_chunk is None:
                items.append(
                    CitationValidationItem(
                        citation_text=ref["raw_match"],
                        source_code=src,
                        clause_or_section=clause,
                        status=ValidationStatus.INVALID_CLAUSE,
                        matched_chunk_id=None,
                        claim_relevance_status=ClaimRelevanceStatus.CLAIM_UNSUPPORTED,
                        explanation=(
                            f"Regulatory clause '{clause}' for '{src}' was cited in response text "
                            f"but was not found in any retrieved evidence chunks. Potential hallucination.{jurisdiction_note}{superseded_note}"
                        ),
                    )
                )
            else:
                if has_unverified_compliance_claim or jurisdiction_mismatch:
                    items.append(
                        CitationValidationItem(
                            citation_text=ref["raw_match"],
                            source_code=src,
                            clause_or_section=clause,
                            status=ValidationStatus.VALID,
                            matched_chunk_id=str(matched_chunk.chunk_id),
                            claim_support_verified=False,
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_PARTIALLY_SUPPORTED,
                            explanation=(
                                f"Reference verified against available official regulatory text ({src} Clause {clause}). "
                                f"Regulatory interpretation requires confirmation from the relevant authority or licensed professional; "
                                f"absolute legal or structural compliance cannot be certified by automated text matching. "
                                f"Automated text matching does not legally certify a building or approve structural drawings.{jurisdiction_note}{superseded_note}"
                            ),
                        )
                    )
                else:
                    items.append(
                        CitationValidationItem(
                            citation_text=ref["raw_match"],
                            source_code=src,
                            clause_or_section=clause,
                            status=ValidationStatus.VALID,
                            matched_chunk_id=str(matched_chunk.chunk_id),
                            claim_support_verified=True,
                            claim_relevance_status=ClaimRelevanceStatus.CLAIM_SUPPORTED,
                            explanation=(
                                f"Reference verified against available official regulatory text ({src} Clause {clause}). "
                                f"Regulatory interpretation requires confirmation from the relevant authority or licensed professional.{superseded_note}"
                            ),
                        )
                    )
        return items
