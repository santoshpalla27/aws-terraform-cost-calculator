"""
Custom assertions for platform testing.
"""
import uuid
from typing import Dict, List


# Valid job state transitions
VALID_TRANSITIONS = {
    'UPLOADED': ['PLANNING', 'FAILED'],
    'PLANNING': ['PARSING', 'FAILED'],
    'PARSING': ['ENRICHING', 'FAILED'],
    'ENRICHING': ['COSTING', 'FAILED'],
    'COSTING': ['COMPLETED', 'FAILED'],
    'COMPLETED': [],  # Terminal
    'FAILED': []      # Terminal
}


def assert_valid_state_transition(from_state: str, to_state: str):
    """
    Assert job state transition is valid.
    
    Args:
        from_state: Current state
        to_state: Next state
        
    Raises:
        AssertionError: If transition is invalid
    """
    valid_next_states = VALID_TRANSITIONS.get(from_state, [])
    assert to_state in valid_next_states, \
        f"Invalid state transition: {from_state} → {to_state}. Valid: {valid_next_states}"


def assert_correlation_id(response: dict):
    """
    Assert correlation_id exists and is valid UUID.
    
    Args:
        response: API response
        
    Raises:
        AssertionError: If correlation_id missing or invalid
    """
    assert 'correlation_id' in response, "Missing correlation_id in response"
    
    correlation_id = response['correlation_id']
    try:
        uuid.UUID(correlation_id)
    except (ValueError, AttributeError):
        raise AssertionError(f"Invalid correlation_id format: {correlation_id}")


def assert_api_success(response: dict):
    """
    Assert API response indicates success.
    
    Args:
        response: API response
        
    Raises:
        AssertionError: If response indicates failure
    """
    assert response.get('success') is True, \
        f"API call failed: {response.get('error', {}).get('message', 'Unknown error')}"


def assert_api_failure(response: dict, expected_code: str = None):
    """
    Assert API response indicates failure.
    
    Args:
        response: API response
        expected_code: Optional expected error code
        
    Raises:
        AssertionError: If response indicates success or wrong error code
    """
    assert response.get('success') is False, "Expected API failure but got success"
    assert response.get('error') is not None, "Missing error object in failure response"
    
    if expected_code:
        actual_code = response['error'].get('code')
        assert actual_code == expected_code, \
            f"Expected error code '{expected_code}' but got '{actual_code}'"


def assert_no_forbidden_fields(data: dict, forbidden: List[str]):
    """
    Assert response doesn't contain forbidden fields.
    
    Args:
        data: Response data
        forbidden: List of forbidden field names
        
    Raises:
        AssertionError: If forbidden fields present
    """
    found_forbidden = [field for field in forbidden if field in data]
    assert not found_forbidden, \
        f"Response contains forbidden fields: {found_forbidden}"


def assert_monotonic_progress(old_progress: float, new_progress: float):
    """
    Assert progress is monotonically increasing.
    
    Args:
        old_progress: Previous progress value
        new_progress: New progress value
        
    Raises:
        AssertionError: If progress decreased
    """
    assert new_progress >= old_progress, \
        f"Progress decreased: {old_progress} → {new_progress}"


def assert_terminal_state(state: str):
    """
    Assert state is terminal (COMPLETED or FAILED).
    
    Args:
        state: Job state
        
    Raises:
        AssertionError: If state is not terminal
    """
    assert state in ['COMPLETED', 'FAILED'], \
        f"Expected terminal state but got: {state}"


def assert_immutable_result(result_id: str, old_data: dict, new_data: dict):
    """
    Assert result data hasn't changed (immutability).
    
    Args:
        result_id: Result identifier
        old_data: Original result data
        new_data: New result data
        
    Raises:
        AssertionError: If data has changed
    """
    assert old_data == new_data, \
        f"Result {result_id} was mutated! Immutability violated."
