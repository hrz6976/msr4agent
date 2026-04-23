# GEMINI.md

## Project Overview

This is the repository for **Seaborn**, a popular Python library for creating statistical data visualizations. It is built on top of Matplotlib and is tightly integrated with the PyData stack, including support for numpy and pandas data structures. The project's source code is located in the `seaborn/` directory.

The library is designed to provide a high-level interface for drawing attractive and informative statistical graphics.

## Building and Running

The project uses `flit` for building and packaging. Core dependencies include `numpy`, `pandas`, and `matplotlib`.

### Installation

To install the package for development, you can use pip with the editable flag:

```bash
pip install -e .[dev,stats,docs]
```

### Key Commands

The `Makefile` provides several useful commands for development:

*   **Running Tests:**
    To run the full test suite and generate a coverage report, use:
    ```bash
    make test
    ```
    This command uses `pytest` to discover and run the tests located in the `tests/` directory.

*   **Linting:**
    To check the code against the project's style guidelines, run:
    ```bash
    make lint
    ```
    This uses `flake8` with the configuration specified in `setup.cfg`.

*   **Type Checking:**
    To perform static type checking, use:
    ```bash
    make typecheck
    ```
    This runs `mypy` on the core modules of the library.

## Development Conventions

### Code Style

*   The project follows the **PEP 8** style guide, with a maximum line length of **88 characters**, as enforced by `flake8`.
*   `pre-commit` is used to automatically run lint checks before committing code. To set it up, run `pre-commit install`.

### Testing

*   The project uses `pytest` for unit testing.
*   Tests are located in the `tests/` directory.
*   Test coverage is configured in `setup.cfg`.

### Documentation

*   The documentation is located in the `doc/` directory.
*   Building the documentation locally requires additional dependencies, which can be installed with the `docs` extra (`pip install .[docs]`).
*   Instructions for building the documentation can be found in `doc/README.md`.
