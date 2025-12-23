"""
Retry handler for AWS API calls with exponential backoff.
"""
from typing import Any, Callable, TypeVar
from botocore.exceptions import ClientError
from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryHandler:
    """Handles retries for AWS API calls."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: int = 2):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def execute_with_retry(
        self,
        func: Callable[[], T],
        operation_name: str = "AWS API call"
    ) -> T:
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute (synchronous)
            operation_name: Name of operation for logging
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func()
                
                if attempt > 0:
                    logger.info(
                        f"{operation_name} succeeded after {attempt} retries"
                    )
                
                return result
            
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                # Check if error is retryable
                if self._is_retryable(error_code):
                    last_exception = e
                    
                    if attempt < self.max_retries:
                        wait_time = self.backoff_factor ** attempt
                        logger.warning(
                            f"{operation_name} failed with {error_code}, "
                            f"retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        import time
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"{operation_name} failed after {self.max_retries} retries"
                        )
                else:
                    # Non-retryable error
                    logger.error(f"{operation_name} failed with non-retryable error: {error_code}")
                    raise
            
            except Exception as e:
                logger.error(f"{operation_name} failed with unexpected error: {e}")
                raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        
        raise Exception(f"{operation_name} failed after all retries")
    
    def _is_retryable(self, error_code: str) -> bool:
        """
        Check if error code is retryable.
        
        Args:
            error_code: AWS error code
            
        Returns:
            True if retryable
        """
        retryable_errors = {
            'Throttling',
            'ThrottlingException',
            'RequestLimitExceeded',
            'TooManyRequestsException',
            'ProvisionedThroughputExceededException',
            'RequestThrottled',
            'ServiceUnavailable',
            'InternalError',
            'InternalServerError'
        }
        
        return error_code in retryable_errors
