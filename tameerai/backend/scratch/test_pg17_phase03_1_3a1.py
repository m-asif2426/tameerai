import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
import sys
import uuid

sys.path.insert(0, r"D:\new idea project\tameerai\backend")
os.chdir(r"D:\new idea project\tameerai\backend")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select
from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
)
from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge
from app.services.material_rates.canonical_engine import CanonicalMarketRateEngine
from app.services.material_rates.historical_service import HistoricalMarketIntelligenceService
from app.services.material_rates.identity_resolver import (
    centralized_identity_resolver,
    detect_observation_steel_grade,
    PRODUCT_CODE_STEEL_G40,
    PRODUCT_CODE_STEEL_G60,
)

PG17_DSN = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

async def main():
    print("=" * 80)
    print("TAMEERAI — PHASE 03.1.3A.1 LIVE POSTGRESQL 17 VERIFICATION SUITE")
    print("Host: 127.0.0.1:5433 | DB: tameerai_isolated_test")
    print("=" * 80)

    engine = create_async_engine(PG17_DSN)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    bridge = MaterialRateIntelligenceBridge()
    canonical_engine = CanonicalMarketRateEngine()
    historical_service = HistoricalMarketIntelligenceService()

    async with session_factory() as session:
        # ----------------------------------------------------------------------
        # TEST 1: RECONCILE ALL 35 HISTORICAL PBS STEEL OBSERVATIONS
        # ----------------------------------------------------------------------
        print("\n--- TEST 1: Comprehensive Inventory of All 35 PBS Steel Observations ---")
        stmt_pbs_steel = (
            select(MaterialRateObservation, MaterialRateSource, MaterialRateProduct)
            .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
            .join(MaterialRateProduct, MaterialRateObservation.product_id == MaterialRateProduct.id)
            .where(
                MaterialRateSource.code == "PBS_STATISTICAL_MONTHLY",
                MaterialRateObservation.dealer_quote_id.is_(None),
                (MaterialRateProduct.category == "steel") | (MaterialRateProduct.code.like("%STEEL%")),
            )
            .order_by(MaterialRateObservation.city)
        )
        res_pbs_steel = (await session.execute(stmt_pbs_steel)).all()
        print(f"Total PBS Steel Records in PostgreSQL 17: {len(res_pbs_steel)}")
        assert len(res_pbs_steel) == 35, f"Expected 35 records, got {len(res_pbs_steel)}"

        grade_40_count = 0
        grade_60_count = 0
        for i, (obs, src, prod) in enumerate(res_pbs_steel, 1):
            detected_grade = detect_observation_steel_grade(obs)
            res_id, res_code, res_name, _ = await centralized_identity_resolver.resolve_observation_canonical_product(
                session, obs, prod
            )
            if detected_grade == "Grade 40":
                grade_40_count += 1
            elif detected_grade == "Grade 60":
                grade_60_count += 1

            assert detected_grade == "Grade 40", f"Obs {obs.id} not Grade 40: {detected_grade}"
            assert res_code == PRODUCT_CODE_STEEL_G40, f"Obs {obs.id} did not resolve to Grade 40 product code: {res_code}"
            assert res_name == "Mild Steel Bar Grade 40", f"Obs {obs.id} name unexpected: {res_name}"

            if i <= 5 or i >= 31:
                meta = obs.observation_metadata or {}
                item = meta.get("item_name")
                print(f"[{i:02d}] {obs.city:15} | Stored: {prod.code} | Item: '{item}' | Resolved: {res_code} ({res_name})")

        print(f"-> Verified: 35 out of 35 historical PBS steel records are GENUINE GRADE 40.")
        print(f"-> Verified: 0 out of 35 historical PBS steel records are Grade 60.")
        print("-> [PASSED] Full 35-record PBS steel inventory & Grade 40 resolution verified.")

        # ----------------------------------------------------------------------
        # TEST 2: CANONICAL MARKET RATE ENGINE GRADE ISOLATION (LIVE PG17)
        # ----------------------------------------------------------------------
        print("\n--- TEST 2: CanonicalMarketRateEngine Grade 40 vs Grade 60 Isolation ---")
        prod_g60 = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G60"))).scalar_one()
        prod_g40 = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.code == "STEEL_REBAR_G40"))).scalar_one()

        # Compute Lahore benchmark for G60
        bench_g60 = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod_g60, "Lahore")
        if bench_g60:
            print(f"G60 Lahore Benchmark: PKR {bench_g60.rate_pkr:,.2f} / {bench_g60.product.standard_unit} (obs count: {bench_g60.observation_count})")
            assert bench_g60.product.code == "STEEL_REBAR_G60"

        # Compute Lahore benchmark for G40
        bench_g40 = await canonical_engine.compute_canonical_rate_for_product_and_city(session, prod_g40, "Lahore")
        assert bench_g40 is not None, "Grade 40 benchmark should be computed"
        print(f"G40 Lahore Benchmark: PKR {bench_g40.rate_pkr:,.2f} / {bench_g40.product.standard_unit} (obs count: {bench_g40.observation_count})")
        assert bench_g40.product.code == "STEEL_REBAR_G40"
        assert bench_g40.rate_pkr != bench_g60.rate_pkr, "Grade 40 and Grade 60 benchmarks must be distinct"
        print("-> [PASSED] CanonicalMarketRateEngine isolates Grade 40 from Grade 60 benchmarks.")

        # ----------------------------------------------------------------------
        # TEST 3: HISTORICAL MARKET INTELLIGENCE SERVICE (LIVE PG17)
        # ----------------------------------------------------------------------
        print("\n--- TEST 3: Historical Service Isolation & ISO Week Formatting ---")
        hist_g40 = await historical_service.get_price_history(session, product_code="STEEL_REBAR_G40", city="Lahore", interval="weekly")
        print(f"G40 Lahore History Data Points: {len(hist_g40['data_points'])}")
        assert hist_g40["total_observations"] >= 1
        assert hist_g40["product_code"] == "STEEL_REBAR_G40"
        for dp in hist_g40["data_points"]:
            print(f"  Period: {dp['period']} | Median: PKR {dp['median_pkr']:,.2f} | Obs: {dp['observation_count']}")
            assert "-W" in dp["period"], f"Expected ISO week format, got {dp['period']}"

        # ----------------------------------------------------------------------
        # TEST 4: OBSERVATION DATE VS INSERTION DATE FRESHNESS SEPARATION
        # ----------------------------------------------------------------------
        print("\n--- TEST 4: Date & Freshness Policy (Rejecting Stale Imported Records) ---")
        # PBS observation reliable market date
        obs_pbs_sample = res_pbs_steel[0][0]
        obs_sample_id = obs_pbs_sample.id
        m_date = centralized_identity_resolver.resolve_effective_market_date(obs_pbs_sample)
        print(f"PBS Sample Survey Period: '{obs_pbs_sample.observation_metadata.get('survey_reference_period')}' -> Market Date: {m_date.isoformat()}")
        assert m_date is not None
        assert m_date.year == 2026 and m_date.month == 10

        now_utc = datetime.now(timezone.utc)
        assert centralized_identity_resolver.is_market_date_fresh(m_date, ttl_days=45.0, now=now_utc) is True
        print("-> [PASSED] October 2026 monthly reference period is fresh within 45-day TTL.")

        # Test historical 2020 record with current collected_at
        synthetic_old_obs = MaterialRateObservation(
            id=uuid.uuid4(),
            observed_price_pkr=Decimal("150000.00"),
            observed_unit="metric_ton",
            published_at=None,
            collected_at=now_utc,  # Collected right now!
            observation_metadata={"survey_reference_period": "July, 2020"},
        )
        old_m_date = centralized_identity_resolver.resolve_effective_market_date(synthetic_old_obs)
        assert old_m_date is not None
        assert old_m_date.year == 2020 and old_m_date.month == 7 and old_m_date.day == 31
        is_fresh = centralized_identity_resolver.is_market_date_fresh(old_m_date, ttl_days=45.0, now=now_utc)
        assert is_fresh is False
        print(f"Historical 2020 Observation (collected_at = now) -> Market Date: {old_m_date.date()} -> Fresh: {is_fresh}")
        print("-> [PASSED] Ingestion timestamp (collected_at=now) NEVER establishes freshness for historical data.")

        # ----------------------------------------------------------------------
        # TEST 5: AUTHORITATIVE DEALER OWNERSHIP VALIDATION ON PG17
        # ----------------------------------------------------------------------
        print("\n--- TEST 5: Authoritative Dealer Ownership & Fail-Closed Tenancy ---")
        dealer = MaterialRateDealer(
            id=uuid.uuid4(),
            dealer_code=f"DLR-PG17-{uuid.uuid4().hex[:6]}",
            business_name="PG17 Authority Vetted Merchant",
            city="Lahore",
            verification_state="verified",
            is_active=True,
        )
        session.add(dealer)
        await session.flush()

        proj_auth = uuid.uuid4()
        proj_foreign = uuid.uuid4()
        proj_conf_obs = uuid.uuid4()

        # Authoritative quote
        quote = MaterialRateDealerQuote(
            id=uuid.uuid4(),
            dealer_id=dealer.id,
            product_id=prod_g60.id,
            city="Lahore",
            quoted_price_pkr=Decimal("258000.00"),
            quoted_unit="metric_ton",
            normalized_price_pkr=Decimal("258000.00"),
            normalized_unit="metric_ton",
            quotation_date=now_utc,
            valid_until=now_utc + timedelta(days=7),
            validity_days=7,
            status="verified",
        )
        setattr(quote, "quotation_metadata", {"project_id": str(proj_auth)})
        session.add(quote)
        await session.flush()

        obs_dealer = MaterialRateObservation(
            id=uuid.uuid4(),
            source_id=res_pbs_steel[0][1].id,
            product_id=prod_g60.id,
            dealer_quote_id=quote.id,
            city="Lahore",
            observed_price_pkr=Decimal("258000.00"),
            observed_unit="metric_ton",
            normalized_price_pkr=Decimal("258000.00"),
            normalized_unit="metric_ton",
            published_at=now_utc,
            collected_at=now_utc,
            verification_status="verified_quote",
            duplicate_fingerprint=f"fp_dlr_pg_{uuid.uuid4().hex[:8]}",
            observation_metadata={"project_id": str(proj_auth)},
        )
        session.add(obs_dealer)
        await session.flush()

        # Authorized Project Query
        res_auth = await bridge.resolve_material_rate_query("Steel in Lahore", db=session, project_id=proj_auth)
        assert any(i.observation_id == str(obs_dealer.id) for i in res_auth.evidence_items), "Authorized project should retrieve quote"
        print("-> [PASSED] Authorized project successfully retrieves own dealer quote.")

        # Foreign Project Query
        res_foreign = await bridge.resolve_material_rate_query("Steel in Lahore", db=session, project_id=proj_foreign)
        assert not any(i.observation_id == str(obs_dealer.id) for i in res_foreign.evidence_items), "Foreign project retrieved quote"
        print("-> [PASSED] Foreign project is strictly blocked from private dealer quote.")

        # Anonymous Query
        res_anon = await bridge.resolve_material_rate_query("Steel in Lahore", db=session, project_id=None)
        assert not any(i.observation_id == str(obs_dealer.id) for i in res_anon.evidence_items), "Anonymous retrieved quote"
        print("-> [PASSED] Anonymous query is strictly blocked from private dealer quote.")

        # Rollback all temporary fixtures cleanly
        await session.rollback()

        # ----------------------------------------------------------------------
        # TEST 6: APPEND-ONLY IMMUTABILITY TRIGGER TEST
        # ----------------------------------------------------------------------
        print("\n--- TEST 6: Append-Only Immutability Trigger Protection ---")
        try:
            await session.execute(text("DELETE FROM material_rate_observations WHERE id = :id"), {"id": obs_sample_id})
            assert False, "Trigger failed to block DELETE!"
        except Exception as e:
            assert "material_rate_observations table is strictly append-only" in str(e)
            print("-> [PASSED] trg_protect_immutable_observations strictly blocks DELETE.")
        await session.rollback()

    await engine.dispose()
    print("\n" + "=" * 80)
    print("ALL 6 POSTGRESQL 17 LIVE VERIFICATION AUDIT TESTS PASSED WITH ZERO DEFECTS!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
