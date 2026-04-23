# AGENTS.md

This file provides a comprehensive guide for agents interacting with the PDM (Python Development Master) repository.

## Project Overview

PDM is a modern Python package and dependency manager that supports the latest PEP standards. It aims to provide a fast and simple dependency resolver, a PEP 517 build backend, and support for PEP 621 project metadata.

**Key Technologies:**

*   **Programming Language:** Python
*   **Package Management:** PDM itself
*   **Build System:** `pdm-backend`
*   **Testing:** `pytest`, `tox`
*   **Linting and Formatting:** `ruff`, `codespell`
*   **Documentation:** `mkdocs`

**Architectural Highlights:**

*   **Modular Design:** PDM is designed with a flexible plugin system, allowing for extensibility.
*   **Standard Compliance:** It adheres to modern Python standards, including PEP 517 (build systems), PEP 621 (project metadata), and PEP 582 (local package directory).
*   **Virtual Environment Management:** PDM can manage virtual environments in both a project-local and a centralized manner.
*   **Dependency Resolution:** It features a fast dependency resolver and uses a `pdm.lock` file to ensure deterministic builds.

## Building and Running the Project

The project uses a set of scripts and tools defined in `pyproject.toml` for building, testing, and documentation.

**Key Commands:**

*   **Install Dependencies:**
    ```bash
    pdm install
    ```
*   **Run Tests:**
    ```bash
    pdm run test
    ```
*   **Run Tests with Coverage:**
    ```bash
    pdm run coverage
    ```
*   **Run Tests across Multiple Python Versions:**
    ```bash
    pdm run tox
    ```
*   **Run Linters:**
    ```bash
    pdm run lint
    ```
*   **Build Documentation:**
    ```bash
    pdm run doc
    ```

## Development Conventions

The repository follows a set of conventions to ensure code quality and consistency.

*   **Code Style:** The project uses `ruff` for linting and formatting. The configuration can be found in the `[tool.ruff]` section of `pyproject.toml`.
*   **Testing:**
    *   Tests are located in the `tests/` directory and are written using `pytest`.
    *   The test setup is configured in the `[tool.pytest.ini_options]` section of `pyproject.toml`.
    *   `tox` is used for running tests in isolated environments against different Python versions, as defined in `tox.ini`.
*   **Commit Messages:** While not explicitly defined in the provided files, a `towncrier` configuration in `pyproject.toml` suggests that the project follows a structured approach to changelog generation based on commit messages.
*   **Documentation:**
    *   The documentation is built using `mkdocs` with the `material` theme.
    *   The structure of the documentation is defined in the `nav` section of `mkdocs.yml`.
    *   Docstrings are written in Google style, as configured in the `[tool.mkdocstrings]` section.
*   **Dependency Management:** All project dependencies are managed through PDM and are defined in `pyproject.toml`. The `pdm.lock` file ensures that dependency resolution is consistent across different environments.
*   **Pre-commit Hooks:** The `.pre-commit-config.yaml` and `.pre-commit-hooks.yaml` files indicate that the project uses pre-commit hooks to enforce code quality standards before commits are made.
