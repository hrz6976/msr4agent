# Repository Guidelines

## Project Structure & Module Organization
Core library code lives in `src/smolagents/` (agents, tools, models, CLI, executors).  
Tests are under `tests/`, with shared fixtures in `tests/fixtures/` and test helpers in `tests/utils/`.  
Documentation sources are in `docs/source/<lang>/` (`en`, `zh`, `ko`, `es`, `hi`), and runnable examples are in `examples/` (including subprojects like `open_deep_research/` and `async_agent/`).

## Build, Test, and Development Commands
- `pip install -e ".[dev]"`: install editable package with lint/test dependencies.
- `make quality`: run lint and formatting checks (`ruff check` + `ruff format --check`) on `examples/`, `src/`, and `tests/`.
- `make style`: auto-fix lint issues and format code with Ruff.
- `make test`: run full pytest suite (`pytest ./tests/`).
- `pytest tests/test_agents.py -k <pattern>`: run a focused subset while iterating.
- `doc-builder preview smolagents docs/source/en/`: preview docs locally (after installing `hf-doc-builder`).

## Coding Style & Naming Conventions
Target Python 3.10+ and keep code Ruff-clean.  
Ruff settings are defined in `pyproject.toml` (line length 119, import sorting enabled, first-party package `smolagents`).  
Use:
- `snake_case` for functions, variables, and test files (`test_<feature>.py`)
- `PascalCase` for classes
- clear module names aligned with features (`remote_executors.py`, `tool_validation.py`)

Run `make style` before committing. Pre-commit config also runs Ruff and basic YAML/merge checks.

## Testing Guidelines
Framework: `pytest` with verbosity/duration reporting (`-sv --durations=0`).  
Add unit tests in `tests/` close to the affected module, and name tests `test_<behavior>`.  
Some tests are environment-gated (for example `RUN_ALL`, optional deps like `torch`/`soundfile`), so document any required env vars in PR notes.

## Commit & Pull Request Guidelines
Follow the repository’s commit style seen in history: short, imperative subjects (e.g., `fix(gradio_ui): ...`, `Add ...`, `Upgrade ...`).  
Prefer focused commits per logical change.  
For PRs, include:
- concise problem/solution description
- linked issue(s) when applicable
- tests added/updated and command(s) run
- docs/example updates when behavior or APIs change

If changing user-facing behavior, include a minimal usage snippet or CLI example in the PR description.
