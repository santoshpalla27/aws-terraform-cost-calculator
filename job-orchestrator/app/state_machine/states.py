"""
Job state enumeration.
STRICT finite state machine with 7 states.
"""
from enum import Enum


class JobState(str, Enum):
    """Job state enumeration - STRICT, no additions allowed."""
    
    CREATED = "CREATED"  # Initial state from API Gateway
    UPLOADED = "UPLOADED"
    PLANNING = "PLANNING"
    PARSING = "PARSING"
    ENRICHING = "ENRICHING"
    COSTING = "COSTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
    @classmethod
    def is_terminal(cls, state: "JobState") -> bool:
        """Check if state is terminal (no further transitions)."""
        return state in [cls.COMPLETED, cls.FAILED]
    
    @classmethod
    def get_next_state(cls, current: "JobState") -> "JobState":
        """
        Get the next state in the normal flow.
        
        Args:
            current: Current state
            
        Returns:
            Next state
            
        Raises:
            ValueError: If current state has no next state
        """
        transitions = {
            cls.CREATED: cls.PLANNING,  # API Gateway creates jobs in CREATED state
            cls.UPLOADED: cls.PLANNING,
            cls.PLANNING: cls.PARSING,
            cls.PARSING: cls.ENRICHING,
            cls.ENRICHING: cls.COSTING,
            cls.COSTING: cls.COMPLETED,
        }
        
        if current not in transitions:
            raise ValueError(f"State {current} has no next state")
        
        return transitions[current]
