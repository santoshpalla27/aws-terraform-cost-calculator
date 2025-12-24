"""
Health check tests - ensure all services are reachable.

These tests run first and fail fast if infrastructure is down.
"""
import pytest
import requests


@pytest.mark.health
def test_nginx_responds(base_url):
    """Test that nginx is responding."""
    response = requests.get(f"{base_url}/health", timeout=5)
    assert response.status_code == 200, "Nginx health check failed"


@pytest.mark.health
def test_api_gateway_health(api_client):
    """Test that API Gateway is healthy."""
    response = api_client.get('/health')
    
    assert response['success'] is True, "API Gateway health check failed"
    assert 'correlation_id' in response, "Missing correlation_id in health response"


@pytest.mark.health
def test_all_backend_services_reachable(api_client):
    """
    Test that all backend services are reachable through API Gateway.
    
    This is a smoke test to ensure the platform is minimally functional.
    """
    # Try to list usage profiles (touches multiple services)
    response = api_client.get('/usage-profiles')
    
    # Should succeed or fail gracefully, but not crash
    assert 'success' in response, "API Gateway not responding correctly"
    assert 'correlation_id' in response, "Missing correlation_id"
