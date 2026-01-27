"""
MusicAgent - A foundational Python application for interacting with the Discogs API.

This package provides a robust, production-ready framework for making authenticated
requests to the Discogs API with built-in rate limiting, error handling, and data
validation.
"""

__version__ = "0.1.0"
__author__ = "Simon Allocca"

from .client.http_client import DiscogsHTTPClient
from .client.request_builder import RequestBuilder
from .models.base import BaseDiscogsModel
from .exceptions.api_exceptions import (
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
    "DiscogsHTTPClient",
    "RequestBuilder",
    "BaseDiscogsModel",
    "DiscogsAPIException",
    "AuthenticationError",
    "RateLimitError",
    "ResourceNotFoundError",
    "BadRequestError",
    "ServerError",
    "NetworkError",
    "ValidationError",
]
