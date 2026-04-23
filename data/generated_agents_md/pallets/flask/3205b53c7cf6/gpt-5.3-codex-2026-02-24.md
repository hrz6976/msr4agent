# Repository Guidelines

## Project Structure & Module Organization
Flask uses a `src` layout. Core framework code lives in `src/flask/` (for example `app.py`, `cli.py`, `templating.py`, and JSON helpers under `src/flask/json/`).

Tests are in `tests/` and follow module-focused files such as `test_cli.py` and `test_templating.py`, with fixtures in `tests/conftest.py` and sample apps in `tests/test_apps/`.

Documentation is in `docs/` (Sphinx), dependency pins are in `requirements/`, and runnable examples are in `examples/`.

## Build, Test, and Development Commands
- `python -m venv .venv && . .venv/bin/activate`: create and activate a local virtualenv.
- `pip install -r requirements/dev.txt && pip install -e .`: install dev tools and editable Flask.
- `pytest`: run the default test suite (`tests/`).
- `tox`: run full multi-env checks (Py versions, style, typing, docs).
- `tox -e style`: run pre-commit style/lint checks across all files.
- `tox -e typing`: run `mypy` on `src/flask`.
- `tox -e docs` or `cd docs && make html`: build docs with warnings treated as errors.

## Coding Style & Naming Conventions
Use 4-space indentation for Python and 2 spaces for YAML/JSON/CSS/HTML (`.editorconfig`). Keep Python formatting Black-compatible (88-char style); Flake8 with bugbear is enforced via pre-commit.

Naming patterns:
- modules/functions: `snake_case`
- classes: `CapWords`
- tests: `test_*.py`, with descriptive `test_*` function names.

Run `pre-commit install --install-hooks` once, then `pre-commit run --all-files` before opening a PR.

## Testing Guidelines
Use `pytest` for all tests. Add or update tests for every behavior change, and ensure the test fails before your fix and passes after it. Keep tests near related coverage in `tests/` (for example, CLI changes in `tests/test_cli.py`).

For coverage checks:
- `coverage run -m pytest`
- `coverage html` (report in `htmlcov/index.html`).

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit subjects (for example, `fix flake8 bugbear findings`, `cleanup`) and optional issue/PR references like `(#5217)`.

For pull requests:
- link the issue (`fixes #123` when applicable)
- include tests and relevant docs/docstring updates
- add an entry to `CHANGES.rst`
- keep CI clean (`pytest` locally at minimum; `tox` preferred)
- provide clear scope and rationale in the PR description.
