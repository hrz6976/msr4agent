# GEMINI.md - Ansible

## Project Overview

This is the Ansible project, a powerful and simple IT automation engine written in Python. Ansible is used for configuration management, application deployment, cloud provisioning, ad-hoc task execution, network automation, and multi-node orchestration.

**Key Technologies:**

*   **Language:** Python
*   **Package Management:** `pip`, `setuptools`
*   **Core Dependencies:** `jinja2`, `PyYAML`, `cryptography`, `packaging`, `resolvelib`

**Architecture:**

Ansible follows an agentless architecture, communicating with managed nodes over SSH or other protocols. It uses a declarative language (YAML) to describe the desired state of the system. The project is organized into several components, including a core engine, modules, and plugins.

## Building and Running

### Development Environment Setup

To start developing on Ansible, you need to set up a development environment. The `hacking/env-setup` script is provided for this purpose:

```bash
# Set up the environment to run from the checkout
source ./hacking/env-setup

# Install the required dependencies
pip install -r requirements.txt
```

### Running Tests

The primary tool for running tests is `ansible-test`. The project has a comprehensive test suite that is executed in Azure Pipelines. The tests are categorized into different stages, including:

*   **Sanity Tests:** Check for basic code quality and style issues.
*   **Unit Tests:** Test individual components and functions.
*   **Integration Tests:** Test the interaction between different components.

To run the full test suite locally, you can use the `ansible-test` command. For example, to run the sanity tests:

```bash
ansible-test sanity
```

You can also run specific tests. For example, to run the unit tests for a specific Python version:

```bash
ansible-test units --python 3.11
```

The Azure Pipelines configuration in `.azure-pipelines/azure-pipelines.yml` provides a complete overview of the testing strategy and the different test targets.

### Running Ansible

Once the development environment is set up, you can run Ansible commands directly from the checkout. For example:

```bash
ansible --version
ansible-playbook --help
```

## Development Conventions

### Coding Style

While not explicitly defined in the files I've reviewed, the presence of sanity tests and a `.pre-commit-config.yaml` file (though I haven't read it) suggests that the project enforces a consistent coding style. It's recommended to explore the project's documentation for specific coding guidelines.

### Testing

The project has a strong emphasis on testing, with a comprehensive test suite that covers different aspects of the application. All new code should be accompanied by tests. The `hacking/test-module.py` script can be used to test modules in isolation.

### Contribution Guidelines

The `README.md` file provides links to the contributor's guide and other community resources. Before contributing, it's recommended to review these documents and engage with the community.
