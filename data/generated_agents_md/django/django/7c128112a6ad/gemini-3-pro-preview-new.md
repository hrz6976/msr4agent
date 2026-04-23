# Project Overview

This is the source code for the Django web framework, a high-level Python framework designed for rapid development and clean, pragmatic design.

**Key Technologies:**

*   **Backend:** Python
*   **Frontend:** JavaScript (for the admin interface and other components)
*   **Build & Packaging:** `setuptools`, `pyproject.toml`, `setup.py`
*   **Testing:** `tox`, `pytest` (implied via `runtests.py`), `QUnit`, `Puppeteer`
*   **Linting & Formatting:** `black`, `flake8`, `isort`, `eslint`

The project uses `tox` to manage and run tests across different Python environments and for various checks like linting and documentation builds. The JavaScript components are managed with `npm` and tested using `Grunt` and `QUnit`.

# Building and Running

## Installation

To install the development version of Django from this source code, you can use `pip`:

```bash
python -m pip install -e .
```

## Running Tests

The primary method for running the full test suite is with `tox`.

**1. Full Test Suite (Python):**

```bash
tox
```

This will run all Python tests and code quality checks in isolated environments.

**2. Specific Python Environment:**

To run tests for a specific Python version (e.g., Python 3):

```bash
tox -e py3
```

**3. JavaScript Tests:**

The project uses `npm` and `Grunt` to manage and run JavaScript tests.

```bash
npm install
npm test
```

This will first install the necessary dependencies and then run the test suite, which includes linting with ESLint and running QUnit tests.

# Development Conventions

## Code Style

*   **Python:** The project uses `black` for code formatting, `flake8` for linting, and `isort` for import ordering. These checks are integrated into the `tox` configuration.
*   **JavaScript:** `eslint` is used for linting JavaScript code.

## Contributions

*   **Trac:** All non-trivial changes require a ticket on Django's Trac instance before a pull request is made.
*   **Code of Conduct:** Contributors are expected to follow the Django Code of Conduct.
*   **Documentation:** All contributions should be well-documented. The documentation is written in reStructuredText and built using Sphinx.

## Testing

*   **Python:** The main test suite is located in the `tests/` directory and is run using a custom test runner script (`runtests.py`), orchestrated by `tox`.
*   **JavaScript:** Tests for the JavaScript components are managed via `package.json` and run with `Grunt`.
