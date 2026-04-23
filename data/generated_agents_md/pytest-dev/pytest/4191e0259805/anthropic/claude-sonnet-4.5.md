# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the pytest repository - a full-featured Python testing framework. Pytest makes it easy to write small tests, yet scales to support complex functional testing for applications and libraries.

## Essential Commands

### Running Tests

```bash
# Run all tests using tox (recommended)
tox -e linting,py37

# Run tests for a specific Python version
tox -e py37

# Run a specific test file
tox -e py37 -- testing/test_config.py

# Run tests with additional pytest options (e.g., enter pdb on failure)
tox -e py37 -- --pdb

# Run tests directly without tox (after setting up dev environment)
python3 -m venv .venv
source .venv/bin/activate  # Linux
pip install -e ".[testing]"
pytest testing/test_config.py
```

### Development Setup

```bash
# Install pre-commit hooks
pip install --user pre-commit
pre-commit install

# Run linting
tox -e linting

# Build documentation
tox -e docs
# Docs will be in doc/en/_build/html/
```

### Creating Changelog Entries

When making changes that affect documented behavior, create a changelog file:
- Format: `changelog/<issue_id>.<type>.rst`
- Types: `feature`, `improvement`, `bugfix`, `doc`, `deprecation`, `breaking`, `vendor`, `trivial`
- Example: `changelog/2574.bugfix.rst`

### Git Workflow for Backports

When a bug fix needs to be backported to a release branch:
```bash
# Automatic method: Add "backport X.Y.x" label to the PR

# Manual method:
git checkout origin/X.Y.x -b backport-XXXX
git cherry-pick -x -m1 <merge-commit-sha>
# Open PR targeting X.Y.x with "[X.Y.x]" prefix
```

## Architecture & Code Organization

### Source Code Structure

- **`src/_pytest/`**: Main pytest implementation
  - `main.py`: Core test session and collection loop
  - `python.py`: Python test collection (Module, Class, Function nodes)
  - `runner.py`: Test execution engine (setup/call/teardown)
  - `fixtures.py`: Fixture system implementation
  - `hookspec.py`: Plugin hook specifications
  - `config/`: Configuration and plugin management
  - `assertion/`: Assertion rewriting and introspection
  - `mark/`: Test marking system (@pytest.mark.*)
  - `_code/`: Code inspection and traceback formatting
  
- **`testing/`**: Pytest's own test suite
  - Tests use the `pytester` fixture extensively for black-box testing
  - Tests are organized by feature (e.g., `test_assertion.py`, `test_fixtures.py`)

### Plugin Architecture

Pytest is built on pluggy - a plugin management system that uses hooks extensively:
- Hooks are specified in `hookspec.py` using `@hookspec` decorator
- Plugins implement hooks using `@hookimpl` decorator
- Hook execution follows a well-defined order (first/last/wrapper semantics)
- Many internal features are implemented as built-in plugins

### Test Collection & Execution Flow

1. **Configuration** (`config/__init__.py`): Parse args, load plugins, read ini files
2. **Collection** (`main.py`): Discover and build the test tree (Session → Module → Class → Function)
3. **Setup/Call/Teardown** (`runner.py`): Execute tests with fixture management
4. **Reporting** (`terminal.py`, `junitxml.py`): Format and output results

### Key Concepts

- **Nodes** (`nodes.py`): Base class hierarchy for test items and collectors
- **Fixtures** (`fixtures.py`): Dependency injection system with scope management (function/class/module/session)
- **Assertion Rewriting** (`assertion/rewrite.py`): AST transformation for detailed assertion messages
- **Markers** (`mark/`): Metadata system for test categorization and parameterization

## Development Guidelines

### Testing Your Changes

- Use the `pytester` fixture for writing tests about pytest itself
- Example pattern:
  ```python
  def test_feature(pytester):
      pytester.makepyfile("""
          def test_foo():
              assert True
      """)
      result = pytester.runpytest()
      result.assert_outcomes(passed=1)
  ```

### Code Style

- PEP-8 naming conventions
- Black formatting (enforced by pre-commit)
- Import ordering via reorder-python-imports
- Type hints required (checked with mypy)
- Python 3.7+ compatibility required

### Test Organization

- Place tests in the appropriate `test_*.py` file based on the feature being tested
- If testing `cacheprovider.py`, add tests to `test_cacheprovider.py`
- For new subsystems, create a new test file following the naming pattern

### Common Patterns

- Configuration options are added via `pytest_addoption` hook
- Use `@pytest.hookimpl` for implementing plugin hooks
- Test ordering: `testing/conftest.py` reorders tests, moving slow ones (using pexpect) to the end
- Always consider fixture scope when adding new fixtures

## Important Notes

### Version Requirements

- Python 3.7+ minimum
- Uses setuptools-scm for version management (from git tags)
- Version written to `src/_pytest/_version.py`

### Pre-commit Hooks

The project uses extensive pre-commit hooks including:
- black (formatting)
- mypy (type checking)
- flake8 (linting)
- reorder-python-imports (import sorting)
- pyupgrade (syntax modernization)

All code changes must pass pre-commit checks before being committed.

### Testing Configuration

Key pytest.ini options (in `pyproject.toml`):
- `addopts = "-rfEX -p pytester --strict-markers"` - Default test run options
- `testpaths = ["testing"]` - Test discovery location
- `python_files/classes/functions` - Test discovery patterns
- The pytester plugin is loaded by default for testing

### Avoiding Common Issues

- **Never import from `py` library directly** - it's deprecated (pre-commit hook enforces this)
- **Fixtures**: Check for existing fixtures before creating new ones
- **Markers**: Register new markers in `pyproject.toml` under `[tool.pytest.ini_options]`
- **When changing configs/hooks**: Consider impact on plugin ecosystem
