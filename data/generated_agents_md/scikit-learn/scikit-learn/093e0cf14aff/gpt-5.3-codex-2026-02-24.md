# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `sklearn/` (estimators, metrics, utils, datasets, etc.).
- Unit and doctest-style tests are colocated with modules under `sklearn/**/tests/`.
- Narrative docs and API docs are in `doc/`; runnable examples are in `examples/`.
- Performance benchmarks are in `benchmarks/` and `asv_benchmarks/`.
- Build and maintenance helpers are in `build_tools/` and `maint_tools/`.

## Build, Test, and Development Commands
- `python -m pip install -e .` installs scikit-learn in editable mode.
- `make inplace` builds C/Cython extensions in place (`setup.py build_ext -i`).
- `pytest sklearn` runs the main test suite (configured via `setup.cfg`).
- `make test-code` runs verbose package tests with durations.
- `make test-code-parallel` runs tests in parallel (`pytest -n auto`).
- `make test-coverage` generates coverage HTML under `coverage/`.
- `make doc` builds documentation in `doc/_build/`.

## Coding Style & Naming Conventions
- Python style is enforced with Black (line length 88) and Ruff (`E/F/W/I` rules).
- Run checks with `pre-commit run -a` (Black, Ruff, mypy, cython-lint, whitespace hooks).
- Use 4-space indentation; `snake_case` for functions/variables, `PascalCase` for classes.
- Follow existing estimator conventions in `sklearn/` (public API stability and parameter naming consistency matter).

## Testing Guidelines
- Framework: `pytest` with doctests enabled (`--doctest-modules`).
- Add tests in the nearest `tests/test_*.py` next to changed code.
- Prefer deterministic tests; set `SKLEARN_SEED` when reproducing randomness-sensitive failures.
- For targeted runs, use patterns like `pytest sklearn/metrics/tests/test_pairwise.py -k cosine`.

## Commit & Pull Request Guidelines
- Recent history favors short, prefixed commit subjects: `FIX ...`, `DOC ...`, `MAINT ...`, `TST ...`, `CI ...`, `REL ...`.
- Keep subject lines imperative and concise; reference issues/PRs when relevant (e.g., `(#27616)`).
- PRs should include: problem statement, change summary, test coverage, and doc updates when behavior/API changes.
- Link related issues and include benchmark evidence for performance-impacting changes.

## Security & Configuration Tips
- Review `SECURITY.md` before reporting vulnerabilities.
- Avoid committing generated artifacts, local environments, or secrets; rely on `.pre-commit-config.yaml` and CI checks.
