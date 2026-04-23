# AGENTS.md

This file provides instructional context about the `psf/requests` project for AI agents.

## Project Overview

The `requests` library is a simple, yet elegant, HTTP library for Python. It allows developers to send HTTP/1.1 requests easily, abstracting away the complexities of making HTTP requests. It is one of the most downloaded Python packages and is a dependency for many other projects.

**Key Technologies:**

*   **Language:** Python
*   **Testing:** `pytest` is used for testing, with `tox` for running tests in different Python environments.
*   **Dependencies:** `urllib3`, `charset_normalizer` (for Python 3), `chardet` (for Python 2), `idna`, and `certifi`.
*   **Documentation:** Sphinx is used for generating documentation.

## Building and Running

### Development Setup

To set up the development environment, install the project in editable mode and the development dependencies:

```bash
pip install -e .[socks]
pip install -r requirements-dev.txt
```

### Running Tests

Tests are run using `tox` to test against multiple Python versions, or `pytest` directly.

*   **Using tox (recommended):**
    ```bash
    tox -p
    ```
*   **Using pytest:**
    ```bash
    pytest tests
    ```
*   **To run tests with coverage:**
    ```bash
    pytest --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=requests tests
    ```

### Building Documentation

The documentation is built using Sphinx:

```bash
cd docs && make html
```

The output will be in `docs/_build/html/index.html`.

### Building the Project

To build the project for distribution (sdist and wheel):

```bash
python setup.py sdist bdist_wheel
```

## Development Conventions

*   **Coding Style:** The project follows standard Python coding conventions. The `flake8` tool is used for linting.
    ```bash
    flake8 --ignore=E501,F401,E128,E402,E731,F821 requests
    ```
*   **Testing:**
    *   Tests are located in the `tests/` directory.
    *   `pytest` is the test runner.
    *   `pytest-httpbin` is used for HTTP testing.
    *   Code coverage is configured via `.coveragerc`, which omits `requests/packages/*` from the report.
    *   Docstrings are tested, as configured in `pytest.ini`.
*   **Commits and Pull Requests:** (Inferred from general open-source best practices)
    *   Commits should be atomic and have clear messages.
    *   Pull requests should be focused and address a single issue or feature.
    *   All tests must pass before a PR is merged.
