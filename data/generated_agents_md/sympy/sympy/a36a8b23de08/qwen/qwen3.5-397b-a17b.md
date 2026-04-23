# AGENTS.md

This file provides instructional context for AI agents interacting with the SymPy project.

## Project Overview

SymPy is a Python library for symbolic mathematics. It aims to become a full-featured computer algebra system (CAS) while keeping the code as simple as possible in order to be comprehensible and easily extensible. SymPy is written entirely in Python.

**Key Technologies:**

*   **Language:** Python 3.8+
*   **Core Dependency:** [mpmath](http://mpmath.org/)
*   **Build & Packaging:** `setuptools`
*   **Code Quality:** `ruff`, `flake8` (linting), `mypy` (type checking)
*   **Parsing:** ANTLR is used for generating parsers (e.g., for LaTeX).

**Architecture:**

*   The main source code is located in the `sympy/` directory.
*   The project is divided into modules based on functionality (e.g., `sympy.core`, `sympy.calculus`, `sympy.plotting`).
*   Tests are located within each module's `tests` subdirectory (e.g., `sympy.core.tests`).

## Building and Running

### Installation

The recommended way to install SymPy is using `pip`:

```bash
pip install .
```

### Running Tests

To run the complete test suite, use the following command:

```bash
python setup.py test
```

For more granular control over testing, the `bin/test` and `bin/doctest` scripts can be used.

### Building Documentation

The documentation can be generated locally:

```bash
cd doc
make html
```

The output will be in `doc/_build/html`.

### ANTLR Parser Generation

The project uses ANTLR to generate parsers. To regenerate the parser code after modifying a `.g4` grammar file, run:

```bash
python setup.py antlr
```

## Development Conventions

*   **Code Style:** The project uses `ruff` and `flake8` for code linting. Configuration can be found in `pyproject.toml` and `setup.cfg`. The general style follows standard Python conventions (PEP 8), with a line length of 88 characters.
*   **Type Checking:** The project uses `mypy` for static type checking. Configurations are in `setup.cfg`.
*   **Testing:** All new code should be accompanied by tests. The project uses a combination of unit tests and doctests.
*   **Contributions:** Contributions are welcome. The project has a detailed guide for new contributors in the GitHub wiki and expects participants to follow its [Code of Conduct](CODE_OF_CONDUCT.md).
*   **Branching and PRs:** Pull Requests should be made from forks into the main SymPy repository.
