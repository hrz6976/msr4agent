# Project Overview

This project, `fastmcp`, is a Python framework for building servers and clients for the Model Context Protocol (MCP). It aims to be a production-ready solution, extending the official MCP SDK with features like enterprise authentication, deployment tools, and advanced server patterns. The framework is built to be fast, simple, and Pythonic, allowing developers to create MCP servers with minimal boilerplate code.

The core technologies used are:
- **Python 3.10+**
- **MCP (Model Context Protocol)**: The underlying standard for communication.
- **`cyclopts`**: For building the command-line interface.
- **`httpx`**: For HTTP communication.
- **`pydantic`**: For data validation and settings management.
- **`uvicorn`**: For serving the application over HTTP/SSE.
- **`pytest`**: For running tests.
- **`ruff`** and **`prek`**: For code linting and formatting.
- **`just`**: As a command runner for development tasks.
- **`uv`**: For environment and dependency management.

## Building and Running

The project uses `just` as a command runner to simplify common development tasks.

### Installation

To set up the development environment and install all necessary dependencies, run:
```bash
just build
```
This command executes `uv sync`.

### Running the Server

The primary way to run an MCP server is using the `fastmcp run` command. For a simple server defined in `server.py`:
```bash
fastmcp run server.py
```
For development, you can use the `dev` command to run the server with the MCP Inspector:
```bash
fastmcp dev server.py
```

### Running Tests

The project has a comprehensive test suite using `pytest`. To run the tests:
```bash
just test
```

### Static Analysis and Formatting

The project uses `prek`, which integrates `ruff`, for static analysis and code formatting. These checks are configured to run automatically on commit via pre-commit hooks. To run them manually:
```bash
prek run --all-files
```
To run type checking with `ty`:
```bash
just typecheck
```

### Documentation

The documentation can be served locally with the following command:
```bash
just docs
```
This will start a local server to view the documentation.

## Development Conventions

- **Dependencies**: Managed with `uv` and defined in `pyproject.toml`.
- **Testing**: Tests are located in the `tests/` directory and run with `pytest`. New contributions should include corresponding tests.
- **Code Style**: The project uses `ruff` for linting and `prek` for formatting, with rules defined in `pyproject.toml`. Pre-commit hooks are used to enforce these standards.
- **Command Runner**: A `justfile` is provided with convenient commands for building, testing, and other development tasks.
- **CLI**: The command-line interface is built with `cyclopts` and is the main entry point for interacting with the framework.
- **Contributions**: The `README.md` provides clear guidelines for contributing, including setting up the environment, running tests, and submitting pull requests.
