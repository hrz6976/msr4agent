# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

scikit-learn is a comprehensive Python machine learning library built on NumPy, SciPy, and joblib. The project emphasizes consistent APIs, extensive documentation, and robust testing. The codebase includes both Python and Cython (`.pyx`) for performance-critical operations.

## Build and Development Commands

### Initial Setup

Build scikit-learn in editable mode (required after cloning or modifying Cython files):
```bash
pip install -v --no-use-pep517 --no-build-isolation -e .
```

The `--no-build-isolation` flag avoids recompiling the entire project; `--no-use-pep517` is required for this flag to work correctly. You must rebuild after editing any `.pyx` or `.pxd` Cython files.

### Building

```bash
make inplace  # or: python setup.py build_ext -i
make clean    # Clean build artifacts
python setup.py build_src  # Regenerate Cython sources only
```

### Testing

```bash
# Run all tests
pytest sklearn

# Run tests for a specific module
pytest sklearn/linear_model

# Run a specific test file
pytest sklearn/linear_model/tests/test_logistic.py

# Run a specific test
pytest sklearn/linear_model/tests/test_logistic.py::test_logistic_regression

# Run tests in parallel
pytest -n auto sklearn

# Run with verbose output and show durations
pytest --showlocals -v sklearn --durations=20

# Run full test suite (includes doctests and sphinxext)
make test

# Test coverage
make test-coverage        # Single-threaded
make test-coverage-parallel  # Parallel execution
```

**Important Testing Notes:**
- Control random number generation with `SKLEARN_SEED` environment variable
- Network-dependent tests are skipped by default; enable with `SKLEARN_SKIP_NETWORK_TESTS=0`
- Float32 tests require `SKLEARN_RUN_FLOAT32_TESTS=1`
- pytest >= 7.1.2 is required

### Linting and Code Quality

```bash
# Run all linting checks
make code-analysis  # or: build_tools/linting.sh

# Individual linters
black --check --diff .      # Code formatting check
black .                     # Auto-format code
ruff check --show-source .  # Fast linting
mypy sklearn/               # Type checking
cython-lint sklearn/        # Cython-specific linting
```

**Code Style Requirements:**
- Black for Python formatting (line length: 88)
- Ruff for fast linting (E, F, W, I rules)
- Mypy for type checking
- cython-lint for Cython files
- Property decorators must come *before* deprecated decorators
- Import `Parallel` and `delayed` from `sklearn.utils.parallel`, not directly from joblib

### Documentation

```bash
make -C doc html        # Build full documentation
make doc               # Same as above  
make doc-noplot        # Build docs without running plot examples
```

## Architecture and Code Organization

### Module Structure

The `sklearn/` package is organized by machine learning task:
- **Supervised Learning**: `linear_model/`, `ensemble/`, `tree/`, `svm/`, `neighbors/`, `neural_network/`, `gaussian_process/`
- **Unsupervised Learning**: `cluster/`, `decomposition/`, `manifold/`, `mixture/`
- **Data Processing**: `preprocessing/`, `feature_extraction/`, `feature_selection/`, `impute/`
- **Model Evaluation**: `model_selection/`, `metrics/`
- **Utilities**: `utils/`, `datasets/`
- **Meta-estimators**: `pipeline/`, `compose/`, `multioutput/`, `calibration/`

### Core Design Patterns

**Estimator API:**
All estimators follow a consistent interface defined in `sklearn/base.py`:
- Inherit from `BaseEstimator` (provides `get_params`/`set_params`)
- `__init__`: Only accepts hyperparameters as keyword arguments with defaults. Must not perform validation or modify parameters. Store all kwargs as instance attributes with the same name.
- `fit(X, y=None)`: Learn from data. Unsupervised estimators must still accept `y=None` for pipeline compatibility. Returns `self`.
- Learned attributes: End with trailing underscore (e.g., `coef_`, `classes_`)
- `n_features_in_`: Set during `fit` to track expected feature count

**Transformers:**
- Implement `transform(X)` method
- Often implement `fit_transform(X, y=None)` for efficiency
- Inherit from `TransformerMixin`

**Predictors:**
- Implement `predict(X)` method
- Classifiers typically provide `predict_proba(X)` or `decision_function(X)`
- Implement `score(X, y)` for model evaluation

**Validation:**
Use utilities from `sklearn/utils/validation.py`:
- `check_X_y(X, y)`: Validate X and y in `fit`
- `check_array(X)`: Validate input arrays
- `check_is_fitted(estimator)`: Verify estimator has been fitted

### Cython Integration

Performance-critical code uses Cython (`.pyx` files). When working with Cython:
- Files requiring recompilation: `.pyx`, `.pxd` files
- After editing Cython, rebuild with: `pip install -v --no-use-pep517 --no-build-isolation -e .`
- Some Cython files are generated from Tempita templates (`.pyx.tp` extension)
- OpenMP is used for parallelization in Cython code

### Random State Handling

- Estimators accepting randomness should have a `random_state` parameter
- Use utilities from `sklearn/utils/` for consistent random number generation
- Clone operations preserve random state for reproducibility

## Common Development Workflows

### Adding a New Estimator

1. Inherit from `BaseEstimator` and appropriate mixins (`ClassifierMixin`, `RegressorMixin`, `TransformerMixin`)
2. Implement `__init__` (parameters only, no validation)
3. Implement `fit(X, y=None)` (perform validation here)
4. Implement prediction/transformation methods
5. Add tests in `tests/` subdirectory
6. Run `check_estimator()` from `sklearn.utils.estimator_checks`
7. Add examples showing usage

### Modifying Existing Code

1. Run relevant tests first: `pytest sklearn/module/tests/test_file.py`
2. Make changes to Python files directly, or Cython files if needed
3. If Cython was modified: `make inplace` to rebuild
4. Run tests again to verify
5. Run linting: `make code-analysis`
6. Consider whether docstring examples need updates

### Working with Tests

- Test files: `sklearn/*/tests/test_*.py`
- Use pytest fixtures from `sklearn/conftest.py` for common setup
- Global fixtures: `global_dtype` (float32/float64), dataset fetchers
- Use `pytest.mark.parametrize` for varying test inputs
- Skip network tests by default; mark network-dependent tests appropriately

## Important Constraints and Guidelines

### API Compatibility
- scikit-learn is highly selective about new algorithms - they must have proven track records
- API changes require a SLEP (Scikit-Learn Enhancement Proposal)
- Maintain backward compatibility; deprecate before removing features

### Performance
- Use vectorized NumPy operations over Python loops
- Profile before optimizing
- Consider Cython for hot paths (not premature optimization)
- Leverage BLAS/LAPACK through NumPy/SciPy where possible

### Dependencies
- Avoid adding new required dependencies
- Optional dependencies: Use `sklearn.utils.fixes` for compatibility shims
- Support multiple versions of NumPy/SciPy based on `_min_dependencies.py`

### Code Quality
- All public functions/classes need docstrings (NumPy style)
- Docstrings should include examples that run as doctests
- Type hints are gradually being added but not yet universal
- Use descriptive variable names; avoid single-letter names except in math-heavy code

### Testing Requirements
- Aim for high test coverage (check with `make test-coverage`)
- Test edge cases: empty arrays, single samples, high-dimensional data
- Include both unit tests and integration tests
- Test error conditions and validate error messages

## Git and CI

- Main branch: `main`
- CI runs on Azure Pipelines, CircleCI, CirrusCI
- Pre-commit hooks available in `.pre-commit-config.yaml`
- Commit messages should be descriptive

## Additional Resources

- Contributing guide: `doc/developers/contributing.rst`
- Developer documentation: `doc/developers/develop.rst`
- Advanced installation: `doc/developers/advanced_installation.rst`
- Online documentation: https://scikit-learn.org/dev/developers/
