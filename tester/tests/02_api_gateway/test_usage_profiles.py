"""
API Gateway tests - authentication, rate limiting, validation.
"""
import pytest


@pytest.mark.api
def test_usage_profiles_endpoint(api_client, track_correlation):
    """Test that usage profiles endpoint works."""
    response = api_client.get('/usage-profiles')
    track_correlation(response, '/usage-profiles', 'GET')
    
    assert response['success'], "Failed to fetch usage profiles"
    assert isinstance(response['data'], list), "Usage profiles should be a list"


@pytest.mark.api
def test_cors_headers_present(api_client):
    """Test that CORS headers are present (for browser clients)."""
    import requests
    
    # Make OPTIONS request (preflight)
    response = requests.options(
        f"{api_client.base_url}/usage-profiles",
        headers={'Origin': 'http://localhost:3000'}
    )
    
    # Check for CORS headers
    assert 'Access-Control-Allow-Origin' in response.headers, \
        "Missing CORS header: Access-Control-Allow-Origin"


@pytest.mark.api
def test_input_validation_returns_error(api_client):
    """Test that invalid input returns proper error response."""
    # Try to create job with invalid data
    import requests
    
    response = requests.post(
        f"{api_client.base_url}/jobs",
        json={'invalid': 'data'}
    )
    
    # Should return error response (not 500)
    assert response.status_code in [400, 422], \
        f"Expected 400/422 for invalid input, got {response.status_code}"
