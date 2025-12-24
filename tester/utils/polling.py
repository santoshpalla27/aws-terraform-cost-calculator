"""
Polling utilities with exponential backoff.
"""
import asyncio
import time
from typing import Callable, Any, Optional


async def poll_until(
    check_fn: Callable[[], Any],
    condition_fn: Callable[[Any], bool] = None,
    max_attempts: int = 100,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    timeout: float = 300.0
) -> Any:
    """
    Poll until condition is met with exponential backoff.
    
    Args:
        check_fn: Function to call for checking
        condition_fn: Function to test result (default: truthy check)
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        timeout: Total timeout in seconds
        
    Returns:
        Result from check_fn when condition is met
        
    Raises:
        TimeoutError: If condition not met within attempts/timeout
    """
    if condition_fn is None:
        condition_fn = lambda x: bool(x)
    
    start_time = time.time()
    
    for attempt in range(max_attempts):
        # Check timeout
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Polling timed out after {timeout}s")
        
        # Execute check
        result = check_fn()
        
        # Test condition
        if condition_fn(result):
            return result
        
        # Calculate delay with exponential backoff
        delay = min(initial_delay * (2 ** attempt), max_delay)
        
        # Sleep
        await asyncio.sleep(delay)
    
    raise TimeoutError(f"Polling failed after {max_attempts} attempts")


def poll_until_sync(
    check_fn: Callable[[], Any],
    condition_fn: Callable[[Any], bool] = None,
    max_attempts: int = 100,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    timeout: float = 300.0
) -> Any:
    """
    Synchronous version of poll_until.
    
    Args:
        check_fn: Function to call for checking
        condition_fn: Function to test result (default: truthy check)
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        timeout: Total timeout in seconds
        
    Returns:
        Result from check_fn when condition is met
        
    Raises:
        TimeoutError: If condition not met within attempts/timeout
    """
    if condition_fn is None:
        condition_fn = lambda x: bool(x)
    
    start_time = time.time()
    
    for attempt in range(max_attempts):
        # Check timeout
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Polling timed out after {timeout}s")
        
        # Execute check
        result = check_fn()
        
        # Test condition
        if condition_fn(result):
            return result
        
        # Calculate delay with exponential backoff
        delay = min(initial_delay * (2 ** attempt), max_delay)
        
        # Sleep
        time.sleep(delay)
    
    raise TimeoutError(f"Polling failed after {max_attempts} attempts")
