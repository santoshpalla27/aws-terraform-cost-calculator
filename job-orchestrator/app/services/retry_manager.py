"""
Retry manager with selective retry logic.

CRITICAL RULES:
- Terraform execution: NO RETRY (stateful, not idempotent)
- Plan parsing: NO RETRY (deterministic)
- Metadata/Pricing: RETRY with exponential backoff
"""
import asyncio
from typing import Callable, TypeVar, Set
from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryManager:
    """
    Manages retry logic for job steps.
    
    CRITICAL: Only retries steps that are safe to retry.
    """
    
    # Steps that should NEVER be retried
    NO_RETRY_STEPS: Set[str] = {
        "terraform_planning",  # Stateful, not idempotent
        "plan_parsing"         # Deterministic, no point retrying
    }
    
    # Steps that can be retried
    RETRY_STEPS: Set[str] = {
        "metadata_resolution",   # External API, transient failures
        "pricing_calculation",   # Database queries, can retry
        "cost_aggregation"       # Computation, safe to retry
    }
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        """
        Initialize retry manager.
        
        Args:
            max_attempts: Maximum retry attempts
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    def can_retry(self, step_name: str) -> bool:
        """
        Check if step can be retried.
        
        Args:
            step_name: Name of the step
            
        Returns:
            True if step can be retried
        """
        if step_name in self.NO_RETRY_STEPS:
            return False
        
        if step_name in self.RETRY_STEPS:
            return True
        
        # Default: no retry for unknown steps
        logger.warning(
            f"Unknown step {step_name}, defaulting to NO RETRY",
            extra={"step_name": step_name}
        )
        return False
    
    async def execute_with_retry(
        self,
        step_name: str,
        func: Callable[[], T],
        job_id: str,
        correlation_id: str
    ) -> T:
        """
        Execute function with retry logic.
        
        Args:
            step_name: Name of the step
            func: Async function to execute
            job_id: Job ID for logging
            correlation_id: Correlation ID for tracing
            
        Returns:
            Result from function
            
        Raises:
            Exception: If all retry attempts fail
        """
        # Check if step can be retried
        can_retry = self.can_retry(step_name)
        max_attempts = self.max_attempts if can_retry else 1
        
        logger.info(
            f"Executing {step_name} (max_attempts: {max_attempts})",
            extra={
                "job_id": job_id,
                "step_name": step_name,
                "can_retry": can_retry,
                "max_attempts": max_attempts,
                "correlation_id": correlation_id
            }
        )
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                result = await func()
                
                if attempt > 0:
                    logger.info(
                        f"Step {step_name} succeeded on attempt {attempt + 1}",
                        extra={
                            "job_id": job_id,
                            "step_name": step_name,
                            "attempt": attempt + 1,
                            "correlation_id": correlation_id
                        }
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_attempts - 1:
                    # Calculate backoff delay
                    delay = self.base_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"Step {step_name} failed on attempt {attempt + 1}, "
                        f"retrying in {delay}s: {str(e)}",
                        extra={
                            "job_id": job_id,
                            "step_name": step_name,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "error": str(e),
                            "correlation_id": correlation_id
                        }
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Step {step_name} failed after {max_attempts} attempts: {str(e)}",
                        extra={
                            "job_id": job_id,
                            "step_name": step_name,
                            "attempts": max_attempts,
                            "error": str(e),
                            "correlation_id": correlation_id
                        },
                        exc_info=True
                    )
        
        # All attempts failed
        raise last_exception


# Singleton instance
retry_manager = RetryManager()
