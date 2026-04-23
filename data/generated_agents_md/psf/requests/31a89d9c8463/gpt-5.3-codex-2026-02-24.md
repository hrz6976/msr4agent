# Repository Guidelines

## Project Structure & Module Organization
- `requests/`: core library code (API surface, sessions, adapters, auth, utils, exceptions).
- `tests/`: pytest suite, including integration helpers in `tests/testserver/`.
- `docs/`: Sphinx documentation (`docs/user/`, `docs/community/`, `docs/dev/`).
- `ext/`: project images and branding assets.
- Root config/tooling: `Makefile`, `tox.ini`, `pytest.ini`, `.coveragerc`, `requirements-dev.txt`.

## Build, Test, and Development Commands
- `make init`: install editable package with dev dependencies.
- `make test`: run full tox matrix in parallel (`tox -p`).
- `tox -e py39-default` (example): run one env quickly during local iteration.
- `pytest tests`: run test suite directly.
- `make ci`: run pytest with JUnit XML output (`report.xml`).
- `make flake8`: run style checks for `requests/`.
- `make coverage`: run tests with coverage report for `requests`.
- `make docs`: build Sphinx HTML docs in `docs/_build/html/`.

## Coding Style & Naming Conventions
- Follow PEP 8 with Requests-specific conventions from `docs/dev/contributing.rst`.
- Prefer single-quoted strings (`'value'`) unless escaping would be worse.
- Use hanging indents for wrapped calls/collections; avoid visual-align continuation.
- Keep lines readable; ~100 chars is acceptable when practical.
- Add docstrings for public functions, methods, and classes (dunder methods may be exempt).
- Use `snake_case` for functions/variables, `PascalCase` for classes, and descriptive test names.

## Testing Guidelines
- Framework: `pytest` (configured in `pytest.ini`, including doctest collection).
- Add or update tests with every behavioral change.
- Test files should be named `tests/test_*.py`; test functions should start with `test_`.
- Run `pytest tests` locally before opening a PR; run `make test` for cross-environment confidence.
- No fixed coverage gate is enforced here, but changes should include meaningful coverage.

## Commit & Pull Request Guidelines
- Commit messages in history are short, imperative, and specific (e.g., `Fix auth parsing for proxies`).
- Keep commits focused; avoid mixing refactors with behavior changes.
- Open PRs against `main` with: problem statement, change summary, and test evidence.
- Link relevant issues/PRs and include docs updates when behavior or public guidance changes.
- Ensure all tests pass before requesting review.
