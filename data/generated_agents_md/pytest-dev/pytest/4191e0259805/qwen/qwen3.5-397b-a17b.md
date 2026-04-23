# AGENTS.md

## Project Overview

This is the source code for `pytest`, a mature and feature-rich testing framework for Python. It is designed to be easy to use for simple tests while also being powerful enough to handle complex functional testing. The project is licensed under the MIT license.

## Building and Running

### Dependencies

The project's dependencies are listed in `setup.cfg`. The main dependencies are:

-   `attrs`
-   `iniconfig`
-   `packaging`
-   `pluggy`
-   `colorama` (for Windows)
-   `exceptiongroup` (for Python < 3.11)
-   `importlib-metadata` (for Python < 3.8)
-   `tomli` (for Python < 3.11)

### Commands

-   **Installation**: The project can be installed using `pip`.
-   **Running Tests**: Tests are run using `tox`. The command `tox -e linting,py37` will run the tests against Python 3.7 and perform linting checks. The configuration in `pyproject.toml` specifies that tests are located in the `testing` directory.

## Development Conventions

-   **Code Style**: The project uses `black` for code formatting and follows PEP-8 for naming. `pre-commit` is used to enforce style guides and code checks.
-   **Testing**: The project uses its own `pytest` framework for testing. The test files are located in the `testing` directory and follow the naming convention `test_*.py`.
-   **Changelog**: The project uses `towncrier` to manage the changelog. A changelog entry should be created for each pull request.
-   **Contributions**: Contributions are welcome. Bugs and feature requests should be submitted to the GitHub issue tracker. Pull requests should be submitted to the `pytest-dev/pytest` repository. Before submitting a pull request, please ensure that the tests pass and that a changelog entry has been created.
