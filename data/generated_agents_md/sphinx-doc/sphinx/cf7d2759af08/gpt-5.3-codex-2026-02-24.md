# Repository Guidelines

## Project Structure & Module Organization
- `sphinx/`: core Python package (builders, domains, extensions, CLI commands).
- `tests/`: pytest suite (`test_*.py`) plus fixture projects under `tests/roots/`.
- `doc/`: Sphinx’s own documentation sources (`.rst`) and theme/static assets.
- `utils/`: maintenance helpers (for example, translation tooling).
- Root config files: `pyproject.toml`, `tox.ini`, `.flake8`, `Makefile`, `karma.conf.js`.

Keep feature code in `sphinx/`, behavior/regression coverage in `tests/`, and user/developer docs in `doc/`.

## Build, Test, and Development Commands
- `make test`: run Python tests with development warnings enabled.
- `make style-check`: run `flake8`.
- `make type-check`: run `mypy sphinx`.
- `make doclinter`: lint reStructuredText (`sphinx-lint`).
- `tox -e py310` (or `py39`, `py311`, etc.): run tests in a pinned environment.
- `tox -e docs`: build docs with warnings treated as errors.
- `make docs target=html`: build docs via `doc/Makefile`.
- `npm install && npm run test`: run JavaScript tests with Karma/Firefox.

## Coding Style & Naming Conventions
- Python: 4-space indentation, max line length 95 (see `.flake8`/Ruff config).
- Follow existing local style; prefer small, focused changes.
- Test files use `tests/test_*.py`; test functions use `test_*`.
- For non-trivial behavior changes, add a short entry to `CHANGES`.
- Run `ruff .` and `mypy sphinx/` before opening a PR.

## Testing Guidelines
- Frameworks: `pytest` (Python) and Karma/Jasmine (JavaScript).
- Add or update tests for every bug fix/feature; prefer minimal reproductions.
- Reuse `sphinx.testing` fixtures and existing `tests/roots/*` projects when possible.
- Useful targeted run: `tox -e py311 -- tests/test_build_html.py::test_case_name`.

## Commit & Pull Request Guidelines
- Base work on the appropriate branch (`A.x` for backward-compatible changes; `master` for larger/incompatible work).
- Commit messages are short, imperative, and often reference issues (examples from history: `Fix ... (#11634)`, `Bump to 7.2.6 final`).
- Preferred pattern: `Closes #1234: <brief description>`.
- PRs should include: problem statement, change summary, tests added/updated, and docs/`CHANGES` updates when applicable.
- Link related GitHub issues and note any follow-up work explicitly.
