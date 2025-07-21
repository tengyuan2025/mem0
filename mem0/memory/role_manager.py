import logging
import hashlib
from typing import Optional, Dict, Any
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


class RoleManager:
    """角色管理器，负责音色识别和角色管理"""
    
    def __init__(self, mysql_config: Dict[str, Any]):
        self.mysql_config = mysql_config
        self.connection = None
        self._connect()
        self._create_role_table()
        self._ensure_default_roles()
        
    def _connect(self) -> None:
        """连接MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(**self.mysql_config)
            logger.info("Successfully connected to MySQL for role management")
        except Error as e:
            logger.error(f"Error connecting to MySQL for role management: {e}")
            raise

    def _execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """执行MySQL查询"""
        try:
            if not self.connection or not self.connection.is_connected():
                self._connect()
                
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                cursor.close()
                return cursor.lastrowid if cursor.lastrowid else None
                
        except Error as e:
            logger.error(f"MySQL query error in role manager: {e}")
            raise

    def _create_role_table(self) -> None:
        """创建role表"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS role (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            voice_hash VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_voice_hash (voice_hash),
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self._execute_query(create_table_query)
            logger.info("Role table created successfully")
        except Error as e:
            logger.error(f"Error creating role table: {e}")
            raise

    def _ensure_default_roles(self) -> None:
        """确保默认角色存在"""
        # 先清理可能存在的乱码角色
        self._clean_corrupted_roles()
        
        default_roles = [
            {"name": "用户", "voice_hash": None},
            {"name": "助手", "voice_hash": None}
        ]
        
        for role_data in default_roles:
            # 检查角色是否存在
            existing_role = self.get_role_by_name(role_data["name"])
            if not existing_role:
                # 创建角色
                insert_query = "INSERT INTO role (name, voice_hash) VALUES (%s, %s)"
                role_id = self._execute_query(insert_query, (role_data["name"], role_data["voice_hash"]))
                logger.info(f"Created default role: {role_data['name']} with ID: {role_id}")

    def _clean_corrupted_roles(self) -> None:
        """清理可能存在的乱码角色"""
        try:
            # 查找所有角色
            query = "SELECT id, name FROM role"
            roles = self._execute_query(query, fetch=True)
            
            # 用于映射旧ID到新ID
            role_mapping = {}
            
            for role in roles:
                should_delete = False
                
                # 检查是否是乱码（包含非UTF-8字符或特殊字符）
                if role['name'] and (
                    'ç"¨æˆ·' in role['name'] or 
                    'åŠ©æ‰‹' in role['name'] or 
                    len(role['name'].encode('utf-8')) != len(role['name'])
                ):
                    should_delete = True
                    # 映射乱码角色到正确名称
                    if 'ç"¨æˆ·' in role['name']:
                        role_mapping[role['id']] = '用户'
                    elif 'åŠ©æ‰‹' in role['name']:
                        role_mapping[role['id']] = '助手'
                
                # 也删除重复的正确角色（保留最新的）
                elif role['name'] in ['用户', '助手']:
                    # 检查是否已经有更新的同名角色
                    check_query = "SELECT id FROM role WHERE name = %s AND id > %s"
                    newer_roles = self._execute_query(check_query, (role['name'], role['id']), fetch=True)
                    if newer_roles:
                        should_delete = True
                        role_mapping[role['id']] = role['name']
                
                if should_delete:
                    logger.info(f"Will clean role with ID: {role['id']}, name: {role['name']}")
            
            # 更新memory表中的role_id引用
            for old_id, role_name in role_mapping.items():
                # 找到或创建正确的角色
                correct_role = self.get_role_by_name(role_name)
                if not correct_role:
                    # 创建正确的角色
                    insert_query = "INSERT INTO role (name, voice_hash) VALUES (%s, %s)"
                    new_id = self._execute_query(insert_query, (role_name, None))
                    logger.info(f"Created correct role: {role_name} with ID: {new_id}")
                else:
                    new_id = correct_role['id']
                
                # 更新memory表中的引用
                update_query = "UPDATE memory SET role_id = %s WHERE role_id = %s"
                self._execute_query(update_query, (new_id, old_id))
                logger.info(f"Updated memory records from role_id {old_id} to {new_id}")
            
            # 现在安全删除旧角色
            for old_id in role_mapping.keys():
                delete_query = "DELETE FROM role WHERE id = %s"
                self._execute_query(delete_query, (old_id,))
                logger.info(f"Deleted old role with ID: {old_id}")
                    
        except Exception as e:
            logger.error(f"Error cleaning corrupted roles: {e}")

    def identify_role_by_voice(self, voice_hash: str) -> Optional[Dict[str, Any]]:
        """根据音色hash识别角色"""
        query = "SELECT id, name, voice_hash FROM role WHERE voice_hash = %s"
        result = self._execute_query(query, (voice_hash,), fetch=True)
        return result[0] if result else None

    def create_role(self, name: str, voice_hash: str = None) -> Dict[str, Any]:
        """创建新角色"""
        try:
            insert_query = "INSERT INTO role (name, voice_hash) VALUES (%s, %s)"
            role_id = self._execute_query(insert_query, (name, voice_hash))
            
            if role_id:
                return {
                    'id': role_id,
                    'name': name,
                    'voice_hash': voice_hash
                }
            else:
                # 如果插入失败，可能是因为name已存在，尝试获取现有的
                return self.get_role_by_name(name)
        except Exception as e:
            logger.error(f"Error creating role {name}: {e}")
            # 尝试获取现有角色
            return self.get_role_by_name(name)

    def create_role_if_not_exists(self, voice_hash: str, default_name: str = None) -> Dict[str, Any]:
        """如果角色不存在则创建新角色"""
        # 先尝试查找现有角色
        existing_role = self.identify_role_by_voice(voice_hash)
        if existing_role:
            return existing_role
            
        # 创建新角色
        if not default_name:
            default_name = f"角色_{voice_hash[:8]}"
            
        insert_query = "INSERT INTO role (name, voice_hash) VALUES (%s, %s)"
        role_id = self._execute_query(insert_query, (default_name, voice_hash))
        
        logger.info(f"Created new role: {default_name} with voice_hash: {voice_hash}")
        
        return {
            'id': role_id,
            'name': default_name,
            'voice_hash': voice_hash
        }

    def get_role_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据角色名称获取角色信息"""
        query = "SELECT id, name, voice_hash FROM role WHERE name = %s"
        result = self._execute_query(query, (name,), fetch=True)
        return result[0] if result else None

    def update_role_voice_hash(self, role_id: int, voice_hash: str) -> bool:
        """更新角色的voice_hash"""
        try:
            update_query = "UPDATE role SET voice_hash = %s WHERE id = %s"
            self._execute_query(update_query, (voice_hash, role_id))
            logger.info(f"Updated role {role_id} with voice_hash: {voice_hash}")
            return True
        except Exception as e:
            logger.error(f"Failed to update role voice_hash: {e}")
            return False

    def get_default_roles(self) -> Dict[str, Dict[str, Any]]:
        """获取默认角色映射"""
        user_role = self.get_role_by_name("用户")
        assistant_role = self.get_role_by_name("助手")
        
        return {
            "用户": user_role,
            "助手": assistant_role
        }

    def parse_role_from_text(self, text: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """从text中解析角色标签并返回清理后的文本和角色信息"""
        # 检查是否包含角色标签
        if text.startswith("[用户]"):
            clean_text = text[4:].strip()  # 移除"[用户]"
            user_role = self.get_role_by_name("用户")
            if not user_role:
                # 如果用户角色不存在，创建它
                user_role = self.create_role("用户")
            return clean_text, user_role
        elif text.startswith("[助手]"):
            clean_text = text[4:].strip()  # 移除"[助手]"
            assistant_role = self.get_role_by_name("助手")
            if not assistant_role:
                # 如果助手角色不存在，创建它
                assistant_role = self.create_role("助手")
            return clean_text, assistant_role
        else:
            # 没有角色标签，返回原文和None
            return text, None

    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Role manager MySQL connection closed")

    def fix_orphaned_role_references(self) -> None:
        """修复孤立的role_id引用"""
        try:
            # 获取当前存在的角色
            current_roles = {}
            role_query = "SELECT id, name FROM role"
            roles = self._execute_query(role_query, fetch=True)
            for role in roles:
                current_roles[role['name']] = role['id']
            
            logger.info(f"Current roles: {current_roles}")
            
            # 查找所有有role_id但role_name为NULL的记忆
            orphaned_query = """
            SELECT m.id, m.role_id, m.memory_text 
            FROM memory m 
            LEFT JOIN role r ON m.role_id = r.id 
            WHERE m.role_id IS NOT NULL AND r.id IS NULL
            """
            orphaned_memories = self._execute_query(orphaned_query, fetch=True)
            
            logger.info(f"Found {len(orphaned_memories)} orphaned memory records")
            
            # 根据记忆文本内容推断角色并更新
            for memory in orphaned_memories:
                new_role_id = None
                text = memory['memory_text']
                
                # 根据文本内容推断角色
                if text.startswith('[用户]') or '用户' in text:
                    new_role_id = current_roles.get('用户')
                elif text.startswith('[助手]') or '助手' in text:
                    new_role_id = current_roles.get('助手')
                
                if new_role_id:
                    update_query = "UPDATE memory SET role_id = %s WHERE id = %s"
                    self._execute_query(update_query, (new_role_id, memory['id']))
                    logger.info(f"Fixed role_id for memory {memory['id']}: {memory['role_id']} -> {new_role_id}")
                else:
                    # 如果无法推断，设为NULL
                    update_query = "UPDATE memory SET role_id = NULL WHERE id = %s"
                    self._execute_query(update_query, (memory['id'],))
                    logger.info(f"Set role_id to NULL for memory {memory['id']}")
                    
        except Exception as e:
            logger.error(f"Error fixing orphaned role references: {e}")

    def __del__(self):
        self.close()