# Example Usage Patterns

## Complete Example Scripts

### 1. Basic Usage (`examples/basic_usage.py`)

```python
"""
Basic usage examples for the MusicAgent Discogs API client.
"""

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.client.request_builder import RequestBuilder
from musicagent.config.settings import settings

def main():
    """Demonstrate basic API usage."""
    
    # Initialize client
    client = DiscogsHTTPClient()
    
    print("=== Basic Artist Search ===")
    
    # Search for an artist
    builder = RequestBuilder()
    search_url = builder.search(
        query="Miles Davis",
        search_type="artist"
    ).build()
    
    # Extract endpoint from full URL
    endpoint = search_url.replace(settings.DISCOGS_BASE_URL, "")
    response = client.get(endpoint)
    
    # Display results
    for result in response['results'][:5]:  # First 5 results
        print(f"- {result['title']} (ID: {result['id']})")
    
    print("\n=== Get Artist Details ===")
    
    # Get specific artist
    artist_id = 97784  # Miles Davis ID
    artist_response = client.get(f"artists/{artist_id}")
    
    print(f"Name: {artist_response['name']}")
    print(f"Profile: {artist_response['profile'][:100]}...")
    print(f"URLs: {artist_response.get('urls', [])}")
    
    print("\n=== Search for Releases ===")
    
    # Search for releases
    release_url = builder.reset().search(
        query="Kind of Blue",
        search_type="release"
    ).paginate(page=1, per_page=10).build()
    
    endpoint = release_url.replace(settings.DISCOGS_BASE_URL, "")
    releases = client.get(endpoint)
    
    print(f"Found {releases['pagination']['items']} releases")
    for release in releases['results'][:3]:
        print(f"- {release['title']} ({release.get('year', 'N/A')})")

if __name__ == "__main__":
    main()
```

---

### 2. Advanced Usage with Data Models (`examples/advanced_usage.py`)

```python
"""
Advanced usage with Pydantic models and data export.
"""

from typing import List, Optional
from pydantic import Field
from pathlib import Path

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.models.base import BaseDiscogsModel
from musicagent.output.json_exporter import JSONExporter
from musicagent.output.csv_exporter import CSVExporter
from musicagent.config.settings import settings

# Define custom models for responses

class ArtistSearchResult(BaseDiscogsModel):
    """Model for artist search result."""
    id: int
    title: str
    type: str
    thumb: Optional[str] = None
    cover_image: Optional[str] = None
    resource_url: str

class SearchResponse(BaseDiscogsModel):
    """Model for search response with pagination."""
    results: List[ArtistSearchResult]
    pagination: dict

class Release(BaseDiscogsModel):
    """Model for release details."""
    id: int
    title: str
    year: Optional[int] = None
    artists: List[dict]
    labels: List[dict]
    genres: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    tracklist: List[dict] = Field(default_factory=list)

def search_and_export(query: str, export_format: str = "json"):
    """
    Search for artists and export results.
    
    Args:
        query: Search query
        export_format: Export format (json or csv)
    """
    print(f"Searching for: {query}")
    
    # Initialize client
    client = DiscogsHTTPClient()
    
    # Search
    from musicagent.client.request_builder import RequestBuilder
    builder = RequestBuilder()
    
    search_url = builder.search(
        query=query,
        search_type="artist"
    ).paginate(page=1, per_page=50).build()
    
    endpoint = search_url.replace(settings.DISCOGS_BASE_URL, "")
    response = client.get(endpoint)
    
    # Parse with Pydantic
    search_response = SearchResponse.from_api_response(response)
    
    print(f"Found {len(search_response.results)} results")
    
    # Export results
    if export_format == "json":
        exporter = JSONExporter()
        output_path = exporter.export(
            search_response.results,
            f"search_{query.replace(' ', '_')}.json"
        )
    else:
        exporter = CSVExporter()
        output_path = exporter.export(
            search_response.results,
            f"search_{query.replace(' ', '_')}.csv"
        )
    
    print(f"Exported to: {output_path}")
    
    return search_response

def get_artist_releases(artist_id: int, export: bool = True):
    """
    Get all releases for an artist.
    
    Args:
        artist_id: Discogs artist ID
        export: Whether to export results
    """
    client = DiscogsHTTPClient()
    
    print(f"Fetching releases for artist {artist_id}...")
    
    # Get artist info
    artist = client.get(f"artists/{artist_id}")
    print(f"Artist: {artist['name']}")
    
    # Get releases with pagination
    all_releases = []
    page = 1
    per_page = 100
    
    while True:
        from musicagent.client.request_builder import RequestBuilder
        builder = RequestBuilder()
        
        url = builder.artist_releases(artist_id).paginate(
            page=page,
            per_page=per_page
        ).build()
        
        endpoint = url.replace(settings.DISCOGS_BASE_URL, "")
        response = client.get(endpoint)
        
        releases = response.get('releases', [])
        all_releases.extend(releases)
        
        # Check if there are more pages
        pagination = response.get('pagination', {})
        if page >= pagination.get('pages', 1):
            break
        
        page += 1
        print(f"Fetched page {page-1}/{pagination['pages']}")
    
    print(f"Total releases: {len(all_releases)}")
    
    if export:
        exporter = JSONExporter()
        output_path = exporter.export(
            all_releases,
            f"artist_{artist_id}_releases.json"
        )
        print(f"Exported to: {output_path}")
    
    return all_releases

def analyze_release(release_id: int):
    """
    Get detailed information about a release.
    
    Args:
        release_id: Discogs release ID
    """
    client = DiscogsHTTPClient()
    
    print(f"Analyzing release {release_id}...")
    
    # Get release details
    response = client.get(f"releases/{release_id}")
    
    # Parse with model
    release = Release.from_api_response(response)
    
    print(f"\nTitle: {release.title}")
    print(f"Year: {release.year}")
    print(f"Artists: {', '.join(a['name'] for a in release.artists)}")
    print(f"Genres: {', '.join(release.genres)}")
    print(f"Styles: {', '.join(release.styles)}")
    print(f"\nTracklist:")
    for track in release.tracklist:
        print(f"  {track.get('position', '')} - {track.get('title', '')} ({track.get('duration', 'N/A')})")
    
    # Export to JSON
    exporter = JSONExporter()
    output_path = exporter.export(
        release,
        f"release_{release_id}.json",
        indent=2
    )
    print(f"\nExported to: {output_path}")
    
    return release

def main():
    """Run advanced usage examples."""
    
    # Example 1: Search and export
    print("=" * 60)
    print("Example 1: Search and Export")
    print("=" * 60)
    search_and_export("Jazz", export_format="json")
    
    # Example 2: Get artist releases
    print("\n" + "=" * 60)
    print("Example 2: Artist Releases")
    print("=" * 60)
    get_artist_releases(97784, export=True)  # Miles Davis
    
    # Example 3: Analyze specific release
    print("\n" + "=" * 60)
    print("Example 3: Release Analysis")
    print("=" * 60)
    analyze_release(1293893)  # Kind of Blue

if __name__ == "__main__":
    main()
```

---

### 3. Error Handling Patterns (`examples/error_handling.py`)

```python
"""
Demonstrate comprehensive error handling patterns.
"""

import time
from typing import Optional

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.exceptions.api_exceptions import (
    DiscogsAPIException,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    BadRequestError,
    ServerError,
    NetworkError
)
from musicagent.utils.logger import setup_logger

logger = setup_logger()

def safe_api_call(client: DiscogsHTTPClient, endpoint: str, max_retries: int = 3):
    """
    Make API call with comprehensive error handling.
    
    Args:
        client: HTTP client instance
        endpoint: API endpoint
        max_retries: Maximum retry attempts
    
    Returns:
        API response or None on failure
    """
    retries = 0
    
    while retries < max_retries:
        try:
            # Attempt API call
            response = client.get(endpoint)
            logger.info(f"Successfully fetched {endpoint}")
            return response
            
        except AuthenticationError as e:
            # Authentication failed - no point retrying
            logger.error(f"Authentication failed: {e.message}")
            logger.error("Please check your API token in .env file")
            return None
            
        except RateLimitError as e:
            # Rate limited - wait and retry
            wait_time = e.retry_after or 60
            logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            retries += 1
            continue
            
        except ResourceNotFoundError as e:
            # Resource doesn't exist
            logger.error(f"Resource not found: {endpoint}")
            logger.error(f"Details: {e.message}")
            return None
            
        except BadRequestError as e:
            # Invalid request parameters
            logger.error(f"Bad request: {e.message}")
            logger.error(f"Status code: {e.status_code}")
            return None
            
        except ServerError as e:
            # Server error - retry
            logger.error(f"Server error: {e.message}")
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds... (attempt {retries}/{max_retries})")
                time.sleep(wait_time)
            continue
            
        except NetworkError as e:
            # Network issue - retry
            logger.error(f"Network error: {e.message}")
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            continue
            
        except DiscogsAPIException as e:
            # Generic API exception
            logger.error(f"API error: {e.message}")
            logger.error(f"Error details: {e.to_dict()}")
            return None
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return None
    
    logger.error(f"Failed after {max_retries} retries")
    return None

def batch_fetch_with_error_handling(artist_ids: list):
    """
    Fetch multiple artists with error handling.
    
    Args:
        artist_ids: List of artist IDs to fetch
    """
    client = DiscogsHTTPClient()
    
    results = []
    errors = []
    
    for artist_id in artist_ids:
        print(f"\nFetching artist {artist_id}...")
        
        try:
            response = safe_api_call(client, f"artists/{artist_id}")
            
            if response:
                results.append({
                    'id': artist_id,
                    'name': response.get('name'),
                    'status': 'success'
                })
                print(f"✓ Success: {response.get('name')}")
            else:
                errors.append({
                    'id': artist_id,
                    'status': 'failed'
                })
                print(f"✗ Failed")
                
        except Exception as e:
            logger.error(f"Unexpected error for artist {artist_id}: {e}")
            errors.append({
                'id': artist_id,
                'status': 'error',
                'message': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(errors)}")
    
    if errors:
        print("\nFailed IDs:")
        for error in errors:
            print(f"  - {error['id']}: {error.get('message', 'Unknown error')}")
    
    return results, errors

def demonstrate_validation_error():
    """Demonstrate data validation error handling."""
    from pydantic import ValidationError
    from musicagent.models.base import BaseDiscogsModel
    
    class Artist(BaseDiscogsModel):
        id: int
        name: str
        year_formed: int  # Required field
    
    # Invalid data (missing year_formed)
    invalid_data = {
        'id': 123,
        'name': 'Test Artist'
    }
    
    try:
        artist = Artist.from_api_response(invalid_data)
    except ValidationError as e:
        print("\n" + "=" * 60)
        print("Validation Error Example")
        print("=" * 60)
        print("Pydantic validation failed:")
        print(e)
        
        # Log validation errors
        logger.error("Data validation failed", extra={
            'errors': e.errors(),
            'data': invalid_data
        })

def main():
    """Run error handling examples."""
    
    # Example 1: Single API call with error handling
    print("=" * 60)
    print("Example 1: Safe API Call")
    print("=" * 60)
    
    client = DiscogsHTTPClient()
    
    # Valid artist
    print("\nFetching valid artist...")
    result = safe_api_call(client, "artists/97784")
    if result:
        print(f"Artist: {result.get('name')}")
    
    # Invalid artist (will fail)
    print("\nFetching invalid artist...")
    result = safe_api_call(client, "artists/99999999")
    
    # Example 2: Batch fetching
    print("\n" + "=" * 60)
    print("Example 2: Batch Fetch with Error Handling")
    print("=" * 60)
    
    artist_ids = [97784, 12345, 99999999, 54321]  # Mix of valid and invalid
    results, errors = batch_fetch_with_error_handling(artist_ids)
    
    # Example 3: Validation errors
    demonstrate_validation_error()

if __name__ == "__main__":
    main()
```

---

### 4. Configuration Example (`.env.example`)

```bash
# Discogs API Configuration
DISCOGS_API_TOKEN=your_personal_access_token_here
DISCOGS_USER_AGENT=YourAppName/1.0 +https://yourwebsite.com

# Optional: Override defaults
# DISCOGS_BASE_URL=https://api.discogs.com
# RATE_LIMIT_REQUESTS=60
# RATE_LIMIT_WINDOW=60

# Logging Configuration
# LOG_LEVEL=INFO
# LOG_DIR=logs
# LOG_FILE_NAME=musicagent.log
# LOG_ERROR_FILE=errors.log
# LOG_FORMAT=json

# Export Configuration
# EXPORT_DIR=exports
# DEFAULT_EXPORT_FORMAT=json

# Retry Configuration
# MAX_RETRIES=3
# RETRY_BACKOFF_FACTOR=2.0
# REQUEST_TIMEOUT=30
```

---

### 5. Quick Start Script (`examples/quickstart.py`)

```python
"""
Quick start guide - Get up and running in 5 minutes.
"""

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.client.request_builder import RequestBuilder
from musicagent.config.settings import settings

def quickstart():
    """
    Quick start guide for the MusicAgent.
    
    This example shows the minimal code needed to start making API calls.
    """
    
    print("🎵 MusicAgent Quick Start")
    print("=" * 60)
    
    # Step 1: Initialize the client
    print("\n1. Initializing client...")
    client = DiscogsHTTPClient()
    print("✓ Client initialized")
    
    # Step 2: Search for an artist
    print("\n2. Searching for 'Beatles'...")
    
    builder = RequestBuilder()
    search_url = builder.search(
        query="Beatles",
        search_type="artist"
    ).build()
    
    endpoint = search_url.replace(settings.DISCOGS_BASE_URL, "")
    results = client.get(endpoint)
    
    print(f"✓ Found {len(results['results'])} results")
    
    # Step 3: Display first result
    print("\n3. First result:")
    first_result = results['results'][0]
    print(f"   Name: {first_result['title']}")
    print(f"   ID: {first_result['id']}")
    print(f"   Type: {first_result['type']}")
    
    # Step 4: Get detailed info
    print("\n4. Getting detailed information...")
    artist_id = first_result['id']
    artist = client.get(f"artists/{artist_id}")
    
    print(f"   Profile: {artist.get('profile', 'N/A')[:150]}...")
    print(f"   URLs: {artist.get('urls', [])}")
    
    print("\n✨ Quick start complete!")
    print("\nNext steps:")
    print("  - Check out examples/advanced_usage.py for more features")
    print("  - Read the documentation in docs/")
    print("  - Export data using JSONExporter or CSVExporter")

if __name__ == "__main__":
    try:
        quickstart()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you've set DISCOGS_API_TOKEN in .env file")
        print("  2. Check your internet connection")
        print("  3. Review the logs in the logs/ directory")
```

---

### 6. Performance Testing (`examples/performance_test.py`)

```python
"""
Test API performance and rate limiting.
"""

import time
from statistics import mean, median

from musicagent.client.http_client import DiscogsHTTPClient

def benchmark_api_calls(num_requests: int = 10):
    """
    Benchmark API call performance.
    
    Args:
        num_requests: Number of requests to make
    """
    client = DiscogsHTTPClient()
    
    print(f"🔥 Performance Benchmark")
    print(f"Making {num_requests} API calls...")
    print("=" * 60)
    
    response_times = []
    
    # Make requests to different artists
    artist_ids = [97784, 12345, 67890, 111, 222, 333, 444, 555, 666, 777]
    
    for i in range(num_requests):
        artist_id = artist_ids[i % len(artist_ids)]
        
        start = time.time()
        try:
            response = client.get(f"artists/{artist_id}")
            elapsed = time.time() - start
            response_times.append(elapsed)
            
            print(f"Request {i+1:2d}: {elapsed:.3f}s - {response.get('name', 'N/A')}")
            
        except Exception as e:
            print(f"Request {i+1:2d}: Failed - {e}")
    
    # Statistics
    if response_times:
        print("\n" + "=" * 60)
        print("Statistics")
        print("=" * 60)
        print(f"Total requests: {len(response_times)}")
        print(f"Average time:   {mean(response_times):.3f}s")
        print(f"Median time:    {median(response_times):.3f}s")
        print(f"Min time:       {min(response_times):.3f}s")
        print(f"Max time:       {max(response_times):.3f}s")
        print(f"Total time:     {sum(response_times):.3f}s")
    
    # Rate limiter status
    print("\n" + "=" * 60)
    print("Rate Limiter Status")
    print("=" * 60)
    status = client.rate_limiter.get_status()
    print(f"Requests made:      {status['requests_made']}")
    print(f"Requests remaining: {status['requests_remaining']}")
    print(f"Time window:        {status['time_window']}s")

if __name__ == "__main__":
    benchmark_api_calls(10)
```

---

## Usage Patterns Summary

### Basic Pattern
```python
# 1. Import
from musicagent.client.http_client import DiscogsHTTPClient

# 2. Initialize
client = DiscogsHTTPClient()

# 3. Make request
response = client.get("artists/12345")

# 4. Use data
print(response['name'])
```

### Advanced Pattern with Models
```python
# 1. Define model
from musicagent.models.base import BaseDiscogsModel

class Artist(BaseDiscogsModel):
    id: int
    name: str
    profile: str

# 2. Parse response
artist = Artist.from_api_response(response)

# 3. Export
from musicagent.output.json_exporter import JSONExporter
exporter = JSONExporter()
exporter.export(artist, "artist.json")
```

### Error Handling Pattern
```python
from musicagent.exceptions.api_exceptions import (
    RateLimitError,
    ResourceNotFoundError
)

try:
    response = client.get(endpoint)
except RateLimitError as e:
    time.sleep(e.retry_after)
    response = client.get(endpoint)
except ResourceNotFoundError:
    print("Not found")
```

These examples provide comprehensive usage patterns that users can reference when implementing their own applications with the architecture.
