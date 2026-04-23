# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the Hugging Face Transformers library - a model-definition framework for state-of-the-art machine learning models across text, computer vision, audio, video, and multimodal tasks. The library acts as the pivot across frameworks, ensuring model definitions are compatible with training frameworks (Axolotl, Unsloth, DeepSpeed), inference engines (vLLM, SGLang, TGI), and adjacent libraries (llama.cpp, mlx).

The codebase contains 400+ model implementations in `src/transformers/models/`, each typically having configuration, modeling, tokenization, and processing files.

## Development Commands

### Setup
```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or just quality tools if full dev install fails
pip install -e ".[quality]"
```

### Code Quality & Style

```bash
# Fast fixup - only checks modified files on your branch (recommended during development)
make fixup

# Full style check and auto-format all files
make style

# Check code quality without modifying files
make quality

# Check repository consistency (imports, docstrings, copies, etc.)
make repo-consistency

# Fix model copy markers to match original code
make fix-copies

# Get environment info for bug reports
transformers env
# or
python src/transformers/commands/transformers_cli.py env
```

The `make fixup` command is optimized to only work with files modified in your PR - use this during active development. It runs ruff formatting, style checks, and repo consistency checks.

### Testing

```bash
# Run specific test file (always specify a path - don't run all tests!)
python -m pytest -n auto --dist=loadfile -s -v ./tests/models/my_new_model/test_modeling_my_new_model.py

# Run slow tests (downloads models, requires disk space and good connection)
RUN_SLOW=yes python -m pytest -n auto --dist=loadfile -s -v ./tests/models/my_new_model

# Run single test method
python -m pytest -n auto --dist=loadfile -s -v ./tests/models/my_model/test_modeling.py::MyModelTest::test_forward_pass

# Run all library tests (avoid unless necessary - very slow)
make test

# Run example tests
python -m pytest -n auto --dist=loadfile -s -v ./examples/pytorch/text-classification
```

**Important**: Always specify a path to a subfolder or test file. Running all tests takes hours.

### Documentation

```bash
# Install documentation builder
pip install hf-doc-builder

# Build documentation locally (from repository root)
doc-builder build transformers docs/source/en --build_dir ~/tmp/test-build
```

## Architecture & Code Organization

### Source Structure

- **`src/transformers/`**: Core library code
  - **`models/`**: 400+ model implementations, each in its own subdirectory
    - Each model has: `configuration_*.py`, `modeling_*.py`, `tokenization_*.py` (and optionally `*_fast.py`)
    - Configuration classes inherit from `PreTrainedConfig`
    - Model classes inherit from `PreTrainedModel`
  - **`pipelines/`**: High-level inference APIs for common tasks
  - **`generation/`**: Text generation utilities and strategies
  - **`training_args.py`, `trainer.py`**: Training infrastructure
  - **`utils/`**: Utility functions and helper modules
  
- **`tests/`**: Test suite organized to mirror `src/transformers/`
  - `tests/models/<model_name>/` contains tests for each model
  - Use `pytest` with `-n auto --dist=loadfile` for parallel execution
  
- **`examples/`**: Example scripts for common tasks (text classification, QA, etc.)
  - Not guaranteed to work out-of-box; meant as starting points
  
- **`utils/`**: Repository maintenance scripts
  - `check_copies.py`, `check_dummies.py`, `check_repo.py`, etc.
  - These enforce consistency and are run by `make repo-consistency`

### Modular Model Architecture (New Models)

**All new models must use the modular architecture pattern.** Instead of separate files for configuration, modeling, and processing, new models should use a single `modular_<model_name>.py` file that contains all components.

```bash
# Generate modular skeleton for a new model
transformers add-new-model-like <base_model> <new_model_name>

# Verify modular file and generate separate files for backward compatibility
python utils/modular_model_converter.py <model_name>
```

The CI enforces that generated files match the modular file. Modeling code must be in the modular file; configuration should also be included when possible.

Examples of modular files:
- `src/transformers/models/sam2/modular_sam2.py`
- `src/transformers/models/dia/modular_dia.py`

### Vision-Language Model Requirements

When contributing vision-language or multimodal models, you must:

1. **Use modular architecture** (`modular_<model_name>.py`)
2. **Implement fast image processor** (if processing images)
   - Inherit from `BaseImageProcessorFast`
   - Use torch/torchvision instead of PIL/numpy
   - See `LlavaOnevisionImageProcessorFast`, `Idefics2ImageProcessorFast`
3. **Create weight conversion script** (`convert_<model_name>_to_hf.py`)
   - Include usage examples and documentation
4. **Add integration tests with exact output matching**
   - Test end-to-end generation with real checkpoints
   - Use 4-bit or half precision if needed to fit in CI
   - Verify generated text or logits match expected output exactly
5. **Update documentation** (`docs/source/en/model_doc/<model_name>.md`)
6. **Reuse existing patterns** from similar models (LLaVA, Idefics2, Fuyu)
7. **Run `make fixup`** and read its output before submitting

### Key Design Principles

- **Not a modular toolbox**: Model files are intentionally not heavily abstracted - researchers should be able to quickly iterate without diving through multiple abstraction layers
- **Three main classes**: Every model is built from Configuration, Model, and Preprocessor classes
- **Code is duplicated intentionally**: Models share similar code patterns but are kept independent for fast iteration
- **Consistency via scripts**: Repository consistency is maintained through automated checks rather than inheritance
- **Example scripts are examples**: They may need adaptation for your use case

## Git Workflow

```bash
# Create feature branch (never work on main!)
git checkout -b a-descriptive-name-for-my-changes

# Keep your branch updated
git fetch upstream
git rebase upstream/main

# Commit changes
git add modified_file.py
git commit  # Write good commit messages!

# Push to your fork
git push -u origin a-descriptive-name-for-my-changes
```

**Never** work directly on the `main` branch.

## Common Pitfalls

- **Don't skip hooks or signing**: Never use `--no-verify` or `--no-gpg-sign` unless explicitly needed
- **Always specify test paths**: Running `pytest tests/` without a specific path will take hours
- **Read `make fixup` output**: It shows what was fixed and what still needs manual attention
- **Use slow tests appropriately**: `RUN_SLOW=yes` downloads gigabytes of models - only use when testing with real checkpoints
- **Windows development**: Configure git for LF line endings: `git config core.autocrlf input`

## Code Style

- Uses **ruff** for linting and formatting (replaces black and flake8)
- Line length: 119 characters
- Follow Google Python Style Guide for docstrings
- Python 3.9+ required (but target 3.10+)
- PyTorch 2.1+ required

## Testing Philosophy

- Tests use `pytest` but don't rely on pytest-specific features (unittest compatible)
- Fast tests run in CI; slow tests run nightly
- Each model has its own test directory mirroring the source structure
- Integration tests must verify exact output matches, not approximate
- `@slow` decorator for tests requiring model downloads
- `RUN_CUSTOM_TOKENIZERS` environment variable enables custom tokenizer tests

## Environment Variables

- `RUN_SLOW=yes`: Enable slow tests that download models
- `RUN_CUSTOM_TOKENIZERS=yes`: Enable custom tokenizer tests
- `PYTHONPATH=src`: Ensures local checkout is tested, not installed package (set by Makefile)

## PR Checklist

Before submitting a PR:
1. Run `make fixup` and ensure it passes
2. Run tests for your changes: `pytest tests/<path_to_your_test>.py`
3. For new models: verify all files with `python utils/modular_model_converter.py <model_name>` (if using modular architecture)
4. Add tests for new features (slow tests for new models)
5. Write informative docstrings following existing patterns
6. Don't add images/videos to repo - use Hub repositories like `hf-internal-testing`

## Anti-patterns

- ❌ Adding images/large files directly to the repository
- ❌ Using interactive git commands (`git add -i`, `git rebase -i`)
- ❌ Creating abstractions or refactoring beyond what's needed for your task
- ❌ Running tests without specifying a path
- ❌ Working directly on the main branch
- ❌ Force pushing to main/master branches
- ❌ Syncing forks via PR (merge directly to avoid pinging upstream PRs)
