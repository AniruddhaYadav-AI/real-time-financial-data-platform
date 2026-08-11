from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test that GET /health returns 200 OK and expected status response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "version" in data
