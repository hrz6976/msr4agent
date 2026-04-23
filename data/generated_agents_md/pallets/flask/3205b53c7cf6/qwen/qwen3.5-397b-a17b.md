# Flask Project AGENTS.md

This document provides an overview of the Flask project, its structure, and development guidelines for agents interacting with this codebase.

## Project Overview

Flask is a lightweight WSGI web application framework in Python. It's designed to be simple and easy to get started with, while also being scalable for complex applications. The project uses a standard Python project structure, with source code in the `src` directory, tests in the `tests` directory, and documentation in the `docs` directory.

The project's main dependencies are:
*   Werkzeug
*   Jinja2
*   ItsDangerous
*   Click
*   Blinker

## Building and Running

### Development Environment

To set up a local development environment, follow these steps:

1.  Create and activate a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2.  Install development dependencies:
    ```bash
    pip install -r requirements/dev.txt
    ```
3.  Install Flask in editable mode:
    ```bash
    pip install -e .
    ```

### Running Tests

The test suite can be run using `pytest`:
```bash
pytest
```
To run the full test suite for all supported Python versions, use `tox`:
```bash
tox
```

### Building Documentation

The documentation is built using Sphinx.
```bash
cd docs
make html
```

## Development Conventions

*   **Code Style:** The project uses Black for code formatting. This is enforced by a pre-commit hook.
*   **Testing:** All code changes should be accompanied by tests. The test suite is written using `pytest`.
*   **Commits:** Commits should be clear and descriptive. Pull requests should reference the issue they are addressing.
*   **Docstrings:** Docstrings should be wrapped at 72 characters.
*   **Changelog:** Add an entry in `CHANGES.rst` for any user-facing changes.
