
# AGENTS.md

## Project Overview

This is the source code for Matplotlib, a comprehensive library for creating static, animated, and interactive visualizations in Python. Matplotlib is a large and mature project with a long history.

**Key Technologies:**

*   **Language:** Python, with some C/C++ for performance-critical parts.
*   **Build System:** `setuptools`, configured via `pyproject.toml` and `setup.cfg`.
*   **Dependencies:** `NumPy` is a core dependency. Other optional dependencies exist for different backends and features.

**Architecture:**

*   The core of Matplotlib is a powerful object-oriented API for creating plots.
*   A `pylab` interface provides a more state-based, MATLAB-like experience.
*   The library is highly extensible, with a system of "backends" for rendering to different output formats and interactive environments.
*   The code is organized into several sub-packages, including `lib` for the core library, `examples` for example plots, and `doc` for documentation.

## Building and Running

**Installation:**

The recommended way to install Matplotlib is from PyPI using pip:

```bash
python -m pip install -U pip
python -m pip install -U matplotlib
```

To install from source for development:

1.  Clone the repository:
    ```bash
    git clone https://github.com/matplotlib/matplotlib.git
    ```
2.  Install in editable mode:
    ```bash
    cd matplotlib
    python -m pip install -e .
    ```

**Running Tests:**

To run the tests, you will need to install the development requirements:

```bash
python -m pip install -r requirements/dev/dev-requirements.txt
```

Then, you can run the tests using `pytest`:

```bash
pytest
```

## Development Conventions

*   **Coding Style:** Matplotlib follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
*   **Testing:** Matplotlib has an extensive test suite using `pytest`. Contributions should include tests.
*   **Contributions:** The project has a detailed [contributing guide](https://matplotlib.org/devdocs/devel/contributing.html). Pull requests are welcome.

