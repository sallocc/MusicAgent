"""
Rate limiting implementation using token bucket algorithm.

This module provides thread-safe rate limiting to prevent exceeding
Discogs API rate limits (60 requests per minute for authenticated users).
"""

import time
import threading
from collections import deque
from typing import Dict, Any


class RateLimiter:
    """
    Token bucket rate limiter for API requests.

    This implementation ensures requests don't exceed the configured rate limit
    by tracking request timestamps and blocking when the limit is reached.
    """

    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Blocks if rate limit would be exceeded until a slot becomes available.
        This method is thread-safe.
        """
        with self._lock:
            now = time.time()

            # Remove requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            # Wait if at limit
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    # Release lock while sleeping to allow other threads
                    self._lock.release()
                    try:
                        time.sleep(sleep_time)
                    finally:
                        self._lock.acquire()
                    # Recursively try again after sleeping
                    return self.acquire()

            # Record this request
            self.requests.append(now)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current rate limiter status.

        Returns:
            Dictionary with current status information
        """
        with self._lock:
            now = time.time()

            # Clean old requests
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            requests_made = len(self.requests)
            requests_remaining = self.max_requests - requests_made

            return {
                "requests_made": requests_made,
                "requests_remaining": requests_remaining,
                "time_window": self.time_window,
                "reset_time": (
                    self.requests[0] + self.time_window if self.requests else now
                ),
            }

    def wait_if_needed(self) -> float:
        """
        Check if waiting is needed without blocking.

        Returns:
            Seconds to wait, or 0.0 if no waiting needed
        """
        with self._lock:
            now = time.time()

            # Clean old requests
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            if len(self.requests) >= self.max_requests:
                return max(0.0, self.time_window - (now - self.requests[0]))

            return 0.0

    def reset(self) -> None:
        """Reset the rate limiter by clearing all recorded requests."""
        with self._lock:
            self.requests.clear()
