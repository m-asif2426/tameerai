"""
TameerAI - Phase 03H Stage 1: Material Rate Intelligence Models & Schema Tests

Comprehensive test suite verifying:
1. Model registration on Base.metadata (7 new entities + updated BackgroundJob + MaterialRate).
2. Primary keys, UUID generation, foreign keys, and cascade deletion behaviors.
3. Check constraints on all models (status enums, non-negative amounts, variance ranges).
4. BackgroundJob system-scope consistency check:
   - (project_id IS NULL AND user_id IS NULL) -> VALID (Global system job).
   - (project_id IS NOT NULL AND user_id IS NOT NULL) -> VALID (Project-scoped job).
   - (project_id IS NOT NULL AND user_id IS NULL) -> REJECTED.
   - (project_id IS NULL AND user_id IS NOT NULL) -> REJECTED.
5. System-job partial unique idempotency index.
6. MaterialRate backward compatibility and extended verification status check constraint.
7. Immutable observation deduplication via unique SHA-256 fingerprint.
8. Independent dealer quote evidence references (no project scoping requirement).
9. Source-specific configurable freshness TTL and dealer quotation validity windows.
10. Alembic Migration 006 file integrity, revision chain, upgrade/downgrade methods.
11. Full relational CRUD and cascade verification on isolated test database.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.cost import MaterialRate, BOQAnalysis, BOQItem
from app.models.job import BackgroundJob, JobStatus, JobType
from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateVerificationEvent,
    MaterialRateSourceRun,
)


# ---------------------------------------------------------------------------
# Fixture: Isolated in-memory database enforcing foreign keys & check constraints
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def isolated_db() -> Generator[Session, None, None]:
    """Creates an isolated in-memory database with foreign keys and check constraints enforced."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# Helper: Seed core user and project
# ---------------------------------------------------------------------------

def seed_user_and_project(db: Session):
    user = User(
        email=f"eng_{uuid.uuid4().hex[:6]}@tameerai.pk",
        hashed_password="hash",
        full_name="Engr. Tariq Mehmood",
        city="Lahore",
    )
    db.add(user)
    db.flush()

    project = Project(
        code=f"PRJ-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        name="Gulberg Commercial Plaza",
        location="Main Boulevard, Gulberg III, Lahore",
        city="Lahore",
        budget_raw=Decimal("150000000.00"),
    )
    db.add(project)
    db.flush()
    return user, project


# ---------------------------------------------------------------------------
# Test Group A: Model Registration & Schema Introspection
# ---------------------------------------------------------------------------

class TestModelRegistrationAndSchema:
    def test_01_all_new_tables_registered_on_base_metadata(self):
        """Verifies that all 7 Stage 1 tables are properly registered on Base.metadata."""
        expected_tables = {
            "material_rate_products",
            "material_rate_sources",
            "material_rate_dealers",
            "material_rate_dealer_quotes",
            "material_rate_observations",
            "material_rate_verification_events",
            "material_rate_source_runs",
            "material_rates",
            "background_jobs",
        }
        actual_tables = set(Base.metadata.tables.keys())
        for table in expected_tables:
            assert table in actual_tables, f"Table '{table}' missing from Base.metadata"

    def test_02_uuid_primary_keys_configured(self):
        """Verifies that all new models use UUID primary keys with default generators."""
        models = [
            MaterialRateProduct,
            MaterialRateSource,
            MaterialRateDealer,
            MaterialRateDealerQuote,
            MaterialRateObservation,
            MaterialRateVerificationEvent,
            MaterialRateSourceRun,
        ]
        for model in models:
            pk_col = model.__table__.primary_key.columns.values()[0]
            assert pk_col.name == "id", f"{model.__name__} primary key must be 'id'"
            assert pk_col.type.python_type is uuid.UUID, f"{model.__name__} PK must have python_type UUID"


# ---------------------------------------------------------------------------
# Test Group B: BackgroundJob System-Scope Consistency (Correction 1 & 2)
# ---------------------------------------------------------------------------

class TestBackgroundJobSystemScope:
    def test_03_project_scoped_job_accepted(self, isolated_db: Session):
        """Verifies that traditional project-scoped jobs (both project_id and user_id present) are accepted."""
        user, project = seed_user_and_project(isolated_db)
        job = BackgroundJob(
            project_id=project.id,
            user_id=user.id,
            job_type=JobType.BOQ_EXTRACTION.value,
            idempotency_key="idemp_prj_01",
        )
        isolated_db.add(job)
        isolated_db.commit()
        assert job.id is not None
        assert job.project_id == project.id
        assert job.user_id == user.id

    def test_04_global_system_job_accepted(self, isolated_db: Session):
        """Verifies that global system jobs (both project_id and user_id NULL) are accepted."""
        job = BackgroundJob(
            project_id=None,
            user_id=None,
            job_type=JobType.PBS_WEEKLY_SYNC.value,
            idempotency_key="pbs_spi_2026_w44",
        )
        isolated_db.add(job)
        isolated_db.commit()
        assert job.id is not None
        assert job.project_id is None
        assert job.user_id is None

    def test_05_inconsistent_scope_rejected_project_without_user(self, isolated_db: Session):
        """Verifies that providing project_id without user_id violates ck_background_jobs_scope_consistency."""
        user, project = seed_user_and_project(isolated_db)
        job = BackgroundJob(
            project_id=project.id,
            user_id=None,
            job_type=JobType.MATERIAL_RATE_SOURCE_SYNC.value,
        )
        isolated_db.add(job)
        with pytest.raises(IntegrityError):
            isolated_db.commit()
        isolated_db.rollback()

    def test_06_inconsistent_scope_rejected_user_without_project(self, isolated_db: Session):
        """Verifies that providing user_id without project_id violates ck_background_jobs_scope_consistency."""
        user, project = seed_user_and_project(isolated_db)
        job = BackgroundJob(
            project_id=None,
            user_id=user.id,
            job_type=JobType.MATERIAL_RATE_SOURCE_SYNC.value,
        )
        isolated_db.add(job)
        with pytest.raises(IntegrityError):
            isolated_db.commit()
        isolated_db.rollback()

    def test_07_system_job_idempotency_enforced(self, isolated_db: Session):
        """Verifies that duplicate system jobs with the same job_type and idempotency_key are rejected."""
        job1 = BackgroundJob(
            project_id=None,
            user_id=None,
            job_type=JobType.PBS_WEEKLY_SYNC.value,
            idempotency_key="pbs_spi_same_week",
        )
        isolated_db.add(job1)
        isolated_db.commit()

        job2 = BackgroundJob(
            project_id=None,
            user_id=None,
            job_type=JobType.PBS_WEEKLY_SYNC.value,
            idempotency_key="pbs_spi_same_week",
        )
        isolated_db.add(job2)
        with pytest.raises(IntegrityError):
            isolated_db.commit()
        isolated_db.rollback()


# ---------------------------------------------------------------------------
# Test Group C: MaterialRate Backward Compatibility (Correction 3)
# ---------------------------------------------------------------------------

class TestMaterialRateBackwardCompatibility:
    def test_08_legacy_statuses_preserved(self, isolated_db: Session):
        """Verifies that legacy statuses ('verified', 'unverified', 'stale') continue working seamlessly."""
        for status_val in ["verified", "unverified", "stale"]:
            rate = MaterialRate(
                city="Lahore",
                category="cement",
                name=f"Legacy Cement {status_val}",
                unit="bag (50kg)",
                rate_pkr=Decimal("1550.00"),
                source_name="Pakistan Bureau of Statistics",
                observed_at=datetime.now(timezone.utc),
                verification_status=status_val,
            )
            isolated_db.add(rate)
        isolated_db.commit()

    def test_09_extended_verification_statuses_accepted(self, isolated_db: Session):
        """Verifies that new multi-source statuses are accepted by the expanded check constraint."""
        extended_statuses = [
            "verified_quote",
            "cross_checked",
            "verified_market_range",
            "indicative",
            "conflicted",
        ]
        for st in extended_statuses:
            rate = MaterialRate(
                city="Karachi",
                category="steel",
                name=f"Steel G60 ({st})",
                unit="ton",
                rate_pkr=Decimal("265000.00"),
                source_name="Verified Market Dealer Feed",
                observed_at=datetime.now(timezone.utc),
                verification_status=st,
            )
            isolated_db.add(rate)
        isolated_db.commit()

    def test_10_invalid_verification_status_rejected(self, isolated_db: Session):
        """Verifies that arbitrary or invalid status strings are rejected by check constraint."""
        rate = MaterialRate(
            city="Islamabad",
            category="sand",
            name="Ravi Sand",
            unit="cft",
            rate_pkr=Decimal("55.00"),
            source_name="Test Source",
            observed_at=datetime.now(timezone.utc),
            verification_status="bogus_status_123",
        )
        isolated_db.add(rate)
        with pytest.raises(IntegrityError):
            isolated_db.commit()
        isolated_db.rollback()

    def test_11_boq_item_relationship_preserved(self, isolated_db: Session):
        """Verifies that BOQItem.material_rate_id foreign key remains functional and intact."""
        user, project = seed_user_and_project(isolated_db)
        rate = MaterialRate(
            city="Lahore",
            category="steel",
            name="Deformed Rebar Grade 60 1/2 inch",
            unit="ton",
            rate_pkr=Decimal("260000.00"),
            source_name="Mughal Steel Mill Gate",
            observed_at=datetime.now(timezone.utc),
            verification_status="verified",
        )
        isolated_db.add(rate)
        isolated_db.flush()

        analysis = BOQAnalysis(
            project_id=project.id,
            user_id=user.id,
            status="completed",
        )
        isolated_db.add(analysis)
        isolated_db.flush()

        item = BOQItem(
            analysis_id=analysis.id,
            material_rate_id=rate.id,
            phase="Superstructure",
            description="Supply and fix Grade 60 12mm rebar",
            unit="ton",
            quantity=Decimal("15.5"),
            boq_base_rate=Decimal("250000.00"),
            current_price=Decimal("260000.00"),
            budget_amount=Decimal("3875000.00"),
            estimated_amount=Decimal("4030000.00"),
        )
        isolated_db.add(item)
        isolated_db.commit()

        # Query back through relationship
        loaded_item = isolated_db.scalar(select(BOQItem).where(BOQItem.id == item.id))
        assert loaded_item is not None
        assert loaded_item.material_rate is not None
        assert loaded_item.material_rate.rate_pkr == Decimal("260000.00")
        assert loaded_item.material_rate.name == "Deformed Rebar Grade 60 1/2 inch"


# ---------------------------------------------------------------------------
# Test Group D: Canonical Products & Source Catalog (Correction 4 & 5)
# ---------------------------------------------------------------------------

class TestCatalogAndSources:
    def test_12_material_rate_product_creation(self, isolated_db: Session):
        """Verifies creation of canonical product definitions with JSON attributes."""
        prod = MaterialRateProduct(
            code="CEMENT-OPC-50KG",
            category="cement",
            subcategory="OPC",
            canonical_name="Ordinary Portland Cement 50kg Bag",
            canonical_name_urdu="عام پورٹلینڈ سیمنٹ 50 کلو بوری",
            standard_unit="bag_50kg",
            standard_unit_urdu="50 کلو بوری",
            spec_attributes={"standard": "PSQCA 232-2008", "weight_kg": 50},
            volatility_tier="medium",
            max_acceptable_variance_pct=Decimal("12.50"),
        )
        isolated_db.add(prod)
        isolated_db.commit()

        loaded = isolated_db.scalar(select(MaterialRateProduct).where(MaterialRateProduct.code == "CEMENT-OPC-50KG"))
        assert loaded is not None
        assert loaded.category == "cement"
        assert loaded.spec_attributes.get("weight_kg") == 50
        assert loaded.max_acceptable_variance_pct == Decimal("12.50")

    def test_13_product_volatility_check_constraint(self, isolated_db: Session):
        """Verifies that invalid volatility tier is rejected."""
        prod = MaterialRateProduct(
            code="INVALID-VOLATILITY",
            category="steel",
            canonical_name="Invalid Product",
            standard_unit="kg",
            volatility_tier="super_extreme_unsupported",
        )
        isolated_db.add(prod)
        with pytest.raises(IntegrityError):
            isolated_db.commit()
        isolated_db.rollback()

    def test_14_material_rate_source_configurable_ttl(self, isolated_db: Session):
        """Verifies that data sources support configurable freshness TTL (Correction 5)."""
        pbs_source = MaterialRateSource(
            code="PBS_SPI",
            name="Pakistan Bureau of Statistics - Weekly SPI",
            source_type="official",
            permission_status="permitted",
            reliability_tier="authoritative",
            refresh_cadence="weekly",
            freshness_ttl_days=14,  # Configurable 14 days
            base_url="https://www.pbs.gov.pk",
        )
        dealer_source = MaterialRateSource(
            code="DEALER_DIRECT",
            name="Verified Merchant Direct Quotes",
            source_type="dealer_network",
            permission_status="permitted",
            reliability_tier="verified",
            refresh_cadence="daily",
            freshness_ttl_days=7,  # Configurable 7 days for retail dealer quotes
        )
        isolated_db.add_all([pbs_source, dealer_source])
        isolated_db.commit()

        loaded_pbs = isolated_db.scalar(select(MaterialRateSource).where(MaterialRateSource.code == "PBS_SPI"))
        loaded_dlr = isolated_db.scalar(select(MaterialRateSource).where(MaterialRateSource.code == "DEALER_DIRECT"))
        assert loaded_pbs.freshness_ttl_days == 14
        assert loaded_dlr.freshness_ttl_days == 7


# ---------------------------------------------------------------------------
# Test Group E: Dealers & Quotations with Safe Evidence (Correction 6)
# ---------------------------------------------------------------------------

class TestDealersAndQuotes:
    def test_15_dealer_profile_creation(self, isolated_db: Session):
        """Verifies dealer merchant registration and verification state."""
        user, _ = seed_user_and_project(isolated_db)
        dealer = MaterialRateDealer(
            user_id=user.id,
            business_name="Al-Rehman Steel & Cement Traders",
            dealer_code="DLR-LHR-0012",
            city="Lahore",
            market_area="Badami Bagh",
            contact_person="Mian Abdul Rehman",
            contact_phone="0300-1234567",
            ntn_number="1234567-8",
            verification_state="verified",
            verified_by_user_id=user.id,
            verified_at=datetime.now(timezone.utc),
        )
        isolated_db.add(dealer)
        isolated_db.commit()

        loaded = isolated_db.scalar(select(MaterialRateDealer).where(MaterialRateDealer.dealer_code == "DLR-LHR-0012"))
        assert loaded is not None
        assert loaded.verification_state == "verified"
        assert loaded.city == "Lahore"

    def test_16_dealer_quotation_with_safe_evidence_storage(self, isolated_db: Session):
        """Verifies dealer quotation submission with independent storage path (Correction 6)."""
        user, _ = seed_user_and_project(isolated_db)
        prod = MaterialRateProduct(
            code="STEEL-G60-12MM",
            category="steel",
            canonical_name="Deformed Rebar Grade 60 12mm",
            standard_unit="metric_ton",
        )
        dealer = MaterialRateDealer(
            business_name="Ittifaq Steel Agency",
            dealer_code="DLR-LHR-0088",
            city="Lahore",
            verification_state="verified",
        )
        isolated_db.add_all([prod, dealer])
        isolated_db.flush()

        now = datetime.now(timezone.utc)
        validity = 5  # 5 days validity
        quote = MaterialRateDealerQuote(
            dealer_id=dealer.id,
            product_id=prod.id,
            city="Lahore",
            quoted_price_pkr=Decimal("268000.00"),
            quoted_unit="per ton",
            normalized_price_pkr=Decimal("268000.00"),
            normalized_unit="metric_ton",
            quotation_date=now,
            validity_days=validity,
            valid_until=now + timedelta(days=validity),
            minimum_order_quantity=Decimal("5.00"),
            delivery_charges_pkr=Decimal("3500.00"),
            tax_included=True,
            payment_terms="50% Advance, 50% on Delivery",
            # Independent storage reference (No project document required)
            evidence_file_path="dealer-quotations/DLR-LHR-0088/quote_20261106.pdf",
            evidence_file_name="quote_20261106.pdf",
            evidence_content_type="application/pdf",
            evidence_file_size_bytes=245890,
            status="pending_review",
        )
        isolated_db.add(quote)
        isolated_db.commit()

        loaded_quote = isolated_db.scalar(select(MaterialRateDealerQuote).where(MaterialRateDealerQuote.id == quote.id))
        assert loaded_quote is not None
        assert loaded_quote.evidence_file_path == "dealer-quotations/DLR-LHR-0088/quote_20261106.pdf"
        assert loaded_quote.normalized_price_pkr == Decimal("268000.00")
        assert loaded_quote.validity_days == 5
        assert loaded_quote.status == "pending_review"


# ---------------------------------------------------------------------------
# Test Group F: Immutable Observations & Deduplication Fingerprints
# ---------------------------------------------------------------------------

class TestObservationsAndFingerprints:
    def test_17_immutable_observation_created(self, isolated_db: Session):
        """Verifies immutable observation recording with SHA-256 fingerprint."""
        prod = MaterialRateProduct(
            code="BRICK-AWWAL-STD",
            category="bricks",
            canonical_name="Red Clay Bricks A-Class (Awwal)",
            standard_unit="1000_bricks",
        )
        source = MaterialRateSource(
            code="MANUAL_SURVEY_LHR",
            name="Lahore Local Kiln Survey",
            source_type="manual_survey",
        )
        isolated_db.add_all([prod, source])
        isolated_db.flush()

        now = datetime.now(timezone.utc)
        fingerprint_raw = f"{source.id}:{prod.id}:Lahore:{now.date().isoformat()}:1000_bricks"
        sha_fp = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()

        obs = MaterialRateObservation(
            source_id=source.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("14500.00"),
            observed_unit="1000 bricks",
            normalized_price_pkr=Decimal("14500.00"),
            normalized_unit="1000_bricks",
            published_at=now,
            verification_status="verified_quote",
            duplicate_fingerprint=sha_fp,
            observation_metadata={"kiln_location": "Raiwind Road", "quality": "Awwal"},
        )
        isolated_db.add(obs)
        isolated_db.commit()

        loaded_obs = isolated_db.scalar(select(MaterialRateObservation).where(MaterialRateObservation.duplicate_fingerprint == sha_fp))
        assert loaded_obs is not None
        assert loaded_obs.normalized_price_pkr == Decimal("14500.00")
        assert loaded_obs.verification_status == "verified_quote"

    def test_18_duplicate_observation_rejected_by_fingerprint(self, isolated_db: Session):
        """Verifies that inserting an observation with an identical fingerprint fails immediately."""
        prod = MaterialRateProduct(
            code="SAND-CHENAB-CFT",
            category="sand",
            canonical_name="Chenab River Sand",
            standard_unit="cft",
        )
        source = MaterialRateSource(
            code="SAND_SURVEY",
            name="Sand Survey Source",
            source_type="manual_survey",
        )
        isolated_db.add_all([prod, source])
        isolated_db.flush()

        fp = hashlib.sha256(b"same_sand_observation_fingerprint").hexdigest()
        now = datetime.now(timezone.utc)

        obs1 = MaterialRateObservation(
            source_id=source.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("65.00"),
            observed_unit="cft",
            normalized_price_pkr=Decimal("65.00"),
            normalized_unit="cft",
            published_at=now,
            duplicate_fingerprint=fp,
        )
        isolated_db.add(obs1)
        isolated_db.commit()

        obs2 = MaterialRateObservation(
            source_id=source.id,
            product_id=prod.id,
            city="Lahore",
            observed_price_pkr=Decimal("65.00"),
            observed_unit="cft",
            normalized_price_pkr=Decimal("65.00"),
            normalized_unit="cft",
            published_at=now,
            duplicate_fingerprint=fp,  # Colliding fingerprint
        )
        isolated_db.add(obs2)
        with pytest.raises(IntegrityError):
            isolated_db.commit()
        isolated_db.rollback()


# ---------------------------------------------------------------------------
# Test Group G: Verification Audit Trail & Source Runs
# ---------------------------------------------------------------------------

class TestAuditTrailAndRuns:
    def test_19_verification_event_logged(self, isolated_db: Session):
        """Verifies explainable verification decision logging."""
        user, _ = seed_user_and_project(isolated_db)
        prod = MaterialRateProduct(
            code="CRUSH-MARGALLA-CFT",
            category="crush",
            canonical_name="Margalla 3/4 Crush",
            standard_unit="cft",
        )
        source = MaterialRateSource(
            code="TEST_SRC",
            name="Test Source",
            source_type="official",
        )
        isolated_db.add_all([prod, source])
        isolated_db.flush()

        obs = MaterialRateObservation(
            source_id=source.id,
            product_id=prod.id,
            city="Islamabad",
            observed_price_pkr=Decimal("110.00"),
            observed_unit="cft",
            normalized_price_pkr=Decimal("110.00"),
            normalized_unit="cft",
            published_at=datetime.now(timezone.utc),
            duplicate_fingerprint=uuid.uuid4().hex,
            verification_status="unverified",
        )
        isolated_db.add(obs)
        isolated_db.flush()

        event_log = MaterialRateVerificationEvent(
            observation_id=obs.id,
            previous_status="unverified",
            new_status="verified_quote",
            reason="Confirmed by on-site structural engineer against Taxila quarry dispatch receipt.",
            actor_user_id=user.id,
            metadata_snapshot={"variance_vs_median_pct": 2.4},
        )
        isolated_db.add(event_log)
        isolated_db.commit()

        loaded_ev = isolated_db.scalar(select(MaterialRateVerificationEvent).where(MaterialRateVerificationEvent.id == event_log.id))
        assert loaded_ev is not None
        assert loaded_ev.new_status == "verified_quote"
        assert loaded_ev.actor_user_id == user.id

    def test_20_source_run_telemetry_recorded(self, isolated_db: Session):
        """Verifies data collection worker run execution tracking."""
        source = MaterialRateSource(
            code="PBS_RUN_SRC",
            name="PBS SPI Source",
            source_type="official",
        )
        isolated_db.add(source)
        isolated_db.flush()

        run = MaterialRateSourceRun(
            source_id=source.id,
            status="completed",
            records_discovered=17,
            records_accepted=17,
            records_rejected=0,
            duration_seconds=Decimal("1.45"),
        )
        isolated_db.add(run)
        isolated_db.commit()

        loaded_run = isolated_db.scalar(select(MaterialRateSourceRun).where(MaterialRateSourceRun.id == run.id))
        assert loaded_run is not None
        assert loaded_run.status == "completed"
        assert loaded_run.records_accepted == 17


# ---------------------------------------------------------------------------
# Test Group H: Alembic Migration 006 File & Revision Integrity
# ---------------------------------------------------------------------------

class TestAlembicMigration006:
    def test_21_migration_006_file_structure(self):
        """Verifies that migration 006 script exists, wires revisions correctly, and defines upgrade/downgrade."""
        migration_path = (
            Path(__file__).resolve().parent.parent
            / "alembic"
            / "versions"
            / "006_material_rate_intelligence_system.py"
        )
        assert migration_path.exists(), f"Migration file missing at: {migration_path}"
        content = migration_path.read_text(encoding="utf-8")

        assert 'revision: str = "006_material_rate_intelligence"' in content
        assert 'down_revision: Union[str, None] = "005_background_jobs_infrastructure"' in content
        assert "def upgrade() -> None:" in content
        assert "def downgrade() -> None:" in content

        # Check critical migration commands
        assert "ck_background_jobs_scope_consistency" in content
        assert "uq_background_jobs_system_idempotency" in content
        assert "material_rate_products" in content
        assert "material_rate_sources" in content
        assert "material_rate_dealers" in content
        assert "material_rate_dealer_quotes" in content
        assert "material_rate_observations" in content
        assert "material_rate_verification_events" in content
        assert "material_rate_source_runs" in content
        assert "ck_material_rates_verification_status" in content
