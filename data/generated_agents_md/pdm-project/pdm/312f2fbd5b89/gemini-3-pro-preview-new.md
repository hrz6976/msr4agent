
# Project Overview

This project is **PDM**, a modern Python package and dependency manager. It aims to provide a next-generation tool for managing Python packages, supporting the latest PEP standards. PDM can manage virtual environments, resolve dependencies, build packages, and publish them to PyPI. It uses `pyproject.toml` for project metadata and offers a flexible plugin system.

**Key Technologies:**

*   **Language:** Python
*   **Package Management:** PDM itself
*   **Build Backend:** `pdm-backend`
*   **Testing:** pytest, tox
*   **Linting:** ruff, pre-commit

## Building and Running

### Development Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install PDM in editable mode:**
    ```bash
    pip install -e .
    ```

3.  **Install development dependencies:**
    ```bash
    pdm install
    ```

### Running Tests

*   **Run the full test suite:**
    ```bash
    pdm run test
    ```
    or
    ```bash
    tox
    ```

*   **Run tests in parallel:**
    ```bash
    pdm run test -n auto
    ```

### Running the Linter

```bash
pdm run lint
```

## Development Conventions

*   **Branching:** Create new branches for features and bugfixes. Do not commit directly to `main`.
*   **Code Style:** The project uses `ruff` for formatting and linting. Pre-commit hooks are configured to enforce the style.
*   **Commits:** No specific convention is mentioned, but it's good practice to write clear and descriptive commit messages.
*   **Pull Requests:** Pull requests should be created from feature branches.
*   **Changelog:** For any user-facing changes, add a "news fragment" in the `news/` directory. The filename should follow the format `<issue_num>.<type>.md` (e.g., `123.feature.md`).
