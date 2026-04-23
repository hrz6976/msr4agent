# AGENTS.md

## Project Overview

This project is the Sphinx documentation generator, a tool for creating intelligent and beautiful documentation from reStructuredText sources. It's a mature and widely used Python project.

The main technologies used are:
- **Python**: The core language of the project.
- **reStructuredText**: The markup language for documentation.
- **Jinja2**: For templating HTML output.
- **Pygments**: for code highlighting.
- **Flit**: For building and packaging the project.
- **Tox**: For managing test environments.
- **Pytest**: The testing framework.
- **MyPy**: For type checking.
- **flake8** and **ruff**: For code style and linting.

The project is structured as a standard Python library with the main source code in the `sphinx` directory.

## Building and Running

### Dependencies

To install the dependencies for development, including for tests, linting and documentation, run:

```bash
pip install -e .[test,lint,docs]
```

### Building the Documentation

To build the HTML documentation:

```bash
make docs target=html
```

Or using tox:

```bash
tox -e docs
```

The output will be in `doc/_build/html`.

### Running Tests

To run the full test suite against the current python environment:

```bash
make test
```

Or using `pytest` directly:

```bash
pytest
```

To run tests in all supported Python versions using `tox`:

```bash
tox
```

### Linting and Style Checking

To check the code style with `flake8`:

```bash
make style-check
```

To run `mypy` for type checking:
```bash
make type-check
```

## Development Conventions

- **Code Style**: The project uses `flake8` and `ruff` for linting, with configurations defined in `.flake8` and `pyproject.toml`.
- **Testing**: Tests are located in the `tests` directory and are written using `pytest`. The project aims for high test coverage.
- **Commits**: There is no explicit commit message convention found in the documentation, but following standard practices is recommended.
- **Contributions**: The `CONTRIBUTING.rst` file provides guidelines for contributing to the project. It's important to read it before making any changes.
