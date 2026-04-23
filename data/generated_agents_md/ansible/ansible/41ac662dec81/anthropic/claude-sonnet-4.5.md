# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is **ansible-core**, the core runtime and CLI for Ansible, a radically simple IT automation system. Ansible is agentless (uses SSH), supports configuration management, application deployment, cloud provisioning, and multi-node orchestration. The repository provides the `ansible-*` CLI tools and core plugin framework, while modules live in separate collections repositories.

Requires Python 3.11+.

## Development Setup

Set up a development environment from git checkout:

```bash
# Source the environment setup script
source ./hacking/env-setup

# Install required Python dependencies
pip install -r requirements.txt
```

This modifies `PYTHONPATH` and `PATH` to run ansible from the checkout rather than installed packages. For fish shell, use `hacking/env-setup.fish`.

## Running Tests

Ansible uses **ansible-test** as its unified test runner. All test commands should use `./bin/ansible-test`.

### Sanity Tests (Linting and Code Quality)

Run all sanity tests:
```bash
./bin/ansible-test sanity
```

Run specific sanity tests:
```bash
./bin/ansible-test sanity --test pep8
./bin/ansible-test sanity --test pylint
./bin/ansible-test sanity --test mypy
./bin/ansible-test sanity --test black
./bin/ansible-test sanity --test validate-modules
```

Run sanity tests on changed files only:
```bash
./bin/ansible-test sanity --changed
```

Available sanity tests include: `action-plugin-docs`, `ansible-doc`, `black`, `boilerplate`, `changelog`, `compile`, `import`, `mypy`, `pep8`, `pylint`, `validate-modules`, and more.

### Unit Tests

Run all unit tests:
```bash
./bin/ansible-test units
```

Run specific test files or directories:
```bash
./bin/ansible-test units test/units/cli/
./bin/ansible-test units test/units/module_utils/basic/test_run_command.py
```

Run a specific test function:
```bash
./bin/ansible-test units test/units/cli/test_adhoc.py::TestAdhoc::test_run
```

### Integration Tests

Run integration tests:
```bash
./bin/ansible-test integration <target>
```

Integration test targets are located in `test/integration/targets/`.

### Common Test Options

- `--python X.Y`: Test against specific Python version (e.g., `--python 3.11`)
- `--docker`: Run tests in a Docker container
- `--docker [IMAGE]`: Run tests in specific Docker image
- `--venv`: Create and use a virtual environment
- `--coverage`: Collect code coverage data
- `--changed`: Only test changed files
- `-v`: Verbose output
- `--collect-only`: List tests without running them (units only)

## Repository Structure

### Core Source Code (`lib/ansible/`)

- **`cli/`**: Entry points for all `ansible-*` commands (ansible-playbook, ansible-doc, ansible-galaxy, etc.)
- **`executor/`**: Playbook and task execution engine
  - `playbook_executor.py`: Orchestrates playbook execution
  - `task_executor.py`: Executes individual tasks
  - `task_queue_manager.py`: Manages task execution across multiple hosts
  - `play_iterator.py`: Iterates through plays and handles task sequencing
  - `module_common.py`: Module wrapper/loader for running modules on target hosts
- **`playbook/`**: Playbook object model (Play, Task, Block, Role, etc.)
- **`plugins/`**: Plugin system with subdirectories per plugin type
  - `action/`, `callback/`, `connection/`, `filter/`, `inventory/`, `lookup/`, `strategy/`, `test/`, `vars/`, etc.
  - `loader.py`: Plugin discovery and loading mechanism
- **`module_utils/`**: Reusable code shared by modules (imported on target nodes)
  - `basic.py`: Core `AnsibleModule` class used by nearly all modules
  - `common/`: Common utilities (parameters, validation, file operations, etc.)
  - `facts/`: Fact gathering subsystem
  - `powershell/`, `csharp/`: Support for Windows modules
- **`modules/`**: Built-in modules (minimal; most modules are in collections)
- **`parsing/`**: YAML parsing, Jinja2 templating, and variable resolution
- **`inventory/`**: Inventory management and host/group data
- **`vars/`**: Variable management and precedence
- **`galaxy/`**: ansible-galaxy implementation for role/collection management
- **`config/`**: Configuration management and ansible.cfg parsing
- **`template/`**: Jinja2 templating integration
- **`utils/`**: Various utilities (display, encryption, hashing, etc.)
- **`_internal/`**: Internal implementation details not for external import
- **`constants.py`**: Global constants and default values

### Test Code (`test/`)

- **`units/`**: Unit tests mirroring `lib/ansible/` structure
- **`integration/targets/`**: Integration test targets (each subdirectory is a separate target)
- **`sanity/`**: Sanity test implementations
- **`lib/ansible_test/`**: Implementation of ansible-test framework
- **`support/`**: Plugins and modules used only for testing (do not modify)

### Development Tools (`hacking/`)

- **`env-setup`**: Sets up development environment from git checkout
- **`test-module.py`**: Run a module locally for debugging
- **`return_skeleton_generator.py`**: Generate RETURNS documentation from module output
- **`azp/`**: Azure Pipelines CI scripts and tools

### Other Key Directories

- **`bin/`**: Wrapper scripts for all `ansible-*` commands
- **`changelogs/`**: Changelog fragments and configuration
  - Add changelog fragments to `changelogs/fragments/` for PRs
- **`packaging/`**: Release and packaging scripts
- **`.azure-pipelines/`**: Azure Pipelines CI configuration

## Key Architecture Concepts

### Plugin Architecture

Ansible is built around a plugin system. Nearly everything is a plugin: modules, inventory sources, connection methods, callbacks, filters, tests, lookups, strategies, etc. Plugins are loaded dynamically by the `PluginLoader` in `lib/ansible/plugins/loader.py`.

### Execution Flow

1. **CLI Layer** (`cli/`): Parses arguments, loads configuration
2. **Playbook Parsing** (`parsing/`, `playbook/`): Loads YAML, resolves Jinja2, creates object model
3. **Execution Engine** (`executor/`):
   - `PlaybookExecutor` orchestrates multiple plays
   - `TaskQueueManager` coordinates parallel execution across hosts
   - `PlayIterator` manages task sequencing and flow control
   - `TaskExecutor` runs individual tasks on target hosts
   - Action plugins run on controller, modules run on target
4. **Connection Layer** (`plugins/connection/`): Establishes connection to targets (SSH, local, winrm, etc.)
5. **Module Execution** (`executor/module_common.py`): Wraps modules, transfers to target, executes
6. **Results** (`executor/task_result.py`): Collects and returns results to controller

### Module Execution Model

Modules are transferred to target systems and executed there. `AnsibleModule` from `module_utils/basic.py` provides the framework modules use to parse parameters, return results, and interact with the system.

### Collections vs Core

Modern Ansible separates content (modules, plugins, roles) into **collections** (distributed separately) from **ansible-core** (this repository). Most modules have been moved to collections under `github.com/ansible-collections/`. This repository contains only core runtime, CLI tools, and a minimal set of essential modules/plugins.

## Branching and Release Model

- **`devel`**: Active development branch for next release
- **`stable-2.X`**: Stable release branches
- Base PRs on `devel` branch
- See [Ansible release and maintenance](https://docs.ansible.com/ansible/devel/reference_appendices/release_and_maintenance.html) for supported versions

## Code Quality and CI

All code must pass sanity tests before merge. Azure Pipelines runs:
- Sanity tests (linting, type checking, documentation validation)
- Unit tests across multiple Python versions
- Integration tests
- Code coverage analysis

Run the same checks locally with `ansible-test` before submitting PRs.

## Useful Commands

```bash
# Run a module locally for debugging
./hacking/test-module.py -m lib/ansible/modules/command.py -a "echo hi"

# Check what would be tested by changed files
./bin/ansible-test sanity --changed --list-tests

# Run specific module validation
./bin/ansible-test sanity --test validate-modules lib/ansible/modules/copy.py

# Generate RETURNS documentation from module output
./hacking/return_skeleton_generator.py <module-output.json>
```

## External Documentation

- Developer Guide: https://docs.ansible.com/ansible/devel/dev_guide/
- API documentation: https://docs.ansible.com/ansible/devel/dev_guide/developing_api.html
- Module development: https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html
- Contributing guide: https://docs.ansible.com/ansible/devel/community/index.html
