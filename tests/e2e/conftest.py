"""
TechCorp Customer Success AI Agent - E2E Test Fixtures

Lightweight fixtures for API-focused E2E tests.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="function")
def client():
    """Create a fresh test client for each test."""
    with TestClient(app) as test_client:
        yield test_client
