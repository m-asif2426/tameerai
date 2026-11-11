"""
TameerAI - Canonical Market Rate Engine (Stage 2F)

Implements:
1. Deterministic Multi-Factor Ranking & Selection:
   - Verification tier weight (40%), source credibility (30%), freshness decay (20%), geographic specificity (10%).
   - Detects market conflicts (> 15% divergence) and flags them safely.
2. Authoritative Synchronization into material_rates (app/models/cost.py):
   - Ensures 100% backward compatibility for BOQItem foreign keys and existing cost endpoints.
   - Computes historical trend (up, down, neutral) relative to previous canonical rates.
3. Market Snapshot Generation:
   - Creates point-in-time benchmark snapshots for all products across Pakistani cities.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.cost import MaterialRate
from app.models.material_rate import (
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateVerificationEvent,
)
from app.services.material_rates.db_compat import (
    db_commit,
    db_execute,
    db_refresh,
    db_scalar,
    db_scalars,
)
from app.services.material_rates.registry import national_registry
from app.services.material_rates.identity_resolver import (
    centralized_identity_resolver,
    detect_observation_steel_grade,
    PRODUCT_CODE_STEEL_G40,
    PRODUCT_CODE_STEEL_G60,
    KNOWN_PRODUCT_ID_G60,
)

logger = logging.getLogger("tameerai.material_rates.canonical")

MAJOR_PAKISTANI_CITIES = [
    "Lahore",
    "Karachi",
    "Islamabad",
    "Rawalpindi",
    "Peshawar",
    "Multan",
    "Faisalabad",
    "Quetta",
]


class CanonicalSelectionResult:
    """Represents the benchmark rate computed for a specific product and location."""

    def __init__(
        self,
        product: MaterialRateProduct,
        city: str,
        rate_pkr: Decimal,
        prev_rate_pkr: Optional[Decimal],
        trend: str,
        verification_status: str,
        confidence_score: int,
        observation_count: int,
        min_rate_pkr: Decimal,
        max_rate_pkr: Decimal,
        is_conflicted: bool = False,
        statistical_rate_pkr: Optional[Decimal] = None,
        wholesale_rate_pkr: Optional[Decimal] = None,
        is_composite: bool = False,
        price_basis: str = "indicative_composite",
        eligible_observation_count: Optional[int] = None,
        contributing_observation_count: Optional[int] = None,
        statistical_observation_count: Optional[int] = None,
        wholesale_observation_count: Optional[int] = None,
        evidence_quality_score: Optional[int] = None,
        confidence_methodology: str = "multi_factor_evidence_quality_heuristic",
    ):
        self.product = product
        self.city = city
        self.rate_pkr = rate_pkr
        self.prev_rate_pkr = prev_rate_pkr
        self.trend = trend
        self.verification_status = verification_status
        self.confidence_score = confidence_score
        self.evidence_quality_score = evidence_quality_score if evidence_quality_score is not None else confidence_score
        self.confidence_methodology = confidence_methodology
        self.observation_count = observation_count
        self.eligible_observation_count = eligible_observation_count if eligible_observation_count is not None else observation_count
        self.contributing_observation_count = contributing_observation_count if contributing_observation_count is not None else min(3, observation_count)
        self.statistical_observation_count = statistical_observation_count if statistical_observation_count is not None else (1 if statistical_rate_pkr is not None else 0)
        self.wholesale_observation_count = wholesale_observation_count if wholesale_observation_count is not None else (observation_count - (1 if statistical_rate_pkr is not None else 0))
        self.min_rate_pkr = min_rate_pkr
        self.max_rate_pkr = max_rate_pkr
        self.is_conflicted = is_conflicted
        self.statistical_rate_pkr = statistical_rate_pkr
        self.wholesale_rate_pkr = wholesale_rate_pkr
        self.is_composite = is_composite
        self.price_basis = price_basis

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": str(self.product.id),
            "product_code": self.product.code,
            "product_name": self.product.canonical_name,
            "category": self.product.category,
            "city": self.city,
            "rate_pkr": float(self.rate_pkr),
            "prev_rate_pkr": float(self.prev_rate_pkr) if self.prev_rate_pkr else None,
            "unit": self.product.standard_unit,
            "trend": self.trend,
            "verification_status": self.verification_status,
            "confidence_score": self.confidence_score,
            "evidence_quality_score": self.evidence_quality_score,
            "confidence_methodology": self.confidence_methodology,
            "observation_count": self.observation_count,
            "eligible_observation_count": self.eligible_observation_count,
            "contributing_observation_count": self.contributing_observation_count,
            "statistical_observation_count": self.statistical_observation_count,
            "wholesale_observation_count": self.wholesale_observation_count,
            "price_range": {
                "min": float(self.min_rate_pkr),
                "max": float(self.max_rate_pkr),
            },
            "is_conflicted": self.is_conflicted,
            "statistical_rate_pkr": float(self.statistical_rate_pkr) if self.statistical_rate_pkr else None,
            "wholesale_rate_pkr": float(self.wholesale_rate_pkr) if self.wholesale_rate_pkr else None,
            "is_composite": self.is_composite,
            "price_basis": self.price_basis,
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }


class CanonicalMarketRateEngine:
    """Computes authoritative market benchmarks and synchronizes the canonical material_rates table."""

    TIER_WEIGHTS = {
        "verified_quote": 100,
        "cross_checked": 90,
        "verified_market_range": 85,
        "indicative": 50,
        "unverified": 30,
        "conflicted": 20,
        "stale": 10,
    }

    def compute_observation_weight(
        self,
        obs: MaterialRateObservation,
        source: Optional[MaterialRateSource],
        target_city: str,
        now: datetime,
        volume_count: int = 1,
        query_evidence_volume: Optional[int] = None,
    ) -> Decimal:
        """
        Computes composite ranking score according to the approved architecture:
        Score = (Credibility * 0.35) + (Verification * 0.30) + (Freshness * 0.25) + (Volume * 0.10)
        
        Uses Decimal arithmetic throughout to preserve full intermediate precision.
        All components are strictly normalized to [0.0, 100.0]:
        - Credibility (0-100): Publisher trustworthiness and methodology tier.
        - Verification (0-100): Verification status confidence (verified_quote=100, cross_checked=90, etc.)
        - Freshness (0-100): Exponential decay exp(-0.05 * days_old) * 100.
        - Volume (0-100): Overall query-wide market evidence density min(100.0, evidence_volume * 20.0).
          NOTE: This reflects dataset corroboration depth (>= 5 observations achieves 100% density).
          It does NOT represent the individual sample size of a source (e.g. PBS surveys thousands
          of retail establishments nationally to compute its single statistical average).
          Source-specific counts are preserved separately in CanonicalSelectionResult.
        """
        tier_weight = Decimal(str(self.TIER_WEIGHTS.get(obs.verification_status, 40)))

        credibility = Decimal("50.0")
        if source:
            entry = national_registry.get_source(source.code)
            if entry:
                credibility = Decimal(str(entry.credibility_score))
            elif source.reliability_tier == "authoritative":
                credibility = Decimal("95.0")
            elif source.reliability_tier == "verified":
                credibility = Decimal("80.0")
            else:
                credibility = Decimal("50.0")
        else:
            entry = national_registry.get_source(str(obs.source_id))
            if entry:
                credibility = Decimal(str(entry.credibility_score))

        # Freshness decay based on reliable market date (Task 3)
        # Ingestion timestamps (collected_at, created_at) must NEVER establish freshness
        market_date = centralized_identity_resolver.resolve_effective_market_date(obs, source)
        if market_date is not None:
            if market_date.tzinfo is None:
                market_date = market_date.replace(tzinfo=timezone.utc)
            days_old = max(0.0, (now - market_date).total_seconds() / 86400.0)
            freshness_float = max(0.0, min(100.0, math.exp(-0.05 * days_old) * 100.0))
            freshness_pct = Decimal(str(round(freshness_float, 6)))
        else:
            freshness_pct = Decimal("0.0")

        # Query-wide market evidence volume normalization: min(100.0, evidence_volume * 20.0)
        eff_volume = query_evidence_volume if query_evidence_volume is not None else volume_count
        volume_pct = Decimal(str(min(100.0, float(eff_volume) * 20.0)))

        FACTOR_CREDIBILITY = Decimal("0.35")
        FACTOR_VERIFICATION = Decimal("0.30")
        FACTOR_FRESHNESS = Decimal("0.25")
        FACTOR_VOLUME = Decimal("0.10")

        score = (
            (FACTOR_CREDIBILITY * credibility)
            + (FACTOR_VERIFICATION * tier_weight)
            + (FACTOR_FRESHNESS * freshness_pct)
            + (FACTOR_VOLUME * volume_pct)
        )
        return max(Decimal("0.0"), min(Decimal("100.0"), score))

    async def compute_canonical_rate_for_product_and_city(
        self,
        db: Any,
        product: MaterialRateProduct,
        city: str,
        now: Optional[datetime] = None,
    ) -> Optional[CanonicalSelectionResult]:
        """
        Computes the benchmark market rate for a specific product and city.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # Centralized canonical product identity query (Task 2)
        if product.code == PRODUCT_CODE_STEEL_G40:
            # Steel Grade 40 may include historical observations attached to G60 product id
            g60_prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G60)
            g60_id = g60_prod.id if g60_prod else KNOWN_PRODUCT_ID_G60
            stmt = (
                select(MaterialRateObservation)
                .where(
                    MaterialRateObservation.product_id.in_([product.id, g60_id]),
                    MaterialRateObservation.normalized_unit == product.standard_unit,
                )
            )
        else:
            stmt = (
                select(MaterialRateObservation)
                .where(
                    MaterialRateObservation.product_id == product.id,
                    MaterialRateObservation.normalized_unit == product.standard_unit,
                )
            )
        all_obs = list(await db_scalars(db, stmt))

        # Fetch sources for market date / TTL resolution and weight computation
        sources_map = {}
        for o in all_obs:
            if o.source_id not in sources_map:
                src = await db_scalar(db, select(MaterialRateSource).where(MaterialRateSource.id == o.source_id))
                sources_map[o.source_id] = src

        # Filter observations matching product identity, city, and market freshness
        obs_list = []
        for o in all_obs:
            src = sources_map.get(o.source_id)

            # 0. Provenance-based synthetic test fixture exclusion (Phase 03.4C.2 Task 4)
            if centralized_identity_resolver.is_synthetic_test_fixture(o, src):
                continue

            # 1. Product identity isolation (Grade 40 vs Grade 60)
            if not centralized_identity_resolver.is_observation_eligible_for_product(
                o, product.code, stored_product_code=product.code
            ):
                continue

            # 2. City match (target city or national/None)
            if city and o.city and o.city.lower() != city.lower():
                continue

            # 3. Market date & freshness verification (Task 3)
            # Never trust collected_at or created_at for freshness
            ttl_days = float(getattr(src, "freshness_ttl_days", 45) or 45)
            market_date = centralized_identity_resolver.resolve_effective_market_date(o, src)
            if not centralized_identity_resolver.is_market_date_fresh(market_date, ttl_days=ttl_days, now=now):
                continue

            obs_list.append(o)

        if not obs_list:
            return None

        # Calculate weights for each observation
        scored_obs: List[Tuple[MaterialRateObservation, Decimal]] = []
        for o in obs_list:
            w = self.compute_observation_weight(o, sources_map.get(o.source_id), city, now, volume_count=len(obs_list))
            scored_obs.append((o, w))

        # Deterministic sorting: weight DESC, published_at DESC, created_at DESC, id DESC
        def _sort_key(pair: Tuple[MaterialRateObservation, Decimal]):
            o, w = pair
            pub = o.published_at.replace(tzinfo=timezone.utc) if o.published_at and o.published_at.tzinfo is None else (o.published_at or datetime.min.replace(tzinfo=timezone.utc))
            created = o.created_at.replace(tzinfo=timezone.utc) if o.created_at and o.created_at.tzinfo is None else (o.created_at or datetime.min.replace(tzinfo=timezone.utc))
            return (w, pub, created, str(o.id))

        scored_obs.sort(key=_sort_key, reverse=True)

        prices = [o.normalized_price_pkr for o, _ in scored_obs]
        min_p = min(prices)
        max_p = max(prices)

        # Check for market conflict across observations
        is_conflicted = False
        if len(prices) >= 2:
            avg_p = sum(prices) / Decimal(str(len(prices)))
            spread = ((max_p - min_p) / avg_p) * Decimal("100")
            if spread > Decimal("15.00"):
                is_conflicted = True

        # Compute benchmark rate: weighted average of top 3 observations using Decimal arithmetic
        top_candidates = scored_obs[:3]
        total_weight = sum(w for _, w in top_candidates)
        if total_weight > Decimal("0"):
            weighted_sum = sum(o.normalized_price_pkr * w for o, w in top_candidates)
            benchmark_pkr = (weighted_sum / total_weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            benchmark_pkr = top_candidates[0][0].normalized_price_pkr

        # Task 3: Dual benchmark disaggregation (Statistical vs Wholesale)
        stat_obs = []
        ws_obs = []
        for o in obs_list:
            src = sources_map.get(o.source_id)
            meta = o.observation_metadata or {}
            is_pbs = "PBS" in ((src.code if src else "") or "").upper()
            basis = meta.get("price_basis") or ("retail_statistical" if is_pbs else "wholesale")
            if basis in ("retail_statistical", "statistical_index") or is_pbs:
                stat_obs.append(o)
            elif basis in ("wholesale", "retail", "ex_mill", "dealer_quotation"):
                ws_obs.append(o)

        statistical_rate_pkr = None
        if stat_obs:
            statistical_rate_pkr = stat_obs[0].normalized_price_pkr

        wholesale_rate_pkr = None
        if ws_obs:
            ws_prices = sorted([o.normalized_price_pkr for o in ws_obs])
            n_ws = len(ws_prices)
            if n_ws % 2 == 1:
                wholesale_rate_pkr = ws_prices[n_ws // 2]
            else:
                wholesale_rate_pkr = ((ws_prices[n_ws // 2 - 1] + ws_prices[n_ws // 2]) / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Check if top candidates blend mixed price bases
        unique_bases = set()
        for o, _ in top_candidates:
            src = sources_map.get(o.source_id)
            meta = o.observation_metadata or {}
            is_pbs = "PBS" in ((src.code if src else "") or "").upper()
            basis = meta.get("price_basis") or ("retail_statistical" if is_pbs else "wholesale")
            unique_bases.add(basis)

        is_composite = len(unique_bases) > 1
        price_basis_label = "indicative_composite" if is_composite else (list(unique_bases)[0] if unique_bases else "indicative")

        # Determine verification tier and confidence
        top_obs = top_candidates[0][0]
        if is_conflicted:
            ver_status = "conflicted"
        elif is_composite:
            # An indicative composite that blends incompatible bases must NEVER be marked verified
            ver_status = "indicative"
        else:
            ver_status = top_obs.verification_status
        confidence = int(min(100, max(20, int(top_candidates[0][1]))))

        # Fetch existing canonical rate in material_rates to determine trend
        # Deterministic tie-breaking on (observed_at DESC, created_at DESC, id DESC) (Task 6)
        existing_canonical = await db_scalar(
            db,
            select(MaterialRate).where(
                MaterialRate.product_id == product.id,
                MaterialRate.city == city,
            ).order_by(
                desc(MaterialRate.observed_at),
                desc(MaterialRate.created_at),
                desc(MaterialRate.id),
            ).limit(1),
        )

        prev_rate_pkr = None
        trend = "neutral"
        if existing_canonical and existing_canonical.rate_pkr:
            prev_rate_pkr = existing_canonical.rate_pkr
            if benchmark_pkr > prev_rate_pkr:
                trend = "up"
            elif benchmark_pkr < prev_rate_pkr:
                trend = "down"
            else:
                trend = "neutral"

        return CanonicalSelectionResult(
            product=product,
            city=city,
            rate_pkr=benchmark_pkr,
            prev_rate_pkr=prev_rate_pkr,
            trend=trend,
            verification_status=ver_status,
            confidence_score=confidence,
            observation_count=len(obs_list),
            eligible_observation_count=len(obs_list),
            contributing_observation_count=len(top_candidates),
            statistical_observation_count=len(stat_obs),
            wholesale_observation_count=len(ws_obs),
            evidence_quality_score=confidence,
            confidence_methodology="multi_factor_evidence_quality_heuristic",
            min_rate_pkr=min_p,
            max_rate_pkr=max_p,
            is_conflicted=is_conflicted,
            statistical_rate_pkr=statistical_rate_pkr,
            wholesale_rate_pkr=wholesale_rate_pkr,
            is_composite=is_composite,
            price_basis=price_basis_label,
        )

    async def synchronize_canonical_rate(
        self,
        db: Any,
        result: CanonicalSelectionResult,
    ) -> MaterialRate:
        """
        Synchronizes a CanonicalSelectionResult into the authoritative material_rates table (app/models/cost.py).
        Preserves 100% backward compatibility for all BOQItem foreign keys.
        """
        existing = await db_scalar(
            db,
            select(MaterialRate).where(
                MaterialRate.product_id == result.product.id,
                MaterialRate.city == result.city,
            ).order_by(
                desc(MaterialRate.observed_at),
                desc(MaterialRate.created_at),
                desc(MaterialRate.id),
            ).limit(1),
        )

        now = datetime.now(timezone.utc)
        change_pct = Decimal("0.00")
        if existing and existing.rate_pkr and existing.rate_pkr > Decimal("0"):
            change_pct = (((result.rate_pkr - existing.rate_pkr) / existing.rate_pkr) * Decimal("100")).quantize(Decimal("0.01"))

        if result.is_composite:
            source_label = (
                f"TameerAI Indicative Composite "
                f"({result.contributing_observation_count} contributing / {result.eligible_observation_count} eligible observations)"
            )
        else:
            source_label = f"TameerAI Canonical Engine ({result.observation_count} observations)"

        if existing:
            existing.rate_pkr = result.rate_pkr
            existing.change_pct = change_pct
            existing.trend = result.trend
            existing.verification_status = result.verification_status
            existing.source_name = source_label
            existing.observed_at = now
            await db_commit(db)
            await db_refresh(db, existing)
            return existing

        new_rate = MaterialRate(
            id=uuid.uuid4(),
            product_id=result.product.id,
            city=result.city,
            category=result.product.category,
            name=result.product.canonical_name,
            spec=result.product.subcategory,
            unit=result.product.standard_unit,
            rate_pkr=result.rate_pkr,
            change_pct=change_pct,
            trend=result.trend,
            verification_status=result.verification_status,
            source_name=source_label,
            observed_at=now,
            created_at=now,
        )
        db.add(new_rate)
        await db_commit(db)
        await db_refresh(db, new_rate)
        return new_rate

    async def refresh_all_snapshots(
        self,
        db: Any,
        cities: Optional[List[str]] = None,
    ) -> List[CanonicalSelectionResult]:
        """
        Computes canonical benchmarks for all active products across all major cities,
        synchronizing the material_rates table.
        """
        target_cities = cities or MAJOR_PAKISTANI_CITIES
        products = list(await db_scalars(db, select(MaterialRateProduct).where(MaterialRateProduct.is_active.is_(True))))

        results: List[CanonicalSelectionResult] = []
        for prod in products:
            for city in target_cities:
                res = await self.compute_canonical_rate_for_product_and_city(db, prod, city)
                if res:
                    await self.synchronize_canonical_rate(db, res)
                    results.append(res)

        logger.info("Refreshed %d canonical market rate snapshots across %d cities.", len(results), len(target_cities))
        return results


# Global singleton engine
canonical_engine = CanonicalMarketRateEngine()
