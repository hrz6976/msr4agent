# AGENTS.md

This file provides instructional context for interacting with the `ragas` project.

## Project Overview

`ragas` is a Python-based evaluation framework for Retrieval-Augmented Generation (RAG) and other Large Language Model (LLM) applications. It provides tools to assess the quality of LLM responses, generate test data, and integrate with popular LLM frameworks.

**Key Technologies:**

- **Programming Language:** Python 3.9+
- **Dependency Management:** `uv` and `pip`
- **Formatting and Linting:** `ruff`
- **Type Checking:** `pyright`
- **Testing:** `pytest`
- **Command-Line Interface:** `typer`
- **Documentation:** `mkdocs`

## Building and Running

### Setup

1.  **Create a virtual environment:**
    ```bash
    make setup-venv
    ```
2.  **Install minimal dependencies:**
    ```bash
    make install-minimal
    ```
3.  **Install all dependencies:**
    ```bash
    make install
    ```

### Running Tests

-   **Run all unit tests:**
    ```bash
    make test
    ```
-   **Run all unit tests (including notebooks):**
    ```bash
    make test-all
    ```
-   **Run end-to-end tests:**
    ```bash
    make test-e2e
    ```

### Code Quality

-   **Format and lint all code:**
    ```bash
    make format
    ```
-   **Type check all code:**
    ```bash
    make type
    ```
-   **Run a quick health check (format + type):**
    ```bash
    make check
    ```

### Documentation

-   **Build the documentation:**
    ```bash
    make build-docs
    ```
-   **Serve the documentation locally:**
    ```bash
    make serve-docs
    ```

## Development Conventions

-   The project uses `ruff` for code formatting and linting.
-   Type checking is enforced using `pyright`.
-   Tests are written using `pytest` and are located in the `tests/` directory.
-   The project follows the contribution guidelines outlined in `CONTRIBUTING.md`.

## Command-Line Interface (CLI)

The `ragas` CLI provides the following commands:

-   `ragas quickstart`: Clones a complete example project to get started with `ragas`.
    -   `ragas quickstart`: Lists available templates.
    -   `ragas quickstart [template_name]`: Creates a project from a template.
-   `ragas evals`: Runs evaluations on a dataset.
    -   `ragas evals [eval_file] --dataset [dataset_name] --metrics [metrics_list]`: Runs an evaluation with the specified parameters.

For more details on the CLI commands, refer to the source code in `src/ragas/cli.py`.
