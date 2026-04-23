# Gemini Project Context: pytest

## Project Overview

This is the source code for `pytest`, a mature and popular testing framework for Python. It allows for writing simple, scalable tests from small unit tests to complex functional testing. The project is written in Python and is highly extensible through a rich plugin ecosystem.

The source code is located in the `src/_pytest` directory. The project's own tests are in the `testing` directory.

## Building and Running

The project uses `tox` as the primary tool for managing test environments and running checks. `setuptools` is used for building and packaging.

### Key Commands:

*   **Running tests:**
    *   To run the core test suite and linting checks, use:
        ```bash
        tox -e linting,py37
        ```
    *   To run the full test suite against all configured Python versions and environments:
        ```bash
        tox
        ```
    *   For faster, iterative development, you can install `pytest` in an editable mode and run tests directly:
        ```bash
        pip install -e ".[testing]"
        pytest testing/
        ```

*   **Building documentation:**
    *   The documentation is built using Sphinx. To build it locally, run:
        ```bash
        tox -e docs
        ```
    *   The output will be in `doc/en/_build/html`.

*   **Linting and Formatting:**
    *   The project uses `pre-commit` to manage a suite of linters and formatters. To run them:
        ```bash
        pre-commit run --all-files
        ```

## Development Conventions

*   **Code Style:** The project uses `black` for code formatting and `flake8` for linting. These are enforced via `pre-commit` hooks.
*   **Contribution Guidelines:** Contributions are made via pull requests to the [GitHub repository](https://github.com/pytest-dev/pytest). The `CONTRIBUTING.rst` file contains detailed information on the contribution process, including how to report bugs, submit features, and prepare pull requests.
*   **Testing:** Tests for `pytest` itself are written using `pytest`. The `testing/` directory contains a large suite of tests. New tests should be added to the appropriate module within this directory. The `pytester` fixture is a key tool for writing tests for `pytest`'s own functionality.
*   **Changelog:** The project uses `towncrier` to manage the changelog. When making a change that requires a changelog entry, create a file in the `changelog/` directory with the format `<issueid>.<type>.rst`.
