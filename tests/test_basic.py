"""
Basic tests for Moni-Personal-GCP application
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data


def test_ping_endpoint():
    """Test ping endpoint"""
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "timestamp" in data


def test_root_redirect():
    """Test root endpoint redirects to login"""
    response = client.get("/", allow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


def test_invalid_endpoint():
    """Test 404 for invalid endpoints"""
    response = client.get("/invalid-endpoint-12345")
    assert response.status_code == 404