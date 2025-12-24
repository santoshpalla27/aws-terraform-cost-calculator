"""
Custom assertions for platform testing.
"""
import uuid
from typing import Dict, List, Optional


# CANONICAL JOB STATE SEQUENCE - HARD INVARIANT
CANONICAL_STATE_SEQUENCE = [
    'UPLOADED',
    'PLANNING',
    'PARSING',
    'ENRICHING',
    'PRICING',
    'COSTING',
    'COMPLETED'
]

# Progress bounds per state (min, max)
STATE_PROGRESS_BOUNDS = {
    'UPLOADED': (0, 10),
    'PLANNING': (10, 20),
    'PARSING': (20, 40),
    'ENRICHING': (40, 60),
    'PRICING': (60, 75),
    'COSTING': (75, 95),
    'COMPLETED': (100, 100),
    'FAILED': (0, 100)  # Can fail at any progress
}

# Valid job state transitions (for backward compatibility)
VALID_TRANSITIONS = {
    'UPLOADED': ['PLANNING', 'FAILED'],
    'PLANNING': ['PARSING', 'FAILED'],
    'PARSING': ['ENRICHING', 'FAILED'],
    'ENRICHING': ['PRICING', 'FAILED'],
    'PRICING': ['COSTING', 'FAILED'],
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


def assert_canonical_state_sequence(state_history: List[str], correlation_id: str = None):
    """
    Assert job followed canonical state sequence with NO SKIPS.
    
    HARD INVARIANTS:
    - States must follow CANONICAL_STATE_SEQUENCE order
    - No states can be skipped (except FAILED)
    - No backward transitions
    - Terminal state reached exactly once
    
    Args:
        state_history: List of states in order observed
        correlation_id: Optional correlation ID for debugging
        
    Raises:
        AssertionError: If sequence violated
    """
    if not state_history:
        raise AssertionError("State history is empty")
    
    # Remove duplicates while preserving order
    unique_states = []
    for state in state_history:
        if not unique_states or unique_states[-1] != state:
            unique_states.append(state)
    
    # Check if ended in FAILED
    if unique_states[-1] == 'FAILED':
        # FAILED is allowed from any non-terminal state
        # Verify all states before FAILED are in canonical order
        states_before_fail = unique_states[:-1]
        if states_before_fail:
            _validate_canonical_order(states_before_fail, correlation_id, allow_incomplete=True)
        return
    
    # Check if ended in COMPLETED
    if unique_states[-1] == 'COMPLETED':
        # Must have gone through ALL canonical states
        _validate_canonical_order(unique_states, correlation_id, allow_incomplete=False)
        return
    
    # Job hasn't reached terminal state yet - validate partial sequence
    _validate_canonical_order(unique_states, correlation_id, allow_incomplete=True)


def _validate_canonical_order(states: List[str], correlation_id: Optional[str], allow_incomplete: bool):
    """
    Validate states follow canonical order.
    
    Args:
        states: List of states to validate
        correlation_id: Optional correlation ID for debugging
        allow_incomplete: If True, allow partial sequence
        
    Raises:
        AssertionError: If order violated
    """
    # Map states to their canonical indices
    state_indices = []
    for state in states:
        if state == 'FAILED':
            continue  # Skip FAILED in sequence check
        
        if state not in CANONICAL_STATE_SEQUENCE:
            raise AssertionError(
                f"Unknown state '{state}' not in canonical sequence. "
                f"correlation_id={correlation_id}"
            )
        
        state_indices.append(CANONICAL_STATE_SEQUENCE.index(state))
    
    # Verify strictly increasing (no skips, no backward)
    for i in range(len(state_indices) - 1):
        current_idx = state_indices[i]
        next_idx = state_indices[i + 1]
        
        # Check for backward transition
        if next_idx < current_idx:
            raise AssertionError(
                f"BACKWARD TRANSITION: {CANONICAL_STATE_SEQUENCE[current_idx]} → "
                f"{CANONICAL_STATE_SEQUENCE[next_idx]}. correlation_id={correlation_id}"
            )
        
        # Check for skipped state
        if next_idx - current_idx > 1:
            skipped_states = [
                CANONICAL_STATE_SEQUENCE[j] 
                for j in range(current_idx + 1, next_idx)
            ]
            raise AssertionError(
                f"SKIPPED STATES: {CANONICAL_STATE_SEQUENCE[current_idx]} → "
                f"{CANONICAL_STATE_SEQUENCE[next_idx]}. "
                f"Skipped: {skipped_states}. correlation_id={correlation_id}"
            )
    
    # If not allowing incomplete, verify reached COMPLETED
    if not allow_incomplete:
        if states[-1] != 'COMPLETED':
            raise AssertionError(
                f"Job did not reach COMPLETED. Last state: {states[-1]}. "
                f"correlation_id={correlation_id}"
            )
        
        # Verify ALL canonical states were visited
        if len(state_indices) != len(CANONICAL_STATE_SEQUENCE):
            missing_states = [
                CANONICAL_STATE_SEQUENCE[i]
                for i in range(len(CANONICAL_STATE_SEQUENCE))
                if i not in state_indices
            ]
            raise AssertionError(
                f"Not all canonical states visited. Missing: {missing_states}. "
                f"correlation_id={correlation_id}"
            )


def assert_progress_in_bounds(state: str, progress: float):
    """
    Assert progress is within valid bounds for state.
    
    Args:
        state: Current job state
        progress: Current progress value
        
    Raises:
        AssertionError: If progress out of bounds
    """
    if state not in STATE_PROGRESS_BOUNDS:
        # Unknown state, skip bounds check
        return
    
    min_progress, max_progress = STATE_PROGRESS_BOUNDS[state]
    
    assert min_progress <= progress <= max_progress, \
        f"Progress {progress}% out of bounds for state {state}. " \
        f"Expected: {min_progress}-{max_progress}%"


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
