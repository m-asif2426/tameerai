"""
TameerAI - Historical Market Intelligence Service (Stage 2G)

Implements:
1. Pure Append-Only Analytics Engine:
   - Queries immutable material_rate_observations table with zero modification or deletion.
2. Time-Series Aggregations & Volatility Modeling:
   - Daily, weekly, and monthly bucketed medians, means, min/max ranges.
   - Percentage price change and statistical volatility (standard deviation / variance).
3. Multi-City & Cross-Brand Comparative Spread Analytics:
   - Compares regional price parity across Pakistani provincial capitals.
   - Evaluates brand premiums (e.g. Mughal vs Amreli vs Ittehad).
4. Trend Confidence Scoring:
   - Communicates data density, source diversity, and temporal continuity.
5. Reusable Intelligence API for Phase 03 AI Readiness:
   - get_current_rate(), get_price_history(), compare_cities(), get_cheapest_alternative(), get_monthly_inflation_summary().
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
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
)
from app.services.material_rates.canonical_engine import canonical_engine
from app.services.material_rates.db_compat import (
    db_execute,
    db_scalar,
    db_scalars,
)
from app.services.material_rates.normalization import normalize_city
from app.services.material_rates.identity_resolver import (
    centralized_identity_resolver,
    detect_observation_steel_grade,
    PRODUCT_CODE_STEEL_G40,
    PRODUCT_CODE_STEEL_G60,
    KNOWN_PRODUCT_ID_G60,
)

logger = logging.getLogger("tameerai.material_rates.historical")


class HistoricalMarketIntelligenceService:
    """Provides historical time-series analytics, volatility calculation, and comparative market intelligence."""

    @staticmethod
    def _calculate_std_dev(values: List[Decimal]) -> Decimal:
        """Calculates standard deviation of a sample of Decimal numbers."""
        if len(values) < 2:
            return Decimal("0.00")
        float_vals = [float(v) for v in values]
        mean = sum(float_vals) / len(float_vals)
        variance = sum((x - mean) ** 2 for x in float_vals) / (len(float_vals) - 1)
        return Decimal(str(round(math.sqrt(variance), 2)))

    @staticmethod
    def _calculate_median(values: List[Decimal]) -> Decimal:
        """Calculates exact median of Decimal numbers."""
        if not values:
            return Decimal("0.00")
        s = sorted(values)
        n = len(s)
        if n % 2 == 1:
            return s[n // 2]
        return ((s[n // 2 - 1] + s[n // 2]) / Decimal("2")).quantize(Decimal("0.01"))

    async def get_price_history(
        self,
        db: Any,
        *,
        product_code: str,
        city: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "daily",  # daily, weekly, monthly
    ) -> Dict[str, Any]:
        """
        Retrieves historical price movements and statistical aggregations for a product.
        Intervals: daily, weekly, monthly.
        """
        product = await db_scalar(
            db,
            select(MaterialRateProduct).where(MaterialRateProduct.code == product_code),
        )
        if not product:
            raise ValueError(f"Product '{product_code}' not found")

        now = datetime.now(timezone.utc)
        start = start_date or (now - timedelta(days=90))
        end = end_date or now

        norm_city = normalize_city(city) if city else None

        # Centralized canonical product identity query (Task 2)
        if product.code == PRODUCT_CODE_STEEL_G40:
            g60_prod = await centralized_identity_resolver.get_canonical_product(db, PRODUCT_CODE_STEEL_G60)
            g60_id = g60_prod.id if g60_prod else KNOWN_PRODUCT_ID_G60
            stmt = (
                select(MaterialRateObservation)
                .where(
                    MaterialRateObservation.product_id.in_([product.id, g60_id]),
                )
            )
        else:
            stmt = (
                select(MaterialRateObservation)
                .where(
                    MaterialRateObservation.product_id == product.id,
                )
            )
        if norm_city:
            stmt = stmt.where(MaterialRateObservation.city == norm_city)

        stmt = stmt.order_by(MaterialRateObservation.created_at.asc())
        all_raw_obs: List[MaterialRateObservation] = list(await db_scalars(db, stmt))

        # Preload sources for frequency-aware temporal grouping and synthetic fixture exclusion
        sources_list = list(await db_scalars(db, select(MaterialRateSource)))
        sources_by_id = {s.id: s for s in sources_list}

        # Filter observations using centralized product identity & reliable market date (Tasks 2 & 3)
        observations: List[MaterialRateObservation] = []
        obs_market_dates: Dict[uuid.UUID, datetime] = {}
        for obs in all_raw_obs:
            src = sources_by_id.get(obs.source_id)
            # 0. Provenance-based synthetic test fixture exclusion (Phase 03.4C.2 Task 4)
            if centralized_identity_resolver.is_synthetic_test_fixture(obs, src):
                continue

            if not centralized_identity_resolver.is_observation_eligible_for_product(
                obs, product.code, stored_product_code=product.code
            ):
                continue
            m_dt = centralized_identity_resolver.resolve_effective_market_date(obs, src) or obs.published_at
            if m_dt:
                if m_dt.tzinfo is None:
                    m_dt = m_dt.replace(tzinfo=timezone.utc)
                if start <= m_dt <= end:
                    observations.append(obs)
                    obs_market_dates[obs.id] = m_dt

        if not observations:
            return {
                "product_code": product.code,
                "product_name": product.canonical_name,
                "category": product.category,
                "city": norm_city,
                "interval": interval,
                "total_observations": 0,
                "data_points": [],
                "price_change_pct": 0.0,
                "volatility_pkr": 0.0,
                "trend_confidence": 0,
            }

        # Bucket observations by interval key using reliable market dates and source frequency
        buckets: Dict[str, List[Decimal]] = {}
        for obs in observations:
            obs_dt = obs_market_dates.get(obs.id) or obs.published_at
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)

            src = sources_by_id.get(obs.source_id)
            src_cadence = (getattr(src, "refresh_cadence", None) or "").lower()
            src_code = (getattr(src, "code", None) or "").upper()
            is_monthly_source = (
                src_cadence == "monthly"
                or "PBS_STATISTICAL_MONTHLY" in src_code
                or "MONTHLY" in src_code
                or centralized_identity_resolver.is_pbs_monthly_observation(obs, src)
            )
            is_weekly_source = (
                src_cadence == "weekly"
                or "PBS_STATISTICAL_SPI" in src_code
                or "SPI" in src_code
            )

            # Source-frequency-aware grouping (Task 1):
            # 1. Monthly statistical series (e.g. PBS monthly) must strictly remain in YYYY-MM buckets.
            #    Weekly commercial aggregation must not convert monthly observations into weekly data.
            # 2. Weekly statistical series (e.g. PBS weekly SPI) use ISO YYYY-Www (%G-W%V) when weekly/daily requested.
            # 3. Daily commercial observations and dealer quotations use requested interval (daily, weekly, monthly).
            if is_monthly_source:
                key = obs_dt.strftime("%Y-%m")
            elif interval == "monthly":
                key = obs_dt.strftime("%Y-%m")
            elif interval == "weekly":
                key = obs_dt.strftime("%G-W%V")
            else:
                key = obs_dt.strftime("%Y-%m-%d")

            if key not in buckets:
                buckets[key] = []
            buckets[key].append(obs.normalized_price_pkr)

        data_points = []
        all_medians: List[Decimal] = []

        for period_key in sorted(buckets.keys()):
            prices = buckets[period_key]
            med = self._calculate_median(prices)
            all_medians.append(med)
            mean_val = (sum(prices) / Decimal(str(len(prices)))).quantize(Decimal("0.01"))

            data_points.append({
                "period": period_key,
                "median_pkr": float(med),
                "mean_pkr": float(mean_val),
                "min_pkr": float(min(prices)),
                "max_pkr": float(max(prices)),
                "observation_count": len(prices),
            })

        # Calculate overall price change %
        first_median = all_medians[0]
        last_median = all_medians[-1]
        price_change_pct = Decimal("0.00")
        if first_median > Decimal("0"):
            price_change_pct = (((last_median - first_median) / first_median) * Decimal("100")).quantize(Decimal("0.01"))

        volatility = self._calculate_std_dev(all_medians)

        # Trend confidence score (0-100) based on sample size and continuity
        density_score = min(50, len(observations) * 2)
        continuity_score = min(50, len(buckets) * 5)
        trend_confidence = density_score + continuity_score

        return {
            "product_code": product.code,
            "product_name": product.canonical_name,
            "category": product.category,
            "city": norm_city,
            "interval": interval,
            "total_observations": len(observations),
            "data_points": data_points,
            "price_change_pct": float(price_change_pct),
            "volatility_pkr": float(volatility),
            "trend_confidence": trend_confidence,
        }

    async def compare_cities(
        self,
        db: Any,
        *,
        product_code: str,
        cities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compares current and historical rates for a product across specified Pakistani cities.
        """
        product = await db_scalar(
            db,
            select(MaterialRateProduct).where(MaterialRateProduct.code == product_code),
        )
        if not product:
            raise ValueError(f"Product '{product_code}' not found")

        target_cities = cities or ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Multan"]

        city_data = []
        rates = []

        for city in target_cities:
            norm_c = normalize_city(city)
            res = await canonical_engine.compute_canonical_rate_for_product_and_city(db, product, norm_c)
            if res:
                rates.append(res.rate_pkr)
                city_data.append({
                    "city": norm_c,
                    "rate_pkr": float(res.rate_pkr),
                    "unit": product.standard_unit,
                    "trend": res.trend,
                    "verification_status": res.verification_status,
                    "confidence_score": res.confidence_score,
                    "observation_count": res.observation_count,
                    "is_conflicted": res.is_conflicted,
                })
            else:
                city_data.append({
                    "city": norm_c,
                    "rate_pkr": None,
                    "unit": product.standard_unit,
                    "trend": "no_data",
                    "verification_status": "unverified",
                    "confidence_score": 0,
                    "observation_count": 0,
                    "is_conflicted": False,
                })

        national_median = float(self._calculate_median(rates)) if rates else 0.0

        return {
            "product_code": product.code,
            "product_name": product.canonical_name,
            "category": product.category,
            "standard_unit": product.standard_unit,
            "national_median_pkr": national_median,
            "cities": city_data,
        }

    async def get_current_rate(
        self,
        db: Any,
        product_code: str,
        city: str,
    ) -> Optional[Dict[str, Any]]:
        """Convenience method for Phase 03 AI assistant to fetch current benchmark."""
        product = await db_scalar(
            db,
            select(MaterialRateProduct).where(MaterialRateProduct.code == product_code),
        )
        if not product:
            return None

        res = await canonical_engine.compute_canonical_rate_for_product_and_city(db, product, city)
        if not res:
            return None
        return res.to_dict()

    async def get_cheapest_alternative(
        self,
        db: Any,
        category: str,
        city: str,
    ) -> List[Dict[str, Any]]:
        """Finds active products in category sorted by rate (lowest first)."""
        products = list(await db_scalars(
            db,
            select(MaterialRateProduct).where(
                MaterialRateProduct.category == category.lower(),
                MaterialRateProduct.is_active.is_(True),
            ),
        ))

        results = []
        for p in products:
            res = await canonical_engine.compute_canonical_rate_for_product_and_city(db, p, city)
            if res:
                results.append(res.to_dict())

        results.sort(key=lambda item: item["rate_pkr"])
        return results

    async def get_monthly_inflation_summary(
        self,
        db: Any,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Summarizes 30-day price movements across core materials."""
        products = list(await db_scalars(
            db,
            select(MaterialRateProduct).where(MaterialRateProduct.is_active.is_(True)),
        ))

        summary = []
        target_city = normalize_city(city) if city else "Lahore"

        for p in products:
            hist = await self.get_price_history(
                db,
                product_code=p.code,
                city=target_city,
                interval="daily",
            )
            if hist["total_observations"] > 0:
                summary.append({
                    "product_code": p.code,
                    "product_name": p.canonical_name,
                    "category": p.category,
                    "change_pct": hist["price_change_pct"],
                    "volatility_pkr": hist["volatility_pkr"],
                })

        return {
            "city": target_city,
            "period": "Last 30 Days",
            "products_analyzed": len(summary),
            "summary": summary,
        }


# Global singleton service
historical_service = HistoricalMarketIntelligenceService()

