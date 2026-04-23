# Repository Guidelines

## Project Structure & Module Organization
- Core package code lives in `pylint/` (checkers, message handling, CLI entry points).
- Tests live in `tests/`, including checker/unit tests, functional tests, benchmark tests, and primer tooling.
- Documentation is under `doc/` (user guide, contributor guide, generated message docs).
- Helper scripts are in `script/` (for example, changelog and contributor utilities).
- Configuration and tooling are defined in `pyproject.toml`, `tox.ini`, `.pre-commit-config.yaml`, and `pylintrc`.

## Build, Test, and Development Commands
- `python -m tox` runs the default env matrix (formatting + multiple Python test envs where available).
- `python -m tox -e py311 -- -k test_functional` runs a targeted pytest subset in one env.
- `python -m tox -e formatting` runs full pre-commit formatting/lint checks.
- `python -m tox -e pylint` runs pylint against this codebase.
- `python -m tox -e docs` builds Sphinx docs in `doc/_build/html`.
- `python -m pytest tests/` is the fastest local test loop when you do not need tox isolation.

## Coding Style & Naming Conventions
- Python style is enforced by pre-commit hooks: `black`, `isort`, `ruff`, `pydocstringformatter`, and `mypy`.
- Use 4-space indentation and keep line length compatible with project tooling (ruff is configured to 115).
- Follow existing module naming patterns: snake_case file names, descriptive checker names, and message-symbol-oriented test names.
- Run `pre-commit run --all-files` before opening a PR.

## Testing Guidelines
- Test framework: `pytest` with strict markers (`--strict-markers`) and warnings treated as errors.
- Keep/extend tests near the affected area in `tests/`.
- Functional tests should pair a `.py` case with expected output files and inline `# [message-symbol]` annotations.
- For behavior changes, add regression coverage and run targeted tests plus at least one tox env.

## Commit & Pull Request Guidelines
- Prefer short, imperative commit titles (for example: `Fix FP for no-member in decorators`).
- Reference issues/PRs when relevant (for example `(#9453)`).
- Keep changes focused; split unrelated work into separate commits/PRs.
- For non-trivial user-facing changes, add a Towncrier fragment:
  `towncrier create <issue>.<type>` where `<type>` matches `towncrier.toml` categories.
- PRs should explain the problem, the fix, and test coverage; link related issues.
