"""
Configuration management using Pydantic settings.

This module provides environment-based configuration with validation
and default values for the MusicAgent application.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    # API Configuration
    DISCOGS_BASE_URL: str = Field(
        default="https://api.discogs.com",
        description="Base URL for Discogs API",
    )
    DISCOGS_API_TOKEN: Optional[str] = Field(
        default=None, description="Personal access token for Discogs API"
    )
    DISCOGS_USER_AGENT: str = Field(
        default="MusicAgent/1.0", description="User agent string for API requests"
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=60, description="Maximum requests per time window"
    )
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Time window in seconds")

    # Retry Configuration
    MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts")
    RETRY_BACKOFF_FACTOR: float = Field(
        default=2.0, description="Exponential backoff multiplier"
    )
    RETRY_STATUS_CODES: List[int] = Field(
        default=[429, 500, 502, 503, 504],
        description="HTTP status codes to retry",
    )

    # Timeouts
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_DIR: Path = Field(default=Path("logs"), description="Log directory path")
    LOG_FILE_NAME: str = Field(
        default="musicagent.log", description="Main log file"
    )
    LOG_ERROR_FILE: str = Field(default="errors.log", description="Error log file")
    LOG_ROTATION_SIZE: int = Field(
        default=10485760, description="Log rotation size in bytes (10MB)"
    )
    LOG_BACKUP_COUNT: int = Field(
        default=5, description="Number of backup logs"
    )
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")

    # Export
    EXPORT_DIR: Path = Field(
        default=Path("exports"), description="Export directory"
    )
    DEFAULT_EXPORT_FORMAT: str = Field(
        default="json", description="Default export format"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("LOG_DIR", "EXPORT_DIR")
    @classmethod
    def create_directory(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v_upper

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "text"]
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"Invalid log format. Must be one of {valid_formats}")
        return v_lower

    @field_validator("DEFAULT_EXPORT_FORMAT")
    @classmethod
    def validate_export_format(cls, v: str) -> str:
        """Validate export format."""
        valid_formats = ["json", "csv"]
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"Invalid export format. Must be one of {valid_formats}")
        return v_lower


# Global settings instance
settings = Settings()
