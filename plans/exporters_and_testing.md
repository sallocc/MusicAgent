# Data Exporters and Testing Specifications

## Data Export Components

### 1. Base Exporter (`src/musicagent/output/exporter.py`)

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Union
import logging

logger = logging.getLogger(__name__)

class BaseExporter(ABC):
    """Abstract base class for data exporters."""
    
    def __init__(self, output_dir: Path = Path("exports")):
        """
        Initialize exporter.
        
        Args:
            output_dir: Directory for exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def export(
        self,
        data: Union[List[Any], Any],
        filepath: Union[str, Path],
        **kwargs
    ) -> Path:
        """
        Export data to file.
        
        Args:
            data: Data to export (models or dicts)
            filepath: Output file path
            **kwargs: Format-specific options
        
        Returns:
            Path to created file
        """
        pass
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate data before export.
        
        Args:
            data: Data to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If data is invalid
        """
        if data is None:
            raise ValueError("Data cannot be None")
        return True
    
    def _get_full_path(self, filepath: Union[str, Path]) -> Path:
        """Get full path for output file."""
        filepath = Path(filepath)
        if not filepath.is_absolute():
            filepath = self.output_dir / filepath
        filepath.parent.mkdir(parents=True, exist_ok=True)
        return filepath
```

---

### 2. JSON Exporter (`src/musicagent/output/json_exporter.py`)

```python
import json
from pathlib import Path
from typing import Any, List, Union, Optional
from pydantic import BaseModel

from .exporter import BaseExporter

class JSONExporter(BaseExporter):
    """Export data to JSON format."""
    
    def export(
        self,
        data: Union[List[Any], Any],
        filepath: Union[str, Path],
        indent: Optional[int] = 2,
        ensure_ascii: bool = False,
        **kwargs
    ) -> Path:
        """
        Export data to JSON file.
        
        Args:
            data: Data to export (models or dicts)
            filepath: Output file path
            indent: JSON indentation (None for compact)
            ensure_ascii: Escape non-ASCII characters
            **kwargs: Additional json.dump options
        
        Returns:
            Path to created file
        """
        self.validate_data(data)
        
        # Get full path
        full_path = self._get_full_path(filepath)
        
        # Ensure .json extension
        if not full_path.suffix:
            full_path = full_path.with_suffix('.json')
        
        # Convert Pydantic models to dicts
        export_data = self._prepare_data(data)
        
        # Write to file
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(
                export_data,
                f,
                indent=indent,
                ensure_ascii=ensure_ascii,
                default=str,  # Handle datetime, etc.
                **kwargs
            )
        
        logger.info(f"Exported data to {full_path}")
        return full_path
    
    def _prepare_data(self, data: Any) -> Any:
        """Convert data to JSON-serializable format."""
        if isinstance(data, BaseModel):
            return data.model_dump(mode='json')
        elif isinstance(data, list):
            return [self._prepare_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._prepare_data(v) for k, v in data.items()}
        else:
            return data
    
    def export_streaming(
        self,
        data: List[Any],
        filepath: Union[str, Path],
        **kwargs
    ) -> Path:
        """
        Export large datasets using streaming (line-delimited JSON).
        
        Args:
            data: List of data items
            filepath: Output file path
            **kwargs: Additional options
        
        Returns:
            Path to created file
        """
        full_path = self._get_full_path(filepath)
        
        if not full_path.suffix:
            full_path = full_path.with_suffix('.jsonl')
        
        with open(full_path, 'w', encoding='utf-8') as f:
            for item in data:
                export_item = self._prepare_data(item)
                f.write(json.dumps(export_item, default=str) + '\n')
        
        logger.info(f"Exported {len(data)} items to {full_path}")
        return full_path
```

---

### 3. CSV Exporter (`src/musicagent/output/csv_exporter.py`)

```python
import csv
from pathlib import Path
from typing import Any, List, Union, Optional, Dict
from pydantic import BaseModel

from .exporter import BaseExporter

class CSVExporter(BaseExporter):
    """Export data to CSV format."""
    
    def export(
        self,
        data: Union[List[Any], Any],
        filepath: Union[str, Path],
        delimiter: str = ',',
        include_headers: bool = True,
        flatten_nested: bool = True,
        **kwargs
    ) -> Path:
        """
        Export data to CSV file.
        
        Args:
            data: Data to export (models or dicts)
            filepath: Output file path
            delimiter: CSV delimiter
            include_headers: Include header row
            flatten_nested: Flatten nested structures
            **kwargs: Additional csv.writer options
        
        Returns:
            Path to created file
        """
        self.validate_data(data)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        if not data:
            raise ValueError("Cannot export empty data to CSV")
        
        # Get full path
        full_path = self._get_full_path(filepath)
        
        # Ensure .csv extension
        if not full_path.suffix:
            full_path = full_path.with_suffix('.csv')
        
        # Convert to flat dictionaries
        rows = [self._flatten_data(item) for item in data]
        
        # Get all unique keys for headers
        headers = self._get_all_keys(rows)
        
        # Write to CSV
        with open(full_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=headers,
                delimiter=delimiter,
                **kwargs
            )
            
            if include_headers:
                writer.writeheader()
            
            writer.writerows(rows)
        
        logger.info(f"Exported {len(rows)} rows to {full_path}")
        return full_path
    
    def _flatten_data(
        self,
        data: Any,
        parent_key: str = '',
        separator: str = '_'
    ) -> Dict[str, Any]:
        """
        Flatten nested structures for CSV export.
        
        Args:
            data: Data to flatten
            parent_key: Parent key for nested items
            separator: Separator for nested keys
        
        Returns:
            Flattened dictionary
        """
        # Convert Pydantic model to dict
        if isinstance(data, BaseModel):
            data = data.model_dump()
        
        items = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                
                if isinstance(value, dict):
                    items.update(self._flatten_data(value, new_key, separator))
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    if value and isinstance(value[0], (dict, BaseModel)):
                        # Complex nested objects - skip or stringify
                        items[new_key] = str(value)
                    else:
                        items[new_key] = ', '.join(str(v) for v in value)
                else:
                    items[new_key] = value
        else:
            items[parent_key] = data
        
        return items
    
    def _get_all_keys(self, rows: List[Dict[str, Any]]) -> List[str]:
        """Get all unique keys from list of dictionaries."""
        keys = set()
        for row in rows:
            keys.update(row.keys())
        return sorted(keys)
```

---

## Testing Structure

### 1. Test Configuration (`tests/conftest.py`)

```python
import pytest
from pathlib import Path
from typing import Dict, Any
import json

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.config.settings import Settings

@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        DISCOGS_API_TOKEN="test_token_12345",
        DISCOGS_USER_AGENT="TestAgent/1.0",
        LOG_DIR=Path("tests/logs"),
        EXPORT_DIR=Path("tests/exports"),
        RATE_LIMIT_REQUESTS=100,  # Higher for tests
        MAX_RETRIES=2
    )

@pytest.fixture
def mock_client(test_settings, monkeypatch):
    """Provide HTTP client with mocked settings."""
    monkeypatch.setattr(
        'musicagent.config.settings.settings',
        test_settings
    )
    return DiscogsHTTPClient()

@pytest.fixture
def sample_artist_data() -> Dict[str, Any]:
    """Sample artist response data."""
    return {
        "id": 12345,
        "name": "Miles Davis",
        "profile": "American jazz musician",
        "uri": "https://api.discogs.com/artists/12345",
        "urls": ["https://www.milesdavis.com"],
        "images": [
            {
                "type": "primary",
                "uri": "https://img.discogs.com/...",
                "width": 600,
                "height": 600
            }
        ]
    }

@pytest.fixture
def sample_release_data() -> Dict[str, Any]:
    """Sample release response data."""
    return {
        "id": 67890,
        "title": "Kind of Blue",
        "year": 1959,
        "artists": [
            {"name": "Miles Davis", "id": 12345}
        ],
        "labels": [
            {"name": "Columbia", "id": 111}
        ],
        "genres": ["Jazz"],
        "styles": ["Modal", "Cool Jazz"],
        "tracklist": [
            {
                "position": "A1",
                "title": "So What",
                "duration": "9:22"
            }
        ]
    }

@pytest.fixture
def sample_error_response() -> Dict[str, Any]:
    """Sample API error response."""
    return {
        "message": "Resource not found"
    }

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    from musicagent.utils.rate_limiter import RateLimiter
    return RateLimiter(max_requests=5, time_window=1)

@pytest.fixture
def temp_export_dir(tmp_path):
    """Temporary directory for export tests."""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return export_dir
```

---

### 2. Mock API Responses (`tests/mocks/api_responses.py`)

```python
from typing import Dict, Any

class MockDiscogsResponses:
    """Collection of mock API responses for testing."""
    
    ARTIST_SEARCH = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "per_page": 50,
            "items": 1,
            "urls": {}
        },
        "results": [
            {
                "id": 12345,
                "type": "artist",
                "user_data": {"in_wantlist": False, "in_collection": False},
                "master_id": None,
                "master_url": None,
                "uri": "/artists/12345",
                "title": "Miles Davis",
                "thumb": "https://img.discogs.com/...",
                "cover_image": "https://img.discogs.com/...",
                "resource_url": "https://api.discogs.com/artists/12345"
            }
        ]
    }
    
    ARTIST_DETAIL = {
        "id": 12345,
        "name": "Miles Davis",
        "profile": "American jazz musician and composer",
        "uri": "https://api.discogs.com/artists/12345",
        "urls": ["https://www.milesdavis.com"],
        "namevariations": ["Miles Dewey Davis III"],
        "members": [],
        "images": [
            {
                "type": "primary",
                "uri": "https://img.discogs.com/...",
                "resource_url": "https://img.discogs.com/...",
                "uri150": "https://img.discogs.com/...",
                "width": 600,
                "height": 600
            }
        ],
        "data_quality": "Correct"
    }
    
    RELEASE_DETAIL = {
        "id": 67890,
        "status": "Accepted",
        "year": 1959,
        "resource_url": "https://api.discogs.com/releases/67890",
        "uri": "https://www.discogs.com/release/67890",
        "artists": [
            {
                "name": "Miles Davis",
                "anv": "",
                "join": "",
                "role": "",
                "tracks": "",
                "id": 12345,
                "resource_url": "https://api.discogs.com/artists/12345"
            }
        ],
        "title": "Kind of Blue",
        "labels": [
            {
                "name": "Columbia",
                "catno": "CL 1355",
                "entity_type": "1",
                "entity_type_name": "Label",
                "id": 111,
                "resource_url": "https://api.discogs.com/labels/111"
            }
        ],
        "genres": ["Jazz"],
        "styles": ["Modal", "Cool Jazz"],
        "country": "US",
        "released": "1959-08-17",
        "tracklist": [
            {
                "position": "A1",
                "type_": "track",
                "title": "So What",
                "duration": "9:22"
            },
            {
                "position": "A2",
                "type_": "track",
                "title": "Freddie Freeloader",
                "duration": "9:33"
            }
        ]
    }
    
    ERROR_404 = {
        "message": "Resource not found"
    }
    
    ERROR_401 = {
        "message": "Invalid or missing authentication token"
    }
    
    ERROR_429 = {
        "message": "Rate limit exceeded"
    }
```

---

### 3. HTTP Client Tests (`tests/test_http_client.py`)

```python
import pytest
import responses
from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.exceptions.api_exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    RateLimitError,
    ServerError
)
from tests.mocks.api_responses import MockDiscogsResponses

@responses.activate
def test_get_artist_success(mock_client, sample_artist_data):
    """Test successful artist retrieval."""
    responses.add(
        responses.GET,
        'https://api.discogs.com/artists/12345',
        json=sample_artist_data,
        status=200
    )
    
    result = mock_client.get('artists/12345')
    
    assert result['id'] == 12345
    assert result['name'] == "Miles Davis"

@responses.activate
def test_get_artist_not_found(mock_client):
    """Test 404 error handling."""
    responses.add(
        responses.GET,
        'https://api.discogs.com/artists/99999',
        json=MockDiscogsResponses.ERROR_404,
        status=404
    )
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        mock_client.get('artists/99999')
    
    assert exc_info.value.status_code == 404

@responses.activate
def test_authentication_error(mock_client):
    """Test authentication error."""
    responses.add(
        responses.GET,
        'https://api.discogs.com/artists/12345',
        json=MockDiscogsResponses.ERROR_401,
        status=401
    )
    
    with pytest.raises(AuthenticationError):
        mock_client.get('artists/12345')

@responses.activate
def test_rate_limit_error(mock_client):
    """Test rate limit error with retry-after."""
    responses.add(
        responses.GET,
        'https://api.discogs.com/artists/12345',
        json=MockDiscogsResponses.ERROR_429,
        status=429,
        headers={'Retry-After': '60'}
    )
    
    with pytest.raises(RateLimitError) as exc_info:
        mock_client.get('artists/12345')
    
    assert exc_info.value.retry_after == 60
```

---

### 4. Model Tests (`tests/test_models.py`)

```python
import pytest
from pydantic import ValidationError
from musicagent.models.base import BaseDiscogsModel

def test_base_model_to_dict(sample_artist_data):
    """Test model to dictionary conversion."""
    
    class ArtistModel(BaseDiscogsModel):
        id: int
        name: str
        profile: str
    
    artist = ArtistModel.from_api_response(sample_artist_data)
    result = artist.to_dict()
    
    assert result['id'] == 12345
    assert result['name'] == "Miles Davis"

def test_base_model_to_json(sample_artist_data):
    """Test model to JSON conversion."""
    
    class ArtistModel(BaseDiscogsModel):
        id: int
        name: str
    
    artist = ArtistModel.from_api_response(sample_artist_data)
    json_str = artist.to_json()
    
    assert '"id": 12345' in json_str
    assert '"name": "Miles Davis"' in json_str

def test_model_validation_error():
    """Test validation error on invalid data."""
    
    class ArtistModel(BaseDiscogsModel):
        id: int
        name: str
    
    with pytest.raises(ValidationError):
        ArtistModel.from_api_response({"id": "not_an_int", "name": "Test"})
```

---

### 5. Exporter Tests (`tests/test_exporters.py`)

```python
import pytest
import json
import csv
from pathlib import Path
from musicagent.output.json_exporter import JSONExporter
from musicagent.output.csv_exporter import CSVExporter

def test_json_export(temp_export_dir, sample_artist_data):
    """Test JSON export."""
    exporter = JSONExporter(output_dir=temp_export_dir)
    
    output_path = exporter.export(
        sample_artist_data,
        "test_artist.json"
    )
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['id'] == 12345
    assert data['name'] == "Miles Davis"

def test_csv_export(temp_export_dir, sample_release_data):
    """Test CSV export."""
    exporter = CSVExporter(output_dir=temp_export_dir)
    
    output_path = exporter.export(
        [sample_release_data],
        "test_releases.csv"
    )
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['id'] == '67890'
    assert rows[0]['title'] == "Kind of Blue"

def test_csv_flatten_nested(temp_export_dir):
    """Test CSV flattening of nested data."""
    exporter = CSVExporter(output_dir=temp_export_dir)
    
    nested_data = {
        "id": 1,
        "name": "Test",
        "metadata": {
            "created": "2024-01-01",
            "updated": "2024-01-02"
        }
    }
    
    output_path = exporter.export([nested_data], "nested.csv")
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Check flattened keys
    assert 'metadata_created' in rows[0]
    assert 'metadata_updated' in rows[0]
```

---

### 6. Rate Limiter Tests (`tests/test_rate_limiter.py`)

```python
import pytest
import time
from musicagent.utils.rate_limiter import RateLimiter

def test_rate_limiter_basic():
    """Test basic rate limiting."""
    limiter = RateLimiter(max_requests=5, time_window=1)
    
    # Make 5 requests - should succeed
    for _ in range(5):
        limiter.acquire()
    
    status = limiter.get_status()
    assert status['requests_made'] == 5
    assert status['requests_remaining'] == 0

def test_rate_limiter_blocking():
    """Test that rate limiter blocks when limit reached."""
    limiter = RateLimiter(max_requests=2, time_window=1)
    
    start = time.time()
    
    # Make 3 requests - third should block
    for _ in range(3):
        limiter.acquire()
    
    elapsed = time.time() - start
    
    # Should have taken at least 1 second
    assert elapsed >= 1.0

def test_rate_limiter_status():
    """Test rate limiter status reporting."""
    limiter = RateLimiter(max_requests=5, time_window=1)
    
    # Make 3 requests
    for _ in range(3):
        limiter.acquire()
    
    status = limiter.get_status()
    
    assert status['requests_made'] == 3
    assert status['requests_remaining'] == 2
```

---

### 7. Request Builder Tests (`tests/test_request_builder.py`)

```python
import pytest
from musicagent.client.request_builder import RequestBuilder

def test_search_endpoint():
    """Test search endpoint building."""
    builder = RequestBuilder()
    url = builder.search(query="Miles Davis", search_type="artist").build()
    
    assert "/database/search" in url
    assert "q=Miles+Davis" in url
    assert "type=artist" in url

def test_artist_endpoint():
    """Test artist endpoint building."""
    builder = RequestBuilder()
    url = builder.artist(12345).build()
    
    assert "/artists/12345" in url

def test_pagination():
    """Test pagination parameters."""
    builder = RequestBuilder()
    url = builder.search(query="jazz").paginate(page=2, per_page=25).build()
    
    assert "page=2" in url
    assert "per_page=25" in url

def test_builder_reset():
    """Test builder reset functionality."""
    builder = RequestBuilder()
    
    builder.artist(123).paginate(1, 50)
    builder.reset()
    
    url = builder.search(query="test").build()
    
    assert "/database/search" in url
    assert "/artists/" not in url
```

---

## Test Coverage Goals

### Minimum Coverage Targets
- **Overall**: 80%+ code coverage
- **Core modules**: 90%+ (HTTP client, rate limiter, models)
- **Utility modules**: 85%+ (logger, retry handler)
- **Export modules**: 80%+

### Testing Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/musicagent --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_http_client.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_rate"
```

---

## Continuous Integration

### GitHub Actions Workflow (`.github/workflows/test.yml`)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src/musicagent --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

This completes the comprehensive testing and export specifications for the architecture.
