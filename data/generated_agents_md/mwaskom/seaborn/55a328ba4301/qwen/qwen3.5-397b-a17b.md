# Seaborn Project: Agent Instructions

This document provides instructions for interacting with the Seaborn project, a Python statistical data visualization library.

## Project Overview

Seaborn is a Python library for creating attractive and informative statistical graphics. It is built on top of Matplotlib and integrates closely with pandas data structures.

- **Purpose**: Statistical data visualization.
- **Technologies**: Python, Matplotlib, Pandas, NumPy, SciPy, Statsmodels.
- **Architecture**: A library of modules that can be imported and used in Python scripts and notebooks. The main logic is in the `seaborn/` directory.

## Building and Running

### Dependencies

The project's dependencies are managed using `flit` and are defined in `pyproject.toml`.

- **Core Dependencies**: `numpy`, `pandas`, `matplotlib`.
- **Optional Dependencies**:
  - `stats`: `scipy`, `statsmodels` (for advanced statistical functionality).
  - `dev`: `pytest`, `pytest-cov`, `flake8`, `mypy` (for development and testing).
  - `docs`: `sphinx`, `numpydoc` (for building documentation).

To install the core dependencies, run:
```bash
pip install .
```

To install optional dependencies for development, run:
```bash
pip install .[dev]
```

### Commands

The following commands are available in the `Makefile`:

- **`make test`**: Run the test suite using `pytest`.
- **`make lint`**: Check the code for style issues using `flake8`.
- **`make typecheck`**: Run static type checking using `mypy`.

## Development Conventions

- **Testing**: The project uses `pytest` for unit testing. Tests are located in the `tests/` directory. Test coverage is measured using `coverage.py`.
- **Linting**: Code style is enforced with `flake8`. The configuration is in `setup.cfg`.
- **Type Checking**: The project uses `mypy` for static type checking.
- **Pre-commit Hooks**: The project uses `pre-commit` to automatically run lint checks before committing. The configuration is in `.pre-commit-config.yaml`.
- **Documentation**: The documentation is built using Sphinx and is located in the `doc/` directory.

## Key Files

- **`pyproject.toml`**: Defines the project's metadata, dependencies, and build system.
- **`setup.cfg`**: Contains configuration for `flake8`, `mypy`, and `coverage`.
- **`Makefile`**: Defines commands for testing, linting, and type checking.
- **`seaborn/`**: The main source code for the library.
- **`tests/`**: Unit tests for the library.
- **`doc/`**: Documentation for the library.
- **`examples/`**: Example scripts and notebooks.
