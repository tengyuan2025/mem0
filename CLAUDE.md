# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build & Package
- `hatch build` - Build the package
- `hatch publish` - Publish to PyPI

### Code Quality
- `hatch run format` or `make format` - Format code with ruff
- `hatch run lint` or `make lint` - Lint code with ruff
- `hatch run lint-fix` - Fix linting issues automatically
- `make sort` - Sort imports with isort

### Testing
- `hatch run test` or `make test` - Run all tests
- `hatch run dev_py_3_9:test` - Run tests on Python 3.9
- `hatch run dev_py_3_10:test` - Run tests on Python 3.10
- `hatch run dev_py_3_11:test` - Run tests on Python 3.11

### Environment Setup
- `hatch env create` or `make install` - Create development environment
- `make install_all` - Install all optional dependencies

### Documentation
- `make docs` - Start documentation dev server (requires mintlify)

## Architecture Overview

Mem0 is a memory layer for AI applications with a pluggable architecture:

### Core Components
- **Memory Core** (`mem0/memory/`): Main `Memory` and `AsyncMemory` classes for memory operations
- **LLMs** (`mem0/llms/`): Language model providers (OpenAI, Anthropic, etc.) for fact extraction and processing
- **Embeddings** (`mem0/embeddings/`): Embedding model providers for vector representations
- **Vector Stores** (`mem0/vector_stores/`): Storage backends (Qdrant, Chroma, Pinecone, etc.)
- **Configuration** (`mem0/configs/`): Type-safe configuration system
- **Factory Pattern** (`mem0/utils/factory.py`): Dynamic provider loading

### Data Flow
1. **Add**: Messages → Fact extraction (LLM) → Embedding → Vector storage → History tracking
2. **Search**: Query → Embedding → Vector search → Result formatting
3. **Update/Delete**: Memory modification with LLM-driven decisions

### Key Classes
- `Memory`/`AsyncMemory`: Main entry points for memory operations
- `MemoryBase`: Abstract base class for memory implementations  
- `LLMBase`, `EmbeddingBase`, `VectorStoreBase`: Provider interfaces
- `MemoryConfig`: Central configuration object

### Memory Scoping
- Memories are scoped by `user_id`, `agent_id`, or `run_id`
- Metadata-based filtering ensures data isolation
- Graph database support for entity relationships (optional)

## Project Structure

- `mem0/` - Main package with core functionality
- `embedchain/` - Legacy embedchain code (excluded from linting)
- `openmemory/` - OpenMemory UI and API (excluded from linting)
- `tests/` - Test suites for all components
- `examples/` - Usage examples and demos
- `docs/` - Documentation source files

## Development Notes

- Python 3.9+ required
- Uses hatch for package management and development
- Ruff for code formatting and linting (line length: 120)
- SQLite for history tracking, vector stores for semantic search
- Optional graph database support via Neo4j
- Modular provider system allows easy extension