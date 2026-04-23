# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `src/agents/` (subpackages include `realtime/`, `voice/`, `mcp/`, `memory/`, and `tracing/`).
- Tests mirror package areas under `tests/` (for example, `tests/realtime/`, `tests/voice/`, `tests/mcp/`) with top-level behavioral tests in files like `tests/test_*.py`.
- Runnable samples are in `examples/` (agent patterns, model providers, MCP, voice).
- Documentation source is in `docs/`; site config is in `mkdocs.yml`.

## Build, Test, and Development Commands
- `make sync`: install/update dev environment with all extras via `uv`.
- `make format`: run Ruff formatter and auto-fix lint issues.
- `make lint`: run Ruff lint checks.
- `make mypy`: run strict type checking.
- `make tests`: run full pytest suite.
- `make coverage`: run tests with coverage report (`--fail-under=95`).
- `make check`: run format-check, lint, mypy, and tests (recommended before PR).
- `make build-docs` / `make serve-docs`: build or preview docs locally.

## Coding Style & Naming Conventions
- Target Python `>=3.9`; keep compatibility across supported versions.
- Use Ruff defaults from `pyproject.toml` (`line-length = 100`, import sorting, pyupgrade, bugbear).
- Mypy is configured `strict = true`; prefer explicit types in new/changed code.
- Follow Google-style docstring convention where docstrings are needed.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` (`asyncio_mode = auto`).
- Place tests near related domain (e.g., realtime changes in `tests/realtime/`).
- Name files `test_*.py` and tests `test_*`.
- For snapshot updates, use `make snapshots-fix` (or `make snapshots-create` for new snapshots).
- Validate coverage locally with `make coverage` for significant behavior changes.

## Commit & Pull Request Guidelines
- Follow existing commit style: concise, imperative subjects, often prefixed (`feat:`, `fix:`, `docs:`), and reference issues/PRs like `(#2095)` when applicable.
- Keep commits focused; avoid mixing refactors with behavior changes.
- PRs should include: purpose, user-visible impact, linked issue(s), test evidence (`make check` output summary), and docs/example updates when behavior changes.
- If API behavior changes, add or update examples and relevant docs pages in the same PR.
