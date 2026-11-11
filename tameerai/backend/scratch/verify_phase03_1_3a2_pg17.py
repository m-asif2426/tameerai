"""
TameerAI - Phase 03.1.3A.2 Comprehensive PostgreSQL 17 Verification Script
Tests all 5 tasks against the live PostgreSQL 17 database on port 5433:
1. PBS Monthly vs Weekly Period Granularity (Historical Service)
2. PBS Date Attribution Reconciliation (Observation 47b2ed20)
3. Grade 60 Observation Count Reconciliation (18 vs 17 in Lahore)
4. Full Pytest Accounting Reconciliation (41 modules, 768 tests)
5. Dealer Security Tenancy 10-Condition PostgreSQL Verification
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import os
import sys
import uuid
from typing import Dict, Any, List

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_, func

from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
)
from app.services.material_rates.identity_resolver import (
    PRODUCT_CODE_STEEL_G40,
    PRODUCT_CODE_STEEL_G60,
    KNOWN_PRODUCT_ID_G40,
    KNOWN_PRODUCT_ID_G60,
    centralized_identity_resolver,
    detect_observation_steel_grade,
)
from app.services.material_rates.historical_service import HistoricalMarketIntelligenceService
from app.services.material_rates.canonical_engine import CanonicalMarketRateEngine

PG17_URL = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"


async def verify_task1(session: AsyncSession) -> Dict[str, Any]:
    print("\n--- TASK 1: PBS Monthly vs Weekly Period Granularity ---")
    hist_service = HistoricalMarketIntelligenceService()

    # Query Grade 40 (PBS data) with interval='weekly'
    res_g40_weekly = await hist_service.get_price_history(
        session,
        product_code=PRODUCT_CODE_STEEL_G40,
        city="Karachi",
        interval="weekly",
    )
    print(f"G40 Weekly interval query data points count: {len(res_g40_weekly['data_points'])}")
    for dp in res_g40_weekly["data_points"]:
        print(f"  G40 Period key: {dp['period']} | Median: PKR {dp['median_pkr']} | Count: {dp['observation_count']}")

    # Query Grade 40 with interval='monthly'
    res_g40_monthly = await hist_service.get_price_history(
        session,
        product_code=PRODUCT_CODE_STEEL_G40,
        city="Karachi",
        interval="monthly",
    )
    print(f"G40 Monthly interval query data points count: {len(res_g40_monthly['data_points'])}")
    for dp in res_g40_monthly["data_points"]:
        print(f"  G40 Period key: {dp['period']} | Median: PKR {dp['median_pkr']} | Count: {dp['observation_count']}")

    # Query Grade 60 (SteelRateToday daily commercial quotes) with interval='weekly'
    res_g60_weekly = await hist_service.get_price_history(
        session,
        product_code=PRODUCT_CODE_STEEL_G60,
        city="Lahore",
        interval="weekly",
    )
    print(f"G60 Weekly interval query data points count: {len(res_g60_weekly['data_points'])}")
    for dp in res_g60_weekly["data_points"]:
        print(f"  G60 Period key: {dp['period']} | Median: PKR {dp['median_pkr']} | Count: {dp['observation_count']}")

    # Assertions
    assert len(res_g40_weekly["data_points"]) > 0, "Expected G40 weekly data points"
    assert res_g40_weekly["data_points"][0]["period"] == "2026-10", (
        f"Expected '2026-10', got {res_g40_weekly['data_points'][0]['period']}"
    )
    assert res_g60_weekly["data_points"][0]["period"].startswith("2026-W"), (
        f"Expected ISO week format, got {res_g60_weekly['data_points'][0]['period']}"
    )
    print("[PASS] Task 1: Source-frequency-aware bucketing verified!")
    return {
        "g40_weekly_period": res_g40_weekly["data_points"][0]["period"],
        "g40_monthly_period": res_g40_monthly["data_points"][0]["period"],
        "g60_weekly_period": res_g60_weekly["data_points"][0]["period"],
    }


async def verify_task2(session: AsyncSession) -> Dict[str, Any]:
    print("\n--- TASK 2: PBS Date Attribution Reconciliation ---")
    obs_id = uuid.UUID("47b2ed20-47a1-4c38-8fa3-d4a54273a98a")
    obs = await session.get(MaterialRateObservation, obs_id)
    assert obs is not None, f"Observation {obs_id} not found in PG17!"

    src = await session.get(MaterialRateSource, obs.source_id)

    # Reference evaluation time: 2026-11-08 19:30:00 UTC
    eval_now = datetime(2026, 11, 8, 19, 30, 0, tzinfo=timezone.utc)

    semantics = centralized_identity_resolver.resolve_observation_date_semantics(
        obs, source=src, now=eval_now, ttl_days=45.0
    )

    print(f"Observation ID: {obs.id}")
    print(f"Raw Spec / Item: {obs.observation_metadata.get('item_name')}")
    print(f"Stored published_at (DB Column): {semantics['stored_published_at']} (Import artifact)")
    print(f"Stored collected_at (DB Column): {semantics['stored_collected_at']}")
    print(f"Stored survey_reference_period (JSONB): {semantics['stored_survey_reference_period']}")
    print(f"Stored survey_date (JSONB): {semantics['stored_survey_date']}")
    print(f"Stored official_publication_date (JSONB): {semantics['stored_official_publication_date']}")
    print(f"Query-derived survey_reference_period: {semantics['query_derived_survey_reference_period']}")
    print(f"Query-derived effective_market_date: {semantics['query_derived_effective_market_date']}")
    print(f"Derivation Method: {semantics['market_date_derivation_method']}")
    print(f"Age as of Nov 8, 2026: {semantics['age_days']} days (TTL = {semantics['ttl_days']} days)")
    print(f"Freshness status: {'FRESH (Eligible)' if semantics['is_fresh'] else 'STALE (Excluded)'}")

    assert semantics["stored_survey_reference_period"] is None, "Stored survey_reference_period must be None"
    assert semantics["query_derived_survey_reference_period"] == "October, 2026"
    assert semantics["query_derived_effective_market_date"] == "2026-10-31T23:59:59+00:00"
    assert semantics["is_fresh"] is True
    print("[PASS] Task 2: PBS date attribution semantics verified!")
    return semantics


async def verify_task3(session: AsyncSession) -> Dict[str, Any]:
    print("\n--- TASK 3: Grade 60 Observation Count Reconciliation (Lahore) ---")

    # Get G40 and G60 products
    g40_prod = await centralized_identity_resolver.get_canonical_product(session, PRODUCT_CODE_STEEL_G40)
    g60_prod = await centralized_identity_resolver.get_canonical_product(session, PRODUCT_CODE_STEEL_G60)

    # Query all steel candidate observations in Lahore stored under STEEL_REBAR_G60 with normalized_price >= 100000 (ton basis)
    stmt = (
        select(MaterialRateObservation, MaterialRateSource)
        .join(MaterialRateSource, MaterialRateObservation.source_id == MaterialRateSource.id)
        .where(
            MaterialRateObservation.city == "Lahore",
            MaterialRateObservation.product_id == g60_prod.id,
            MaterialRateObservation.normalized_price_pkr >= Decimal("100000.00"),
            MaterialRateObservation.dealer_quote_id.is_(None),
            MaterialRateObservation.verification_status.in_(["indicative", "verified_market_range"]),
        )
        .order_by(MaterialRateObservation.created_at.asc())
    )
    res = await session.execute(stmt)
    rows = res.all()

    print(f"Total Lahore Steel Candidate Observations stored under STEEL_REBAR_G60: {len(rows)}")

    candidates = []
    g60_eligible_count = 0
    g40_eligible_count = 0

    for obs, src in rows:
        detected_grade = detect_observation_steel_grade(obs)
        is_g40 = centralized_identity_resolver.is_observation_eligible_for_product(
            obs, PRODUCT_CODE_STEEL_G40, stored_product_code="STEEL_REBAR_G60"
        )
        is_g60 = centralized_identity_resolver.is_observation_eligible_for_product(
            obs, PRODUCT_CODE_STEEL_G60, stored_product_code="STEEL_REBAR_G60"
        )

        exclusion_reason = None
        if not is_g60:
            exclusion_reason = f"Detected as {detected_grade} from raw spec ('{obs.observation_metadata.get('raw_specification') or obs.observation_metadata.get('item_name')}'); strictly isolated from Grade 60"

        if is_g60:
            g60_eligible_count += 1
        if is_g40:
            g40_eligible_count += 1

        rec = {
            "uuid": str(obs.id),
            "source_code": src.code,
            "raw_spec": obs.observation_metadata.get("raw_specification") or obs.observation_metadata.get("item_name") or obs.observation_metadata.get("brand") or "N/A",
            "price_pkr": float(obs.normalized_price_pkr),
            "stored_product_id": str(obs.product_id),
            "detected_grade": detected_grade or "Grade 60 (default)",
            "is_g60_eligible": is_g60,
            "is_g40_eligible": is_g40,
            "exclusion_reason": exclusion_reason,
        }
        candidates.append(rec)
        print(f"  [{rec['uuid'][:8]}] {rec['source_code'][:22]} | {rec['raw_spec'][:25]} | PKR {rec['price_pkr']} | G60={rec['is_g60_eligible']} | G40={rec['is_g40_eligible']} | {rec['exclusion_reason'] or 'ADMITTED TO G60'}")

    print(f"\nSummary: Total Candidates: {len(candidates)} | G60 Eligible: {g60_eligible_count} | G40 Eligible: {g40_eligible_count}")
    assert len(candidates) == 18, f"Expected 18 candidate records, got {len(candidates)}"
    assert g60_eligible_count == 17, f"Expected 17 Grade 60 eligible records, got {g60_eligible_count}"
    assert g40_eligible_count == 1, f"Expected 1 Grade 40 eligible record, got {g40_eligible_count}"

    print("[PASS] Task 3: Grade 60 observation count 18 vs 17 mathematically proven!")
    return {
        "total_candidates": len(candidates),
        "g60_eligible_count": g60_eligible_count,
        "g40_eligible_count": g40_eligible_count,
        "candidates": candidates,
    }


async def verify_task4() -> Dict[str, Any]:
    print("\n--- TASK 4: Full Pytest Accounting Reconciliation ---")
    import pytest

    # Run pytest collection using subprocess or pytest collector
    import subprocess
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd="D:\\new idea project\\tameerai\\backend", capture_output=True, text=True)

    lines = proc.stdout.splitlines()
    test_nodes = [l for l in lines if "::" in l]
    total_collected = len(test_nodes)

    module_counts: Dict[str, int] = {}
    for node in test_nodes:
        mod = node.split("::")[0].replace("\\", "/")
        module_counts[mod] = module_counts.get(mod, 0) + 1

    sorted_modules = sorted(module_counts.items(), key=lambda x: -x[1])
    print(f"Total test modules collected: {len(sorted_modules)}")
    print(f"Total test nodes collected: {total_collected}")
    sum_check = sum(cnt for _, cnt in sorted_modules)
    print(f"Sum of module test counts: {sum_check}")

    for mod, cnt in sorted_modules:
        print(f"  {mod}: {cnt}")

    assert len(sorted_modules) == 41, f"Expected 41 modules, got {len(sorted_modules)}"
    assert total_collected == 768, f"Expected 768 tests, got {total_collected}"
    assert sum_check == 768, f"Mathematical sum must be 768, got {sum_check}"

    print("[PASS] Task 4: Complete Pytest inventory mathematically verified at 768 tests!")
    return {
        "total_modules": len(sorted_modules),
        "total_tests": total_collected,
        "module_breakdown": dict(sorted_modules),
    }


async def verify_task5(session: AsyncSession) -> Dict[str, Any]:
    print("\n--- TASK 5: Dealer Security Tenancy 10-Condition PostgreSQL Verification ---")

    # We perform these tests inside a transaction and roll back at the end
    proj_a = uuid.uuid4()
    proj_b = uuid.uuid4()
    dealer_user_id = uuid.uuid4()

    # Pre-fetch or create a test dealer source
    src_stmt = select(MaterialRateSource).where(MaterialRateSource.source_type == "dealer_network")
    src = (await session.execute(src_stmt)).scalars().first()
    if not src:
        src = MaterialRateSource(
            id=uuid.uuid4(),
            code=f"SRC-DEALER-{uuid.uuid4().hex[:6]}",
            name="Dealer Source",
            source_type="dealer_network",
            permission_status="approved_direct",
            reliability_tier="verified_partner",
            refresh_cadence="daily",
            freshness_ttl_days=7,
        )
        session.add(src)

    g60_prod = (await session.execute(select(MaterialRateProduct).where(MaterialRateProduct.code == PRODUCT_CODE_STEEL_G60))).scalars().first()

    # Create active verified dealer
    active_dealer = MaterialRateDealer(
        id=uuid.uuid4(),
        dealer_code=f"DLR-ACT-{uuid.uuid4().hex[:6]}",
        user_id=None,
        business_name="Active Verified Steel Traders",
        city="Lahore",
        is_active=True,
        verification_state="verified",
    )
    # Create inactive dealer
    inactive_dealer = MaterialRateDealer(
        id=uuid.uuid4(),
        dealer_code=f"DLR-INA-{uuid.uuid4().hex[:6]}",
        user_id=None,
        business_name="Inactive Steel Traders",
        city="Lahore",
        is_active=False,
        verification_state="verified",
    )
    # Create unverified dealer
    unverified_dealer = MaterialRateDealer(
        id=uuid.uuid4(),
        dealer_code=f"DLR-UNV-{uuid.uuid4().hex[:6]}",
        user_id=None,
        business_name="Unverified Steel Traders",
        city="Lahore",
        is_active=True,
        verification_state="unverified",
    )
    session.add_all([active_dealer, inactive_dealer, unverified_dealer])
    await session.flush()

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=5)
    past = now - timedelta(days=2)

    # 1. Valid Quote for Project A
    quote_valid_a = MaterialRateDealerQuote(
        id=uuid.uuid4(),
        dealer_id=active_dealer.id,
        product_id=g60_prod.id,
        city="Lahore",
        quoted_price_pkr=Decimal("260000.00"),
        quoted_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        quotation_date=now,
        status="verified",
        valid_until=future,
    )
    quote_valid_a.quotation_metadata = {"project_id": str(proj_a)}

    # 2. Expired Quote for Project A
    quote_expired = MaterialRateDealerQuote(
        id=uuid.uuid4(),
        dealer_id=active_dealer.id,
        product_id=g60_prod.id,
        city="Lahore",
        quoted_price_pkr=Decimal("260000.00"),
        quoted_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        quotation_date=past,
        status="verified",
        valid_until=past,
    )
    quote_expired.quotation_metadata = {"project_id": str(proj_a)}

    # 3. Inactive Dealer Quote
    quote_inactive_dealer = MaterialRateDealerQuote(
        id=uuid.uuid4(),
        dealer_id=inactive_dealer.id,
        product_id=g60_prod.id,
        city="Lahore",
        quoted_price_pkr=Decimal("260000.00"),
        quoted_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        quotation_date=now,
        status="verified",
        valid_until=future,
    )
    quote_inactive_dealer.quotation_metadata = {"project_id": str(proj_a)}

    # 4. Unverified Dealer Quote
    quote_unverified_dealer = MaterialRateDealerQuote(
        id=uuid.uuid4(),
        dealer_id=unverified_dealer.id,
        product_id=g60_prod.id,
        city="Lahore",
        quoted_price_pkr=Decimal("260000.00"),
        quoted_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        quotation_date=now,
        status="verified",
        valid_until=future,
    )
    quote_unverified_dealer.quotation_metadata = {"project_id": str(proj_a)}

    # 5. Unknown Project Ownership Quote
    quote_unknown_proj = MaterialRateDealerQuote(
        id=uuid.uuid4(),
        dealer_id=active_dealer.id,
        product_id=g60_prod.id,
        city="Lahore",
        quoted_price_pkr=Decimal("260000.00"),
        quoted_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        quotation_date=now,
        status="verified",
        valid_until=future,
    )
    quote_unknown_proj.quotation_metadata = {}
    session.add_all([quote_valid_a, quote_expired, quote_inactive_dealer, quote_unverified_dealer, quote_unknown_proj])
    await session.flush()

    # Create observations corresponding to each test scenario
    # C1: Project A valid quote accessed by Project A
    obs_c1 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=quote_valid_a.id,
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c1_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_a)},
    )
    # C4: Missing quotation link (dealer observation without dealer_quote_id)
    obs_c4 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=None,
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c4_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_a)},
    )
    # C5: Non-existent quotation link
    obs_c5 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=uuid.uuid4(),  # Does not exist
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c5_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_a)},
    )
    # C6: Unknown project ownership
    obs_c6 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=quote_unknown_proj.id,
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c6_{uuid.uuid4().hex[:8]}",
        observation_metadata={},
    )
    # C7: Conflicting project ownership
    obs_c7 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=quote_valid_a.id,  # Owned by proj_a
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c7_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_b)},  # Claims proj_b!
    )
    # C8: Expired quotation
    obs_c8 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=quote_expired.id,
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c8_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_a)},
    )
    # C9: Inactive dealer
    obs_c9 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=quote_inactive_dealer.id,
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c9_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_a)},
    )
    # C10: Unverified dealer
    obs_c10 = MaterialRateObservation(
        id=uuid.uuid4(),
        source_id=src.id,
        product_id=g60_prod.id,
        dealer_quote_id=quote_unverified_dealer.id,
        city="Lahore",
        observed_price_pkr=Decimal("260000.00"),
        observed_unit="metric_ton",
        normalized_price_pkr=Decimal("260000.00"),
        normalized_unit="metric_ton",
        published_at=now,
        collected_at=now,
        verification_status="verified_quote",
        duplicate_fingerprint=f"fp_test_c10_{uuid.uuid4().hex[:8]}",
        observation_metadata={"project_id": str(proj_a)},
    )
    # No need to insert test observations into DB (which would fail on FK for C5 or pollute DB)
    # The quotes and dealers are in the DB transaction, and the validator queries DB for them.

    # Now test all 10 conditions:
    results = {}

    # 1. Project A valid quote accessed by Project A -> ADMITTED
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c1, src, requesting_project_id=proj_a
    )
    print(f"Condition 1 (Proj A valid quote -> Proj A caller): ok={ok}, reason={reason}")
    assert ok is True and reason is None
    results["condition_1"] = {"ok": ok, "reason": reason or "AUTHORIZED"}

    # 2. Project A valid quote accessed by Project B -> QUARANTINED (cross_project_isolation)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c1, src, requesting_project_id=proj_b
    )
    print(f"Condition 2 (Proj A valid quote -> Proj B caller): ok={ok}, reason={reason}")
    assert ok is False and reason == "cross_project_isolation"
    results["condition_2"] = {"ok": ok, "reason": reason}

    # 3. Project A valid quote accessed by Anonymous -> QUARANTINED (anonymous_access_forbidden)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c1, src, requesting_project_id=None
    )
    print(f"Condition 3 (Proj A valid quote -> Anonymous caller): ok={ok}, reason={reason}")
    assert ok is False and reason == "anonymous_access_forbidden"
    results["condition_3"] = {"ok": ok, "reason": reason}

    # 4. Dealer quote missing quotation link -> QUARANTINED (missing_quotation_link)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c4, src, requesting_project_id=proj_a
    )
    print(f"Condition 4 (Missing quotation link): ok={ok}, reason={reason}")
    assert ok is False and reason == "missing_quotation_link"
    results["condition_4"] = {"ok": ok, "reason": reason}

    # 5. Non-existent quote ID -> QUARANTINED (unverified_dealer_quotation)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c5, src, requesting_project_id=proj_a
    )
    print(f"Condition 5 (Nonexistent quote ID): ok={ok}, reason={reason}")
    assert ok is False and reason == "unverified_dealer_quotation"
    results["condition_5"] = {"ok": ok, "reason": reason}

    # 6. Unknown project ownership -> QUARANTINED (unknown_project_ownership)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c6, src, requesting_project_id=proj_a
    )
    print(f"Condition 6 (Unknown project ownership): ok={ok}, reason={reason}")
    assert ok is False and reason == "unknown_project_ownership"
    results["condition_6"] = {"ok": ok, "reason": reason}

    # 7. Conflicting project ownership -> QUARANTINED (conflicting_project_ownership)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c7, src, requesting_project_id=proj_a
    )
    print(f"Condition 7 (Conflicting project ownership): ok={ok}, reason={reason}")
    assert ok is False and reason == "conflicting_project_ownership"
    results["condition_7"] = {"ok": ok, "reason": reason}

    # 8. Expired dealer quotation -> QUARANTINED (expired_dealer_quotation)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c8, src, requesting_project_id=proj_a
    )
    print(f"Condition 8 (Expired quotation): ok={ok}, reason={reason}")
    assert ok is False and reason == "expired_dealer_quotation"
    results["condition_8"] = {"ok": ok, "reason": reason}

    # 9. Inactive dealer -> QUARANTINED (inactive_dealer)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c9, src, requesting_project_id=proj_a
    )
    print(f"Condition 9 (Inactive dealer): ok={ok}, reason={reason}")
    assert ok is False and reason == "inactive_dealer"
    results["condition_9"] = {"ok": ok, "reason": reason}

    # 10. Unverified dealer -> QUARANTINED (unverified_dealer)
    ok, reason = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, obs_c10, src, requesting_project_id=proj_a
    )
    print(f"Condition 10 (Unverified dealer): ok={ok}, reason={reason}")
    assert ok is False and reason == "unverified_dealer"
    results["condition_10"] = {"ok": ok, "reason": reason}

    # Bonus: Public PBS observation global access check
    pbs_obs_id = uuid.UUID("47b2ed20-47a1-4c38-8fa3-d4a54273a98a")
    pbs_obs = await session.get(MaterialRateObservation, pbs_obs_id)
    pbs_src = await session.get(MaterialRateSource, pbs_obs.source_id)

    ok_anon, _ = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, pbs_obs, pbs_src, requesting_project_id=None
    )
    ok_proj_a, _ = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, pbs_obs, pbs_src, requesting_project_id=proj_a
    )
    ok_proj_b, _ = await centralized_identity_resolver.validate_dealer_quotation_tenancy(
        session, pbs_obs, pbs_src, requesting_project_id=proj_b
    )
    print(f"Public PBS access: Anonymous={ok_anon}, Proj A={ok_proj_a}, Proj B={ok_proj_b}")
    assert ok_anon is True and ok_proj_a is True and ok_proj_b is True

    # Roll back transaction so test records do not persist
    await session.rollback()
    print("[PASS] Task 5: All 10 dealer tenancy conditions and public PBS access verified on PostgreSQL 17!")
    return results


async def main():
    engine = create_async_engine(PG17_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("================================================================================")
    print("TAMEERAI PHASE 03.1.3A.2 - LIVE POSTGRESQL 17 FINAL VERIFICATION")
    print("================================================================================")

    async with async_session() as session:
        t1_res = await verify_task1(session)
        t2_res = await verify_task2(session)
        t3_res = await verify_task3(session)
        t4_res = await verify_task4()
        t5_res = await verify_task5(session)

    await engine.dispose()
    print("\n================================================================================")
    print("ALL 5 TASKS SUCCESSFULLY VERIFIED ON POSTGRESQL 17!")
    print("================================================================================")

if __name__ == "__main__":
    asyncio.run(main())
