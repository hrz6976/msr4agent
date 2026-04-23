# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastMCP is a production-ready Python framework for building Model Context Protocol (MCP) servers and clients. It provides:

- **Server Framework**: FastMCP class for creating MCP servers with tools, resources, prompts, and context
- **Client Library**: Client class for connecting to MCP servers via multiple transports (STDIO, SSE, HTTP)
- **Enterprise Authentication**: Comprehensive OAuth providers (Google, GitHub, Azure, WorkOS, Auth0, Discord, AWS, etc.)
- **Advanced Patterns**: Server composition, proxying, OpenAPI/FastAPI integration, tool transformation
- **Testing Infrastructure**: In-memory transport for efficient testing without process spawning

The codebase is structured as a dual framework: server-side components for building MCP servers and client-side components for consuming them.

## Development Commands

### Environment Setup

```bash
# Install dependencies (use uv for package management)
uv sync

# Activate environment (if not using uv run prefix)
source .venv/bin/activate
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
uv run pytest --cov=src --cov=examples --cov-report=html

# Run specific test file
pytest tests/path/to/test_file.py

# Run specific test function
pytest tests/path/to/test_file.py::test_function_name

# Run tests excluding integration tests
pytest -m "not integration"

# Run with verbose output and stop on first failure
pytest -xvs
```

**Test Markers:**
- `integration`: Integration tests (may hit external services)
- `client_process`: Tests that spawn client processes via stdio transport

**Test Configuration:**
- `FASTMCP_TEST_MODE=1` is set automatically via pytest.ini_options
- Tests use isolated settings.home directories to prevent SQLite locking issues
- Timeout is 5 seconds per test by default

### Code Quality

```bash
# Install pre-commit hooks (runs automatically on commit)
uv run prek install

# Run all checks manually (formatting, linting, type checking)
prek run --all-files
# or
uv run prek run --all-files

# Type checking only (using 'ty' type checker, not mypy/pyright)
uv run ty check
just typecheck
```

**Pre-commit hooks include:**
- validate-pyproject: Validates pyproject.toml syntax
- prettier: Formats YAML and JSON5 files
- ruff-check: Lints and auto-fixes Python code
- ruff-format: Formats Python code
- ty: Type checks Python code in src/ and tests/
- codespell: Spell checks code and comments
- no-commit-to-branch: Prevents commits directly to main

### Building & Running

```bash
# Build project
just build

# Run server locally (STDIO transport)
fastmcp run path/to/server.py

# Run server with HTTP transport
fastmcp run path/to/server.py --transport http --port 8000

# Serve documentation locally
just docs
```

### Documentation

```bash
# Generate API reference for all modules
just api-ref-all

# Generate API reference for specific modules
just api-ref fastmcp.server fastmcp.client

# Clean API reference docs
just api-ref-clean
```

## Architecture Overview

### Core Components

**Server Side (`src/fastmcp/server/`):**
- `server.py`: FastMCP class - main server implementation with composition, mounting, and transport support
- `context.py`: Context class - provides tools/resources/prompts access to MCP capabilities (logging, sampling, progress reporting, resource reading)
- `low_level.py`: LowLevelServer - wrapper around MCP SDK's Server with lifecycle management
- `http.py`: HTTP/SSE transport implementations using Starlette

**Client Side (`src/fastmcp/client/`):**
- `client.py`: Client class - main client for connecting to and interacting with MCP servers
- `transports.py`: Transport implementations (STDIO, SSE, HTTP, FastMCPTransport for in-memory testing)
- `auth/`: Client-side auth handlers (OAuth, Bearer tokens)
- `tasks.py`: Client-side task management

**Provider System (`src/fastmcp/server/providers/`):**
Providers are the internal abstraction for composing MCP servers:
- `base.py`: Provider abstract base class
- `local_provider.py`: LocalProvider - wraps tools/resources/prompts registered directly on a FastMCP instance
- `fastmcp_provider.py`: Wraps another FastMCP instance for mounting/composition
- `proxy.py`: ProxyProvider - proxies to remote MCP servers
- `openapi/`: OpenAPIProvider - generates MCP tools from OpenAPI specs
- `transforming.py`: TransformingProvider - applies transformations to tools/resources/prompts from another provider

**Authentication (`src/fastmcp/server/auth/`):**
- Enterprise OAuth providers in `providers/` (google.py, github.py, azure.py, workos.py, auth0.py, discord.py, aws.py, scalekit.py, etc.)
- Token storage with TTL management using py-key-value-aio (disk, keyring, memory backends)
- OAuth proxy pattern for Dynamic Client Registration (DCR) with standard providers

**Tools, Resources & Prompts:**
- `tools/tool.py`: Tool base classes and FunctionTool
- `resources/resource.py`: Resource base classes
- `resources/template.py`: ResourceTemplate for parameterized resources
- `prompts/prompt.py`: Prompt base classes and FunctionPrompt

**Utilities (`src/fastmcp/utilities/`):**
- `async_utils.py`: Async utilities (gather, sync wrappers)
- `logging.py`: Logging configuration with Rich support
- `json_schema.py`: JSON schema generation from type hints
- `visibility.py`: Visibility filtering for tools/resources/prompts
- `openapi/`: OpenAPI parsing and generation
- `mcp_server_config/`: MCP server configuration parsing

### Key Architectural Patterns

**1. Server Composition via Providers**
FastMCP servers compose multiple providers internally. When you call `mcp.mount()` or `mcp.import_server()`, FastMCP wraps the mounted server in a provider and adds it to its internal provider list. All tool/resource/prompt operations iterate through providers.

**2. In-Memory Testing**
The `FastMCPTransport` enables efficient testing by connecting a Client directly to a FastMCP instance without process spawning:
```python
async with Client(mcp_instance) as client:
    result = await client.call_tool("tool_name", args)
```

**3. Context Injection**
Functions decorated with `@mcp.tool`, `@mcp.resource`, or `@mcp.prompt` can receive a `Context` parameter. FastMCP automatically injects the context when the function signature includes `ctx: Context`.

**4. Dual Tool/Resource Types**
- Internal types: `Tool`, `Resource`, `Prompt` (FastMCP's representation)
- SDK types: `SDKTool`, `SDKResource`, `SDKPrompt` (MCP SDK's wire format)
- Conversion happens at the provider boundary

**5. Settings & Environment**
- `settings.py`: Global settings object loaded from environment variables
- Prefix: `FASTMCP_*` (e.g., `FASTMCP_LOG_LEVEL`, `FASTMCP_TEST_MODE`)
- Settings can be temporarily overridden in tests using `temporary_settings()`

## Code Conventions

### Testing Patterns

**Use in-memory transport for testing:**
```python
from fastmcp import FastMCP, Client

async def test_something():
    mcp = FastMCP("Test")
    
    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b
    
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 1, "b": 2})
        assert result.content[0].text == "3"
```

**Test fixtures (tests/conftest.py):**
- `isolate_settings_home`: Automatically isolates settings.home per test
- Windows compatibility: Uses SelectorEventLoop instead of ProactorEventLoop

**Integration tests:**
- Place in `tests/integration_tests/` - automatically marked with `@pytest.mark.integration`
- Can be excluded with `pytest -m "not integration"`

### Type Checking

**Use 'ty' not mypy/pyright:**
- The project uses `ty` (Astral's type checker) configured in pyproject.toml
- Run with `uv run ty check`
- Known limitation: ty doesn't support type narrowing with isinstance() on unions
- Use `# ty: ignore[invalid-argument-type]` sparingly for this limitation

**Common type patterns:**
- `NotSet` / `NotSetT`: Sentinel value for "not provided" (different from None)
- Type vars: `T`, `ResultT`, `LifespanResultT`
- Protocol types: `FunctionPrompt`, `FunctionTool`

### Import Patterns

**Conditional imports for type checking:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.client import Client
    from fastmcp.server.providers.openapi import OpenAPIProvider
```

**Lazy imports in __init__.py:**
```python
# Configure logging first
from fastmcp.settings import Settings
settings = Settings()
if settings.log_enabled:
    _configure_logging(...)

# Then import main components
from fastmcp.server.server import FastMCP
from fastmcp.client import Client
```

### Async Conventions

- All I/O operations are async (use `async def` and `await`)
- Use `anyio` for portable async primitives (TaskGroup, Event, etc.)
- Use `asyncio` only for asyncio-specific features
- Context managers: Use `@asynccontextmanager` for async resource management
- Use `AsyncExitStack` for dynamic async context management

### Error Handling

**FastMCP exception hierarchy:**
- `FastMCPError`: Base exception
  - `ToolError`: Tool execution errors
  - `ResourceError`: Resource access errors
  - `PromptError`: Prompt generation errors
  - `ValidationError`: Input validation errors
  - `NotFoundError`: Tool/resource/prompt not found
  - `DisabledError`: Component disabled

**Wrap MCP SDK errors:**
- Catch `McpError` from MCP SDK and convert to FastMCP exceptions where appropriate
- Preserve original error info in exception chain

## Common Development Tasks

### Adding a New OAuth Provider

1. Create `src/fastmcp/server/auth/providers/newprovider.py`
2. Subclass `AuthProvider` or use `create_oauth_provider()` helper
3. Configure OAuth endpoints, scopes, and token handling
4. Add token storage with TTL using `py-key-value-aio`
5. Add tests in `tests/server/auth/`
6. Add example in `examples/auth/newprovider_oauth/`

### Adding a Feature to FastMCP Server

1. Consider if it belongs in LocalProvider or directly on FastMCP
2. Add method to `server.py` if client-facing API
3. Add tests using in-memory transport pattern
4. Update type hints and docstrings
5. Add example if non-trivial

### Adding a New Transport

1. Subclass `ClientTransport` in `src/fastmcp/client/transports.py`
2. Implement `connect_session()` async context manager
3. Add to `infer_transport()` if auto-detection should work
4. Add tests in `tests/client/`

## Dependencies

**Core:**
- `mcp`: Official MCP SDK (protocol implementation)
- `pydantic`: Data validation and JSON schema generation
- `httpx`: HTTP client
- `uvicorn`: ASGI server for HTTP/SSE transports
- `starlette`: ASGI framework for HTTP endpoints
- `authlib`: OAuth implementations
- `py-key-value-aio`: Async key-value storage for tokens (disk, keyring, memory)

**CLI:**
- `cyclopts`: CLI framework (note: v4 includes docutils dependency with complex licensing; v5+ removes it)
- `rich`: Terminal formatting

**Dev:**
- `pytest` + plugins: Testing framework
- `ruff`: Linting and formatting
- `ty`: Type checking (not mypy/pyright)
- `prek`: Pre-commit framework
- `inline-snapshot`: Snapshot testing
- `pytest-httpx`: HTTP mocking

## Additional Notes

- **Python version**: Requires Python 3.10+
- **Package manager**: Use `uv` for all package operations (not pip directly)
- **Justfile**: Contains common development commands - use `just <command>`
- **Git workflow**: Never commit directly to main (enforced by pre-commit hook)
- **FastMCP v3.0**: In development with breaking changes - pin to `fastmcp<3` if stability needed
- **Documentation**: Lives in `docs/` (Mintlify format) and is deployed to gofastmcp.com
