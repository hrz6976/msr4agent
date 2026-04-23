# Repository Guidelines

## Project Structure & Module Organization
- `seaborn/`: library source code. Public plotting APIs are in modules like `relational.py`, `categorical.py`, and `distributions.py`; newer object system internals live under `seaborn/_core`, `seaborn/_marks`, and `seaborn/_stats`.
- `tests/`: pytest suite, organized by feature area (e.g., `tests/test_relational.py`, `tests/_core/test_plot.py`).
- `doc/`: Sphinx docs, tutorials, and build tools; see `doc/README.md` for notebook-to-doc workflow.
- `examples/`: runnable example scripts used for gallery-style plots.
- `ci/`: CI helpers (dataset/font setup and gallery checks).

## Build, Test, and Development Commands
- `pip install -e .[dev]`: install seaborn in editable mode with test/lint/type-check tooling.
- `make test`: run full test suite with coverage (`pytest -n auto --cov=seaborn --cov=tests`).
- `make lint`: run `flake8 seaborn`.
- `make typecheck`: run `mypy` on `seaborn/_core`, `seaborn/_marks`, and `seaborn/_stats`.
- `pre-commit install`: enable local pre-commit hooks (`flake8`, `mypy`, whitespace/yaml checks).
- Docs: `pip install -e .[stats,docs] && make -C doc notebooks html`.

## Coding Style & Naming Conventions
- Python style follows `flake8` in `setup.cfg`: max line length `88`; excluded paths include `seaborn/cm.py` and `seaborn/external/`.
- Use 4-space indentation, `snake_case` for functions/variables, `CapWords` for classes, and descriptive test names.
- Keep new modules/tests aligned with existing naming patterns: `seaborn/<topic>.py` and `tests/test_<topic>.py`.

## Testing Guidelines
- Framework: `pytest` with `pytest-xdist` and `pytest-cov`.
- Add/extend tests in the closest topical file or subpackage (`tests/_core`, `tests/_marks`, `tests/_stats`).
- Prefer targeted runs while developing, e.g. `pytest tests/test_distributions.py -k kde`, then run `make test` before opening a PR.

## Commit & Pull Request Guidelines
- Recent history favors short, imperative commit subjects, often with issue links, e.g. `Fix ... (#3136)`, `Add Boolean scale (#3205)`.
- Keep commits focused and atomic; include tests/docs updates when behavior changes.
- PRs should include: concise problem statement, implementation summary, linked issue(s), and before/after visual output for plot-facing changes.
- Ensure `make test`, `make lint`, and `make typecheck` pass before requesting review.
