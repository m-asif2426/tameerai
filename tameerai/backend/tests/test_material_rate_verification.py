"""
TameerAI - Stage 2D Hybrid Multi-Source Verification Engine Tests
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateVerificationEvent,
)
from app.services.material_rates.verification import (
    MultiSourceVerificationEngine,
    verification_engine,
)


@pytest.fixture
def verification_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Seed Product
    prod = MaterialRateProduct(
        id=uuid.uuid4(),
        code="CEMENT_OPC_50KG",
        category="cement",
        canonical_name="Ordinary Portland Cement 50kg Bag",
        standard_unit="bag_50kg",
        volatility_tier="medium",
        is_active=True,
    )
    session.add(prod)

    # Seed Sources
    src1 = MaterialRateSource(
        id=uuid.uuid4(),
        code="PBS_STATISTICAL_SPI",
        name="Pakistan Bureau of Statistics",
        source_type="official",
        reliability_tier="authoritative",
        refresh_cadence="weekly",
        freshness_ttl_days=30,
        is_active=True,
    )
    src2 = MaterialRateSource(
        id=uuid.uuid4(),
        code="ZAREA_B2B_MARKETPLACE",
        name="Zarea Marketplace",
        source_type="dealer_network",
        reliability_tier="verified",
        refresh_cadence="daily",
        freshness_ttl_days=14,
        is_active=True,
    )
    src3 = MaterialRateSource(
        id=uuid.uuid4(),
        code="GHARHUB_PK_PUBLISHER",
        name="GharHub Pakistan",
        source_type="aggregator",
        reliability_tier="indicative",
        refresh_cadence="daily",
        freshness_ttl_days=7,
        is_active=True,
    )
    session.add_all([src1, src2, src3])
    session.commit()

    try:
        yield session, prod, [src1, src2, src3]
    finally:
        session.close()
        engine.dispose()


class TestMultiSourceVerificationEngine:
    @pytest.mark.asyncio
    async def test_single_source_indicative_tier(self, verification_db):
        """Single observation with no peers should be evaluated as indicative."""
        session, prod, sources = verification_db
        src = sources[0]

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
            verification_status="unverified",
            duplicate_fingerprint="fp_single_indicative",
        )
        session.add(obs)
        session.commit()

        event = await verification_engine.verify_observation(session, obs.id)
        assert event.new_status == "indicative"
        assert "single source" in event.reason.lower()

    @pytest.mark.asyncio
    async def test_cross_checked_two_sources_tight_spread(self, verification_db):
        """Two independent sources within 5% spread should achieve cross_checked status."""
        session, prod, sources = verification_db
        now = datetime.now(timezone.utc)

        # Source 1: 1500 PKR
        obs1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_cross_1",
        )
        # Source 2: 1520 PKR (1.3% spread)
        obs2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[1].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1520.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_cross_2",
        )
        session.add_all([obs1, obs2])
        session.commit()

        event = await verification_engine.verify_observation(session, obs1.id)
        assert event.new_status == "cross_checked"
        assert event.metadata_snapshot["metrics"]["spread_pct"] < 5.0

    @pytest.mark.asyncio
    async def test_verified_market_range_three_sources(self, verification_db):
        """Three independent sources within 10% spread should achieve verified_market_range."""
        session, prod, sources = verification_db
        now = datetime.now(timezone.utc)

        obs1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_range_1",
        )
        obs2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[1].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1550.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1550.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_range_2",
        )
        obs3 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[2].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1525.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1525.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_range_3",
        )
        session.add_all([obs1, obs2, obs3])
        session.commit()

        event = await verification_engine.verify_observation(session, obs1.id)
        assert event.new_status == "verified_market_range"

    @pytest.mark.asyncio
    async def test_conflict_detection_spread_exceeds_15_pct(self, verification_db):
        """Divergence > 15% across comparable sources triggers conflicted status."""
        session, prod, sources = verification_db
        now = datetime.now(timezone.utc)

        # Source 1: 1500 PKR
        obs1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_conf_1",
        )
        # Source 2: 1800 PKR (20% divergence from 1500)
        obs2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[1].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1800.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1800.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_conf_2",
        )
        session.add_all([obs1, obs2])
        session.commit()

        event = await verification_engine.verify_observation(session, obs1.id)
        assert event.new_status == "conflicted"
        assert "conflict detected" in event.reason.lower()

    @pytest.mark.asyncio
    async def test_stale_detection_past_30_days(self, verification_db):
        """Observations older than 30 days must be flagged as stale."""
        session, prod, sources = verification_db
        stale_date = datetime.now(timezone.utc) - timedelta(days=35)

        obs = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=stale_date,
            collected_at=stale_date,
            verification_status="unverified",
            duplicate_fingerprint="fp_stale_1",
        )
        session.add(obs)
        session.commit()

        event = await verification_engine.verify_observation(session, obs.id)
        assert event.new_status == "stale"
        assert "exceeding the 30-day" in event.reason

    @pytest.mark.asyncio
    async def test_syndication_independence_filter(self, verification_db):
        """Syndicated sources quoting the same original citation cannot count as independent."""
        session, prod, sources = verification_db
        now = datetime.now(timezone.utc)

        # Source 1: Primary SteelRateToday
        obs1 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_synd_1",
            observation_metadata={"provenance": {"original_source_citation": "SteelRateToday.pk"}},
        )
        # Source 2: Aggregator citing SteelRateToday.pk
        obs2 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[2].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_synd_2",
            observation_metadata={"provenance": {"original_source_citation": "SteelRateToday.pk"}},
        )
        session.add_all([obs1, obs2])
        session.commit()

        event = await verification_engine.verify_observation(session, obs1.id)
        # Because obs2 is syndicated from obs1's root citation, it cannot provide independent corroboration
        assert event.new_status == "indicative"

    @pytest.mark.asyncio
    async def test_comparability_matrix_price_basis_and_grade_incompatibility(self, verification_db):
        """
        Validates Task D comparability matrix:
        1. Retail cement must NOT be compared with Ex-Factory cement.
        2. Grade 40 steel must NOT be compared with Grade 60 steel.
        """
        session, prod, sources = verification_db
        now = datetime.now(timezone.utc)

        # Cement Retail vs Ex-Factory
        obs_retail = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1500.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_basis_ret",
            observation_metadata={"price_basis": "retail"},
        )
        obs_ex_factory = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[1].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("1300.00"),
            observed_unit="bag_50kg",
            normalized_price_pkr=Decimal("1300.00"),
            normalized_unit="bag_50kg",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_basis_ex",
            observation_metadata={"price_basis": "ex_factory"},
        )
        assert not verification_engine.are_comparable(obs_retail, obs_ex_factory, prod)

        # Steel Grade 40 vs Grade 60
        obs_g40 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("240.00"),
            observed_unit="kg",
            normalized_price_pkr=Decimal("240000.00"),
            normalized_unit="metric_ton",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_grade_40",
            observation_metadata={"grade": "Grade 40"},
        )
        obs_g60 = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[1].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("250.00"),
            observed_unit="kg",
            normalized_price_pkr=Decimal("250000.00"),
            normalized_unit="metric_ton",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_grade_60",
            observation_metadata={"grade": "Grade 60"},
        )
        assert not verification_engine.are_comparable(obs_g40, obs_g60, prod)

    @pytest.mark.asyncio
    async def test_comparability_matrix_brand_and_location_incompatibility(self, verification_db):
        """
        Validates Phase 02H Task F:
        1. Different declared brands (Mughal vs Amreli) must NOT be cross-compared as identical.
        2. Different market cities (Lahore vs Karachi) must NOT be cross-compared.
        """
        session, prod, sources = verification_db
        now = datetime.now(timezone.utc)

        # Brand Incompatibility (Mughal vs Amreli)
        obs_mughal = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("255000.00"),
            observed_unit="metric_ton",
            normalized_price_pkr=Decimal("255000.00"),
            normalized_unit="metric_ton",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_br_mughal",
            observation_metadata={"brand": "Mughal Steel"},
        )
        obs_amreli = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[1].id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("258000.00"),
            observed_unit="metric_ton",
            normalized_price_pkr=Decimal("258000.00"),
            normalized_unit="metric_ton",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_br_amreli",
            observation_metadata={"brand": "Amreli Steels"},
        )
        assert not verification_engine.are_comparable(obs_mughal, obs_amreli, prod)

        # Location Incompatibility (Lahore vs Karachi)
        obs_karachi = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=sources[0].id,
            product_id=prod.id,
            city="Karachi",
            observed_price_pkr=Decimal("255000.00"),
            observed_unit="metric_ton",
            normalized_price_pkr=Decimal("255000.00"),
            normalized_unit="metric_ton",
            published_at=now,
            collected_at=now,
            verification_status="unverified",
            duplicate_fingerprint="fp_loc_khi",
            observation_metadata={"brand": "Mughal Steel"},
        )
        assert not verification_engine.are_comparable(obs_mughal, obs_karachi, prod)
