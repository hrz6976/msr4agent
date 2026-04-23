# AGENTS.md

## Project Overview

This project is `tinygrad`, a deep learning framework designed to be a middle ground between the complexity of PyTorch and the simplicity of micrograd. It is maintained by the "tiny corp" and aims to be hackable and easy to understand.

**Core Components:**

*   **Tensor Library:** Provides a `Tensor` object with autograd capabilities, similar to PyTorch.
*   **Compiler and IR:** Features an Intermediate Representation (IR) and a compiler that can fuse operations and lower kernels for efficient execution.
*   **JIT and Graph Execution:** Includes a Just-In-Time (JIT) compiler (`TinyJit`) for capturing and replaying kernel executions.
*   **Neural Network Primitives:** Offers `nn`, `optim`, and `datasets` modules for building and training neural networks.

**Supported Accelerators:**

`tinygrad` supports a variety of hardware accelerators, including:
*   OpenCL
*   CPU
*   METAL
*   CUDA
*   AMD
*   NV
*   QCOM
*   WEBGPU

## Building and Running

### Installation

The recommended way to install `tinygrad` is from the source code.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/tinygrad/tinygrad.git
    cd tinygrad
    ```

2.  **Install in editable mode:**
    ```bash
    python3 -m pip install -e .
    ```

Alternatively, you can install the latest master branch directly using pip:
```bash
python3 -m pip install git+https://github.com/tinygrad/tinygrad.git
```

### Running Tests

To run the tests, you first need to install the testing dependencies:

```bash
python3 -m pip install -e '.[testing]'
```

Then, you can run specific tests or the entire suite:

*   **Run a single test file:**
    ```bash
    python3 test/test_ops.py
    ```

*   **Run the entire test suite with pytest:**
    ```bash
    python3 -m pytest test/
    ```

The project also uses pre-commit hooks for linting and type-checking. To install them:
```bash
pre-commit install
```

## Development Conventions

*   **Simplicity and Readability:** The primary goal is to reduce complexity. Code golf is explicitly discouraged.
*   **Benchmarking:** Any changes claimed to be a "speedup" must be accompanied by benchmarks.
*   **Small, Focused PRs:** Large or complex pull requests are likely to be rejected. The preference is for small, incremental changes that are easy to review.
*   **Testing:**
    *   Bug fixes must include a regression test.
    *   New features must have regression tests.
    *   Refactors should pass the "process replay" tests, which compare generated kernels against the master branch.
*   **API Consistency:** New features should aim to match the API of PyTorch or NumPy where applicable.
*   **Contribution Scope:** Contributions are most welcome in the core `tinygrad/` directory for bug fixes, new features, and meaningful refactors. Changes to documentation and non-core code are more restricted.
