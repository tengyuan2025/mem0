#!/usr/bin/env python3
"""
Mem0 嵌入模型下载脚本
用于预下载和验证嵌入模型
"""

import os
import sys
import time
from typing import List, Dict, Optional
from pathlib import Path
import argparse

try:
    from sentence_transformers import SentenceTransformer
    from dotenv import load_dotenv
    import torch
except ImportError as e:
    print(f"❌ 缺少依赖包: {e}")
    print("请先运行: pip install -r requirements.txt")
    sys.exit(1)


class ModelDownloader:
    """嵌入模型下载器"""
    
    # 支持的模型列表（按推荐程度排序）
    SUPPORTED_MODELS = {
        # 中文优化模型
        'shibing624/text2vec-base-chinese': {
            'description': '中文基础模型，轻量级，适合树莓派',
            'size': '300-500MB',
            'language': 'zh',
            'performance': 'good'
        },
        'BAAI/bge-large-zh-v1.5': {
            'description': '百度高性能中文模型',
            'size': '1.2GB',
            'language': 'zh',
            'performance': 'excellent'
        },
        'moka-ai/m3e-small': {
            'description': '小型多语言模型，内存占用最小',
            'size': '200-350MB',
            'language': 'multilingual',
            'performance': 'fair'
        },
        'shibing624/text2vec-base-multilingual': {
            'description': '多语言基础模型',
            'size': '250-400MB',
            'language': 'multilingual',
            'performance': 'good'
        },
        
        # 多语言模型
        'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2': {
            'description': '标准多语言模型',
            'size': '300-450MB',
            'language': 'multilingual',
            'performance': 'good'
        },
        'sentence-transformers/all-MiniLM-L6-v2': {
            'description': '轻量级英文模型',
            'size': '90MB',
            'language': 'en',
            'performance': 'fair'
        },
    }
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.hf_home = self.data_dir / "huggingface"
        self.transformers_cache = self.data_dir / "transformers"
        
        # 设置环境变量
        os.environ['HF_HOME'] = str(self.hf_home)
        os.environ['TRANSFORMERS_CACHE'] = str(self.transformers_cache)
        
        # 创建目录
        self.hf_home.mkdir(parents=True, exist_ok=True)
        self.transformers_cache.mkdir(parents=True, exist_ok=True)
    
    def list_models(self) -> None:
        """列出支持的模型"""
        print("📋 支持的嵌入模型列表：")
        print("=" * 80)
        
        for model_name, info in self.SUPPORTED_MODELS.items():
            print(f"🤖 {model_name}")
            print(f"   📝 描述: {info['description']}")
            print(f"   📦 大小: {info['size']}")
            print(f"   🌍 语言: {info['language']}")
            print(f"   ⚡ 性能: {info['performance']}")
            print()
    
    def check_model_exists(self, model_name: str) -> bool:
        """检查模型是否已下载"""
        try:
            # 尝试快速加载模型（仅检查不实际加载）
            model = SentenceTransformer(model_name, cache_folder=str(self.hf_home))
            return True
        except:
            return False
    
    def get_model_size(self, model_name: str) -> str:
        """获取模型预估大小"""
        return self.SUPPORTED_MODELS.get(model_name, {}).get('size', '未知')
    
    def download_model(self, model_name: str, force: bool = False) -> bool:
        """下载指定模型"""
        print(f"🔄 准备下载模型: {model_name}")
        
        # 检查模型是否已存在
        if not force and self.check_model_exists(model_name):
            print(f"✅ 模型 {model_name} 已存在，跳过下载")
            return True
        
        # 显示模型信息
        if model_name in self.SUPPORTED_MODELS:
            info = self.SUPPORTED_MODELS[model_name]
            print(f"   📝 描述: {info['description']}")
            print(f"   📦 预估大小: {info['size']}")
        
        try:
            print(f"📥 正在下载 {model_name}...")
            start_time = time.time()
            
            # 下载模型
            model = SentenceTransformer(model_name, cache_folder=str(self.hf_home))
            
            end_time = time.time()
            print(f"✅ 模型 {model_name} 下载完成！耗时: {end_time - start_time:.1f}秒")
            
            # 验证模型
            print("🧪 验证模型...")
            test_texts = ["测试文本", "Hello world", "This is a test"]
            embeddings = model.encode(test_texts)
            print(f"✅ 模型验证成功！嵌入维度: {embeddings.shape[1]}")
            
            return True
            
        except Exception as e:
            print(f"❌ 下载模型 {model_name} 失败: {e}")
            return False
    
    def download_multiple_models(self, model_names: List[str], force: bool = False) -> Dict[str, bool]:
        """下载多个模型"""
        results = {}
        
        for model_name in model_names:
            print(f"\n{'='*60}")
            success = self.download_model(model_name, force)
            results[model_name] = success
            
            if not success:
                print(f"⚠️  模型 {model_name} 下载失败，继续下载其他模型...")
        
        return results
    
    def get_config_model(self) -> Optional[str]:
        """从配置文件获取模型名称"""
        load_dotenv()
        return os.getenv('MEM0_EMBEDDER_MODEL')
    
    def list_downloaded_models(self) -> List[str]:
        """列出已下载的模型"""
        downloaded = []
        
        for model_name in self.SUPPORTED_MODELS.keys():
            if self.check_model_exists(model_name):
                downloaded.append(model_name)
        
        return downloaded
    
    def show_storage_info(self) -> None:
        """显示存储信息"""
        print(f"📁 模型存储位置:")
        print(f"   HuggingFace缓存: {self.hf_home}")
        print(f"   Transformers缓存: {self.transformers_cache}")
        
        # 计算存储空间使用
        try:
            hf_size = sum(f.stat().st_size for f in self.hf_home.rglob('*') if f.is_file())
            transformer_size = sum(f.stat().st_size for f in self.transformers_cache.rglob('*') if f.is_file())
            total_size = hf_size + transformer_size
            
            print(f"   已使用空间: {total_size / 1024**3:.2f} GB")
        except:
            print("   无法计算存储空间使用情况")


def main():
    parser = argparse.ArgumentParser(description='Mem0 嵌入模型下载工具')
    parser.add_argument('--list', action='store_true', help='列出支持的模型')
    parser.add_argument('--download', type=str, help='下载指定模型')
    parser.add_argument('--download-all', action='store_true', help='下载所有推荐模型')
    parser.add_argument('--download-config', action='store_true', help='下载配置文件中指定的模型')
    parser.add_argument('--force', action='store_true', help='强制重新下载')
    parser.add_argument('--show-downloaded', action='store_true', help='显示已下载的模型')
    parser.add_argument('--data-dir', default='./data', help='数据目录 (默认: ./data)')
    parser.add_argument('--recommended', action='store_true', help='下载推荐的中文模型')
    
    args = parser.parse_args()
    
    # 创建下载器
    downloader = ModelDownloader(args.data_dir)
    
    print("🤖 Mem0 嵌入模型下载工具")
    print("=" * 50)
    
    # 显示存储信息
    downloader.show_storage_info()
    print()
    
    if args.list:
        downloader.list_models()
    
    elif args.show_downloaded:
        downloaded = downloader.list_downloaded_models()
        if downloaded:
            print("✅ 已下载的模型:")
            for model in downloaded:
                print(f"   • {model}")
        else:
            print("📭 没有已下载的模型")
    
    elif args.download:
        model_name = args.download
        if model_name not in downloader.SUPPORTED_MODELS:
            print(f"❌ 不支持的模型: {model_name}")
            print("使用 --list 查看支持的模型列表")
            return
        
        success = downloader.download_model(model_name, args.force)
        if success:
            print(f"\n🎉 模型 {model_name} 安装完成！")
        else:
            print(f"\n❌ 模型 {model_name} 安装失败！")
    
    elif args.download_config:
        model_name = downloader.get_config_model()
        if not model_name:
            print("❌ 未在配置文件中找到 MEM0_EMBEDDER_MODEL")
            print("请检查 .env 文件")
            return
        
        print(f"📋 配置文件中的模型: {model_name}")
        success = downloader.download_model(model_name, args.force)
        if success:
            print(f"\n🎉 配置的模型 {model_name} 安装完成！")
        else:
            print(f"\n❌ 配置的模型 {model_name} 安装失败！")
    
    elif args.recommended:
        # 推荐的中文模型
        recommended_models = [
            'shibing624/text2vec-base-chinese',
            'BAAI/bge-large-zh-v1.5'
        ]
        print("📥 下载推荐的中文模型...")
        results = downloader.download_multiple_models(recommended_models, args.force)
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n📊 下载结果: {success_count}/{len(results)} 个模型成功")
    
    elif args.download_all:
        print("📥 下载所有支持的模型...")
        all_models = list(downloader.SUPPORTED_MODELS.keys())
        results = downloader.download_multiple_models(all_models, args.force)
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n📊 下载结果: {success_count}/{len(results)} 个模型成功")
    
    else:
        # 默认行为：检查配置文件中的模型，如果没有则下载推荐模型
        config_model = downloader.get_config_model()
        
        if config_model:
            print(f"📋 检测到配置的模型: {config_model}")
            if not downloader.check_model_exists(config_model):
                print("🔄 配置的模型尚未下载，开始下载...")
                downloader.download_model(config_model, args.force)
            else:
                print("✅ 配置的模型已存在")
        else:
            print("📥 未检测到配置的模型，下载默认推荐模型...")
            downloader.download_model('shibing624/text2vec-base-chinese', args.force)


if __name__ == "__main__":
    main()