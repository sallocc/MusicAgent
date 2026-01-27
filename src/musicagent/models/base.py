"""
Base model class for all Discogs API responses using Pydantic v2.

This module provides an abstract base class with common functionality
for serialization, deserialization, and validation of API responses.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="BaseDiscogsModel")


class BaseDiscogsModel(BaseModel):
    """
    Base model for all Discogs API responses.

    This class provides common functionality for handling API response data,
    including JSON serialization/deserialization and data validation using
    Pydantic v2.
    """

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
        extra="forbid",
        # Validate default values
        validate_default=True,
    )

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Args:
            exclude_none: Exclude None values from output

        Returns:
            Dictionary representation of the model
        """
        return self.model_dump(exclude_none=exclude_none, by_alias=True)

    def to_json(
        self, indent: Optional[int] = 2, exclude_none: bool = False
    ) -> str:
        """
        Convert model to JSON string.

        Args:
            indent: JSON indentation (None for compact)
            exclude_none: Exclude None values

        Returns:
            JSON string representation of the model
        """
        return self.model_dump_json(
            indent=indent, exclude_none=exclude_none, by_alias=True
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

        Raises:
            ValidationError: If JSON doesn't match schema
        """
        return cls.model_validate_json(json_str)

    def __repr__(self) -> str:
        """Return string representation of the model."""
        class_name = self.__class__.__name__
        fields = ", ".join(
            f"{k}={v!r}"
            for k, v in self.model_dump().items()
            if v is not None
        )
        return f"{class_name}({fields})"
