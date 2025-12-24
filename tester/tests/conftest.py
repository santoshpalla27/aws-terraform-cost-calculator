"""
Pytest configuration and shared fixtures.
"""
import pytest
from utils.api_client import PlatformClient
from utils.correlation import get_tracker, print_correlation_summary


@pytest.fixture(scope="session")
def api_client():
    """Create API client for testing."""
    return PlatformClient()


@pytest.fixture(scope="session")
def base_url():
    """Get base URL from environment."""
    import os
    return os.getenv('BASE_URL', 'http://nginx')


@pytest.fixture(autouse=True, scope="session")
def print_summary_at_end():
    """Print correlation ID summary at end of test session."""
    yield
    print_correlation_summary()


@pytest.fixture
def track_correlation(api_client):
    """Fixture to track correlation IDs."""
    tracker = get_tracker()
    
    def _track(response, endpoint, method):
        correlation_id = api_client.get_correlation_id(response)
        success = response.get('success', False)
        tracker.track(correlation_id, endpoint, method, success)
        return correlation_id
    
    return _track
