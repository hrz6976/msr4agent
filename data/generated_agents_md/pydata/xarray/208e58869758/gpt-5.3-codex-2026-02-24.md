# Repository Guidelines

## Project Structure & Module Organization
Core library code lives in `xarray/`, with major areas such as `core/`, `backends/`, `coding/`, `plot/`, and `indexes/`. Unit and integration tests are primarily in `xarray/tests/` (files follow `test_*.py`), with additional property-based checks in `properties/`. Documentation sources are under `doc/` (Sphinx + notebooks), and performance benchmarks are in `asv_bench/`. CI/environment definitions are in `ci/requirements/`.

## Build, Test, and Development Commands
- `conda env update -f ci/requirements/environment.yml` (or `environment-windows.yml`): provision the recommended dev environment.
- `pip install -e .`: install xarray in editable mode.
- `pytest`: run the default test suite (`xarray/tests` and `properties`).
- `pytest xarray/tests/test_dataset.py -k "merge"`: run a targeted subset while iterating.
- `pre-commit run --all-files`: run formatting and lint checks (autoflake, isort, black, blackdoc, flake8, etc.).
- `pre-commit run mypy --all-files --hook-stage manual`: run type checks configured as manual-stage.
- `make -C doc html` (or `make -C doc rtdhtml`): build docs locally.

## Coding Style & Naming Conventions
Use 4-space indentation and keep style compatible with Black. Imports are standardized with isort (`profile = black`), and linting uses Flake8 rules from `setup.cfg` (e.g., line length handled by Black). Prefer descriptive snake_case for functions/variables and `test_*.py` naming for tests. Keep public API/docstring changes aligned with NumPy docstring conventions used in this project.

## Testing Guidelines
Write tests with `pytest` and colocate them in `xarray/tests/` near the affected feature area. Use parametrization for matrixed behavior and marks like `@pytest.mark.slow`, `network`, or `flaky` only when justified. Before opening a PR, run the narrowest relevant tests plus at least one broader sweep (`pytest` or module-level run).

## Commit & Pull Request Guidelines
Recent history favors concise, imperative commit subjects, often with PR reference suffixes (e.g., `Fix deepcopy ... (#7089)`). Keep commits focused on one logical change. PRs should include: problem statement, approach, tests added/updated, and any user-visible impact (API/docs/whats-new). Link related issues and include screenshots only for UI/doc-rendering changes.
