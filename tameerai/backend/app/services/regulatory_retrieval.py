"""
TameerAI - Pakistan Statutory Regulatory Retrieval & Citation Engine (Phase 03.3)

Provides jurisdiction-aware, point-in-time statutory search, multi-term ranking,
and canonical legal citation generation adhering to strict structural safety boundaries.
Supports both AsyncSession and sync Session.
"""

from datetime import date, datetime
from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.models.regulation import (
    RegulatoryAuthority,
    RegulatoryClause,
    RegulatoryDocument,
    RegulatoryDocumentVersion,
)
from app.schemas.regulation import (
    RegulatoryCitation,
    RegulatoryClauseRead,
    RegulatorySearchQuery,
    RegulatorySearchResponse,
    RegulatorySearchResult,
)
from app.services.regulatory_discovery import RegulatoryDiscoveryService

logger = logging.getLogger(__name__)


class RegulatoryRetrievalService:
    """
    Search and citation engine for statutory construction regulations.
    """

    @classmethod
    async def search_async(
        cls,
        db: AsyncSession,
        query_in: RegulatorySearchQuery,
    ) -> RegulatorySearchResponse:
        """
        Asynchronously executes a jurisdiction-aware search across regulatory clauses.
        """
        jurisdiction_filtered = False
        allowed_authority_ids: Optional[Set[uuid.UUID]] = None

        if query_in.city or query_in.province:
            resolved_authorities = await RegulatoryDiscoveryService.resolve_authorities_for_location_async(
                db=db,
                city=query_in.city,
                province=query_in.province,
            )
            allowed_authority_ids = {a.id for a in resolved_authorities}
            jurisdiction_filtered = True

        if query_in.authority_codes:
            auth_codes = [c.upper() for c in query_in.authority_codes]
            stmt_auth = select(RegulatoryAuthority.id).where(RegulatoryAuthority.code.in_(auth_codes))
            res_auth = await db.execute(stmt_auth)
            explicit_ids = set(res_auth.scalars().all())
            if allowed_authority_ids is not None:
                allowed_authority_ids = allowed_authority_ids.intersection(explicit_ids)
            else:
                allowed_authority_ids = explicit_ids
            jurisdiction_filtered = True

        stmt = cls._build_search_stmt(query_in, allowed_authority_ids)

        search_raw = query_in.query.strip().lower()
        search_terms = [t for t in re.split(r"\s+", search_raw) if len(t) >= 2]

        if not search_terms:
            return RegulatorySearchResponse(
                total=0,
                page=(query_in.offset // query_in.limit) + 1 if query_in.limit > 0 else 1,
                limit=query_in.limit,
                results=[],
                jurisdiction_filtered=jurisdiction_filtered,
                applied_filters=query_in.model_dump(exclude={"query"}),
            )

        res = await db.execute(stmt)
        candidates = list(res.scalars().unique().all())

        return cls._rank_and_format_results(candidates, query_in, search_raw, search_terms, jurisdiction_filtered)

    @classmethod
    def search(
        cls,
        db: Session,
        query_in: RegulatorySearchQuery,
    ) -> RegulatorySearchResponse:
        """
        Synchronously executes a jurisdiction-aware search across regulatory clauses.
        """
        jurisdiction_filtered = False
        allowed_authority_ids: Optional[Set[uuid.UUID]] = None

        if query_in.city or query_in.province:
            resolved_authorities = RegulatoryDiscoveryService.resolve_authorities_for_location(
                db=db,
                city=query_in.city,
                province=query_in.province,
            )
            allowed_authority_ids = {a.id for a in resolved_authorities}
            jurisdiction_filtered = True

        if query_in.authority_codes:
            auth_codes = [c.upper() for c in query_in.authority_codes]
            stmt_auth = select(RegulatoryAuthority.id).where(RegulatoryAuthority.code.in_(auth_codes))
            explicit_ids = set(db.execute(stmt_auth).scalars().all())
            if allowed_authority_ids is not None:
                allowed_authority_ids = allowed_authority_ids.intersection(explicit_ids)
            else:
                allowed_authority_ids = explicit_ids
            jurisdiction_filtered = True

        stmt = cls._build_search_stmt(query_in, allowed_authority_ids)

        search_raw = query_in.query.strip().lower()
        search_terms = [t for t in re.split(r"\s+", search_raw) if len(t) >= 2]

        if not search_terms:
            return RegulatorySearchResponse(
                total=0,
                page=(query_in.offset // query_in.limit) + 1 if query_in.limit > 0 else 1,
                limit=query_in.limit,
                results=[],
                jurisdiction_filtered=jurisdiction_filtered,
                applied_filters=query_in.model_dump(exclude={"query"}),
            )

        candidates = list(db.execute(stmt).scalars().unique().all())
        return cls._rank_and_format_results(candidates, query_in, search_raw, search_terms, jurisdiction_filtered)

    @classmethod
    def _build_search_stmt(
        cls,
        query_in: RegulatorySearchQuery,
        allowed_authority_ids: Optional[Set[uuid.UUID]],
    ):
        stmt = (
            select(RegulatoryClause)
            .join(RegulatoryClause.version)
            .join(RegulatoryDocumentVersion.document)
            .join(RegulatoryDocument.authority)
            .options(
                joinedload(RegulatoryClause.version).joinedload(RegulatoryDocumentVersion.document).joinedload(RegulatoryDocument.authority)
            )
        )

        # Currency filter
        if query_in.is_current_only:
            stmt = stmt.where(RegulatoryDocumentVersion.is_current == True)

        # Point-in-time effective date filter
        if query_in.effective_date:
            eff_d = query_in.effective_date
            stmt = stmt.where(
                and_(
                    or_(RegulatoryDocumentVersion.effective_date == None, RegulatoryDocumentVersion.effective_date <= eff_d),
                    or_(RegulatoryDocumentVersion.expiry_date == None, RegulatoryDocumentVersion.expiry_date >= eff_d),
                )
            )

        # Authority boundary filter
        if allowed_authority_ids is not None:
            stmt = stmt.where(RegulatoryDocument.authority_id.in_(allowed_authority_ids))

        # Document codes filter
        if query_in.document_codes:
            doc_codes = [d.upper() for d in query_in.document_codes]
            stmt = stmt.where(RegulatoryDocument.document_code.in_(doc_codes))

        # Jurisdiction level filter
        if query_in.jurisdiction_level:
            stmt = stmt.where(RegulatoryAuthority.jurisdiction_level == query_in.jurisdiction_level)

        # Content types filter
        if query_in.content_types:
            stmt = stmt.where(RegulatoryClause.content_type.in_(query_in.content_types))

        # Legal significance filter
        if query_in.legal_significance:
            stmt = stmt.where(RegulatoryClause.legal_significance.in_(query_in.legal_significance))

        # Text matching
        search_raw = query_in.query.strip().lower()
        search_terms = [t for t in re.split(r"\s+", search_raw) if len(t) >= 2]

        if search_terms:
            or_clauses = []
            for term in search_terms:
                pattern = f"%{term}%"
                or_clauses.extend([
                    RegulatoryClause.clause_title.ilike(pattern),
                    RegulatoryClause.normalized_text.ilike(pattern),
                    RegulatoryClause.original_text.ilike(pattern),
                    RegulatoryClause.clause_number.ilike(pattern),
                ])
            stmt = stmt.where(or_(*or_clauses))

        return stmt

    @classmethod
    def _rank_and_format_results(
        cls,
        candidates: List[RegulatoryClause],
        query_in: RegulatorySearchQuery,
        search_raw: str,
        search_terms: List[str],
        jurisdiction_filtered: bool,
    ) -> RegulatorySearchResponse:
        scored_results: List[Tuple[float, RegulatoryClause, List[str]]] = []
        for clause in candidates:
            score, matched = cls._score_clause(clause, search_raw, search_terms)
            if score > 0:
                scored_results.append((score, clause, matched))

        scored_results.sort(key=lambda x: x[0], reverse=True)

        total_matches = len(scored_results)
        page_slice = scored_results[query_in.offset : query_in.offset + query_in.limit]

        formatted_results: List[RegulatorySearchResult] = []
        for score, clause, matched in page_slice:
            citation = cls.format_citation(clause)
            clause_dto = RegulatoryClauseRead.model_validate(clause)
            formatted_results.append(
                RegulatorySearchResult(
                    clause=clause_dto,
                    citation=citation,
                    relevance_score=round(score, 3),
                    matched_terms=matched,
                )
            )

        current_page = (query_in.offset // query_in.limit) + 1 if query_in.limit > 0 else 1

        return RegulatorySearchResponse(
            total=total_matches,
            page=current_page,
            limit=query_in.limit,
            results=formatted_results,
            jurisdiction_filtered=jurisdiction_filtered,
            applied_filters=query_in.model_dump(exclude={"query"}),
        )

    @classmethod
    def _score_clause(
        cls,
        clause: RegulatoryClause,
        raw_query: str,
        terms: List[str],
    ) -> Tuple[float, List[str]]:
        score = 0.0
        matched_terms = []

        title = (clause.clause_title or "").lower()
        norm_text = (clause.normalized_text or clause.original_text or "").lower()
        c_num = (clause.clause_number or "").lower()
        sec_title = (clause.section_title or "").lower()

        if raw_query in norm_text:
            score += 15.0
            matched_terms.append(raw_query)
        if raw_query in title:
            score += 25.0

        for t in terms:
            term_matched = False
            if t in c_num:
                score += 8.0
                term_matched = True
            if t in title:
                score += 6.0
                term_matched = True
            if t in sec_title:
                score += 3.0
                term_matched = True
            if t in norm_text:
                score += 2.0
                term_matched = True

            if term_matched:
                matched_terms.append(t)

        # Weight bonus for mandatory requirements / prohibitions
        if clause.legal_significance in ("mandatory_requirement", "prohibition"):
            score *= 1.25

        return score, list(set(matched_terms))

    @classmethod
    def format_citation(cls, clause: RegulatoryClause) -> RegulatoryCitation:
        version = clause.version
        doc = version.document if version else None
        authority = doc.authority if doc else None

        auth_code = authority.code if authority else "UNKNOWN"
        auth_name = authority.name if authority else "Unknown Authority"
        doc_code = doc.document_code if doc else "UNKNOWN-DOC"
        doc_title = doc.title if doc else "Unknown Statutory Document"
        version_label = version.version_label if version else "1.0"
        legal_force = doc.legal_force_status if doc else "mandatory_notified"
        cred_tier = authority.credibility_tier if authority else "tier_b_official_regulatory"

        parts = [auth_code, doc_title, f"Ed. {version_label}"]

        if clause.chapter_number:
            parts.append(f"Ch. {clause.chapter_number}")
        if clause.section_number:
            parts.append(f"Sec. {clause.section_number}")
        if clause.clause_number:
            parts.append(f"Clause {clause.clause_number}")

        if clause.page_start:
            if clause.page_end and clause.page_end > clause.page_start:
                parts.append(f"pp. {clause.page_start}-{clause.page_end}")
            else:
                parts.append(f"p. {clause.page_start}")

        citation_str = f"[{', '.join(parts)}]"

        return RegulatoryCitation(
            citation_string=citation_str,
            authority_code=auth_code,
            authority_name=auth_name,
            document_code=doc_code,
            document_title=doc_title,
            version_label=version_label,
            section_identifier=clause.section_number,
            clause_number=clause.clause_number,
            page_start=clause.page_start,
            page_end=clause.page_end,
            legal_force_status=legal_force,
            legal_significance=clause.legal_significance,
            credibility_tier=cred_tier,
        )

    @classmethod
    async def get_regulatory_guidance_for_safety_async(
        cls,
        db: AsyncSession,
        hazard_code: str,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        hazard_mapping = {
            "shear_cracks_columns": "shear column reinforcement seismic",
            "diagonal_cracks_beam": "diagonal tension beam shear reinforcement",
            "settlement_cracks": "differential settlement foundation bearing capacity",
            "spalling_concrete": "concrete cover reinforcement corrosion spalling",
            "diy_column_removal": "unauthorized load bearing alteration removal penalty",
            "seismic_zone": "seismic zone map lateral force design",
        }

        search_text = hazard_mapping.get(hazard_code, hazard_code.replace("_", " "))

        query = RegulatorySearchQuery(
            query=search_text,
            city=city,
            document_codes=["BCP-SP-2007", "LDA-BZR-2020", "SBCA-KBTPR-2002", "CDA-BR-2020"],
            limit=5,
        )

        search_response = await cls.search_async(db, query)

        return {
            "hazard_code": hazard_code,
            "disclaimer": (
                "Statutory regulatory citations are provided solely for professional engineering reference "
                "and legal compliance verification. They do not constitute an on-site structural clearance, "
                "nor do they modify, downgrade, or override structural hazard classifications or emergency evacuation advisories."
            ),
            "applicable_regulations_count": search_response.total,
            "citations": [r.citation.model_dump() for r in search_response.results],
            "relevant_clauses": [
                {
                    "clause_number": r.clause.clause_number,
                    "clause_title": r.clause.clause_title,
                    "legal_significance": r.clause.legal_significance,
                    "summary": r.clause.normalized_text[:200] if r.clause.normalized_text else "",
                }
                for r in search_response.results
            ],
        }

    @classmethod
    def get_regulatory_guidance_for_safety(
        cls,
        db: Session,
        hazard_code: str,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        hazard_mapping = {
            "shear_cracks_columns": "shear column reinforcement seismic",
            "diagonal_cracks_beam": "diagonal tension beam shear reinforcement",
            "settlement_cracks": "differential settlement foundation bearing capacity",
            "spalling_concrete": "concrete cover reinforcement corrosion spalling",
            "diy_column_removal": "unauthorized load bearing alteration removal penalty",
            "seismic_zone": "seismic zone map lateral force design",
        }

        search_text = hazard_mapping.get(hazard_code, hazard_code.replace("_", " "))

        query = RegulatorySearchQuery(
            query=search_text,
            city=city,
            document_codes=["BCP-SP-2007", "LDA-BZR-2020", "SBCA-KBTPR-2002", "CDA-BR-2020"],
            limit=5,
        )

        search_response = cls.search(db, query)

        return {
            "hazard_code": hazard_code,
            "disclaimer": (
                "Statutory regulatory citations are provided solely for professional engineering reference "
                "and legal compliance verification. They do not constitute an on-site structural clearance, "
                "nor do they modify, downgrade, or override structural hazard classifications or emergency evacuation advisories."
            ),
            "applicable_regulations_count": search_response.total,
            "citations": [r.citation.model_dump() for r in search_response.results],
            "relevant_clauses": [
                {
                    "clause_number": r.clause.clause_number,
                    "clause_title": r.clause.clause_title,
                    "legal_significance": r.clause.legal_significance,
                    "summary": r.clause.normalized_text[:200] if r.clause.normalized_text else "",
                }
                for r in search_response.results
            ],
        }
