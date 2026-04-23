# GEMINI.md: Your Guide to the `smolagents` Project

This document provides a comprehensive overview of the `smolagents` project, tailored for AI-powered development assistance. It covers the project's purpose, key technologies, and development conventions to ensure smooth and effective collaboration.

## Project Overview

`smolagents` is a lightweight yet powerful Python library designed to simplify the creation and deployment of AI agents. It stands out by enabling "Code Agents" that think and act through Python code, offering enhanced security and flexibility. The library is model-agnostic, supporting a wide range of LLMs from local `transformers` to major providers like OpenAI, Anthropic, and Hugging Face.

### Key Features:

- **Code Agents**: A unique approach where agents write and execute Python code to perform actions, leading to more efficient and powerful workflows.
- **Security First**: Offers sandboxed execution environments via Docker, E2B, and other backends to mitigate the risks of arbitrary code execution.
- **Model-Agnostic**: Seamlessly integrates with numerous LLM providers, giving you the freedom to choose the best model for your needs.
- **Hugging Face Hub Integration**: Simplifies sharing and discovering agents and tools through direct integration with the Hugging Face Hub.
- **Extensible Toolkit**: Easily extend agent capabilities with custom tools or by integrating with existing frameworks like LangChain.

## Building and Running

### Installation

To get started with `smolagents`, install the core library and a default set of tools using pip:

```bash
pip install "smolagents[toolkit]"
```

For development, additional dependencies for testing and code quality checks are required:

```bash
pip install "smolagents[dev]"
```

### Running the Agents

Agents can be run programmatically or through the command line.

#### Programmatic Usage

Here's a quick example of how to run a `CodeAgent` in your Python code:

```python
from smolagents import CodeAgent, WebSearchTool, InferenceClientModel

# Initialize your desired model
model = InferenceClientModel()

# Create an agent and equip it with tools
agent = CodeAgent(tools=[WebSearchTool()], model=model)

# Run the agent with a specific task
agent.run("How many seconds would it take for a leopard at full speed to run through Pont des Arts?")
```

#### Command-Line Interface

The library provides two CLI commands for easy interaction:

- **`smolagent`**: A general-purpose command for running a multi-step `CodeAgent` with various tools.

  ```bash
  # Run with a direct prompt and options
  smolagent "Plan a trip to Tokyo" --model-id "gpt-4"

  # Run in interactive mode for guided setup
  smolagent
  ```

- **`webagent`**: A specialized agent for web browsing tasks.

  ```bash
  webagent "Go to example.com, find the contact email, and return it." --model-id "gpt-4"
  ```

### Testing

The project uses `pytest` for testing. To run the test suite, first install the testing dependencies, then execute `pytest`:

```bash
pip install "smolagents[test]"
pytest
```

## Development Conventions

`smolagents` follows standard Python development practices to ensure code quality and consistency.

### Code Style and Linting

The project uses `ruff` for linting and code formatting. A pre-commit hook is configured in `.pre-commit-config.yaml` to automatically check and format code before each commit. This ensures that all contributions adhere to the established coding style.

### Contribution Guidelines

For those looking to contribute, the `CONTRIBUTING.md` file provides detailed instructions on the development process, from setting up your environment to submitting a pull request.

### Core Logic

The heart of the library's functionality resides in `src/smolagents/agents.py`. This file contains the primary classes, `MultiStepAgent`, `CodeAgent`, and `ToolCallingAgent`, which implement the core logic for agentic workflows. Understanding this file is key to grasping how agents process tasks, interact with tools, and generate responses.
