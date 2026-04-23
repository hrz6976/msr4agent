# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpShin is a Python-to-Cardano smart contract compiler that compiles a strict subset of valid Python into UPLC (Untyped Plutus Core), the assembly language of the Cardano blockchain. The key design principle: if it compiles, the on-chain behavior matches the Python execution.

## Development Commands

### Installation & Setup
```bash
# Install dependencies using Poetry
python3 -m pip install opshin

# For development (from source)
poetry install
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
coverage run -m pytest
coverage report

# Run a specific test file
pytest tests/test_misc.py

# Run a specific test
pytest tests/test_misc.py::TestClass::test_method
```

### Code Quality
```bash
# Format code with black
black .

# Run pre-commit hooks
pre-commit run --all-files
```

### Compiling & Evaluating Smart Contracts
```bash
# Evaluate a contract in Python (for quick testing)
opshin eval spending examples/smart_contracts/assert_sum.py "{\"int\": 4}" "{\"int\": 38}" <script_context_cbor>

# Compile to UPLC
opshin compile spending examples/smart_contracts/assert_sum.py

# Build all deployment artifacts (for production use)
opshin build spending examples/smart_contracts/assert_sum.py

# Debug: compile to intermediate Pluto language
opshin compile_pluto spending examples/smart_contracts/assert_sum.py

# Debug: evaluate in UPLC
opshin eval_uplc spending examples/smart_contracts/assert_sum.py <args>

# Compile with parameterization (for minting policies)
opshin compile examples/smart_contracts/wrapped_token.py --force-three-params
```

### Binary Size Tracking
```bash
# Check binary sizes against latest release
python scripts/check_binary_sizes.py
```

## Architecture

OpShin uses a multi-stage compilation pipeline:

### 1. Type Inference (`opshin/type_inference.py`)
- Implements aggressive static type inference based on Aycock's work
- Infers types for all Python AST nodes in a strict subset of Python
- Enables resolution of overloaded functions and adds type safety
- Key: all types must be statically inferrable; no dynamic typing

### 2. Rewriting (`opshin/rewrite/`)
Transforms complex Python constructs into simpler equivalents:
- `rewrite_import.py`: Handles imports (typing, dataclasses, hashlib, etc.)
- `rewrite_augassign.py`: Expands `+=`, `-=` to full assignments
- `rewrite_comparison_chaining.py`: Expands `a < b < c` to `a < b and b < c`
- `rewrite_tuple_assign.py`: Handles tuple unpacking
- `rewrite_scoping.py`: Manages variable scoping
- And more...

### 3. Compilation (`opshin/compiler.py`)
Two-stage process:
- **Stage 1**: Python AST → Pluthon (intermediate language based on Pluto)
- **Stage 2**: Pluthon → UPLC (via the `pluthon` and `uplc` libraries)

Key techniques:
- Uses Y combinator to map imperative Python to functional UPLC
- Emulates variables through UPLC lambda applications
- Maps loops to recursive functions
- Statemonad emulation for mutability (implicit for the user)

### 4. Optimization (`opshin/optimize/`)
- `optimize_const_folding.py`: Compile-time constant evaluation
- `optimize_remove_deadvars.py`: Dead variable elimination
- `optimize_remove_trace.py`: Removes trace/print statements
- `optimize_union_expansion.py`: Union type optimizations

### 5. Building (`opshin/builder.py`)
Generates deployment artifacts:
- Compiled UPLC script
- Script addresses (mainnet/testnet)
- Policy IDs
- CIP-0057 blueprints for off-chain usage

## Type System & Memory Model

### Type Mappings
Python types map to UPLC builtins:
- `int` ↔ `BuiltinInteger`
- `str` ↔ `BuiltinString` (utf8 encoded)
- `bytes` ↔ `BuiltinByteString`
- `bool` ↔ `BuiltinBool`
- `None` ↔ `BuiltinUnit`
- `list` ↔ `BuiltinList`
- `dict` ↔ `BuiltinList` (of data pairs)
- `PlutusData` subclasses ↔ `PlutusData` (identity)

### Memory Model
- Variables are UPLC variables (lambda applications with named parameters)
- Re-assignments are nested variable declarations (shadowing)
- Loops compile to recursive functions that handle variable re-assignment
- Python objects are immutable Plutus Data counterparts

### Validator Functions
- **Spending validators**: 3 params (datum, redeemer, script_context)
- **Minting policies**: 3 params (unit, redeemer, script_context)
  - Note: OpShin adds a unit parameter to minting policies for consistency
  - Use `--force-three-params` flag for dual-use validators

## Important Type Inference & Compilation Details

### Known Deviations from Python
- `isinstance` only checks constructor ID, not field types/count
- `int("  123  ")` fails (no auto-trim of whitespace)
- `bytes.fromhex("00 11\t")` fails (no auto-removal of spaces)
- `pow(x, y)` and `x ** y` fail when `y` is negative (no floats)
- Chained comparisons like `x <= y <= z` evaluate `y` twice

### Parameter Validation
Parameters are passed as Data objects and converted to native UPLC types on entry. Data objects are NOT type-checked at runtime to save execution costs. The validator writer must ensure:
- Continuing/chained protocol state is properly validated
- User-controlled state is checked for size/validity
- Script context never needs checking (protocol-controlled)

### Parameterized Scripts
Define validators with more than the standard 2-3 parameters. Extra parameters become compile-time constants that must be applied during deployment. Example:
```bash
opshin compile contract.py '{"int": 42}' '{"bytes": "deadbeef"}'
```

### Function ABI
- Functions take arguments wrapped in delay statements
- Argument order: alphabetically sorted surrounding variables, then declared parameters
- Exception: 0-arg functions with 0 read variables take 1 discarded argument
- Functions access surrounding variables at call-time (consistent with Python)

## Project Structure

- `opshin/`: Core compiler source
  - `type_inference.py`: Static type inferencer
  - `compiler.py`: Main compilation logic (Python → Pluthon → UPLC)
  - `builder.py`: Build system for deployment artifacts
  - `rewrite/`: AST rewriting passes
  - `optimize/`: Optimization passes
  - `type_impls.py`: Type system implementations
  - `fun_impls.py`: Built-in function implementations
  - `prelude.py`, `prelude_v3.py`: Standard library for contracts
  - `std/`: Standard library modules
  - `ledger/`: Cardano ledger type definitions
- `tests/`: Test suite
  - `test_misc.py`: General functionality tests
  - `test_builtins.py`: Built-in function tests
  - `test_ops.py`: Operator tests
  - `test_types.py`: Type system tests
  - Test subdirs mirror main package structure
- `examples/`: Example contracts and programs
  - `examples/smart_contracts/`: Production-ready contract examples
- `scripts/`: Development utilities
- `docs/`: Documentation

## Recursion Limits

The default recursion limit has been raised for compilation of complex contracts. If you encounter recursion errors during compilation, this is expected for very deeply nested or complex code structures.

## Pre-commit Hooks

The repository uses `black` for code formatting. All code must be formatted before committing.
