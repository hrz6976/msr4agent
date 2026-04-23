# Repository Guidelines

## Project Structure & Module Organization
- Core library code lives in `astropy/` with feature subpackages (for example `astropy/io`, `astropy/wcs`, `astropy/table`).
- Tests are colocated under each subpackage as `astropy/<subpkg>/tests/`, plus shared test helpers in `astropy/tests/`.
- Documentation sources are in `docs/` (API, user guides, and developer docs).
- Changelog fragments are stored in `docs/changes/` and subdirectories by subpackage.
- External/vendor code is under `cextern/` and `astropy/extern/`; avoid changing these unless required.

## Build, Test, and Development Commands
- `pip install -e .[test]`: editable install with test dependencies.
- `tox -e test`: run the default test environment in an isolated env.
- `pytest astropy/<subpkg>`: run a focused subpackage test pass during iteration.
- `tox -e codestyle`: run repository style/file checks via pre-commit.
- `pre-commit run --all-files`: run hooks locally before pushing.
- `tox -e build_docs`: build Sphinx docs in `docs/_build/html`.
- `tox -e linkcheck`: validate documentation links.

## Coding Style & Naming Conventions
- Python style follows Black and isort defaults with `line-length = 88`.
- Use 4-space indentation; keep imports grouped and sorted by isort.
- Follow numpydoc docstring conventions for public APIs.
- Test files use `test_*.py`; test functions should be descriptive, e.g., `test_time_scale_conversion_roundtrip`.
- Respect existing package/module naming patterns (`lowercase_with_underscores`).

## Testing Guidelines
- Test framework: `pytest` with Astropy plugins (`pytest-astropy`, doctest-plus, xdist, etc.).
- `setup.cfg` enforces strict settings (warnings as errors, strict xfail, doctest on `.rst`).
- Add regression tests for bug fixes and include doc tests when behavior is documented.
- For optional dependency or remote-data behavior, use the established pytest markers/plugins.

## Commit & Pull Request Guidelines
- Open PRs against `main` from your fork.
- Include code, tests, and documentation updates for user-visible changes.
- Add a changelog fragment: `docs/changes/<subpkg>/<PR>.<type>.rst` where type is `feature`, `api`, `bugfix`, or `other` (root only for `other`).
- Recent history uses short, scoped commit subjects (for example `DOC: ...`, `BUG: ...`, `TST: ...`). Keep commits focused and imperative.
- In PR descriptions, link related issues, summarize impact, and note any follow-up work.
