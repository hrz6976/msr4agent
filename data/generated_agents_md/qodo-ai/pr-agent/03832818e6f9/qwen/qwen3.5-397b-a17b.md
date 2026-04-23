
# AGENTS.md

## Project Overview

This project, `pr-agent`, is an open-source AI-powered code review tool designed to help developers efficiently review and handle pull requests. It provides AI-driven feedback and suggestions to improve code quality. The tool can be run locally, as a GitHub Action, or self-hosted. It supports various Git providers, including GitHub, GitLab, Bitbucket, and Azure DevOps. The project is written in Python and uses the `setuptools` build system.

## Building and Running

### Command-Line Interface (CLI)

The project includes a command-line tool, `pr-agent`, for local usage.

**Installation:**

```bash
pip install -r requirements.txt
```

**Usage:**

To run the agent on a specific pull request, use the following command:

```bash
export OPENAI_KEY=your_key_here
pr-agent --pr_url https://github.com/owner/repo/pull/123 review
```

### GitHub Action

The `pr-agent` can be run as a GitHub Action to automate code reviews on pull requests.

**Example Workflow:**

Create a `.github/workflows/pr-agent.yml` file with the following content:

```yaml
name: PR Agent
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    steps:
    - name: PR Agent action step
      uses: Codium-ai/pr-agent@main
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

The action uses a Docker container to execute, as specified in `action.yaml`.

### Running Tests

The project uses `pytest` for testing. To run the test suite:

```bash
pytest
```

## Development Conventions

### Linting

The project uses `ruff` for linting and code formatting. The configuration is defined in `pyproject.toml`. To run the linter:

```bash
ruff check .
```

### Dependencies

The project's dependencies are listed in `requirements.txt`. Key dependencies include:
- `openai`: For interacting with OpenAI models.
- `anthropic`: For using Anthropic models.
- `PyGithub`, `python-gitlab`, `atlassian-python-api`, `azure-devops`: For interacting with various Git provider APIs.
- `fastapi`, `uvicorn`: For serving the agent as a web service.
- `pytest`: For running tests.
- `ruff`: For linting.
- `setuptools`: For packaging and distribution.
