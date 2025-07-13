from flask import Flask, request, jsonify
from mem0.memory.main import Memory  # 假设这是你的 MemoryClient 类所在位置
from mem0.configs.base import MemoryConfig
from mem0.llms.configs import LlmConfig
from mem0.embeddings.configs import EmbedderConfig
from mem0.vector_stores.configs import VectorStoreConfig
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 单例初始化Memory
memory_instance = None

def init_memory():
    global memory_instance
    try:
        # 只在主进程初始化
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            if memory_instance is None:
                # 创建配置
                llm_config = {
                    "provider": "deepseek",
                    "config": {
                        "api_key": "sk-6bf523713f35415390ce4a6b0b3de1fa",
                        "model": "deepseek-chat",
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                }

                # 创建 embedder 配置
                embedder_config = {
                    "provider": "ollama",
                    "config": {
                        "model": "mxbai-embed-large:latest",
                        "embedding_dims": 1024,
                        "ollama_base_url": "http://localhost:11434"
                    }
                }

                # 创建 vector store 配置
                vector_store_config = {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": "mem0",
                        "embedding_model_dims": 1024,
                        "path": "./qdrant_data",
                        "on_disk": True
                    }
                }
                config = MemoryConfig(
                    llm=LlmConfig(**llm_config),
                    embedder=EmbedderConfig(**embedder_config),
                    vector_store=VectorStoreConfig(**vector_store_config)
                )
                memory_instance = Memory(config)
                logger.info("Memory initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing memory: {str(e)}")
        # 可以选择重新抛出异常或者返回None
        raise e
    return memory_instance

def get_client():
    # 确保任何进程都能拿到已初始化的 memory_instance
    global memory_instance
    try:
        if memory_instance is None:
            memory_instance = init_memory()
        return memory_instance
    except Exception as e:
        logger.error(f"Error getting memory client: {str(e)}")
        # 返回None或者抛出异常，取决于你的错误处理策略
        raise e

@app.route('/add', methods=['POST'])
def add_memory():
    try:
        client = get_client()
        data = request.get_json()
        msgs = data.get('msgs', [])
        user_id = data.get('user_id')
        logger.info(f"Received add request: msgs={msgs}, user_id={user_id}")
        result = client.add(msgs, user_id=user_id)
        return jsonify({'status': 'success', 'result': result})
    except Exception as e:
        logger.error(f"Error in add_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_memory():
    try:
        query = request.args.get('query') or ""
        user_id = request.args.get('user_id') or ""
        logger.info(f"Received search request: query={query}, user_id={user_id}")
        results = get_client().search(query=str(query), user_id=str(user_id))
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        logger.error(f"Error in search_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/list', methods=['GET'])
def list_memory():
    try:
        user_id = request.args.get('user_id')
        logger.info(f"Received list request for user_id: {user_id}")
        client = get_client()
        results = client.get_all(user_id=user_id)
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        logger.error(f"Error in list_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)