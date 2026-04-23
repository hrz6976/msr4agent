# GEMINI.md

## Project Overview

This directory contains the source code for **scikit-learn**, a popular open-source machine learning library for Python. It is built on top of other scientific computing libraries like NumPy and SciPy.

The project is written in Python, with some performance-critical parts implemented in Cython. The directory structure includes the main library code under `sklearn/`, documentation in `doc/`, examples in `examples/`, and benchmarks in `asv_benchmarks/` and `benchmarks/`.

## Building and Running

### Dependencies

The main dependencies are listed in `pyproject.toml` and `README.rst` and include:

*   Python (>= 3.8)
*   NumPy
*   SciPy
*   joblib
*   threadpoolctl
*   Cython

### Installation

To install the package for development, you can build it in-place. The `Makefile` provides a helper for this:

```bash
make inplace
```

This will compile the Cython extensions and make the package available for import in your environment.

### Testing

The project uses `pytest` for testing. You can run the test suite using the `Makefile`:

```bash
make test
```

This command will run all tests, including code tests, documentation tests, and tests for the Sphinx extensions.

To run tests in parallel, you can use:

```bash
make test-code-parallel
```

### Building Documentation

The documentation is built using Sphinx. You can build the HTML documentation with the following command:

```bash
make doc
```

## Development Conventions

### Code Style

*   The project uses **black** for code formatting. Configuration for `black` is in `pyproject.toml`.
*   **ruff** is used for linting, and its configuration is also in `pyproject.toml`.

### Contributing

*   The `CONTRIBUTING.md` file provides a high-level overview of how to contribute.
*   Detailed contribution guidelines, including coding standards, are available in the `doc/developers/contributing.rst` file and on the project's website.
*   Pull requests are submitted through GitHub.

### Makefile Targets

The `Makefile` provides several useful targets for development:

*   `clean`: Removes build artifacts.
*   `inplace` or `in`: Builds the project in-place for development.
*   `test`: Runs the full test suite.
*   `test-code`: Runs only the Python code tests.
*   `test-coverage`: Runs tests and generates a coverage report.
*   `doc`: Builds the documentation.
*   `code-analysis`: Runs linting and other code checks.
