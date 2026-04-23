# GEMINI.md

## Project Overview

This project, `pr-agent`, is an AI-powered command-line tool designed to automate and enhance the process of reviewing pull requests. It integrates with multiple Git providers (GitHub, GitLab, Bitbucket, Azure DevOps) and AI models (OpenAI, Anthropic) to provide intelligent feedback, code suggestions, and analysis directly within the PR workflow.

The agent can be invoked via CLI, GitHub Actions, or webhooks. It offers a suite of commands, including:

-   `/review`: Generates a comprehensive PR review, including a summary, code suggestions, and security analysis.
-   `/describe`: Automatically creates a title and description for the PR based on its changes.
-   `/improve`: Provides code suggestions to enhance the quality of the PR.
-   `/ask`: Answers questions about the PR content.

The tool is built in Python and uses a modular architecture, with different "tools" handling specific commands. It's highly configurable through TOML files, allowing users to customize prompts, models, and behavior.

## Building and Running

### Dependencies

The project uses Python `3.12+` and manages dependencies with `pip` and `requirements.txt`. Key dependencies include:

-   `openai`, `anthropic`, `litellm`: For interacting with various AI models.
-   `PyGithub`, `python-gitlab`, `atlassian-python-api`, `azure-devops`: For integrating with different Git hosting platforms.
-   `fastapi`, `uvicorn`: For the web server component.
-   `ruff`: For linting and code formatting.

### Installation

To install the necessary dependencies, run:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt # for development
```

### Running the CLI

The main entry point for the tool is `pr_agent/cli.py`. It can be run directly or using the installed `pr-agent` script.

**Basic Usage:**

```bash
export OPENAI_KEY="your_openai_api_key"
pr-agent --pr-url <PULL_REQUEST_URL> <COMMAND>
```

**Example Commands:**

```bash
# Get a review of a pull request
pr-agent --pr-url https://github.com/owner/repo/pull/123 review

# Ask a question about the pull request
pr-agent --pr-url https://github.com/owner/repo/pull/123 ask "What is the purpose of this change?"
```

### Running Tests

The project uses `pytest` for testing. To run the test suite:

```bash
pytest
```

## Development Conventions

### Code Style

The project uses `ruff` for linting and code style enforcement. The configuration can be found in `pyproject.toml`. Before committing, it's recommended to run `ruff` to ensure code quality:

```bash
ruff check .
```

### Contribution Guidelines

Contributions are welcome. The `CONTRIBUTING.md` file provides detailed instructions for setting up the development environment, running tests, and submitting pull requests.

### Configuration

The application is configured through a `configuration.toml` file. This allows for extensive customization of prompts, AI model settings, and tool-specific behavior. The configuration is loaded using the `dynaconf` library.

### Architecture

The core of the application is the `PRAgent` class (`pr_agent/agent/pr_agent.py`), which acts as a dispatcher. It receives a command and a PR URL, then instantiates the appropriate "tool" class to handle the request.

Each tool (e.g., `PRReviewer`, `PRDescription`) is responsible for a specific action. It interacts with the Git provider to fetch PR data, prepares a prompt for the AI model, and then formats the AI's response to be published back to the PR.
