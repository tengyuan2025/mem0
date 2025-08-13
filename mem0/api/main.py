"""
FastAPI application for Mem0 Memory operations
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mem0.configs.base import MemoryConfig
from mem0.memory.main import Memory, AsyncMemory
from mem0.api.models import (
    MemoryCreateRequest,
    MemoryCreateResponse,
    MemorySearchRequest, 
    MemorySearchResponse,
    MemoryUpdateRequest,
    MemoryGetAllRequest,
    MemoryListResponse,
    MemoryDeleteAllRequest,
    MemoryResponse,
    MessageResponse,
    MemoryHistoryResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

# Global memory instance
memory_instance: Optional[Memory] = None
async_memory_instance: Optional[AsyncMemory] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global memory_instance, async_memory_instance
    
    # Startup
    logger.info("Starting Mem0 API server...")
    try:
        # 配置本地化和中文优化的 Memory 实例
        config = create_local_memory_config()
        memory_instance = Memory(config)
        async_memory_instance = AsyncMemory(config)
        logger.info("Local Memory instances initialized successfully")
        logger.info(f"Using LLM: {config.llm.config.get('model', 'default')}")
        logger.info(f"Using Embedder: {config.embedder.config.get('model', 'default')}")
        logger.info(f"Using Vector Store: {config.vector_store.provider}")
    except Exception as e:
        logger.error(f"Failed to initialize memory instances: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mem0 API server...")
    memory_instance = None
    async_memory_instance = None


def create_local_memory_config() -> MemoryConfig:
    """创建本地化和中文优化的内存配置"""
    import os
    from mem0.llms.configs import LlmConfig
    from mem0.embeddings.configs import EmbedderConfig
    from mem0.vector_stores.configs import VectorStoreConfig
    
    # 获取配置参数
    llm_provider = os.getenv("MEM0_LLM_PROVIDER", "doubao")
    llm_model = os.getenv("MEM0_LLM_MODEL", "doubao-pro-32k")
    embedder_provider = os.getenv("MEM0_EMBEDDER_PROVIDER", "huggingface")
    embedder_model = os.getenv("MEM0_EMBEDDER_MODEL", "BAAI/bge-large-zh-v1.5")
    vector_store_provider = os.getenv("MEM0_VECTOR_STORE_PROVIDER", "qdrant")
    qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    logger.info(f"Configuring local memory with Chinese optimization...")
    logger.info(f"LLM: {llm_provider}/{llm_model}")
    logger.info(f"Embedder: {embedder_provider}/{embedder_model}")
    
    # LLM配置
    llm_config = {}
    if llm_provider == "doubao":
        doubao_api_key = os.getenv("DOUBAO_API_KEY") or os.getenv("ARK_API_KEY")
        if not doubao_api_key:
            logger.warning("DOUBAO_API_KEY not found, falling back to OpenAI")
            llm_provider = "openai"
            llm_model = os.getenv("MEM0_LLM_MODEL", "gpt-4o-mini")
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("Either DOUBAO_API_KEY or OPENAI_API_KEY is required")
            llm_config = {
                "model": llm_model,
                "temperature": 0.1,
                "max_tokens": 2000,
                "api_key": openai_api_key
            }
        else:
            llm_config = {
                "model": llm_model,
                "temperature": 0.1,
                "max_tokens": 2000,
                "api_key": doubao_api_key,
                "doubao_base_url": os.getenv("DOUBAO_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
            }
    else:
        # 默认使用OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when not using Doubao")
        llm_config = {
            "model": llm_model,
            "temperature": 0.1,
            "max_tokens": 2000,
            "api_key": openai_api_key
        }
    
    # 嵌入模型配置
    embedder_config = {}
    embedding_dims = 1024  # BGE-Large-ZH 默认维度
    
    if embedder_provider == "huggingface":
        embedder_config = {
            "model": embedder_model,
            "embedding_dims": embedding_dims
        }
    else:
        # 默认使用OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
        embedder_provider = "openai"
        embedder_model = os.getenv("MEM0_EMBEDDER_MODEL", "text-embedding-3-small")
        embedding_dims = 1536  # OpenAI text-embedding-3-small 维度
        embedder_config = {
            "model": embedder_model,
            "api_key": openai_api_key
        }
    
    return MemoryConfig(
        # LLM 配置
        llm=LlmConfig(
            provider=llm_provider,
            config=llm_config
        ),
        
        # 嵌入模型配置
        embedder=EmbedderConfig(
            provider=embedder_provider,
            config=embedder_config
        ),
        
        # 向量数据库配置
        vector_store=VectorStoreConfig(
            provider=vector_store_provider,
            config={
                "host": qdrant_host,
                "port": qdrant_port,
                "collection_name": "mem0_memories",
                "embedding_model_dims": embedding_dims,
                "distance": "cosine"
            }
        ),
        
        # 历史数据库路径
        history_db_path="./data/history.db",
        
        # 版本
        version="v1.1"
    )


app = FastAPI(
    title="Mem0 Memory API",
    description="API for managing AI memory operations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_memory() -> Memory:
    """Dependency to get memory instance"""
    if memory_instance is None:
        raise HTTPException(status_code=500, detail="Memory instance not initialized")
    return memory_instance


def get_async_memory() -> AsyncMemory:
    """Dependency to get async memory instance"""
    if async_memory_instance is None:
        raise HTTPException(status_code=500, detail="Async memory instance not initialized")
    return async_memory_instance


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).model_dump()
    )


@app.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint"""
    return MessageResponse(message="Mem0 Memory API is running")


@app.get("/health", response_model=MessageResponse)
async def health_check():
    """Health check endpoint"""
    return MessageResponse(message="API is healthy")


@app.post("/memories", response_model=MemoryCreateResponse, summary="Create Memory", tags=["Memory Operations"])
async def create_memory(
    request: MemoryCreateRequest,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Create new memories from messages.
    
    This endpoint processes messages and creates memories using the configured LLM
    for fact extraction and memory management.
    """
    try:
        result = await memory.add(
            messages=request.messages,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            metadata=request.metadata,
            infer=request.infer,
            memory_type=request.memory_type,
            prompt=request.prompt
        )
        return MemoryCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}", response_model=MemoryResponse, summary="Get Memory", tags=["Memory Operations"])
async def get_memory_by_id(
    memory_id: str,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Retrieve a specific memory by its ID.
    """
    try:
        result = await memory.get(memory_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        return MemoryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/search", response_model=MemorySearchResponse, summary="Search Memories", tags=["Memory Operations"])
async def search_memories(
    request: MemorySearchRequest,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Search memories using semantic similarity.
    
    Returns memories that are semantically similar to the query, optionally
    filtered by user, agent, or run identifiers.
    """
    try:
        result = await memory.search(
            query=request.query,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            limit=request.limit,
            filters=request.filters,
            threshold=request.threshold
        )
        
        # Convert results to MemoryResponse objects
        memories = [MemoryResponse(**item) for item in result["results"]]
        return MemorySearchResponse(
            results=memories,
            relations=result.get("relations")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/all", response_model=MemoryListResponse, summary="Get All Memories", tags=["Memory Operations"])
async def get_all_memories(
    request: MemoryGetAllRequest,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Retrieve all memories, optionally filtered by user, agent, or run identifiers.
    """
    try:
        result = await memory.get_all(
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            filters=request.filters,
            limit=request.limit
        )
        
        # Convert results to MemoryResponse objects
        memories = [MemoryResponse(**item) for item in result["results"]]
        return MemoryListResponse(
            results=memories,
            relations=result.get("relations")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting all memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/memories/{memory_id}", response_model=MessageResponse, summary="Update Memory", tags=["Memory Operations"])
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Update a specific memory by its ID.
    """
    try:
        result = await memory.update(memory_id, request.data)
        return MessageResponse(**result)
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories/{memory_id}", response_model=MessageResponse, summary="Delete Memory", tags=["Memory Operations"])
async def delete_memory(
    memory_id: str,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Delete a specific memory by its ID.
    """
    try:
        result = await memory.delete(memory_id)
        return MessageResponse(**result)
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories", response_model=MessageResponse, summary="Delete All Memories", tags=["Memory Operations"])
async def delete_all_memories(
    request: MemoryDeleteAllRequest,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Delete all memories, optionally filtered by user, agent, or run identifiers.
    
    At least one of user_id, agent_id, or run_id must be provided for safety.
    """
    try:
        result = await memory.delete_all(
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id
        )
        return MessageResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting all memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}/history", response_model=MemoryHistoryResponse, summary="Get Memory History", tags=["Memory Operations"])
async def get_memory_history(
    memory_id: str,
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Retrieve the change history for a specific memory.
    """
    try:
        history = await memory.history(memory_id)
        return MemoryHistoryResponse(history=history)
    except Exception as e:
        logger.error(f"Error getting memory history {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/reset", response_model=MessageResponse, summary="Reset All Memories", tags=["Admin Operations"])
async def reset_memories(
    memory: AsyncMemory = Depends(get_async_memory)
):
    """
    Reset all memories and storage. This is a destructive operation.
    
    WARNING: This will delete ALL memories and cannot be undone.
    """
    try:
        await memory.reset()
        return MessageResponse(message="All memories have been reset successfully")
    except Exception as e:
        logger.error(f"Error resetting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)