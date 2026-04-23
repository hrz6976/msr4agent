# Repository Guidelines

## Project Structure & Module Organization
- `django/`: Django framework source code (core packages, contrib apps, DB backends).
- `tests/`: Django’s primary test suite and test runner (`tests/runtests.py`).
- `docs/`: Sphinx/reST documentation, including contributor guides in `docs/internals/contributing/`.
- `js_tests/`: JavaScript unit tests (QUnit/Grunt) for admin and contrib JS.
- `scripts/`: project maintenance scripts; `extras/` contains helper assets (for example shell completion).

## Build, Test, and Development Commands
- `python -m pip install -e .` from repo root: install Django in editable mode.
- `python -m pip install -r tests/requirements/py3.txt`: install core Python test deps.
- `cd tests && ./runtests.py`: run full Python suite with bundled SQLite settings.
- `cd tests && ./runtests.py <module_or_test>`: run a subset, e.g. `./runtests.py i18n.tests.TranslationTests`.
- `tox`: run CI-like default checks (tests, `black`, `blacken-docs`, `flake8`, `isort`, docs spelling).
- `tox -e javascript` (or `npm test`): run JavaScript tests.

## Coding Style & Naming Conventions
- Python: 4-space indentation, UTF-8, LF line endings (`.editorconfig`).
- Formatting/lint: `black` (line length 88), `isort` (Black profile), `flake8`.
- Docs (`docs/**/*.txt`) should wrap near 79 chars.
- Test modules typically use `tests.py` or `test_*.py`; keep names descriptive and app-scoped (e.g. `tests/db_functions/comparison/test_cast.py`).
- Run `pre-commit install` once, then commit normally to auto-run hooks.

## Testing Guidelines
- Use Django’s built-in test framework and add regression tests with every code fix.
- Prefer targeted runs during development, then run broader suites before opening a PR.
- For backend-specific work, use `tox` envs (e.g. `tox -e py311-postgres -- --settings=...`).
- Keep tests deterministic and backend-aware; avoid relying on execution order.

## Commit & Pull Request Guidelines
- Non-trivial changes require a Trac ticket; reference it in PR and commit messages.
- Commit format follows Django conventions: `Fixed #xxxxx -- <summary>` or `Refs #xxxxx -- <summary>`.
- Write commit bodies in past tense, with subject + blank line + wrapped body (~72 chars).
- Keep commits logically small; include docs and tests when behavior changes.
- PRs should explain scope, linked ticket, test coverage, and environments used (DB/backend).
