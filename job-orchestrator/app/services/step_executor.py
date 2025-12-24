"""
Step execution with timeout enforcement.

CRITICAL: All steps execute with timeouts to prevent hanging jobs.
"""
import asyncio
from typing import Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Step timeout configuration (seconds)
STEP_TIMEOUTS = {
    "terraform_planning": 600,      # 10 minutes
    "plan_parsing": 120,            # 2 minutes
    "metadata_resolution": 300,     # 5 minutes
    "pricing_calculation": 180,     # 3 minutes
    "cost_aggregation": 120         # 2 minutes
}


@dataclass
class StepResult:
    """Result of step execution."""
    success: bool
    data: Optional[Any] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


class StepExecutor:
    """
    Executes job steps with timeout enforcement.
    
    CRITICAL: Steps that exceed timeout are terminated and marked as failed.
    """
    
    async def execute_step(
        self,
        step_name: str,
        func: Callable,
        job_id: str,
        correlation_id: str,
        timeout: Optional[int] = None
    ) -> StepResult:
        """
        Execute a step with timeout.
        
        Args:
            step_name: Name of the step
            func: Async function to execute
            job_id: Job ID for logging
            correlation_id: Correlation ID for tracing
            timeout: Timeout in seconds (uses default if not provided)
            
        Returns:
            StepResult with success/failure info
        """
        # Get timeout
        timeout_seconds = timeout or STEP_TIMEOUTS.get(step_name, 300)
        
        logger.info(
            f"Executing step: {step_name} (timeout: {timeout_seconds}s)",
            extra={
                "job_id": job_id,
                "step_name": step_name,
                "timeout": timeout_seconds,
                "correlation_id": correlation_id
            }
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(),
                timeout=timeout_seconds
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Step {step_name} completed successfully ({execution_time:.2f}s)",
                extra={
                    "job_id": job_id,
                    "step_name": step_name,
                    "execution_time": execution_time,
                    "correlation_id": correlation_id
                }
            )
            
            return StepResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                f"Step {step_name} timed out after {timeout_seconds}s",
                extra={
                    "job_id": job_id,
                    "step_name": step_name,
                    "timeout": timeout_seconds,
                    "correlation_id": correlation_id
                }
            )
            
            return StepResult(
                success=False,
                error_code="STEP_TIMEOUT",
                error_message=f"Step {step_name} exceeded timeout of {timeout_seconds}s",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                f"Step {step_name} failed: {str(e)}",
                extra={
                    "job_id": job_id,
                    "step_name": step_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            
            return StepResult(
                success=False,
                error_code="STEP_EXECUTION_ERROR",
                error_message=str(e),
                execution_time=execution_time
            )


# Singleton instance
step_executor = StepExecutor()
