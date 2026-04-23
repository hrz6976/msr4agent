# GEMINI.md

## Project Overview

This project, `ragas`, is a Python-based evaluation framework for Retrieval-Augmented Generation (RAG) and Large Language Model (LLM) applications. Its purpose is to provide objective metrics and tools to assess and improve the performance of LLM-powered systems.

The project is structured as a standard Python package with its source code in the `src/ragas` directory. It uses `pyproject.toml` for dependency management and packaging with `setuptools`.

**Key Technologies:**

*   **Language:** Python (3.9+)
*   **Core Libraries:** `numpy`, `pydantic`, `datasets`, `langchain`, `openai`, `tiktoken`
*   **Development Tools:**
    *   `uv`: For environment and dependency management.
    *   `ruff`: For code formatting and linting.
    *   `pyright`: For static type checking.
    *   `pytest`: For testing.
    *   `mkdocs`: For documentation.

## Building and Running

The project uses a `Makefile` to simplify common development tasks. A virtual environment is expected, preferably managed by `uv`.

### Installation

1.  **Set up the virtual environment:**
    ```bash
    make setup-venv
    ```
2.  **Install dependencies:**
    *   For a minimal development setup (faster):
        ```bash
        make install-minimal
        ```
    *   For a full development setup with all optional features:
        ```bash
        make install
        ```

### Running Tests

*   **Run unit tests:**
    ```bash
    make test
    ```
*   **Run all tests, including notebooks:**
    ```bash
    make test-all
    ```
*   **Run end-to-end tests:**
    ```bash
    make test-e2e
    ```

### Running the Application

The project provides a command-line interface (CLI).

*   **Access the CLI:**
    ```bash
    ragas --help
    ```
*   **Quickstart a new evaluation project:**
    ```bash
    ragas quickstart rag_eval -o ./my-project
    ```

### Building Documentation

*   **Build the documentation site:**
    ```bash
    make build-docs
    ```
*   **Serve the documentation locally for development:**
    ```bash
    make serve-docs
    ```

## Development Conventions

### Code Style

*   The project uses `ruff` for both formatting and linting to enforce a consistent code style.
*   Formatting can be applied automatically by running:
    ```bash
    make format
    ```
*   A pre-commit hook is set up to run format checks automatically on commit.

### Type Checking

*   Static type checking is performed using `pyright`.
*   To run the type checker:
    ```bash
    make type
    ```

### Continuous Integration (CI)

*   The project has a CI pipeline that validates code quality and runs tests.
*   To run the full CI pipeline locally, which includes formatting checks, type checks, and tests:
    ```bash
    make run-ci
    ```
