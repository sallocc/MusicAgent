"""Custom exception classes for Discogs API errors."""

from .api_exceptions import (
    DiscogsAPIException,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    BadRequestError,
    ServerError,
    NetworkError,
    ValidationError,
)

__all__ = [
    "DiscogsAPIException",
    "AuthenticationError",
    "RateLimitError",
    "ResourceNotFoundError",
    "BadRequestError",
    "ServerError",
    "NetworkError",
    "ValidationError",
]
