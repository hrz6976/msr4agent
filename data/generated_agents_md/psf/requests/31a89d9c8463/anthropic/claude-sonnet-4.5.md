# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the `requests` library - a simple, elegant HTTP library for Python. It's one of the most popular Python packages with 30M+ downloads/week and 1M+ dependent repositories. The library provides a high-level, user-friendly API for making HTTP requests, abstracting the complexity of urllib3.

## Development Commands

### Installation
```bash
# Install in development mode with all dependencies
make init
# Or manually:
pip install -e .[socks]
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run tests on current Python version
pytest tests

# Run specific test file
pytest tests/test_requests.py

# Run specific test
pytest tests/test_requests.py::TestRequests::test_specific_test

# Run tests with coverage
make coverage

# Run tests across all Python versions (uses tox)
make test

# CI test run (generates JUnit XML report)
make ci
```

### Code Quality
```bash
# Run flake8 linter
make flake8
```

### Documentation
```bash
# Build HTML documentation
make docs
# Output will be in docs/_build/html/index.html
```

## Architecture

### Core Module Structure

The library follows a layered architecture with clear separation of concerns:

**API Layer** (`api.py`):
- Top-level convenience functions: `get()`, `post()`, `put()`, `delete()`, etc.
- These are simple wrappers around `Session.request()`
- User's main entry point to the library

**Session Layer** (`sessions.py`):
- `Session` class manages and persists settings across requests (cookies, auth, proxies)
- Handles request preparation, sending, and response processing
- Manages redirect logic and history
- Session merges its settings with per-request settings using `merge_setting()`

**Models Layer** (`models.py`):
- `Request`: High-level request representation (user's input)
- `PreparedRequest`: Low-level HTTP request ready to send (actual bytes/headers)
- `Response`: HTTP response with content, status, headers, and convenience methods like `.json()`
- Request preparation involves encoding, header construction, and body serialization

**Adapter Layer** (`adapters.py`):
- `HTTPAdapter`: Transport adapter that uses urllib3 for actual HTTP communication
- Manages connection pooling via urllib3's `PoolManager`
- Handles retries, timeouts, and SSL verification
- `SOCKSProxyManager` for SOCKS proxy support
- Adapters are pluggable - sessions use a mount dict: `session.mount('https://', adapter)`

**Supporting Modules**:
- `auth.py`: Authentication handlers (Basic, Digest, custom)
- `cookies.py`: Cookie jar handling and management
- `exceptions.py`: HTTP-specific exceptions
- `hooks.py`: Event hooks (response, request)
- `utils.py`: Utility functions for headers, encodings, URLs
- `structures.py`: Special data structures (e.g., `CaseInsensitiveDict`)
- `status_codes.py`: HTTP status code constants

### Request Flow

1. User calls `requests.get(url, **kwargs)` → calls `request('GET', url, **kwargs)`
2. `api.request()` creates a `Session` and calls `session.request()`
3. Session creates a `Request` object and prepares it into a `PreparedRequest`
4. Session merges session-level settings with request-specific settings
5. Session sends via adapter: `adapter.send(prepared_request)`
6. Adapter uses urllib3 to make the actual HTTP connection
7. Adapter builds a `Response` object from urllib3's response
8. Session handles redirects if needed, building response history
9. Response returned to user

### Key Design Patterns

**Adapter Pattern**: The `HTTPAdapter` allows swapping transport implementations. Users can mount custom adapters for specific URL prefixes.

**Preparation Pattern**: Requests go through a two-phase process:
1. High-level `Request` (user's intent)
2. Low-level `PreparedRequest` (wire format)

This separation allows inspection, modification, and reuse of prepared requests.

**Hook System**: Users can register callbacks for events like 'response'. Hooks receive the full response object and can modify it.

**Settings Merging**: Session-level and request-level settings are merged using `merge_setting()` and `merge_hooks()`. Request settings take precedence.

## Testing Notes

- Tests use `pytest` with `pytest-httpbin` for an HTTP testing server
- `conftest.py` provides fixtures including `httpbin` and `httpbin_secure` for test endpoints
- Test coverage is tracked with `pytest-cov`
- Tests run in parallel with `pytest-xdist` (uses CPU count by default)
- Doctests are enabled for modules

## Compatibility

- Supports Python 2.7 and 3.6+
- Uses compatibility layer in `compat.py` for Python 2/3 differences
- Character encoding handled via `charset_normalizer` (Python 3) or `chardet` (Python 2)
- Dependencies: `urllib3>=1.21.1,<1.27`, `certifi`, `idna`, encoding library

## Important Conventions

- **No mutable default arguments**: Use `None` and initialize inside function
- **Lazy imports**: Some imports are delayed to avoid initialization issues (see `encodings.idna` comment in models.py)
- **Encoding handling**: Response encoding detection is complex - see `Response.apparent_encoding` and `Response.text`
- **URL handling**: URLs are requoted and normalized - be careful with special characters
- **Auth tuple format**: `auth=(username, password)` for Basic auth
- **Proxy format**: `proxies={'http': 'http://proxy:port', 'https': 'https://proxy:port'}`

## Git Notes

When cloning this repository, you may need the `-c fetch.fsck.badTimezone=ignore` flag due to a historical commit with a malformed timestamp:

```bash
git clone -c fetch.fsck.badTimezone=ignore https://github.com/psf/requests.git
```
