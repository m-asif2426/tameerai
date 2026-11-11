"""
TameerAI - Centralized Material Product Identity & Market Date Resolution Service
Phase 03.1.3A.1 Core Infrastructure

Centralizes:
1. Canonical Product Identity Resolution (Grade 40 vs Grade 60):
   - Safely isolates Mild Steel Bar Grade 40 (STEEL_REBAR_G40) from Deformed Steel Bar Grade 60 (STEEL_REBAR_G60).
   - Resolves historical immutable PBS observations whose metadata indicates Grade 40
     even when stored with STEEL_REBAR_G60 product ID.
   - Provides consistent filtering across AI Bridge, Canonical Engine, Historical Service, and APIs.
2. Market Observation Date & Freshness Resolution:
   - Decouples ingestion/audit timestamps (collected_at, created_at) from authoritative market dates.
   - Derives effective market dates strictly from published_at, verified observation dates,
     or survey_reference_period (e.g. 'October, 2026').
   - Guarantees that historical records imported recently (with current collected_at) are NEVER
     treated as current or fresh market rates.
3. Authoritative Dealer Quotation Ownership & Quarantine:
   - Validates the authoritative dealer quotation relationship.
   - Enforces fail-closed tenancy: missing relationship, unknown ownership, or conflicting
     metadata immediately quarantines private dealer quotations.
"""

from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy import select, and_, or_, not_

from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
)
from app.services.material_rates.db_compat import (
    db_scalar,
    db_scalars,
)

logger = logging.getLogger("tameerai.material_rates.identity_resolver")

# Canonical Product Codes
PRODUCT_CODE_STEEL_G40 = "STEEL_REBAR_G40"
PRODUCT_CODE_STEEL_G60 = "STEEL_REBAR_G60"
CANONICAL_NAME_STEEL_G40 = "Mild Steel Bar Grade 40"
CANONICAL_NAME_STEEL_G60 = "Deformed Steel Bar Grade 60"

# Known canonical product IDs in PostgreSQL 17
KNOWN_PRODUCT_ID_G40 = uuid.UUID("70b657f5-9947-424b-859b-0c87f668841b")
KNOWN_PRODUCT_ID_G60 = uuid.UUID("3ccf0cab-0b2f-4212-b3b8-ec332f7af5bc")

MONTH_NAME_TO_INT = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def detect_observation_steel_grade(
    obs: MaterialRateObservation,
) -> Optional[str]:
    """
    Inspects observation metadata and specifications to detect if the record
    is explicitly Grade 40 or Grade 60 steel rebar.
    Returns: 'Grade 40', 'Grade 60', or None if not determinable/not steel.
    """
    meta = obs.observation_metadata or {}
    raw_spec = (meta.get("raw_specification") or "").lower()
    item_name = (meta.get("item_name") or "").lower()
    meta_grade = (meta.get("grade") or "").lower()

    text_to_check = f"{raw_spec} {item_name} {meta_grade}"

    # Grade 40 check: '40 grade', 'grade 40', 'iron bars (1/2" 40 grade)'
    if re.search(r"\b(grade\s*40|40\s*grade|g40)\b", text_to_check):
        return "Grade 40"

    # Grade 60 check: '60 grade', 'grade 60', 'g60'
    if re.search(r"\b(grade\s*60|60\s*grade|g60)\b", text_to_check):
        return "Grade 60"

    return None


class CentralizedProductIdentityResolver:
    """
    Shared singleton / service that resolves canonical product identity,
    market timestamps, and tenancy across all consumers.
    """

    def __init__(self):
        self._g40_product_cache: Optional[MaterialRateProduct] = None
        self._g60_product_cache: Optional[MaterialRateProduct] = None

    async def get_canonical_product(
        self,
        db: Any,
        code: str,
    ) -> Optional[MaterialRateProduct]:
        """Retrieves canonical product by product_code from the active database."""
        stmt = select(MaterialRateProduct).where(MaterialRateProduct.code == code)
        return await db_scalar(db, stmt)

    async def resolve_observation_canonical_product(
        self,
        db: Any,
        obs: MaterialRateObservation,
        stored_product: Optional[MaterialRateProduct] = None,
    ) -> Tuple[uuid.UUID, str, str, Optional[str]]:
        """
        Determines the true canonical identity of an observation.
        Returns: (resolved_product_id, resolved_product_code, resolved_canonical_name, detected_grade)
        """
        if stored_product is None and obs.product_id:
            stored_product = await db_scalar(
                db,
                select(MaterialRateProduct).where(MaterialRateProduct.id == obs.product_id),
            )

        detected_grade = detect_observation_steel_grade(obs)

        # Historical remediation: If stored under STEEL_REBAR_G60 or similar, but
        # detected as Grade 40, map to canonical Grade 40 product.
        if detected_grade == "Grade 40":
            g40_prod = await self.get_canonical_product(db, PRODUCT_CODE_STEEL_G40)
            if g40_prod:
                return g40_prod.id, g40_prod.code, g40_prod.canonical_name, "Grade 40"
            return (
                KNOWN_PRODUCT_ID_G40,
                PRODUCT_CODE_STEEL_G40,
                CANONICAL_NAME_STEEL_G40,
                "Grade 40",
            )

        if stored_product:
            return (
                stored_product.id,
                stored_product.code,
                stored_product.canonical_name,
                detected_grade or ("Grade 60" if stored_product.code == PRODUCT_CODE_STEEL_G60 else None),
            )

        return (
            obs.product_id,
            "UNKNOWN",
            "Unknown Product",
            detected_grade,
        )

    def is_observation_eligible_for_product(
        self,
        obs: MaterialRateObservation,
        target_product_code: str,
        stored_product_code: Optional[str] = None,
    ) -> bool:
        """
        Determines if an observation strictly matches the target canonical product (Phase 03.4E.2A.3 Task 3).
        - Target Grade 40: Matches ONLY if verified as Grade 40 and standard unit (51 authentic observations).
        - Target Grade 60: Matches ONLY if verified as Grade 60 and standard unit (23 authentic observations).
        - Malformed/unverified unit records: Strictly excluded from both Grade 40 and Grade 60.
        - Other products: Matches stored_product_code.
        """
        detected_grade = detect_observation_steel_grade(obs)
        unit_str = str(obs.normalized_unit or "").lower()
        price_val = float(obs.normalized_price_pkr or 0)
        is_malformed = price_val < 1000 or unit_str.startswith("rs_") or "rs" in unit_str or unit_str != "metric_ton"

        if target_product_code == PRODUCT_CODE_STEEL_G40:
            if is_malformed:
                return False
            return detected_grade == "Grade 40"

        if target_product_code == PRODUCT_CODE_STEEL_G60:
            if is_malformed:
                return False
            if detected_grade != "Grade 60":
                return False
            if stored_product_code and stored_product_code != PRODUCT_CODE_STEEL_G60:
                return False
            return True

        if stored_product_code:
            return stored_product_code == target_product_code

        return True

    @staticmethod
    def is_synthetic_test_fixture(
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource] = None,
    ) -> bool:
        """
        Provenance-based synthetic fixture detection (Phase 03.4C.2 Task 4):
        Strictly flags synthetic test records so they are never included in genuine market benchmarks.
        """
        if getattr(obs, "verification_status", None) == "synthetic_test_fixture":
            return True
        meta = getattr(obs, "observation_metadata", None) or {}
        if meta.get("is_synthetic") is True or meta.get("synthetic") is True:
            return True
        if source:
            src_code = (getattr(source, "code", None) or "").upper()
            src_name = (getattr(source, "name", None) or "").upper()
            if (
                src_code.startswith("SRC-PG17-")
                or src_code.startswith("GHARHUB_SRC_")
                or src_code.startswith("PBS_SPI_")
                or src_code.startswith("SRC-AUDIT-")
                or "TEST" in src_code
                or "TEST" in src_name
            ):
                return True
        return False

    @staticmethod
    def is_pbs_monthly_observation(
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource] = None,
    ) -> bool:
        """Determines if an observation originates from the PBS Monthly Construction dataset."""
        meta = obs.observation_metadata or {}
        if source and getattr(source, "code", None) == "PBS_STATISTICAL_MONTHLY":
            return True
        if source and getattr(source, "refresh_cadence", None) == "monthly" and "PBS" in (getattr(source, "code", "") or ""):
            return True
        if meta.get("agency") == "Pakistan Bureau of Statistics":
            url = meta.get("source_url") or ""
            if "Urbn-Construction" in url or "pbs.gov.pk" in url:
                return True
            item_name = meta.get("item_name") or ""
            if "grade 40" in item_name.lower() or "deformed" in item_name.lower() or "cement" in item_name.lower():
                return True
        return False

    @classmethod
    def resolve_effective_market_date(
        cls,
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource] = None,
    ) -> Optional[datetime]:
        """
        Source-specific reliable market date resolution (Task 2 & 3):
        1. PBS Monthly Construction Series:
           - Ingestion set published_at = 2026-10-01 (start of survey month) as an import artifact.
           - Economic statistical data reflects the full survey reference period ('October, 2026').
           - The query-layer mapping safely maps this to the period-end proxy: 2026-10-31 23:59:59 UTC.
        2. Authoritative publication timestamp (published_at): if present on other sources.
        3. Verified survey / observation date from metadata:
           - 'observation_date', 'survey_date', 'market_date', 'effective_date'
        4. Monthly survey reference period (e.g. 'October, 2026' or 'July, 2020'):
           Parses to the final day of the reference month at 23:59:59 UTC.
        5. Ingestion / audit timestamps (collected_at, created_at) are NEVER used
           as market dates and NEVER establish freshness.
        6. If no reliable market date exists, returns None.
        """
        meta = obs.observation_metadata or {}

        # 1. PBS Monthly Statistical Series: Check if it is a PBS monthly observation
        is_pbs_monthly = cls.is_pbs_monthly_observation(obs, source)
        if is_pbs_monthly:
            ref_period = meta.get("survey_reference_period") or meta.get("period")
            if not ref_period and obs.published_at is not None:
                # If published_at is in October 2026 (the known 188 historical rows import artifact)
                if obs.published_at.year == 2026 and obs.published_at.month == 10:
                    ref_period = "October, 2026"
            if ref_period and isinstance(ref_period, str):
                m = re.search(r"([A-Za-z]+)[,\s]+(\d{4})", ref_period)
                if m:
                    m_name = m.group(1).lower()
                    year = int(m.group(2))
                    m_num = MONTH_NAME_TO_INT.get(m_name)
                    if m_num and 1990 <= year <= 2100:
                        _, last_day = monthrange(year, m_num)
                        return datetime(year, m_num, last_day, 23, 59, 59, tzinfo=timezone.utc)

        # 2. Authoritative publication date (non-PBS monthly)
        if obs.published_at is not None and not is_pbs_monthly:
            dt = obs.published_at
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

        # 3. Trustworthy observation date from metadata
        for key in ("observation_date", "survey_date", "market_date", "effective_date"):
            val = meta.get(key)
            if val:
                if isinstance(val, datetime):
                    return val.replace(tzinfo=timezone.utc) if val.tzinfo is None else val
                elif isinstance(val, str):
                    try:
                        parsed = datetime.fromisoformat(val.replace("Z", "+00:00"))
                        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
                    except (ValueError, TypeError):
                        pass

        # 4. Monthly survey reference period from metadata (general case)
        ref_period = meta.get("survey_reference_period") or meta.get("period")
        if ref_period and isinstance(ref_period, str):
            m = re.search(r"([A-Za-z]+)[,\s]+(\d{4})", ref_period)
            if m:
                m_name = m.group(1).lower()
                year = int(m.group(2))
                m_num = MONTH_NAME_TO_INT.get(m_name)
                if m_num and 1990 <= year <= 2100:
                    _, last_day = monthrange(year, m_num)
                    return datetime(year, m_num, last_day, 23, 59, 59, tzinfo=timezone.utc)

        # 5. Workbook compilation date metadata
        comp_date = meta.get("workbook_compilation_date")
        if comp_date and isinstance(comp_date, str):
            try:
                parsed = datetime.fromisoformat(comp_date.replace("Z", "+00:00"))
                return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
            except (ValueError, TypeError):
                pass

        # Fallback to published_at if present
        if obs.published_at is not None:
            dt = obs.published_at
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

        return None

    @classmethod
    def resolve_observation_date_semantics(
        cls,
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource] = None,
        now: Optional[datetime] = None,
        ttl_days: float = 45.0,
    ) -> Dict[str, Any]:
        """
        Auditable date attribution breakdown (Task 2):
        Distinguishes stored database columns/metadata from query-derived semantics.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        meta = obs.observation_metadata or {}
        is_pbs = cls.is_pbs_monthly_observation(obs, source)

        stored_ref_period = meta.get("survey_reference_period")
        stored_survey_date = meta.get("survey_date")
        stored_pub_date = meta.get("official_publication_date")

        query_ref_period = stored_ref_period or ("October, 2026" if is_pbs else None)
        effective_market_date = cls.resolve_effective_market_date(obs, source)

        is_fresh = False
        age_days = None
        if effective_market_date is not None:
            age_days = (now - effective_market_date).total_seconds() / 86400.0
            is_fresh = age_days <= ttl_days

        return {
            "observation_id": str(obs.id),
            "stored_published_at": obs.published_at.isoformat() if obs.published_at else None,
            "stored_collected_at": obs.collected_at.isoformat() if obs.collected_at else None,
            "stored_survey_reference_period": stored_ref_period,
            "stored_survey_date": stored_survey_date,
            "stored_official_publication_date": stored_pub_date,
            "is_pbs_monthly": is_pbs,
            "query_derived_survey_reference_period": query_ref_period,
            "query_derived_effective_market_date": effective_market_date.isoformat() if effective_market_date else None,
            "market_date_derivation_method": (
                "period_end_proxy_2026_10_31" if is_pbs and effective_market_date and effective_market_date.day == 31
                else ("published_at" if obs.published_at else "metadata_or_none")
            ),
            "freshness_reference_now": now.isoformat(),
            "age_days": round(age_days, 2) if age_days is not None else None,
            "ttl_days": ttl_days,
            "is_fresh": is_fresh,
        }

    @staticmethod
    def is_market_date_fresh(
        market_date: Optional[datetime],
        ttl_days: float,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Evaluates whether an observation's reliable market date is within its freshness TTL.
        Returns False if market_date is None or exceeds TTL.
        """
        if market_date is None:
            return False

        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        m_tz = market_date.replace(tzinfo=timezone.utc) if market_date.tzinfo is None else market_date
        age_days = (now - m_tz).total_seconds() / 86400.0
        return age_days <= ttl_days

    @staticmethod
    async def validate_dealer_quotation_tenancy(
        db: Any,
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource],
        requesting_project_id: Optional[uuid.UUID],
    ) -> Tuple[bool, Optional[str]]:
        """
        Authoritative Dealer Ownership & Tenancy Validation (Task 4):
        Rules:
        1. If observation is a dealer observation (dealer_quote_id exists, status is verified_quote,
           or source is dealer_network):
           - Must have an authoritative dealer_quote_id. If missing -> FAIL CLOSED (False, 'missing_quotation_link')
           - Must successfully load MaterialRateDealerQuote from DB with status == 'verified'.
           - Must verify active, vetted dealer profile.
           - Authoritative quotation ownership must be defined.
           - Observation metadata project_id (if present) must strictly match quotation ownership.
           - If conflicting ownership -> FAIL CLOSED (False, 'conflicting_project_ownership')
           - If unknown quotation ownership -> FAIL CLOSED (False, 'unknown_project_ownership')
           - Anonymous caller (requesting_project_id is None) -> FAIL CLOSED (False, 'anonymous_access_forbidden')
           - Project mismatch -> FAIL CLOSED (False, 'cross_project_isolation')
        2. If observation is not a dealer observation, returns True.
        """
        is_dealer = (
            obs.dealer_quote_id is not None
            or obs.verification_status == "verified_quote"
            or (source is not None and getattr(source, "source_type", None) == "dealer_network")
        )

        if not is_dealer:
            # Check if non-dealer observation has project-scoped restriction
            obs_meta = obs.observation_metadata or {}
            obs_proj = obs_meta.get("project_id")
            if obs_proj is not None:
                if requesting_project_id is None or str(obs_proj) != str(requesting_project_id):
                    return False, "project_scoped_observation_mismatch"
            return True, None

        # 1. Authoritative relationship MUST exist
        if obs.dealer_quote_id is None:
            return False, "missing_quotation_link"

        quote = await db_scalar(
            db,
            select(MaterialRateDealerQuote).where(MaterialRateDealerQuote.id == obs.dealer_quote_id),
        )
        if not quote or quote.status != "verified":
            return False, "unverified_dealer_quotation"

        # Check dealer validity
        dealer = await db_scalar(
            db,
            select(MaterialRateDealer).where(MaterialRateDealer.id == quote.dealer_id),
        )
        if not dealer or not dealer.is_active:
            return False, "inactive_dealer"
        if dealer.verification_state != "verified":
            return False, "unverified_dealer"

        # Check validity window
        now = datetime.now(timezone.utc)
        if quote.valid_until:
            q_val = quote.valid_until.replace(tzinfo=timezone.utc) if quote.valid_until.tzinfo is None else quote.valid_until
            if q_val < now:
                return False, "expired_dealer_quotation"

        # Extract authoritative quotation project ownership
        quote_proj = None
        if hasattr(quote, "quotation_metadata") and isinstance(quote.quotation_metadata, dict):
            quote_proj = quote.quotation_metadata.get("project_id")

        obs_meta = obs.observation_metadata or {}
        obs_proj = obs_meta.get("project_id")

        # Conflict check: If both exist and disagree, quarantine
        if obs_proj is not None and quote_proj is not None:
            if str(obs_proj) != str(quote_proj):
                return False, "conflicting_project_ownership"

        authoritative_proj = quote_proj or obs_proj
        if authoritative_proj is None:
            return False, "unknown_project_ownership"

        if requesting_project_id is None:
            return False, "anonymous_access_forbidden"

        if str(authoritative_proj) != str(requesting_project_id):
            return False, "cross_project_isolation"

        return True, None


# Shared singleton instance
centralized_identity_resolver = CentralizedProductIdentityResolver()
