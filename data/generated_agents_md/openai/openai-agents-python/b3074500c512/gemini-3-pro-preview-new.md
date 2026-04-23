# GEMINI.md

## Project Overview

This project is the OpenAI Agents SDK for Python, a lightweight framework for building multi-agent workflows. It is provider-agnostic, supporting the OpenAI Responses and Chat Completions APIs, as well as 100+ other LLMs. The core concepts include Agents, Handoffs, Guardrails, Sessions, and Tracing.

The main technologies used are Python 3.9+, with dependencies such as `openai`, `pydantic`, `griffe`, and `typing-extensions`. The project uses `uv` for environment and package management and `ruff` for linting and formatting.

## Building and Running

### Setup

1.  **Install `uv`:** Ensure you have `uv` installed.
2.  **Install dependencies:**
    ```bash
    make sync
    ```

### Running Tests

```bash
make tests
```

### Linting and Formatting

*   **Check formatting:**
    ```bash
    make format-check
    ```
*   **Format code:**
    ```bash
    make format
    ```
*   **Run linter:**
    ```bash
    make lint
    ```
*   **Run typechecker:**
    ```bash
    make mypy
    ```
*   **Run all checks:**
    ```bash
    make check
    ```

### Documentation

*   **Build docs:**
    ```bash
    make build-docs
    ```
*   **Serve docs locally:**
    ```bash
    make serve-docs
    ```

## Development Conventions

*   **Coding Style:** The project uses `ruff` for formatting and linting. The configuration can be found in `pyproject.toml`.
*   **Testing:** Tests are written using `pytest`. Test files are located in the `tests/` directory.
*   **Type Checking:** The project uses `mypy` for static type checking.
*   **Contributions:** The `README.md` mentions that the project is open source and encourages community contributions.
