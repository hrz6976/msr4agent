# GEMINI.md: xarray

## Project Overview

xarray is a Python library for working with labeled multi-dimensional arrays. It provides a high-level interface for N-dimensional arrays, inspired by the pandas library. It's particularly useful for scientific and engineering datasets that have dimensions, coordinates, and attributes.

**Key Technologies:**

*   **Core:** Python, NumPy, pandas
*   **Parallel Computing:** Dask
*   **Build:** setuptools
*   **Testing:** pytest
*   **Linting/Formatting:** flake8, isort, mypy

## Building and Running

The project is a Python library and can be installed from PyPI. To install for development, you can clone the repository and install it in editable mode:

```bash
git clone https://github.com/pydata/xarray.git
cd xarray
pip install -e .
```

To install all optional dependencies for a complete development environment, you can use the following command:

```bash
pip install -e ".[complete]"
```

To run the tests, use `pytest`:

```bash
pytest
```

## Development Conventions

*   **Testing:** Tests are written using `pytest` and are located in the `xarray/tests` and `properties` directories.
*   **Code Style:** The project uses `black` for code formatting, `isort` for import sorting, and `flake8` for linting.
*   **Type Hinting:** The project uses `mypy` for static type checking.
*   **Contributions:** Contribution guidelines are available in the online documentation.
