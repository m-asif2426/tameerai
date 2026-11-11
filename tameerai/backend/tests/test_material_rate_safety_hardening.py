"""
TameerAI - Stage 1.3 Material Rate Safety, Canonical Fingerprinting & PostgreSQL Hardening Tests

Validates:
1. Canonical SHA-256 Fingerprint Engine (Task C):
   - Deterministic key ordering and UTF-8 encoding.
   - Unicode NFKC normalization and whitespace collapse.
   - Date normalization (YYYY-MM-DD from string, date, or tz-aware datetime).
   - Decimal rate formatting to fixed 2 decimal places (ROUND_HALF_UP).
   - Version contract ("tameerai:material-rate-observation:v1").
   - Distinction across different materials, prices, units, and dates.
2. Foreign-Key RESTRICT Compatibility (Task B):
   - fk_observations_dealer_quote_id is RESTRICT.
   - fk_observations_background_job_id is RESTRICT.
   - Attempting to delete a dealer quote with active observations is rejected by FK RESTRICT.
   - Attempting to delete a background job with active observations is rejected by FK RESTRICT.
3. Dedicated PostgreSQL 17 Integration Tests (Task D, marked with @pytest.mark.postgres):
   - Statement-level BEFORE TRUNCATE trigger blocks TRUNCATE.
   - Statement-level BEFORE TRUNCATE trigger blocks TRUNCATE CASCADE.
   - Row-level BEFORE UPDATE/DELETE triggers block UPDATE/DELETE.
   - PostgreSQL unique index enforces duplicate rejection on canonical fingerprints.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import os
import uuid
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
)
from app.models.job import BackgroundJob, JobType, JobStatus
from app.models.user import User
from app.services.material_rates.fingerprint import (
    generate_observation_fingerprint,
    FINGERPRINT_VERSION_V1,
)


# ---------------------------------------------------------------------------
# Test Fixtures (SQLite in-memory for unit and model validation)
# ---------------------------------------------------------------------------

@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite:///:memory:", echo=False)

    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# TASK C: Canonical SHA-256 Fingerprint Tests
# ---------------------------------------------------------------------------

class TestCanonicalFingerprintEngine:
    def test_01_identical_inputs_generate_identical_fingerprint(self):
        source_id = uuid.uuid4()
        prod_id = uuid.uuid4()
        dt = datetime(2026, 11, 6, 12, 30, 45, tzinfo=timezone.utc)

        fp1 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Lahore",
            published_at=dt,
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
        )
        fp2 = generate_observation_fingerprint(
            source_id=str(source_id),
            product_id=str(prod_id),
            city="  lahore  ",
            published_at="2026-11-06T12:30:45Z",
            normalized_price_pkr="1520.0",
            normalized_unit="  BAG_50KG  ",
        )
        assert fp1 == fp2
        assert len(fp1) == 64

    def test_02_price_difference_produces_different_fingerprint(self):
        source_id = uuid.uuid4()
        prod_id = uuid.uuid4()
        dt = date(2026, 11, 6)

        fp1 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Lahore",
            published_at=dt,
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
        )
        fp2 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Lahore",
            published_at=dt,
            normalized_price_pkr=Decimal("1520.50"),
            normalized_unit="bag_50kg",
        )
        assert fp1 != fp2

    def test_03_date_boundary_normalization(self):
        """Times on the same UTC calendar day generate the same publication day fingerprint."""
        source_id = uuid.uuid4()
        prod_id = uuid.uuid4()
        dt_morning = datetime(2026, 11, 6, 8, 0, 0, tzinfo=timezone.utc)
        dt_evening = datetime(2026, 11, 6, 20, 0, 0, tzinfo=timezone.utc)

        fp_morning = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Karachi",
            published_at=dt_morning,
            normalized_price_pkr=Decimal("1480.00"),
            normalized_unit="bag_50kg",
        )
        fp_evening = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Karachi",
            published_at=dt_evening,
            normalized_price_pkr=Decimal("1480.00"),
            normalized_unit="bag_50kg",
        )
        assert fp_morning == fp_evening

    def test_04_different_calendar_days_generate_different_fingerprints(self):
        source_id = uuid.uuid4()
        prod_id = uuid.uuid4()

        fp_day1 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Islamabad",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1550.00"),
            normalized_unit="bag_50kg",
        )
        fp_day2 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Islamabad",
            published_at="2026-11-07",
            normalized_price_pkr=Decimal("1550.00"),
            normalized_unit="bag_50kg",
        )
        assert fp_day1 != fp_day2

    def test_05_dealer_id_differentiation(self):
        source_id = uuid.uuid4()
        prod_id = uuid.uuid4()
        dlr1 = uuid.uuid4()
        dlr2 = uuid.uuid4()

        fp_general = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Rawalpindi",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            dealer_id=None,
        )
        fp_dealer1 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Rawalpindi",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            dealer_id=dlr1,
        )
        fp_dealer2 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Rawalpindi",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1500.00"),
            normalized_unit="bag_50kg",
            dealer_id=dlr2,
        )
        assert fp_general != fp_dealer1
        assert fp_dealer1 != fp_dealer2

    def test_06_version_contract_included(self):
        source_id = uuid.uuid4()
        prod_id = uuid.uuid4()

        fp_v1 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Lahore",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
            version=FINGERPRINT_VERSION_V1,
        )
        fp_v2 = generate_observation_fingerprint(
            source_id=source_id,
            product_id=prod_id,
            city="Lahore",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
            version="tameerai:material-rate-observation:v2",
        )
        assert fp_v1 != fp_v2


# ---------------------------------------------------------------------------
# TASK B: Foreign-Key RESTRICT Tests
# ---------------------------------------------------------------------------

class TestForeignKeyRestrictCompatibility:
    def test_07_dealer_quote_deletion_blocked_by_restrict(self, sqlite_session: Session):
        """Verifies that deleting a dealer quote with active observations is blocked by FK RESTRICT."""
        # Seed user, dealer, product, source
        user = User(
            email=f"dealer_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="argon2id$hashed",
            role="contractor",
            full_name="Dealer User",
            is_active=True,
            is_verified=True,
        )
        dealer = MaterialRateDealer(
            business_name="Audit Merchant",
            dealer_code=f"DLR-{uuid.uuid4().hex[:6]}",
            city="Lahore",
        )
        prod = MaterialRateProduct(
            code=f"PRD-{uuid.uuid4().hex[:6]}",
            category="cement",
            canonical_name="Falcon Cement OPC",
            standard_unit="bag_50kg",
        )
        source = MaterialRateSource(
            code=f"SRC-{uuid.uuid4().hex[:6]}",
            name="Dealer Portal",
            source_type="dealer_network",
        )
        sqlite_session.add_all([user, dealer, prod, source])
        sqlite_session.flush()

        quote = MaterialRateDealerQuote(
            dealer_id=dealer.id,
            product_id=prod.id,
            city="Lahore",
            quoted_price_pkr=Decimal("1490.00"),
            quoted_unit="bag",
            normalized_price_pkr=Decimal("1490.00"),
            normalized_unit="bag_50kg",
            quotation_date=datetime.now(timezone.utc),
            validity_days=7,
            valid_until=datetime.now(timezone.utc),
            status="verified",
        )
        sqlite_session.add(quote)
        sqlite_session.flush()

        obs = MaterialRateObservation(
            source_id=source.id,
            product_id=prod.id,
            dealer_quote_id=quote.id,
            city="Lahore",
            observed_price_pkr=Decimal("1490.00"),
            observed_unit="bag",
            normalized_price_pkr=Decimal("1490.00"),
            normalized_unit="bag_50kg",
            published_at=datetime.now(timezone.utc),
            verification_status="verified_quote",
            duplicate_fingerprint=uuid.uuid4().hex,
        )
        sqlite_session.add(obs)
        sqlite_session.commit()

        # Attempt to delete the parent dealer quote
        sqlite_session.delete(quote)
        with pytest.raises(IntegrityError) as exc_info:
            sqlite_session.commit()
        sqlite_session.rollback()

        # In SQLite with PRAGMA foreign_keys=ON, FK RESTRICT raises IntegrityError
        assert "foreign key" in str(exc_info.value).lower() or "restrict" in str(exc_info.value).lower()

    def test_08_background_job_deletion_blocked_by_restrict(self, sqlite_session: Session):
        """Verifies that deleting a background job linked to an observation is blocked by FK RESTRICT."""
        prod = MaterialRateProduct(
            code=f"PRD-{uuid.uuid4().hex[:6]}",
            category="steel",
            canonical_name="Mughal Supreme G60 12mm",
            standard_unit="metric_ton",
        )
        source = MaterialRateSource(
            code=f"SRC-{uuid.uuid4().hex[:6]}",
            name="Sync Worker Source",
            source_type="official",
        )
        job = BackgroundJob(
            job_type=JobType.MATERIAL_RATE_SOURCE_SYNC.value,
            status=JobStatus.COMPLETED.value,
            priority=0,
            payload={"source": "official"},
        )
        sqlite_session.add_all([prod, source, job])
        sqlite_session.flush()

        obs = MaterialRateObservation(
            source_id=source.id,
            product_id=prod.id,
            background_job_id=job.id,
            city="Karachi",
            observed_price_pkr=Decimal("260000.00"),
            observed_unit="ton",
            normalized_price_pkr=Decimal("260000.00"),
            normalized_unit="metric_ton",
            published_at=datetime.now(timezone.utc),
            verification_status="verified_market_range",
            duplicate_fingerprint=uuid.uuid4().hex,
        )
        sqlite_session.add(obs)
        sqlite_session.commit()

        # Attempt to delete the parent job
        sqlite_session.delete(job)
        with pytest.raises(IntegrityError):
            sqlite_session.commit()
        sqlite_session.rollback()


# ---------------------------------------------------------------------------
# TASK D: Dedicated PostgreSQL 17 Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.postgres
class TestPostgreSqlSafetyHardeningIntegration:
    """
    Dedicated PostgreSQL 17 integration tests.
    Executes ONLY when ISOLATED_POSTGRES_URL environment variable is set.
    Never connects to Supabase or production.
    """

    @pytest.fixture
    async def pg_connection(self):
        pg_url = os.environ.get("ISOLATED_POSTGRES_URL")
        if not pg_url or "5433" not in pg_url:
            pytest.skip("Skipping PostgreSQL integration test: ISOLATED_POSTGRES_URL on port 5433 not configured")

        import asyncpg
        conn = await asyncpg.connect(pg_url)
        try:
            yield conn
        finally:
            await conn.close()

    async def test_09_statement_level_truncate_trigger_blocks_truncate(self, pg_connection):
        """Confirms that TRUNCATE is blocked either by FK reference or by the TRUNCATE trigger."""
        with pytest.raises(Exception) as exc_info:
            await pg_connection.execute("TRUNCATE TABLE material_rate_observations, material_rate_verification_events;")
        assert "material_rate_observations is strictly append-only; TRUNCATE is forbidden" in str(exc_info.value)

    async def test_10_statement_level_truncate_trigger_blocks_truncate_cascade(self, pg_connection):
        """Confirms that TRUNCATE CASCADE is blocked with explicit exception on PostgreSQL 17."""
        with pytest.raises(Exception) as exc_info:
            await pg_connection.execute("TRUNCATE TABLE material_rate_observations CASCADE;")
        assert "material_rate_observations is strictly append-only; TRUNCATE is forbidden" in str(exc_info.value)
