# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenAI Agents SDK is a Python framework for building multi-agent workflows. It's provider-agnostic, supporting OpenAI Responses/Chat Completions APIs and 100+ other LLMs via LiteLLM.

**Key concepts:**
- **Agents**: LLMs configured with instructions, tools, guardrails, and handoffs
- **Handoffs**: Specialized tool calls for transferring control between agents
- **Guardrails**: Configurable safety checks for input/output validation
- **Sessions**: Automatic conversation history management
- **Tracing**: Built-in tracking of agent runs

**Python versions**: 3.9+ required

## Development Setup

### Initial setup
```bash
# Install uv if needed
# Follow: https://docs.astral.sh/uv/

# Install all dependencies (including dev dependencies and all extras)
make sync
```

### Environment
Set `OPENAI_API_KEY` environment variable for running examples and tests that require model access.

## Common Commands

### Testing
```bash
make tests              # Run all tests
make coverage           # Run tests with coverage report (requires 95%+ coverage)
uv run pytest path/to/test_file.py  # Run specific test file
uv run pytest path/to/test_file.py::test_function  # Run specific test
```

Tests use pytest with asyncio mode enabled. Most tests are async by default.

### Linting and Type Checking
```bash
make check              # Run all checks: format-check, lint, mypy, tests
make lint               # Run ruff linter
make mypy               # Run type checker (strict mode enabled)
make format-check       # Check code formatting
make format             # Auto-format code with ruff
```

### Snapshots (inline-snapshot library)
```bash
make snapshots-fix      # Update existing snapshots
make snapshots-create   # Create new snapshots
```

### Documentation
```bash
make build-docs         # Build docs locally
make serve-docs         # Serve docs locally at http://127.0.0.1:8000
make build-full-docs    # Build docs with translations
```

Documentation uses MkDocs with mkdocs-material theme. API reference is auto-generated from docstrings using mkdocstrings/griffe.

## Project Structure

### Source Code (`src/agents/`)
Main implementation is in `src/agents/`. Key modules:

- **Core agent system**:
  - `agent.py`: Agent class definition
  - `run.py`: Runner class for executing agents
  - `_run_impl.py`: Internal run loop implementation
  - `result.py`: RunResult and RunResultStreaming classes

- **Tools system**: 
  - `tool.py`: Tool base classes, function_tool decorator
  - `tool_guardrails.py`: Input/output guardrails for tools
  - Built-in tools: ShellTool, ComputerTool, FileSearchTool, WebSearchTool, etc.

- **Multi-agent patterns**:
  - `handoffs/`: Handoff system for agent-to-agent transfers
  - `guardrail.py`: Input/output guardrails with @input_guardrail/@output_guardrail decorators

- **Model abstraction**:
  - `models/`: Provider-agnostic model interface
    - `interface.py`: Model and ModelProvider base classes
    - `openai_provider.py`: OpenAI implementation
    - `openai_responses.py`: OpenAI Responses API
    - `openai_chatcompletions.py`: OpenAI Chat Completions API
    - `multi_provider.py`: MultiProvider for routing across providers

- **Session/memory**:
  - `memory/`: Session implementations (SQLiteSession, RedisSession, etc.)
  
- **Tracing**:
  - `tracing/`: Built-in tracing system with spans
  
- **Extensions**:
  - `extensions/`: Optional features (MCP, voice, realtime)
  - `mcp/`: Model Context Protocol integration
  - `realtime/`: Realtime API support
  - `voice/`: Voice pipeline support

### Tests (`tests/`)
129+ test files. Tests are organized to mirror the source structure. Use pytest-asyncio for async tests.

### Examples (`examples/`)
Working examples organized by category:
- `basic/`: Simple usage patterns
- `agent_patterns/`: Common multi-agent patterns (routing, parallelization, etc.)
- `handoffs/`: Handoff examples
- `tools/`: Tool usage examples
- `memory/`: Session management examples
- `mcp/`: MCP integration examples
- `realtime/`, `voice/`: Realtime and voice examples

### Documentation (`docs/`)
Documentation source for MkDocs site. Includes Japanese and Korean translations in `docs/ja/` and `docs/ko/`.

## Code Architecture

### The Agent Loop
When `Runner.run()` is called:
1. Call LLM with current message history
2. LLM returns response (may include tool calls)
3. If response has final output → return and end loop
4. If response has handoff → switch to new agent and goto step 1
5. Process tool calls (if any), append tool responses, goto step 1

Loop continues until final output or `max_turns` (default 10) is reached.

**Final output determination**:
- If agent has `output_type`: final output is when LLM returns structured output of that type
- If no `output_type`: first LLM response without tool calls/handoffs is final output

### Multi-Agent Patterns
Two primary patterns:
1. **Manager pattern (agents as tools)**: Central orchestrator invokes specialized sub-agents as tools via `agent.as_tool()`
2. **Handoffs pattern**: Peer agents hand off control using `handoffs` parameter

See `examples/agent_patterns/` for implementations.

### Provider Abstraction
The SDK abstracts model providers through `ModelProvider` interface. Default is OpenAI, but supports:
- Custom providers implementing the ModelProvider protocol
- LiteLLM for 100+ LLM providers
- See `examples/model_providers/` for custom provider examples

## Testing Patterns

- Most tests are async and use pytest-asyncio
- Mock models are used by default; real model calls require `@pytest.mark.allow_call_model_methods`
- Use inline-snapshot for snapshot testing
- Coverage target is 95%+
- Test files follow naming: `test_*.py`

## Style Conventions

- **Code formatting**: Use ruff (line length 100)
- **Type checking**: Strict mypy enabled, but `disallow_untyped_defs` is False
- **Imports**: Use isort via ruff with `combine-as-imports = true`
- **Docstrings**: Google style
- **Example files**: E501 (line length) ignored for readability

## Important Notes

- **Async by default**: Most SDK functions are async. Use `Runner.run()` for async, `Runner.run_sync()` for sync
- **Context typing**: Agents are generic on context type: `Agent[MyContextType](...)`
- **Structured outputs**: Use `output_type` parameter on agents to enable structured outputs
- **Test model access**: Tests that call real models must be marked with `@pytest.mark.allow_call_model_methods`
- **Memory/Sessions**: Use Session protocol (SQLiteSession, RedisSession, etc.) for conversation persistence
- **Tracing**: Automatically enabled by default; can be customized or disabled

## Related Resources

- Documentation site: https://openai.github.io/openai-agents-python/
- GitHub: https://github.com/openai/openai-agents-python
- PyPI: https://pypi.org/project/openai-agents/
- JavaScript/TypeScript SDK: https://github.com/openai/openai-agents-js
