# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `src/fastmcp/` (major areas: `server/`, `client/`, `cli/`, `utilities/`, `contrib/`, `experimental/`).
- Tests live in `tests/` and generally mirror `src/` paths (for example, server auth logic is covered under `tests/server/auth/`).
- Documentation source is in `docs/` (`.mdx` pages plus assets), and runnable examples are in `examples/`.
- Automation scripts are in `scripts/`; short project task aliases are defined in `justfile`.

## Build, Test, and Development Commands
- `uv sync`: install project and dev dependencies.
- `just build`: sync dependencies (wrapper around `uv sync`).
- `just test` or `uv run --frozen pytest -xvs tests`: run test suite.
- `uv run pytest -m "not integration and not client_process"`: faster local pass while skipping slow/special tests.
- `uv run prek run --all-files`: run pre-commit checks (Ruff, Prettier, ty, etc.).
- `just typecheck`: run static typing checks with `ty`.
- `just docs`: serve docs locally from `docs/`.

## Coding Style & Naming Conventions
- Target Python `>=3.10`; keep full type annotations on public and internal functions.
- Use Ruff for linting/formatting (`ruff-check` + `ruff-format` in pre-commit).
- Follow existing naming: `snake_case` for functions/modules, `PascalCase` for classes, `test_*.py` for tests.
- Prefer explicit, descriptive names and specific exception handling; avoid bare `except`.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio`; tests should be isolated and self-contained.
- Mark long/external tests with existing markers (`integration`, `client_process`) and filter locally when needed.
- Keep one behavior per test and mirror source layout for discoverability.
- Snapshot-style assertions use `inline-snapshot` when validating complex schemas.

## Commit & Pull Request Guidelines
- Open/confirm an issue before submitting code; PRs are expected to map to an issue.
- Keep PRs small and scoped to one feature/fix.
- Commit messages in this repo are concise, imperative, and often reference PR numbers, e.g. `Fix OAuth token storage TTL calculation (#2796)`.
- Before opening a PR, run `uv run prek run --all-files && uv run pytest` and update docs for behavior/API changes.
- PR descriptions should explain the problem, approach, and trade-offs; include migration notes for breaking changes.

## Security & Configuration Tips
- Review `SECURITY.md` for reporting expectations.
- Use test-mode env defaults in `pyproject.toml`/pytest config; never commit real secrets or tokens.
