# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PR-Agent is an open-source AI-powered code review tool that provides automated PR analysis. It supports multiple git providers (GitHub, GitLab, BitBucket, Azure DevOps, Gitea) and can be deployed via CLI, GitHub Actions, Docker, webhooks, or self-hosted servers.

The codebase uses Python 3.12+ with async/await patterns throughout. Core functionality includes PR description generation, code review, code suggestions, Q&A, and changelog updates.

## Development Setup

### Installation

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install the package in editable mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unittest/test_file_filter.py

# Run with coverage
pytest --cov=pr_agent tests/
```

### Code Quality

```bash
# Format imports (most important - configured in pre-commit)
isort .

# Run ruff linter
ruff check pr_agent/

# Install pre-commit hooks
pre-commit install

# Run pre-commit manually
pre-commit run --all-files
```

Note: The project uses `isort` for import formatting, which is configured in pre-commit hooks. Most other linters (ruff, bandit, autoflake) are commented out in the pre-commit config but defined in `pyproject.toml`.

### CLI Usage

```bash
# Basic review
python pr_agent/cli.py --pr_url=<PR_URL> review

# Other commands
python pr_agent/cli.py --pr_url=<PR_URL> describe
python pr_agent/cli.py --pr_url=<PR_URL> improve
python pr_agent/cli.py --pr_url=<PR_URL> ask "your question here"

# With configuration override
python pr_agent/cli.py --pr_url=<PR_URL> review --pr_reviewer.extra_instructions="focus on security"
```

## Architecture

### Core Components

**pr_agent/agent/pr_agent.py**: Main orchestrator that routes commands to appropriate tool classes. The `PRAgent` class handles request parsing, settings application, and command dispatch.

**pr_agent/tools/**: Each tool (review, describe, improve, ask, etc.) is a separate class:
- `PRReviewer`: Generates AI-powered code reviews
- `PRDescription`: Creates/updates PR titles and descriptions
- `PRCodeSuggestions`: Suggests code improvements
- `PRQuestions`: Handles Q&A about PRs
- `PRUpdateChangelog`: Updates changelogs based on PR content

**pr_agent/git_providers/**: Provider abstraction layer with concrete implementations:
- `GitProvider` (base class): Defines abstract interface for git operations
- `GithubProvider`, `GitLabProvider`, `AzureDevopsProvider`, `BitbucketProvider`, `GiteaProvider`: Provider-specific implementations
- Each provider handles authentication, API calls, comment posting, and file retrieval

**pr_agent/algo/ai_handlers/**: AI model integration layer:
- `BaseAiHandler`: Abstract interface for AI providers
- `LiteLLMAIHandler`: Primary handler using LiteLLM for multi-model support (OpenAI, Claude, Deepseek, etc.)
- `OpenAIAIHandler`: Direct OpenAI integration
- `LangChainOpenAIHandler`: LangChain integration (optional)

**pr_agent/servers/**: Deployment modes for different platforms:
- `github_app.py`: FastAPI/Starlette webhook server for GitHub App
- `gitlab_webhook.py`: GitLab webhook handler
- `bitbucket_app.py`, `bitbucket_server_webhook.py`: BitBucket integrations
- `azuredevops_server_webhook.py`: Azure DevOps webhook
- `github_action_runner.py`: GitHub Actions entrypoint
- `github_polling.py`: Polling-based GitHub integration

**pr_agent/algo/pr_processing.py**: Core PR processing logic including:
- PR compression strategy (handles large PRs by intelligently clipping patches)
- Token management and counting
- Diff processing and parsing

**pr_agent/config_loader.py**: Configuration management using Dynaconf:
- Loads settings from `pr_agent/settings/*.toml` files
- Supports configuration hierarchy: defaults → global settings → repo settings → command-line overrides
- Files can override with `.pr_agent.toml` in repository root or `pyproject.toml` under `[tool.pr-agent]`

### Configuration System

Configuration is hierarchical and loaded from multiple sources (in order of precedence):
1. Command-line arguments (e.g., `--pr_reviewer.extra_instructions="..."`)
2. Repository-specific: `.pr_agent.toml` or `pyproject.toml` `[tool.pr-agent]` section
3. Global defaults in `pr_agent/settings/configuration.toml`

Key configuration files:
- `configuration.toml`: Main settings (models, prompts, behavior)
- `pr_reviewer_prompts.toml`, `pr_description_prompts.toml`, etc.: Tool-specific prompts
- `language_extensions.toml`: File extension to language mappings
- `ignore.toml`: Files/patterns to ignore

### Request Flow

1. Request enters via CLI, GitHub Action, or webhook server
2. `PRAgent.handle_request()` parses URL and command
3. Repository-specific settings applied via `apply_repo_settings()`
4. Command mapped to tool class via `command2class` dict
5. Tool instantiates appropriate `GitProvider` and `BaseAiHandler`
6. Tool fetches PR data, processes patches, generates prompts
7. AI handler sends to LLM and returns response
8. Tool formats response and publishes via git provider

### Key Design Patterns

**Provider Pattern**: Git providers implement a common interface (`GitProvider`) allowing the same tool code to work across GitHub, GitLab, etc.

**Handler Pattern**: AI handlers abstract LLM interactions, supporting multiple models through a unified interface.

**Token-Aware Compression**: The system intelligently clips patches when they exceed token limits, prioritizing changed lines and relevant context.

**Async-First**: Most operations use async/await for efficient I/O, especially important for webhook servers handling concurrent requests.

## Testing

Tests are organized in `tests/`:
- `tests/unittest/`: Unit tests for specific modules (use pytest)
- `tests/e2e_tests/`: End-to-end tests for webhook servers
- `tests/health_test/`: Health check tests

Test structure follows standard pytest patterns with fixtures. Mock git providers and AI handlers when testing tools.

## Common Patterns

### Adding a New Tool

1. Create `pr_agent/tools/pr_new_tool.py` with a class inheriting appropriate patterns
2. Add prompts to `pr_agent/settings/pr_new_tool_prompts.toml`
3. Register in `pr_agent/agent/pr_agent.py` `command2class` dict
4. Update CLI help text in `pr_agent/cli.py`
5. Add tests in `tests/unittest/test_new_tool.py`

### Adding a New Git Provider

1. Create `pr_agent/git_providers/new_provider.py`
2. Inherit from `GitProvider` base class
3. Implement required abstract methods (especially `publish_comment`, `get_files`, `get_diff_files`)
4. Add provider detection logic in `git_providers/__init__.py`
5. Add webhook server if needed in `pr_agent/servers/`

### Configuration Override

Tools should respect configuration from `get_settings()`:
```python
from pr_agent.config_loader import get_settings

# Access config
max_tokens = get_settings().config.max_model_tokens
extra_instructions = get_settings().pr_reviewer.extra_instructions

# Temporarily override
get_settings().set("config.publish_output", False)
```

## Important Notes

- **Environment Variables**: API keys should be set as `OPENAI_KEY`, `ANTHROPIC_API_KEY`, etc. (see `.secrets_template.toml`)
- **Token Limits**: Always check token counts before sending to LLM; use `TokenHandler` for estimation
- **Git Provider Capabilities**: Check `git_provider.is_supported(capability)` before using provider-specific features
- **Async Context**: Most tool methods are async; use `await` for git provider and AI handler calls
- **Error Handling**: Use `get_logger()` from `pr_agent.log` for consistent logging
- **PR Compression**: Large PRs automatically trigger compression strategy in `pr_processing.py`

## Docker

Multi-stage Dockerfile in `docker/Dockerfile` with targets for different deployment modes:
- `cli`: Command-line usage
- `github_app`: GitHub App webhook server
- `gitlab_webhook`: GitLab webhook server
- `bitbucket_app`: BitBucket webhook server
- `azure_devops_webhook`: Azure DevOps webhook server
- `test`: Test environment with dev dependencies
