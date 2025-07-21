from flask import Flask, request, jsonify
import json
from mem0.memory.mysql_memory import MySQLSyncMemory  # 使用MySQL同步内存类
from mem0.configs.base import MemoryConfig
from mem0.configs.mysql import MySQLConfig
from mem0.llms.configs import LlmConfig
from mem0.embeddings.configs import EmbedderConfig
from mem0.vector_stores.configs import VectorStoreConfig
import os
import logging
import traceback

# 禁用 PostHog 遥测避免连接超时
os.environ["MEM0_TELEMETRY"] = "False"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

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

                # 创建 embedder 配置 - 使用Ollama
                embedder_config = {
                    "provider": "ollama",
                    "config": {
                        "model": "mxbai-embed-large:latest",
                        "embedding_dims": 1024,
                        "ollama_base_url": "http://localhost:11434"
                    }
                }

                # 创建 vector store 配置 - 相对于当前工作目录
                qdrant_data_path = os.path.join(os.getcwd(), "qdrant_data")
                os.makedirs(qdrant_data_path, exist_ok=True)  # 确保目录存在
                vector_store_config = {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": "mem0",
                        "embedding_model_dims": 1024,  # 匹配Ollama embedding维度
                        "path": qdrant_data_path,
                        "on_disk": True
                    }
                }
                # MySQL配置
                mysql_config = MySQLConfig(
                    host="127.0.0.1",
                    port=3306,
                    user="root",
                    password="123456",
                    database="xiaozhi_esp32_server",
                    charset="utf8mb4"
                )
                
                config = MemoryConfig(
                    llm=LlmConfig(**llm_config),
                    embedder=EmbedderConfig(**embedder_config),
                    vector_store=VectorStoreConfig(**vector_store_config)
                )
                memory_instance = MySQLSyncMemory(config, mysql_config.model_dump())
                logger.info("Memory initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing memory: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
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
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # 返回None或者抛出异常，取决于你的错误处理策略
        raise e

@app.route('/add', methods=['POST'])
def add_memory():
    try:
        client = get_client()
        data = request.get_json()
        msgs = data.get('msgs', [])
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        voice_hash = data.get('voice_hash')  # 音色特征哈希值
        audio_id = data.get('audio_id')      # 音频文件ID
        audio_path = data.get('audio_path')  # 音频文件路径
        role_id = data.get('role_id')        # 角色ID
        role_name = data.get('role_name')    # 角色名称
        force_single_memory = data.get('force_single_memory', False)  # 强制单条记忆
        logger.info(f"Received add request: msgs={msgs}, user_id={user_id}, session_id={session_id}, role_id={role_id}, role_name={role_name}, force_single={force_single_memory}")
        
        # 添加相关信息到metadata中
        metadata = {}
        if voice_hash:
            metadata['voice_hash'] = voice_hash
        if audio_id:
            metadata['audio_id'] = audio_id
        if audio_path:
            metadata['audio_path'] = audio_path
        if session_id:
            metadata['session_id'] = session_id  # 保留在metadata中供MySQL使用
        if role_id:
            metadata['role_id'] = role_id
        if role_name:
            metadata['role_name'] = role_name
        if force_single_memory:
            metadata['force_single_memory'] = True
            
        # 处理记忆添加 - 使用run_id参数替代metadata中的session_id
        try:
            # 检查是否为参与者记忆整合请求（有role_id就进行整合）
            is_participant_memory = bool(role_id)
            
            # 检查是否强制单条记忆或总结请求
            is_summary_request = (
                force_single_memory or
                (len(msgs) == 1 and 
                 msgs[0].get('role') == 'user' and 
                 ('总结' in msgs[0].get('content', '') or '[' in msgs[0].get('content', '')))
            )
            
            if is_participant_memory:
                # 对于参与者记忆整合，使用LLM提取关键事实
                logger.info(f"Processing participant memory integration for role: {role_name}")
                
                # 先清除该参与者在此session中的旧记忆
                if session_id and role_id:
                    try:
                        clear_query = "DELETE FROM memory WHERE session_id = %s AND role_id = %s"
                        client.mysql_db._execute_query(clear_query, (session_id, role_id))
                        logger.info(f"Cleared old memories for role {role_id} in session {session_id}")
                    except Exception as clear_error:
                        logger.warning(f"Failed to clear old memories: {clear_error}")
                
                # 使用mem0标准流程进行事实提取，然后合并为一条记忆
                logger.info(f"Using LLM fact extraction for role: {role_name}")
                result = client.add(msgs, user_id=user_id, run_id=session_id, metadata=metadata)
                
                # 如果生成了多条记忆，合并为一条
                if len(result.get('results', [])) > 1:
                    logger.warning(f"Generated {len(result['results'])} memories, consolidating to 1...")
                    
                    # 获取所有生成的记忆内容
                    memory_ids = [r.get('id') for r in result.get('results', []) if r.get('id')]
                    all_memories = []
                    
                    for memory_id in memory_ids:
                        try:
                            memory_data = client.get_mysql_memory(memory_id)
                            if memory_data and memory_data.get('memory_text'):
                                all_memories.append(memory_data['memory_text'])
                        except Exception as e:
                            logger.error(f"Failed to get memory {memory_id}: {e}")
                    
                    # 合并所有事实为一条记忆
                    if all_memories:
                        consolidated_memory = "; ".join(all_memories)
                        
                        # 删除所有旧的分散记忆
                        for memory_id in memory_ids:
                            try:
                                delete_query = "DELETE FROM memory WHERE id = %s"
                                client.mysql_db._execute_query(delete_query, (memory_id,))
                            except Exception as e:
                                logger.error(f"Failed to delete memory {memory_id}: {e}")
                        
                        # 创建一条新的聚合记忆
                        import uuid
                        consolidated_id = str(uuid.uuid4())
                        consolidated_metadata = {
                            'user_id': user_id,
                            'session_id': session_id,
                            'role_id': role_id,
                            'role_name': role_name,
                            'run_id': session_id,
                            'is_consolidated': True
                        }
                        consolidated_metadata.update(metadata)
                        
                        # 直接存储聚合记忆到MySQL
                        client._sync_memory_to_mysql(
                            memory_id=consolidated_id,
                            data=consolidated_memory,
                            metadata=consolidated_metadata,
                            original_text=consolidated_memory,
                            event="ADD"
                        )
                        
                        result = {
                            'results': [{'event': 'ADD', 'id': consolidated_id}],
                            'status': 'success',
                            'consolidated_from': len(memory_ids)
                        }
                        logger.info(f"Consolidated {len(memory_ids)} memories into 1 for role {role_name}")
                
            elif is_summary_request:
                # 对于总结请求，直接存储为单条记忆，不经过LLM处理
                logger.info(f"Processing single memory request for role: {role_name}")
                
                content = msgs[0].get('content', '')
                
                # 直接存储到MySQL，跳过向量化处理以避免分解
                try:
                    mysql_client = get_client()
                    memory_id = f"summary_{user_id}_{session_id}_{role_id}"
                    
                    # 直接调用MySQL同步方法
                    mysql_client._sync_memory_to_mysql(
                        memory_id=memory_id,
                        data=content,
                        metadata=metadata,
                        original_text=content,
                        event="ADD"
                    )
                    
                    result = {
                        'results': [{'event': 'ADD', 'id': memory_id}],
                        'status': 'success'
                    }
                    
                except Exception as direct_error:
                    logger.error(f"Direct storage failed, using standard processing: {direct_error}")
                    # 如果直接存储失败，使用标准流程
                    result = client.add(msgs, user_id=user_id, run_id=session_id, metadata=metadata)
            else:
                # 普通消息处理
                result = client.add(msgs, user_id=user_id, run_id=session_id, metadata=metadata)
            
            logger.info(f"Received add response: {result}")

            # 简化响应以减少传输数据量
            simplified_result = {
                'total_memories': len(result.get('results', [])),
                'events': [{'event': r.get('event'), 'id': r.get('id')} for r in result.get('results', [])],
                'summary': f"处理了{len(result.get('results', []))}条记忆",
                'is_summary': is_summary_request
            }
            
            return jsonify({'status': 'success', 'result': simplified_result})
        except Exception as mem_error:
            logger.error(f"Memory processing error: {mem_error}")
            # 即使有错误，记忆可能已经保存，返回部分成功状态
            return jsonify({
                'status': 'partial_success', 
                'message': 'Memories may have been saved despite network error',
                'error': str(mem_error)
            }), 202
            
    except Exception as e:
        logger.error(f"Error in add_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_memory():
    try:
        query = request.args.get('query') or ""
        user_id = request.args.get('user_id') or ""
        session_id = request.args.get('session_id') or ""
        logger.info(f"Received search request: query={query}, user_id={user_id}, session_id={session_id}")
        
        # 使用run_id进行搜索
        results = get_client().search(query=str(query), user_id=str(user_id), run_id=session_id)
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        logger.error(f"Error in search_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/list', methods=['GET'])
def list_memory():
    try:
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        logger.info(f"Received list request for user_id: {user_id}, session_id: {session_id}")
        client = get_client()
        
        # 使用新的get_all_with_roles方法获取包含角色信息的记忆
        if hasattr(client, 'get_all_with_roles'):
            results = client.get_all_with_roles(
                user_id=user_id,
                session_id=session_id
            )
        else:
            # 兼容性处理，使用原方法with run_id
            results = client.get_all(user_id=user_id, run_id=session_id)
        response_data = {'status': 'success', 'results': results}
        response = app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=200,
            mimetype='application/json; charset=utf-8'
        )
        return response
    except Exception as e:
        logger.error(f"Error in list_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/add_summary', methods=['POST'])
def add_summary_memory():
    """直接添加总结记忆，不经过LLM处理"""
    try:
        client = get_client()
        data = request.get_json()
        
        content = data.get('content', '')
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        role_id = data.get('role_id')
        role_name = data.get('role_name')
        voice_hash = data.get('voice_hash')
        
        logger.info(f"Adding summary memory for user_id: {user_id}, role: {role_name}")
        
        # 生成唯一的memory_id
        import uuid
        memory_id = str(uuid.uuid4())
        
        # 准备metadata
        metadata = {
            'user_id': user_id,
            'session_id': session_id,
            'role_id': role_id,
            'role_name': role_name,
            'run_id': session_id,
            'is_summary': True
        }
        if voice_hash:
            metadata['voice_hash'] = voice_hash
        
        # 直接存储到MySQL
        client._sync_memory_to_mysql(
            memory_id=memory_id,
            data=content,
            metadata=metadata,
            original_text=content,
            event="ADD"
        )
        
        return jsonify({
            'status': 'success', 
            'result': {
                'total_memories': 1,
                'events': [{'event': 'ADD', 'id': memory_id}],
                'summary': '直接存储了1条总结记忆'
            }
        })
        
    except Exception as e:
        logger.error(f"Error in add_summary_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/clear_session', methods=['DELETE', 'POST'])
def clear_session_memory():
    """清除指定session的记忆"""
    try:
        client = get_client()
        data = request.get_json() if request.method == 'POST' else {}
        session_id = data.get('session_id') or request.args.get('session_id')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'session_id is required'}), 400
        
        logger.info(f"Clearing memories for session: {session_id}")
        
        # 清除MySQL中该session的记忆
        delete_query = "DELETE FROM memory WHERE session_id = %s"
        client.mysql_db._execute_query(delete_query, (session_id,))
        
        # 也清除history记录
        delete_history_query = "DELETE FROM memory_history WHERE memory_id IN (SELECT id FROM memory WHERE session_id = %s)"
        client.mysql_db._execute_query(delete_history_query, (session_id,))
        
        logger.info(f"Successfully cleared memories for session: {session_id}")
        
        return jsonify({'status': 'success', 'message': f'Session {session_id} memories cleared'})
    except Exception as e:
        logger.error(f"Error in clear_session_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/replace_with_summary', methods=['POST'])
def replace_with_summary():
    """替换指定session的记忆为总结记忆"""
    try:
        client = get_client()
        data = request.get_json()
        session_id = data.get('session_id')
        summaries = data.get('summaries', [])  # [{"content": "...", "user_id": "...", "role_id": "...", "role_name": "..."}]
        
        if not session_id or not summaries:
            return jsonify({'status': 'error', 'message': 'session_id and summaries are required'}), 400
        
        logger.info(f"Replacing memories for session {session_id} with {len(summaries)} summaries")
        
        # 先清除该session的旧记忆
        delete_query = "DELETE FROM memory WHERE session_id = %s"
        client.mysql_db._execute_query(delete_query, (session_id,))
        
        # 添加新的总结记忆
        results = []
        for summary in summaries:
            import uuid
            memory_id = str(uuid.uuid4())
            
            # 提取user_id（去掉角色后缀，获取原始user_id）
            original_user_id = summary.get('user_id', '').replace(f"_{summary.get('role_id', '')}", "").replace("converted_", "")
            if not original_user_id:
                # 如果无法提取，使用默认格式
                original_user_id = "98:a3:16:e5:db:74"  # 使用您的设备ID作为默认值
            
            metadata = {
                'user_id': original_user_id,
                'session_id': session_id,
                'role_id': summary.get('role_id'),
                'role_name': summary.get('role_name'),
                'run_id': session_id,
                'is_summary': True
            }
            
            # 直接插入MySQL，包含user_id
            client.mysql_db.add_memory(
                memory_id=memory_id,
                memory_text=summary.get('content'),
                user_id=original_user_id,
                session_id=session_id,
                role_id=summary.get('role_id'),
                metadata=metadata
            )
            
            results.append({'event': 'ADD', 'id': memory_id, 'role_name': summary.get('role_name')})
        
        return jsonify({
            'status': 'success', 
            'message': f'Replaced with {len(summaries)} summary memories',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in replace_with_summary: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/clear', methods=['DELETE', 'GET'])
def clear_memory():
    try:
        client = get_client()
        logger.info("Received clear request - clearing all memories from both MySQL and vector database")
        
        # 清除向量数据库中的所有数据
        client.reset()
        logger.info("Successfully cleared all data from vector database and MySQL")
        
        return jsonify({'status': 'success', 'message': 'All memories cleared from both MySQL and vector database'})
    except Exception as e:
        logger.error(f"Error in clear_memory: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # 配置Flask服务器
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)