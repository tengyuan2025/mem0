#!/usr/bin/env python3
"""
Test the new API format without proxy issues
"""
import requests
import json
import os

# Disable proxy for this request
os.environ.pop('http_proxy', None)
os.environ.pop('HTTP_PROXY', None) 
os.environ.pop('https_proxy', None)
os.environ.pop('HTTPS_PROXY', None)

# Configure session to not use proxy
session = requests.Session()
session.proxies = {}

# Configuration
BASE_URL = "http://localhost:8002"
API_TOKEN = "your-secret-key-change-this"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_health():
    """Test health endpoint"""
    try:
        response = session.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False

def test_root():
    """Test root endpoint"""
    try:
        response = session.get(f"{BASE_URL}/", timeout=5)
        print(f"Root status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Root request failed: {response.text}")
            return False
    except Exception as e:
        print(f"Root request error: {e}")
        return False

def test_weather_conversation():
    """Test weather conversation scenario"""
    
    # Build request in new format - direct array
    messages = [
        {
            "user_id": 1,
            "content": "今天可太热了",
            "role": "user"
        },
        {
            "user_id": 2, 
            "content": "是啊 都快40度了吧",
            "role": "user"
        },
        {
            "user_id": 3,
            "content": "北京今天的最高温度是34度哦",
            "role": "assistant"
        }
    ]
    
    print("🌡️  Testing weather conversation scenario...")
    print(f"📤 Sending {len(messages)} messages")
    
    try:
        response = session.post(
            f"{BASE_URL}/api/v1/memories/add",
            json=messages,  # Direct array
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 Response content:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("status") == "success":
                print("\n✅ Memory added successfully!")
                
                # Show each user's memory
                for user_result in result.get("results", []):
                    print(f"\n👤 User {user_result['user_id']}:")
                    print(f"   Status: {user_result.get('status')}")
                    if user_result.get('memory_id'):
                        print(f"   Memory ID: {user_result['memory_id']}")
                return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("       Testing Mem0 API without Proxy")
    print("=" * 60)
    
    # Test health first
    if not test_health():
        print("Health check failed, stopping tests")
        exit(1)
    
    # Test root endpoint
    if not test_root():
        print("Root endpoint failed")
        exit(1)
        
    # Test memory API
    if not test_weather_conversation():
        print("Memory API test failed")
        exit(1)
        
    print("\n" + "=" * 60)
    print("All tests passed!")