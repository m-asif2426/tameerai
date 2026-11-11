from starlette.testclient import TestClient


def test_home_endpoint(client: TestClient):
    """Verify legacy root home endpoint continues to work."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "TameerAI Backend is Running 🚀"}


def test_legacy_prototype_routes_safely_unmounted_for_production_security(client: TestClient):
    """
    Verify that obsolete unauthenticated prototype routes (/projects) have been safely
    decommissioned in Phase 03.4E.2A.3 and cannot be accessed anonymously.
    All project workspace operations must use /api/v1/projects with JWT authentication.
    """
    assert client.get("/projects").status_code == 404
    assert client.get("/projects/1").status_code == 404
    assert client.post("/projects", json={"name": "test"}).status_code == 404
    assert client.put("/projects/1", json={"name": "test"}).status_code == 404
    assert client.delete("/projects/1").status_code == 404

