# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ragas is an evaluation framework for LLM and RAG (Retrieval-Augmented Generation) applications. It provides:
- **Objective metrics** for evaluating LLM outputs (faithfulness, answer relevance, context precision, etc.)
- **Test data generation** for creating comprehensive test datasets
- **Integrations** with popular LLM frameworks (LangChain, LlamaIndex, Haystack, OpenAI, etc.)
- **Optimizers** including DSPy and genetic algorithms for prompt optimization

The codebase is organized as a monorepo with the main Ragas library and experimental features integrated together.

## Essential Development Commands

All development should use the Makefile commands. Never invoke tools directly - always use `make` or `uv run` prefix.

### Setup
```bash
make install-minimal    # Fast setup with core dev tools (79 packages) - RECOMMENDED for most work
make install           # Full environment with all features (ML packages, observability tools)
make help              # Show all available commands
```

### Code Quality
```bash
make format           # Format and lint all code (includes import sorting and unused imports cleanup)
make type            # Type check all code with pyright
make check           # Quick health check (format + type, no tests)
```

### Testing
```bash
make test            # Run all unit tests
make test-all        # Run all unit tests including notebook tests
make test-e2e        # Run end-to-end integration tests
make benchmarks      # Run performance benchmarks
```

### Running Tests Selectively
```bash
make test k="test_name"           # Run specific test by name
uv run pytest tests/unit/test_specific.py    # Run specific test file
uv run pytest tests/unit -k "keyword"        # Run tests matching keyword
```

### CI/CD
```bash
make run-ci          # Run complete CI pipeline (format check + type check + tests) - mirrors GitHub CI
make run-ci-fast     # Fast CI check for quick feedback (2-3 minutes)
make clean          # Clean all generated files
```

### Documentation
```bash
make build-docs      # Build all documentation
make serve-docs      # Serve documentation locally at http://localhost:8000
```

## Architecture and Code Organization

### Core Components

**1. Metrics System (`src/ragas/metrics/`)**
- **Base classes**: `Metric`, `SingleTurnMetric`, `MultiTurnMetric`, `MetricWithLLM`, `MetricWithEmbeddings` in `base.py`
- **Metric types**: Binary, Discrete, Continuous, Ranking (defined by `MetricOutputType`)
- **LLM-based metrics**: AspectCritic, Faithfulness, AnswerRelevance, ContextPrecision, etc.
- **Traditional metrics**: BLEU, ROUGE, ChrF scores, string similarity
- **Collections**: Pre-configured metric sets in `metrics/collections/`
- All metrics inherit from `Metric` base class and implement `_ascore()` for async scoring

**2. Evaluation (`src/ragas/evaluation.py`)**
- Main entry point: `evaluate()` and `aevaluate()` functions
- Takes `Dataset` or `EvaluationDataset` and list of metrics
- Returns `EvaluationResult` with scores and metadata
- Supports callbacks, cost tracking, and custom run configurations
- Uses `Executor` for parallel metric computation

**3. LLM Integration (`src/ragas/llms/`)**
- **Factory pattern**: Use `llm_factory(model_name, client=...)` instead of direct wrappers
- Supports OpenAI, Anthropic, LangChain, LlamaIndex, Haystack, OCI GenAI, LiteLLM
- Base classes: `BaseRagasLLM`, `InstructorBaseRagasLLM` for structured outputs
- Legacy wrappers (`LangchainLLMWrapper`, `LlamaIndexLLMWrapper`) are deprecated

**4. Testset Generation (`src/ragas/testset/`)**
- **Graph-based approach**: Uses knowledge graphs for test generation
- **Synthesizers**: Generate different types of test questions (simple, reasoning, multi-context, etc.)
- **Transforms**: Extract entities, relationships, and structure from documents
- Main interface: `TestsetGenerator` class

**5. Optimizers (`src/ragas/optimizers/`)**
- **DSPy integration**: `DSPyOptimizer` with MIPROv2 for prompt optimization
- **Genetic algorithms**: For evolutionary optimization of prompts and configurations
- Optimizers work with metrics to improve evaluation prompts

**6. Integrations (`src/ragas/integrations/`)**
- LangChain, LangSmith, LlamaIndex tracking
- Observability: Langfuse, MLflow, Helicone, Opik, Phoenix
- AI frameworks: Griptape, Amazon Bedrock, R2R, Swarm
- AG UI protocol for user interfaces

### Data Schemas

**Dataset Types** (`src/ragas/dataset_schema.py`):
- `SingleTurnSample`: Single input-output interaction with optional retrieved contexts
- `MultiTurnSample`: Multi-turn conversation with user and system messages
- `EvaluationDataset`: Collection of samples with metadata
- `EvaluationResult`: Contains evaluated samples with scores

**Standard Column Names**:
- `user_input`: The input/question from the user
- `response`: The LLM's response/answer
- `retrieved_contexts`: List of retrieved context chunks (for RAG)
- `reference_contexts`: Ground truth contexts
- `reference`: Ground truth answer/response

### Key Design Patterns

1. **Async-first**: All metrics use `_ascore()` async method, synchronous `score()` is a wrapper
2. **Prompt-based metrics**: Many metrics use `FewShotPydanticPrompt` for LLM-based evaluation
3. **Factory pattern**: Use `llm_factory()` and `embedding_factory()` for creating LLM/embedding instances
4. **Column mapping**: Use `column_map` parameter to map custom column names to expected names
5. **Caching**: Built-in caching support via `ragas.cache` module for LLM responses and embeddings

## Code Quality Standards

### Type Checking
- Python 3.9+ with type hints throughout
- Configured in `pyproject.toml` under `[tool.pyright]`
- Run with `make type` before committing
- Type checking mode: "basic"

### Formatting and Linting
- **ruff**: Format, lint, and auto-fix (includes import sorting via isort)
- Line length: 88 characters
- Quote style: double quotes
- Run `make format` which does:
  1. `ruff format` - code formatting
  2. `ruff check --fix-only` - auto-fix issues including unused imports
  3. `ruff check` - final validation

### Testing
- **pytest** with `pytest-asyncio` for async tests
- **nbmake** for notebook testing
- Test organization:
  - `tests/unit/` - Fast, isolated component tests
  - `tests/e2e/` - Integration tests for complete workflows
  - `tests/benchmarks/` - Performance tests
- CI uses parallel testing: `pytest --dist loadfile -n auto`

### Pre-commit Hooks
- Automatically installed with `make install-minimal` or `make install`
- Runs format and type checks before commits
- Never bypass with `--no-verify` unless explicitly instructed

## Common Development Patterns

### Adding a New Metric

1. Create file in `src/ragas/metrics/_your_metric.py`
2. Inherit from appropriate base class (`SingleTurnMetric`, `MultiTurnMetric`, `MetricWithLLM`, etc.)
3. Define `_required_columns` dict mapping `MetricType` to required column names
4. Implement `_ascore()` method returning `MetricResult`
5. Add to `src/ragas/metrics/__init__.py`
6. Add tests in `tests/unit/metrics/test_your_metric.py`
7. Update metric collections if appropriate

### Running Single Tests During Development
```bash
# Test a specific metric
uv run pytest tests/unit/metrics/test_faithfulness.py -v

# Test with specific LLM (set API key first)
OPENAI_API_KEY=xxx uv run pytest tests/unit/metrics/test_faithfulness.py

# Debug mode with print statements
uv run pytest tests/unit/metrics/test_faithfulness.py -s
```

### Working with LLMs
```python
# CORRECT: Use factory pattern
from ragas.llms import llm_factory
llm = llm_factory("gpt-4o")

# DEPRECATED: Don't use direct wrappers
# from ragas.llms import LangchainLLMWrapper  # DON'T DO THIS
```

### Using Datasets
```python
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset

# Create samples
samples = [
    SingleTurnSample(
        user_input="What is RAG?",
        response="RAG is Retrieval-Augmented Generation...",
        retrieved_contexts=["Context 1", "Context 2"]
    )
]

# Create dataset
dataset = EvaluationDataset(samples=samples)
```

## Environment Variables

- `OPENAI_API_KEY`: For OpenAI models (most commonly used)
- `ANTHROPIC_API_KEY`: For Claude models
- `RAGAS_DO_NOT_TRACK`: Set to `true` to disable analytics (telemetry)
- `__RAGAS_DEBUG_TRACKING`: Set to `true` for debug tracking in CI

## Python Version Support

- **Officially supported**: Python 3.9 - 3.12
- **Python 3.13**: Not officially supported yet (NumPy compatibility issues on some platforms)
  - If needed, use Python 3.12: `uv python install 3.12 && uv venv -p 3.12`

## Monorepo Structure

```
/
├── src/ragas/              # Main source code
│   ├── metrics/           # Evaluation metrics
│   ├── llms/             # LLM integrations
│   ├── testset/          # Test dataset generation
│   ├── optimizers/       # Prompt optimization
│   ├── integrations/     # Third-party integrations
│   ├── embeddings/       # Embedding model support
│   └── evaluation.py     # Main evaluation interface
├── tests/
│   ├── unit/            # Unit tests
│   ├── e2e/             # End-to-end tests
│   └── benchmarks/      # Performance benchmarks
├── examples/            # Example code (separate package: ragas-examples)
├── docs/                # Documentation
├── pyproject.toml       # Dependencies and configuration
└── Makefile            # Build commands
```

## Working with Examples

The `examples/` directory is a separate package (`ragas-examples`) that can be installed independently:
```bash
uv pip install -e . -e ./examples
python -m ragas_examples.benchmark_llm.prompt
```

## Key Files to Know

- `src/ragas/metrics/base.py` - Base classes for all metrics
- `src/ragas/evaluation.py` - Main evaluation functions
- `src/ragas/dataset_schema.py` - Dataset and sample schemas
- `src/ragas/llms/base.py` - LLM base classes and factory
- `src/ragas/prompt/` - Prompt templates and few-shot learning
- `pyproject.toml` - All dependencies, tool configs, and project metadata
- `Makefile` - All development commands (use `make help`)

## Analytics and Telemetry

Ragas collects minimal, anonymized usage data to improve the product. All data collection code is open source in `src/ragas/_analytics.py`. To opt out, set `RAGAS_DO_NOT_TRACK=true`.

## CI/CD Configuration

The CI pipeline uses the same commands as local development:
1. Format check: `ruff format --check` and `ruff check`
2. Type check: `pyright src`
3. Unit tests: `pytest --nbmake tests/unit --dist loadfile -n auto`
4. E2E tests: `pytest --nbmake tests/e2e`

Multi-OS testing: Ubuntu, macOS, Windows across Python 3.9-3.12.

Always run `make run-ci` before submitting PRs.
