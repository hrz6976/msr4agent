# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Astropy is the core Python package for astronomy and astrophysics. It provides:
- Core astronomy functionality (coordinates, tables, units, time, WCS, FITS I/O)
- Common tools for astronomical research
- A foundation for affiliated astronomy packages

The codebase is a large monorepo with multiple subpackages under `astropy/`, each handling specific astronomy domains. It has significant compiled components (Cython extensions) and wraps external C libraries (WCSLIB, CFITSIO, ERFA).

## Development Commands

### Installation and Setup

```bash
# Install in development mode with minimal dependencies
pip install -e .

# Install with test dependencies
pip install -e .[test]

# Install with all optional dependencies
pip install -e .[all]

# Install with recommended dependencies
pip install -e .[recommended]
```

**Note**: Astropy includes C/Cython extensions that must be compiled. The `-e` flag sets up an editable install but requires the extensions to be built. On code changes to `.pyx` files, you may need to reinstall.

### Running Tests

```bash
# Run full test suite using tox (recommended for CI-like testing)
tox -e test

# Run tests directly with pytest (faster for development)
pytest

# Run tests for a specific subpackage
pytest astropy/table

# Run a specific test file
pytest astropy/table/tests/test_table.py

# Run a specific test function
pytest astropy/table/tests/test_table.py::test_column_rename

# Run with coverage
tox -e test-cov

# Run with specific numpy version
tox -e py39-test-numpy122

# Run image comparison tests
tox -e py39-test-image-mpl311

# Skip remote data tests (faster)
pytest --remote-data=none

# Run only tests that require remote data
pytest --remote-data=any
```

**Important**: Tests must be run from outside the source directory to avoid importing from the source tree instead of the installed package. Tox handles this automatically by using `.tmp/{envname}` as the working directory.

### Code Quality and Linting

```bash
# Run all pre-commit checks (style, linting, formatting)
tox -e codestyle

# Or use pre-commit directly
pre-commit run --all-files

# Run on modified files only
pre-commit run

# Format code with black
black .

# Sort imports with isort
isort .

# Run flake8
flake8 astropy
```

**Style Guidelines**:
- Code must be compatible with Python >= 3.8
- Black (line length 88) for formatting
- isort for import sorting
- Flake8 for linting
- Follow [coding guidelines](https://docs.astropy.org/en/latest/development/codeguide.html)

### Building Documentation

```bash
# Build HTML documentation
tox -e build_docs

# Or manually
cd docs
pip install -e .[docs]
sphinx-build -b html . _build/html

# Check for broken links
tox -e linkcheck
```

### Single Test Development Workflow

When fixing a bug or implementing a feature:

```bash
# 1. Install with test dependencies
pip install -e .[test]

# 2. Run the specific test you're working on
pytest astropy/coordinates/tests/test_angles.py::test_angle_format -v

# 3. After code changes, re-run the test
pytest astropy/coordinates/tests/test_angles.py::test_angle_format -v

# 4. Before committing, run broader tests
pytest astropy/coordinates/tests/test_angles.py
```

## Codebase Architecture

### Major Subpackages

- **`astropy/coordinates`**: Celestial coordinate systems, transformations, sky positions
- **`astropy/table`**: N-dimensional heterogeneous tables (similar to pandas but astronomy-focused)
- **`astropy/units`**: Physical units and quantities with automatic unit conversion
- **`astropy/time`**: Time and date handling with high precision for astronomy
- **`astropy/io/fits`**: Reading/writing FITS files (standard astronomy format)
- **`astropy/io/ascii`**: Reading/writing ASCII tables in various formats
- **`astropy/io/votable`**: VOTable XML format support
- **`astropy/wcs`**: World Coordinate System (maps pixel to sky coordinates)
- **`astropy/modeling`**: Model fitting framework (1D/2D models, fitters)
- **`astropy/cosmology`**: Cosmological calculations and models
- **`astropy/stats`**: Statistical functions for astronomy
- **`astropy/visualization`**: Plotting utilities and image scaling
- **`astropy/timeseries`**: Time series data analysis
- **`astropy/nddata`**: N-dimensional dataset container with metadata
- **`astropy/convolution`**: Convolution and filtering
- **`astropy/constants`**: Physical and astronomical constants
- **`astropy/utils`**: Shared utilities used across subpackages
- **`astropy/config`**: Configuration system

### Directory Structure

- **`astropy/`**: Main package source code
  - Each subpackage has its own `/tests` directory with pytest tests
  - Cython extensions are `.pyx` files alongside Python code
- **`docs/`**: Sphinx documentation with RST files and example code
- **`cextern/`**: External C libraries (WCSLIB, CFITSIO, Expat)
- **`examples/`**: Example scripts demonstrating astropy usage
- **`licenses/`**: License files for bundled components
- **`docs/changes/`**: Changelog fragments for towncrier

### Key Architectural Patterns

**1. Quantity Framework**: The `astropy.units` system uses `Quantity` objects that combine numerical values with units. Many astropy functions accept and return Quantities, enabling automatic unit checking and conversion.

**2. Coordinate Frames**: The `astropy.coordinates` system has a polymorphic design where different coordinate frames (ICRS, Galactic, FK5, etc.) are classes that can transform between each other. Positions are represented as frame objects containing coordinates.

**3. Table Structure**: `astropy.table.Table` is built around columns stored as `Column` objects (backed by numpy arrays). Tables support metadata, units, masked values, and mixin columns.

**4. I/O Registry**: The `astropy.io.registry` provides a unified interface where different file formats register their read/write functions. Users call `Table.read()` and the registry dispatches to the appropriate reader based on file format.

**5. FITS Handling**: The `astropy.io.fits` package wraps the CFITSIO C library with Python classes representing HDU (Header Data Unit) structures. Files are accessed through `HDUList` objects.

**6. Configuration**: The `astropy.config` system allows users to configure behavior through a `.astropy/config` file. Packages define configuration options using `ConfigNamespace` and `ConfigItem`.

**7. Testing**: Used `pytest` with custom plugins (`pytest-astropy`, `pytest-doctestplus`, `pytest-remotedata`). Tests are organized in `tests/` subdirectories. The `@pytest.mark.remote_data` decorator marks tests requiring internet access.

### Compiled Extensions

Astropy contains Cython (`.pyx`) extensions for performance-critical code:
- These must be compiled before the package can be used
- Changes to `.pyx` files require reinstallation
- Build system uses `setuptools` with `extension-helpers`

External C libraries in `cextern/`:
- **WCSLIB**: World Coordinate System library (wrapped by `astropy.wcs`)
- **CFITSIO**: FITS file I/O library (wrapped by `astropy.io.fits`)  
- **ERFA**: Essential Routines for Fundamental Astronomy (wrapped by `pyerfa` dependency)
- **Expat**: XML parser used by VOTable

## Changelog and Versioning

### Changelog Fragments (Towncrier)

**Every pull request must include a changelog entry** (unless it's a trivial docs fix or internal change). Create a file in `docs/changes/`:

```bash
# Format: docs/changes/<subpackage>/<PR_NUMBER>.<type>.rst
# Example: docs/changes/table/12345.bugfix.rst

# Types:
# - feature: New feature
# - api: API change  
# - bugfix: Bug fix
# - other: Other changes (only in root docs/changes/, not subpackages)
```

**Example changelog file** (`docs/changes/coordinates/12345.bugfix.rst`):
```
Fixed a bug in ``SkyCoord.match_to_catalog_sky`` where matches were 
incorrect when the catalog contained duplicate entries.
```

- Use double backticks for code elements
- Write full sentences with proper punctuation
- If you don't know the PR number yet, use a placeholder and update it after opening the PR
- Maintainers may tell you to skip the changelog for minor fixes with the `no-changelog-entry-needed` label

## Testing Conventions

- Tests go in `<subpackage>/tests/` directories
- Test files must start with `test_` prefix
- Test functions must start with `test_` prefix
- Use `pytest` fixtures for setup/teardown
- Mark tests requiring optional dependencies: `@pytest.mark.skipif('not HAS_SCIPY')`
- Mark tests requiring internet: `@pytest.mark.remote_data`
- Mark image comparison tests: `@pytest.mark.mpl_image_compare`
- Include regression tests for bug fixes
- Document the source/rationale for test data

## Pull Request Workflow

1. Fork the repository and create a branch from `main`
2. Make changes following the coding style guidelines
3. Add tests for new functionality or bug fixes
4. Add documentation updates if needed  
5. Create a changelog fragment in `docs/changes/`
6. Open a PR against the `main` branch (not against release branches)
7. Ensure GitHub Actions and CircleCI tests pass
8. Respond to review feedback

**Pre-commit checks**: Astropy uses pre-commit hooks configured in `.pre-commit-config.yaml`. These run automatically in CI, so running `pre-commit run --all-files` locally helps catch issues early.

**CI Skip**: Add `[ci skip]` to commit messages for work-in-progress or trivial doc changes that don't need full CI:
```bash
git commit -m "WIP: refactoring [ci skip]"
```

## Key Dependencies

**Required**:
- `numpy >= 1.20`: Array operations, core numerical computing
- `pyerfa >= 2.0`: Wraps ERFA C library for fundamental astronomy routines
- `PyYAML >= 3.13`: YAML parsing for configuration and serialization
- `packaging >= 19.0`: Version parsing and comparison

**Optional but commonly used**:
- `scipy >= 1.5`: Advanced scientific computing (modeling, stats)
- `matplotlib >= 3.1`: Plotting and visualization
- `pytest`: Testing framework
- `h5py`: HDF5 file I/O
- `asdf >= 2.10.0`: Advanced Scientific Data Format

## Development Notes

### Pre-commit Configuration

The repository uses extensive pre-commit hooks. Key checks:
- `pyupgrade`: Modernizes Python syntax for Python 3.8+
- `black`: Code formatting (line length 88)
- `isort`: Import sorting
- `flake8`: Linting (subset of checks in CI)
- Various file format validators (JSON, YAML, TOML, RST)

### Compatibility

- **Python**: Minimum Python 3.8, but code should work with newer versions
- **NumPy**: Support for NumPy >= 1.20
- **Platform**: Cross-platform (Linux, macOS, Windows)
- C extensions must compile on all platforms

### Long-running Operations

Some tests involve:
- Remote data downloads (use `--remote-data=none` to skip)
- Image comparison tests (require `pytest-mpl` and baseline images)
- Long computations (mark with appropriate timeouts)

### Common Gotchas

1. **Import astropy from installed version**: Don't run tests from the source directory - pytest should be run from a different directory or use tox
2. **C extension changes**: After modifying `.pyx` files, you must reinstall: `pip install -e .`
3. **Pytest cache**: Clear with `pytest --cache-clear` if you see stale test results
4. **Units**: Many functions accept `Quantity` objects - check if quantities are supported before assuming plain numpy arrays
5. **Coordinates**: Coordinate objects are immutable - operations return new objects

### Working with Subpackages

Each subpackage is fairly self-contained with its own:
- `__init__.py`: Subpackage initialization and public API
- `tests/`: Test suite  
- `setup_package.py` (if needed): Build configuration for C/Cython extensions
- Module-specific documentation in `docs/<subpackage>/`

Many subpackages can be worked on independently, but cross-dependencies exist (e.g., `coordinates` uses `units`, `table` uses `units` and `time`).

## Useful Resources

- [Development workflow documentation](https://docs.astropy.org/en/latest/development/workflow/development_workflow.html)
- [Coding guidelines](https://docs.astropy.org/en/latest/development/codeguide.html)
- [Testing guidelines](https://docs.astropy.org/en/latest/development/testguide.html)
- [Documentation guidelines](https://docs.astropy.org/en/latest/development/docguide.html)
- Online docs: https://docs.astropy.org/
