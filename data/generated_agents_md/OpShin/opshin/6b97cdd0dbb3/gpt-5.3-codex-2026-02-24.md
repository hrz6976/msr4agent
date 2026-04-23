# Repository Guidelines

## Project Structure & Module Organization
- `opshin/`: core compiler and language implementation.
- Key subpackages: `rewrite/` (AST rewriting passes), `optimize/` (optimization passes), `ledger/` (ledger APIs), `std/` (stdlib for contracts).
- `tests/`: pytest suite, organized by feature area (for example `tests/test_rewrite/`, `tests/test_optimize/`, `tests/test_ledger/`).
- `examples/`: runnable contract and language examples, including `examples/smart_contracts/`.
- `scripts/`: utility tooling (artifact conversion, binary-size checks/tracking).
- `docs/`: generated and template-based documentation assets.

## Build, Test, and Development Commands
- `poetry install`: install runtime and dev dependencies.
- `poetry run pytest`: run the full test suite.
- `poetry run pytest tests/test_rewrite -q`: run a focused subset while iterating.
- `poetry run coverage run -m pytest && poetry run coverage report`: run tests with coverage.
- `poetry run black opshin tests`: format code.
- `poetry run pre-commit run --all-files`: run configured hooks before pushing.
- `./build_docs.sh`: regenerate API/docs pages and binary-size trend page inputs.
- `poetry run python scripts/check_binary_sizes.py`: check binary-size regressions.

## Coding Style & Naming Conventions
- Python only; follow Black defaults (4-space indentation, Black-managed line length/format).
- Use `snake_case` for modules/functions/variables; classes use `PascalCase`; constants use `UPPER_SNAKE_CASE`.
- Prefer descriptive module names for passes (pattern: `rewrite_<purpose>.py`, `optimize_<purpose>.py`).
- Keep changes small and pass-oriented: one semantic rewrite/optimization concern per module when possible.

## Testing Guidelines
- Framework: `pytest` (with `hypothesis` available for property-style tests).
- Add tests in the matching domain folder, and name files/functions `test_*.py` / `test_*`.
- Include regression tests for compiler rewrites/optimizations and ledger/API behavior changed by your patch.
- Run targeted tests locally first, then `poetry run pytest` before opening a PR.

## Commit & Pull Request Guidelines
- Recent history favors short, imperative commit subjects (for example: `Fix compilation`, `Increase recursion limit`).
- Keep commit titles concise, present tense, and scoped to one change.
- PRs should include: problem statement, approach summary, test evidence (commands run), and any compatibility/perf impact.
- Link related issues; include artifact/output snippets when behavior or generated artifacts change.
