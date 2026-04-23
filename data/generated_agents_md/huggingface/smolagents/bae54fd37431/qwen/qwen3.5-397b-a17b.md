# AGENTS.md

## Project Overview

`smolagents` is a Python library for building, running, and sharing AI agents that "think in code." The library is designed with simplicity and extensibility in mind, allowing developers to create powerful agents with minimal code.

**Key Features:**

*   **Code-First Agents:** Agents write their actions as Python code, enabling more complex and flexible tool use.
*   **Model-Agnostic:** Supports any LLM, including local `transformers`, `ollama`, and models from providers like OpenAI, Anthropic, and Hugging Face.
*   **Tool-Agnostic:** Integrates with tools from various sources, including `LangChain` and Hugging Face Hub Spaces.
*   **Sandboxed Execution:** Provides options for secure code execution in sandboxed environments like Docker, E2B, and Blaxel.
*   **Hub Integration:** Facilitates sharing and discovering agents and tools on the Hugging Face Hub.

The core logic is contained in `src/smolagents/`, with examples in the `examples/` directory and tests in `tests/`. The project uses `pyproject.toml` for dependency management and `ruff` for code formatting and linting.

## Building and Running

The project uses a `Makefile` to streamline common development tasks.

*   **Installation:**
    Install the package and its core dependencies using pip. For development, you may want to install with the `[dev]` extras.
    ```bash
    # Basic installation
    pip install .

    # Installation with toolkit dependencies
    pip install ".[toolkit]"

    # Development installation
    pip install -e ".[dev]"
    ```

*   **Running Tests:**
    Tests are run using `pytest`.
    ```bash
    make test
    ```

*   **Code Quality and Formatting:**
    The project uses `ruff` for linting and code formatting.
    ```bash
    # Check code quality (linting and formatting)
    make quality

    # Automatically fix and format code
    make style
    ```

*   **Command-Line Interface (CLI):**
    The package provides two CLI commands, `smolagent` and `webagent`, for running agents directly from the terminal.
    ```bash
    # Example: Run a general-purpose agent
    smolagent "Plan a trip to Tokyo" --model-id "gpt-4"

    # Example: Run a web-browsing agent
    webagent "go to example.com and find the contact email"
    ```

## Development Conventions

*   **Code Style:** The project follows the `ruff` code style. All code should be formatted with `make style` before committing.
*   **Testing:** New features and bug fixes should be accompanied by tests in the `tests/` directory. The testing framework is `pytest`.
*   **Dependencies:** Project dependencies are managed in `pyproject.toml`. Core dependencies are listed under `dependencies`, while optional features and development tools are in `[project.optional-dependencies]`.
*   **Contribution:** Contributions are welcome. Follow the guidelines in `CONTRIBUTING.md`.
