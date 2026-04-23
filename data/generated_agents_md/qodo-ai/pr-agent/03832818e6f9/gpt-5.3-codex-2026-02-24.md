# Repository Guidelines

## Project Structure & Module Organization
- Core code lives in `pr_agent/`.
- `pr_agent/tools/` contains user-facing PR tools (`review`, `describe`, `improve`, `ask`, etc.).
- `pr_agent/git_providers/` contains provider integrations (GitHub, GitLab, Bitbucket, Azure DevOps, Gitea, Gerrit).
- `pr_agent/servers/` contains webhook/action/server entry points.
- `pr_agent/algo/` contains processing logic, token handling, and AI handlers.
- `pr_agent/settings/` contains TOML configuration and prompt templates.
- Tests live in `tests/unittest/`, `tests/e2e_tests/`, and `tests/health_test/`.
- Documentation source is under `docs/docs/` (MkDocs config: `docs/mkdocs.yml`).

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local environment.
- `pip install -r requirements.txt -r requirements-dev.txt`: install runtime and dev dependencies.
- `pip install -e .`: install the package in editable mode.
- `pytest tests/unittest`: run unit tests.
- `pytest tests/e2e_tests`: run e2e/integration tests (requires provider credentials/env vars).
- `python -m tests.health_test.main`: run health checks used by automation.
- `pre-commit run --all-files`: run configured hooks (file hygiene + isort).

## Coding Style & Naming Conventions
- Target Python is 3.12+ (`pyproject.toml`).
- Use 4-space indentation and keep lines at or under 120 characters.
- Import ordering is enforced with isort (`I001`, `I002` in Ruff lint config).
- Use `snake_case` for functions/modules, `PascalCase` for classes, and descriptive test files like `test_<behavior>.py`.
- Run `pre-commit` before pushing to catch formatting/import issues early.

## Testing Guidelines
- Use `pytest`; async tests are supported where needed.
- Add or update unit tests for each behavior change in `tests/unittest/`.
- Keep e2e tests focused on provider/server flows and mock external calls when possible.
- `codecov.yml` does not enforce strict coverage gates, but changes should preserve or improve practical coverage.

## Commit & Pull Request Guidelines
- Follow Conventional Commits used in history: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Keep commits focused and atomic; include a clear scope when possible.
- PRs should include a concise summary, linked issue/ticket when relevant, test evidence (commands run), and docs/config updates when behavior changes.
