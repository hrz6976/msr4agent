# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pylint is a static code analyzer for Python that checks for errors, enforces coding standards, and detects code smells. It uses **astroid** for AST inference, which allows it to infer actual values beyond type hints (e.g., knowing that `import logging as argparse` means `argparse.error()` is actually a logging call).

## Development Commands

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test type
pytest tests/ -k test_functional

# Run a specific functional test
pytest "tests/test_functional.py::test_functional[test_name]"

# Run with coverage
pytest tests/message/ --cov=pylint.message
coverage html

# Run functional tests directly (faster during development)
python tests/test_functional.py

# Run specific test and update expected output
python tests/test_functional.py --update-functional-output -k "test_functional[test_name]"
```

### Using Tox

```bash
# Run full test suite
tox

# Run for specific Python version
tox -e py38

# Run specific test with tox
tox -e py310 -- -k test_functional

# Recreate environment (recommended after astroid updates)
tox --recreate
```

### Linting and Formatting

```bash
# Run pre-commit hooks on all files
pre-commit run --all-files

# Run pylint on pylint's own codebase
tox -e pylint

# Run formatting checks
tox -e formatting

# Run type checking with mypy
tox -e mypy
```

### Documentation

```bash
cd doc
make install-dependencies
make build-html  # Fast build for quick checks
make html        # Full build with all checks
make clean       # Clean generated files
```

### Building and Installing

```bash
# Install in development mode with test dependencies
pip install -e .
pip install -r requirements_test.txt

# Run pylint command directly
pylint [options] modules_or_packages
```

## Architecture

### Core Components

1. **`pylint.lint.Run`** - Entry point that processes command-line options, discovers config files and plugins, then creates and initializes the PyLinter instance.

2. **`pylint.lint.PyLinter`** - Main coordinator that:
   - Parses configuration
   - Handles messages emitted by checkers
   - Manages output reporting
   - Launches checkers (including parallel execution)

3. **`pylint.checkers`** - Contains all default checkers. Most are AST-based and rely heavily on astroid.
   - Each checker inherits from `BaseChecker`
   - Checkers define `msgs` dict with message definitions
   - Checkers implement `visit_*` methods for AST node types

4. **`pylint.checkers.utils`** - Utility methods for working with astroid ASTs.

5. **`pylint.extensions`** - Optional checker plugins that can be enabled via `load-plugins` in configuration.

6. **astroid** - External dependency providing the AST representation with type inference capabilities. Pylint's inference-based approach is what differentiates it from faster linters.

### Message System

- Messages have IDs like `C0123` where `C`=category (convention/refactor/warning/error/fatal) and `0123`=unique ID
- Use `script/get_unused_message_id_category.py` to find the next available message ID when creating a new checker

## Writing Tests

### Functional Tests (Primary Test Type)

Location: `tests/functional/`

Functional tests consist of:
- `.py` file - Python code to be linted
- `.txt` file - Expected messages (same basename)
- `.rc` file (optional) - Pylint configuration for the test

**Annotation format**: Mark expected messages with comments:
```python
a, b, c = 1  # [unbalanced-tuple-unpacking]
a, b = 1.test  # [unbalanced-tuple-unpacking, no-member]

A = 5
# +1: [singleton-comparison]
B = A == None
```

**Test location guidelines**:
- For new checkers: `tests/functional/n/new_checker_message.py` (use underscores)
- For extensions: `tests/functional/ext/extension_name/`
- For regression tests: `tests/functional/r/regression/` with `regression_` prefix
- Use subdirectories when they match the prefix of your test name (e.g., `use_*` tests go in `u/use/`)

**Running and updating**:
```bash
python tests/test_functional.py -k "test_functional[test_name]"
python tests/test_functional.py --update-functional-output -k "test_functional[test_name]"
```

### Unit Tests

Location: `tests/`

For testing Pylint's internal functionality. Look at existing tests for similar functionality before writing new ones. Test data files go in `tests/regrtest_data/`.

### Configuration Tests

Location: `tests/config/functional/`

Test configuration loading. Each test needs:
- config file (`.toml`, `.ini`, etc.)
- `.result.json` - Expected configuration **differences** from default

## Checker Development

### Creating a New Checker

1. Find an unused message ID:
   ```bash
   python script/get_unused_message_id_category.py
   ```

2. Create checker class inheriting from `BaseChecker`:
   ```python
   from pylint.checkers import BaseChecker
   
   class MyChecker(BaseChecker):
       name = "my-checker"
       msgs = {
           "W1234": (
               "Message displayed to user",
               "message-symbol",
               "Longer explanation"
           ),
       }
       
       def visit_call(self, node):
           # Check logic here
           self.add_message("message-symbol", node=node)
   ```

3. Register via `pylint.extensions` or `load-plugins` configuration

### Important Notes

- **astroid.extract_node** is essential for working with AST in tests and checkers
- Search for existing warning messages to find where checker logic lives
- Pylint uses `black` for formatting (format checks are disabled in pylintrc)
- Most checkers visit AST nodes via `visit_*` methods (astroid visitor pattern)

## Configuration

- Default config: `pylintrc` in repo root
- Pylint supports `.pylintrc`, `pyproject.toml`, `setup.cfg`
- Use `py-version = 3.8.0` (minimum supported Python version)
- `jobs=1` by default; use `jobs=0` for auto-detect CPU count

## Dependencies

- **astroid** (3.0.1 - 3.1.0-dev0) - AST with inference (critical dependency)
- **isort** - Import sorting
- **mccabe** - Complexity checker  
- **dill** - Serialization for parallel processing
- **platformdirs** - Cross-platform path handling
- **tomlkit** - TOML parsing

Key: Astroid version pins are strict because Pylint's inference depends on astroid's internals.

## PR Workflow

1. Create functional test first (TDD approach)
2. Use `towncrier create <IssueNumber>.<type>` for changelog (unless maintainer marks `skip-news`)
3. Keep PRs small and focused - maintainers review in short windows
4. Update `script/.contributors_aliases.json` if using multiple emails/names
5. Run pre-commit hooks before pushing

## Additional Tools

Besides `pylint`, this repo provides:
- **pyreverse** - Generate UML diagrams from code
- **symilar** - Find code duplication
- **pylint-config** - Configuration helper
