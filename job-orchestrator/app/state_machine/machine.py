"""
State machine implementation.
Manages job state transitions with validation.
"""
from datetime import datetime
from typing import Optional
from app.state_machine.states import JobState
from app.state_machine.transitions import validate_transition, InvalidTransitionError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StateMachine:
    """State machine for job orchestration."""
    
    def __init__(self, job_id: str, current_state: JobState):
        self.job_id = job_id
        self.current_state = current_state
    
    def transition(
        self,
        to_state: JobState,
        error_message: Optional[str] = None
    ) -> None:
        """
        Transition to a new state.
        
        Args:
            to_state: Target state
            error_message: Error message if transitioning to FAILED
            
        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        # Validate transition
        validate_transition(self.current_state, to_state)
        
        # Log transition
        logger.info(
            f"State transition: {self.current_state} → {to_state}",
            extra={
                'job_id': self.job_id,
                'from_state': self.current_state.value,
                'to_state': to_state.value,
                'error_message': error_message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Update state
        previous_state = self.current_state
        self.current_state = to_state
        
        # Additional logging for terminal states
        if JobState.is_terminal(to_state):
            if to_state == JobState.COMPLETED:
                logger.info(
                    f"Job {self.job_id} completed successfully",
                    extra={'job_id': self.job_id}
                )
            elif to_state == JobState.FAILED:
                logger.error(
                    f"Job {self.job_id} failed: {error_message}",
                    extra={'job_id': self.job_id, 'error': error_message}
                )
    
    def can_transition_to(self, to_state: JobState) -> bool:
        """Check if transition to state is allowed."""
        from app.state_machine.transitions import can_transition
        return can_transition(self.current_state, to_state)
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal."""
        return JobState.is_terminal(self.current_state)
