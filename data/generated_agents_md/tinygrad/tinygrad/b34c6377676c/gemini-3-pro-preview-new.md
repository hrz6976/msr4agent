# Project Overview

`tinygrad` is a lightweight and hackable deep learning framework designed to be a simpler alternative to PyTorch, JAX, and TVM. It provides an end-to-end stack for deep learning, including a Tensor library with autograd, a compiler for fusing and lowering kernels, JIT and graph execution, and essential components for training neural networks. The project is written in Python and supports multiple accelerators, including OpenCL, CPU, METAL, CUDA, and more.

## Building and Running

### Installation

The recommended way to install `tinygrad` is from source:

```sh
git clone https://github.com/tinygrad/tinygrad.git
cd tinygrad
python3 -m pip install -e .
```

### Running Tests

To run the tests, first install the testing dependencies:

```sh
python3 -m pip install -e '.[testing]'
```

Then, you can run the test suite using pytest:

```sh
python3 -m pytest test/
```

Individual test files can also be run directly:

```sh
python3 test/test_ops.py
```

## Development Conventions

*   **Linting and Type Checking:** The project uses `pylint`, `mypy`, `ruff`, and `pre-commit` to maintain code quality. The pre-commit hooks should be installed with `pre-commit install`.
*   **Testing:** A comprehensive test suite is located in the `test/` directory. New features and bug fixes should include corresponding tests.
*   **Contributions:** The project has a detailed `CONTRIBUTING.md` guide that outlines the process for submitting pull requests. The emphasis is on simplicity, readability, and well-benchmarked improvements.
