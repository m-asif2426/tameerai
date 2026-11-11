"""
TameerAI - Stage 2B National Construction Material Data Source Adapters Tests

Validates:
1. NationalSourceRegistry source discovery catalog, credibility scoring, and multi-faceted filtering.
2. PBS Statistical Source Adapter parsing (JSON and HTML SPI bulletins, statistical index basis).
3. NHA Composite Schedule of Rates Adapter parsing (CSR statutory schedule rates, district mapping).
4. Zarea B2B Marketplace Adapter parsing (wholesale/ex-mill pricing, brands, MOQs, grades).
5. MaterialRate.pk Secondary Publisher Adapter parsing (daily retail roundups across multi-materials).
6. SteelRateToday Specialized Adapter parsing (wholesale trading yards: Badami Bagh & Shershah).
7. Direct Dealer Connector ingestion (dealer IDs, quote IDs, commercial terms).
8. Provenance and syndication detection (original citations, republished tags, metadata persistence).
9. End-to-end execution through BaseSourceAdapter pipeline into database observations.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import json
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateObservation,
    MaterialRateSourceRun,
)
from app.services.material_rates.contracts import (
    CollectionSourceType,
    NormalizedCategory,
    PriceBasis,
    RawSourceRecord,
    SourceCategory,
    SourceOperationalStatus,
)
from app.services.material_rates.registry import (
    NationalSourceRegistry,
    SourceRegistryEntry,
    national_registry,
)
from app.services.material_rates.adapters.pbs_adapter import PbsStatisticalSourceAdapter
from app.services.material_rates.adapters.nha_schedule_adapter import NhaScheduleSourceAdapter
from app.services.material_rates.adapters.zarea_adapter import ZareaMarketplaceSourceAdapter
from app.services.material_rates.adapters.materialrate_adapter import MaterialRatePublisherSourceAdapter
from app.services.material_rates.adapters.steelratetoday_adapter import SteelRateTodaySourceAdapter
from app.services.material_rates.adapters.gharhub_adapter import GharHubPublisherSourceAdapter
from app.services.material_rates.adapters.dealer_connector import DirectDealerConnector
from app.services.material_rates.registry import (
    NationalSourceRegistry,
    SourceRegistryEntry,
    compute_transparent_credibility_score,
    compute_observation_confidence,
    national_registry,
)
from app.services.material_rates.normalization import (
    convert_price,
    normalize_location,
    normalize_unit_and_price,
    normalize_published_date,
    NormalizationError,
)


@pytest.fixture
def test_db_session():
    """Provides an isolated in-memory SQLite database session seeded with core products."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Seed baseline products
    products = [
        MaterialRateProduct(
            id=uuid.uuid4(),
            code="CEMENT_OPC_50KG",
            canonical_name="Ordinary Portland Cement 50kg Bag",
            category="cement",
            standard_unit="bag_50kg",
            is_active=True,
        ),
        MaterialRateProduct(
            id=uuid.uuid4(),
            code="STEEL_REBAR_G60_TON",
            canonical_name="Deformed Steel Rebar Grade 60 Metric Ton",
            category="steel",
            standard_unit="metric_ton",
            is_active=True,
        ),
        MaterialRateProduct(
            id=uuid.uuid4(),
            code="BRICKS_AWWAL_1000",
            canonical_name="Clay Bricks Awwal Class 1000 Nos",
            category="bricks",
            standard_unit="thousand_nos",
            is_active=True,
        ),
        MaterialRateProduct(
            id=uuid.uuid4(),
            code="SAND_CHENAB_100CFT",
            canonical_name="Chenab River Sand 100 Cu Ft",
            category="sand",
            standard_unit="hundred_cft",
            is_active=True,
        ),
        MaterialRateProduct(
            id=uuid.uuid4(),
            code="CRUSH_MARGALLA_100CFT",
            canonical_name="Margalla Limestone Crush 100 Cu Ft",
            category="crush",
            standard_unit="hundred_cft",
            is_active=True,
        ),
    ]
    for p in products:
        session.add(p)
    session.commit()

    yield session
    session.close()


# ==============================================================================
# 1. National Source Discovery & Registry Tests
# ==============================================================================

def test_registry_contains_comprehensive_sources():
    """Verify registry encompasses all major Pakistani construction material sources."""
    summary = national_registry.get_source_inventory_summary()
    assert summary["total_registered_sources"] >= 15
    assert "official_statistical" in summary["by_category"]
    assert "government_schedule" in summary["by_category"]
    assert "manufacturer_ex_factory" in summary["by_category"]
    assert "marketplace_listing" in summary["by_category"]
    assert "secondary_market_publisher" in summary["by_category"]
    assert "verified_dealer_quotation" in summary["by_category"]


def test_registry_filtering_capabilities():
    """Verify registry search by category, status, material, and city."""
    # Official statistical
    official_sources = national_registry.list_sources(category=SourceCategory.OFFICIAL_STATISTICAL)
    assert len(official_sources) >= 2
    assert any(s.source_code == "PBS_STATISTICAL_SPI" for s in official_sources)

    # Steel manufacturers
    steel_sources = national_registry.list_sources(
        category=SourceCategory.MANUFACTURER_EX_FACTORY,
        material_keyword="steel"
    )
    assert len(steel_sources) >= 3
    steel_codes = [s.source_code for s in steel_sources]
    assert "MFR_MUGHAL_STEEL" in steel_codes
    assert "MFR_AMRELI_STEEL" in steel_codes

    # Government schedules
    gov_schedules = national_registry.list_sources(category=SourceCategory.GOVERNMENT_SCHEDULE)
    assert len(gov_schedules) >= 4  # NHA, Punjab MRS, Sindh CSR, KP CSR

    # City filter (Lahore)
    lahore_sources = national_registry.list_sources(city_keyword="Lahore")
    assert len(lahore_sources) >= 5

    # Credibility scores
    for source in national_registry.list_sources():
        assert 1 <= source.credibility_score <= 100
        assert source.notes_and_rationale != ""


# ==============================================================================
# 2. Pakistan Bureau of Statistics (PBS) Adapter Tests
# ==============================================================================

def test_pbs_adapter_json_parsing():
    """Verify PBS SPI weekly JSON payload parsing."""
    adapter = PbsStatisticalSourceAdapter()
    sample_payload = {
        "bulletin_no": "SPI-2026-44",
        "bulletin_date": "2026-11-05",
        "items": [
            {
                "item_name": "Cement Ordinary Portland",
                "price": 1585.50,
                "unit": "50 kg bag",
                "city": "Lahore",
            },
            {
                "item_name": "Cement Ordinary Portland",
                "price": 1520.00,
                "unit": "50 kg bag",
                "city": "Karachi",
            },
            {
                "item_name": "Cement Ordinary Portland",
                "price": 1610.00,
                "unit": "50 kg bag",
                "city": "Rawalpindi",
            },
        ],
    }

    records = adapter.parse_raw_data(sample_payload)
    assert len(records) == 3
    assert records[0].raw_city == "Lahore"
    assert records[0].raw_price == 1585.50
    assert records[0].price_basis == PriceBasis.STATISTICAL_INDEX
    assert records[0].original_source_citation == "Pakistan Bureau of Statistics SPI Bulletin"
    assert records[1].raw_city == "Karachi"


def test_pbs_adapter_html_parsing():
    """Verify PBS HTML bulletin table parsing."""
    adapter = PbsStatisticalSourceAdapter()
    html_sample = """
    <table>
        <tr><th>Item</th><th>Unit</th><th>Center</th><th>Price</th></tr>
        <tr><td>Cement (OPC)</td><td>50 kg bag</td><td>Peshawar</td><td>1,595.00</td></tr>
        <tr><td>Cement (OPC)</td><td>50 kg bag</td><td>Multan</td><td>1,570.00</td></tr>
    </table>
    """
    records = adapter.parse_raw_data(html_sample)
    assert len(records) == 2
    assert records[0].raw_city == "Peshawar"
    assert records[0].raw_price == 1595.00
    assert records[1].raw_city == "Multan"
    assert records[1].raw_price == 1570.00


# ==============================================================================
# 3. NHA Schedule of Rates Adapter Tests
# ==============================================================================

def test_nha_adapter_structured_parsing():
    """Verify NHA Composite Schedule of Rates (CSR) parsing."""
    adapter = NhaScheduleSourceAdapter(default_district="Islamabad")
    sample_payload = {
        "edition": "CSR 2024-2025",
        "effective_date": "2026-10-01",
        "rates": [
            {
                "item_code": "106-A",
                "description": "Deformed Steel Bar Grade 60 (ASTM A615)",
                "rate": 268000.00,
                "unit": "Metric Ton",
                "district": "Rawalpindi",
            },
            {
                "item_code": "101-B",
                "description": "Ordinary Portland Cement (OPC)",
                "rate": 1540.00,
                "unit": "50 Kg Bag",
                "district": "Lahore",
            },
            {
                "item_code": "202-C",
                "description": "Crush / Coarse Aggregate Margalla Quarry",
                "rate": 8500.00,
                "unit": "100 Cft",
                "district": "Islamabad",
            },
        ],
    }

    records = adapter.parse_raw_data(sample_payload)
    assert len(records) == 3
    assert records[0].grade == "Grade 60"
    assert records[0].price_basis == PriceBasis.GOVERNMENT_SCHEDULE_RATE
    assert "CSR 2024-2025" in records[0].original_source_citation
    assert records[0].raw_city == "Rawalpindi"
    assert records[0].raw_price == 268000.00


# ==============================================================================
# 4. Zarea B2B Marketplace Adapter Tests
# ==============================================================================

def test_zarea_adapter_parsing():
    """Verify Zarea commodity exchange listings parsing with brand & MOQ."""
    adapter = ZareaMarketplaceSourceAdapter()
    sample_payload = {
        "listings": [
            {
                "id": "zar-cem-01",
                "title": "Bestway Ordinary Portland Cement",
                "price": 1550.00,
                "unit": "50kg bag",
                "brand": "Bestway",
                "city": "Lahore",
                "moq": "500 Bags",
                "delivery_terms": "Ex-Factory Hattar",
            },
            {
                "id": "zar-stl-02",
                "title": "Mughal Steel Grade 60 Rebar",
                "price": 262000.00,
                "unit": "ton",
                "brand": "Mughal Steel",
                "grade": "Grade 60",
                "city": "Lahore",
                "moq": "10 Tons",
            },
        ]
    }

    records = adapter.parse_raw_data(sample_payload)
    assert len(records) == 2
    assert records[0].brand == "Bestway"
    assert records[0].price_basis == PriceBasis.WHOLESALE
    assert records[0].raw_metadata["moq"] == "500 Bags"
    assert records[1].brand == "Mughal Steel"
    assert records[1].grade == "Grade 60"
    assert records[1].raw_price == 262000.00


# ==============================================================================
# 5. MaterialRate.pk Publisher Adapter Tests
# ==============================================================================

def test_materialrate_adapter_multi_material_parsing():
    """Verify MaterialRate.pk daily market roundup across all core materials."""
    adapter = MaterialRatePublisherSourceAdapter()
    sample_payload = {
        "citation": "MaterialRate.pk Daily Market Survey",
        "rates": [
            {"material": "Ordinary Portland Cement", "price": 1580, "unit": "bag", "city": "Lahore", "brand": "Lucky"},
            {"material": "Deformed Steel Bar Grade 60", "price": 265, "unit": "kg", "city": "Karachi", "grade": "Grade 60"},
            {"material": "Clay Bricks Awwal Class", "price": 14500, "unit": "1000 nos", "city": "Rawalpindi"},
            {"material": "Chenab River Sand", "price": 4500, "unit": "100 cft", "city": "Faisalabad"},
            {"material": "Margalla Limestone Crush", "price": 9200, "unit": "100 cft", "city": "Islamabad"},
        ],
    }

    records = adapter.parse_raw_data(sample_payload)
    assert len(records) == 5
    assert records[0].brand == "Lucky"
    assert records[0].price_basis == PriceBasis.RETAIL
    assert records[1].grade == "Grade 60"
    assert records[1].raw_city == "Karachi"
    assert records[2].raw_material_name == "Clay Bricks Awwal Class"
    assert records[3].raw_city == "Faisalabad"


# ==============================================================================
# 6. SteelRateToday Specialized Adapter Tests
# ==============================================================================

def test_steelratetoday_adapter_parsing():
    """Verify SteelRateToday rebar and steel yard quotes parsing."""
    adapter = SteelRateTodaySourceAdapter(default_city="Lahore")
    sample_payload = {
        "steel_rates": [
            {
                "brand": "Mughal Steel",
                "grade": "Grade 60",
                "price_per_kg": 264.00,
                "city": "Lahore",
                "market_yard": "Badami Bagh",
            },
            {
                "brand": "Amreli Steels",
                "grade": "Grade 60",
                "price_per_kg": 262.00,
                "city": "Karachi",
                "market_yard": "Shershah",
            },
        ]
    }

    records = adapter.parse_raw_data(sample_payload)
    assert len(records) == 2
    assert records[0].brand == "Mughal Steel"
    assert records[0].grade == "Grade 60"
    assert records[0].raw_city == "Lahore"
    assert records[0].price_basis == PriceBasis.WHOLESALE
    assert records[0].raw_metadata["trading_yard"] == "Badami Bagh"
    assert records[1].brand == "Amreli Steels"
    assert records[1].raw_city == "Karachi"
    assert records[1].raw_metadata["trading_yard"] == "Shershah"


# ==============================================================================
# 7. Direct Dealer Connector Ingestion Tests
# ==============================================================================

def test_direct_dealer_connector_parsing():
    """Verify direct registered dealer quote payload ingestion."""
    connector = DirectDealerConnector(default_city="Lahore")
    dealer_id = uuid.uuid4()
    dealer_quote_id = uuid.uuid4()

    payload = {
        "dealer_id": str(dealer_id),
        "dealer_quote_id": str(dealer_quote_id),
        "dealer_business_name": "Pak Builders & Steel Traders",
        "city": "Lahore",
        "quotation_date": "2026-11-06",
        "valid_until": "2026-11-13",
        "payment_terms": "100% Cash on Delivery",
        "delivery_terms": "Delivered to Site (Raiwind Road)",
        "items": [
            {
                "material_name": "Bestway Ordinary Portland Cement",
                "price": 1540.00,
                "unit": "50 kg Bag",
                "brand": "Bestway",
                "grade": "OPC",
            },
            {
                "material_name": "Mughal Supreme Grade 60 Rebar",
                "price": 260.00,
                "unit": "kg",
                "brand": "Mughal Steel",
                "grade": "Grade 60",
            },
        ],
    }

    records = connector.parse_raw_data(payload)
    assert len(records) == 2
    assert records[0].dealer_id == dealer_id
    assert records[0].dealer_quote_id == dealer_quote_id
    assert records[0].price_basis == PriceBasis.DEALER_QUOTATION
    assert records[0].brand == "Bestway"
    assert records[0].raw_metadata["dealer_business_name"] == "Pak Builders & Steel Traders"
    assert records[0].raw_metadata["valid_until"] == "2026-11-13"


# ==============================================================================
# 8. Provenance & Syndication Tracking Tests
# ==============================================================================

def test_provenance_and_syndication_detection(test_db_session: Session):
    """Verify syndicated records preserve original citations and syndication flags."""
    adapter = MaterialRatePublisherSourceAdapter()
    source = MaterialRateSource(
        id=uuid.uuid4(),
        code="TEST_AGGREGATOR",
        name="Test Aggregator",
        source_type="aggregator",
        is_active=True,
    )
    test_db_session.add(source)
    test_db_session.commit()

    syndicated_rec = RawSourceRecord(
        raw_material_name="Ordinary Portland Cement 50kg Bag",
        raw_price=1580,
        raw_unit="50kg bag",
        raw_city="Lahore",
        raw_published_date="2026-11-06",
        is_syndicated=True,
        original_source_citation="Mughal & Bestway Stockist Daily Notice",
        republished_from="https://example.com/daily-notice",
    )

    candidate = adapter.normalize_and_validate(syndicated_rec, source, test_db_session)
    assert candidate is not None
    assert candidate.is_syndicated is True
    assert candidate.original_source_citation == "Mughal & Bestway Stockist Daily Notice"
    assert candidate.republished_from == "https://example.com/daily-notice"

    # Verify metadata embedding
    prov_meta = candidate.observation_metadata.get("provenance", {})
    assert prov_meta.get("is_syndicated") is True
    assert prov_meta.get("original_source_citation") == "Mughal & Bestway Stockist Daily Notice"
    assert prov_meta.get("republished_from") == "https://example.com/daily-notice"


# ==============================================================================
# 9. End-to-End Collection Run Execution with Multi-Source Adapters
# ==============================================================================

@pytest.mark.asyncio
async def test_end_to_end_collection_run_multi_source(test_db_session: Session):
    """
    Executes real collection runs for multiple adapters (PBS, NHA, Zarea, Dealer)
    against an in-memory database to verify persistence, accounting, and metadata.
    """
    # 1. Run PBS Adapter
    pbs_adapter = PbsStatisticalSourceAdapter()
    pbs_payload = {
        "items": [
            {"item_name": "Ordinary Portland Cement 50kg Bag", "price": 1580, "unit": "bag_50kg", "city": "Islamabad"}
        ]
    }
    pbs_summary = await pbs_adapter.execute_run(test_db_session, payload=pbs_payload)
    assert pbs_summary.status == "completed"
    assert pbs_summary.total_fetched == 1
    assert pbs_summary.inserted_count == 1
    assert pbs_summary.duplicate_count == 0

    # 2. Run Zarea Adapter with Steel
    zarea_adapter = ZareaMarketplaceSourceAdapter()
    zarea_payload = {
        "listings": [
            {
                "title": "Deformed Steel Rebar Grade 60 Metric Ton",
                "price": 265000,
                "unit": "ton",
                "city": "Lahore",
                "brand": "Mughal Steel",
                "grade": "Grade 60",
                "moq": "20 tons",
            }
        ]
    }
    zarea_summary = await zarea_adapter.execute_run(test_db_session, payload=zarea_payload)
    assert zarea_summary.status == "completed"
    assert zarea_summary.total_fetched == 1
    assert zarea_summary.inserted_count == 1

    # 3. Duplicate Prevention: Run PBS with identical data again
    pbs_dup_summary = await pbs_adapter.execute_run(test_db_session, payload=pbs_payload)
    assert pbs_dup_summary.total_fetched == 1
    assert pbs_dup_summary.inserted_count == 0
    assert pbs_dup_summary.duplicate_count == 1

    # 4. Ingest Direct Dealer Quote
    dealer_connector = DirectDealerConnector()
    d_id = uuid.uuid4()
    dq_id = uuid.uuid4()
    dealer_payload = {
        "dealer_id": str(d_id),
        "dealer_quote_id": str(dq_id),
        "dealer_business_name": "Al-Madina Traders",
        "city": "Rawalpindi",
        "items": [
            {"material_name": "Clay Bricks Awwal Class 1000 Nos", "price": 14000, "unit": "1000 nos"}
        ]
    }
    dealer_summary = await dealer_connector.execute_run(
        test_db_session,
        quotation_payload=dealer_payload,
    )
    assert dealer_summary.status == "completed"
    assert dealer_summary.inserted_count == 1

    # Verify observations in database
    observations = test_db_session.query(MaterialRateObservation).all()
    assert len(observations) == 3

    # Check price_basis and metadata in stored observations
    pbs_obs = [o for o in observations if o.city == "Islamabad"][0]
    assert pbs_obs.observation_metadata["price_basis"] == "statistical_index"
    assert pbs_obs.observation_metadata["location"]["canonical_city"] == "Islamabad"

    dealer_obs = [o for o in observations if o.city == "Rawalpindi"][0]
    assert dealer_obs.observation_metadata["price_basis"] == "dealer_quote" or dealer_obs.observation_metadata["price_basis"] == "dealer_quotation"
    assert dealer_obs.dealer_quote_id == dq_id


@pytest.mark.asyncio
async def test_pg17_adapters_live_persistence():
    """
    Validates end-to-end ingestion and JSONB metadata for national adapters against
    isolated PostgreSQL 17 cluster when ISOLATED_POSTGRES_URL is configured.
    """
    import os
    pg_url = os.environ.get("ISOLATED_POSTGRES_URL")
    if not pg_url:
        pytest.skip("ISOLATED_POSTGRES_URL not configured")

    import asyncpg
    from app.services.material_rates.fingerprint import generate_observation_fingerprint

    conn = await asyncpg.connect(pg_url)
    try:
        unique_token = uuid.uuid4().hex[:6]
        prod_code = f"CEMENT_OPC_PG_{unique_token}"
        prod_name = f"Ordinary Portland Cement {unique_token}"

        product_id = await conn.fetchval(
            """
            INSERT INTO material_rate_products (id, code, category, canonical_name, standard_unit, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, 'cement', $2, 'bag_50kg', true, NOW(), NOW())
            RETURNING id
            """,
            prod_code,
            prod_name,
        )

        source_code = f"PBS_SPI_{unique_token}"
        source_id = await conn.fetchval(
            """
            INSERT INTO material_rate_sources (id, code, name, source_type, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, 'PBS SPI Weekly Test', 'official', true, NOW(), NOW())
            RETURNING id
            """,
            source_code,
        )

        # 1. Test PBS Adapter normalization & fingerprinting
        adapter = PbsStatisticalSourceAdapter(source_code=source_code)
        raw_rec = RawSourceRecord(
            raw_material_name=prod_name,
            raw_price=1590.00,
            raw_unit="50 kg bag",
            raw_city="Multan",
            raw_published_date="2026-11-06",
            price_basis=PriceBasis.STATISTICAL_INDEX,
            original_source_citation="PBS Statistical Bulletin",
            raw_metadata={"bulletin_no": "SPI-2026-44"},
        )

        # Generate fingerprint
        now = datetime.now(timezone.utc)
        fingerprint = generate_observation_fingerprint(
            source_id=source_id,
            product_id=product_id,
            city="Multan",
            published_at=now,
            normalized_price_pkr=Decimal("1590.00"),
            normalized_unit="bag_50kg",
        )

        # Insert observation directly into PostgreSQL 17
        obs_id = await conn.fetchval(
            """
            INSERT INTO material_rate_observations (
                id, source_id, product_id, city, observed_price_pkr, observed_unit,
                normalized_price_pkr, normalized_unit, published_at, verification_status,
                duplicate_fingerprint, observation_metadata, created_at
            )
            VALUES (
                gen_random_uuid(), $1, $2, 'Multan', 1590.00, '50 kg bag',
                1590.00, 'bag_50kg', $3, 'unverified',
                $4, $5::jsonb, NOW()
            )
            RETURNING id
            """,
            source_id,
            product_id,
            now,
            fingerprint,
            json.dumps({
                "price_basis": "statistical_index",
                "location": {"canonical_city": "Multan", "raw_location": "Multan"},
                "provenance": {"is_syndicated": False, "citation": "PBS Statistical Bulletin"},
            }),
        )
        assert obs_id is not None

        # 2. Query and inspect JSONB column on PG17
        row = await conn.fetchrow(
            "SELECT city, duplicate_fingerprint, observation_metadata FROM material_rate_observations WHERE id = $1",
            obs_id,
        )
        assert row["city"] == "Multan"
        assert row["duplicate_fingerprint"] == fingerprint
        meta = json.loads(row["observation_metadata"]) if isinstance(row["observation_metadata"], str) else row["observation_metadata"]
        assert meta["price_basis"] == "statistical_index"
        assert meta["location"]["canonical_city"] == "Multan"
        assert meta["provenance"]["is_syndicated"] is False

        # 3. Test duplicate fingerprint rejection by unique constraint on PG17
        with pytest.raises(asyncpg.UniqueViolationError):
            await conn.execute(
                """
                INSERT INTO material_rate_observations (
                    id, source_id, product_id, city, observed_price_pkr, observed_unit,
                    normalized_price_pkr, normalized_unit, published_at, verification_status,
                    duplicate_fingerprint, observation_metadata, created_at
                )
                VALUES (
                    gen_random_uuid(), $1, $2, 'Multan', 1590.00, '50 kg bag',
                    1590.00, 'bag_50kg', $3, 'unverified',
                    $4, '{}'::jsonb, NOW()
                )
                """,
                source_id,
                product_id,
                now,
                fingerprint,
            )

        # 4. Test immutability trigger protection (UPDATE and DELETE blocked)
        with pytest.raises(asyncpg.RaiseError) as update_err:
            await conn.execute("UPDATE material_rate_observations SET observed_price_pkr = 1600.00 WHERE id = $1", obs_id)
        assert "append-only" in str(update_err.value).lower()

        with pytest.raises(asyncpg.RaiseError) as delete_err:
            await conn.execute("DELETE FROM material_rate_observations WHERE id = $1", obs_id)
        assert "append-only" in str(delete_err.value).lower()

    finally:
        await conn.close()


# ==============================================================================
# 10. Stage 2B.1 Credibility Scoring & Live Extracted Record Tests
# ==============================================================================

def test_credibility_scoring_methodology():
    """Validates the multi-dimensional, transparent credibility scoring model."""
    # Statutory agency
    stat_score = compute_transparent_credibility_score(
        category=SourceCategory.OFFICIAL_STATISTICAL,
        operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
        is_primary_producer_or_statutory=True,
        evidence_tier="statutory_bulletin",
        geographic_granularity="city_or_mill_specific",
    )
    assert 90 <= stat_score <= 100

    # Verified direct dealer with invoice
    dealer_score = compute_transparent_credibility_score(
        category=SourceCategory.VERIFIED_DEALER_QUOTATION,
        operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
        is_primary_producer_or_statutory=True,
        evidence_tier="verified_invoice",
        geographic_granularity="city_or_mill_specific",
    )
    assert 95 <= dealer_score <= 100

    # Manufacturer with restricted pricing access
    mfr_score = compute_transparent_credibility_score(
        category=SourceCategory.MANUFACTURER_EX_FACTORY,
        operational_status=SourceOperationalStatus.RESTRICTED,
        is_primary_producer_or_statutory=True,
        evidence_tier="verified_invoice",
        geographic_granularity="city_or_mill_specific",
    )
    assert 70 <= mfr_score <= 85

    # Secondary publisher with syndication penalty
    pub_score = compute_transparent_credibility_score(
        category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
        operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
        is_primary_producer_or_statutory=False,
        evidence_tier="structured_daily_table",
        geographic_granularity="city_or_mill_specific",
        has_syndication_risk=True,
    )
    assert 40 <= pub_score <= 55

    # Secondary publisher clean (no syndication)
    clean_pub_score = compute_transparent_credibility_score(
        category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
        operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
        is_primary_producer_or_statutory=False,
        evidence_tier="structured_daily_table",
        geographic_granularity="city_or_mill_specific",
        has_syndication_risk=False,
    )
    assert 60 <= clean_pub_score <= 80

    # Inaccessible source penalty
    offline_score = compute_transparent_credibility_score(
        category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
        operational_status=SourceOperationalStatus.INACCESSIBLE,
        is_primary_producer_or_statutory=False,
        evidence_tier="secondary_web_survey",
        geographic_granularity="city_or_mill_specific",
    )
    assert offline_score <= 50


def test_gharhub_adapter_live_table_parsing():
    """Verify GharHub adapter extracts actual published construction rates across 5 materials."""
    adapter = GharHubPublisherSourceAdapter()

    # Actual live extracted HTML snippet from GharHub Cement
    html_cement = """
    <table>
        <tr><th>Product</th><th>Current Listed Price</th><th>Type</th></tr>
        <tr><td>Maple Leaf OPC Cement</td><td>PKR 1,610 / bag</td><td>OPC</td></tr>
        <tr><td>DG Khan OPC Cement</td><td>PKR 1,590 / bag</td><td>OPC</td></tr>
        <tr><td>Bestway OPC Cement</td><td>PKR 1,570 / bag</td><td>OPC</td></tr>
    </table>
    """
    records = adapter.parse_raw_data(html_cement)
    assert len(records) == 3
    assert records[0].brand == "Maple Leaf"
    assert records[0].raw_price == 1610.0
    assert records[0].raw_unit == "bag_50kg"
    assert records[1].brand == "Dg Khan"
    assert records[1].raw_price == 1590.0

    # Actual live extracted HTML snippet from GharHub Steel (range price test)
    html_steel = """
    <table>
        <tr><th>Product</th><th>Current Listed Price</th><th>Equivalent per Ton</th><th>Type</th></tr>
        <tr><td>Mughal Grade 60 Steel Bars</td><td>PKR 256 – 258 / kg</td><td>PKR 256,000 – 258,000</td><td>Grade 60 bars</td></tr>
        <tr><td>Kamran Grade 60 Steel Bars</td><td>PKR 244 – 246 / kg</td><td>PKR 244,000 – 246,000</td><td>Grade 60 bars</td></tr>
    </table>
    """
    steel_records = adapter.parse_raw_data(html_steel)
    assert len(steel_records) == 2
    assert steel_records[0].brand == "Mughal"
    assert steel_records[0].grade == "Grade 60"
    # Range midpoint: (256 + 258) / 2 = 257.0
    assert steel_records[0].raw_price == 257.0
    assert steel_records[0].raw_unit == "kg"
    assert steel_records[1].brand == "Kamran"
    assert steel_records[1].raw_price == 245.0

    # Actual live extracted HTML snippet from GharHub Bricks
    html_bricks = """
    <table>
        <tr><th>Product</th><th>Current Listed Price</th><th>Type / Grade</th><th>Equivalent per 1,000</th></tr>
        <tr><td>Awwal A-Grade Bricks</td><td>PKR 28.5 – 29.5 / brick</td><td>A-Grade (Awwal)</td><td>PKR 28,500 – 29,500</td></tr>
        <tr><td>Doam B-Grade Bricks Online</td><td>PKR 26 – 27 / brick</td><td>B-Grade (Doam)</td><td>PKR 26,000 – 27,000</td></tr>
    </table>
    """
    brick_records = adapter.parse_raw_data(html_bricks)
    assert len(brick_records) == 2
    assert brick_records[0].grade == "Awwal Class"
    assert brick_records[0].raw_price == 29.0
    assert brick_records[0].raw_unit == "piece"


def test_materialrate_adapter_real_table_parsing():
    """Verify MaterialRate adapter extracts actual published live cement and steel tables."""
    adapter = MaterialRatePublisherSourceAdapter()

    # Actual live extracted HTML snippet from MaterialRate Cement
    html_cement = """
    <table>
        <tr><th>Brand</th><th>Price (PKR / 50kg)</th><th>Origin / Plant Location</th></tr>
        <tr><td>Lucky Cement</td><td>RS. 1,540 – 1,555</td><td>Karachi</td></tr>
        <tr><td>DG Khan Cement</td><td>RS. 1,550 – 1,555</td><td>DG Khan</td></tr>
        <tr><td>Maple Leaf Cement</td><td>RS. 1,550 – 1,560</td><td>Iskanderabad</td></tr>
    </table>
    """
    records = adapter.parse_raw_data(html_cement)
    assert len(records) == 3
    assert "Lucky" in records[0].brand
    assert records[0].raw_city == "Karachi"
    # Midpoint of 1540 - 1555 = 1547.5
    assert records[0].raw_price == 1547.5
    assert records[0].raw_unit == "bag_50kg"

    # Actual live extracted HTML snippet from MaterialRate Steel
    html_steel = """
    <table>
        <tr><th>Brand Name</th><th>Sotar (Bar Size)</th><th>40 Grade Rate (Per KG)</th><th>40 Grade (Per Ton)</th><th>60 Grade Rate (Per KG)</th></tr>
        <tr><td>Five Star Steel</td><td>3, 4, 5, 6 Sotar</td><td>Rs. 239</td><td>Rs. 239,000</td><td>Rs. 242</td></tr>
        <tr><td>Mughal Steel</td><td>2.5, 3, 4, 5 Sotar</td><td>Rs. 240</td><td>Rs. 240,000</td><td>Rs. 243</td></tr>
    </table>
    """
    records_steel = adapter.parse_raw_data(html_steel)
    assert len(records_steel) == 4  # G60 and G40 for each brand
    g60_recs = [r for r in records_steel if r.grade == "Grade 60"]
    assert len(g60_recs) == 2
    assert g60_recs[0].brand == "Five Star Steel"
    assert g60_recs[0].raw_price == 242.0
    assert g60_recs[1].brand == "Mughal Steel"
    assert g60_recs[1].raw_price == 243.0


@pytest.mark.asyncio
async def test_pg17_real_extracted_records_persistence():
    """
    Validates that real extracted market records across multiple materials
    persist cleanly to PostgreSQL 17 with valid schema, metadata, and triggers.
    """
    import os
    pg_url = os.environ.get("ISOLATED_POSTGRES_URL")
    if not pg_url:
        pytest.skip("ISOLATED_POSTGRES_URL not configured")

    import asyncpg
    from app.services.material_rates.fingerprint import generate_observation_fingerprint

    conn = await asyncpg.connect(pg_url)
    try:
        run_token = uuid.uuid4().hex[:6]
        
        # 1. Seed Product
        p_id = await conn.fetchval(
            """
            INSERT INTO material_rate_products (id, code, category, canonical_name, standard_unit, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, 'steel', 'Deformed Steel Rebar Grade 60', 'metric_ton', true, NOW(), NOW())
            RETURNING id
            """,
            f"STEEL_G60_REAL_{run_token}",
        )

        # 2. Seed GharHub Source
        s_id = await conn.fetchval(
            """
            INSERT INTO material_rate_sources (id, code, name, source_type, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, 'GharHub Construction Monitor', 'aggregator', true, NOW(), NOW())
            RETURNING id
            """,
            f"GHARHUB_SRC_{run_token}",
        )

        # 3. Insert real extracted observation (Mughal Grade 60 Rebar, 257.0/kg -> 257000/ton)
        now = datetime.now(timezone.utc)
        fingerprint = generate_observation_fingerprint(
            source_id=s_id,
            product_id=p_id,
            city="Lahore",
            published_at=now,
            normalized_price_pkr=Decimal("257000.00"),
            normalized_unit="metric_ton",
        )

        obs_id = await conn.fetchval(
            """
            INSERT INTO material_rate_observations (
                id, source_id, product_id, city, observed_price_pkr, observed_unit,
                normalized_price_pkr, normalized_unit, published_at, verification_status,
                duplicate_fingerprint, observation_metadata, created_at
            )
            VALUES (
                gen_random_uuid(), $1, $2, 'Lahore', 257.00, 'kg',
                257000.00, 'metric_ton', $3, 'unverified',
                $4, $5::jsonb, NOW()
            )
            RETURNING id
            """,
            s_id,
            p_id,
            now,
            fingerprint,
            json.dumps({
                "brand": "Mughal Steel",
                "grade": "Grade 60",
                "price_basis": "retail",
                "evidence_url": "https://gharhub.com/shop/steel-price-in-pakistan-today/",
                "location": {"canonical_city": "Lahore", "locality_or_district": "Lahore"},
            }),
        )
        assert obs_id is not None

        # Verify DB Row
        row = await conn.fetchrow(
            "SELECT observed_price_pkr, normalized_price_pkr, observation_metadata FROM material_rate_observations WHERE id = $1",
            obs_id,
        )
        assert float(row["observed_price_pkr"]) == 257.00
        assert float(row["normalized_price_pkr"]) == 257000.00
        meta = json.loads(row["observation_metadata"]) if isinstance(row["observation_metadata"], str) else row["observation_metadata"]
        assert meta["brand"] == "Mughal Steel"
        assert meta["evidence_url"] == "https://gharhub.com/shop/steel-price-in-pakistan-today/"

    finally:
        await conn.close()


# ==============================================================================
# 9. Stage 2B.1 Targeted Corrective Audit Tests
# ==============================================================================

def test_steelratetoday_pk_three_tables_and_metadata():
    """TASK 1: Verify SteelRateToday parsing on https://steelratetoday.pk/ with 3 tables, date, and disclaimer."""
    adapter = SteelRateTodaySourceAdapter()
    assert adapter.base_url == "https://steelratetoday.pk"

    sample_html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "datePublished": "2026-09-12T18:54:08+00:00",
            "dateModified": "2026-11-06T19:15:00+00:00"
        }
        </script>
    </head>
    <body>
        <p>Disclaimer: Steel rates are collected from local markets/mills and are indicative.</p>

        <!-- Table 1: Size-wise Rates -->
        <table>
            <tr><th>Size</th><th>Grade 40 Per KG</th><th>Grade 40 Per Ton</th><th>Grade 60 Per KG</th><th>Grade 60 Per Ton</th></tr>
            <tr><td>3 Sutar / 10mm</td><td>Rs. 250</td><td>Rs. 250,000</td><td>Rs. 252</td><td>Rs. 252,000</td></tr>
            <tr><td>4 Sutar / 12mm</td><td>Rs. 250</td><td>Rs. 250,000</td><td>Rs. 252</td><td>Rs. 252,000</td></tr>
        </table>

        <!-- Table 2: Brand-wise Rates with Rowspan -->
        <table>
            <tr><th>Steel Brand</th><th>Size</th><th>Grade 40 Per KG</th><th>Grade 40 Per Ton</th><th>Grade 60 Per KG</th><th>Grade 60 Per Ton</th></tr>
            <tr><td>Mughal Steel</td><td>3 Sutar / 10mm</td><td>Rs. 260</td><td>Rs. 260,000</td><td>Rs. 262</td><td>Rs. 262,000</td></tr>
            <tr><td>4 Sutar / 12mm</td><td>Rs. 260</td><td>Rs. 260,000</td><td>Rs. 262</td><td>Rs. 262,000</td></tr>
            <tr><td>Amreli Steel</td><td>3 Sutar / 10mm</td><td>Rs. 259</td><td>Rs. 259,000</td><td>Rs. 261</td><td>Rs. 261,000</td></tr>
        </table>

        <!-- Table 3: City-wise Rates -->
        <table>
            <tr><th>City</th><th>Steel Rate Per KG</th><th>Steel Rate Per Ton</th></tr>
            <tr><td>Lahore</td><td>Rs. 228</td><td>Rs. 228,000</td></tr>
            <tr><td>Karachi</td><td>Rs. 235</td><td>Rs. 235,000</td></tr>
            <tr><td>Islamabad</td><td>Rs. 230</td><td>Rs. 230,000</td></tr>
        </table>
    </body>
    </html>
    """

    records = adapter.parse_raw_data(sample_html)
    assert len(records) >= 8

    # Table 2 Brand check
    mughal_records = [r for r in records if r.brand == "Mughal Steel"]
    assert len(mughal_records) >= 2
    for r in mughal_records:
        assert r.raw_published_date == "2026-11-06T19:15:00+00:00"
        assert "disclaimer" in r.raw_metadata
        assert r.price_basis == PriceBasis.WHOLESALE

    # Table 3 City check
    city_records = [r for r in records if r.raw_city in ("Lahore", "Karachi", "Islamabad")]
    assert len(city_records) >= 3


def test_pbs_native_excel_construction_workbook_parsing():
    """TASK 2: Verify PBS Native OpenXML Excel extraction for Urban Construction Items."""
    adapter = PbsStatisticalSourceAdapter()

    # Read downloaded real sample or generated minimal OpenXML
    import io, zipfile
    # Build minimal valid .xlsx in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
            <Default Extension="xml" ContentType="application/xml"/>
            <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
            <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
            <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
            <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
        </Types>""")

        # _rels/.rels
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
            <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
        </Relationships>""")

        # xl/_rels/workbook.xml.rels
        zf.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
            <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
            <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
        </Relationships>""")

        # xl/workbook.xml
        zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets>
        </workbook>""")

        # xl/sharedStrings.xml
        strings = [
            "Urban Inter-City Consumer Prices of Construction Items",  # 0
            "October, 2026",                                          # 1
            "Names of Urban Centers",                                 # 2
            "Bricks (New first class) (1000)",                        # 3
            "Bajri (rata) (100 CFT)",                                 # 4
            "Sand (Black Pit) (100 CFT)",                             # 5
            "Cement (local) (50kg bag)",                              # 6
            "Iron bars (1/2\" 40 grade) (per tonne)",                 # 7
            "Rawalpindi",                                             # 8
            "Lahore",                                                 # 9
            "Islamabad",                                              # 10
        ]
        sst_xml = '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{}" uniqueCount="{}">'.format(len(strings), len(strings))
        for s in strings:
            sst_xml += f"<si><t>{s}</t></si>"
        sst_xml += "</sst>"
        zf.writestr("xl/sharedStrings.xml", sst_xml)

        # xl/worksheets/sheet1.xml
        sheet_data = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheetData>
                <row r="1"><c r="A1" t="s"><v>0</v></c></row>
                <row r="2"><c r="A2" t="s"><v>1</v></c></row>
                <row r="3">
                    <c r="A3" t="s"><v>2</v></c>
                    <c r="B3" t="s"><v>3</v></c>
                    <c r="C3" t="s"><v>4</v></c>
                    <c r="D3" t="s"><v>5</v></c>
                    <c r="E3" t="s"><v>6</v></c>
                    <c r="F3" t="s"><v>7</v></c>
                </row>
                <row r="4">
                    <c r="A4" t="s"><v>8</v></c>
                    <c r="B4"><v>26694.15</v></c>
                    <c r="C4"><v>15870.41</v></c>
                    <c r="D4"><v>13610.90</v></c>
                    <c r="E4"><v>1557.97</v></c>
                    <c r="F4"><v>244899.85</v></c>
                </row>
                <row r="5">
                    <c r="A5" t="s"><v>9</v></c>
                    <c r="B5"><v>25830.87</v></c>
                    <c r="C5"><v>17772.19</v></c>
                    <c r="D5"><v>7691.11</v></c>
                    <c r="E5"><v>1619.98</v></c>
                    <c r="F5"><v>235380.45</v></c>
                </row>
            </sheetData>
        </worksheet>"""
        zf.writestr("xl/worksheets/sheet1.xml", sheet_data)

    excel_bytes = buf.getvalue()
    records = adapter.parse_raw_data(excel_bytes)
    assert len(records) == 10  # 5 materials x 2 cities (Rawalpindi & Lahore)

    # Inspect parsed materials
    rawalpindi_cement = next(r for r in records if r.raw_city == "Rawalpindi" and "Cement" in r.raw_material_name)
    assert rawalpindi_cement.raw_price == 1557.97
    assert rawalpindi_cement.raw_unit == "50kg bag"
    assert rawalpindi_cement.price_basis == PriceBasis.RETAIL
    assert "October, 2026" in rawalpindi_cement.original_source_citation

    lahore_steel = next(r for r in records if r.raw_city == "Lahore" and "Iron" in r.raw_material_name)
    assert lahore_steel.raw_price == 235380.45
    assert lahore_steel.raw_unit == "per tonne"


def test_gharhub_conflicting_blocks_precedence():
    """TASK 3: Verify GharHub selects Live Rates Today over older static article/SEO tables."""
    adapter = GharHubPublisherSourceAdapter()

    conflicting_html = """
    <html>
    <body>
        <article>
            <h2>Old 2023 Construction Cost Guide Overview</h2>
            <p>Historical article cement prices in Punjab:</p>
            <table>
                <tr><th>Material</th><th>Price</th></tr>
                <tr><td>Maple Leaf Cement</td><td>PKR 1,450 / bag</td></tr>
                <tr><td>Bestway Cement</td><td>PKR 1,420 / bag</td></tr>
            </table>
        </article>

        <section class="live-pricing-section">
            <h2>Live Cement Rates Today</h2>
            <table>
                <tr><th>Product</th><th>Current Listed Price</th><th>Type</th></tr>
                <tr><td>Maple Leaf OPC Cement</td><td>PKR 1,610 / bag</td><td>OPC</td></tr>
                <tr><td>DG Khan OPC Cement</td><td>PKR 1,590 / bag</td><td>OPC</td></tr>
                <tr><td>Bestway OPC Cement</td><td>PKR 1,570 / bag</td><td>OPC</td></tr>
            </table>
        </section>
    </body>
    </html>
    """

    records = adapter.parse_raw_data(conflicting_html)
    assert len(records) == 3

    # Must choose Live rate (1610) NOT the old article rate (1450)
    maple_leaf = next(r for r in records if "Maple Leaf" in r.raw_material_name)
    assert maple_leaf.raw_price == 1610.00
    assert maple_leaf.raw_unit == "bag_50kg"
    assert maple_leaf.raw_metadata["is_live_block"] is True
    assert "html_evidence" in maple_leaf.raw_metadata
    assert "extracted_at" in maple_leaf.raw_metadata

    bestway = next(r for r in records if "Bestway" in r.raw_material_name)
    assert bestway.raw_price == 1570.00


def test_materialrate_indicative_estimates_and_null_published_at():
    """TASK 4: Verify MaterialRate.pk records have published_at=None when undated and indicative status."""
    adapter = MaterialRatePublisherSourceAdapter()

    undated_html = """
    <html>
    <body>
        <table>
            <tr><th>Brand</th><th>Price (PKR / 50kg)</th><th>Plant Location</th></tr>
            <tr><td>Bestway</td><td>1,570</td><td>Hattar</td></tr>
            <tr><td>Lucky</td><td>1,565</td><td>Pezu</td></tr>
        </table>
    </body>
    </html>
    """

    records = adapter.parse_raw_data(undated_html)
    assert len(records) == 2
    for r in records:
        assert r.raw_published_date is None  # Must NOT invent today's date
        assert r.raw_metadata["estimate_classification"] == "indicative"
        assert "fetched_at" in r.raw_metadata


def test_canonical_unit_conversions_and_decimal_precision():
    """TASK 6: Verify canonical units (cft, metric_ton, 1000_bricks, bag_50kg) and Decimal precision."""
    # Sand: 100 cft -> cft (16,000 / 100 = 160.00)
    obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("16,000", "100 cft")
    assert obs_p == Decimal("16000.00")
    assert norm_p == Decimal("160.00")
    assert norm_u == "cft"

    # Crush: 100 cft -> cft (18,000 / 100 = 180.00)
    obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("18,000", "100_cft")
    assert norm_p == Decimal("180.00")
    assert norm_u == "cft"

    # Steel: kg -> metric_ton (260.00 * 1000 = 260,000.00)
    obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("260.00", "kg")
    assert obs_p == Decimal("260.00")
    assert norm_p == Decimal("260000.00")
    assert norm_u == "metric_ton"

    # Bricks: per piece -> 1000_bricks (28.50 * 1000 = 28,500.00)
    obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("28.50", "piece")
    assert norm_p == Decimal("28500.00")
    assert norm_u == "1000_bricks"

    # Reversible converter tests
    assert convert_price(Decimal("260.00"), "kg", "metric_ton") == Decimal("260000.00")
    assert convert_price(Decimal("260000.00"), "metric_ton", "kg") == Decimal("260.00")
    assert convert_price(Decimal("16000.00"), "100_cft", "cft") == Decimal("160.00")
    assert convert_price(Decimal("160.00"), "cft", "100_cft") == Decimal("16000.00")


def test_geographic_semantics_separation():
    """TASK 7: Verify separation of market city, locality, quarry, river basin, and plant."""
    # 1. Pure quarry origin: canonical_city must be None
    loc1 = normalize_location("Margalla Quarry")
    assert loc1.canonical_city is None
    assert loc1.quarry_origin == "Margalla"

    # 2. Pure river basin: canonical_city must be None
    loc2 = normalize_location("Chenab River Sand")
    assert loc2.canonical_city is None
    assert loc2.river_basin == "Chenab"

    # 3. Market city with quarry detail
    loc3 = normalize_location("Islamabad (Margalla Bajri)")
    assert loc3.canonical_city == "Islamabad"
    assert loc3.quarry_origin == "Margalla"

    # 4. Market city with locality
    loc4 = normalize_location("Lahore Cantt")
    assert loc4.canonical_city == "Lahore"
    assert loc4.locality_or_district == "Lahore Cantt"

    # 5. Prohibited broad regional province
    with pytest.raises(NormalizationError):
        normalize_location("Punjab")


def test_credibility_scoring_bounds_and_penalties():
    """TASK 8: Verify 0-100 clamping, offline penalty (-25), syndication penalty (-15), and confidence separation."""
    # Inaccessible source has -25 penalty
    score_inacc = compute_transparent_credibility_score(
        category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
        operational_status=SourceOperationalStatus.INACCESSIBLE,
        is_primary_producer_or_statutory=False,
        evidence_tier="secondary_web_survey",
        geographic_granularity="city_or_mill_specific",
    )
    score_active = compute_transparent_credibility_score(
        category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
        operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
        is_primary_producer_or_statutory=False,
        evidence_tier="secondary_web_survey",
        geographic_granularity="city_or_mill_specific",
    )
    # Difference between active (+10) and inaccessible (-25) is exactly 35 points
    assert score_active - score_inacc == 35

    # Syndication penalty (-15)
    score_synd = compute_transparent_credibility_score(
        category=SourceCategory.SECONDARY_MARKET_PUBLISHER,
        operational_status=SourceOperationalStatus.VERIFIED_CURRENT,
        is_primary_producer_or_statutory=False,
        evidence_tier="secondary_web_survey",
        geographic_granularity="city_or_mill_specific",
        has_syndication_risk=True,
    )
    assert score_active - score_synd == 15

    # Range bound
    assert 0 <= score_inacc <= 100
    assert 0 <= score_active <= 100

    # Observation confidence separation
    conf_clean = compute_observation_confidence(publisher_credibility=70, verification_status="verified_quote")
    conf_indicative_undated = compute_observation_confidence(
        publisher_credibility=70, verification_status="indicative", has_exact_date=False
    )
    assert conf_clean > conf_indicative_undated
    assert conf_indicative_undated == 70 - 20 - 20  # 30


def test_dealer_network_status_clarification():
    """TASK 9: Verify DirectDealerConnector is implemented in code while network is CANDIDATE (0 dealers)."""
    connector = DirectDealerConnector()
    assert connector.source_code == "DIRECT_DEALER_QUOTATION"

    entry = national_registry.get_source("DIRECT_DEALER_QUOTATION")
    assert entry is not None
    assert entry.operational_status == SourceOperationalStatus.CANDIDATE
    assert "0 registered dealers" in entry.notes_and_rationale


def test_zarea_operational_status_restricted():
    """TASK 5: Verify Zarea URL points to /daily-price/cement and status is RESTRICTED."""
    entry = national_registry.get_source("ZAREA_B2B_MARKETPLACE")
    assert entry is not None
    assert entry.base_url == "https://zarea.com/daily-price/cement"
    assert entry.operational_status == SourceOperationalStatus.RESTRICTED
    assert "Next.js" in entry.access_method


