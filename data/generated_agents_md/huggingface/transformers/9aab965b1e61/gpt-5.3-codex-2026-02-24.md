# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `src/transformers/`.
- Model implementations are organized under `src/transformers/models/<model_name>/` (for example, `configuration_*.py`, `modeling_*.py`, `tokenization_*.py`, `processing_*.py`, optional `modular_*.py`).
- Tests are in `tests/` (library behavior) and `examples/` (example scripts and example-focused tests).
- Documentation sources are in `docs/source/`; utility and consistency scripts are in `utils/`; CI/docker assets are in `.circleci/` and `docker/`.

## Build, Test, and Development Commands
- `pip install -e ".[dev]"`: editable install with full contributor dependencies.
- `pip install -e ".[quality]"`: lighter setup for lint/format/check workflows.
- `make fixup`: preferred pre-PR command; runs targeted formatting/lint plus repo consistency checks.
- `make style`: formats and fixes all tracked code paths.
- `make quality`: runs non-mutating quality checks used in CI.
- `make test`: runs the full test suite (`pytest -n auto --dist=loadfile`).
- `python -m pytest -n auto --dist=loadfile -s -v ./tests/<path>`: run focused tests for changed areas.
- `doc-builder build transformers docs/source/en --build_dir ~/tmp/test-build`: validate docs builds when docs change.

## Coding Style & Naming Conventions
- Python style is enforced with `ruff` (format + lint); line length target is 119.
- Use 4-space indentation and double quotes (as formatted by `ruff format`).
- Follow existing naming patterns: snake_case for modules/functions, PascalCase for classes, and descriptive model folder names.
- Docstrings for public methods should follow Google Python Style guidance.

## Testing Guidelines
- Test runner: `pytest` (with `pytest-xdist` for parallelism).
- Add or update tests with every behavior change; place model-specific tests in `tests/models/<model_name>/`.
- Run slow paths when relevant: `RUN_SLOW=yes python -m pytest ...`.
- Keep tests targeted locally before running broader suites.

## Commit & Pull Request Guidelines
- Do not work on `main`; create a descriptive branch name.
- Commit messages should be clear, imperative, and scoped (recent examples: `Fix ...`, `Update ...`, `feat: ...`).
- PRs should include: concise title, linked issue (if applicable), tests for new behavior, and passing `make fixup`/CI checks.
- Prefix draft work with `[WIP]` in the PR title.

## Security & Repository Hygiene
- Avoid committing large binary assets (images/videos/models); host them on Hub/datasets and reference by URL.
- Run `transformers env` when filing bugs to capture environment details accurately.
