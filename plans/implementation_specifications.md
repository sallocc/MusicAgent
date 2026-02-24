# Implementation Specifications

## Detailed Component Specifications

This document provides detailed implementation specifications for each component in the Discogs API architecture.

---

## 1. Exception Classes (`src/musicagent/exceptions/api_exceptions.py`)

### Base Exception
```python
class DiscogsAPIException(Exception):
    """Base exception for all Discogs API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.request_id = request_id
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "request_id": self.request_id
        }
```

### Specific Exception Classes
```python
class AuthenticationError(DiscogsAPIException):
    """Raised when authentication fails (401)."""
    pass

class RateLimitError(DiscogsAPIException):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

class ResourceNotFoundError(DiscogsAPIException):
    """Raised when resource is not found (404)."""
    pass

class BadRequestError(DiscogsAPIException):
    """Raised when request is invalid (400)."""
    pass

class ServerError(DiscogsAPIException):
    """Raised when server error occurs (5xx)."""
    pass

class NetworkError(DiscogsAPIException):
    """Raised when network communication fails."""
    pass

class ValidationError(DiscogsAPIException):
    """Raised when data validation fails."""
    pass
```

---

## 2. Configuration (`src/musicagent/config/settings.py`)

```python
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    # API Configuration
    DISCOGS_BASE_URL: str = Field(
        default="https://api.discogs.com",
        description="Base URL for Discogs API"
    )
    DISCOGS_API_TOKEN: Optional[str] = Field(
        default=None,
        description="Personal access token for Discogs API"
    )
    DISCOGS_USER_AGENT: str = Field(
        default="MusicAgent/1.0",
        description="User agent string for API requests"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=60,
        description="Maximum requests per time window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Time window in seconds"
    )
    
    # Retry Configuration
    MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts")
    RETRY_BACKOFF_FACTOR: float = Field(
        default=2.0,
        description="Exponential backoff multiplier"
    )
    RETRY_STATUS_CODES: list = Field(
        default=[429, 500, 502, 503, 504],
        description="HTTP status codes to retry"
    )
    
    # Timeouts
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_DIR: Path = Field(default=Path("logs"), description="Log directory path")
    LOG_FILE_NAME: str = Field(default="musicagent.log", description="Main log file")
    LOG_ERROR_FILE: str = Field(default="errors.log", description="Error log file")
    LOG_ROTATION_SIZE: int = Field(
        default=10485760,
        description="Log rotation size in bytes (10MB)"
    )
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup logs")
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json or text"
    )
    
    # Export
    EXPORT_DIR: Path = Field(default=Path("exports"), description="Export directory")
    DEFAULT_EXPORT_FORMAT: str = Field(default="json", description="Default format")
    
    @validator("LOG_DIR", "EXPORT_DIR")
    def create_directory(cls, v):
        """Ensure directory exists."""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
settings = Settings()
```

---

## 3. Rate Limiter (`src/musicagent/utils/rate_limiter.py`)

```python
import time
import threading
from typing import Optional
from collections import deque

class RateLimiter:
    """Token bucket rate limiter for API requests."""
    
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
        Blocks if rate limit would be exceeded.
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
                    time.sleep(sleep_time)
                    # Recursively try again
                    return self.acquire()
            
            # Record this request
            self.requests.append(now)
    
    def get_status(self) -> dict:
        """Get current rate limiter status."""
        with self._lock:
            now = time.time()
            # Clean old requests
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()
            
            return {
                "requests_made": len(self.requests),
                "requests_remaining": self.max_requests - len(self.requests),
                "time_window": self.time_window,
                "reset_time": self.requests[0] + self.time_window if self.requests else now
            }
    
    def wait_if_needed(self) -> Optional[float]:
        """
        Check if waiting is needed without blocking.
        
        Returns:
            Seconds to wait, or None if no waiting needed
        """
        with self._lock:
            now = time.time()
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()
            
            if len(self.requests) >= self.max_requests:
                return self.time_window - (now - self.requests[0])
            return None
```

---

## 4. Retry Handler (`src/musicagent/utils/retry_handler.py`)

```python
import time
import random
from functools import wraps
from typing import Callable, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def calculate_backoff(
    attempt: int,
    backoff_factor: float = 2.0,
    max_delay: int = 60
) -> float:
    """
    Calculate exponential backoff with jitter.
    
    Args:
        attempt: Current attempt number (1-indexed)
        backoff_factor: Exponential backoff multiplier
        max_delay: Maximum delay in seconds
    
    Returns:
        Delay in seconds
    """
    # Exponential backoff: backoff_factor ^ (attempt - 1)
    delay = min(backoff_factor ** (attempt - 1), max_delay)
    
    # Add jitter (0-25% of delay)
    jitter = random.uniform(0, delay * 0.25)
    
    return delay + jitter

def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on_exceptions: Tuple = (Exception,),
    retry_on_status_codes: Optional[list] = None
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        retry_on_exceptions: Tuple of exceptions to retry on
        retry_on_status_codes: List of HTTP status codes to retry
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_retries + 2):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                    
                except retry_on_exceptions as e:
                    last_exception = e
                    
                    # Check if we should retry based on status code
                    if retry_on_status_codes and hasattr(e, 'status_code'):
                        if e.status_code not in retry_on_status_codes:
                            raise
                    
                    # Don't retry after last attempt
                    if attempt > max_retries:
                        raise
                    
                    # Calculate backoff
                    delay = calculate_backoff(attempt, backoff_factor)
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Should not reach here, but raise last exception if we do
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator
```

---

## 5. Logger Configuration (`src/musicagent/utils/logger.py`)

```python
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from pythonjsonlogger import jsonlogger

def setup_logger(
    name: str = "musicagent",
    log_level: str = "INFO",
    log_dir: Path = Path("logs"),
    log_file: str = "musicagent.log",
    error_log_file: str = "errors.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_format: str = "json"
) -> logging.Logger:
    """
    Set up comprehensive logging with file rotation.
    
    Args:
        name: Logger name
        log_level: Logging level
        log_dir: Directory for log files
        log_file: Main log file name
        error_log_file: Error log file name
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        log_format: Format type (json or text)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Define formatters
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (all logs)
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (errors only)
    error_handler = RotatingFileHandler(
        log_dir / error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

class RequestLogger:
    """Helper class for logging API requests and responses."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log API request details."""
        self.logger.info(
            "API Request",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "params": params
            }
        )
    
    def log_response(
        self,
        status_code: int,
        response_time: float,
        request_id: Optional[str] = None,
        size: Optional[int] = None
    ) -> None:
        """Log API response details."""
        self.logger.info(
            "API Response",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "response_time_ms": response_time * 1000,
                "response_size_bytes": size
            }
        )
    
    def log_error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        context: Optional[dict] = None
    ) -> None:
        """Log API error."""
        self.logger.error(
            f"API Error: {str(error)}",
            extra={
                "request_id": request_id,
                "error_type": type(error).__name__,
                "context": context
            },
            exc_info=True
        )
```

---

## 6. Base Model (`src/musicagent/models/base.py`)

```python
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ConfigDict
import json

T = TypeVar('T', bound='BaseDiscogsModel')

class BaseDiscogsModel(BaseModel):
    """Base model for all Discogs API responses."""
    
    model_config = ConfigDict(
        # Allow arbitrary types
        arbitrary_types_allowed=True,
        # Validate on assignment
        validate_assignment=True,
        # Use enum values
        use_enum_values=True,
        # Populate by name (allow field aliases)
        populate_by_name=True,
        # Extra fields forbidden by default
        extra='forbid'
    )
    
    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            exclude_none: Exclude None values from output
        
        Returns:
            Dictionary representation
        """
        return self.model_dump(
            exclude_none=exclude_none,
            by_alias=True
        )
    
    def to_json(
        self,
        indent: Optional[int] = 2,
        exclude_none: bool = False
    ) -> str:
        """
        Convert model to JSON string.
        
        Args:
            indent: JSON indentation (None for compact)
            exclude_none: Exclude None values
        
        Returns:
            JSON string
        """
        return self.model_dump_json(
            indent=indent,
            exclude_none=exclude_none,
            by_alias=True
        )
    
    @classmethod
    def from_api_response(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from API response data.
        
        Args:
            data: Raw API response dictionary
        
        Returns:
            Model instance
        
        Raises:
            ValidationError: If data doesn't match schema
        """
        return cls.model_validate(data)
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        Create model instance from JSON string.
        
        Args:
            json_str: JSON string
        
        Returns:
            Model instance
        """
        return cls.model_validate_json(json_str)
```

---

## 7. Request Builder (`src/musicagent/client/request_builder.py`)

```python
from typing import Dict, Optional, Any
from urllib.parse import urljoin, urlencode

class RequestBuilder:
    """Builder for constructing Discogs API requests."""
    
    def __init__(self, base_url: str = "https://api.discogs.com"):
        """
        Initialize request builder.
        
        Args:
            base_url: Base URL for API
        """
        self.base_url = base_url.rstrip('/')
        self._endpoint = ""
        self._params: Dict[str, Any] = {}
    
    def search(
        self,
        query: Optional[str] = None,
        search_type: Optional[str] = None,
        **kwargs
    ) -> 'RequestBuilder':
        """
        Build database search request.
        
        Args:
            query: Search query string
            search_type: Type of search (release, artist, label)
            **kwargs: Additional search parameters
        
        Returns:
            Self for chaining
        """
        self._endpoint = "/database/search"
        if query:
            self._params['q'] = query
        if search_type:
            self._params['type'] = search_type
        self._params.update(kwargs)
        return self
    
    def artist(self, artist_id: int) -> 'RequestBuilder':
        """Build artist request."""
        self._endpoint = f"/artists/{artist_id}"
        return self
    
    def artist_releases(self, artist_id: int) -> 'RequestBuilder':
        """Build artist releases request."""
        self._endpoint = f"/artists/{artist_id}/releases"
        return self
    
    def release(self, release_id: int) -> 'RequestBuilder':
        """Build release request."""
        self._endpoint = f"/releases/{release_id}"
        return self
    
    def master(self, master_id: int) -> 'RequestBuilder':
        """Build master release request."""
        self._endpoint = f"/masters/{master_id}"
        return self
    
    def label(self, label_id: int) -> 'RequestBuilder':
        """Build label request."""
        self._endpoint = f"/labels/{label_id}"
        return self
    
    def user(self, username: str) -> 'RequestBuilder':
        """Build user profile request."""
        self._endpoint = f"/users/{username}"
        return self
    
    def paginate(self, page: int = 1, per_page: int = 50) -> 'RequestBuilder':
        """
        Add pagination parameters.
        
        Args:
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
        
        Returns:
            Self for chaining
        """
        self._params['page'] = page
        self._params['per_page'] = min(per_page, 100)
        return self
    
    def sort(self, sort: str, order: str = 'asc') -> 'RequestBuilder':
        """
        Add sorting parameters.
        
        Args:
            sort: Field to sort by
            order: Sort order (asc/desc)
        
        Returns:
            Self for chaining
        """
        self._params['sort'] = sort
        self._params['sort_order'] = order
        return self
    
    def build(self) -> str:
        """
        Build final URL.
        
        Returns:
            Complete URL with parameters
        """
        url = urljoin(self.base_url, self._endpoint)
        if self._params:
            url = f"{url}?{urlencode(self._params)}"
        return url
    
    def reset(self) -> 'RequestBuilder':
        """Reset builder to initial state."""
        self._endpoint = ""
        self._params = {}
        return self
```

---

## 8. HTTP Client (Partial - Core Methods)

```python
# src/musicagent/client/http_client.py

import uuid
import time
from typing import Dict, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.settings import settings
from ..utils.rate_limiter import RateLimiter
from ..utils.logger import setup_logger, RequestLogger
from ..exceptions.api_exceptions import *

class DiscogsHTTPClient:
    """Main HTTP client for Discogs API."""
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        user_agent: Optional[str] = None,
        rate_limit: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        """
        Initialize HTTP client.
        
        Args:
            api_token: Discogs API token
            user_agent: User agent string
            rate_limit: Requests per minute
            max_retries: Maximum retry attempts
        """
        self.api_token = api_token or settings.DISCOGS_API_TOKEN
        self.user_agent = user_agent or settings.DISCOGS_USER_AGENT
        self.base_url = settings.DISCOGS_BASE_URL
        
        # Set up rate limiter
        rate_limit = rate_limit or settings.RATE_LIMIT_REQUESTS
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit,
            time_window=settings.RATE_LIMIT_WINDOW
        )
        
        # Set up logging
        self.logger = setup_logger()
        self.request_logger = RequestLogger(self.logger)
        
        # Create session
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create configured requests session."""
        session = requests.Session()
        
        # Set default headers
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
        })
        
        # Add authentication
        if self.api_token:
            session.headers['Authorization'] = f'Discogs token={self.api_token}'
        
        return session
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            Response data
        """
        return self._make_request('GET', endpoint, params=params)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
        
        Returns:
            Response data
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Construct URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Apply rate limiting
        self.rate_limiter.acquire()
        
        # Log request
        self.request_logger.log_request(
            method=method,
            url=url,
            params=kwargs.get('params'),
            request_id=request_id
        )
        
        # Make request
        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=settings.REQUEST_TIMEOUT,
                **kwargs
            )
            response_time = time.time() - start_time
            
            # Log response
            self.request_logger.log_response(
                status_code=response.status_code,
                response_time=response_time,
                request_id=request_id,
                size=len(response.content)
            )
            
            # Handle response
            return self._handle_response(response, request_id)
            
        except requests.exceptions.RequestException as e:
            self.request_logger.log_error(e, request_id=request_id)
            raise NetworkError(
                f"Network error: {str(e)}",
                request_id=request_id
            )
    
    def _handle_response(
        self,
        response: requests.Response,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Handle API response and errors.
        
        Args:
            response: Response object
            request_id: Request correlation ID
        
        Returns:
            Response data
        
        Raises:
            Appropriate API exception
        """
        # Success
        if 200 <= response.status_code < 300:
            return response.json()
        
        # Error handling
        try:
            error_data = response.json()
            message = error_data.get('message', response.text)
        except:
            message = response.text
        
        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(
                message,
                status_code=response.status_code,
                request_id=request_id
            )
        elif response.status_code == 404:
            raise ResourceNotFoundError(
                message,
                status_code=response.status_code,
                request_id=request_id
            )
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(
                message,
                retry_after=retry_after,
                status_code=response.status_code,
                request_id=request_id
            )
        elif 400 <= response.status_code < 500:
            raise BadRequestError(
                message,
                status_code=response.status_code,
                request_id=request_id
            )
        else:
            raise ServerError(
                message,
                status_code=response.status_code,
                request_id=request_id
            )
```

This implementation specification provides detailed code-level guidance for each component. The actual implementation would involve creating these files with complete implementations including docstrings, type hints, and comprehensive error handling.
