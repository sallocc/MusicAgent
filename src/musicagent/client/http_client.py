"""
HTTP client for Discogs API with authentication, rate limiting, and error handling.

This module provides the main client class for making authenticated requests
to the Discogs API with built-in rate limiting, retry logic, and comprehensive
error handling.
"""

import uuid
import time
from typing import Dict, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.settings import settings
from ..utils.rate_limiter import RateLimiter
from ..utils.logger import setup_logger, RequestLogger
from ..exceptions.api_exceptions import (
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    BadRequestError,
    ServerError,
    NetworkError,
)


class DiscogsHTTPClient:
    """
    Main HTTP client for Discogs API.

    This client handles authentication, rate limiting, error handling,
    and request/response logging for all API interactions.
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        user_agent: Optional[str] = None,
        rate_limit: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize HTTP client.

        Args:
            api_token: Discogs API personal access token
            user_agent: User agent string for requests
            rate_limit: Maximum requests per minute
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_token = api_token or settings.DISCOGS_API_TOKEN
        self.user_agent = user_agent or settings.DISCOGS_USER_AGENT
        self.base_url = settings.DISCOGS_BASE_URL

        # Validate required configuration
        if not self.api_token:
            raise ValueError(
                "Discogs API token is required. Set DISCOGS_API_TOKEN in .env file."
            )

        # Set up rate limiter
        rate_limit = rate_limit or settings.RATE_LIMIT_REQUESTS
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit, time_window=settings.RATE_LIMIT_WINDOW
        )

        # Set up logging
        self.logger = setup_logger(
            log_level=settings.LOG_LEVEL,
            log_dir=settings.LOG_DIR,
            log_file=settings.LOG_FILE_NAME,
            error_log_file=settings.LOG_ERROR_FILE,
            max_bytes=settings.LOG_ROTATION_SIZE,
            backup_count=settings.LOG_BACKUP_COUNT,
            log_format=settings.LOG_FORMAT,
        )
        self.request_logger = RequestLogger(self.logger)

        # Create session with retry configuration
        self.session = self._create_session(max_retries)

    def _create_session(
        self, max_retries: Optional[int] = None
    ) -> requests.Session:
        """
        Create configured requests session with connection pooling.

        Args:
            max_retries: Maximum retry attempts

        Returns:
            Configured session
        """
        session = requests.Session()

        # Set default headers
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Authorization": f"Discogs token={self.api_token}",
            }
        )

        # Configure retry strategy for connection errors
        max_retries = max_retries or settings.MAX_RETRIES
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request to API.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            Various API exceptions based on response status
        """
        return self._make_request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request to API.

        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json: JSON data

        Returns:
            Response data as dictionary
        """
        return self._make_request("POST", endpoint, data=data, json=json)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request to API.

        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json: JSON data

        Returns:
            Response data as dictionary
        """
        return self._make_request("PUT", endpoint, data=data, json=json)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make DELETE request to API.

        Args:
            endpoint: API endpoint (without base URL)

        Returns:
            Response data as dictionary
        """
        return self._make_request("DELETE", endpoint)

    def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response data as dictionary

        Raises:
            NetworkError: On network communication failure
            Various API exceptions based on response status
        """
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())

        # Construct full URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Apply rate limiting
        self.rate_limiter.acquire()

        # Log request
        # Disabling logging for MCP integration due to JSON-RPC errors
        # self.request_logger.log_request(
        #     method=method,
        #     url=url,
        #     params=kwargs.get("params"),
        #     request_id=request_id,
        # )

        # Make request
        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=settings.REQUEST_TIMEOUT,
                **kwargs,
            )
            response_time = time.time() - start_time

            # Log response
            # Disabling logging for MCP integration due to JSON-RPC errors
            # self.request_logger.log_response(
            #     status_code=response.status_code,
            #     response_time=response_time,
            #     request_id=request_id,
            #     size=len(response.content) if response.content else 0,
            # )

            # Handle response
            return self._handle_response(response, request_id)

        except requests.exceptions.Timeout as e:
            self.request_logger.log_error(e, request_id=request_id)
            raise NetworkError(
                f"Request timeout after {settings.REQUEST_TIMEOUT}s",
                request_id=request_id,
            )

        except requests.exceptions.ConnectionError as e:
            self.request_logger.log_error(e, request_id=request_id)
            raise NetworkError(
                f"Connection error: {str(e)}", request_id=request_id
            )

        except requests.exceptions.RequestException as e:
            self.request_logger.log_error(e, request_id=request_id)
            raise NetworkError(
                f"Network error: {str(e)}", request_id=request_id
            )

    def _handle_response(
        self, response: requests.Response, request_id: str
    ) -> Dict[str, Any]:
        """
        Handle API response and errors.

        Args:
            response: Response object
            request_id: Request correlation ID

        Returns:
            Response data as dictionary

        Raises:
            Appropriate API exception based on status code
        """
        # Success (2xx)
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except ValueError:
                # Response has no JSON body (e.g., 204 No Content)
                return {}

        # Error handling
        try:
            error_data = response.json()
            message = error_data.get("message", response.text or "Unknown error")
        except ValueError:
            message = response.text or f"HTTP {response.status_code} error"

        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(
                message, status_code=response.status_code, request_id=request_id
            )

        elif response.status_code == 404:
            raise ResourceNotFoundError(
                message, status_code=response.status_code, request_id=request_id
            )

        elif response.status_code == 429:
            # Parse retry-after header
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                message,
                retry_after=retry_after,
                status_code=response.status_code,
                request_id=request_id,
            )

        elif 400 <= response.status_code < 500:
            raise BadRequestError(
                message, status_code=response.status_code, request_id=request_id
            )

        else:  # 5xx errors
            raise ServerError(
                message, status_code=response.status_code, request_id=request_id
            )

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        return self.rate_limiter.get_status()

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "DiscogsHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
