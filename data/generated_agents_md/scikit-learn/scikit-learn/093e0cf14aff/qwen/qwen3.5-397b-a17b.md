# AGENTS.md

This file provides a summary of the scikit-learn project for agents.

## Project Overview

Scikit-learn is a Python module for machine learning built on top of SciPy. It is a community-driven project and is distributed under the 3-Clause BSD license.

The main source code is located in the `sklearn` directory. The project uses `Cython` to build performance-critical parts of the library.

## Building and Running

### Dependencies

The project's build and runtime dependencies are listed in `pyproject.toml`. The main dependencies are:

*   Python (>= 3.8)
*   NumPy (>= 1.17.3)
*   SciPy (>= 1.5.0)
*   joblib (>= 1.1.1)
*   threadpoolctl (>= 2.0.0)

Development dependencies are listed in `doc/developers/contributing.rst` and include `pytest`, `ruff`, `black`, and `mypy`.

### Building the project

To build the project, you can use the `Makefile`:

```bash
# Build the project in-place
make inplace
```

Alternatively, you can build using `pip` in editable mode:

```bash
pip install -v --no-use-pep517 --no-build-isolation -e .
```

### Running Tests

The tests are located in the `sklearn` directory, mostly in `tests` subdirectories. To run the tests, use `pytest`:

```bash
pytest sklearn
```

The `Makefile` provides several testing targets:

```bash
# Run all tests
make test

# Run tests in parallel
make test-code-parallel

# Run tests with coverage
make test-coverage
```

## Development Conventions

### Code Style

The project uses `black` for code formatting and `ruff` for linting. The configuration for these tools can be found in `pyproject.toml`.

It is recommended to use `pre-commit` to automatically run these checks before each commit. To set it up:

```bash
pip install pre-commit
pre-commit install
```

### Contribution Guidelines

The contribution guidelines are detailed in `doc/developers/contributing.rst`. Key points include:

*   Fork the repository and create a feature branch for your changes.
*   Write tests for new features and bug fixes.
*   Follow the code style guidelines.
*   Ensure the documentation is updated and renders correctly.
*   Submit a pull request with a clear title and description.

Pull requests should be prefixed with `[MRG]` when ready for review, and `[WIP]` if they are a work in progress.
