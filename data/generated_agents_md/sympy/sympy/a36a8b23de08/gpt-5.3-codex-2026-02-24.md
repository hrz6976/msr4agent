# Repository Guidelines

## Project Structure & Module Organization
Core library code lives in `sympy/`, organized by domain (for example `sympy/core`, `sympy/solvers`, `sympy/polys`). Tests are colocated with modules under `*/tests/test_*.py` (for example `sympy/core/tests/test_basic.py`). Documentation sources are in `doc/src/`, with Sphinx configuration in `doc/src/conf.py`. Utility scripts for testing and maintenance are in `bin/`.

## Build, Test, and Development Commands
- `pip install -e .` installs SymPy in editable mode for local development.
- `bin/test` runs the full SymPy test suite through SymPy’s test runner.
- `bin/test sympy/core/tests/test_basic.py` runs a focused test file.
- `bin/test code_quality` runs quality checks wired into the test runner.
- `bin/doctest` runs doctests in both code and `doc/src`.
- `pytest` runs tests using `pytest.ini` defaults (`sympy` and `doc/src` testpaths).
- `cd doc && make html` builds documentation into `doc/_build/html`.

## Coding Style & Naming Conventions
Use 4 spaces for Python indentation and UTF-8 with LF line endings (`.editorconfig`). Keep module/function names `snake_case`, classes `CamelCase`, and tests named `test_*.py`/`test_*`. Linting is configured in `pyproject.toml` and `setup.cfg` (`ruff`/`flake8` rules); run `bin/test code_quality` before opening a PR.

## Testing Guidelines
Add or update tests in the same subsystem you modify. Prefer narrowly scoped regression tests that fail before your fix and pass after it. For quick iteration, run targeted tests first, then broader module tests, then full suite as needed. If behavior is documented, add or update doctests/docs accordingly.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit subjects, often with prefixes like `maint:`, `release:`, or concise verbs (`cleanup`, `fix ...`). Keep commits focused and logically separated. PRs should include: a clear problem statement, approach summary, related issue links, and test evidence (exact commands run). Include doc updates when user-facing behavior changes.

## Security & Configuration Tips
Avoid committing local environment artifacts. Use virtual environments for dependency isolation, and prefer optional dependency guards in tests when adding integrations.
