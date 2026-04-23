# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graphiti is a Python framework for building and querying temporally-aware knowledge graphs, designed for AI agents operating in dynamic environments. It provides real-time incremental updates to a knowledge graph represented as nodes (entities, episodes, communities) and edges (relationships) stored in either Neo4j or FalkorDB.

Core capabilities:
- **Bi-temporal tracking**: Explicit tracking of event occurrence and ingestion times for point-in-time queries
- **Incremental updates**: Episodes are continuously integrated without batch recomputation
- **Hybrid retrieval**: Combines semantic embeddings, keyword (BM25), and graph traversal
- **Custom entity ontology**: Developer-defined entities via Pydantic models
- **LLM-driven extraction**: Uses structured output from LLMs to extract entities and relationships

## Development Commands

Install dependencies:
```bash
make install
# or: uv sync --extra dev
```

Format code (imports and style):
```bash
make format
```

Lint code (ruff + pyright):
```bash
make lint
```

Run tests:
```bash
make test
# or: uv run pytest
```

Run integration tests (requires database and API keys):
```bash
# Set environment variables first
export TEST_OPENAI_API_KEY=...
export TEST_OPENAI_MODEL=...
export TEST_URI=bolt://localhost:7687  # or falkor://localhost:6379
export TEST_USER=neo4j
export TEST_PASSWORD=password

# Run tests including integration tests
uv run pytest -m integration
```

Run specific test file:
```bash
uv run pytest tests/test_graphiti_int.py
```

Run all checks (format, lint, test):
```bash
make check
```

## Project Structure

### Core Components

- **`graphiti_core/graphiti.py`**: Main `Graphiti` class - entry point for all operations. Orchestrates episode ingestion, search, and graph maintenance.

- **`graphiti_core/nodes.py`**: Node types
  - `EpisodicNode`: Represents raw episodes (text, json, messages)
  - `EntityNode`: Semantic entities extracted from episodes (people, places, organizations, etc.)
  - `CommunityNode`: Clusters of related entities for hierarchical search

- **`graphiti_core/edges.py`**: Edge types
  - `EpisodicEdge`: Links episodes to mentioned entities
  - `EntityEdge`: Relationships between entities (the "facts")
  - `CommunityEdge`: Links entities to their communities

- **`graphiti_core/driver/`**: Graph database drivers
  - `driver.py`: Abstract base class defining the driver interface
  - `neo4j_driver.py`: Neo4j implementation
  - `falkordb_driver.py`: FalkorDB implementation (Redis-based graph DB)

- **`graphiti_core/llm_client/`**: LLM provider integrations
  - `openai_client.py`: OpenAI and Azure OpenAI
  - `anthropic_client.py`: Anthropic Claude
  - `gemini_client.py`: Google Gemini
  - `groq_client.py`: Groq
  - All support structured output for entity/relationship extraction

- **`graphiti_core/embedder/`**: Embedding provider integrations
  - `openai.py`: OpenAI embeddings
  - `azure_openai.py`: Azure OpenAI embeddings
  - `gemini.py`: Google Gemini embeddings
  - `voyage.py`: Voyage AI embeddings

- **`graphiti_core/cross_encoder/`**: Reranking implementations
  - `openai_reranker_client.py`: Uses LLM log probabilities for reranking
  - `gemini_reranker_client.py`: Gemini-based reranking
  - `bge_reranker_client.py`: BGE cross-encoder models

- **`graphiti_core/search/`**: Search and retrieval
  - `search.py`: Main search orchestration
  - `search_config.py`: Configurable search parameters
  - `search_config_recipes.py`: Predefined search configurations (e.g., `EDGE_HYBRID_SEARCH_NODE_DISTANCE`, `NODE_HYBRID_SEARCH_RRF`)
  - `search_filters.py`: Temporal and group-based filtering
  - `search_utils.py`: Utilities for candidate retrieval and reranking

- **`graphiti_core/utils/maintenance/`**: Graph maintenance operations
  - `node_operations.py`: Extract and resolve nodes from episodes
  - `edge_operations.py`: Extract and resolve edges, handle duplicates
  - `community_operations.py`: Build and update community clusters
  - `temporal_operations.py`: Handle edge invalidation based on temporal constraints
  - `graph_data_operations.py`: Database schema setup and episode retrieval

- **`graphiti_core/utils/bulk_utils.py`**: Bulk processing for episode ingestion (parallel processing of multiple episodes)

- **`graphiti_core/prompts/`**: LLM prompts for extraction and analysis
  - `extract_nodes.py`: Entity extraction prompts
  - `extract_edges.py`: Relationship extraction prompts
  - `dedupe_nodes.py`, `dedupe_edges.py`: Deduplication prompts
  - `summarize_nodes.py`: Node summarization prompts
  - `invalidate_edges.py`: Edge invalidation prompts

### Supporting Directories

- **`examples/`**: Working examples demonstrating usage patterns
  - `quickstart/`: Basic usage with Neo4j and FalkorDB
  - `langgraph-agent/`: Integration with LangGraph agents
  - `podcast/`, `ecommerce/`, `wizard_of_oz/`: Domain-specific examples

- **`tests/`**: Test suite
  - `test_*_int.py`: Integration tests (require database + API keys)
  - `driver/`, `llm_client/`, `embedder/`: Module-specific tests

- **`mcp_server/`**: Model Context Protocol server implementation for AI assistants

- **`server/`**: REST API service (FastAPI)

## Architecture Notes

### Episode Ingestion Pipeline

Ingestion is the core operation where new data is added to the graph:

1. **Episode Creation**: Text, JSON, or message data is wrapped in `EpisodicNode`
2. **Entity Extraction** (`extract_nodes`): LLM extracts entities with types and summaries
3. **Node Resolution** (`resolve_extracted_nodes`): Deduplicate and merge entities with existing nodes
4. **Edge Extraction** (`extract_edges`): LLM extracts relationships between entities
5. **Edge Resolution** (`resolve_extracted_edges`): Deduplicate and invalidate contradicting edges
6. **Graph Update**: Nodes and edges are persisted to the database with embeddings
7. **Community Building** (optional): Entities are clustered into communities

The pipeline uses high concurrency by default, controlled by `SEMAPHORE_LIMIT` environment variable (default: 10). Increase for better performance if LLM provider allows.

### Bi-Temporal Model

Edges track two timestamps:
- **`valid_at`**: When the fact occurred in the real world
- **`created_at`**: When the fact was ingested into the system

This enables:
- Point-in-time queries ("What did we know on June 1st?")
- Temporal invalidation (new facts can invalidate old ones)
- Historical reasoning

### Search Architecture

Search combines three retrieval methods:
1. **Semantic**: Embedding-based similarity (using configured embedder)
2. **Keyword**: BM25 full-text search (built into graph database)
3. **Graph**: Traversal-based distance from reference nodes

Reranking strategies:
- **RRF (Reciprocal Rank Fusion)**: Combines semantic + keyword ranks
- **Cross-encoder**: LLM-based relevance scoring
- **Graph distance**: Prioritizes facts close to a reference node in the graph

Search recipes in `search_config_recipes.py` bundle these strategies for different use cases.

### Custom Entity Types

Define custom entity types via Pydantic:

```python
from graphiti_core.utils.ontology_utils.entity_types_utils import validate_entity_types

entity_types = {
    'Person': ['name', 'age', 'occupation'],
    'Organization': ['name', 'industry'],
    'Location': ['name', 'country']
}
validate_entity_types(entity_types)

graphiti = Graphiti(..., entity_types=entity_types)
```

## Environment Variables

Required for basic operation:
- `OPENAI_API_KEY`: Required if using OpenAI (default LLM and embedder)

Database connection (Neo4j):
- `NEO4J_URI`: Default `bolt://localhost:7687`
- `NEO4J_USER`: Default `neo4j`
- `NEO4J_PASSWORD`: Required

Database connection (FalkorDB):
- `FALKORDB_URI`: Default `falkor://localhost:6379`
- `FALKORDB_USER`: Optional
- `FALKORDB_PASSWORD`: Optional

Optional LLM providers:
- `ANTHROPIC_API_KEY`: For Anthropic Claude models
- `GROQ_API_KEY`: For Groq models

Performance:
- `SEMAPHORE_LIMIT`: Concurrent operations limit (default: 10, increase for faster ingestion)
- `USE_PARALLEL_RUNTIME`: Enable Neo4j parallel runtime (requires Enterprise edition)

Testing:
- `TEST_OPENAI_API_KEY`, `TEST_OPENAI_MODEL`: For integration tests
- `TEST_URI`, `TEST_USER`, `TEST_PASSWORD`: Test database credentials
- `TEST_ANTHROPIC_API_KEY`: For Anthropic integration tests

Telemetry:
- `GRAPHITI_TELEMETRY_ENABLED`: Set to `false` to disable anonymous telemetry

## Code Style

This project uses:
- **ruff**: Linting and formatting (100 char line length, single quotes)
- **pyright**: Static type checking (basic mode, Python 3.10+)
- **pytest**: Testing framework with async support

Code style guidelines:
- Use single quotes for strings
- 100 character line length
- Type hints required (enforced by pyright)
- All async functions use `async`/`await`

## Integration Patterns

### Adding a New LLM Provider

1. Create `graphiti_core/llm_client/your_provider_client.py`
2. Extend `LLMClient` base class
3. Add optional dependency to `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   your-provider = ["your-package>=1.0.0"]
   dev = [..., "your-package>=1.0.0"]  # Also add to dev
   ```
4. Use TYPE_CHECKING pattern for imports to avoid hard dependencies
5. Add tests in `tests/llm_client/`

### Adding a New Database Driver

1. Create `graphiti_core/driver/your_db_driver.py`
2. Extend `GraphDriver` base class and implement all abstract methods
3. Add to `GraphProvider` enum in `driver.py`
4. Register Cypher/query translations if syntax differs from Neo4j
5. Add integration tests in `tests/driver/`

### Adding a New Embedder

1. Create `graphiti_core/embedder/your_provider.py`
2. Extend `EmbedderClient` base class
3. Follow optional dependency pattern (same as LLM providers)
4. Add tests in `tests/embedder/`

## Important Notes

- **Structured Output Required**: Graphiti works best with LLM providers that support structured output (OpenAI, Gemini). Other providers may fail during extraction.

- **Database Schema**: Call `await graphiti.build_indices_and_constraints()` once before first use to create required indices.

- **Concurrency**: Default `SEMAPHORE_LIMIT=10` is conservative to avoid rate limits. Increase for better performance.

- **Testing**: Integration tests are marked with `@pytest.mark.integration` and require external services (database, LLM API).

- **Breaking Changes**: For architectural changes >500 LOC, create a GitHub issue (RFC) for discussion before submitting a PR.

## Common Development Workflows

**Adding a new episode to test graph**:
```python
from graphiti_core import Graphiti

graphiti = Graphiti(...)
await graphiti.add_episode(
    name="test_episode",
    episode_body="Your text content here",
    source_description="Where this came from"
)
```

**Searching the graph**:
```python
from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF

results = await graphiti.search(
    "query text",
    config=EDGE_HYBRID_SEARCH_RRF,
    num_results=10
)
```

**Custom database name**:
```python
from graphiti_core.driver.neo4j_driver import Neo4jDriver

driver = Neo4jDriver(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="my_custom_db"
)
graphiti = Graphiti(graph_driver=driver)
```
