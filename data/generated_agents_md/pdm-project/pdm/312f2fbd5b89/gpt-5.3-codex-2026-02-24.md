# Repository Guidelines

## Project Structure & Module Organization
- Core source code lives in `src/pdm/` (CLI in `src/pdm/cli/`, resolver in `src/pdm/resolver/`, installers in `src/pdm/installers/`).
- Tests are under `tests/` and mirror major modules (`tests/cli/`, `tests/models/`, `tests/resolver/`).
- Documentation is in `docs/`; site config is `mkdocs.yml`.
- Changelog fragments go in `news/` and are compiled into `CHANGELOG.md`.
- Utility/release scripts are in `tasks/`.

## Build, Test, and Development Commands
- `pdm install`: install project and dev dependency groups.
- `pdm run test`: run the pytest suite.
- `pdm run test -n auto`: run tests in parallel via `pytest-xdist`.
- `pdm run coverage`: run tests with branch coverage for `src/pdm`.
- `tox`: run the test matrix for Python 3.9-3.13.
- `pdm build`: build distribution artifacts.
- `pdm run release --dry-run`: preview release/changelog generation.

## Coding Style & Naming Conventions
- Python style is enforced with Ruff (`ruff` + `ruff-format`), line length `120`.
- Use 4-space indentation and type hints for new or modified code.
- Mypy is enabled for `src/`; avoid introducing untyped defs in typed modules.
- Keep module and function names `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Run pre-commit hooks before opening a PR.

## Testing Guidelines
- Framework: `pytest` with markers configured in `pyproject.toml` (for example `network`, `integration`, `uv`).
- Keep tests close to changed behavior and follow `test_*.py` naming.
- Prefer targeted runs during development (example: `pdm run test tests/cli/test_add.py`).
- Coverage is branch-aware; add tests for new code paths and regressions.

## Commit & Pull Request Guidelines
- Follow the Conventional Commit style used in history: `fix: ...`, `feat: ...`, `docs: ...`, `chore: ...`.
- Reference issues/PRs when relevant (example: `fix: handle lock edge case (#1234)`).
- PRs should include a clear summary, rationale, tests, and doc updates when behavior changes.
- Add a news fragment in `news/` named `<issue>.<type>.md` (for example `3695.bugfix.md`).
- Use fragment types defined by the project: `feature`, `bugfix`, `doc`, `dep`, `removal`, `misc`.

## Security & Configuration Tips
- Do not commit secrets or machine-local config; prefer environment variables for credentials.
- For docs work, run `pdm run doc` locally before submitting changes touching `docs/`.
