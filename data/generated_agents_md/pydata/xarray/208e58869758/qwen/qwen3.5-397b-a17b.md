# AGENTS.md

This file provides context for AI agents to understand and interact with the `xarray` project.

## Project Overview

**xarray** is a Python library for working with labeled multi-dimensional arrays and datasets. It is built on top of NumPy and integrates with other scientific Python libraries like pandas and Dask. The project's main goal is to provide a more intuitive and powerful way to work with N-dimensional data by leveraging labels (dimensions, coordinates, and attributes).

**Key Technologies:**

*   **Language:** Python
*   **Core Dependencies:** NumPy, pandas, Dask
*   **Packaging:** setuptools, setuptools-scm
*   **Testing:** pytest, coverage.py
*   **Linting/Formatting:** black, flake8, isort, mypy
*   **Documentation:** Sphinx, nbsphinx

## Building and Running

### Installation

To install the project for development, including all dependencies, run the following command from the root of the repository:

```bash
pip install -e .[complete]
```

### Running Tests

Tests are located in the `xarray/tests` directory and can be run using `pytest`:

```bash
pytest xarray/tests
```

### Building Documentation

The documentation is built using Sphinx. To build the documentation, navigate to the `doc` directory and run:

```bash
make html
```

## Development Conventions

### Code Style

*   The project uses `black` for code formatting, `isort` for import sorting, and `flake8` for linting.
*   Pre-commit hooks are configured in `.pre-commit-config.yaml` to enforce these standards automatically before each commit.

### Testing

*   All new features should be accompanied by tests.
*   Tests should be written using `pytest`.
*   The project aims for high test coverage, which is tracked using `codecov`.

### Contribution Guidelines

*   The contribution guidelines are available in the online documentation, which can be found in the `CONTRIBUTING.md` file.
*   Pull requests are the primary mechanism for contributing to the project.
*   All pull requests must pass the CI checks, which include running tests and linters.
