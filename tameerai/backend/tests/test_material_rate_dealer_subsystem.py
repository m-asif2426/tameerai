"""
TameerAI - Stage 2E Dealer Quotations & Private Evidence Tests
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
from pathlib import Path
import tempfile
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
)
from app.services.material_rates.dealer_service import (
    DealerEvidenceManager,
    DealerQuotationService,
    EvidenceStorageError,
    dealer_service,
)


@pytest.fixture
def dealer_test_env():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    tmp_dir = Path(tempfile.mkdtemp())
    evidence_mgr = DealerEvidenceManager(base_dir=tmp_dir, signing_secret="test-secret-key-12345")
    svc = DealerQuotationService(evidence_manager=evidence_mgr)

    # Seed products across categories: Cement, Steel, Bricks, Sand
    cement = MaterialRateProduct(
        id=uuid.uuid4(),
        code="CEMENT_OPC_50KG",
        category="cement",
        canonical_name="Ordinary Portland Cement 50kg",
        standard_unit="bag_50kg",
        is_active=True,
    )
    steel = MaterialRateProduct(
        id=uuid.uuid4(),
        code="STEEL_REBAR_G60_TON",
        category="steel",
        canonical_name="Deformed Rebar G60 Ton",
        standard_unit="metric_ton",
        is_active=True,
    )
    bricks = MaterialRateProduct(
        id=uuid.uuid4(),
        code="BRICK_CLAY_AWWAL",
        category="bricks",
        canonical_name="Clay Masonry Bricks Awwal",
        standard_unit="1000_bricks",
        is_active=True,
    )
    session.add_all([cement, steel, bricks])
    session.commit()

    try:
        yield session, svc, evidence_mgr, cement, steel, bricks
    finally:
        session.close()
        engine.dispose()


class TestDealerRegistrationAndLifecycle:
    @pytest.mark.asyncio
    async def test_dealer_registration_and_verification(self, dealer_test_env):
        session, svc, _, _, _, _ = dealer_test_env

        # 1. Register Dealer
        dealer = await svc.register_dealer(
            session,
            business_name="Mughal & Sons Steel Corporation",
            dealer_code="DLR-LHR-0001",
            city="Lahore",
            market_area="Badami Bagh",
            contact_person="Chaudhry Akram",
            contact_phone="0300-1234567",
            ntn_number="1234567-8",
        )
        assert dealer.verification_state == "unverified"
        assert dealer.city == "Lahore"

        # 2. Verify Dealer
        admin_id = uuid.uuid4()
        verified_dealer = await svc.verify_dealer(session, dealer.id, admin_id)
        assert verified_dealer.verification_state == "verified"
        assert verified_dealer.verified_by_user_id == admin_id


class TestQuotationIntakeAndNormalization:
    @pytest.mark.asyncio
    async def test_quote_intake_and_auto_observation(self, dealer_test_env):
        session, svc, _, cement, steel, bricks = dealer_test_env

        dealer = await svc.register_dealer(
            session,
            business_name="Bismillah Building Traders",
            dealer_code="DLR-LHR-0002",
            city="Lahore",
        )
        await svc.verify_dealer(session, dealer.id, uuid.uuid4())

        # Submit Cement quote: 1550 PKR per bori (normalized to bag_50kg)
        quote = await svc.submit_quotation(
            session,
            dealer_id=dealer.id,
            product_id=cement.id,
            quoted_price_pkr=Decimal("1550.00"),
            quoted_unit="bori",
            city="Lahore",
            validity_days=7,
            minimum_order_quantity=Decimal("100"),
            delivery_charges_pkr=Decimal("20.00"),
            tax_included=True,
            payment_terms="Cash on Delivery",
        )

        assert quote.normalized_unit == "bag_50kg"
        assert quote.normalized_price_pkr == Decimal("1550.00")

        # Verify auto-created observation linked to quote
        obs = session.query(MaterialRateObservation).filter(MaterialRateObservation.dealer_quote_id == quote.id).first()
        assert obs is not None
        assert obs.normalized_price_pkr == Decimal("1550.00")
        assert obs.city == "Lahore"
        assert obs.verification_status == "indicative" or obs.verification_status == "verified_quote"
        assert obs.observation_metadata["payment_terms"] == "Cash on Delivery"

    @pytest.mark.asyncio
    async def test_steel_unit_normalization_from_kg_to_ton(self, dealer_test_env):
        session, svc, _, _, steel, _ = dealer_test_env

        dealer = await svc.register_dealer(
            session,
            business_name="Karachi Rebar Traders",
            dealer_code="DLR-KHI-0001",
            city="Karachi",
        )

        # Quoted in per kg: 260 PKR/kg -> 260,000 PKR/metric_ton
        quote = await svc.submit_quotation(
            session,
            dealer_id=dealer.id,
            product_id=steel.id,
            quoted_price_pkr=Decimal("260.00"),
            quoted_unit="kg",
            city="Karachi",
        )
        assert quote.normalized_unit == "metric_ton"
        assert quote.normalized_price_pkr == Decimal("260000.00")

    @pytest.mark.asyncio
    async def test_truckload_capacity_explicit_rule(self, dealer_test_env):
        """
        Validates Task F truckload capacity rule:
        1. When vehicle capacity is NOT declared, retain original unit 'truckload' with factor 1.0 (no assumed capacity).
        2. When vehicle capacity is explicitly declared (e.g. 500 cft), convert to canonical 'cft'.
        """
        session, svc, _, _, _, _ = dealer_test_env

        dealer = await svc.register_dealer(
            session,
            business_name="Chenab Sand Suppliers",
            dealer_code="DLR-LHE-SAND-01",
            city="Lahore",
        )

        sand_prod = MaterialRateProduct(
            id=uuid.uuid4(),
            code="SAND_CHENAB_TEST",
            category="sand",
            canonical_name="Chenab River Sand",
            standard_unit="cft",
            is_active=True,
        )
        session.add(sand_prod)
        session.commit()

        # Case A: No capacity declared -> retains original unit, no invented conversion
        quote_a = await svc.submit_quotation(
            session,
            dealer_id=dealer.id,
            product_id=sand_prod.id,
            quoted_price_pkr=Decimal("25000.00"),
            quoted_unit="truckload",
            city="Lahore",
            vehicle_capacity_cft=None,
        )
        assert quote_a.normalized_unit == "truckload"
        assert quote_a.normalized_price_pkr == Decimal("25000.00")

        # Case B: Explicit capacity declared (500 cft dumper) -> converts cleanly to cft
        quote_b = await svc.submit_quotation(
            session,
            dealer_id=dealer.id,
            product_id=sand_prod.id,
            quoted_price_pkr=Decimal("25000.00"),
            quoted_unit="truckload",
            city="Lahore",
            vehicle_capacity_cft=Decimal("500.00"),
        )
        assert quote_b.normalized_unit == "cft"
        assert quote_b.normalized_price_pkr == Decimal("50.00")  # 25000 / 500 = 50 PKR/cft


class TestPrivateEvidenceStorageAndSecurity:
    def test_evidence_storage_and_tamper_hash(self, dealer_test_env):
        _, _, evidence_mgr, _, _, _ = dealer_test_env

        dealer_id = uuid.uuid4()
        quote_id = uuid.uuid4()
        sample_bytes = b"%PDF-1.4 sample invoice quotation slip content for audit verification"

        rel_path, sha_hash, size = evidence_mgr.save_evidence_file(
            dealer_id=dealer_id,
            quote_id=quote_id,
            filename="receipt.pdf",
            content_type="application/pdf",
            file_bytes=sample_bytes,
        )

        assert sha_hash is not None
        assert len(sha_hash) == 64
        assert size == len(sample_bytes)

        # Verify full path exists
        full_path = evidence_mgr.get_full_file_path(rel_path)
        assert full_path.exists()
        assert full_path.read_bytes() == sample_bytes

    def test_signed_token_lifecycle(self, dealer_test_env):
        _, _, evidence_mgr, _, _, _ = dealer_test_env
        rel_path = "dealers/d1/quotes/q1/hash.pdf"

        # Generate token
        token = evidence_mgr.generate_signed_token(rel_path, expires_in_seconds=60)
        assert evidence_mgr.verify_signed_token(rel_path, token) is True

        # Tampered token fails
        tampered_token = token + "xyz"
        assert evidence_mgr.verify_signed_token(rel_path, tampered_token) is False

        # Wrong path fails
        assert evidence_mgr.verify_signed_token("different/path.pdf", token) is False

    def test_unsupported_file_type_rejected(self, dealer_test_env):
        _, _, evidence_mgr, _, _, _ = dealer_test_env
        with pytest.raises(EvidenceStorageError):
            evidence_mgr.save_evidence_file(
                dealer_id=uuid.uuid4(),
                quote_id=uuid.uuid4(),
                filename="script.exe",
                content_type="application/x-msdownload",
                file_bytes=b"malicious payload",
            )


class TestQuoteExpirySweeper:
    @pytest.mark.asyncio
    async def test_sweep_expired_quotes(self, dealer_test_env):
        session, svc, _, cement, _, _ = dealer_test_env

        dealer = await svc.register_dealer(
            session,
            business_name="Rawalpindi Materials",
            dealer_code="DLR-RWP-0001",
            city="Rawalpindi",
        )

        # Create quote with valid_until in the past
        past_date = datetime.now(timezone.utc) - timedelta(days=2)
        quote = MaterialRateDealerQuote(
            id=uuid.uuid4(),
            dealer_id=dealer.id,
            product_id=cement.id,
            city="Rawalpindi",
            quoted_price_pkr=Decimal("1520.00"),
            quoted_unit="bag_50kg",
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
            quotation_date=datetime.now(timezone.utc) - timedelta(days=10),
            validity_days=7,
            valid_until=past_date,
            delivery_charges_pkr=Decimal("0.00"),
            tax_included=True,
            status="pending_review",
        )
        session.add(quote)
        session.commit()

        expired_count = await svc.sweep_expired_quotes(session)
        assert expired_count >= 1

        session.refresh(quote)
        assert quote.status == "expired"

