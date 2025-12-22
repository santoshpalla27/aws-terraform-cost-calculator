"""
Retry logic with exponential backoff.
"""
import asyncio
from typing import Callable, Any, TypeVar
from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


async def execute_with_retry(
    func: Callable[[], Any],
    max_retries: int,
    backoff_base: int = 2,
    stage_name: str = "unknown"
) -> Any:
    """
    Execute function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retries
        backoff_base: Base for exponential backoff
        stage_name: Name of stage for logging
        
    Returns:
        Function result
        
    Raises:
        Exception: If all retries exhausted
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Executing {stage_name} (attempt {attempt + 1}/{max_retries + 1})",
                extra={'stage': stage_name, 'attempt': attempt + 1}
            )
            
            result = await func()
            
            if attempt > 0:
                logger.info(
                    f"{stage_name} succeeded after {attempt} retries",
                    extra={'stage': stage_name, 'retries': attempt}
                )
            
            return result
        
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(
                    f"{stage_name} failed after {max_retries + 1} attempts: {str(e)}",
                    extra={'stage': stage_name, 'error': str(e)}
                )
                raise
            
            wait_time = backoff_base ** attempt
            logger.warning(
                f"{stage_name} failed (attempt {attempt + 1}), retrying in {wait_time}s",
                extra={
                    'stage': stage_name,
                    'attempt': attempt + 1,
                    'wait_time': wait_time,
                    'error': str(e)
                }
            )
            
            await asyncio.sleep(wait_time)
    
    # Should never reach here, but for type safety
    raise last_exception or Exception("Retry logic error")


async def execute_with_timeout(
    func: Callable[[], Any],
    timeout: int,
    stage_name: str = "unknown"
) -> Any:
    """
    Execute function with timeout.
    
    Args:
        func: Async function to execute
        timeout: Timeout in seconds
        stage_name: Name of stage for logging
        
    Returns:
        Function result
        
    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    try:
        result = await asyncio.wait_for(func(), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.error(
            f"{stage_name} timed out after {timeout}s",
            extra={'stage': stage_name, 'timeout': timeout}
        )
        raise
