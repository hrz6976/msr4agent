# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SymPy is a Python library for symbolic mathematics, aiming to be a full-featured computer algebra system (CAS). It is written entirely in Python and depends on mpmath (version >= 1.1.0, < 1.4.0). The project requires Python 3.8+.

## Essential Commands

### Running Tests

```bash
# Run all tests
./setup.py test

# Run tests with bin/test (more fine-grained control)
bin/test [options] [tests]

# Run specific test file
bin/test sympy/core/tests/test_basic.py

# Run specific test function
bin/test sympy/core/tests/test_basic.py::test_function_name

# Use pytest directly (installed via requirements-dev.txt)
pytest sympy/

# Run with quick filters (skip very slow tests)
pytest --quickcheck

# Run with very quick filters (skip slow and very slow tests)
pytest --veryquickcheck

# Run tests in parallel
pytest -n auto

# Run with verbose output
bin/test -v
```

### Running Doctests

```bash
# Run all doctests
bin/doctest

# Run doctests for specific file
bin/doctest sympy/core/basic.py

# Run doctests in documentation
bin/doctest doc/src/
```

### Interactive Shell

```bash
# Start SymPy interactive console (loads SymPy namespace)
bin/isympy

# Or if SymPy is installed
isympy
```

### Building Documentation

```bash
cd doc
make html
# Documentation will be in doc/_build/html/
```

### Linting

```bash
# Run ruff linter (configured in pyproject.toml)
ruff check .

# Run flake8 (dev dependency)
flake8
```

### Installation

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -r requirements-dev.txt
```

### ANTLR Parser Generation

If working on LaTeX or AutoLev parsers:

```bash
# Regenerate ANTLR parsers (requires antlr4 in PATH)
./setup.py antlr
```

## Architecture Overview

### Core Module (`sympy/core/`)

The foundation of SymPy's symbolic computation:

- **`basic.py`**: Defines `Basic`, the base class for all SymPy objects. All symbolic objects inherit from `Basic` and implement tree-like structures.
- **`expr.py`**: Defines `Expr`, the base class for algebraic expressions. Most mathematical objects are `Expr` subclasses.
- **`sympify.py`**: Contains `sympify()`, which converts Python objects to SymPy expressions. This is the entry point for most user input.
- **`symbol.py`**: Defines `Symbol`, `Wild`, `Dummy` - the fundamental symbolic variable types.
- **`numbers.py`**: Number classes (`Integer`, `Rational`, `Float`, etc.) and singletons (`S.One`, `S.Zero`, `S.Infinity`).
- **`add.py`, `mul.py`, `pow.py`**: Core algebraic operations. These use automatic evaluation and canonical ordering.
- **`function.py`**: Framework for mathematical functions and their derivatives.
- **`cache.py`**: Caching mechanisms using `@cacheit` decorator for performance.
- **`assumptions.py`**: Old assumptions system (being phased out in favor of `sympy/assumptions/`).
- **`singleton.py`**: Defines `S`, the singleton registry containing common constants.

### Key Architectural Concepts

1. **Immutability**: All SymPy objects are immutable. Operations create new objects rather than modifying existing ones.

2. **Automatic Evaluation**: Expressions are automatically simplified during creation (e.g., `Add(x, 0)` returns `x`). Use `evaluate=False` to prevent this.

3. **Tree Structure**: All expressions are tree structures where `expr.args` gives child nodes. The root is accessed via `expr.func`.

4. **Canonical Ordering**: Arguments in `Add` and `Mul` are automatically ordered canonically for comparison and hashing.

5. **Printer System** (`sympy/printing/`): Visitors that traverse expression trees to produce output in various formats (LaTeX, C, Python, etc.). Each printer subclasses a base printer and implements type-specific handlers.

6. **Assumptions System** (`sympy/assumptions/`): New three-valued logic system (True/False/None) for symbolic assumptions. Use `Q` for queries and `ask()` for inference.

### Major Subsystems

- **`sympy/polys/`**: Polynomial manipulation, GCD, factorization, Groebner bases. Critical for algebraic operations.
- **`sympy/solvers/`**: Equation solving (algebraic, differential, recurrence). Includes `solve()`, `solveset()`, and ODE solvers.
- **`sympy/simplify/`**: Expression simplification strategies (`simplify()`, `trigsimp()`, `ratsimp()`, etc.).
- **`sympy/matrices/`**: Dense and sparse matrices, matrix expressions, linear algebra.
- **`sympy/integrals/`**: Symbolic integration using heuristics and pattern matching.
- **`sympy/series/`**: Series expansions, limits, and asymptotic analysis.
- **`sympy/logic/`**: Boolean algebra, SAT solving, and logic inference.
- **`sympy/physics/`**: Physics modules (mechanics, quantum, units, etc.).
- **`sympy/parsing/`**: Parsers for LaTeX, C, Fortran, and Mathematica. ANTLR-based grammars in `_antlr/` subdirectories.

### Testing Infrastructure

- **`sympy/testing/`**: Testing utilities and the test runner framework.
- **`conftest.py`**: pytest configuration with custom hooks for slow test filtering.
- **`.ci/durations.json`**: Tracks slow and very slow tests for filtering with `--quickcheck` and `--veryquickcheck`.
- **`.ci/blacklisted.json`**: Tests temporarily disabled (skipped during CI).

Tests are in `tests/` subdirectories within each module. Doctests are embedded in docstrings and documentation.

## Development Guidelines

### Code Style

- Follow PEP 8 with some exceptions (see `pyproject.toml` for ignored rules).
- Use 4 spaces for indentation.
- Ruff and flake8 are used for linting.
- Import order: standard library, third-party, SymPy modules (use isort conventions).

### Testing Requirements

- All new functionality must include tests in the appropriate `tests/` directory.
- Doctests should demonstrate typical usage and appear in docstrings.
- Tests should be fast; mark slow tests appropriately (they may be added to `.ci/durations.json`).
- Use `pytest` conventions for test functions (`test_*` naming).

### Working with SymPy's Core

- Understand that automatic evaluation happens during object creation.
- To prevent evaluation, pass `evaluate=False` to constructors.
- Use `.args` to access expression children and `.func` to get the class.
- Test both with and without assumptions when working on assumption-dependent code.
- Many core classes implement `__new__` instead of `__init__` due to immutability.

### Common Pitfalls

- **Don't use `==` for structural comparison**: Use `.equals()` for mathematical equality or `unchanged()` in tests.
- **Hash randomization**: Tests may fail due to dict/set ordering. Sort outputs or use ordered structures in tests.
- **Caching**: When modifying cached functions, be aware that cache may persist between tests. Use `clear_cache()` if needed.
- **Ground types**: SymPy can use different backends for polynomial arithmetic (Python, gmpy, gmpy2). Tests should pass with all backends.

### Deprecation Process

- Mark deprecated features with `@deprecated` decorator (see `sympy.utilities.decorator`).
- Add deprecation warnings visible in dev builds (see `sympy/__init__.py`).
- Document in release notes and docs.
- Remove after appropriate deprecation period.

## Environment Variables

- `SYMPY_DEBUG`: Set to 'True' for debug mode.
- `SYMPY_USE_CACHE`: Set to 'no' to disable caching (useful for debugging).
- `SYMPY_GROUND_TYPES`: Set to 'gmpy', 'gmpy1', or 'python' to select polynomial arithmetic backend.

## CI and Testing Notes

- Tests run via pytest using `conftest.py` configuration.
- Slow tests are tracked in `.ci/durations.json` and can be skipped with `--quickcheck` or `--veryquickcheck`.
- The test suite is comprehensive and may take significant time to run fully; use filters for rapid iteration.
- CircleCI configuration is in `.circleci/config.yml`.

## Additional Resources

- Main documentation: https://docs.sympy.org/
- Contributing guide: https://github.com/sympy/sympy/wiki/Introduction-to-contributing
- Development documentation: `doc/src/contributing/`
- Issue tracker: https://github.com/sympy/sympy/issues
- Use the "Easy to Fix" label for newcomer-friendly issues
