#!/usr/bin/env python3
"""
Mem0 健康检查和服务验证脚本
用于检查系统状态、依赖和配置
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import argparse

try:
    import requests
    from dotenv import load_dotenv
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"❌ 缺少依赖包: {e}")
    print("请先运行安装脚本或: pip install -r requirements.txt")
    sys.exit(1)


class HealthChecker:
    """系统健康检查器"""
    
    def __init__(self, config_file: str = ".env"):
        self.config_file = config_file
        self.config = {}
        self.results = []
        
        # 加载配置
        if os.path.exists(config_file):
            load_dotenv(config_file)
            self._load_config()
    
    def _load_config(self):
        """加载配置"""
        config_keys = [
            'MEM0_LLM_PROVIDER', 'MEM0_LLM_MODEL',
            'MEM0_EMBEDDER_PROVIDER', 'MEM0_EMBEDDER_MODEL',
            'MEM0_VECTOR_STORE_PROVIDER', 'CHROMA_PERSIST_DIRECTORY',
            'APP_HOST', 'APP_PORT', 'API_SECRET_KEY',
            'HF_HOME', 'TRANSFORMERS_CACHE',
            'ENABLE_MYSQL', 'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DATABASE',
            'OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'DASHSCOPE_API_KEY'
        ]
        
        for key in config_keys:
            self.config[key] = os.getenv(key)
    
    def _add_result(self, category: str, name: str, status: str, 
                   message: str, details: Optional[Dict] = None):
        """添加检查结果"""
        self.results.append({
            'category': category,
            'name': name,
            'status': status,  # 'pass', 'fail', 'warn', 'skip'
            'message': message,
            'details': details or {}
        })
    
    def check_python_environment(self) -> None:
        """检查Python环境"""
        print("🐍 检查Python环境...")
        
        # Python版本
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version >= (3, 8):
            self._add_result('environment', 'python_version', 'pass',
                           f"Python版本: {version_str}", {'version': version_str})
        else:
            self._add_result('environment', 'python_version', 'fail',
                           f"Python版本过低: {version_str}，需要3.8+", {'version': version_str})
        
        # 虚拟环境
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if in_venv:
            self._add_result('environment', 'virtual_env', 'pass', "运行在虚拟环境中")
        else:
            self._add_result('environment', 'virtual_env', 'warn',
                           "未运行在虚拟环境中，建议使用虚拟环境")
    
    def check_dependencies(self) -> None:
        """检查Python依赖"""
        print("📦 检查Python依赖...")
        
        required_packages = [
            ('fastapi', 'FastAPI'),
            ('uvicorn', 'Uvicorn'),
            ('sentence_transformers', 'Sentence Transformers'),
            ('chromadb', 'ChromaDB'),
            ('torch', 'PyTorch'),
            ('transformers', 'Transformers'),
            ('openai', 'OpenAI'),
            ('requests', 'Requests'),
            ('numpy', 'NumPy'),
            ('pandas', 'Pandas')
        ]
        
        for package, display_name in required_packages:
            try:
                __import__(package)
                self._add_result('dependencies', package, 'pass',
                               f"{display_name} 已安装")
            except ImportError:
                self._add_result('dependencies', package, 'fail',
                               f"{display_name} 未安装")
    
    def check_configuration(self) -> None:
        """检查配置文件"""
        print("⚙️  检查配置文件...")
        
        if not os.path.exists(self.config_file):
            self._add_result('config', 'config_file', 'fail',
                           f"配置文件 {self.config_file} 不存在")
            return
        
        self._add_result('config', 'config_file', 'pass',
                        f"配置文件 {self.config_file} 存在")
        
        # 检查必要配置项
        required_configs = {
            'MEM0_EMBEDDER_MODEL': '嵌入模型',
            'MEM0_VECTOR_STORE_PROVIDER': '向量数据库提供商',
            'APP_PORT': '应用端口'
        }
        
        for key, description in required_configs.items():
            if self.config.get(key):
                self._add_result('config', key.lower(), 'pass',
                               f"{description}: {self.config[key]}")
            else:
                self._add_result('config', key.lower(), 'warn',
                               f"{description} 未配置")
        
        # 检查API密钥
        api_keys = ['OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'DASHSCOPE_API_KEY']
        has_api_key = any(self.config.get(key) for key in api_keys)
        
        if has_api_key:
            self._add_result('config', 'api_keys', 'pass', "至少配置了一个LLM API密钥")
        else:
            self._add_result('config', 'api_keys', 'warn',
                           "未配置任何LLM API密钥，某些功能可能无法使用")
    
    def check_directories(self) -> None:
        """检查目录结构"""
        print("📁 检查目录结构...")
        
        required_dirs = [
            'data',
            'data/huggingface',
            'data/transformers',
            'data/chroma'
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                self._add_result('directories', dir_path.replace('/', '_'), 'pass',
                               f"目录 {dir_path} 存在")
            else:
                self._add_result('directories', dir_path.replace('/', '_'), 'fail',
                               f"目录 {dir_path} 不存在")
    
    def check_embedding_models(self) -> None:
        """检查嵌入模型"""
        print("🤖 检查嵌入模型...")
        
        model_name = self.config.get('MEM0_EMBEDDER_MODEL', 'shibing624/text2vec-base-chinese')
        
        try:
            print(f"   正在加载模型: {model_name}")
            model = SentenceTransformer(model_name)
            
            # 测试嵌入
            test_text = "这是一个测试文本"
            embedding = model.encode(test_text)
            
            self._add_result('models', 'embedding_model', 'pass',
                           f"嵌入模型 {model_name} 工作正常",
                           {'model': model_name, 'dimension': len(embedding)})
            
        except Exception as e:
            self._add_result('models', 'embedding_model', 'fail',
                           f"嵌入模型 {model_name} 加载失败: {str(e)}")
    
    def check_vector_database(self) -> None:
        """检查向量数据库"""
        print("🗄️  检查向量数据库...")
        
        provider = self.config.get('MEM0_VECTOR_STORE_PROVIDER', 'chroma')
        
        if provider == 'chroma':
            try:
                persist_dir = self.config.get('CHROMA_PERSIST_DIRECTORY', './data/chroma')
                client = chromadb.PersistentClient(path=persist_dir)
                
                # 测试创建collection
                test_collection_name = f"health_check_{int(time.time())}"
                collection = client.get_or_create_collection(test_collection_name)
                
                # 清理测试collection
                client.delete_collection(test_collection_name)
                
                self._add_result('database', 'vector_db', 'pass',
                               f"ChromaDB 连接成功",
                               {'provider': provider, 'path': persist_dir})
                
            except Exception as e:
                self._add_result('database', 'vector_db', 'fail',
                               f"ChromaDB 连接失败: {str(e)}")
        else:
            self._add_result('database', 'vector_db', 'skip',
                           f"跳过 {provider} 数据库检查")
    
    def check_mysql_connection(self) -> None:
        """检查MySQL连接"""
        print("🐬 检查MySQL连接...")
        
        if self.config.get('ENABLE_MYSQL') != 'true':
            self._add_result('database', 'mysql', 'skip', "MySQL未启用")
            return
        
        try:
            import pymysql
            
            connection = pymysql.connect(
                host=self.config.get('MYSQL_HOST', 'localhost'),
                port=int(self.config.get('MYSQL_PORT', 3306)),
                user=self.config.get('MYSQL_USER', 'root'),
                password=self.config.get('MYSQL_PASSWORD', ''),
                database=self.config.get('MYSQL_DATABASE', 'mem0'),
                connect_timeout=5
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            connection.close()
            
            self._add_result('database', 'mysql', 'pass', "MySQL连接成功")
            
        except ImportError:
            self._add_result('database', 'mysql', 'fail', "PyMySQL未安装")
        except Exception as e:
            self._add_result('database', 'mysql', 'fail',
                           f"MySQL连接失败: {str(e)}")
    
    def check_api_service(self, timeout: int = 5) -> None:
        """检查API服务"""
        print("🌐 检查API服务...")
        
        host = self.config.get('APP_HOST', '0.0.0.0')
        port = self.config.get('APP_PORT', '9000')
        
        # 如果host是0.0.0.0，改为localhost进行测试
        test_host = 'localhost' if host == '0.0.0.0' else host
        base_url = f"http://{test_host}:{port}"
        
        try:
            # 检查健康端点
            response = requests.get(f"{base_url}/health", timeout=timeout)
            if response.status_code == 200:
                self._add_result('service', 'api_health', 'pass',
                               f"API服务运行正常 ({base_url})")
            else:
                self._add_result('service', 'api_health', 'warn',
                               f"API服务响应异常: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self._add_result('service', 'api_health', 'fail',
                           f"无法连接到API服务 ({base_url})，服务可能未启动")
        except requests.exceptions.Timeout:
            self._add_result('service', 'api_health', 'warn',
                           f"API服务响应超时 ({base_url})")
        except Exception as e:
            self._add_result('service', 'api_health', 'fail',
                           f"API服务检查失败: {str(e)}")
    
    def check_system_resources(self) -> None:
        """检查系统资源"""
        print("💻 检查系统资源...")
        
        try:
            import psutil
            
            # 内存使用
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_used_percent = memory.percent
            
            if memory_gb >= 4:
                self._add_result('resources', 'memory', 'pass',
                               f"内存充足: {memory_gb:.1f}GB (使用率: {memory_used_percent:.1f}%)")
            else:
                self._add_result('resources', 'memory', 'warn',
                               f"内存较少: {memory_gb:.1f}GB (使用率: {memory_used_percent:.1f}%)")
            
            # 磁盘空间
            disk = psutil.disk_usage('.')
            disk_free_gb = disk.free / (1024**3)
            
            if disk_free_gb >= 5:
                self._add_result('resources', 'disk', 'pass',
                               f"磁盘空间充足: {disk_free_gb:.1f}GB可用")
            else:
                self._add_result('resources', 'disk', 'warn',
                               f"磁盘空间不足: {disk_free_gb:.1f}GB可用")
            
        except ImportError:
            self._add_result('resources', 'system_info', 'skip',
                           "psutil未安装，跳过系统资源检查")
    
    def run_all_checks(self, check_api: bool = True) -> None:
        """运行所有检查"""
        print("🔍 开始系统健康检查...\n")
        
        self.check_python_environment()
        self.check_dependencies()
        self.check_configuration()
        self.check_directories()
        self.check_embedding_models()
        self.check_vector_database()
        self.check_mysql_connection()
        
        if check_api:
            self.check_api_service()
        
        self.check_system_resources()
    
    def print_results(self, verbose: bool = False) -> None:
        """打印检查结果"""
        print(f"\n{'='*60}")
        print("📋 健康检查结果")
        print(f"{'='*60}")
        
        # 按类别分组
        categories = {}
        for result in self.results:
            category = result['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # 状态图标
        status_icons = {
            'pass': '✅',
            'fail': '❌',
            'warn': '⚠️',
            'skip': '⏭️'
        }
        
        # 状态计数
        status_counts = {'pass': 0, 'fail': 0, 'warn': 0, 'skip': 0}
        
        for category_name, results in categories.items():
            print(f"\n📂 {category_name.upper()}:")
            
            for result in results:
                status = result['status']
                icon = status_icons.get(status, '❓')
                
                print(f"   {icon} {result['message']}")
                
                if verbose and result['details']:
                    for key, value in result['details'].items():
                        print(f"      {key}: {value}")
                
                status_counts[status] += 1
        
        # 总结
        total = sum(status_counts.values())
        print(f"\n{'='*60}")
        print("📊 检查总结:")
        print(f"   总检查项: {total}")
        print(f"   ✅ 通过: {status_counts['pass']}")
        print(f"   ❌ 失败: {status_counts['fail']}")
        print(f"   ⚠️  警告: {status_counts['warn']}")
        print(f"   ⏭️  跳过: {status_counts['skip']}")
        
        # 健康状态评估
        if status_counts['fail'] == 0:
            if status_counts['warn'] == 0:
                print(f"\n🎉 系统状态: 健康")
            else:
                print(f"\n😊 系统状态: 良好 (有{status_counts['warn']}个警告)")
        else:
            print(f"\n😟 系统状态: 需要修复 (有{status_counts['fail']}个错误)")
    
    def export_json(self, output_file: str) -> None:
        """导出结果为JSON格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.time(),
                'results': self.results,
                'config': self.config
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 结果已导出到: {output_file}")
    
    def get_failed_checks(self) -> List[Dict]:
        """获取失败的检查项"""
        return [r for r in self.results if r['status'] == 'fail']
    
    def get_warnings(self) -> List[Dict]:
        """获取警告项"""
        return [r for r in self.results if r['status'] == 'warn']


def main():
    parser = argparse.ArgumentParser(description='Mem0 系统健康检查工具')
    parser.add_argument('--config', default='.env', help='配置文件路径')
    parser.add_argument('--no-api', action='store_true', help='跳过API服务检查')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    parser.add_argument('--json', help='导出结果为JSON文件')
    parser.add_argument('--fix-suggestions', action='store_true', help='显示修复建议')
    
    args = parser.parse_args()
    
    # 创建健康检查器
    checker = HealthChecker(args.config)
    
    print("🏥 Mem0 系统健康检查工具")
    print("=" * 50)
    
    # 运行检查
    checker.run_all_checks(check_api=not args.no_api)
    
    # 显示结果
    checker.print_results(args.verbose)
    
    # 显示修复建议
    if args.fix_suggestions:
        failed_checks = checker.get_failed_checks()
        warnings = checker.get_warnings()
        
        if failed_checks or warnings:
            print(f"\n🔧 修复建议:")
            
            for result in failed_checks:
                print(f"\n❌ {result['name']}: {result['message']}")
                # 这里可以添加具体的修复建议
            
            for result in warnings:
                print(f"\n⚠️ {result['name']}: {result['message']}")
    
    # 导出JSON
    if args.json:
        checker.export_json(args.json)
    
    # 返回适当的退出码
    failed_count = len(checker.get_failed_checks())
    if failed_count > 0:
        print(f"\n❌ 发现 {failed_count} 个严重问题")
        sys.exit(1)
    else:
        print(f"\n✅ 系统检查完成")
        sys.exit(0)


if __name__ == "__main__":
    main()