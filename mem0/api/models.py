"""
Pydantic models for Memory API request/response schemas
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    """Request model for creating memories"""
    messages: Union[str, List[Dict[str, str]]] = Field(
        ..., 
        description="Messages to store in memory. Can be a string or list of message dictionaries"
    )
    user_id: Optional[str] = Field(None, description="User ID for memory scoping")
    agent_id: Optional[str] = Field(None, description="Agent ID for memory scoping")
    run_id: Optional[str] = Field(None, description="Run ID for memory scoping")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata to store")
    infer: bool = Field(True, description="Whether to use LLM for fact extraction")
    memory_type: Optional[str] = Field(None, description="Type of memory to create (e.g., 'procedural_memory')")
    prompt: Optional[str] = Field(None, description="Custom prompt for memory creation")


class MemorySearchRequest(BaseModel):
    """Request model for searching memories"""
    query: str = Field(..., description="Search query")
    user_id: Optional[str] = Field(None, description="User ID for memory scoping")
    agent_id: Optional[str] = Field(None, description="Agent ID for memory scoping")
    run_id: Optional[str] = Field(None, description="Run ID for memory scoping")
    limit: int = Field(100, description="Maximum number of results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    threshold: Optional[float] = Field(None, description="Minimum similarity threshold")


class MemoryUpdateRequest(BaseModel):
    """Request model for updating memories"""
    data: str = Field(..., description="New memory content")


class MemoryGetAllRequest(BaseModel):
    """Request model for getting all memories"""
    user_id: Optional[str] = Field(None, description="User ID for memory scoping")
    agent_id: Optional[str] = Field(None, description="Agent ID for memory scoping")
    run_id: Optional[str] = Field(None, description="Run ID for memory scoping")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    limit: int = Field(100, description="Maximum number of results to return")


class MemoryDeleteAllRequest(BaseModel):
    """Request model for deleting all memories"""
    user_id: Optional[str] = Field(None, description="User ID for memory scoping")
    agent_id: Optional[str] = Field(None, description="Agent ID for memory scoping")
    run_id: Optional[str] = Field(None, description="Run ID for memory scoping")


class MemoryResponse(BaseModel):
    """Response model for memory operations"""
    id: str = Field(..., description="Memory ID")
    memory: str = Field(..., description="Memory content")
    hash: Optional[str] = Field(None, description="Content hash")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")
    user_id: Optional[str] = Field(None, description="User ID")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    run_id: Optional[str] = Field(None, description="Run ID")
    actor_id: Optional[str] = Field(None, description="Actor ID")
    role: Optional[str] = Field(None, description="Message role")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    score: Optional[float] = Field(None, description="Similarity score (for search results)")


class MemoryCreateResponse(BaseModel):
    """Response model for memory creation"""
    results: List[Dict[str, Any]] = Field(..., description="Created memory results")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="Graph relations (if enabled)")


class MemorySearchResponse(BaseModel):
    """Response model for memory search"""
    results: List[MemoryResponse] = Field(..., description="Search results")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="Graph relations (if enabled)")


class MemoryListResponse(BaseModel):
    """Response model for memory listing"""
    results: List[MemoryResponse] = Field(..., description="Memory list")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="Graph relations (if enabled)")


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="Response message")


class MemoryHistoryResponse(BaseModel):
    """Response model for memory history"""
    history: List[Dict[str, Any]] = Field(..., description="Memory history records")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")