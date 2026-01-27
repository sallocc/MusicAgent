"""
Retry logic with exponential backoff and jitter.

This module provides decorators and utilities for retrying failed
API requests with exponential backoff to handle transient failures.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type, Union

from musicagent.exceptions import DiscogsAPIException

logger = logging.getLogger(__name__)


def calculate_backoff(
    attempt: int, backoff_factor: float = 2.0, max_delay: int = 60
) -> float:
    """
    Calculate exponential backoff with jitter.

    Args:
        attempt: Current attempt number (1-indexed)
        backoff_factor: Exponential backoff multiplier
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds with jitter applied
    """
    # Exponential backoff: backoff_factor ^ (attempt - 1)
    delay = min(backoff_factor ** (attempt - 1), max_delay)

    # Add jitter (0-25% of delay) to avoid thundering herd
    jitter = random.uniform(0, delay * 0.25)

    return delay + jitter


def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    retry_on_status_codes: Optional[list] = None,
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        retry_on_exceptions: Tuple of exception types to retry on
        retry_on_status_codes: List of HTTP status codes to retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_failure(max_retries=3, backoff_factor=2)
        def api_call():
            return requests.get("https://api.example.com")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            # Initial attempt + retries
            for attempt in range(1, max_retries + 2):
                try:
                    return func(*args, **kwargs)

                except retry_on_exceptions as e:
                    last_exception = e

                    # Check if we should retry based on status code
                    if retry_on_status_codes and hasattr(e, "status_code"):
                        status_code = getattr(e, "status_code")
                        if status_code not in retry_on_status_codes:
                            # Don't retry this status code
                            raise

                    # Don't retry after last attempt
                    if attempt > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Calculate backoff delay
                    delay = calculate_backoff(attempt, backoff_factor)

                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # Should not reach here, but raise last exception if we do
            if last_exception:
                raise last_exception

            # This should never be reached
            raise RuntimeError("Unexpected retry loop exit")

        return wrapper

    return decorator


class RetryStrategy:
    """
    Configurable retry strategy for API calls.

    This class provides a more flexible approach to retries
    compared to the decorator, allowing for runtime configuration.
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        max_delay: int = 60,
        retry_on_status_codes: Optional[list] = None,
    ):
        """
        Initialize retry strategy.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            max_delay: Maximum delay in seconds
            retry_on_status_codes: List of HTTP status codes to retry
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retry_on_status_codes = retry_on_status_codes or [
            429,
            500,
            502,
            503,
            504,
        ]

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if a request should be retried.

        Args:
            exception: Exception that occurred
            attempt: Current attempt number

        Returns:
            True if should retry, False otherwise
        """
        if attempt > self.max_retries:
            return False

        # Check status code if available
        if hasattr(exception, "status_code"):
            status_code = getattr(exception, "status_code")
            return status_code in self.retry_on_status_codes

        # Retry on network errors
        return True

    def get_delay(self, attempt: int) -> float:
        """
        Get delay for the next retry attempt.

        Args:
            attempt: Current attempt number

        Returns:
            Delay in seconds
        """
        return calculate_backoff(attempt, self.backoff_factor, self.max_delay)
