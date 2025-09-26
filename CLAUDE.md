# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mem0 is a self-hosted intelligent memory system for AI assistants and agents, optimized for Chinese language and supporting domestic LLM services in China.

## Architecture

### Core Components

1. **Memory Manager** (`app.py:99-500`) - Centralized memory operations handling CRUD operations and vector search
2. **Provider System** - Factory pattern for swappable LLMs, embeddings, and vector stores:
   - LLMs: DashScope (Alibaba), QianFan (Baidu), ZhipuAI, DeepSeek, OpenAI
   - Embeddings: Local HuggingFace models (BAAI/bge-*), API-based embeddings
   - Vector DBs: ChromaDB, Qdrant, FAISS
3. **API Layer** (`app.py:600-1200`) - FastAPI-based RESTful endpoints with JWT authentication
4. **Storage Layer** - MySQL/SQLite for metadata, vector databases for embeddings

### Key Design Patterns

- **Factory Pattern**: Provider selection based on environment configuration
- **Async/Sync Dual APIs**: Support for both synchronous and asynchronous operations
- **Scoped Memory**: Memories organized by user_id, session_id, and metadata filters
- **Chinese Optimization**: Specialized tokenization and similarity algorithms for Chinese text

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env to configure your LLM providers and API keys
```

### Running the Service
```bash
# Start API server
python app.py

# Start with Docker Compose (includes all databases)
docker-compose up -d

# Use the interactive start script
./start.sh
```

### Testing
```bash
# Run specific test file
python test_chinese.py      # Test Chinese language processing
python test_api.py          # Test API endpoints
python test_minimal.py      # Basic functionality test
python test_multiuser_memory.py  # Multi-user scenarios

# Run pytest (if tests are properly configured)
pytest -v

# Test API endpoints manually
python test_api.py
```

### Docker Operations
```bash
# Build and run with Docker Compose
docker-compose up -d        # Start all services
docker-compose logs -f mem0-api  # View API logs
docker-compose down         # Stop all services

# China-specific deployment
docker-compose -f docker-compose-china.yml up -d
```

## Configuration

### Environment Variables (.env)

Key configuration sections:
- **LLM_PROVIDER**: Choose from `dashscope`, `qianfan`, `zhipu`, `deepseek`, `openai`
- **EMBEDDING_PROVIDER**: Use `local_huggingface` for offline, or provider-specific embeddings
- **VECTOR_DB**: Select `chroma`, `qdrant`, or `faiss`
- **API_SECRET_KEY**: Required for API authentication
- **Database configs**: MySQL, PostgreSQL, Redis settings

### Provider Configuration Examples

```env
# DashScope (Alibaba Cloud)
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-key
DASHSCOPE_MODEL=qwen-max

# Local Chinese Embeddings (no API needed)
EMBEDDING_PROVIDER=local_huggingface
HF_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

## API Endpoints

Primary endpoints with authentication via `Authorization: Bearer {token}`:

- `POST /api/v1/memories/add` - Add new memory with user_id and messages
- `POST /api/v1/memories/search` - Search memories by query and filters
- `POST /api/v1/chat` - Chat with memory context
- `GET /api/v1/users/{user_id}/memories` - Get all user memories
- `POST /api/v1/memories/update` - Update existing memory
- `POST /api/v1/memories/delete` - Delete memory by ID

Full API documentation available at `http://localhost:8000/docs` when running.

## File Structure

```
mem0/
├── app.py                 # Main FastAPI application
├── mysql_handler.py       # MySQL database operations
├── mem0/                  # Core package (provider implementations)
│   ├── memory/           # Memory CRUD operations
│   ├── llms/            # LLM provider implementations
│   ├── embeddings/      # Embedding providers
│   └── vector_stores/   # Vector database implementations
├── test_*.py             # Test files for different features
├── docker-compose*.yml   # Docker deployment configs
└── start.sh             # Interactive startup script
```

## Important Considerations

- **Authentication**: Always use secure API_SECRET_KEY in production
- **Chinese Text**: The system includes specialized handling for Chinese tokenization and similarity matching
- **Provider Selection**: Choose appropriate LLM/embedding providers based on deployment region
- **Data Privacy**: All data can be stored locally when using local embeddings and FAISS
- **Performance**: Use Redis caching and appropriate worker counts for production deployments