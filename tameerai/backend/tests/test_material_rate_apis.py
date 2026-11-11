"""
TameerAI - Phase 02 Material Rate Intelligence FastAPI Endpoints Test Suite
"""

from datetime import datetime, timezone
from decimal import Decimal
import io
from typing import AsyncGenerator
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_db
from app.core.rate_limit import login_limiter
from app.db.base import Base
from app.main import app
from app.models.cost import MaterialRate
from app.models.material_rate import (
    MaterialRateDealer,
    MaterialRateDealerQuote,
    MaterialRateObservation,
    MaterialRateProduct,
    MaterialRateSource,
    MaterialRateVerificationEvent,
)


@pytest_asyncio.fixture
async def api_session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    yield session_factory
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(api_session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with api_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    login_limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    login_limiter.reset()


async def get_auth_token(client: AsyncClient, email: str = "engineer@tameerai.pk") -> str:
    reg_payload = {
        "fullName": "Senior Engineer",
        "email": email,
        "password": "Password12345!",
        "role": "engineer",
        "city": "Lahore",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password12345!"},
    )
    assert login_res.status_code == 200
    return login_res.json()["accessToken"]


class TestMaterialRateCatalogAndSourceAPIs:
    @pytest.mark.asyncio
    async def test_list_products(self, api_client: AsyncClient, api_session_factory):
        token = await get_auth_token(api_client, "prod_user@tameerai.pk")
        headers = {"Authorization": f"Bearer {token}"}

        # Seed product
        async with api_session_factory() as s:
            p = MaterialRateProduct(
                id=uuid.uuid4(),
                code="CEMENT_OPC_50KG",
                category="cement",
                canonical_name="Ordinary Portland Cement 50kg Bag",
                standard_unit="bag_50kg",
                is_active=True,
            )
            s.add(p)
            await s.commit()

        res = await api_client.get("/api/v1/material-rates/products", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert data[0]["code"] == "CEMENT_OPC_50KG"

    @pytest.mark.asyncio
    async def test_list_sources_and_telemetry(self, api_client: AsyncClient, api_session_factory):
        token = await get_auth_token(api_client, "src_user@tameerai.pk")
        headers = {"Authorization": f"Bearer {token}"}

        # Seed source
        async with api_session_factory() as s:
            src = MaterialRateSource(
                id=uuid.uuid4(),
                code="PBS_STATISTICAL_SPI",
                name="Pakistan Bureau of Statistics",
                source_type="official",
                reliability_tier="authoritative",
                refresh_cadence="weekly",
                freshness_ttl_days=30,
                is_active=True,
            )
            s.add(src)
            await s.commit()

        # List sources
        res = await api_client.get("/api/v1/material-rates/sources", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1

        # Get telemetry
        tel_res = await api_client.get("/api/v1/material-rates/sources/telemetry", headers=headers)
        assert tel_res.status_code == 200
        tel_data = tel_res.json()
        assert "total_runs" in tel_data


class TestDealerAndQuotationAPIs:
    @pytest.mark.asyncio
    async def test_dealer_registration_and_quote_submission(self, api_client: AsyncClient, api_session_factory):
        token = await get_auth_token(api_client, "dealer_user@tameerai.pk")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Register Dealer
        dealer_payload = {
            "business_name": "Al-Rehman Steel Traders",
            "dealer_code": "DLR-LHR-0099",
            "city": "Lahore",
            "market_area": "Badami Bagh",
            "contact_person": "Haji Rehman",
            "contact_phone": "0321-9876543",
        }
        dealer_res = await api_client.post("/api/v1/material-rates/dealers", json=dealer_payload, headers=headers)
        assert dealer_res.status_code == 201
        dealer_data = dealer_res.json()
        dealer_id = dealer_data["id"]

        # Seed product
        prod_id = uuid.uuid4()
        async with api_session_factory() as s:
            p = MaterialRateProduct(
                id=prod_id,
                code="STEEL_REBAR_G60_TON",
                category="steel",
                canonical_name="Deformed Rebar G60 Ton",
                standard_unit="metric_ton",
                is_active=True,
            )
            s.add(p)
            await s.commit()

        # 2. Submit Quote
        quote_payload = {
            "dealer_id": dealer_id,
            "product_id": str(prod_id),
            "city": "Lahore",
            "quoted_price_pkr": 265000.0,
            "quoted_unit": "metric_ton",
            "validity_days": 7,
            "delivery_charges_pkr": 0.0,
            "tax_included": True,
        }
        quote_res = await api_client.post("/api/v1/material-rates/dealers/quotes", json=quote_payload, headers=headers)
        assert quote_res.status_code == 201
        quote_data = quote_res.json()
        assert quote_data["normalized_price_pkr"] == "265000.00"
        quote_id = quote_data["id"]

        # 3. Upload Evidence
        file_content = b"%PDF-1.4 Mock quotation document content for verification audit"
        files = {"file": ("quote_slip.pdf", io.BytesIO(file_content), "application/pdf")}
        upload_res = await api_client.post(
            f"/api/v1/material-rates/dealers/quotes/{quote_id}/evidence",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        token_str = upload_data["signed_download_token"]
        assert token_str is not None

        # 4. Download Evidence with signed token
        download_res = await api_client.get(
            f"/api/v1/material-rates/dealers/quotes/{quote_id}/evidence?token={token_str}",
        )
        assert download_res.status_code == 200
        assert download_res.content == file_content


class TestBackwardCompatibilityAndSnapshots:
    @pytest.mark.asyncio
    async def test_backward_compatible_market_rates_endpoints(self, api_client: AsyncClient, api_session_factory):
        token = await get_auth_token(api_client, "compat_user@tameerai.pk")
        headers = {"Authorization": f"Bearer {token}"}

        rate_id = uuid.uuid4()
        async with api_session_factory() as s:
            r = MaterialRate(
                id=rate_id,
                city="Lahore",
                category="cement",
                name="Ordinary Portland Cement 50kg Bag",
                unit="bag_50kg",
                rate_pkr=Decimal("1520.00"),
                trend="up",
                verification_status="verified",
                source_name="Market Survey",
                observed_at=datetime.now(timezone.utc),
            )
            s.add(r)
            await s.commit()

        # GET /api/v1/material-rates
        list_res = await api_client.get("/api/v1/material-rates", headers=headers)
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert len(list_data) >= 1
        assert list_data[0]["city"] == "Lahore"

        # GET /api/v1/material-rates/{rate_id}
        single_res = await api_client.get(f"/api/v1/material-rates/{rate_id}", headers=headers)
        assert single_res.status_code == 200
        single_data = single_res.json()
        assert single_data.get("ratePkr") == 1520.0 or single_data.get("rate_pkr") == "1520.00"

    @pytest.mark.asyncio
    async def test_snapshots_and_history_endpoints(self, api_client: AsyncClient, api_session_factory):
        token = await get_auth_token(api_client, "snap_user@tameerai.pk")
        headers = {"Authorization": f"Bearer {token}"}

        prod_id = uuid.uuid4()
        src_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        async with api_session_factory() as s:
            prod = MaterialRateProduct(
                id=prod_id,
                code="BRICK_CLAY_AWWAL",
                category="bricks",
                canonical_name="Awwal Clay Bricks",
                standard_unit="1000_bricks",
                is_active=True,
            )
            src = MaterialRateSource(
                id=src_id,
                code="PBS_STATISTICAL_SPI",
                name="Pakistan Bureau of Statistics",
                source_type="official",
                reliability_tier="authoritative",
                refresh_cadence="weekly",
                freshness_ttl_days=30,
                is_active=True,
            )
            obs = MaterialRateObservation(
                id=uuid.uuid4(),
                source_id=src_id,
                product_id=prod_id,
                city="Lahore",
                observed_price_pkr=Decimal("14500.00"),
                observed_unit="1000_bricks",
                normalized_price_pkr=Decimal("14500.00"),
                normalized_unit="1000_bricks",
                published_at=now,
                collected_at=now,
                verification_status="verified_quote",
                duplicate_fingerprint="fp_api_brick_1",
            )
            s.add_all([prod, src, obs])
            await s.commit()

        # Snapshots
        snap_res = await api_client.get("/api/v1/material-rates/snapshots?city=Lahore", headers=headers)
        assert snap_res.status_code == 200
        snap_data = snap_res.json()
        assert len(snap_data) >= 1

        # History
        hist_res = await api_client.get(
            "/api/v1/material-rates/history?product_code=BRICK_CLAY_AWWAL&city=Lahore",
            headers=headers,
        )
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        assert hist_data["total_observations"] >= 1

        # Compare
        comp_res = await api_client.get(
            "/api/v1/material-rates/compare?product_code=BRICK_CLAY_AWWAL",
            headers=headers,
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["product_code"] == "BRICK_CLAY_AWWAL"
