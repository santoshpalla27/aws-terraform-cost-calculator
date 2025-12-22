"""
State transition validation.
Enforces allowed transitions and rejects invalid ones.
"""
from typing import Dict, List
from app.state_machine.states import JobState


# ALLOWED TRANSITIONS - STRICT mapping
ALLOWED_TRANSITIONS: Dict[JobState, List[JobState]] = {
    JobState.UPLOADED: [JobState.PLANNING, JobState.FAILED],
    JobState.PLANNING: [JobState.PARSING, JobState.FAILED],
    JobState.PARSING: [JobState.ENRICHING, JobState.FAILED],
    JobState.ENRICHING: [JobState.COSTING, JobState.FAILED],
    JobState.COSTING: [JobState.COMPLETED, JobState.FAILED],
    JobState.COMPLETED: [],  # Terminal state
    JobState.FAILED: [],     # Terminal state
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


def validate_transition(from_state: JobState, to_state: JobState) -> None:
    """
    Validate a state transition.
    
    Args:
        from_state: Current state
        to_state: Target state
        
    Raises:
        InvalidTransitionError: If transition is not allowed
    """
    allowed = ALLOWED_TRANSITIONS.get(from_state, [])
    
    if to_state not in allowed:
        raise InvalidTransitionError(
            f"Invalid transition from {from_state} to {to_state}. "
            f"Allowed transitions: {[s.value for s in allowed]}"
        )


def can_transition(from_state: JobState, to_state: JobState) -> bool:
    """
    Check if a transition is allowed.
    
    Args:
        from_state: Current state
        to_state: Target state
        
    Returns:
        True if transition is allowed, False otherwise
    """
    allowed = ALLOWED_TRANSITIONS.get(from_state, [])
    return to_state in allowed


def get_allowed_transitions(state: JobState) -> List[JobState]:
    """
    Get all allowed transitions from a state.
    
    Args:
        state: Current state
        
    Returns:
        List of allowed target states
    """
    return ALLOWED_TRANSITIONS.get(state, [])
