# Project Overview

This directory contains the source code for SymPy, a Python library for symbolic mathematics. SymPy is a pure Python library that provides a comprehensive set of tools for symbolic computation, including algebra, calculus, and more. The project is open source and has a large community of contributors.

## Building and Running

### Dependencies

The project's development dependencies are listed in the `requirements-dev.txt` file. The main dependency is `mpmath`, a library for arbitrary-precision floating-point arithmetic. Other dependencies include `pytest` for testing and `flake8` for linting.

### Building

To install SymPy from the source, run the following command in the root directory:

```bash
pip install .
```

### Running

SymPy can be used as a library in any Python script. To use SymPy, import the necessary functions and classes from the `sympy` package. For example:

```python
from sympy import Symbol, cos

x = Symbol('x')
e = 1/cos(x)
print(e.series(x, 0, 10))
```

SymPy also comes with an interactive shell called `isympy`, which is a wrapper around the classic Python console (or IPython when available) that loads the SymPy namespace and executes some common commands for you. To start it, run:

```bash
bin/isympy
```

### Testing

The project uses `pytest` for testing. To run the tests, execute the following command in the root directory:

```bash
./setup.py test
```

The tests are located in the `sympy/` and `doc/src` directories.

## Development Conventions

### Code Style

The project uses `flake8` for linting and `ruff` for code formatting. The configuration for these tools can be found in the `pyproject.toml` and `setup.cfg` files. The code style is based on the Black code formatter with a line length of 88 characters.

### Contribution Guidelines

The project welcomes contributions from anyone. The contribution guidelines are detailed in the project's wiki, which can be found in the `CONTRIBUTING.md` file. The wiki provides information on how to get started with contributing, including how to find easy-to-fix issues.
