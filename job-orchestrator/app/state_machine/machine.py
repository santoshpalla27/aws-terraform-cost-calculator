"""
State machine implementation with ATOMIC transitions.

CRITICAL PATTERN:
1. Acquire distributed lock
2. Load current state from DB
3. Validate transition
4. Persist new state to DB
5. Release lock
6. Call downstream service

This ensures state is persisted BEFORE any side effects.
"""
from datetime import datetime
from typing import Optional
import uuid
from app.state_machine.states import JobState
from app.state_machine.transitions import validate_transition, InvalidTransitionError
from app.models.job import Job, StateTransition
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StateMachine:
    """
    Atomic state machine for job orchestration.
    
    CRITICAL: All transitions are atomic and persisted before execution.
    """
    
    def __init__(self, job_repo, lock_manager, transition_repo=None):
        """
        Initialize state machine.
        
        Args:
            job_repo: Job repository for persistence
            lock_manager: Distributed lock manager
            transition_repo: State transition audit log repository
        """
        self.job_repo = job_repo
        self.lock_manager = lock_manager
        self.transition_repo = transition_repo
    
    async def transition(
        self,
        job_id: str,
        to_state: JobState,
        correlation_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        progress: Optional[int] = None
    ) -> Job:
        """
        Atomically transition job to new state.
        
        CRITICAL: State is persisted to database BEFORE any downstream calls.
        
        Args:
            job_id: Job ID
            to_state: Target state
            correlation_id: Request correlation ID
            error_code: Error code if transitioning to FAILED
            error_message: Error message if transitioning to FAILED
            progress: Optional progress override (0-100)
            
        Returns:
            Updated job
            
        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        # Acquire distributed lock
        async with self.lock_manager.acquire(f"job:{job_id}"):
            # 1. Load current state from database
            job = await self.job_repo.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            from_state = job.current_state
            
            # 2. Validate transition
            validate_transition(from_state, to_state)
            
            logger.info(
                f"State transition: {from_state} → {to_state}",
                extra={
                    'job_id': job_id,
                    'from_state': from_state.value,
                    'to_state': to_state.value,
                    'correlation_id': correlation_id
                }
            )
            
            # 3. Update job state
            job.previous_state = from_state
            job.current_state = to_state
            job.updated_at = datetime.utcnow()
            job.correlation_id = correlation_id
            
            # Update progress
            if progress is not None:
                job.progress = progress
            else:
                # Auto-calculate progress based on state
                job.progress = self._calculate_progress(to_state)
            
            # Handle terminal states
            if to_state == JobState.COMPLETED:
                job.completed_at = datetime.utcnow()
                job.progress = 100
            elif to_state == JobState.FAILED:
                job.failed_at = datetime.utcnow()
                job.error_code = error_code
                job.error_message = error_message
                job.progress = 0
            
            # 4. Persist to database FIRST
            await self.job_repo.update(job)
            
            # 5. Log transition (audit trail)
            if self.transition_repo:
                transition = StateTransition(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    from_state=from_state,
                    to_state=to_state,
                    timestamp=datetime.utcnow(),
                    correlation_id=correlation_id,
                    success=to_state != JobState.FAILED,
                    error=error_message
                )
                await self.transition_repo.create(transition)
            
            # Log terminal states
            if JobState.is_terminal(to_state):
                if to_state == JobState.COMPLETED:
                    logger.info(
                        f"Job {job_id} completed successfully",
                        extra={'job_id': job_id, 'correlation_id': correlation_id}
                    )
                elif to_state == JobState.FAILED:
                    logger.error(
                        f"Job {job_id} failed: {error_message}",
                        extra={
                            'job_id': job_id,
                            'error_code': error_code,
                            'error': error_message,
                            'correlation_id': correlation_id
                        }
                    )
            
            return job
    
    def _calculate_progress(self, state: JobState) -> int:
        """Calculate progress percentage based on state."""
        progress_map = {
            JobState.UPLOADED: 10,
            JobState.PLANNING: 20,
            JobState.PARSING: 40,
            JobState.ENRICHING: 60,
            JobState.COSTING: 80,
            JobState.COMPLETED: 100,
            JobState.FAILED: 0
        }
        return progress_map.get(state, 0)
    
    async def can_transition_to(self, job_id: str, to_state: JobState) -> bool:
        """
        Check if job can transition to state.
        
        Args:
            job_id: Job ID
            to_state: Target state
            
        Returns:
            True if transition is allowed
        """
        job = await self.job_repo.get(job_id)
        if not job:
            return False
        
        from app.state_machine.transitions import can_transition
        return can_transition(job.current_state, to_state)
    
    async def is_terminal(self, job_id: str) -> bool:
        """
        Check if job is in terminal state.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if job is in terminal state
        """
        job = await self.job_repo.get(job_id)
        if not job:
            return False
        
        return JobState.is_terminal(job.current_state)

