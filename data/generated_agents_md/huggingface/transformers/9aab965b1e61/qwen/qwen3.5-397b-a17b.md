# AGENTS.md

This document provides instructions and context for AI agents interacting with the Hugging Face Transformers repository.

## Project Overview

The Hugging Face Transformers library is a comprehensive, open-source Python framework for state-of-the-art machine learning models. It supports a wide range of tasks across different modalities, including text, computer vision, audio, video, and multimodal applications. The library is designed to be user-friendly, providing a unified API for both inference and training, while also offering deep customization options for researchers and developers.

Key technologies and architectural features include:

- **Modularity**: The project is highly modular, with different functionalities and dependencies organized into optional "extras." This allows users to install only what they need for their specific use case.
- **Framework Interoperability**: Models can be seamlessly used across different deep learning frameworks, including PyTorch.
- **Community-Driven**: The library thrives on community contributions, with a well-documented process for adding new models, fixing bugs, and improving documentation.
- **Testing and Quality**: The project maintains a high standard of code quality through a comprehensive test suite using `pytest`, code formatting with `black` and `ruff`, and a series of consistency checks.

## Building and Running

### Dependencies

The project's dependencies are managed in `setup.py` and can be installed using `pip`. There are several optional dependencies (extras) that can be installed based on the desired functionality.

- **Core Dependencies**: To install the core dependencies, run:
  ```bash
  pip install .
  ```

- **Development Dependencies**: For development, which includes testing and quality checks, install the `dev` extra:
  ```bash
  pip install -e ".[dev]"
  ```

### Running Tests

The project uses `pytest` for its test suite. Tests are located in the `tests/` directory.

- **Run all tests**:
  ```bash
  make test
  ```

- **Run tests for a specific file or directory**:
  ```bash
  pytest tests/models/bert/test_modeling_bert.py
  ```

- **Run slow tests**: Some tests are marked as "slow" and are skipped by default. To run them, set the `RUN_SLOW` environment variable:
  ```bash
  RUN_SLOW=1 pytest tests/
  ```

### Building the Documentation

The documentation is built using `hf-doc-builder`.

- **Install documentation dependencies**:
  ```bash
  pip install hf-doc-builder
  ```

- **Build the documentation**:
  ```bash
  doc-builder build transformers docs/source/en --build_dir ~/tmp/test-build
  ```

## Development Conventions

### Code Style and Quality

The project enforces a strict code style and quality standards using `black` and `ruff`.

- **Check for style and quality issues**:
  ```bash
  make quality
  ```

- **Automatically fix style issues**:
  ```bash
  make style
  ```

- **Run a combination of formatting and consistency checks**:
  ```bash
  make fixup
  ```

### Contributing

Contributions are welcome and follow a structured process outlined in `CONTRIBUTING.md`.

- **Branching**: All work should be done on a new branch, not on `main`.
- **Pull Requests**: Changes are submitted via pull requests, which are reviewed by the maintainers.
- **Commit Messages**: Commit messages should be clear and descriptive.
- **Adding New Models**: There is a detailed guide for adding new models, including a checklist for vision-language models.

### Release Process

The project has a defined release process, managed through scripts and `Makefile` commands.

- **Create a release**: The `make pre-release` and `make post-release` commands are used to prepare for and finalize a release.
- **Build a release**: The `make build-release` command builds the source distribution and wheel for a new release.
