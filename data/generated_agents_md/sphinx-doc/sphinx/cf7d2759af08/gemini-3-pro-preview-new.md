# Project Overview

This project is Sphinx, a documentation generator written in Python. It uses reStructuredText as its markup language. Sphinx can generate output in various formats, including HTML, PDF, and ePub.

**Key Technologies:**

*   Python
*   reStructuredText
*   Jinja2
*   Pygments

**Architecture:**

The project is structured as a standard Python package with a `sphinx` directory containing the source code. It uses `flit` for packaging and `tox` for testing. The documentation is located in the `doc` directory.

# Building and Running

**Building the package:**

To build the project, run:

```bash
make build
```

This will create a `dist` directory with the wheel and source distribution.

**Running tests:**

To run the tests, you can use `tox` or `make`:

Using `tox`:

```bash
tox
```

This will run the tests in different Python environments.

Using `make`:

```bash
make test
```

This will run the tests using `pytest`.

To run the JavaScript tests:

```bash
npm test
```

**Building the documentation:**

To build the documentation, run:

```bash
make docs target=html
```

Replace `html` with the desired output format.

# Development Conventions

**Coding Style:**

The project uses `flake8` and `ruff` for linting and `isort` for sorting imports. The configuration can be found in `.flake8` and `pyproject.toml`.

**Testing:**

The project uses `pytest` for Python tests and `karma` with `jasmine` for JavaScript tests. The test files are located in the `tests` directory.

**Contributing:**

The `CONTRIBUTING.rst` file provides information on how to contribute to the project.
