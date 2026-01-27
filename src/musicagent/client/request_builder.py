"""
Request builder for constructing Discogs API URLs and parameters.

This module provides a fluent interface for building valid Discogs API
endpoints with proper URL encoding and parameter validation.
"""

from typing import Dict, Optional, Any
from urllib.parse import urljoin, urlencode


class RequestBuilder:
    """
    Builder for constructing Discogs API requests.

    This class provides a fluent interface for building API URLs with
    proper parameter encoding and validation.
    """

    def __init__(self, base_url: str = "https://api.discogs.com"):
        """
        Initialize request builder.

        Args:
            base_url: Base URL for Discogs API
        """
        self.base_url = base_url.rstrip("/")
        self._endpoint = ""
        self._params: Dict[str, Any] = {}

    def search(
        self,
        query: Optional[str] = None,
        search_type: Optional[str] = None,
        **kwargs: Any,
    ) -> "RequestBuilder":
        """
        Build database search request.

        Args:
            query: Search query string
            search_type: Type of search (release, artist, label, master)
            **kwargs: Additional search parameters (year, country, genre, etc.)

        Returns:
            Self for method chaining
        """
        self._endpoint = "/database/search"
        if query:
            self._params["q"] = query
        if search_type:
            self._params["type"] = search_type
        self._params.update(kwargs)
        return self

    def artist(self, artist_id: int) -> "RequestBuilder":
        """
        Build artist request.

        Args:
            artist_id: Discogs artist ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/artists/{artist_id}"
        return self

    def artist_releases(self, artist_id: int) -> "RequestBuilder":
        """
        Build artist releases request.

        Args:
            artist_id: Discogs artist ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/artists/{artist_id}/releases"
        return self

    def release(self, release_id: int) -> "RequestBuilder":
        """
        Build release request.

        Args:
            release_id: Discogs release ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/releases/{release_id}"
        return self

    def master(self, master_id: int) -> "RequestBuilder":
        """
        Build master release request.

        Args:
            master_id: Discogs master release ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/masters/{master_id}"
        return self

    def master_versions(self, master_id: int) -> "RequestBuilder":
        """
        Build master release versions request.

        Args:
            master_id: Discogs master release ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/masters/{master_id}/versions"
        return self

    def label(self, label_id: int) -> "RequestBuilder":
        """
        Build label request.

        Args:
            label_id: Discogs label ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/labels/{label_id}"
        return self

    def label_releases(self, label_id: int) -> "RequestBuilder":
        """
        Build label releases request.

        Args:
            label_id: Discogs label ID

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/labels/{label_id}/releases"
        return self

    def user(self, username: str) -> "RequestBuilder":
        """
        Build user profile request.

        Args:
            username: Discogs username

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/users/{username}"
        return self

    def user_collection(self, username: str, folder_id: int = 0) -> "RequestBuilder":
        """
        Build user collection request.

        Args:
            username: Discogs username
            folder_id: Collection folder ID (0 for all)

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/users/{username}/collection/folders/{folder_id}/releases"
        return self

    def user_wantlist(self, username: str) -> "RequestBuilder":
        """
        Build user wantlist request.

        Args:
            username: Discogs username

        Returns:
            Self for method chaining
        """
        self._endpoint = f"/users/{username}/wants"
        return self

    def paginate(self, page: int = 1, per_page: int = 50) -> "RequestBuilder":
        """
        Add pagination parameters.

        Args:
            page: Page number (1-indexed)
            per_page: Results per page (max 100)

        Returns:
            Self for method chaining
        """
        self._params["page"] = max(1, page)
        self._params["per_page"] = min(per_page, 100)
        return self

    def sort(self, sort: str, order: str = "asc") -> "RequestBuilder":
        """
        Add sorting parameters.

        Args:
            sort: Field to sort by
            order: Sort order (asc/desc)

        Returns:
            Self for method chaining
        """
        self._params["sort"] = sort
        self._params["sort_order"] = order.lower()
        return self

    def filter(self, **filters: Any) -> "RequestBuilder":
        """
        Add filter parameters.

        Args:
            **filters: Filter key-value pairs

        Returns:
            Self for method chaining
        """
        self._params.update(filters)
        return self

    def build(self) -> str:
        """
        Build final URL.

        Returns:
            Complete URL with parameters

        Raises:
            ValueError: If no endpoint has been set
        """
        if not self._endpoint:
            raise ValueError("No endpoint set. Call an endpoint method first.")

        url = urljoin(self.base_url, self._endpoint)

        if self._params:
            # Filter out None values
            clean_params = {k: v for k, v in self._params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urlencode(clean_params)}"

        return url

    def reset(self) -> "RequestBuilder":
        """
        Reset builder to initial state.

        Returns:
            Self for method chaining
        """
        self._endpoint = ""
        self._params = {}
        return self

    def get_endpoint(self) -> str:
        """
        Get the current endpoint without base URL.

        Returns:
            Current endpoint path
        """
        return self._endpoint

    def get_params(self) -> Dict[str, Any]:
        """
        Get current parameters.

        Returns:
            Copy of current parameters
        """
        return self._params.copy()
