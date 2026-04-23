# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDM (Python Dependency Manager) is a modern Python package and dependency manager supporting the latest PEP standards (PEP 517 build backend, PEP 621 project metadata). It provides fast dependency resolution optimized for binary distributions, flexible plugin system, and centralized cache management similar to pnpm.

PDM manages virtual environments (venvs) in both project and centralized locations, reads project metadata from standardized `pyproject.toml` files, and supports lockfiles with exact versions and hashes. Unlike Poetry and Hatch, PDM is not limited to a specific build backend.

## Development Setup

PDM requires Python 3.9+. Set up the development environment:

```bash
# Create a virtual environment with venv or virtualenv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv/Scripts/activate  # Windows

# Ensure pip >= 21.3 for editable installs
python -m pip install -U "pip>=21.3"
python -m pip install -e .

# Configure PDM to use the virtual environment
pdm config -l python.use_venv true
pdm config -l venv.in_project true

# Install all development dependencies
pdm install
```

## Essential Commands

### Testing

```bash
# Run all tests
pdm run test

# Run tests in parallel with pytest-xdist (faster)
pdm run test -n auto

# Exclude integration tests (much faster for local development)
pdm run test -n auto -m "not integration"

# Run specific test file
pdm run test tests/cli/test_add.py

# Run specific test function
pdm run test tests/cli/test_add.py::test_add_package
```

Test markers in `pyproject.toml`:
- `network`: Tests requiring network access
- `integration`: Tests that run with all Python versions (slow)
- `path`: Tests comparing with system paths
- `deprecated`: Tests for deprecated features
- `uv`: Requires uv to be installed
- `msgpack`: Requires msgpack to be installed

### Code Quality

```bash
# Run all linting (ruff format + ruff + codespell + mypy)
pdm run lint

# Pre-commit hooks are managed by prek (not pre-commit)
# Install prek: https://github.com/j178/prek
prek install
```

PDM uses:
- **ruff**: Python linter and formatter (replaces black, isort, flake8)
- **mypy**: Static type checking
- **codespell**: Spell checker
- **Pre-commit hooks** via prek

### Documentation

```bash
# Start local documentation server at http://127.0.0.1:8000
pdm run doc
```

### News Fragments

All changes require a news fragment in `news/` directory:

```bash
# Create a news fragment: news/<issue_num>.<type>.md
# Types: feature, bugfix, refactor, doc, dep, removal, misc
# Example: news/1234.bugfix.md
echo "Fix dependency resolution for git packages." > news/1234.bugfix.md
```

## Architecture

### Core Components

**Core (`src/pdm/core.py`)**: High-level object managing all classes, configurations, and command registration. The `Core` class contains the argument parser, plugin loader, and project/repository/installer class references.

**Project (`src/pdm/project/core.py`)**: The `Project` class is the central object managing project state, including:
- `pyproject.toml` parsing and metadata
- Lock file management
- Python interpreter detection
- Environment management
- Configuration (per-project and global)
- Dependency groups and requirements

**CLI System (`src/pdm/cli/`)**: 
- All commands in `src/pdm/cli/commands/` inherit from `BaseCommand`
- Commands are auto-discovered and registered in `Core.init_parser()`
- Command pattern: Define `name`, `description`, `arguments`, `add_arguments()`, and `handle()` methods
- Common options defined in `src/pdm/cli/options.py` using the `Option` class

**Dependency Resolution (`src/pdm/resolver/`)**: 
- Uses resolvelib library with custom providers
- Multiple resolution strategies (e.g., eager, conservative)
- Provider pattern: `BaseProvider` subclasses registered via `@register_provider` decorator
- Handles Python version constraints, environment markers, and package dependencies
- `PythonRequirement` and `PythonCandidate` classes for Python interpreter resolution

**Package Models (`src/pdm/models/`)**: 
- `Candidate`: Represents a package candidate with metadata
- `Requirement`: Parsed dependency requirement (supports PEP 508, file URLs, VCS URLs)
- `Repository`: PyPI interaction and package finding
  - `BaseRepository`: Abstract base
  - `PyPIRepository`: Default PyPI implementation
  - `LockedRepository`: Repository backed by lock file
- `PackageCache`, `WheelCache`, `HashCache`: Centralized caching system

**Environment Management (`src/pdm/environments/`)**: Creates and manages Python environments (virtualenv, PEP 582, system).

**Installers (`src/pdm/installers/`)**: Installs/uninstalls packages into site-packages with centralized cache support using the installer library.

**Build System (`src/pdm/builders/`)**: PEP 517 build frontend for creating wheels and sdists.

### Key Files

- `src/pdm/core.py` - Main application entry point, command registration, Core class
- `src/pdm/project/core.py` - Project class managing project state
- `src/pdm/cli/commands/base.py` - BaseCommand class for CLI commands
- `src/pdm/resolver/providers.py` - Dependency resolution providers
- `src/pdm/models/candidates.py` - Package candidate representation
- `src/pdm/models/requirements.py` - Dependency requirement parsing

### Testing Structure

- Test files mirror source structure: `tests/cli/test_add.py` tests `src/pdm/cli/commands/add.py`
- Uses pytest with custom fixtures from `pdm.pytest` plugin
- `tests/conftest.py` provides global fixtures (mock PyPI server, git mocking, etc.)
- Test fixtures in `tests/fixtures/` include mock packages and project templates
- Each command test file has its own `conftest.py` with command-specific fixtures

### Plugin System

PDM has a flexible plugin system using entry points:
- Plugins discovered via `pdm` entry point group
- Can add new commands, modify resolution, add hooks, etc.
- See [Awesome PDM](https://github.com/pdm-project/awesome-pdm) for examples

## Common Patterns

### Adding a New Command

1. Create `src/pdm/cli/commands/mycommand.py`
2. Inherit from `BaseCommand` and implement `handle()`
3. The command is auto-discovered via directory scanning in `core.py`

Example:
```python
from pdm.cli.commands.base import BaseCommand

class Command(BaseCommand):
    """Help text for my command"""
    name = "mycommand"
    
    def add_arguments(self, parser):
        parser.add_argument("--option", help="An option")
    
    def handle(self, project, options):
        # Implementation
        pass
```

### Working with Lock Files

Lock file operations:
```bash
# Check lock file validity
pdm lock --check

# Update lock file without installing
pdm lock

# Update specific packages
pdm update package-name

# Add dependency and update lock
pdm add requests
```

PDM lock files (`pdm.lock`) include:
- Exact versions with SHA256 hashes
- Environment markers for conditional dependencies
- Cross-platform support (separate locks per platform if needed)
- Dependency groups (dev, test, doc, etc.)

### Debugging

Set `PDM_DEBUG=1` environment variable for verbose output including:
- Resolution decisions
- Network requests
- Cache operations
- Build backend interactions

## Important Constraints

- PDM itself uses PDM for development (self-hosting)
- Build backend is `pdm-backend`, separate package
- Lock file uses `pdm-build-locked` for reproducible builds with locked dependencies
- Python 3.9+ required for PDM itself
- Support for managing Python 3.7+ projects

## Release Process

Releases are managed via `tasks/release.py`:

```bash
# Preview changelog
pdm run release --dry-run

# Cut a release (creates tag, GitHub Actions handles PyPI upload)
pdm run release
```

Version bumping uses `parver` library, and changelog is generated from news fragments in `news/` using towncrier.