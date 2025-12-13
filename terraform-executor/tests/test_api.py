"""Tests for API endpoints."""

from fastapi import status


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "terraform_version" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_execute_endpoint_invalid_upload(client):
    """Test execute endpoint with invalid upload ID."""
    response = client.post(
        "/api/v1/execute",
        json={
            "job_id": "test_job",
            "upload_id": "nonexistent_upload"
        }
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
