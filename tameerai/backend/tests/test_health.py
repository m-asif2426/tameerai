from starlette.testclient import TestClient


def test_health_endpoint_status(client: TestClient):
    """Verify that /api/v1/health returns 200 OK and valid health schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "TameerAI Backend"
    assert data["version"] == "1.0.0"
    assert data["environment"] == "development"
    assert "timestamp" in data


def test_cors_headers_on_health_endpoint(client: TestClient):
    """Verify that CORS headers are returned for allowed frontend origins."""
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_preflight_options(client: TestClient):
    """Verify that CORS preflight OPTIONS requests are accepted."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "GET" in response.headers.get("access-control-allow-methods", "")

