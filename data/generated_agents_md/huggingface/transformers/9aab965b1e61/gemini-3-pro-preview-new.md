# Project Overview

This directory contains the source code for the Hugging Face `transformers` library, a popular open-source project that provides State-of-the-art Machine Learning for JAX, PyTorch and TensorFlow. The library provides thousands of pretrained models for a wide range of tasks, including natural language processing, computer vision, and audio processing.

The project is written in Python and uses the `ruff` and `black` formatter for code formatting and linting.

# Building and Running

## Installation

To get started with the `transformers` library, you'll first need to install the required dependencies. You can do this by running the following command:

```bash
pip install -e ".[dev]"
```

## Running Tests

The `transformers` library includes an extensive test suite to ensure the quality and correctness of the code. To run the tests, you can use the `pytest` command.

To run all tests, you can use the following command:

```bash
pytest
```

To run a specific test file, you can use the following command:

```bash
pytest tests/models/vit/test_modeling_vit.py
```

# Development Conventions

The `transformers` library follows a set of development conventions to ensure consistency and maintainability of the code.

## Code Style

The project uses the `black` code formatter and `ruff` linter to enforce a consistent code style. Before committing any changes, you should run the following command to format your code:

```bash
make fixup
```

## Branching and Committing

The project follows the standard Gitflow workflow, with a `main` branch for stable releases and feature branches for new development. When contributing to the project, you should create a new branch for your changes and submit a pull request to the `main` branch.

Commit messages should be clear and concise, and should follow the conventional commit format.

## Contribution Guidelines

The `CONTRIBUTING.md` file provides detailed guidelines for contributing to the project, including how to submit bug reports, feature requests, and pull requests. Before contributing, you should read this file carefully to ensure that your contributions align with the project's standards and conventions.
