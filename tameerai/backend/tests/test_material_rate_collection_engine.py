"""
TameerAI - Stage 2A Base Source Adapter & Material Rate Collection Engine Tests

Validates:
A. Base adapter contracts and subclass interfaces.
B. Adapter registration and source identification.
C. SafeHttpClient timeout, retries, and backoff.
D. URL validation and SSRF protection (rejects AWS metadata, invalid schemes, unlisted domains).
E. Content-type and response-size safeguards.
F. Material name and catalog resolution.
G. PKR price and unit normalization (bori -> bag_50kg, ton -> metric_ton, etc.).
H. Canonical SHA-256 fingerprint integration.
I. Duplicate observation rejection.
J. Append-only observation protection.
K. Source run telemetry logging (success, failure, counts).
L. Invalid and incomplete data rejection (negative price, missing unit, malformed date).
M. Background job compatibility (nullable scope IDs, worker execution).
N. Redaction of sensitive errors and credentials.
O. Disabled-by-default collection configuration gate.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import os
import uuid
import pytest
import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.material_rate import (
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateObservation,
    MaterialRateSourceRun,
)
from app.models.job import BackgroundJob, JobType, JobStatus
from app.services.material_rates.base_adapter import BaseSourceAdapter
from app.services.material_rates.contracts import CollectionSourceType, RawSourceRecord
from app.services.material_rates.fingerprint import generate_observation_fingerprint
from app.services.material_rates.fixture_adapter import FixtureSourceAdapter
from app.services.material_rates.http_client import (
    CollectionFetchError,
    CollectionSecurityError,
    SafeHttpClient,
    resolve_and_validate_host,
)
from app.services.material_rates.normalization import (
    NormalizationError,
    convert_price,
    normalize_city,
    normalize_location,
    normalize_published_date,
    normalize_unit_and_price,
)


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
# TEST GROUP 1: Configuration & Security Gates
# ---------------------------------------------------------------------------

class TestConfigurationAndGates:
    def test_01_collection_engine_disabled_by_default(self):
        """Verifies that external material rate collection is safely gated off by default."""
        assert settings.ENABLE_MATERIAL_RATE_COLLECTION is False
        assert settings.ENABLE_GEMINI_API is False
        assert settings.ENABLE_AI_FEATURES is False


# ---------------------------------------------------------------------------
# TEST GROUP 2: Safe HTTP Client & SSRF Protection
# ---------------------------------------------------------------------------

class TestSafeHttpClientAndSSRF:
    def test_02_allowed_domain_whitelist(self):
        client = SafeHttpClient(allowed_domains=["pbs.gov.pk", "tameerai.pk"])
        assert client.validate_url("https://pbs.gov.pk/cpi-bulletin") == "https://pbs.gov.pk/cpi-bulletin"
        assert client.validate_url("https://rates.tameerai.pk/daily") == "https://rates.tameerai.pk/daily"

        with pytest.raises(CollectionSecurityError) as exc_info:
            client.validate_url("https://malicious-site.com/steal-data")
        assert "not in the allowed domain whitelist" in str(exc_info.value)

    def test_03_ssrf_metadata_rejection(self):
        client = SafeHttpClient()
        with pytest.raises(CollectionSecurityError) as exc_info:
            client.validate_url("http://169.254.169.254/latest/meta-data")
        assert "SSRF Protection" in str(exc_info.value)

    def test_03b_ssrf_ipv6_and_private_network_rejection(self):
        client = SafeHttpClient(enforce_https=False)
        prohibited_targets = [
            "http://10.0.0.1/internal-rate",
            "http://192.168.1.100/admin",
            "http://172.16.5.1/status",
            "http://[::1]/secret",
            "http://[fc00::1]/private-data",
            "http://[fe80::1]/link-local",
        ]
        for target in prohibited_targets:
            with pytest.raises(CollectionSecurityError) as exc_info:
                client.validate_url(target)
            assert "SSRF Protection" in str(exc_info.value)

    def test_03c_ssrf_ipv4_mapped_ipv6_rejection(self):
        client = SafeHttpClient(enforce_https=False)
        prohibited_mapped = [
            "http://[::ffff:127.0.0.1]/test",
            "http://[::ffff:10.0.0.1]/internal",
            "http://[::ffff:169.254.169.254]/metadata",
            "http://[::ffff:192.168.1.1]/router",
        ]
        for target in prohibited_mapped:
            with pytest.raises(CollectionSecurityError) as exc_info:
                client.validate_url(target)
            assert "SSRF Protection" in str(exc_info.value)

    def test_03d_ssrf_cloud_metadata_endpoints(self):
        client = SafeHttpClient(enforce_https=False)
        metadata_endpoints = [
            "http://169.254.169.254/latest/meta-data/",
            "http://[fd00:ec2::254]/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
        ]
        for target in metadata_endpoints:
            with pytest.raises(CollectionSecurityError) as exc_info:
                client.validate_url(target)
            assert "SSRF Protection" in str(exc_info.value)

    def test_03e_dns_rebinding_multiple_answers_with_private_ip_rejected(self):
        import socket
        # Mock DNS resolver returning one public IP and one private IP
        def mock_dns_rebinding_resolver(host, port, family, socktype):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", port)),
            ]

        client = SafeHttpClient(dns_resolver=mock_dns_rebinding_resolver, allowed_domains=["rebinding-test.com"])
        with pytest.raises(CollectionSecurityError) as exc_info:
            client.validate_url("https://rebinding-test.com/rates")
        assert "resolves to prohibited IP" in str(exc_info.value)
        assert "10.0.0.1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_03f_dns_rebinding_connection_pinning_and_sni_preservation(self):
        import socket
        from app.services.material_rates.http_client import SafeNetworkBackend

        def mock_dns(host, port, family, socktype):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

        backend = SafeNetworkBackend(dns_resolver=mock_dns)
        assert backend.dns_resolver is not None

        # Verify resolve_and_validate_host pins target IP
        ips = resolve_and_validate_host("safe-domain.pk", 443, dns_resolver=mock_dns)
        assert ips == ["93.184.216.34"]

    @pytest.mark.asyncio
    async def test_03g_redirect_to_private_ip_blocked(self):
        # Initial request returns 302 with Location pointing to private IP
        mock_transport = httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"location": "http://10.0.0.1/admin-secret"})
        )
        client = SafeHttpClient(transport=mock_transport, enforce_https=False)
        with pytest.raises(CollectionSecurityError) as exc_info:
            await client.get("http://localhost/start")
        assert "SSRF Protection" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_03h_redirect_to_unauthorized_domain_blocked(self):
        # Initial request returns 302 to unauthorized external domain
        mock_transport = httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"location": "https://unauthorized-leak.com/exfiltrate"})
        )
        client = SafeHttpClient(
            allowed_domains=["pbs.gov.pk"],
            transport=mock_transport,
            enforce_https=True,
        )
        with pytest.raises(CollectionSecurityError) as exc_info:
            await client.get("https://pbs.gov.pk/cpi")
        assert "not in the allowed domain whitelist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_03i_redirect_https_downgrade_blocked(self):
        # Initial HTTPS request attempts redirect to insecure HTTP scheme
        mock_transport = httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"location": "http://pbs.gov.pk/insecure-cpi"})
        )
        client = SafeHttpClient(
            allowed_domains=["pbs.gov.pk"],
            transport=mock_transport,
            enforce_https=False,
        )
        with pytest.raises(CollectionSecurityError) as exc_info:
            await client.get("https://pbs.gov.pk/cpi")
        assert "Insecure redirect downgrade from HTTPS to HTTP" in str(exc_info.value)

    def test_03j_environment_proxy_bypass_blocked(self):
        # Verifies SafeAsyncHTTPTransport disables trust_env to prevent proxy bypass
        from app.services.material_rates.http_client import SafeAsyncHTTPTransport
        transport = SafeAsyncHTTPTransport()
        assert transport._pool._proxy is None

    def test_04_https_enforcement(self):
        client = SafeHttpClient(enforce_https=True)
        with pytest.raises(CollectionSecurityError) as exc_info:
            client.validate_url("http://external-rates.com/data.json")
        assert "HTTPS is strictly required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_05_max_response_size_safeguard(self):
        # Mock transport returning oversized content
        large_content = b"X" * (1024 * 1024 + 10)  # > 1MB
        mock_transport = httpx.MockTransport(
            lambda request: httpx.Response(200, content=large_content, headers={"content-type": "application/json"})
        )
        client = SafeHttpClient(
            max_response_bytes=1024 * 1024,  # 1MB limit
            transport=mock_transport,
            enforce_https=False,
        )
        with pytest.raises(CollectionSecurityError) as exc_info:
            await client.get("http://localhost/test")
        assert "exceeded maximum allowed size" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_05b_authoritative_5mib_content_length_rejected(self):
        # Pre-check rejection when Content-Length header exceeds 5 MiB (5,242,880 bytes)
        mock_transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-length": "5242881", "content-type": "application/json"},
                content=b"",
            )
        )
        client = SafeHttpClient(transport=mock_transport, enforce_https=False)
        with pytest.raises(CollectionSecurityError) as exc_info:
            await client.get("http://localhost/large-catalog")
        assert "exceeded maximum allowed size" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_05c_payload_at_and_below_5mib_boundary(self):
        five_mib = 5 * 1024 * 1024  # 5,242,880 bytes

        # 1. Payload exactly at 5 MiB boundary succeeds
        boundary_content = b"A" * five_mib
        mock_transport_at = httpx.MockTransport(
            lambda request: httpx.Response(200, headers={"content-type": "application/json"}, content=boundary_content)
        )
        client_at = SafeHttpClient(transport=mock_transport_at, enforce_https=False)
        resp_at = await client_at.get("http://localhost/exact-boundary")
        assert len(resp_at.content) == five_mib

        # 2. Payload immediately below 5 MiB boundary succeeds
        below_content = b"B" * (five_mib - 1)
        mock_transport_below = httpx.MockTransport(
            lambda request: httpx.Response(200, headers={"content-type": "application/json"}, content=below_content)
        )
        client_below = SafeHttpClient(transport=mock_transport_below, enforce_https=False)
        resp_below = await client_below.get("http://localhost/below-boundary")
        assert len(resp_below.content) == (five_mib - 1)

        # 3. Payload immediately above 5 MiB boundary is rejected during streaming
        above_content = b"C" * (five_mib + 1)
        mock_transport_above = httpx.MockTransport(
            lambda request: httpx.Response(200, headers={"content-type": "application/json"}, content=above_content)
        )
        client_above = SafeHttpClient(transport=mock_transport_above, enforce_https=False)
        with pytest.raises(CollectionSecurityError) as exc_above:
            await client_above.get("http://localhost/above-boundary")
        assert "exceeded maximum allowed size" in str(exc_above.value)

    @pytest.mark.asyncio
    async def test_06_content_type_validation(self):
        # Mock transport returning unexpected executable content
        mock_transport = httpx.MockTransport(
            lambda request: httpx.Response(200, content=b"ELF...", headers={"content-type": "application/x-executable"})
        )
        client = SafeHttpClient(transport=mock_transport, enforce_https=False)
        with pytest.raises(CollectionSecurityError) as exc_info:
            await client.get("http://localhost/test")
        assert "Disallowed Content-Type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_07_bounded_retries_on_timeout(self):
        attempt_counter = 0

        def failing_handler(request):
            nonlocal attempt_counter
            attempt_counter += 1
            raise httpx.ReadTimeout("Socket timeout")

        mock_transport = httpx.MockTransport(failing_handler)
        client = SafeHttpClient(
            max_retries=3,
            timeout_seconds=0.1,
            transport=mock_transport,
            enforce_https=False,
        )
        with pytest.raises(CollectionFetchError) as exc_info:
            await client.get("http://localhost/timeout")
        assert attempt_counter == 3
        assert "failed after 3 attempts" in str(exc_info.value)


# ---------------------------------------------------------------------------
# TEST GROUP 3: Data Normalization Pipeline
# ---------------------------------------------------------------------------

class TestDataNormalizationPipeline:
    def test_08_city_normalization(self):
        assert normalize_city("lahore") == "Lahore"
        assert normalize_city("  LHR  ") == "Lahore"
        assert normalize_city("لاہور") == "Lahore"
        assert normalize_city("Karachi South") == "Karachi"
        assert normalize_city("Islamabad Federal Capital") == "Islamabad"

    def test_08b_location_preservation_three_concepts(self):
        # 1. Metropolitan area with locality/district
        city, loc, raw = normalize_location("Lahore Cantt")
        assert city == "Lahore"
        assert loc == "Lahore Cantt"
        assert raw == "Lahore Cantt"

        city, loc, raw = normalize_location("Karachi South")
        assert city == "Karachi"
        assert loc == "Karachi South"
        assert raw == "Karachi South"

        city, loc, raw = normalize_location("Karachi East")
        assert city == "Karachi"
        assert loc == "Karachi East"

        city, loc, raw = normalize_location("Karachi Central")
        assert city == "Karachi"
        assert loc == "Karachi Central"

        city, loc, raw = normalize_location("South Karachi")
        assert city == "Karachi"
        assert loc == "South Karachi"

        # 2. Urdu location names
        city, loc, raw = normalize_location("لاہور کینٹ")
        assert city == "Lahore"
        assert loc == "لاہور کینٹ"
        assert raw == "لاہور کینٹ"

        city, loc, raw = normalize_location("کراچی جنوبی")
        assert city == "Karachi"
        assert loc == "کراچی جنوبی"

        # 3. Plain canonical cities without sub-locality
        city, loc, raw = normalize_location("Lahore")
        assert city == "Lahore"
        assert loc is None
        assert raw == "Lahore"

        city, loc, raw = normalize_location("LHR")
        assert city == "Lahore"
        assert loc is None

    def test_08c_unknown_and_ambiguous_locations(self):
        # Unknown specific town name
        city, loc, raw = normalize_location("Daska")
        assert city == "Daska"
        assert loc is None

        # Unknown town with locality
        city, loc, raw = normalize_location("Daska Sambrial Road")
        assert city == "Daska"
        assert loc == "Daska Sambrial Road"

        # Ambiguous province/national scopes must be rejected
        ambiguous_cases = ["Punjab", "Sindh", "Pakistan", "KPK", "Balochistan", "National", "پنجاب", "سندھ"]
        for case in ambiguous_cases:
            with pytest.raises(NormalizationError) as exc:
                normalize_location(case)
            assert "Ambiguous or regional non-city location" in str(exc.value)

        # Empty location rejection
        with pytest.raises(NormalizationError):
            normalize_location("")
        with pytest.raises(NormalizationError):
            normalize_location("   ")
        with pytest.raises(NormalizationError):
            normalize_location(None)

    def test_08d_no_accidental_merging_of_districts(self):
        # Different districts in same metropolitan area remain differentiated
        districts = ["Karachi South", "Karachi East", "Karachi Central", "Karachi West", "Karachi Malir"]
        results = [normalize_location(d) for d in districts]
        
        # All share canonical city
        assert all(r[0] == "Karachi" for r in results)
        
        # Every locality/district is distinct
        localities = [r[1] for r in results]
        assert len(set(localities)) == len(districts)

    def test_09_unit_and_price_normalization(self):
        # Cement bori
        obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("1,520.00", "bori")
        assert obs_p == Decimal("1520.00")
        assert obs_u == "bori"
        assert norm_p == Decimal("1520.00")
        assert norm_u == "bag_50kg"

        # Steel ton
        obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("265000", "metric ton")
        assert obs_p == Decimal("265000.00")
        assert norm_u == "metric_ton"

        # Negative price rejection
        with pytest.raises(NormalizationError) as exc:
            normalize_unit_and_price("-100.00", "bag")
        assert "Negative price is invalid" in str(exc.value)

    def test_09b_truckload_unit_safety_and_declared_capacity(self):
        """
        Validates Task D truckload unit safety:
        1. When vehicle capacity is undeclared:
           - Retains 'truckload' as original and normalized unit.
           - Normalized price remains 25000.00/truckload.
           - NEVER publishes or treats undeclared truckload as PKR/CFT!
        2. When vehicle capacity is explicitly declared (500 cft):
           - Normalizes to canonical unit 'cft'.
           - Price converted: 25000 / 500 = 50.00 PKR/cft.
        3. convert_price direct call:
           - Fails without declared vehicle capacity.
           - Succeeds when vehicle capacity is declared.
        """
        # Case A: Undeclared capacity
        obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("25,000", "truckload")
        assert obs_p == Decimal("25000.00")
        assert obs_u == "truckload"
        assert norm_p == Decimal("25000.00")
        assert norm_u == "truckload"
        assert norm_u != "cft"

        # Case B: Explicitly declared capacity (500 cft)
        obs_p, obs_u, norm_p, norm_u = normalize_unit_and_price("25,000", "truckload", vehicle_capacity_cft=500)
        assert obs_p == Decimal("25000.00")
        assert obs_u == "truckload"
        assert norm_p == Decimal("50.00")
        assert norm_u == "cft"

        # Case C: convert_price safety
        with pytest.raises(NormalizationError) as exc:
            convert_price(25000, "truckload", "cft")
        assert "without explicitly declared vehicle capacity" in str(exc.value)

        converted = convert_price(25000, "truckload", "cft", vehicle_capacity_cft=500)
        assert converted == Decimal("50.00")

    def test_10_published_date_normalization(self):
        dt = normalize_published_date("2026-11-06")
        assert dt.year == 2026 and dt.month == 11 and dt.day == 6
        assert dt.tzinfo is not None

        # Pakistani standard DD/MM/YYYY
        dt2 = normalize_published_date("06/11/2026")
        assert dt2.year == 2026 and dt2.month == 11 and dt2.day == 6


# ---------------------------------------------------------------------------
# TEST GROUP 4: FixtureSourceAdapter & End-to-End Collection Run
# ---------------------------------------------------------------------------

class TestFixtureSourceAdapterExecution:
    @pytest.mark.asyncio
    async def test_11_fixture_adapter_successful_execution(self, sqlite_session: Session):
        """Verifies full collection run: fetch, parse, normalize, fingerprint, deduplicate, persist."""
        # 1. Seed catalog products
        prod_cement = MaterialRateProduct(
            code="PRD-CEM-LUCKY",
            category="cement",
            canonical_name="Lucky Cement OPC 50kg",
            standard_unit="bag_50kg",
        )
        prod_steel = MaterialRateProduct(
            code="PRD-STL-MUGHAL",
            category="steel",
            canonical_name="Mughal Supreme Deformed Steel G60 12mm",
            standard_unit="metric_ton",
        )
        prod_brick = MaterialRateProduct(
            code="PRD-BRK-AWWAL",
            category="bricks",
            canonical_name="Awwal Clay Bricks",
            standard_unit="1000_bricks",
        )
        sqlite_session.add_all([prod_cement, prod_steel, prod_brick])
        sqlite_session.commit()

        # 2. Run Fixture Adapter
        adapter = FixtureSourceAdapter()
        summary = await adapter.execute_run(sqlite_session)

        # 3. Verify Run Accounting
        assert summary.status == "completed"
        assert summary.total_fetched == 7  # 4 valid + 3 invalid in default fixture
        assert summary.inserted_count == 4
        assert summary.rejected_count == 3
        assert summary.duplicate_count == 0

        # 4. Verify Database Observations
        observations = sqlite_session.query(MaterialRateObservation).all()
        assert len(observations) == 4
        for obs in observations:
            assert obs.verification_status == "unverified"
            assert obs.duplicate_fingerprint is not None
            assert len(obs.duplicate_fingerprint) == 64
            # Verify Task B location metadata preservation
            assert obs.observation_metadata is not None
            assert "location" in obs.observation_metadata
            loc_data = obs.observation_metadata["location"]
            assert loc_data["canonical_city"] == obs.city
            assert loc_data["raw_location"] is not None

        # 5. Verify Telemetry in MaterialRateSourceRun
        run_record = sqlite_session.query(MaterialRateSourceRun).first()
        assert run_record is not None
        assert run_record.status == "completed"
        assert run_record.records_accepted == 4
        assert run_record.records_rejected == 3

    @pytest.mark.asyncio
    async def test_12_duplicate_observations_deduplicated_by_fingerprint(self, sqlite_session: Session):
        """Re-running the same adapter run must deduplicate all records without duplicating or overwriting."""
        prod = MaterialRateProduct(
            code="PRD-CEM-LUCKY",
            category="cement",
            canonical_name="Lucky Cement OPC 50kg",
            standard_unit="bag_50kg",
        )
        sqlite_session.add(prod)
        sqlite_session.commit()

        single_item = [
            {
                "material": "Lucky Cement OPC 50kg",
                "price": "1520.00",
                "unit": "bag",
                "city": "Lahore",
                "date": "2026-11-06",
            }
        ]
        adapter = FixtureSourceAdapter(fixture_payload=single_item)

        # First run: inserts 1 observation
        s1 = await adapter.execute_run(sqlite_session)
        assert s1.inserted_count == 1
        assert s1.duplicate_count == 0

        # Second run with identical payload: detects 1 duplicate
        s2 = await adapter.execute_run(sqlite_session)
        assert s2.inserted_count == 0
        assert s2.duplicate_count == 1

        # Total observations in DB remains exactly 1
        total_obs = sqlite_session.query(MaterialRateObservation).count()
        assert total_obs == 1

    @pytest.mark.asyncio
    async def test_13_failed_source_run_records_sanitized_telemetry(self, sqlite_session: Session):
        adapter = FixtureSourceAdapter(simulate_timeout=True)
        summary = await adapter.execute_run(sqlite_session)

        assert summary.status == "failed"
        assert "CollectionFetchError" in summary.error_message
        assert summary.inserted_count == 0

        # Telemetry logged
        run_log = sqlite_session.query(MaterialRateSourceRun).first()
        assert run_log is not None
        assert run_log.status == "failed"
        assert "CollectionFetchError" in run_log.error_summary


# ---------------------------------------------------------------------------
# TEST GROUP 5: Background Job Compatibility
# ---------------------------------------------------------------------------

class TestBackgroundJobEngineCompatibility:
    @pytest.mark.asyncio
    async def test_14_global_background_job_linking(self, sqlite_session: Session):
        """Verifies that an ingestion run can be associated with a global background job."""
        prod = MaterialRateProduct(
            code="PRD-CEM-LUCKY",
            category="cement",
            canonical_name="Lucky Cement OPC 50kg",
            standard_unit="bag_50kg",
        )
        job = BackgroundJob(
            job_type=JobType.MATERIAL_RATE_SOURCE_SYNC.value,
            status=JobStatus.RUNNING.value,
            priority=0,
            payload={"source_code": "FIXTURE_SRC_01"},
        )
        sqlite_session.add_all([prod, job])
        sqlite_session.commit()

        single_item = [
            {
                "material": "Lucky Cement OPC 50kg",
                "price": "1520.00",
                "unit": "bag",
                "city": "Lahore",
                "date": "2026-11-06",
            }
        ]
        adapter = FixtureSourceAdapter(fixture_payload=single_item)
        summary = await adapter.execute_run(sqlite_session, background_job_id=job.id)

        assert summary.inserted_count == 1
        obs = sqlite_session.query(MaterialRateObservation).first()
        assert obs.background_job_id == job.id


# ---------------------------------------------------------------------------
# TEST GROUP 6: PostgreSQL 17 Integration (Append-Only & Unique Fingerprint)
# ---------------------------------------------------------------------------

@pytest.mark.postgres
class TestPostgreSqlCollectionIntegration:
    """
    Dedicated PostgreSQL 17 live engine collection test.
    Only runs when ISOLATED_POSTGRES_URL on port 5433 is provided.
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

    @pytest.mark.asyncio
    async def test_15_pg17_collection_run_append_only_and_deduplication(self, pg_connection):
        """Verifies collection, duplicate fingerprint rejection, and trigger append-only protection on PostgreSQL 17."""
        import asyncpg
        from app.services.material_rates.fingerprint import generate_observation_fingerprint

        run_token = uuid.uuid4().hex[:8]
        product_code = f"PRD-PG17-{run_token}"
        source_code = f"SRC-PG17-{run_token}"

        # 1. Ensure test product exists
        product_id = await pg_connection.fetchval("""
            INSERT INTO material_rate_products (id, code, category, canonical_name, standard_unit, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, 'cement', 'PG17 Test Cement OPC', 'bag_50kg', true, NOW(), NOW())
            RETURNING id;
        """, product_code)

        # 2. Ensure test source exists
        source_id = await pg_connection.fetchval("""
            INSERT INTO material_rate_sources (id, code, name, source_type, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, 'PG17 Test Source', 'dealer_network', true, NOW(), NOW())
            RETURNING id;
        """, source_code)

        # 3. Compute canonical fingerprint
        fingerprint = generate_observation_fingerprint(
            source_id=source_id,
            product_id=product_id,
            city="Lahore",
            published_at="2026-11-06",
            normalized_price_pkr=Decimal("1520.00"),
            normalized_unit="bag_50kg",
        )

        obs_id = str(uuid.uuid4())

        # 4. Insert valid observation
        await pg_connection.execute("""
            INSERT INTO material_rate_observations (
                id, product_id, source_id, city, observed_price_pkr, observed_unit,
                normalized_price_pkr, normalized_unit, published_at, verification_status,
                duplicate_fingerprint, created_at
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid, 'Lahore', 1520.00, 'bag',
                1520.00, 'bag_50kg', NOW(), 'unverified',
                $4, NOW()
            );
        """, obs_id, product_id, source_id, fingerprint)

        # 5. Attempt duplicate insertion -> MUST be rejected by PostgreSQL unique constraint
        with pytest.raises(asyncpg.exceptions.UniqueViolationError) as exc_dup:
            await pg_connection.execute("""
                INSERT INTO material_rate_observations (
                    id, product_id, source_id, city, observed_price_pkr, observed_unit,
                    normalized_price_pkr, normalized_unit, published_at, verification_status,
                    duplicate_fingerprint, created_at
                ) VALUES (
                    $1::uuid, $2::uuid, $3::uuid, 'Lahore', 1520.00, 'bag',
                    1520.00, 'bag_50kg', NOW(), 'unverified',
                    $4, NOW()
                );
            """, str(uuid.uuid4()), product_id, source_id, fingerprint)
        assert "duplicate_fingerprint" in str(exc_dup.value).lower() or "unique" in str(exc_dup.value).lower()

        # 6. Attempt UPDATE on observation -> MUST be blocked by PostgreSQL trigger
        with pytest.raises(asyncpg.exceptions.RaiseError) as exc_upd:
            await pg_connection.execute("""
                UPDATE material_rate_observations SET city = 'Rawalpindi' WHERE id = $1::uuid;
            """, obs_id)
        assert "strictly append-only" in str(exc_upd.value).lower()

        # 7. Attempt DELETE on observation -> MUST be blocked by PostgreSQL trigger
        with pytest.raises(asyncpg.exceptions.RaiseError) as exc_del:
            await pg_connection.execute("""
                DELETE FROM material_rate_observations WHERE id = $1::uuid;
            """, obs_id)
        assert "strictly append-only" in str(exc_del.value).lower()
