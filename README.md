# MusicAgent

An Agentic AI application which makes use of the Discogs API for music analysis and song recommendations.

## 🏗️ Architecture Overview

This project provides a **production-ready, enterprise-grade Python foundation** for interacting with the Discogs API. The architecture emphasizes robustness, maintainability, and extensibility while adhering to Python best practices.

### Key Features

- ✅ **Type-Safe**: Comprehensive type hints throughout (Python 3.8+)
- ✅ **Pydantic v2**: Runtime validation and serialization
- ✅ **Smart Rate Limiting**: Token bucket algorithm (60 requests/minute)
- ✅ **Automatic Retries**: Exponential backoff with jitter
- ✅ **Structured Logging**: JSON logs with file rotation
- ✅ **Error Handling**: Custom exception hierarchy
- ✅ **Multi-Format Export**: JSON and CSV support
- ✅ **MCP Server Integration**: AI tool integration via Model Context Protocol
- ✅ **Well Documented**: Comprehensive docstrings and examples

## 📋 Prerequisites

- Python 3.8 or higher
- Discogs API personal access token ([Get one here](https://www.discogs.com/settings/developers))

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd MusicAgent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

#Install local dependencies
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Discogs API token
# DISCOGS_API_TOKEN=your_token_here
```

### 3. Basic Usage

```python
from musicagent import DiscogsHTTPClient, RequestBuilder

# Initialize client
client = DiscogsHTTPClient()

# Search for an artist
builder = RequestBuilder()
url = builder.search(query="Miles Davis", search_type="artist").build()

# Make request (note: need to strip base URL from endpoint)
from musicagent.config import settings
endpoint = url.replace(settings.DISCOGS_BASE_URL, "")
results = client.get(endpoint)

# Display results
for artist in results['results']:
    print(f"{artist['title']} (ID: {artist['id']})")
```

## 📁 Project Structure

```
MusicAgent/
├── src/
│   └── musicagent/           # Main package
│       ├── client/           # HTTP client & request builder
│       ├── models/           # Pydantic data models
│       ├── exceptions/       # Custom exceptions
│       ├── utils/            # Rate limiter, logger, retry handler
│       ├── output/           # Data exporters (JSON, CSV)
│       └── config/           # Configuration management
├── mcp_server/              # MCP server for AI tool integration
│   ├── discogs_server.py    # MCP server implementation
│   ├── README.md            # MCP server documentation
│   └── requirements.txt     # MCP dependencies
├── docs/                    # Documentation
│   └── MCP_SERVER_GUIDE.md  # MCP integration guide
├── plans/                   # Architecture documentation
├── logs/                    # Log files (auto-created)
├── exports/                 # Export output (auto-created)
├── requirements.txt         # Production dependencies
├── .env.example            # Configuration template
└── README.md               # This file
```

## 🤖 MCP Server for AI Integration

This project includes a **Model Context Protocol (MCP) server** that enables AI tools and workflows to interact with the Discogs API through a standardized interface.

### Available Tools

The MCP server provides 6 powerful tools:

1. **`get_collection_releases`** - Browse your Discogs collection with pagination and sorting
2. **`add_release_to_collection`** - Add releases to your collection
3. **`create_user_list`** - Create custom lists for organizing releases
4. **`search_by_artist`** - Search the Discogs database by artist name
5. **`search_by_title`** - Search by song or album title
6. **`search_by_genre`** - Filter releases by genre

All tools return **Markdown-formatted responses** instead of raw JSON for better readability in AI workflows.

### Quick Setup

1. Ensure your `.env` file has your Discogs API token configured
2. Install the MCP package: `pip install mcp`
3. The server is already configured in your MCP settings

See the **[MCP Server Integration Guide](docs/MCP_SERVER_GUIDE.md)** for detailed documentation.

### Example AI Workflows

- **Music Discovery**: "Find me some Jazz albums from the 1960s"
- **Collection Management**: "Add the top-rated Miles Davis albums to my collection"
- **Data Analysis**: "What genres are most represented in my collection?"

## 🔧 Core Components

### HTTP Client ([`DiscogsHTTPClient`](src/musicagent/client/http_client.py))

Main client for API interactions with built-in rate limiting and error handling.

```python
from musicagent import DiscogsHTTPClient

client = DiscogsHTTPClient()

# GET request
response = client.get("artists/12345")

# Check rate limit status
status = client.get_rate_limit_status()
print(f"Requests remaining: {status['requests_remaining']}")
```

### Request Builder ([`RequestBuilder`](src/musicagent/client/request_builder.py))

Fluent interface for constructing API URLs with parameters.

```python
from musicagent import RequestBuilder

builder = RequestBuilder()

# Build search URL with pagination
url = builder.search(query="Jazz", search_type="release") \
             .paginate(page=1, per_page=50) \
             .sort("year", "desc") \
             .build()

# Build artist releases URL
url = builder.reset().artist_releases(12345).paginate(1, 100).build()
```

### Base Model ([`BaseDiscogsModel`](src/musicagent/models/base.py))

Pydantic v2 base class for API response models.

```python
from musicagent import BaseDiscogsModel
from typing import Optional

class Artist(BaseDiscogsModel):
    id: int
    name: str
    profile: Optional[str] = None

# Parse API response
artist = Artist.from_api_response(response_data)

# Export to JSON
json_str = artist.to_json(indent=2)

# Export to dict
data = artist.to_dict(exclude_none=True)
```

### Exception Handling

Comprehensive exception hierarchy for different error scenarios.

```python
from musicagent import (
    DiscogsHTTPClient,
    RateLimitError,
    ResourceNotFoundError,
    AuthenticationError
)

client = DiscogsHTTPClient()

try:
    response = client.get("artists/12345")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ResourceNotFoundError:
    print("Artist not found")
except AuthenticationError:
    print("Invalid API token")
```

## ⚙️ Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCOGS_API_TOKEN` | *Required* | Your Discogs personal access token |
| `DISCOGS_USER_AGENT` | `MusicAgent/1.0` | User agent for API requests |
| `RATE_LIMIT_REQUESTS` | `60` | Max requests per minute |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (json or text) |
| `EXPORT_DIR` | `exports` | Directory for exported files |

See [`.env.example`](.env.example) for all available options.

## 📊 Logging

The application provides comprehensive logging with:

- **File rotation**: Automatic log rotation at 10MB
- **Multiple handlers**: Console, all logs, and errors only
- **Structured output**: Optional JSON format for log aggregation
- **Request tracking**: Correlation IDs for tracing requests

Logs are stored in the `logs/` directory:
- `musicagent.log` - All logs
- `errors.log` - Errors only

## 🎯 Usage Examples

### Search for Artists

```python
from musicagent import DiscogsHTTPClient, RequestBuilder
from musicagent.config import settings

client = DiscogsHTTPClient()
builder = RequestBuilder()

# Build search URL
url = builder.search(query="Beatles", search_type="artist").build()
endpoint = url.replace(settings.DISCOGS_BASE_URL, "")

# Execute search
results = client.get(endpoint)

# Process results
for artist in results['results']:
    print(f"{artist['title']} - {artist.get('uri', 'N/A')}")
```

### Get Artist Details

```python
from musicagent import DiscogsHTTPClient

client = DiscogsHTTPClient()

# Get artist by ID
artist = client.get("artists/97784")  # Miles Davis

print(f"Name: {artist['name']}")
print(f"Profile: {artist['profile'][:200]}...")
print(f"URLs: {', '.join(artist.get('urls', []))}")
```

### Handle Pagination

```python
from musicagent import DiscogsHTTPClient, RequestBuilder
from musicagent.config import settings

client = DiscogsHTTPClient()
builder = RequestBuilder()

all_releases = []
page = 1

while True:
    # Build paginated request
    url = builder.reset().artist_releases(12345).paginate(page, 100).build()
    endpoint = url.replace(settings.DISCOGS_BASE_URL, "")
    
    response = client.get(endpoint)
    all_releases.extend(response.get('releases', []))
    
    # Check if more pages
    pagination = response.get('pagination', {})
    if page >= pagination.get('pages', 1):
        break
    
    page += 1

print(f"Total releases: {len(all_releases)}")
```

### Error Handling with Retries

```python
import time
from musicagent import DiscogsHTTPClient, RateLimitError

client = DiscogsHTTPClient()

def fetch_with_retry(endpoint, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return client.get(endpoint)
        except RateLimitError as e:
            if attempt < max_attempts - 1:
                print(f"Rate limited, waiting {e.retry_after}s...")
                time.sleep(e.retry_after)
            else:
                raise

response = fetch_with_retry("artists/12345")
```

## 📚 Documentation

### Core Documentation

Comprehensive architecture documentation is available in the [`plans/`](plans/) directory:

- **[Architecture Overview](plans/discogs_api_architecture.md)** - Complete system design
- **[Implementation Specifications](plans/implementation_specifications.md)** - Detailed component specs
- **[Testing Strategy](plans/exporters_and_testing.md)** - Test infrastructure and examples
- **[Usage Examples](plans/example_usage.md)** - Complete example scripts
- **[Implementation Guide](plans/implementation_guide.md)** - Step-by-step setup guide
- **[Project Summary](plans/PROJECT_SUMMARY.md)** - Executive overview

### MCP Server Documentation

- **[MCP Server Integration Guide](docs/MCP_SERVER_GUIDE.md)** - Complete guide to using the MCP server
- **[MCP Server README](mcp_server/README.md)** - Server features and setup

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It contains your API token
2. **Use `.env.example`** as a template for configuration
3. **Rotate tokens regularly** - Update in `.env` file only
4. **Validate all inputs** - Pydantic models provide automatic validation
5. **Monitor logs** - Check for unauthorized access attempts

## 🧪 Testing

(Test infrastructure to be implemented - see [`plans/exporters_and_testing.md`](plans/exporters_and_testing.md))

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src/musicagent --cov-report=html
```

## 🚧 Future Enhancements

- [ ] Async/await support with `httpx`
- [ ] Response caching layer
- [ ] CLI tool for quick queries
- [ ] Database integration
- [ ] WebSocket support for real-time updates
- [ ] GraphQL query optimization
- [ ] Monitoring dashboard

## 📝 License

See [LICENSE](LICENSE) file for details.

## 👤 Author

**Simon Allocca**

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📞 Support

For issues and questions:
1. Check the [documentation](plans/)
2. Review the logs in `logs/` directory
3. Consult inline docstrings in the code

## 🙏 Acknowledgments

- [Discogs API](https://www.discogs.com/developers/) for providing the music database API
- [Pydantic](https://docs.pydantic.dev/) for excellent data validation
- [Requests](https://requests.readthedocs.io/) for HTTP client functionality

---

**Version**: 0.1.0  
**Python**: 3.8+  
**Status**: ✅ Core Components Implemented
