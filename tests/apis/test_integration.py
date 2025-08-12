"""
Integration tests for Memory API with actual Memory instances
"""
import pytest
from fastapi.testclient import TestClient
import tempfile
import os

from mem0.api.main import app, get_memory, get_async_memory
from mem0.memory.main import Memory, AsyncMemory
from mem0.configs.base import MemoryConfig


class TestMemoryAPIIntegration:
    """Integration tests using real Memory instances"""
    
    @pytest.fixture
    def memory_config(self, temp_db):
        """Memory configuration for testing"""
        return MemoryConfig(
            history_db_path=temp_db,
            vector_store={
                "provider": "qdrant",
                "config": {
                    "collection_name": "test_memories",
                    "path": tempfile.mkdtemp()
                }
            },
            llm={
                "provider": "openai", 
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.1
                }
            },
            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small"
                }
            }
        )
    
    @pytest.fixture
    def real_memory(self, memory_config):
        """Real Memory instance for testing"""
        return Memory(memory_config)
    
    @pytest.fixture
    def real_async_memory(self, memory_config):
        """Real AsyncMemory instance for testing"""
        return AsyncMemory(memory_config)
    
    @pytest.fixture
    def integration_client(self, real_memory, real_async_memory):
        """Test client with real memory instances"""
        app.dependency_overrides[get_memory] = lambda: real_memory
        app.dependency_overrides[get_async_memory] = lambda: real_async_memory
        
        client = TestClient(app)
        yield client
        
        # Cleanup
        app.dependency_overrides.clear()
    
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires OpenAI API key")
    def test_full_memory_workflow(self, integration_client):
        """Test complete memory workflow with real instances"""
        # Create memory
        create_response = integration_client.post("/memories", json={
            "messages": "I love Italian food, especially pasta and pizza",
            "user_id": "integration-test-user",
            "infer": True
        })
        
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert "results" in create_data
        assert len(create_data["results"]) > 0
        
        # Get created memory
        memory_id = create_data["results"][0]["id"]
        get_response = integration_client.get(f"/memories/{memory_id}")
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["id"] == memory_id
        assert get_data["user_id"] == "integration-test-user"
        
        # Search for memories
        search_response = integration_client.post("/memories/search", json={
            "query": "food preferences",
            "user_id": "integration-test-user",
            "limit": 5
        })
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert "results" in search_data
        assert len(search_data["results"]) > 0
        
        # Get all memories
        get_all_response = integration_client.post("/memories/all", json={
            "user_id": "integration-test-user",
            "limit": 10
        })
        
        assert get_all_response.status_code == 200
        get_all_data = get_all_response.json()
        assert "results" in get_all_data
        assert len(get_all_data["results"]) > 0
        
        # Update memory
        update_response = integration_client.put(f"/memories/{memory_id}", json={
            "data": "User loves Italian cuisine including pasta, pizza and gelato"
        })
        
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert "successfully" in update_data["message"]
        
        # Get memory history
        history_response = integration_client.get(f"/memories/{memory_id}/history")
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "history" in history_data
        assert len(history_data["history"]) >= 2  # Should have ADD and UPDATE events
        
        # Delete specific memory
        delete_response = integration_client.delete(f"/memories/{memory_id}")
        
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert "successfully" in delete_data["message"]
        
        # Verify memory is deleted
        get_deleted_response = integration_client.get(f"/memories/{memory_id}")
        assert get_deleted_response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires OpenAI API key")
    def test_multi_user_isolation(self, integration_client):
        """Test that memories are properly isolated between users"""
        # Create memory for user 1
        user1_response = integration_client.post("/memories", json={
            "messages": "User 1 likes chocolate",
            "user_id": "user-1",
            "infer": True
        })
        assert user1_response.status_code == 200
        
        # Create memory for user 2
        user2_response = integration_client.post("/memories", json={
            "messages": "User 2 likes vanilla", 
            "user_id": "user-2",
            "infer": True
        })
        assert user2_response.status_code == 200
        
        # Search for user 1's memories
        user1_search = integration_client.post("/memories/search", json={
            "query": "chocolate",
            "user_id": "user-1",
            "limit": 10
        })
        assert user1_search.status_code == 200
        user1_data = user1_search.json()
        assert len(user1_data["results"]) > 0
        
        # Verify user 1 can't see user 2's memories
        user1_vanilla_search = integration_client.post("/memories/search", json={
            "query": "vanilla",
            "user_id": "user-1", 
            "limit": 10
        })
        assert user1_vanilla_search.status_code == 200
        user1_vanilla_data = user1_vanilla_search.json()
        assert len(user1_vanilla_data["results"]) == 0
        
        # Cleanup
        integration_client.delete("/memories", json={"user_id": "user-1"})
        integration_client.delete("/memories", json={"user_id": "user-2"})
    
    def test_api_error_handling_with_real_instances(self, integration_client):
        """Test error handling with real memory instances"""
        # Test getting non-existent memory
        response = integration_client.get("/memories/non-existent-id")
        assert response.status_code == 404
        
        # Test search without user ID
        response = integration_client.post("/memories/search", json={
            "query": "test query"
        })
        assert response.status_code == 400
        
        # Test delete all without filters
        response = integration_client.delete("/memories", json={})
        assert response.status_code == 400