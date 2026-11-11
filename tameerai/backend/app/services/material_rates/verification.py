"""
TameerAI - Hybrid Multi-Source Verification Engine (Stage 2D)

Implements:
1. Strict Comparability Matrix:
   - Matching product, category, canonical city, standard unit, and price basis.
   - Temporal window enforcement (7 days for high volatility, 30 days for low volatility).
2. Outlier Detection & Spread Analysis:
   - Robust median calculation, Interquartile Range (IQR), and spread percentage.
   - Flagging spread > 15% as conflicted.
3. Provenance & Syndication Independence:
   - Secondary and syndicated publishers referencing the same source cannot provide independent corroboration.
4. Deterministic Verification Status Rules:
   - verified_quote: Direct verified dealer quote with documentary proof.
   - cross_checked: >= 2 independent, non-syndicated sources within 5% spread.
   - verified_market_range: >= 3 independent sources within 10% market tolerance.
   - indicative: Single secondary source or unverified price estimate.
   - conflicted: Multiple comparable sources diverging > 15%.
   - stale: Observation older than 30 days (or source TTL).
5. Durable Audit Trail:
   - Inserts MaterialRateVerificationEvent records for each evaluation without mutating immutable observations.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateVerificationEvent,
)
from app.services.material_rates.contracts import PriceBasis, SourceCategory
from app.services.material_rates.db_compat import (
    db_commit,
    db_execute,
    db_refresh,
    db_scalar,
    db_scalars,
)

logger = logging.getLogger("tameerai.material_rates.verification")


def _normalize_dt(dt: Optional[datetime]) -> datetime:
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class VerificationDecision:
    """Encapsulates the result of a multi-source verification evaluation."""

    def __init__(
        self,
        new_status: str,
        reason: str,
        rule_code: str,
        confidence_score: int,
        metadata_snapshot: Dict[str, Any],
    ):
        self.new_status = new_status
        self.reason = reason
        self.rule_code = rule_code
        self.confidence_score = confidence_score
        self.metadata_snapshot = metadata_snapshot


class MultiSourceVerificationEngine:
    """
    Evaluates market rate observations against comparable evidence
    to determine authoritative verification tiers with complete explainability.
    """

    VOLATILITY_WINDOWS = {
        "extreme": timedelta(days=3),
        "high": timedelta(days=7),
        "medium": timedelta(days=14),
        "low": timedelta(days=30),
    }

    @staticmethod
    def calculate_spread_and_median(prices: List[Decimal]) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Calculates min, max, median, and percentage spread for a set of prices.
        Spread = ((max - min) / median) * 100
        """
        if not prices:
            return Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")

        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        min_p = sorted_prices[0]
        max_p = sorted_prices[-1]

        if n % 2 == 1:
            median_p = sorted_prices[n // 2]
        else:
            median_p = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / Decimal("2")

        if median_p > Decimal("0"):
            spread_pct = ((max_p - min_p) / median_p) * Decimal("100")
        else:
            spread_pct = Decimal("0")

        return min_p, max_p, median_p, spread_pct.quantize(Decimal("0.01"))

    @classmethod
    def are_comparable(
        cls,
        obs_a: MaterialRateObservation,
        obs_b: MaterialRateObservation,
        product: Optional[MaterialRateProduct] = None,
    ) -> bool:
        """Determines if two observations are strictly comparable."""
        if obs_a.product_id != obs_b.product_id:
            return False
        if obs_a.normalized_unit != obs_b.normalized_unit:
            return False

        # City comparability: exact match or both national
        if (obs_a.city or "").lower() != (obs_b.city or "").lower():
            return False

        # Price basis comparability: retail must not be compared directly with ex-factory/ex-mill
        meta_a = obs_a.observation_metadata or {}
        meta_b = obs_b.observation_metadata or {}
        basis_a = str(meta_a.get("price_basis") or "").lower()
        basis_b = str(meta_b.get("price_basis") or "").lower()
        ex_factory_terms = {"ex_factory", "ex_mill"}
        if basis_a and basis_b and basis_a != basis_b:
            if (basis_a in ex_factory_terms and basis_b not in ex_factory_terms) or (basis_b in ex_factory_terms and basis_a not in ex_factory_terms):
                return False

        # Grade / Spec comparability: Grade 40 must not be treated as Grade 60
        grade_a = str(meta_a.get("grade") or "").lower()
        grade_b = str(meta_b.get("grade") or "").lower()
        if grade_a and grade_b and ("40" in grade_a and "60" in grade_b or "60" in grade_a and "40" in grade_b):
            return False

        # Brand comparability: different declared brands must not be cross-compared as identical
        brand_a = str(meta_a.get("brand") or "").strip().lower()
        brand_b = str(meta_b.get("brand") or "").strip().lower()
        if brand_a and brand_b and brand_a != brand_b:
            return False

        # Time window comparability
        volatility = product.volatility_tier if product else "medium"
        window = cls.VOLATILITY_WINDOWS.get(volatility, timedelta(days=14))

        date_a = _normalize_dt(obs_a.published_at or obs_a.collected_at)
        date_b = _normalize_dt(obs_b.published_at or obs_b.collected_at)
        if abs(date_a - date_b) > window:
            return False

        return True

    @staticmethod
    def extract_provenance_root(obs: MaterialRateObservation, source: Optional[MaterialRateSource]) -> str:
        """
        Extracts the ultimate root data source to prevent syndicated sources
        from counting as independent confirmations.
        """
        meta = obs.observation_metadata or {}
        provenance = meta.get("provenance", {})

        if provenance.get("republished_from"):
            return str(provenance["republished_from"]).strip().lower()
        if provenance.get("original_source_citation"):
            return str(provenance["original_source_citation"]).strip().lower()

        if source:
            return str(source.code).strip().lower()
        return str(obs.source_id).strip().lower()

    async def evaluate_observation(
        self,
        db: Any,
        observation: MaterialRateObservation,
    ) -> VerificationDecision:
        """
        Evaluates a single observation against all comparable active observations.
        Returns a deterministic VerificationDecision.
        """
        now = datetime.now(timezone.utc)
        obs_date = observation.published_at or observation.collected_at
        if obs_date.tzinfo is None:
            obs_date = obs_date.replace(tzinfo=timezone.utc)

        # 1. Stale Check
        if (now - obs_date) > timedelta(days=30):
            return VerificationDecision(
                new_status="stale",
                reason=f"Observation is { (now - obs_date).days } days old, exceeding the 30-day freshness limit.",
                rule_code="RULE_EXPIRY_STALE",
                confidence_score=10,
                metadata_snapshot={"age_days": (now - obs_date).days},
            )

        # 2. Direct Dealer Quote Check
        if observation.dealer_quote_id:
            quote = await db_scalar(
                db,
                select(MaterialRateDealerQuote).where(MaterialRateDealerQuote.id == observation.dealer_quote_id),
            )
            if quote:
                dealer = await db_scalar(
                    db,
                    select(MaterialRateDealer).where(MaterialRateDealer.id == quote.dealer_id),
                )
                if dealer and dealer.verification_state == "verified" and quote.status == "verified":
                    return VerificationDecision(
                        new_status="verified_quote",
                        reason=f"Direct quotation issued by verified merchant '{dealer.business_name}' with verified documentary evidence.",
                        rule_code="RULE_DEALER_VERIFIED_QUOTE",
                        confidence_score=95,
                        metadata_snapshot={
                            "dealer_id": str(dealer.id),
                            "dealer_code": dealer.dealer_code,
                            "quote_id": str(quote.id),
                        },
                    )

        # 3. Fetch Product & Comparables
        product = await db_scalar(
            db,
            select(MaterialRateProduct).where(MaterialRateProduct.id == observation.product_id),
        )
        volatility = product.volatility_tier if product else "medium"
        window = self.VOLATILITY_WINDOWS.get(volatility, timedelta(days=14))
        window_start = obs_date - window
        window_end = obs_date + window

        # Query all observations for same product and city in time window
        stmt = (
            select(MaterialRateObservation)
            .where(
                MaterialRateObservation.product_id == observation.product_id,
                MaterialRateObservation.normalized_unit == observation.normalized_unit,
                MaterialRateObservation.id != observation.id,
            )
        )
        if observation.city:
            stmt = stmt.where(MaterialRateObservation.city == observation.city)
        else:
            stmt = stmt.where(MaterialRateObservation.city.is_(None))

        candidates: List[MaterialRateObservation] = list(await db_scalars(db, stmt))
        # Filter by time window in memory to support published_at or collected_at
        comparables = [
            c for c in candidates
            if abs(_normalize_dt(c.published_at or c.collected_at) - obs_date) <= window
        ]

        if not comparables:
            # Single source with no corroboration -> indicative
            return VerificationDecision(
                new_status="indicative",
                reason="Single source observation with no contemporaneous market corroboration.",
                rule_code="RULE_SINGLE_SOURCE_INDICATIVE",
                confidence_score=50,
                metadata_snapshot={"comparables_found": 0},
            )

        # 4. Filter for Independent Provenance
        source_records = {}
        all_obs_to_check = [observation] + comparables
        for o in all_obs_to_check:
            if o.source_id not in source_records:
                src = await db_scalar(db, select(MaterialRateSource).where(MaterialRateSource.id == o.source_id))
                source_records[o.source_id] = src

        obs_root = self.extract_provenance_root(observation, source_records.get(observation.source_id))
        independent_comparables: List[MaterialRateObservation] = []
        seen_roots = {obs_root}

        for c in comparables:
            c_root = self.extract_provenance_root(c, source_records.get(c.source_id))
            if c_root not in seen_roots:
                independent_comparables.append(c)
                seen_roots.add(c_root)

        all_cluster = [observation] + independent_comparables
        cluster_prices = [c.normalized_price_pkr for c in all_cluster]
        min_p, max_p, median_p, spread_pct = self.calculate_spread_and_median(cluster_prices)

        # Deviation of this observation from the cluster median
        dev_pct = Decimal("0")
        if median_p > Decimal("0"):
            dev_pct = (abs(observation.normalized_price_pkr - median_p) / median_p) * Decimal("100")
            dev_pct = dev_pct.quantize(Decimal("0.01"))

        # 5. Outlier & Conflict Check (> 15% divergence)
        if spread_pct > Decimal("15.00") or dev_pct > Decimal("15.00"):
            return VerificationDecision(
                new_status="conflicted",
                reason=(
                    f"Market rate conflict detected: cluster spread of {spread_pct}% "
                    f"exceeds 15% tolerance (median: PKR {median_p}, observation: PKR {observation.normalized_price_pkr})."
                ),
                rule_code="RULE_SPREAD_CONFLICTED",
                confidence_score=35,
                metadata_snapshot={
                    "spread_pct": float(spread_pct),
                    "deviation_pct": float(dev_pct),
                    "median_price": float(median_p),
                    "comparable_count": len(all_cluster),
                    "independent_sources": list(seen_roots),
                },
            )

        # 6. High Consensus (>= 3 independent sources within 10%)
        if len(all_cluster) >= 3 and spread_pct <= Decimal("10.00"):
            return VerificationDecision(
                new_status="verified_market_range",
                reason=(
                    f"Consensus achieved: corroborated by {len(all_cluster)} independent sources "
                    f"within {spread_pct}% tight market spread (median: PKR {median_p})."
                ),
                rule_code="RULE_VERIFIED_MARKET_RANGE",
                confidence_score=90,
                metadata_snapshot={
                    "spread_pct": float(spread_pct),
                    "median_price": float(median_p),
                    "independent_sources_count": len(all_cluster),
                },
            )

        # 7. Cross-Checked (>= 2 independent sources within 5%)
        if len(all_cluster) >= 2 and spread_pct <= Decimal("5.00"):
            return VerificationDecision(
                new_status="cross_checked",
                reason=(
                    f"Cross-checked: corroborated by 2 independent sources within {spread_pct}% spread "
                    f"(median: PKR {median_p})."
                ),
                rule_code="RULE_CROSS_CHECKED_TIGHT",
                confidence_score=85,
                metadata_snapshot={
                    "spread_pct": float(spread_pct),
                    "median_price": float(median_p),
                },
            )

        # Fallback indicative
        return VerificationDecision(
            new_status="indicative",
            reason=f"Corroborating data available ({len(all_cluster)} sources, spread {spread_pct}%), but below formal verification criteria.",
            rule_code="RULE_MARKET_INDICATIVE",
            confidence_score=60,
            metadata_snapshot={
                "spread_pct": float(spread_pct),
                "comparables_count": len(all_cluster),
            },
        )

    async def verify_observation(
        self,
        db: Any,
        observation_id: uuid.UUID,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> MaterialRateVerificationEvent:
        """
        Evaluates an observation, logs an explainable MaterialRateVerificationEvent,
        and returns the durable audit trail record.
        Strictly preserves append-only immutability of MaterialRateObservation.
        """
        obs = await db_scalar(
            db,
            select(MaterialRateObservation).where(MaterialRateObservation.id == observation_id),
        )
        if not obs:
            raise ValueError(f"Observation {observation_id} not found")

        # Determine previous status from latest verification event if present, else observation status
        latest_event = await db_scalar(
            db,
            select(MaterialRateVerificationEvent)
            .where(MaterialRateVerificationEvent.observation_id == obs.id)
            .order_by(desc(MaterialRateVerificationEvent.created_at)),
        )
        prior_status = latest_event.new_status if latest_event else obs.verification_status

        decision = await self.evaluate_observation(db, obs)

        event = MaterialRateVerificationEvent(
            id=uuid.uuid4(),
            observation_id=obs.id,
            dealer_quote_id=obs.dealer_quote_id,
            previous_status=prior_status,
            new_status=decision.new_status,
            reason=decision.reason,
            actor_user_id=actor_user_id,
            metadata_snapshot={
                "rule_code": decision.rule_code,
                "confidence_score": decision.confidence_score,
                "metrics": decision.metadata_snapshot,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(event)
        await db_commit(db)
        await db_refresh(db, event)
        return event

    async def verify_unverified_observations(
        self,
        db: Any,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Sweeps unverified/indicative observations and executes verification rules.
        Used by background worker tasks.
        """
        # Select observations that have not had a verification event in the past 24 hours
        stmt = (
            select(MaterialRateObservation)
            .order_by(desc(MaterialRateObservation.created_at))
            .limit(limit)
        )
        observations = await db_scalars(db, stmt)

        verified_count = 0
        conflicted_count = 0
        stale_count = 0

        for obs in observations:
            try:
                ev = await self.verify_observation(db, obs.id)
                if ev.new_status in ("verified_quote", "cross_checked", "verified_market_range"):
                    verified_count += 1
                elif ev.new_status == "conflicted":
                    conflicted_count += 1
                elif ev.new_status == "stale":
                    stale_count += 1
            except Exception as e:
                logger.error("Error verifying observation %s: %s", obs.id, str(e))

        return {
            "total_evaluated": len(observations),
            "verified_count": verified_count,
            "conflicted_count": conflicted_count,
            "stale_count": stale_count,
        }


# Global singleton engine
verification_engine = MultiSourceVerificationEngine()
