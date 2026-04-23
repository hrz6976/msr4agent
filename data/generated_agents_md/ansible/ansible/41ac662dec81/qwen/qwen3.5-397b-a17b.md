# AGENTS.md

## Project Overview

This is the Ansible project, a powerful IT automation system. It is written in Python and is designed for configuration management, application deployment, cloud provisioning, ad-hoc task execution, network automation, and multi-node orchestration. The project is structured with a clear separation of concerns, including a `lib` directory for the core logic, a `test` directory for tests, and a `hacking` directory for development scripts.

## Building and Running

### Development Environment Setup

To set up your development environment, run the following command from the root of the project:

```shell
source ./hacking/env-setup
```

This script will modify your `PYTHONPATH`, `PATH`, and `MANPATH` to use the code in the checkout directory. You will also need to install the required Python packages:

```shell
pip install -r requirements.txt
```

### Running Tests

The project uses `ansible-test` for testing. The tests are categorized into `sanity`, `integration`, and `unit` tests. To run the tests, use the following commands:

*   **Sanity tests:**
    ```shell
    ansible-test sanity
    ```
*   **Integration tests:**
    ```shell
    ansible-test integration
    ```
*   **Unit tests:**
    ```shell
    ansible-test units
    ```

You can also run specific tests by providing a test name as an argument. For example:

```shell
ansible-test sanity --test pylint
```

## Development Conventions

The project has a set of coding guidelines and conventions that are documented in the [Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/). The `hacking` directory contains various scripts and tools to help with development, including a script to test modules individually (`test-module.py`) and a script to generate the `RETURNS` section of a module (`return_skeleton_generator.py`).

The test directory is organized into `integration`, `sanity`, and `units` subdirectories. This structure helps to keep the tests organized and easy to maintain.
