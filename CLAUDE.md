# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mem0 is a self-hosted intelligent memory system for AI assistants and agents, optimized for Chinese language and supporting domestic LLM services in China.

## Architecture

### Core Components

1. **Memory Manager** (`app.py:99-500`) - Centralized memory operations handling CRUD operations and vector search
2. **Provider System** - Factory pattern for swappable LLMs, embeddings, and vector stores:
   - LLMs: DashScope (Alibaba), QianFan (Baidu), ZhipuAI, DeepSeek, Moonshot, OpenAI
   - Embeddings: Local HuggingFace models (BAAI/bge-*), API-based embeddings, Sentence Transformers
   - Vector DBs: ChromaDB, Qdrant, FAISS, Milvus (optional)
   - Graph DBs: Neo4j (knowledge graphs)
3. **API Layer** (`app.py:600-1200`) - FastAPI-based RESTful endpoints with JWT authentication
4. **Storage Layer** - MySQL/SQLite for metadata, vector databases for embeddings, Redis for caching

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

# Download Chinese models (for local embeddings)
python download_chinese_model.py
python download_models.py
```

### Running the Service
```bash
# Start API server using the automated script (recommended)
chmod +x start.sh
./start.sh

# Or start manually
python app.py

# Start database services only (if needed)
docker-compose -f docker-compose-db.yml up -d
```

### Testing
```bash
# Run specific test file
python test/test_chinese.py           # Test Chinese language processing
python test/test_api.py               # Test API endpoints  
python test/test_minimal.py           # Basic functionality test
python test/test_multiuser_memory.py  # Multi-user scenarios
python test/test_mysql.py             # MySQL database operations
python test/test_embedding.py         # Embedding models test

# Health check
python check_health.py

# Inspect ChromaDB data
python inspect_chromadb.py
```

### Database Services (Docker)
```bash
# Start database services for local development
docker-compose -f docker-compose-db.yml up -d

# Check database service status
docker-compose -f docker-compose-db.yml ps

# View database logs
docker-compose -f docker-compose-db.yml logs -f

# Stop database services
docker-compose -f docker-compose-db.yml down

# Start specific database services
docker-compose -f docker-compose-db.yml up -d postgres redis chromadb neo4j
```

## Configuration

### Environment Variables (.env)

Key configuration sections:
- **LLM_PROVIDER**: Choose from `dashscope`, `qianfan`, `zhipu`, `deepseek`, `moonshot`, `openai`
- **EMBEDDING_PROVIDER**: Use `local_huggingface` for offline, or provider-specific embeddings
- **VECTOR_DB**: Select `chroma`, `qdrant`, `faiss`, or `milvus`
- **API_SECRET_KEY**: Required for API authentication (JWT)
- **Database configs**: MySQL, PostgreSQL, Redis settings
- **CORS settings**: Configure allowed origins for web clients

### Provider Configuration Examples

```env
# DashScope (Alibaba Cloud) - Recommended
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-key
DASHSCOPE_MODEL=qwen-max

# Local Chinese Embeddings (no API needed) - Recommended
EMBEDDING_PROVIDER=local_huggingface
HF_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# Alternative Chinese embedding models
# BAAI/bge-large-zh-v1.5 - Best quality (1.3GB)
# BAAI/bge-base-zh-v1.5 - Balanced (400MB) 
# BAAI/bge-small-zh-v1.5 - Fastest (95MB)

# Redis caching (optional but recommended)
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
```

## API Endpoints

Primary endpoints with authentication via `Authorization: Bearer {token}`:

- `POST /api/v1/memories/add` - Add new memory with user_id and messages
- `POST /api/v1/memories/search` - Search memories by query and filters
- `POST /api/v1/chat` - Chat with memory context
- `GET /api/v1/users/{user_id}/memories` - Get all user memories
- `POST /api/v1/memories/update` - Update existing memory
- `POST /api/v1/memories/delete` - Delete memory by ID

Full API documentation available at `http://localhost:9000/docs` when running.

## File Structure

```
mem0/
├── app.py                      # Main FastAPI application
├── mysql_handler.py            # MySQL database operations
├── mem0/                       # Core package (provider implementations)
│   ├── memory/                # Memory CRUD operations
│   ├── llms/                 # LLM provider implementations
│   ├── embeddings/           # Embedding providers
│   └── vector_stores/        # Vector database implementations
├── test/                       # Test files for different features
│   ├── test_api.py           # API endpoint tests
│   ├── test_chinese.py       # Chinese language tests
│   ├── test_minimal.py       # Basic functionality tests
│   └── ...                   # Other test modules
├── docker-compose-db.yml       # Database services configuration
└── start.sh                    # Local Python environment startup script
```

## Important Considerations

- **Authentication**: Always use secure API_SECRET_KEY in production
- **Chinese Text**: The system includes specialized handling for Chinese tokenization and similarity matching
- **Provider Selection**: Choose appropriate LLM/embedding providers based on deployment region
- **Data Privacy**: All data can be stored locally when using local embeddings and FAISS
- **Performance**: Use Redis caching and appropriate worker counts for production deployments
- **Memory Scope**: Memories can be scoped by user_id, session_id, and custom metadata filters
- **Monitoring**: Prometheus metrics integration available, health check endpoints at `/health`
- **Deployment Mode**: Local Python environment with optional Docker for database services

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check ports 9000 (API), 8001 (ChromaDB), 6333 (Qdrant) are available
2. **Model download failures**: First-time setup downloads models (~1-2GB), ensure stable connection
3. **Database connection issues**: Verify database services are running with `docker-compose -f docker-compose-db.yml ps`
4. **Memory errors**: Ensure adequate system memory for large embedding models
5. **API authentication**: Ensure Bearer token is included in request headers