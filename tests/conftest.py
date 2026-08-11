import pytest
from fastapi.testclient import TestClient

from financial_platform.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture to provide a test client for FastAPI application."""
    return TestClient(app)
