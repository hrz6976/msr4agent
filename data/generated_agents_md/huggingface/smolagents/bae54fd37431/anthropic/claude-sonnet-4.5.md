# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`smolagents` is a lightweight (~1,000 lines of core code) Python library for building agentic systems. The library supports two main agent types:
- **CodeAgent**: Writes actions as Python code snippets (default, most capable)
- **ToolCallingAgent**: Uses JSON/text-based tool calling

Key differentiator: CodeAgent writes actions in Python rather than JSON, enabling more powerful tool orchestration (30% fewer steps, higher benchmark performance).

## Development Commands

### Setup
```bash
# Install with all dependencies for development
pip install -e ".[dev]"

# Or using uv
uv pip install -e "smolagents[dev] @ ."
```

### Code Quality
```bash
# Check code quality (runs ruff)
make quality

# Auto-format code
make style
```

### Testing
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_agents.py

# Run specific test function
pytest tests/test_agents.py::test_function_name -v
```

Note: Tests use fixtures from `tests/fixtures/` (agents.py, tools.py) and suppress agent logging by default via `conftest.py`.

### Pre-commit Hooks
The project uses pre-commit hooks (configured in `.pre-commit-config.yaml`) for:
- Ruff linting and formatting
- Merge conflict checks
- YAML validation

## Architecture & Core Concepts

### Main Components

1. **Agents** (`src/smolagents/agents.py`)
   - `MultiStepAgent`: Abstract base class for all agents
   - `CodeAgent`: Generates Python code for actions (ReAct loop)
   - `ToolCallingAgent`: Standard JSON-based tool calling
   - `ManagedAgent`: Agent that can be used as a tool by other agents

2. **Models** (`src/smolagents/models.py`)
   - Base `Model` class with various provider implementations:
     - `InferenceClientModel`: HuggingFace Inference API (default)
     - `OpenAIModel`: OpenAI and compatible APIs
     - `LiteLLMModel`: Access to 100+ LLMs via LiteLLM
     - `TransformersModel`: Local models via transformers
     - `VLLMModel`, `MLXModel`: Optimized local inference
     - `AzureOpenAIModel`, `AmazonBedrockModel`: Cloud providers
   - All models support streaming and structured output

3. **Tools** (`src/smolagents/tools.py`)
   - `BaseTool`: Abstract base for all tools
   - `Tool`: Standard tool implementation
   - Can load from Hub, LangChain, MCP servers, or Spaces
   - Type system uses JSON schema with support for images, audio, etc.

4. **Executors** (`src/smolagents/local_python_executor.py`, `remote_executors.py`)
   - `LocalPythonExecutor`: Secure Python interpreter for local execution
   - Remote executors for sandboxed execution:
     - `E2BExecutor`: E2B sandboxes
     - `DockerExecutor`: Docker containers
     - `ModalExecutor`: Modal serverless
     - `BlaxelExecutor`: Blaxel sandboxes
     - `WasmExecutor`: Pyodide+Deno WebAssembly

5. **Memory System** (`src/smolagents/memory.py`)
   - `AgentMemory`: Manages conversation history
   - Memory steps: `ActionStep`, `TaskStep`, `PlanningStep`, `FinalAnswerStep`
   - Tracks token usage, timing, tool calls, and observations

6. **CLI Tools** (`src/smolagents/cli.py`, `vision_web_browser.py`)
   - `smolagent`: General-purpose CLI agent
   - `webagent`: Specialized web-browsing agent using Helium

### Key Patterns

**CodeAgent ReAct Loop:**
1. User task added to memory
2. Generate Python code action from LLM
3. Parse and execute code (tool calls are Python function calls)
4. Store execution logs in memory
5. Repeat until `final_answer()` is called

**Tool Execution:**
- In CodeAgent, tools are called as Python functions
- Can iterate over multiple tool calls in one action:
  ```python
  for query in queries:
      print(web_search(query))
  ```

**Sandboxing:**
- Critical for security when executing arbitrary Python code
- Choose executor based on security needs:
  - Local: Fast but less secure
  - E2B/Docker/Modal/Blaxel: Isolated environments
  - Wasm: Browser-based isolation

## File Structure

```
src/smolagents/
  ├── agents.py              # Core agent implementations (~1k lines)
  ├── models.py              # LLM integrations
  ├── tools.py               # Tool abstractions and utilities
  ├── memory.py              # Conversation/execution memory
  ├── local_python_executor.py  # Secure Python interpreter
  ├── remote_executors.py    # Sandboxed execution backends
  ├── default_tools.py       # Built-in tools (PythonInterpreter, FinalAnswer, etc.)
  ├── cli.py                 # CLI entry points
  ├── gradio_ui.py           # Gradio UI components
  ├── mcp_client.py          # MCP (Model Context Protocol) integration
  ├── monitoring.py          # Logging and telemetry
  └── prompts/               # Agent prompt templates (YAML)

tests/
  ├── test_agents.py         # Main agent tests
  ├── test_models.py         # Model integration tests
  ├── test_tools.py          # Tool system tests
  ├── test_local_python_executor.py  # Executor security tests
  └── fixtures/              # Test fixtures

examples/
  ├── multiple_tools.py      # Multi-tool agent examples
  ├── sandboxed_execution.py # Remote executor examples
  ├── rag.py                 # RAG implementation
  ├── async_agent/           # Async agent patterns
  └── smolagents_benchmark/  # Benchmarking code
```

## Testing Considerations

- Test isolation: Agents log to LogLevel.OFF by default in tests (see `conftest.py`)
- Mock models are provided in `tests/fixtures/agents.py`
- Use `pytest -sv` for verbose output (configured in `pyproject.toml`)
- Timeout tests use `@pytest.mark.timeout` for long-running operations
- Remote executor tests may require API keys in environment

## Optional Dependencies

The library has many optional dependency groups in `pyproject.toml`:
- `[toolkit]`: Web search, webpage tools
- `[transformers]`: Local models
- `[litellm]`: Multi-provider access
- `[e2b]`, `[docker]`, `[modal]`, `[blaxel]`: Sandboxing
- `[vision]`: Vision-based web browsing
- `[mcp]`: Model Context Protocol support
- `[gradio]`: UI components
- `[all]`: Everything

When adding features, respect these optional boundaries to keep core lightweight.

## Common Development Patterns

### Adding a New Tool
1. Subclass `Tool` in appropriate module
2. Define `name`, `description`, `inputs`, `output_type`
3. Implement `forward()` method
4. Add tests in `tests/test_tools.py`
5. Consider adding to `TOOL_MAPPING` in `default_tools.py` for CLI access

### Adding a New Model Integration
1. Subclass `Model` or `ApiModel` in `models.py`
2. Implement `__call__()` for single message generation
3. Implement `stream()` for streaming support (optional but recommended)
4. Handle structured output via `response_format` parameter
5. Add tests in `tests/test_models.py`
6. Update README.md with usage example

### Adding a New Executor
1. Subclass `RemotePythonExecutor` in `remote_executors.py`
2. Implement `initialize_runtime()` and `execute_code()`
3. Handle file upload/download if applicable
4. Add cleanup logic for resource management
5. Add tests in `tests/test_remote_executors.py`

## Important Implementation Details

### Code Parsing
- `utils.py`: `extract_code_from_text()` and `parse_code_blobs()` handle extracting Python from LLM outputs
- CodeAgent expects structured JSON output: `{"thought": "...", "code": "..."}`
- Fallback parsing if structured output fails

### Type System
- Tools use JSON Schema for type definitions
- Special types: `image` (base64), `audio` (base64)
- `_function_type_hints_utils.py` converts Python type hints to JSON schema
- `handle_agent_input_types()` / `handle_agent_output_types()` in `agent_types.py`

### Security
- `LocalPythonExecutor` restricts dunder methods, limits operations, and validates imports
- `BASE_BUILTIN_MODULES` lists allowed Python stdlib imports
- Always use sandboxed executors for untrusted code

### Streaming
- Models support streaming via `stream()` method returning `Generator[ChatMessageStreamDelta]`
- `agglomerate_stream_deltas()` combines deltas into full message
- Agents can stream outputs with `stream_outputs=True`

## Hub Integration

Agents and tools can be pushed to/pulled from HuggingFace Hub:
```python
agent.push_to_hub("username/agent-name")
agent = MultiStepAgent.from_hub("username/agent-name")
```

This creates a Space repository with model card and agent definition.
