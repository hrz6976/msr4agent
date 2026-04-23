# Astropy Project

## Project Overview

Astropy is a community effort to develop a single core package for Astronomy in Python and foster interoperability between Python astronomy packages. It provides much of the core functionality and common tools needed for performing astronomy and astrophysics with Python.

**Technologies:** Python, Cython, Numpy, Scipy

**Architecture:** The project is a Python package with a focus on modularity and interoperability. It includes sub-packages for various astronomical functionalities like coordinates, units, tables, WCS, etc. It also includes a C extension for performance-critical parts.

## Building and Running

**Installation:**

To install the latest stable version of Astropy, use pip:

```bash
pip install astropy
```

To install the development version, you can clone the repository and install it in editable mode:

```bash
git clone https://github.com/astropy/astropy.git
cd astropy
pip install -e .
```

**Testing:**

The project uses `tox` for testing. To run the tests, you can use the following command:

```bash
tox -e test
```

This will run the tests in a virtual environment with the specified dependencies. There are many other test environments defined in `tox.ini` for different Python versions, dependencies, and configurations. You can see a list of available environments by running:

```bash
tox -l -v
```

**Building Documentation:**

The documentation is built using Sphinx. To build the documentation, you can use the following command:

```bash
tox -e build_docs
```

The built documentation will be in `docs/_build/html`.

## Development Conventions

**Coding Style:**

The project uses `black` for code formatting and `isort` for import sorting. The code style is checked using `flake8` and `pycodestyle`. You can run the style checks with the following command:

```bash
tox -e codestyle
```

**Contribution Guidelines:**

Contributions are made via pull requests on GitHub. The `CONTRIBUTING.md` file provides a detailed guide on how to contribute to the project. Key points include:

-   Follow the coding guidelines.
-   Include tests for new code.
-   Include documentation for new features.
-   Add a changelog entry for user-visible changes.

**Continuous Integration:**

The project uses GitHub Actions and CircleCI for continuous integration. The CI pipelines run tests, build documentation, and check code style.
