# AGENTS.md

This file provides instructional context about the `openai-agents-python` project, to be used for future interactions.

## Project Overview

This project is the OpenAI Agents SDK for Python, a lightweight and powerful framework for building multi-agent workflows. It is designed to be provider-agnostic, supporting not only the OpenAI APIs but also over 100 other Language Learning Models (LLMs).

The SDK is built around a few core concepts:
- **Agents**: These are the fundamental building blocks, representing LLMs configured with specific instructions, tools, and safety guardrails.
- **Handoffs**: A specialized mechanism that allows one agent to transfer control to another, enabling complex, multi-step workflows.
- **Guardrails**: These are configurable safety checks to validate inputs and outputs, ensuring the agents behave as expected.
- **Sessions**: The SDK provides automatic management of conversation history, making it easy to build conversational agents.
- **Tracing**: Built-in tools for tracking and debugging agent runs, which is crucial for optimizing and understanding complex workflows.

The project is written in Python and uses `pydantic` for data validation and `pytest` for testing. It is configured to be distributed as a PyPI package.

## Building and Running

The project uses `make` to simplify common development tasks. Here are the key commands:

- **Install dependencies**: `make sync`
  - This command uses `uv` to install all necessary dependencies, including optional ones for development.

- **Run tests**: `make tests`
  - This executes the test suite using `pytest`.

- **Linting and Formatting**:
  - `make lint`: Checks the code for style issues using `ruff`.
  - `make format`: Automatically formats the code.
  - `make format-check`: Checks if the code is formatted correctly.

- **Type Checking**: `make mypy`
  - Runs the `mypy` type checker to ensure type safety.

- **All Checks**: `make check`
  - A convenience command that runs formatting checks, linting, type checking, and tests.

- **Build Documentation**: `make build-docs`
  - Generates the project documentation using `mkdocs`.

- **Serve Documentation**: `make serve-docs`
  - Starts a local server to view the documentation.

## Development Conventions

- **Code Style**: The project uses `ruff` for linting and formatting, with a line length of 100 characters. The configuration can be found in `pyproject.toml`.
- **Testing**: Tests are written using `pytest` and are located in the `tests/` directory. The project aims for a high test coverage.
- **Type Hinting**: The codebase uses type hints extensively, and `mypy` is used to enforce type safety.
- **Dependencies**: The project's dependencies are managed in `pyproject.toml`. `uv` is the recommended tool for managing the virtual environment and installing dependencies.
- **Documentation**: The project has extensive documentation in the `docs/` directory, built with `mkdocs`.
