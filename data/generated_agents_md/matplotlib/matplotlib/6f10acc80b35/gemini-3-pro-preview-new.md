# Matplotlib

## Project Overview

Matplotlib is a comprehensive library for creating static, animated, and interactive visualizations in Python. It is a code-based project that produces publication-quality figures in a variety of hardcopy formats and interactive environments across platforms. Matplotlib can be used in Python scripts, Python/IPython shells, web application servers, and various graphical user interface toolkits.

## Building and Running

### Installation

Matplotlib releases are available as wheel packages for macOS, Windows, and Linux on PyPI. Install it using `pip`:

```sh
python -m pip install -U pip
python -m pip install -U matplotlib
```

### Building from Source

To build Matplotlib from source, you will need a C compiler. The easiest way to get the latest development version is to clone the git repository and install it in editable mode:

```sh
git clone https://github.com/matplotlib/matplotlib.git
cd matplotlib
python -m pip install -e .
```

To run the tests, you will need to install some additional dependencies:

```sh
python -m pip install -r requirements/dev/dev-requirements.txt
```

## Development Conventions

### Dependencies

The project's dependencies are managed in the `requirements` directory. The main development dependencies are listed in `requirements/dev/dev-requirements.txt`, which includes the documentation and testing dependencies.

### Testing

The project uses `pytest` for testing. The tests can be run by installing the testing dependencies and running `pytest`.

### Contribution Guidelines

The project has a comprehensive contributing guide that can be found in the documentation. It is recommended to read this guide before contributing to the project.
