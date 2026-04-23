# AGENTS.md

This file provides instructional context about the `Graphiti` project for AI agents.

## Project Overview

**Graphiti** is a Python framework for building and querying temporally-aware knowledge graphs. It's designed for AI agents operating in dynamic environments, allowing for continuous integration of data from various sources into a coherent, queryable graph.

**Key Technologies:**
- **Language:** Python 3.10+
- **Graph Database:** Neo4j (v5.26+) or FalkorDB
- **LLM Integration:** OpenAI (default), Google Gemini, Anthropic, Groq, and local models via Ollama.
- **Package Management:** `uv` and `poetry`
- **API:** FastAPI for the REST service, and a Model Context Protocol (MCP) server for AI assistant integration.
- **Containerization:** Docker and Docker Compose

**Architecture:**
The project is architected as a core Python library (`graphiti-core`) with two main server implementations:
1.  A **REST API server** (`/server`) providing access to Graphiti's functionality.
2.  An **MCP server** (`/mcp_server`) that allows AI assistants (like Claude or Cursor) to use Graphiti for memory and context.

The application services are designed to be run in containers, connecting to a Neo4j or FalkorDB backend.

## Building and Running

### Local Development

**1. Installation:**
Install the project dependencies, including development tools, using `uv`:
```bash
make install
```

**2. Linting and Formatting:**
- To format the code:
  ```bash
  make format
  ```
- To lint the code:
  ```bash
  make lint
  ```

**3. Running Tests:**
Execute the test suite using `pytest`:
```bash
make test
```

**4. Running the Servers:**
- **REST API Server**: The REST server is built with FastAPI. Refer to the `server/README.md` for instructions on running it, typically via Docker.
- **MCP Server**: The MCP server can be run directly with `uv` for local development:
  ```bash
  cd mcp_server
  uv run graphiti_mcp_server.py
  ```
  It can also be run via Docker Compose as described below.

### Docker-Based Deployment

The `docker-compose.yml` file orchestrates the main application (`graph`) and the Neo4j database.

**1. Environment Setup:**
Create a `.env` file in the root directory and populate it with your credentials. You can start by copying the example file:
```bash
cp .env.example .env
```
Edit the `.env` file to add your `OPENAI_API_KEY` and any other necessary credentials.

**2. Running the Services:**
- To start the REST API server and the Neo4j database:
  ```bash
  docker-compose up
  ```
- To start the MCP server, navigate to the `mcp_server` directory and run:
  ```bash
  docker compose up
  ```

The REST API will be available at `http://localhost:8000`, and the Neo4j browser at `http://localhost:7474`.

## Development Conventions

- **Code Style:** The project uses `ruff` for linting and formatting. The configuration is in `pyproject.toml`. Adhere to the existing style (e.g., single quotes, 100-char line length).
- **Type Checking:** `pyright` is used for static type checking. All new code should be fully type-hinted.
- **Testing:** Tests are written using `pytest` and are located in the `/tests` directory. New features and bug fixes should be accompanied by corresponding tests.
- **Dependencies:** Project dependencies are managed with `poetry` and `uv`. Use `uv sync --extra dev` to keep your environment up-to-date.
- **Commits and Contributions:** Follow the guidelines in `CONTRIBUTING.md`. The project uses a standard PR-based contribution workflow.
- **Telemetry**: The project collects anonymous usage data to guide development. It can be disabled by setting the `GRAPHITI_TELEMETRY_ENABLED=false` environment variable.
