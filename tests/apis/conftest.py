"""
Pytest configuration for API tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import tempfile
import os

from mem0.api.main import app, get_memory, get_async_memory
from mem0.memory.main import Memory, AsyncMemory


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def mock_memory():
    """Mock Memory instance"""
    mock = Mock(spec=Memory)
    return mock


@pytest.fixture
def mock_async_memory():
    """Mock AsyncMemory instance"""
    mock = AsyncMock(spec=AsyncMemory)
    return mock


@pytest.fixture
def client(mock_memory, mock_async_memory):
    """Test client with mocked dependencies"""
    app.dependency_overrides[get_memory] = lambda: mock_memory
    app.dependency_overrides[get_async_memory] = lambda: mock_async_memory
    
    client = TestClient(app)
    yield client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "id": "test-memory-id",
        "memory": "User likes pizza",
        "hash": "abc123",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": None,
        "user_id": "test-user",
        "agent_id": None,
        "run_id": None,
        "actor_id": None,
        "role": "user",
        "metadata": {"source": "test"},
        "score": 0.95
    }


@pytest.fixture
def sample_create_request():
    """Sample memory creation request"""
    return {
        "messages": "I love pizza",
        "user_id": "test-user",
        "infer": True
    }


@pytest.fixture
def sample_search_request():
    """Sample memory search request"""
    return {
        "query": "food preferences",
        "user_id": "test-user",
        "limit": 10
    }


@pytest.fixture
def sample_create_response():
    """Sample memory creation response"""
    return {
        "results": [
            {
                "id": "test-memory-id",
                "memory": "User likes pizza",
                "event": "ADD"
            }
        ]
    }