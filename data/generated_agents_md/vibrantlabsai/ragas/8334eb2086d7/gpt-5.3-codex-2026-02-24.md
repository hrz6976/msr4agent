# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `src/ragas/` (metrics, testset generation, integrations, prompts, CLI, backends).
- Tests are in `tests/`:
  - `tests/unit/` for fast unit coverage
  - `tests/e2e/` for integration/end-to-end behavior
  - `tests/benchmarks/` for performance scripts
- Documentation sources are in `docs/` (MkDocs), and runnable examples are in `examples/`.
- Build and tooling configuration is centralized in `pyproject.toml` and `Makefile`.

## Build, Test, and Development Commands
- `make install-minimal`: set up a fast dev environment with essential tooling.
- `make install`: full environment via `uv sync --group dev`.
- `make format`: run Ruff format + lint autofixes + final lint check.
- `make type`: run Pyright type checks on `src/`.
- `make test`: run unit tests.
- `make test-e2e`: run end-to-end tests.
- `make run-ci`: local CI parity (format/type/tests).
- `make build-docs` / `make serve-docs`: build or serve docs locally.

## Coding Style & Naming Conventions
- Python 3.9+ target; line length `88` (Ruff).
- Use 4-space indentation, double quotes, and sorted imports (enforced by Ruff).
- Prefer explicit, typed APIs; Pyright runs in `basic` mode.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep public API changes synchronized with docs and examples when relevant.

## Testing Guidelines
- Framework: `pytest` (with `pytest-asyncio`, `pytest-xdist`, and `nbmake` for notebook tests).
- Place tests under the matching domain in `tests/unit/` or `tests/e2e/`.
- Test files should be named `test_*.py`; test functions should start with `test_`.
- Useful patterns:
  - `make test`
  - `uv run pytest tests/unit -k "keyword"`
  - `make test-all` (includes notebook checks)

## Commit & Pull Request Guidelines
- Follow Conventional Commit style seen in history: `feat:`, `fix:`, `docs:`, `chore:`; scopes are encouraged (e.g., `feat(docs): ...`).
- Keep commits focused and descriptive.
- Before opening a PR, run `make run-ci` and ensure checks pass.
- PRs should include: clear summary, rationale, linked issues, and updates to tests/docs for behavior changes.

## Security & Configuration Tips
- Do not commit secrets; use environment variables (e.g., `OPENAI_API_KEY`).
- For privacy, set `RAGAS_DO_NOT_TRACK=true` when needed.
- Review `SECURITY.md` for vulnerability reporting and handling.
