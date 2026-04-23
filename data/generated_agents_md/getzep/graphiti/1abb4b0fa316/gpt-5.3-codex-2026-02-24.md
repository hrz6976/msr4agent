# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `graphiti_core/` (drivers, LLM clients, embedders, search, models, prompts, and maintenance utilities).
- Tests live in `tests/`, organized by feature area (`tests/llm_client/`, `tests/embedder/`, `tests/driver/`, `tests/evals/`).
- Service layers are separate: `server/` (FastAPI REST service) and `mcp_server/` (MCP server).
- Runnable examples and sample data are in `examples/`; static project images are in `images/`.

## Build, Test, and Development Commands
- `make install`: install dev dependencies with `uv sync --extra dev`.
- `make format`: run Ruff import sorting and formatting.
- `make lint`: run Ruff lint checks and Pyright type checks.
- `make test`: run the full pytest suite.
- `make check`: run format + lint + test before opening a PR.
- Service-specific workflow:
  - `cd server && make check`
  - `cd mcp_server && uv run graphiti_mcp_server.py`

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indentation, max line length 100.
- Ruff enforces style and formatting; configured quote style is single quotes.
- Keep module names snake_case (`openai_client.py`), classes PascalCase, functions/variables snake_case.
- For optional integrations, follow existing TYPE_CHECKING + guarded import pattern used in `graphiti_core/llm_client/` and `graphiti_core/embedder/`.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio`.
- Name test files `test_*.py`; use `_int.py` suffix for integration tests requiring external services.
- Use `@pytest.mark.integration` for integration cases.
- Run targeted tests during development, e.g. `uv run pytest tests/llm_client/test_client.py`.
- For integration runs, set required env vars (for example `TEST_OPENAI_API_KEY`, `TEST_URI`, `TEST_USER`, `TEST_PASSWORD`).

## Commit & Pull Request Guidelines
- Use concise, imperative commit messages; include issue/PR refs when applicable (example: `Fix search config handling (#829)`).
- Keep changes focused; open an RFC issue before large architectural changes (roughly >500 LOC).
- PRs should include: clear description, linked issues, test coverage for behavior changes, and doc updates when APIs or workflows change.
- Run `make check` (and service-specific checks if touched) before requesting review.

## Security & Configuration Tips
- Copy `.env.example` for local setup; never commit secrets.
- Prefer lowering `SEMAPHORE_LIMIT` first when hitting LLM provider `429` rate limits during ingestion.
