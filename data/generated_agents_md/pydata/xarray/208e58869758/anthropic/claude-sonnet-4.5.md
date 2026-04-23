# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Xarray is a Python library for working with labeled multi-dimensional arrays, inspired by pandas but designed for N-dimensional scientific data. The library is particularly tailored for working with netCDF files and integrates with dask for parallel computing. Core data structures are `DataArray` (labeled n-d array) and `Dataset` (collection of labeled arrays).

## Development Commands

### Installation and Setup
```bash
# Install in development mode with all dependencies
pip install -e ".[complete]"

# Or install minimal dependencies
pip install -e .

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run all tests
pytest

# Run tests in a specific file
pytest xarray/tests/test_dataset.py

# Run a specific test function
pytest xarray/tests/test_dataset.py::test_function_name

# Run tests with coverage
pytest --cov=xarray

# Run tests in parallel (faster)
pytest -n auto

# Skip flaky tests (default behavior)
pytest

# Include flaky tests
pytest --run-flaky

# Include network tests
pytest --run-network-tests

# Run property-based tests
pytest properties/
```

Test files are located in `xarray/tests/` and the root-level `conftest.py` configures pytest settings. Custom markers:
- `@pytest.mark.flaky` - Flaky tests requiring `--run-flaky`
- `@pytest.mark.network` - Tests requiring network, need `--run-network-tests`
- `@pytest.mark.slow` - Slow-running tests

### Code Quality
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Format code with black
black xarray/

# Format notebooks with black
black-jupyter doc/

# Check type annotations
mypy xarray/

# Run flake8
flake8 xarray/

# Sort imports
isort xarray/
```

Pre-commit hooks automatically run autoflake, isort, pyupgrade, black, blackdoc, and flake8. Type checking with mypy is manual-stage only (run with `pre-commit run --hook-stage manual`).

### Documentation
```bash
# Build documentation
cd doc/
make html

# Build with live-reload for development
make livehtml

# Build using ReadTheDocs settings
make rtdhtml
```

Documentation is built with Sphinx and hosted on ReadTheDocs. The entry point is `doc/index.rst`.

### Benchmarks
```bash
# Run benchmarks with ASV
cd asv_bench/
asv run

# Run specific benchmark
asv run --bench <benchmark_name>

# Compare performance between commits
asv continuous main HEAD
```

Benchmarks are in `asv_bench/benchmarks/`.

## Code Architecture

### Core Data Structures (`xarray/core/`)
- **`variable.py`** (3137 lines): Low-level `Variable` class - n-d array with named dimensions but no coordinates. Foundation for DataArray and Dataset.
- **`dataarray.py`** (6442 lines): `DataArray` class - labeled n-d array with coordinates, dimensions, and attributes. Primary user-facing object for single arrays.
- **`dataset.py`** (9159 lines): `Dataset` class - dict-like collection of DataArrays sharing dimensions. Primary user-facing object for multi-variable data.
- **`coordinates.py`**: Coordinate management for DataArray and Dataset.
- **`indexes.py`** (1447 lines): Index classes for label-based selection, wrapping pandas indexes and supporting custom index types.
- **`indexing.py`** (1583 lines): Advanced indexing machinery for `.sel()`, `.isel()`, `.loc[]`, and fancy indexing.

### Key Subsystems
- **`computation.py`** (2143 lines): `apply_ufunc()` for wrapping numpy/dask functions, plus `dot()`, `where()`, and other array operations.
- **`alignment.py`**: Broadcasting and alignment logic for operations between DataArrays/Datasets with different coordinates.
- **`merge.py`**: Merging multiple datasets with conflict resolution.
- **`concat.py`**: Concatenating along a dimension.
- **`groupby.py`**: Split-apply-combine operations (`.groupby()`).
- **`resample.py`**: Time-based resampling.
- **`rolling.py`**: Rolling window operations.
- **`missing.py`**: Interpolation and filling missing values.
- **`_reductions.py`** (6490 lines, auto-generated): Reduction operations (sum, mean, etc.).

### Backend System (`xarray/backends/`)
Pluggable I/O system for multiple file formats:
- **`plugins.py`**: Entry point system for registering backends. Standard backends: netcdf4, h5netcdf, scipy.
- **`netCDF4_.py`**, **`h5netcdf_.py`**, **`scipy_.py`**: netCDF backends.
- **`zarr.py`**: Zarr format support.
- **`rasterio_.py`**: Rasterio backend for geospatial rasters.
- **`api.py`**: User-facing `open_dataset()`, `open_mfdataset()`, `load_dataset()` functions.
- **`common.py`**: Base `BackendEntrypoint` and `BackendArray` classes.

Backends implement a lazy-loading interface where data isn't read until accessed. Custom backends can be registered via entry points.

### Accessor System (`xarray/core/`)
- **`accessor_dt.py`**: `.dt` accessor for datetime operations.
- **`accessor_str.py`** (2533 lines): `.str` accessor for string operations.
- **`extensions.py`**: `@register_dataarray_accessor` and `@register_dataset_accessor` decorators for custom accessors.

### Plotting (`xarray/plot/`)
Integration with matplotlib for plotting DataArrays and Datasets. Automatically handles dimensions and coordinates.

## Important Patterns

### Lazy Evaluation
- Operations return new objects without copying data (copy-on-write semantics).
- File I/O is lazy by default - use `.compute()` or `.load()` to trigger computation.
- When working with dask arrays, most operations remain lazy until explicitly computed.

### Dimension and Coordinate Handling
- **Dimensions**: Named axes (e.g., `"time"`, `"lat"`, `"lon"`).
- **Coordinates**: Arrays that label dimensions. Can be:
  - **Dimension coordinates**: 1-D, same name as dimension, used for label-based indexing.
  - **Non-dimension coordinates**: Multi-dimensional or auxiliary coordinates.
- **Indexes**: Pandas indexes wrapping dimension coordinates for fast label-based selection.

### Operations Align Automatically
When combining DataArrays/Datasets with different coordinates:
```python
x + y  # Automatically aligns on dimension labels, fills missing with NaN
```
Control alignment with `xr.align()` or `join` parameter in operations.

### Array Wrapping
Xarray wraps various array types (numpy, dask, cupy, sparse, pint) using duck-typing:
- **`duck_array_ops.py`**: Array-agnostic operations.
- **`pycompat.py`**: Compatibility utilities for different array libraries.

When implementing new operations, use `duck_array_ops` functions rather than numpy directly to maintain compatibility.

### Testing Patterns
- Use helper functions from `xarray/tests/__init__.py`: `assert_identical()`, `assert_equal()`, `assert_allclose()`, `create_test_data()`.
- Use markers like `@requires_dask`, `@requires_scipy` to skip tests when optional dependencies are missing.
- Property-based tests using Hypothesis are in `properties/`.

## Type Checking
The codebase uses type annotations (checked with mypy):
- Type stubs for some operations in `.pyi` files (e.g., `_typed_ops.pyi`).
- Many numeric libraries lack type annotations, so mypy ignores them (see `setup.cfg`).
- `xarray/core/types.py` defines custom types.
- `py.typed` marker file indicates PEP 561 compliance.

## Performance Considerations
- **Dask integration**: Use `chunks` parameter when opening files or via `.chunk()` for parallel/out-of-core computation.
- **Bottleneck**: Optional C-accelerated library for reductions on float arrays.
- **numbagg**: JIT-compiled operations with numba.
- **flox**: Faster groupby operations.
- Avoid calling `.values` or `.to_numpy()` unnecessarily - work with xarray objects to maintain laziness.

## Code Generation
- `xarray/core/_reductions.py` is auto-generated. Do not edit directly - modify `xarray/util/generate_reductions.py` instead and regenerate.
- `xarray/core/_typed_ops.py` and `_typed_ops.pyi` are also generated.

## Configuration
- `setup.cfg`: Package metadata, pytest config, flake8, isort, mypy settings.
- `pyproject.toml`: Build system config and minimal tool config.
- `.pre-commit-config.yaml`: Pre-commit hook configuration.
- `conftest.py`: Pytest configuration and fixtures.

## Contributing Workflow
1. Fork and clone the repository.
2. Create a new branch for your changes.
3. Install pre-commit hooks: `pre-commit install`.
4. Make changes and ensure tests pass: `pytest`.
5. Pre-commit hooks will run automatically on commit.
6. Push and open a pull request.

See detailed contributing guidelines at https://docs.xarray.dev/en/stable/contributing.html.
