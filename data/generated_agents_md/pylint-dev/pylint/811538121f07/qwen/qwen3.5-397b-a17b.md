# AGENTS.md

## Project Overview

This is the source code for `pylint`, a popular static code analyzer for Python. Its purpose is to identify errors, enforce coding standards, and detect "code smells." It works by analyzing Python code without executing it.

The project is built using `setuptools` and has several key dependencies, including `astroid` for building abstract syntax trees, `isort` for import sorting, and `mccabe` for complexity checking. The configuration in `pyproject.toml` also shows the use of `pytest` for testing, `mypy` for type checking, `ruff` for linting, and `black` for code formatting.

The directory structure includes:
- `pylint/`: The main source code for the `pylint` package.
- `tests/`: Contains the test suite for the project, using `pytest`.
- `doc/`: Project documentation.
- `examples/`: Example files.

## Building and Running

### Installation

To install the project for development, you can use `pip` in editable mode:

```bash
pip install -e .
```

### Running Pylint

Once installed, you can run `pylint` on a Python file or module:

```bash
pylint path/to/your/code.py
```

The project also provides other command-line tools: `pyreverse` (for generating UML diagrams) and `symilar` (for finding duplicate code).

### Running Tests

The project uses `tox` to manage test environments. To run the default test suite:

```bash
tox
```

This will execute tests across multiple Python versions, as defined in `tox.ini`. You can also run tests for a specific environment, for example:

```bash
tox -e py311
```

To run the formatting and linting checks:

```bash
tox -e formatting
```

## Development Conventions

### Code Style

- **Formatting:** The project uses `black` for code formatting and `isort` for import sorting. These are enforced via `pre-commit` hooks. You can run these checks manually using `tox -e formatting`.
- **Linting:** `ruff` is used for linting, configured in `pyproject.toml`.
- **Typing:** The project uses type hints, and `mypy` is used for static type checking.

### Testing

- Tests are written using the `pytest` framework and are located in the `tests/` directory.
- `tox` is used to automate testing in different environments.
- Coverage is measured and can be generated in an HTML report using the `coverage-html` environment in `tox`.

### Commits and Contributions

- The project uses `pre-commit` to run checks before committing code. To set this up, run `pre-commit install`.
- Contribution guidelines are available in the documentation (`doc/development_guide/contribute.rst`).
