# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sphinx is a documentation generator that converts reStructuredText files into HTML, PDF, EPUB, and other formats. It is widely used for Python documentation and includes extensive cross-referencing, automatic indexing, code highlighting, and a rich extension ecosystem.

## Development Setup

Install in editable mode with test dependencies:
```bash
pip install -e .
pip install -e .[test]
```

For linting and type checking:
```bash
pip install -e .[lint]
```

## Common Commands

### Testing

Run all tests with pytest:
```bash
pytest -v
```

Run a specific test file:
```bash
pytest tests/test_application.py -v
```

Run a specific test function:
```bash
pytest tests/test_application.py::test_events -v
```

Run tests using tox (tests across multiple Python versions):
```bash
tox -av  # List all environments
tox -e py310  # Run tests on Python 3.10
tox -e py312  # Run tests on Python 3.12
```

Run tests with coverage:
```bash
pytest --cov=sphinx --junitxml=.junit.xml -v
```

### Code Quality

Run style checks (using ruff and flake8):
```bash
make style-check
# or
flake8
ruff check .
```

Run type checks:
```bash
make type-check
# or
mypy sphinx/
```

Run documentation linter:
```bash
make doclinter
```

Run all checks (style, type, and tests):
```bash
make all
```

### JavaScript Tests

Run JavaScript tests for frontend components:
```bash
npm install
npm run test
```

### Building Documentation

Build Sphinx's own documentation:
```bash
make docs target=html
# or directly with tox
tox -e docs
```

Live documentation rebuild on changes:
```bash
tox -e docs-live
```

### Cleaning

Clean all generated files:
```bash
make clean
```

## Architecture

### Core Components

- **sphinx/application.py**: Central `Sphinx` application class that coordinates the build process and manages the extension system. Entry point for all Sphinx functionality.

- **sphinx/builders/**: Output format builders (HTML, LaTeX, EPUB, text, etc.). Each builder subclasses `Builder` and implements format-specific rendering logic. Key builders:
  - `html/`: HTML output with theming support
  - `latex/`: LaTeX/PDF output
  - `epub3.py`: EPUB ebook format
  - `linkcheck.py`: External link validation

- **sphinx/domains/**: Language-specific semantic markup systems. Domains provide directives, roles, and cross-reference resolution for different languages:
  - `python.py`: Python API documentation
  - `c.py`, `cpp.py`: C/C++ documentation
  - `javascript.py`: JavaScript documentation
  - `std.py`: Standard domain (generic cross-references, labels)

- **sphinx/ext/**: Built-in extensions for common documentation needs:
  - `autodoc/`: Automatic API documentation from docstrings
  - `autosummary/`: Generate summary tables and stub files
  - `napoleon/`: Support for NumPy and Google style docstrings
  - `intersphinx.py`: Cross-project references
  - `graphviz.py`: Diagrams via Graphviz
  - `todo.py`: TODO item tracking

- **sphinx/environment/**: `BuildEnvironment` manages the document tree, cross-references, and caching. The environment is pickled between builds for incremental updates.
  - `collectors/`: Gather information during parsing (dependencies, TOC trees, etc.)
  - `adapters/`: Adapt environment data for specific uses

- **sphinx/directives/**: reStructuredText directives (block-level markup). Includes code blocks, tables of contents, includes, and more.

- **sphinx/transforms/**: Docutils transform classes that modify the document tree during processing (i18n, reference resolution, post-processing).

- **sphinx/util/**: Utility functions for docutils integration, logging, file I/O, type hints, parallel processing, and more.

- **sphinx/config.py**: Configuration system (`Config` class). Reads `conf.py` files and manages documentation build settings.

- **sphinx/registry.py**: `SphinxComponentRegistry` manages registration of builders, extensions, domains, directives, roles, and other pluggable components.

### Build Process Flow

1. **Initialization**: `Sphinx` application loads config, initializes builders and extensions
2. **Reading**: Parse source files (reST) into docutils document trees
3. **Environment**: Collect cross-references, indices, and metadata
4. **Transformation**: Apply docutils transforms to resolve references and modify trees
5. **Writing**: Builders render documents to target format (HTML, LaTeX, etc.)

### Extension System

Sphinx is highly extensible via the extension API. Extensions register with the application using `setup(app)` functions and can:
- Add new builders, domains, directives, and roles
- Hook into build events (config-inited, env-updated, build-finished, etc.)
- Add configuration values
- Modify the document tree via transforms

Core extensions live in `sphinx/ext/` and serve as implementation examples.

### Testing Structure

Tests use pytest with Sphinx's testing fixtures (`sphinx.testing.fixtures`):
- `tests/test_*.py`: Unit tests for core functionality
- `tests/roots/`: Test fixture projects (minimal Sphinx projects for integration tests)
- Tests that require `sphinx-build` runs should use existing test infrastructure rather than creating new isolated builds (keeps test suite fast)
- Use `@pytest.mark.sphinx` decorator for tests requiring a Sphinx app

## Development Guidelines

### Branching Strategy

- **master**: Main development branch for next major release
- **A.x**: Stable branches for minor/patch releases (e.g., 7.x)
- Follow Semantic Versioning 2.0.0

### Code Style

- Line length: 95 characters
- Ruff for linting (configured in pyproject.toml)
- Type hints required (mypy for type checking)
- Single quotes for strings (inline-quotes = 'single')
- Use isort for import ordering

### Testing Requirements

- Add tests for all new features and bug fixes
- Bug fixes should include a test that fails before the fix and passes after
- Avoid tests that require full `sphinx-build` runs when unit tests suffice
- Test suite should complete in under a minute

### Pull Request Process

1. Create a feature branch from appropriate base (`master` or `A.x`)
2. Write code and tests
3. Add entry to `CHANGES` file for non-trivial changes
4. Ensure `make all` passes (style, type checks, tests)
5. Push and submit PR to the branch you based on

### Configuration Changes

When adding new configuration variables, update:
1. Documentation in `doc/`
2. `sphinx/cmd/quickstart.py` if the option is important

## Python and Dependency Requirements

- Python: >= 3.9 (supports 3.9, 3.10, 3.11, 3.12, 3.13)
- Build system: flit_core >= 3.7
- Key dependencies: docutils (0.18.1-0.20), Jinja2 (>=3.0), Pygments (>=2.14)
- Testing: pytest >= 4.6
- Type checking: mypy >= 0.990

## Key Entry Points

Command-line tools (defined in pyproject.toml):
- `sphinx-build`: Main build command (`sphinx.cmd.build:main`)
- `sphinx-quickstart`: Project initialization (`sphinx.cmd.quickstart:main`)
- `sphinx-apidoc`: API doc generation (`sphinx.ext.apidoc:main`)
- `sphinx-autogen`: Autosummary stub generation (`sphinx.ext.autosummary.generate:main`)

## Additional Resources

- Contributing guide: `doc/internals/contributing.rst`
- Issue tracker: https://github.com/sphinx-doc/sphinx/issues
- Documentation: https://www.sphinx-doc.org/
