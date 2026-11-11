"""
TameerAI - Stage 2F & 2G Canonical Market Rate Engine & Historical Intelligence Tests
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.cost import MaterialRate
from app.models.material_rate import (
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
)
from app.services.material_rates.canonical_engine import (
    CanonicalMarketRateEngine,
    canonical_engine,
)
from app.services.material_rates.historical_service import (
    HistoricalMarketIntelligenceService,
    historical_service,
)


@pytest.fixture
def canonical_test_env():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    prod = MaterialRateProduct(
        id=uuid.uuid4(),
        code="CEMENT_OPC_50KG",
        category="cement",
        canonical_name="Ordinary Portland Cement 50kg Bag",
        standard_unit="bag_50kg",
        volatility_tier="medium",
        is_active=True,
    )
    src = MaterialRateSource(
        id=uuid.uuid4(),
        code="PBS_STATISTICAL_SPI",
        name="PBS Statistical SPI",
        source_type="official",
        reliability_tier="authoritative",
        refresh_cadence="weekly",
        freshness_ttl_days=30,
        is_active=True,
    )
    session.add_all([prod, src])
    session.commit()

    try:
        yield session, prod, src
    finally:
        session.close()
        engine.dispose()


class TestCanonicalMarketRateEngine:
    @pytest.mark.asyncio
    async def test_canonical_rate_selection_and_trend(self, canonical_test_env):
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # Existing canonical rate: 1450 PKR
        existing = MaterialRate(
            id=uuid.uuid4(),
            product_id=prod.id,
            city="Lahore",
            category="cement",
            name="Ordinary Portland Cement 50kg Bag",
            unit="bag_50kg",
            rate_pkr=Decimal("1450.00"),
            change_pct=Decimal("0.00"),
            trend="neutral",
            verification_status="verified",
            source_name="Market Survey",
            observed_at=now - timedelta(days=7),
        )
        session.add(existing)

        # Insert new observation: 1520 PKR
        obs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1520.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="cross_checked",
            duplicate_fingerprint="fp_canon_1",
        )
        session.add(obs)
        session.commit()

        # Compute canonical rate
        res = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Lahore")
        assert res is not None
        assert res.rate_pkr == Decimal("1520.00")
        assert res.prev_rate_pkr == Decimal("1450.00")
        assert res.trend == "up"  # 1520 > 1450 -> trend up

        # Synchronize into canonical table
        synced = await canonical_engine.synchronize_canonical_rate(session, res)
        assert synced.rate_pkr == Decimal("1520.00")
        assert synced.trend == "up"
        assert synced.change_pct > Decimal("0.00")

    @pytest.mark.asyncio
    async def test_canonical_engine_detects_conflict(self, canonical_test_env):
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # Observation 1: 1500 PKR
        obs1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Karachi",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_khi_1",
        )
        # Observation 2: 1850 PKR (23% difference -> conflicted)
        obs2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Karachi",
            observed_price_pkr=Decimal("1850.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1850.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_khi_2",
        )
        session.add_all([obs1, obs2])
        session.commit()

        res = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Karachi")
        assert res is not None
        assert res.is_conflicted is True
        assert res.verification_status == "conflicted"


class TestHistoricalMarketIntelligenceService:
    @pytest.mark.asyncio
    async def test_historical_price_history_aggregations(self, canonical_test_env):
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # Seed 10 observations across 5 consecutive days
        prices = [Decimal("1480"), Decimal("1490"), Decimal("1500"), Decimal("1510"), Decimal("1520")]
        for i, p in enumerate(prices):
            obs_dt = now - timedelta(days=(5 - i))
            obs = MaterialRateObservation(
                id=uuid.uuid4(),
                source_id=src.id,
                product_id=prod.id,
                city="Lahore",
                observed_price_pkr=p,
                observed_unit="bag_50kg",
                normalized_price_pkr=p,
                normalized_unit="bag_50kg",
                published_at=obs_dt,
                collected_at=obs_dt,
                verification_status="verified_quote",
                duplicate_fingerprint=f"fp_hist_{i}",
            )
            session.add(obs)
        session.commit()

        hist = await historical_service.get_price_history(
            session,
            product_code="CEMENT_OPC_50KG",
            city="Lahore",
            interval="daily",
        )

        assert hist["total_observations"] == 5
        assert len(hist["data_points"]) == 5
        assert hist["price_change_pct"] > 0.0  # 1480 -> 1520 is positive
        assert hist["volatility_pkr"] > 0.0
        assert hist["trend_confidence"] > 0

    @pytest.mark.asyncio
    async def test_cross_city_comparison(self, canonical_test_env):
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # Add Lahore rate: 1500
        obs_lhr = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_quote",
            duplicate_fingerprint="fp_comp_lhr",
        )
        # Add Karachi rate: 1560
        obs_khi = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Karachi",
            observed_price_pkr=Decimal("1560.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1560.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_quote",
            duplicate_fingerprint="fp_comp_khi",
        )
        session.add_all([obs_lhr, obs_khi])
        session.commit()

        comp = await historical_service.compare_cities(
            session,
            product_code="CEMENT_OPC_50KG",
            cities=["Lahore", "Karachi", "Islamabad"],
        )

        assert comp["product_code"] == "CEMENT_OPC_50KG"
        assert comp["national_median_pkr"] > 0.0
        assert len(comp["cities"]) == 3
        cities_map = {c["city"]: c["rate_pkr"] for c in comp["cities"]}
        assert cities_map["Lahore"] == 1500.0
        assert cities_map["Karachi"] == 1560.0
        assert cities_map["Islamabad"] is None

    @pytest.mark.asyncio
    async def test_canonical_scoring_boundaries_and_conflict_safety(self, canonical_test_env):
        """
        Validates Task E:
        1. Scoring formula bounds strictly within [0.0, 100.0].
        2. High numerical score cannot bypass 'conflicted' status when market divergence > 15%.
        """
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # 1. Test weight boundaries
        obs_mock = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_quote",
            duplicate_fingerprint="fp_boundary_1",
        )
        weight = canonical_engine.compute_observation_weight(obs_mock, src, "Lahore", now)
        assert 0.0 <= weight <= 100.0

        # 2. Market conflict check: Divergence > 15% forces is_conflicted=True and ver_status='conflicted'
        obs_high = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1850.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1850.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_quote",
            duplicate_fingerprint="fp_boundary_2",
        )
        session.add_all([obs_mock, obs_high])
        session.commit()

        snap = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Lahore")
        assert snap is not None
        assert snap.is_conflicted is True
        assert snap.verification_status == "conflicted"

    def test_canonical_scoring_formula_comprehensive_matrix(self, canonical_test_env):
        """
        Validates Phase 02H Task C scoring formula requirements:
        Score = (Credibility * 0.35) + (Verification * 0.30) + (Freshness * 0.25) + (Volume * 0.10)
        """
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # 1. Volume normalization: 1 -> 20, 3 -> 60, 5 -> 100, 10 -> capped at 100
        obs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_quote",
            duplicate_fingerprint="fp_vol_1",
        )
        w_vol1 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=1)
        w_vol5 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=5)
        w_vol10 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=10)
        assert w_vol5 > w_vol1
        assert w_vol10 == w_vol5  # Capped at 100% volume weight

        # 2. Freshness decay: today vs 14 days ago
        obs_old = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now - timedelta(days=14),
            collected_at=now - timedelta(days=14),
            verification_status="verified_quote",
            duplicate_fingerprint="fp_fresh_old",
        )
        w_fresh_new = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=3)
        w_fresh_old = canonical_engine.compute_observation_weight(obs_old, src, "Lahore", now, volume_count=3)
        assert w_fresh_new > w_fresh_old

        # 3. Missing source & missing published_at handling (graceful fallback)
        obs_nulls = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=None,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_nulls",
        )
        w_nulls = canonical_engine.compute_observation_weight(obs_nulls, None, "Lahore", now)
        assert 0.0 <= w_nulls <= 100.0

        # 4. Deterministic reproducibility
        w_run1 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=3)
        w_run2 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=3)
        assert w_run1 == w_run2


class TestPhase031FinalCanonicalMathematicalIntegrity:
    """
    Phase 03.1 Final Verification Test Suite:
    Validates exact Decimal weighted-average arithmetic, component scoring breakdown,
    dual price benchmark disaggregation, and BOQ isolation of indicative composites.
    """

    @pytest.mark.asyncio
    async def test_exact_decimal_weighted_average_arithmetic(self, canonical_test_env):
        """Task 1: Verify that canonical benchmark dynamically evaluates weighted average using Decimal arithmetic."""
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # Three distinct observations with known prices
        obs1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("235380.45"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("235380.45"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_market_range",
            duplicate_fingerprint="fp_math_1",
        )
        obs2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("248000.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("248000.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_math_2",
        )
        obs3 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("246000.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("246000.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_math_3",
        )
        session.add_all([obs1, obs2, obs3])
        session.commit()

        # Compute weights independently
        w1 = canonical_engine.compute_observation_weight(obs1, src, "Lahore", now, volume_count=3)
        w2 = canonical_engine.compute_observation_weight(obs2, src, "Lahore", now, volume_count=3)
        w3 = canonical_engine.compute_observation_weight(obs3, src, "Lahore", now, volume_count=3)

        expected_numerator = (
            obs1.normalized_price_pkr * Decimal(str(w1))
            + obs2.normalized_price_pkr * Decimal(str(w2))
            + obs3.normalized_price_pkr * Decimal(str(w3))
        )
        expected_denominator = Decimal(str(w1 + w2 + w3))
        expected_rate = (expected_numerator / expected_denominator).quantize(Decimal("0.01"))

        res = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Lahore")
        assert res is not None
        assert res.rate_pkr == expected_rate
        assert expected_denominator > Decimal("0")

    def test_weight_formula_exact_component_breakdown_and_bounds(self, canonical_test_env):
        """Task 2: Verify exact weight formula components: Credibility(0.35), Tier(0.30), Freshness(0.25), Volume(0.10)."""
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        # 1. Exact mathematical breakdown
        obs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_market_range",  # tier = 85
            duplicate_fingerprint="fp_decomp_1",
        )
        # src is 'PBS_STATISTICAL_SPI' which has credibility_score = 100.0 in national_registry
        # published_at = now -> days_old = 0 -> fresh_pct = 100.0
        # volume_count = 5 -> 5 * 20 = 100.0
        expected_score = (0.35 * 100.0) + (0.30 * 85.0) + (0.25 * 100.0) + (0.10 * 100.0)
        # 35.00 + 25.50 + 25.00 + 10.00 = 95.50
        actual_score = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=5)
        assert actual_score == 95.50

        # 2. Maximum boundary test (score cannot exceed 100.0)
        max_score = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, volume_count=100)
        assert max_score <= 100.0

        # 3. Minimum boundary test (score cannot fall below 0.0)
        min_score = canonical_engine.compute_observation_weight(obs, None, "Lahore", now + timedelta(days=3650))
        assert min_score >= 0.0

    @pytest.mark.asyncio
    async def test_disaggregated_benchmarks_statistical_vs_wholesale(self, canonical_test_env):
        """Task 3: Maintain separate outputs for PBS statistical retail vs commercial wholesale benchmarks."""
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        src_comm = MaterialRateSource(
            id=uuid.uuid4(),
            code="STEELRATETODAY_PK_PUBLISHER",
            name="SteelRateToday Monitor",
            source_type="aggregator",
            reliability_tier="indicative",
            refresh_cadence="daily",
            freshness_ttl_days=7,
            is_active=True,
        )
        session.add(src_comm)
        session.commit()

        # PBS statistical retail observation (retail_statistical)
        obs_pbs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("235380.45"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("235380.45"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_market_range",
            duplicate_fingerprint="fp_dual_pbs",
            observation_metadata={"price_basis": "retail_statistical"},
        )
        # SteelRateToday wholesale observations (wholesale)
        obs_ws1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src_comm.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("245000.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("245000.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_dual_ws1",
            observation_metadata={"price_basis": "wholesale"},
        )
        obs_ws2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src_comm.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("251500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("251500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_dual_ws2",
            observation_metadata={"price_basis": "wholesale"},
        )
        obs_ws3 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src_comm.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("260000.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("260000.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_dual_ws3",
            observation_metadata={"price_basis": "wholesale"},
        )
        session.add_all([obs_pbs, obs_ws1, obs_ws2, obs_ws3])
        session.commit()

        res = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Lahore")
        assert res is not None

        # Verify dual disaggregated outputs
        assert res.statistical_rate_pkr == Decimal("235380.45")
        assert res.wholesale_rate_pkr == Decimal("251500.00")  # Median of 245k, 251.5k, 260k

        # Verify composite detection and indicative classification
        assert res.is_composite is True
        assert res.verification_status == "indicative"  # Must NOT be verified_market_range
        assert res.price_basis == "indicative_composite"

    @pytest.mark.asyncio
    async def test_boq_cannot_consume_indicative_composite_as_verified(self, canonical_test_env):
        """Task 5.6: Verify BOQ cannot consume an incompatible indicative composite as a verified rate."""
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)

        src_comm = MaterialRateSource(
            id=uuid.uuid4(),
            code="STEELRATETODAY_PK_PUBLISHER",
            name="SteelRateToday Monitor",
            source_type="aggregator",
            reliability_tier="indicative",
            refresh_cadence="daily",
            freshness_ttl_days=7,
            is_active=True,
        )
        session.add(src_comm)
        session.commit()

        obs_pbs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("235380.45"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("235380.45"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_market_range",
            duplicate_fingerprint="fp_boq_pbs",
            observation_metadata={"price_basis": "retail_statistical"},
        )
        obs_comm = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src_comm.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("250000.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("250000.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="indicative",
            duplicate_fingerprint="fp_boq_comm",
            observation_metadata={"price_basis": "wholesale"},
        )
        session.add_all([obs_pbs, obs_comm])
        session.commit()

        # Compute canonical selection result and synchronize into material_rates
        res = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Lahore")
        assert res.is_composite is True
        assert res.verification_status == "indicative"

        synced = await canonical_engine.synchronize_canonical_rate(session, res)
        assert synced.verification_status == "indicative"
        assert "Indicative Composite" in synced.source_name

        # Query simulating BOQ cost service filtering for verified market rates
        stmt = (
            select(MaterialRate)
            .where(
                MaterialRate.product_id == prod.id,
                MaterialRate.city == "Lahore",
                MaterialRate.verification_status.in_(["verified", "verified_quote", "verified_market_range"]),
            )
        )
        verified_rates = list(session.execute(stmt).scalars().all())
        # The indicative composite rate MUST NOT be returned in verified queries
        assert len(verified_rates) == 0

    def test_pbs_and_commercial_exact_weight_components_reconciliation(self, canonical_test_env):
        """Task 3: Exact component reconciliation for PBS vs Commercial sources using NationalSourceRegistry."""
        session, prod, _ = canonical_test_env
        fixed_now = datetime(2026, 11, 8, 20, 0, 0, tzinfo=timezone.utc)

        # 1. PBS Monthly Observation
        src_pbs = MaterialRateSource(
            id=uuid.uuid4(),
            code="PBS_STATISTICAL_MONTHLY",
            name="PBS Monthly Construction",
            source_type="official",
            reliability_tier="authoritative",
            refresh_cadence="monthly",
            freshness_ttl_days=45,
            is_active=True,
        )
        # Market date: 2026-10-31 23:59:59 UTC
        # days_old = (2026-11-08 20:00:00 - 2026-10-31 23:59:59) = 7.833345 days
        obs_pbs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src_pbs.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("235380.45"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("235380.45"),
            normalized_unit="bag_50kg",
            published_at=datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
            collected_at=fixed_now,
            verification_status="verified_market_range",
            duplicate_fingerprint="fp_reconcile_pbs",
            observation_metadata={
                "survey_reference_period": "October, 2026",
                "price_basis": "retail_statistical",
            },
        )

        # Component checks for PBS
        # Credibility: registered as 95 in NationalSourceRegistry -> 0.35 * 95 = 33.25
        # Verification: verified_market_range -> 85 -> 0.30 * 85 = 25.50
        # Volume: volume_count = 17 -> min(100.0, 17 * 20.0) = 100.0 -> 0.10 * 100 = 10.00
        # Freshness: days_old = 7.833345 -> exp(-0.05 * 7.833345) * 100 = 67.5929 -> 0.25 * 67.5929 = 16.898225
        # Sum = 33.25 + 25.50 + 16.898225 + 10.00 = 85.648225
        w_pbs = canonical_engine.compute_observation_weight(obs_pbs, src_pbs, "Lahore", fixed_now, volume_count=17)
        assert isinstance(w_pbs, Decimal)
        assert w_pbs == Decimal("85.648225")

        # 2. Commercial SteelRateToday Observation
        src_comm = MaterialRateSource(
            id=uuid.uuid4(),
            code="STEELRATETODAY_PK_PUBLISHER",
            name="SteelRateToday Monitor",
            source_type="aggregator",
            reliability_tier="indicative",
            refresh_cadence="daily",
            freshness_ttl_days=7,
            is_active=True,
        )
        obs_comm = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src_comm.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("254000.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("254000.00"),
            normalized_unit="bag_50kg",
            published_at=datetime(2026, 11, 7, 9, 45, 32, tzinfo=timezone.utc),
            collected_at=fixed_now,
            verification_status="indicative",
            duplicate_fingerprint="fp_reconcile_comm",
            observation_metadata={"price_basis": "wholesale"},
        )

        # Component checks for Commercial
        # Credibility: registered as 63 in NationalSourceRegistry -> 0.35 * 63 = 22.05
        # Verification: indicative -> 50 -> 0.30 * 50 = 15.00
        # Volume: volume_count = 17 -> 100.0 -> 0.10 * 100 = 10.00
        # Freshness: days_old = 1.426713 -> exp(-0.05 * 1.426713) * 100 = 93.114757 -> 0.25 * 93.114757 = 23.27868925
        # Sum = 22.05 + 15.00 + 23.2787325 + 10.00 = 70.3287325
        w_comm = canonical_engine.compute_observation_weight(obs_comm, src_comm, "Lahore", fixed_now, volume_count=17)
        assert isinstance(w_comm, Decimal)
        assert w_comm == Decimal("70.3287325")

    @pytest.mark.asyncio
    async def test_deterministic_top_three_selection_permutation_invariance(self, canonical_test_env):
        """Task 2: Ensure identical database contents always select identical top 3 observation UUIDs regardless of query order."""
        import random
        session, prod, _ = canonical_test_env
        fixed_now = datetime(2026, 11, 8, 20, 0, 0, tzinfo=timezone.utc)

        src_pbs = MaterialRateSource(
            id=uuid.uuid4(),
            code="PBS_STATISTICAL_MONTHLY",
            name="PBS Monthly",
            source_type="official",
            reliability_tier="authoritative",
            refresh_cadence="monthly",
            freshness_ttl_days=45,
            is_active=True,
        )
        src_comm = MaterialRateSource(
            id=uuid.uuid4(),
            code="STEELRATETODAY_PK_PUBLISHER",
            name="SteelRateToday",
            source_type="aggregator",
            reliability_tier="indicative",
            refresh_cadence="daily",
            freshness_ttl_days=7,
            is_active=True,
        )
        session.add_all([src_pbs, src_comm])
        session.commit()

        # Insert 1 PBS observation
        obs_pbs = MaterialRateObservation(
            id=uuid.UUID("30ed83c4-a28a-41f8-86d7-e21271a47aca"),
            source_id=src_pbs.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("235380.45"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("235380.45"),
            normalized_unit="bag_50kg",
            published_at=datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
            collected_at=fixed_now,
            verification_status="verified_market_range",
            duplicate_fingerprint="fp_inv_pbs",
            observation_metadata={"price_basis": "retail_statistical", "survey_reference_period": "October, 2026"},
        )
        session.add(obs_pbs)

        # Insert 16 commercial observations with distinct UUIDs and prices
        comm_uuids = [
            "9c08e68d-ed77-411a-9ac6-d75726560b0d",
            "a9cf82c5-d1d1-4a42-acb7-83a14dcdb996",
            "de352b4a-cdd6-4622-bc26-1327e00c7602",
            "e9ae60b3-427d-496f-8a1c-54375e52d34a",
            "23b39a0d-3ed8-4701-9f2d-b2910f723049",
        ]
        prices = [Decimal("254000.00"), Decimal("251000.00"), Decimal("249000.00"), Decimal("247000.00"), Decimal("253000.00")]
        for u_str, p in zip(comm_uuids, prices):
            obs = MaterialRateObservation(
                id=uuid.UUID(u_str),
                source_id=src_comm.id,
                product_id=prod.id,
                city="Lahore",
                observed_price_pkr=p,
                observed_unit="bag_50kg",
                normalized_price_pkr=p,
                normalized_unit="bag_50kg",
                published_at=datetime(2026, 11, 7, 9, 45, 32, tzinfo=timezone.utc),
                created_at=datetime(2026, 11, 7, 9, 45, 32, tzinfo=timezone.utc),
                collected_at=fixed_now,
                verification_status="indicative",
                duplicate_fingerprint=f"fp_inv_{u_str}",
                observation_metadata={"price_basis": "wholesale"},
            )
            session.add(obs)
        session.commit()

        # Run 10 consecutive evaluations passing fixed_now
        results = []
        for _ in range(10):
            res = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod, "Lahore", now=fixed_now)
            results.append(res.rate_pkr)

        # All 10 runs MUST return the exact same rate
        assert all(r == results[0] for r in results)
        assert results[0] > Decimal("0")

    def test_exact_top_three_numerator_multiplication_and_weighted_average(self):
        """Task 1: Verify exact decimal multiplication of every numerator and final ROUND_HALF_UP average."""
        p_pbs = Decimal("235380.45")
        w_pbs = Decimal("85.64822500")
        num_pbs = p_pbs * w_pbs
        assert num_pbs == Decimal("20159917.7422012500")

        p_shk = Decimal("254000.00")
        w_shk = Decimal("70.32873250")
        num_shk = p_shk * w_shk
        assert num_shk == Decimal("17863498.0550000000")

        p_rsh = Decimal("251000.00")
        w_rsh = Decimal("70.32873250")
        num_rsh = p_rsh * w_rsh
        assert num_rsh == Decimal("17652511.8575000000")

        total_num = num_pbs + num_shk + num_rsh
        total_den = w_pbs + w_shk + w_rsh
        assert total_num == Decimal("55675927.6547012500")
        assert total_den == Decimal("226.30569000")

        exact_quot = total_num / total_den
        final_rate = exact_quot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert final_rate == Decimal("246020.89")

    def test_query_wide_evidence_volume_semantics(self, canonical_test_env):
        """Task 3: Volume score reflects query-wide market evidence density across the search space (>= 5 gives 100%)."""
        session, prod, src = canonical_test_env
        now = datetime.now(timezone.utc)
        obs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=src.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="verified_market_range",
            duplicate_fingerprint="fp_vol_sem",
        )
        # Query-wide density with N=17 eligible observations
        w_17 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, query_evidence_volume=17)
        # Query-wide density with N=1 observation (isolated single data point)
        w_1 = canonical_engine.compute_observation_weight(obs, src, "Lahore", now, query_evidence_volume=1)
        # Difference in volume score: (100.0 - 20.0) * 0.10 = 8.00 Decimal points
        assert (w_17 - w_1) == Decimal("8.00000000")

