# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `tinygrad/` (tensor API, engine, codegen, runtime backends, and nn helpers). Prioritize changes here.
- Tests live in `test/` with focused suites in `test/unit/`, `test/device/`, `test/models/`, and long-running/integration coverage in `test/external/`.
- User-facing examples are in `examples/`; experimental/support code is in `extra/` (less strictly tested).
- Docs source is in `docs/` and built with MkDocs.

## Build, Test, and Development Commands
- `python3 -m pip install -e '.[testing]'`: install editable package + test deps.
- `python3 -m pip install -e '.[linting]'`: install lint/type-check tooling.
- `pre-commit install`: enable local hooks (ruff, mypy, and selected tests).
- `python3 -m ruff check .`: run lint checks.
- `python3 -m mypy`: run static type checks for `tinygrad/`.
- `python3 -m pytest test/`: run full test suite.
- `python3 test/test_ops.py` or `python3 -m pytest test/test_tensor.py`: run targeted tests during iteration.

## Coding Style & Naming Conventions
- Python 3.11+.
- Ruff config enforces **2-space indentation** and max line length 150.
- Keep code simple and readable; avoid “code golf” even when reducing lines.
- Match existing naming patterns: `snake_case` for functions/variables, `PascalCase` for classes, test files as `test_*.py`.
- Prefer small, clear diffs in core paths (`tinygrad/`) over broad refactors.

## Testing Guidelines
- Use `pytest` (with `pytest-xdist`, `hypothesis`, timeout settings from `pyproject.toml`).
- Every bug fix or feature should include a regression test in the nearest relevant suite (often `test/` or `test/unit/`).
- For backend/device-specific behavior, place tests under `test/device/` or `test/external/` and gate appropriately.

## Commit & Pull Request Guidelines
- Follow existing commit style: concise imperative subject, often scoped (for example, `am: rework set_clocks`) and optionally issue-linked (`(#14065)`).
- PRs should explain **what changed, why, and how it was tested**; include benchmark evidence for speedup claims.
- Keep PRs small and clear. Large/complex diffs are less likely to be reviewed.
- For refactors/speedups with no behavior change, include `[pr]` in the PR title and run process replay tests.
