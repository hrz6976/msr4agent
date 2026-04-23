# GEMINI.md - Graphiti

## Project Overview

**Graphiti** is a Python framework for building and querying real-time, temporally-aware knowledge graphs. It's designed for AI agents operating in dynamic environments, allowing them to continuously integrate user interactions, enterprise data, and external information into a coherent, queryable graph.

- **Core Technologies:** Python, Pydantic, Neo4j/FalkorDB
- **LLM Integration:** Defaults to OpenAI, with optional support for Google Gemini, Anthropic, Groq, and local models via Ollama.
- **Architecture:** The project is structured as a Python library (`graphiti-core`) with optional components for different LLM providers and database backends. It includes a `server` directory for a FastAPI-based REST API and an `mcp_server` for integration with AI assistants via the Model Context Protocol (MCP).

## Building and Running

The project uses `uv` for dependency management and `make` for common development tasks.

### Installation

1.  **Install `uv`:** Follow the instructions at [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/).
2.  **Install dependencies:**
    ```bash
    make install
    ```
    This command uses `uv` to sync the development environment, including all optional dependencies.

### Running Tests

-   **Run all tests:**
    ```bash
    make test
    ```
-   **Integration Tests:** To run integration tests, you need to set environment variables for the services you want to test (e.g., `TEST_OPENAI_API_KEY`, `TEST_URI` for Neo4j).

### Running the REST Service

The `server` directory contains a FastAPI application. To run it, you would typically use an ASGI server like Uvicorn.

```bash
# TODO: Add specific command to run the server.
# Example using uvicorn:
# uv run uvicorn server.main:app --reload
```

### Running the MCP Server

The `mcp_server` can be deployed using Docker with Neo4j.

```bash
# TODO: Add specific command to run the MCP server.
# Refer to mcp_server/README.md for detailed instructions.
```

## Development Conventions

### Code Style and Quality

The project uses `ruff` for linting and formatting, and `pyright` for static type checking.

-   **Format code:**
    ```bash
    make format
    ```
-   **Lint code:**
    ```bash
    make lint
    ```
-   **Run all checks (format, lint, test):**
    ```bash
    make check
    ```

### Contributing

-   Contributions are managed through GitHub pull requests.
-   For large changes, a GitHub issue (RFC) discussing the design is expected.
-   New third-party integrations must be added as optional dependencies.
-   All contributions should include or update tests and documentation as necessary.
-   The `CONTRIBUTING.md` file provides detailed guidelines for setting up the environment, making changes, and submitting pull requests.

### Key Files

-   `pyproject.toml`: Defines project metadata, dependencies, and optional extras for different LLM providers and database backends.
-   `Makefile`: Contains shortcuts for common development tasks like installing dependencies, formatting, linting, and testing.
-   `README.md`: Provides a high-level overview of the project, its features, and installation instructions.
-   `CONTRIBUTING.md`: Outlines the contribution process, development setup, and code style guidelines.
-   `graphiti_core/`: The main source code for the library.
-   `server/`: Contains the FastAPI-based REST API.
-   `mcp_server/`: Contains the MCP server implementation.
-   `examples/`: Contains example usage of the library.
