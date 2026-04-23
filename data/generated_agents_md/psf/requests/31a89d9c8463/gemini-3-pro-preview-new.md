# Project Overview

This is the source code for the `requests` library, a simple, yet elegant, HTTP library for Python. It allows developers to send HTTP/1.1 requests easily, without needing to manually add query strings to URLs or form-encode `PUT` & `POST` data.

**Main Technologies:**

*   Python
*   `setuptools` for packaging
*   `pytest` for testing
*   `tox` for test automation across different Python versions
*   `flake8` for linting
*   `Sphinx` for documentation

**Architecture:**

The project is structured as a standard Python library. The main source code is located in the `requests/` directory. Tests are in the `tests/` directory. The project uses a `setup.py` file for packaging and distribution.

# Building and Running

**Installation:**

To install the library for development, run:

```bash
pip install -e .[socks]
pip install -r requirements-dev.txt
```

**Running Tests:**

To run the full test suite across all supported Python versions, use `tox`:

```bash
tox -p
```

To run tests for a specific environment:

```bash
pytest tests
```

To run tests with coverage:

```bash
pytest --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=requests tests
```

**Building Documentation:**

To build the documentation, run:

```bash
cd docs && make html
```

The documentation will be available in `docs/_build/html/index.html`.

# Development Conventions

*   **Linting:** The project uses `flake8` for linting. To run the linter:

    ```bash
    flake8 --ignore=E501,F401,E128,E402,E731,F821 requests
    ```

*   **Testing:** Tests are written using `pytest`. The test suite is extensive and covers a wide range of functionality.
*   **Continuous Integration:** The `ci` target in the `Makefile` suggests that the project uses a CI/CD system to run tests and generate reports.
