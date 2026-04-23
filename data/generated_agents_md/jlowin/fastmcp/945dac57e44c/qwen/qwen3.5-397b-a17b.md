# AGENTS.md

This file provides instructional context for agents interacting with the `fastmcp` repository.

## Project Overview

**FastMCP** is a high-performance Python framework for building servers and clients that adhere to the **Model Context Protocol (MCP)**. It provides a simple, Pythonic interface for creating, managing, and interacting with MCP servers, enabling developers to expose data and functionality to LLM applications in a secure and standardized way.

The project is structured as a standard Python library with the main source code located in the `src/fastmcp` directory. It uses modern Python tooling, including `uv` for dependency management, `hatchling` for building, `pytest` for testing, and `ruff` for linting.

### Key Features:

- **MCP Server & Client:** Core components for building and interacting with MCP applications.
- **Tools, Resources, and Prompts:** Decorator-based approach to defining tools (`@mcp.tool`), data resources (`@mcp.resource`), and prompt templates (`@mcp.prompt`).
- **Enterprise Authentication:** Built-in support for OAuth providers like Google, GitHub, Azure, Auth0, and more.
- **Deployment:** Supports local development, self-hosting (HTTP/SSE), and deployment to FastMCP Cloud.
- **Advanced Patterns:** Includes features for server composition, proxying, and generating MCP servers from OpenAPI specs or FastAPI applications.

## Building and Running

The project uses `uv` for managing dependencies and running tasks. The `justfile` in the root directory defines several convenient commands for common development tasks.

### Installation

To set up the development environment and install all necessary dependencies, run:

```bash
uv sync
```
or
```bash
just build
```

### Running the Server

A FastMCP server can be run from a Python script. Create a file (e.g., `server.py`) with the following content:

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

Then, run the server using the `fastmcp` CLI:

```bash
fastmcp run server.py
```

### Running Tests

The project has a comprehensive test suite using `pytest`. To run the tests, use the following command:

```bash
just test
```
or
```bash
uv run --frozen pytest -xvs tests
```

## Development Conventions

### Code Style and Linting

The project uses `ruff` for code formatting and linting. The configuration can be found in the `pyproject.toml` file. It's recommended to install the `pre-commit` hooks to automatically run checks before each commit.

To install the hooks:
```bash
uv run prek install
```
To run the checks manually:
```bash
prek run --all-files
```
or
```bash
uv run prek run --all-files
```
### Type Checking

The project uses `ty` for static type checking. To run the type checker, use the following command:

```bash
just typecheck
```
or
```bash
uv run --frozen ty check
```

### Documentation

The project's documentation is built using [Mintlify](https://mintlify.com/) and is located in the `docs` directory. To serve the documentation locally, run:

```bash
just docs
```

API reference documentation is generated using `mdxify`. The `justfile` provides commands for generating and cleaning the API reference.
