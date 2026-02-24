# Implementation Guide

## Overview

This guide provides a step-by-step roadmap for implementing the Discogs API foundational architecture for the MusicAgent project.

---

## Implementation Order

The components should be implemented in the following order to ensure dependencies are satisfied:

### Phase 1: Foundation (Core Infrastructure)

1. **Project Structure Setup**
   - Create directory structure
   - Initialize Git repository (if not already done)
   - Set up virtual environment

2. **Dependencies & Configuration**
   - Create `requirements.txt` and `requirements-dev.txt`
   - Create `.env.example` template
   - Implement `config/settings.py`

3. **Exception Hierarchy**
   - Implement `exceptions/api_exceptions.py`
   - Define all custom exception classes

### Phase 2: Utilities (Supporting Components)

4. **Logging System**
   - Implement `utils/logger.py`
   - Configure file rotation and structured logging
   - Create `RequestLogger` helper class

5. **Rate Limiting**
   - Implement `utils/rate_limiter.py`
   - Token bucket algorithm
   - Thread-safe implementation

6. **Retry Handler**
   - Implement `utils/retry_handler.py`
   - Exponential backoff with jitter
   - Retry decorator

### Phase 3: Core API Components

7. **Base Model**
   - Implement `models/base.py`
   - Pydantic v2 base class
   - Serialization methods

8. **Request Builder**
   - Implement `client/request_builder.py`
   - Fluent interface for URL construction
   - Parameter validation

9. **HTTP Client**
   - Implement `client/http_client.py`
   - Authentication
   - Rate limiting integration
   - Error handling
   - Request/response logging

### Phase 4: Data Export

10. **Export Infrastructure**
    - Implement `output/exporter.py` (base class)
    - Implement `output/json_exporter.py`
    - Implement `output/csv_exporter.py`

### Phase 5: Testing

11. **Test Infrastructure**
    - Create `tests/conftest.py` with fixtures
    - Create `tests/mocks/api_responses.py`

12. **Unit Tests**
    - `tests/test_exceptions.py`
    - `tests/test_rate_limiter.py`
    - `tests/test_logger.py`
    - `tests/test_models.py`
    - `tests/test_request_builder.py`
    - `tests/test_http_client.py`
    - `tests/test_exporters.py`

### Phase 6: Examples & Documentation

13. **Example Scripts**
    - `examples/quickstart.py`
    - `examples/basic_usage.py`
    - `examples/advanced_usage.py`
    - `examples/error_handling.py`
    - `examples/performance_test.py`

14. **Documentation**
    - Update `README.md`
    - Create API documentation
    - Add inline docstrings

---

## Detailed Implementation Steps

### Step 1: Project Structure Setup

```bash
# Create directory structure
mkdir -p src/musicagent/{client,models,exceptions,utils,output,config}
mkdir -p tests/{mocks,}
mkdir -p examples
mkdir -p docs
mkdir -p logs
mkdir -p exports

# Create __init__.py files
touch src/musicagent/__init__.py
touch src/musicagent/client/__init__.py
touch src/musicagent/models/__init__.py
touch src/musicagent/exceptions/__init__.py
touch src/musicagent/utils/__init__.py
touch src/musicagent/output/__init__.py
touch src/musicagent/config/__init__.py
touch tests/__init__.py
touch tests/mocks/__init__.py

# Create placeholder files
touch src/musicagent/client/{http_client.py,request_builder.py}
touch src/musicagent/models/{base.py,responses.py}
touch src/musicagent/exceptions/api_exceptions.py
touch src/musicagent/utils/{logger.py,rate_limiter.py,retry_handler.py}
touch src/musicagent/output/{exporter.py,json_exporter.py,csv_exporter.py}
touch src/musicagent/config/settings.py
```

### Step 2: Dependencies

Create `requirements.txt`:
```txt
# Core HTTP and API
requests>=2.31.0
requests-oauthlib>=1.3.1

# Data Modeling and Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Environment Configuration
python-dotenv>=1.0.0

# Logging Enhancements
python-json-logger>=2.0.7

# Data Export
pandas>=2.0.0

# Type Hints (Python 3.8 compatibility)
typing-extensions>=4.5.0
```

Create `requirements-dev.txt`:
```txt
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
responses>=0.23.0
faker>=19.0.0

# Code Quality
black>=23.7.0
mypy>=1.5.0
ruff>=0.0.287
isort>=5.12.0

# Documentation
sphinx>=7.0.0
sphinx-rtd-theme>=1.3.0
```

Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 3: Configuration

Create `.env.example`:
```bash
# Discogs API Configuration
DISCOGS_API_TOKEN=your_personal_access_token_here
DISCOGS_USER_AGENT=YourAppName/1.0 +https://yourwebsite.com

# Optional: Override defaults
# DISCOGS_BASE_URL=https://api.discogs.com
# RATE_LIMIT_REQUESTS=60
# RATE_LIMIT_WINDOW=60
# LOG_LEVEL=INFO
# LOG_DIR=logs
# LOG_FORMAT=json
# EXPORT_DIR=exports
# MAX_RETRIES=3
# REQUEST_TIMEOUT=30
```

Create your own `.env` file:
```bash
cp .env.example .env
# Edit .env with your actual API token
```

Update `.gitignore`:
```
# Environment
.env
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
logs/
exports/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Distribution
dist/
build/
*.egg-info/
```

### Step 4: Setup Configuration

Create `setup.py`:
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="musicagent",
    version="0.1.0",
    author="Simon Allocca",
    author_email="simonallocca6@gmail.com",
    description="A foundational Python application for interacting with the Discogs API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sallocc/MusicAgent",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "python-json-logger>=2.0.7",
        "pandas>=2.0.0",
        "typing-extensions>=4.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "responses>=0.23.0",
            "black>=23.7.0",
            "mypy>=1.5.0",
            "ruff>=0.0.287",
        ],
    },
)
```

Create `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "musicagent"
version = "0.1.0"
description = "A foundational Python application for interacting with the Discogs API"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["discogs", "api", "music", "client"]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src/musicagent --cov-report=html --cov-report=term"

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "F", "W", "I", "N", "UP"]
```

---

## Development Workflow

### 1. Setting Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd MusicAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .

# Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### 2. Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/musicagent --cov-report=html

# Run specific test file
pytest tests/test_http_client.py

# Run tests matching pattern
pytest -k "test_rate"

# Run with verbose output
pytest -v
```

### 3. Code Quality

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

### 4. Running Examples

```bash
# Quick start
python examples/quickstart.py

# Basic usage
python examples/basic_usage.py

# Advanced usage
python examples/advanced_usage.py

# Error handling
python examples/error_handling.py
```

---

## Verification Checklist

After implementation, verify each component:

### ✅ Configuration
- [ ] `.env` file created with API token
- [ ] Settings load correctly from environment
- [ ] All required directories are created

### ✅ Exceptions
- [ ] All exception classes defined
- [ ] Exception hierarchy works correctly
- [ ] `to_dict()` method works

### ✅ Logging
- [ ] Logs written to files
- [ ] File rotation works
- [ ] JSON format optional
- [ ] Console and file handlers work

### ✅ Rate Limiter
- [ ] Requests are rate limited correctly
- [ ] Thread-safe operation
- [ ] Status reporting works

### ✅ Retry Handler
- [ ] Exponential backoff works
- [ ] Jitter is applied
- [ ] Decorator can be applied to functions

### ✅ Base Model
- [ ] Pydantic v2 validation works
- [ ] `to_dict()` and `to_json()` work
- [ ] `from_api_response()` works

### ✅ Request Builder
- [ ] URL construction works
- [ ] Parameters are encoded correctly
- [ ] Pagination works
- [ ] Builder pattern (chaining) works

### ✅ HTTP Client
- [ ] Authentication headers set
- [ ] Rate limiting integrated
- [ ] Error handling works for all status codes
- [ ] Request/response logging works
- [ ] Session management works

### ✅ Exporters
- [ ] JSON export works
- [ ] CSV export works
- [ ] Nested data flattening works
- [ ] File creation in correct directory

### ✅ Tests
- [ ] All tests pass
- [ ] Coverage > 80%
- [ ] Mock responses work correctly
- [ ] Fixtures work correctly

### ✅ Examples
- [ ] All example scripts run without errors
- [ ] Examples demonstrate key features
- [ ] Error handling examples work

---

## Troubleshooting

### Common Issues

**Issue**: Import errors
```
Solution: Make sure package is installed in editable mode:
pip install -e .
```

**Issue**: `.env` file not loaded
```
Solution: Ensure python-dotenv is installed and .env is in project root
```

**Issue**: Rate limiting too aggressive
```
Solution: Adjust RATE_LIMIT_REQUESTS in .env file
```

**Issue**: Tests failing with authentication error
```
Solution: Set test token in conftest.py or use mocked responses
```

**Issue**: Logs not appearing
```
Solution: Check LOG_DIR permissions and LOG_LEVEL setting
```

---

## Performance Optimization Tips

1. **Connection Pooling**: The HTTP client uses `requests.Session()` for connection reuse
2. **Rate Limiting**: Pre-configured for Discogs limits (60 requests/minute)
3. **Retry Logic**: Exponential backoff prevents overwhelming the API
4. **Lazy Loading**: Parse only what you need from responses
5. **Batch Operations**: Group related requests when possible

---

## Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` as template
2. **Rotate API tokens regularly** - Update in `.env` file only
3. **Validate all inputs** - Pydantic models provide automatic validation
4. **Use HTTPS only** - Enforced by default in base URL
5. **Log safely** - Sensitive data should be masked in logs

---

## Next Steps After Implementation

1. **Create Response Models**
   - Define Pydantic models for common API responses
   - Artist, Release, Label, Master, etc.

2. **Add Caching Layer**
   - Implement response caching with TTL
   - Use Redis or in-memory cache

3. **Async Support**
   - Migrate to `httpx` for async/await support
   - Convert client methods to async

4. **CLI Tool**
   - Create command-line interface using Click or Typer
   - Enable quick queries from terminal

5. **Database Integration**
   - Add SQLAlchemy models
   - Implement data persistence

6. **Monitoring Dashboard**
   - Create dashboard for API usage metrics
   - Track rate limits, errors, performance

7. **Advanced Features**
   - Marketplace API integration
   - Collection management
   - Wantlist management
   - Image download utilities

---

## Support Resources

### Documentation
- **Discogs API Docs**: https://www.discogs.com/developers
- **Pydantic v2 Docs**: https://docs.pydantic.dev/latest/
- **Requests Docs**: https://requests.readthedocs.io/

### Community
- **Discogs API Forum**: https://www.discogs.com/forum/thread/759608
- **Stack Overflow**: Tag with `discogs-api`

### Getting Help
1. Check the logs in `logs/` directory
2. Review example scripts in `examples/`
3. Run tests to verify functionality
4. Consult inline docstrings in code

---

## Success Metrics

Your implementation is successful when:

- ✅ All tests pass with >80% coverage
- ✅ Example scripts run without errors
- ✅ API requests are properly rate limited
- ✅ Errors are handled gracefully with clear messages
- ✅ Logs capture all requests and responses
- ✅ Data can be exported to JSON and CSV
- ✅ Code follows type hints and passes mypy checks
- ✅ Documentation is complete and clear

---

**Good luck with the implementation! 🎵**
