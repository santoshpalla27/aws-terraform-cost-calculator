"""Tests for health endpoints."""

from fastapi import status


def test_health_check(client):
    """Test basic health check."""
    response = client.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check(client):
    """Test readiness probe."""
    response = client.get("/health/ready")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"


def test_liveness_check(client):
    """Test liveness probe."""
    response = client.get("/health/live")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "alive"
