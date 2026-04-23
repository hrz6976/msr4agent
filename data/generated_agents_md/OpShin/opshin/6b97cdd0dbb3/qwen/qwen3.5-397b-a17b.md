
# OpShin: Python-based Smart Contracts for Cardano

## Project Overview

OpShin is a compiler that allows developers to write Cardano smart contracts in a strict subset of Python. The project's philosophy is to ensure that if a program compiles, it is a valid Python program, and its behavior is consistent between a standard Python interpreter and the on-chain execution environment.

### Key Technologies

*   **Python:** The primary language for writing smart contracts.
*   **UPLC (Untyped Plutus Core):** The low-level language that Cardano smart contracts are compiled to.
*   **Poetry:** Used for dependency management and packaging.
*   **Pytest:** For running the project's test suite.

### Architecture

The core of the project is the `opshin` compiler, located in the `opshin/` directory. It uses a series of rewriting and optimization passes to transform Python's Abstract Syntax Tree (AST) into UPLC. Key components of the compiler include:

*   **`opshin/compiler.py`:** The main compiler logic, which traverses the typed AST and generates UPLC code.
*   **`opshin/rewrite/`:** Contains various modules for rewriting the AST to make it compatible with UPLC.
*   **`opshin/optimize/`:** Contains modules for optimizing the generated UPLC code.
*   **`opshin/prelude.py`:** Defines the built-in functions and types available in the OpShin language.

## Building and Running

### Installation

To install the necessary dependencies, use Poetry:

```bash
poetry install
```

### Compiling Smart Contracts

The `opshin` command-line tool is the main entry point for compiling smart contracts.

```bash
# Compile a smart contract
opshin compile spending examples/smart_contracts/assert_sum.py
```

### Running Tests

The project uses pytest for testing.

```bash
poetry run pytest
```

### Binary Size Tracking

OpShin includes a script to track the binary size of the compiled smart contracts to prevent regressions.

```bash
python scripts/check_binary_sizes.py
```

## Development Conventions

### Coding Style

The project uses `black` for code formatting. You can run it with pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

### Testing

The test suite is located in the `tests/` directory. New features should be accompanied by corresponding tests.

### Contribution

Contributions are welcome. The project has a bug bounty program to reward contributors for fixing issues. For more details, see `BUG_BOUNTY.md`.
