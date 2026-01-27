"""
Custom exception classes for Discogs API errors.

This module defines a hierarchy of exceptions for handling various
API error scenarios, including authentication, rate limiting, resource
not found, and server errors.
"""

from typing import Any, Dict, Optional


class DiscogsAPIException(Exception):
    """Base exception for all Discogs API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Initialize the Discogs API exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code if available
            response: Raw API response data
            request_id: Request correlation ID for tracing
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        self.request_id = request_id
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for logging.

        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "request_id": self.request_id,
        }

    def __str__(self) -> str:
        """Return string representation of the exception."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status Code: {self.status_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return " | ".join(parts)


class AuthenticationError(DiscogsAPIException):
    """
    Raised when authentication fails (401).

    This typically indicates an invalid or missing API token.
    """

    pass


class RateLimitError(DiscogsAPIException):
    """
    Raised when rate limit is exceeded (429).

    Includes information about when to retry the request.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments passed to base exception
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

    def to_dict(self) -> Dict[str, Any]:
        """Include retry_after in dictionary representation."""
        data = super().to_dict()
        data["retry_after"] = self.retry_after
        return data


class ResourceNotFoundError(DiscogsAPIException):
    """
    Raised when a requested resource is not found (404).

    This indicates the endpoint or resource ID does not exist.
    """

    pass


class BadRequestError(DiscogsAPIException):
    """
    Raised when the request is invalid (400).

    This typically indicates malformed parameters or invalid data.
    """

    pass


class ServerError(DiscogsAPIException):
    """
    Raised when a server error occurs (5xx).

    This indicates a temporary issue with the Discogs API servers.
    These errors are typically retryable.
    """

    pass


class NetworkError(DiscogsAPIException):
    """
    Raised when network communication fails.

    This includes connection timeouts, DNS failures, and other
    network-related issues.
    """

    pass


class ValidationError(DiscogsAPIException):
    """
    Raised when data validation fails.

    This typically indicates that API response data doesn't match
    the expected schema or contains invalid values.
    """

    pass
