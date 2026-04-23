# Repository Guidelines

## Project Structure & Module Organization
- Core implementation lives in `src/`, with public entry points in `src/pytest/` and internal modules in `src/_pytest/` (for example `src/_pytest/assertion/`, `src/_pytest/config/`).
- Tests live under `testing/`; most new tests should be added close to related behavior (for example `testing/test_runner.py`, `testing/logging/`, `testing/code/`).
- Documentation is in `doc/en/` (Sphinx + `.rst`).
- Changelog fragments go in `changelog/` as individual files.
- Helper and release scripts are in `scripts/`.

## Build, Test, and Development Commands
- `tox -e linting,py37`: run baseline lint + test environments used for local contribution checks.
- `tox -e py37 -- testing/test_config.py`: run a focused test module.
- `tox -e py37 -- --pdb`: pass pytest flags through tox for debugging.
- `tox -e docs`: build docs into `doc/en/_build/html`.
- `tox -e docs-checklinks`: validate documentation links.
- `pre-commit run --all-files`: run formatting/lint hooks without creating a commit.
- Optional direct workflow:
  - `pip install -e ".[testing]"`
  - `pytest testing/test_config.py`

## Coding Style & Naming Conventions
- Follow PEP 8 naming and use 4-space indentation.
- Format Python with Black (configured in pre-commit; target Python 3.7).
- Keep imports ordered via `reorder-python-imports` (pre-commit enforces this).
- Flake8 is enforced (`max-line-length = 120` in `tox.ini`).
- Prefer descriptive test/module names like `test_<feature>.py`.

## Testing Guidelines
- Test framework: `pytest`.
- Discovery and defaults are configured in `pyproject.toml` (`testpaths = ["testing"]`, strict markers, strict xfail).
- Add regression tests with each behavior change.
- For plugin/core behavior, prefer `pytester`-based black-box tests when appropriate.

## Commit & Pull Request Guidelines
- Use concise, imperative commit subjects; include issue/PR references when applicable (e.g. `Fix warning formatting (#1234)`).
- Backport branches may use prefixes like `[7.2.x]`.
- Before opening a PR: run `tox -e linting,py37`, add a changelog fragment `changelog/<issueid>.<type>.rst`, and update docs/tests as needed.
- PRs should explain the user-visible change, link related issues, and include rationale for non-trivial design decisions.
