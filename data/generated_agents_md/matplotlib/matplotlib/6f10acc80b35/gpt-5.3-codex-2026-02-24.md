# Repository Guidelines

## Project Structure & Module Organization
Core library code lives under `lib/`, mainly `lib/matplotlib/` and `lib/mpl_toolkits/`.  
Tests are colocated in `lib/matplotlib/tests/` (plus toolkit test modules).  
Documentation sources are in `doc/` (`doc/users/`, `doc/devel/`, `doc/api/`), while runnable gallery/tutorial inputs are in `examples/`, `tutorials/`, and `plot_types/`.  
Build and CI helpers are in `ci/`, `tools/`, and top-level config files such as `pyproject.toml`, `pytest.ini`, `tox.ini`, and `.pre-commit-config.yaml`.

## Build, Test, and Development Commands
Set up a dev install (rebuild after C-extension changes):
```bash
python -m pip install -ve .
```
Run the full test suite:
```bash
python -m pytest
```
Run a targeted test:
```bash
pytest lib/matplotlib/tests/test_simplification.py::test_clipping
```
Run tox environments (multi-Python regression checks):
```bash
tox -e py310
```
Run local hooks before committing:
```bash
pre-commit run --all-files
```
Build docs locally:
```bash
cd doc && make html
```

## Coding Style & Naming Conventions
Follow PEP 8 with Matplotlib’s exceptions: max line length is **88** (`.flake8`).  
Use `flake8` and pre-commit hooks; this project intentionally does **not** use `black`.  
Test file naming follows pytest discovery in `pytest.ini`: `test_*.py`; test functions should start with `test_`.  
Prefer standard scientific aliases (`import numpy as np`, `import matplotlib.pyplot as plt`).

## Testing Guidelines
Testing uses `pytest`. Keep tests deterministic (seed random generators explicitly).  
For image comparisons, use Matplotlib testing decorators and add/update baseline images in the corresponding `baseline_images/` tree when required.  
Before opening a PR, run the focused tests for your change and at least one broader pass (`python -m pytest` or `tox` target).

## Commit & Pull Request Guidelines
Recent history favors short, prefixed commit subjects like `DOC: ...`, `TST: ...`, `BLD: ...`, `REL: ...`, and concise maintenance messages.  
Keep subjects imperative and specific; group related changes per commit.  
PRs should target `main`, link issues (`Fixes #12345`), include tests, and include docs updates for user-facing/API changes (for major features, add `doc/users/next_whats_new/` entries).
