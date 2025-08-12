"""
Test cases for Memory API endpoints
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient


class TestMemoryAPI:
    """Test cases for memory operations API"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Mem0 Memory API is running"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["message"] == "API is healthy"
    
    def test_create_memory_success(self, client, mock_async_memory, sample_create_request, sample_create_response):
        """Test successful memory creation"""
        mock_async_memory.add.return_value = sample_create_response
        
        response = client.post("/memories", json=sample_create_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == "test-memory-id"
        
        # Verify mock was called with correct parameters
        mock_async_memory.add.assert_called_once()
        call_args = mock_async_memory.add.call_args
        assert call_args.kwargs["messages"] == "I love pizza"
        assert call_args.kwargs["user_id"] == "test-user"
        assert call_args.kwargs["infer"] is True
    
    def test_create_memory_validation_error(self, client, mock_async_memory):
        """Test memory creation with validation error"""
        mock_async_memory.add.side_effect = ValueError("At least one of user_id, agent_id, or run_id must be provided")
        
        response = client.post("/memories", json={
            "messages": "Test message"
            # Missing required IDs
        })
        
        assert response.status_code == 400
        assert "At least one of user_id, agent_id, or run_id must be provided" in response.json()["detail"]
    
    def test_get_memory_success(self, client, mock_async_memory, sample_memory_data):
        """Test successful memory retrieval"""
        mock_async_memory.get.return_value = sample_memory_data
        
        response = client.get("/memories/test-memory-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-memory-id"
        assert data["memory"] == "User likes pizza"
        assert data["user_id"] == "test-user"
        
        mock_async_memory.get.assert_called_once_with("test-memory-id")
    
    def test_get_memory_not_found(self, client, mock_async_memory):
        """Test memory retrieval when memory doesn't exist"""
        mock_async_memory.get.return_value = None
        
        response = client.get("/memories/nonexistent-id")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Memory not found"
    
    def test_search_memories_success(self, client, mock_async_memory, sample_search_request, sample_memory_data):
        """Test successful memory search"""
        mock_async_memory.search.return_value = {
            "results": [sample_memory_data],
            "relations": None
        }
        
        response = client.post("/memories/search", json=sample_search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["memory"] == "User likes pizza"
        assert data["results"][0]["score"] == 0.95
        
        # Verify mock was called with correct parameters
        mock_async_memory.search.assert_called_once()
        call_args = mock_async_memory.search.call_args
        assert call_args.kwargs["query"] == "food preferences"
        assert call_args.kwargs["user_id"] == "test-user"
        assert call_args.kwargs["limit"] == 10
    
    def test_search_memories_validation_error(self, client, mock_async_memory):
        """Test memory search with validation error"""
        mock_async_memory.search.side_effect = ValueError("At least one of user_id, agent_id, or run_id must be specified")
        
        response = client.post("/memories/search", json={
            "query": "test query"
            # Missing required IDs
        })
        
        assert response.status_code == 400
        assert "At least one of user_id, agent_id, or run_id must be specified" in response.json()["detail"]
    
    def test_get_all_memories_success(self, client, mock_async_memory, sample_memory_data):
        """Test successful retrieval of all memories"""
        mock_async_memory.get_all.return_value = {
            "results": [sample_memory_data],
            "relations": None
        }
        
        response = client.post("/memories/all", json={
            "user_id": "test-user",
            "limit": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == "test-memory-id"
        
        mock_async_memory.get_all.assert_called_once()
    
    def test_update_memory_success(self, client, mock_async_memory):
        """Test successful memory update"""
        mock_async_memory.update.return_value = {"message": "Memory updated successfully!"}
        
        response = client.put("/memories/test-memory-id", json={
            "data": "Updated memory content"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Memory updated successfully!"
        
        mock_async_memory.update.assert_called_once_with("test-memory-id", "Updated memory content")
    
    def test_delete_memory_success(self, client, mock_async_memory):
        """Test successful memory deletion"""
        mock_async_memory.delete.return_value = {"message": "Memory deleted successfully!"}
        
        response = client.delete("/memories/test-memory-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Memory deleted successfully!"
        
        mock_async_memory.delete.assert_called_once_with("test-memory-id")
    
    def test_delete_all_memories_success(self, client, mock_async_memory):
        """Test successful deletion of all memories"""
        mock_async_memory.delete_all.return_value = {"message": "Memories deleted successfully!"}
        
        response = client.delete("/memories", json={
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Memories deleted successfully!"
        
        mock_async_memory.delete_all.assert_called_once()
        call_args = mock_async_memory.delete_all.call_args
        assert call_args.kwargs["user_id"] == "test-user"
    
    def test_delete_all_memories_validation_error(self, client, mock_async_memory):
        """Test delete all memories with validation error"""
        mock_async_memory.delete_all.side_effect = ValueError("At least one filter is required")
        
        response = client.delete("/memories", json={})
        
        assert response.status_code == 400
        assert "At least one filter is required" in response.json()["detail"]
    
    def test_get_memory_history_success(self, client, mock_async_memory):
        """Test successful memory history retrieval"""
        history_data = [
            {
                "id": "history-1",
                "memory_id": "test-memory-id",
                "old_memory": None,
                "new_memory": "User likes pizza",
                "event": "ADD",
                "timestamp": "2024-01-01T00:00:00",
                "is_deleted": 0
            }
        ]
        mock_async_memory.history.return_value = history_data
        
        response = client.get("/memories/test-memory-id/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 1
        assert data["history"][0]["event"] == "ADD"
        
        mock_async_memory.history.assert_called_once_with("test-memory-id")
    
    def test_reset_memories_success(self, client, mock_async_memory):
        """Test successful memory reset"""
        mock_async_memory.reset.return_value = None
        
        response = client.post("/memories/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "All memories have been reset successfully"
        
        mock_async_memory.reset.assert_called_once()
    
    def test_server_error_handling(self, client, mock_async_memory):
        """Test server error handling"""
        mock_async_memory.get.side_effect = Exception("Database connection failed")
        
        response = client.get("/memories/test-memory-id")
        
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]


class TestMemoryAPIRequestValidation:
    """Test request validation for Memory API"""
    
    def test_create_memory_empty_messages(self, client):
        """Test memory creation with empty messages"""
        response = client.post("/memories", json={
            "user_id": "test-user"
            # Missing required 'messages' field
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_search_memories_empty_query(self, client):
        """Test memory search with empty query"""
        response = client.post("/memories/search", json={
            "user_id": "test-user"
            # Missing required 'query' field
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_update_memory_empty_data(self, client):
        """Test memory update with empty data"""
        response = client.put("/memories/test-id", json={
            # Missing required 'data' field
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_search_request_with_invalid_limit(self, client):
        """Test search request with invalid limit"""
        response = client.post("/memories/search", json={
            "query": "test",
            "user_id": "test-user",
            "limit": -1  # Invalid limit
        })
        
        # Should still process (validation allows negative numbers)
        # In a real implementation, you might add custom validation
        assert response.status_code in [400, 422, 500]  # Various possible error codes