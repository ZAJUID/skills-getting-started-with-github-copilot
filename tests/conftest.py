"""
Pytest configuration and shared fixtures for FastAPI tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient for the FastAPI app.
    This client can be used to make requests to the app in tests.
    """
    return TestClient(app)
