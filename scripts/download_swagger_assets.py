#!/usr/bin/env python3
"""
下载Swagger UI和ReDoc的静态资源到本地
"""

import os
import requests
from pathlib import Path

# Swagger UI版本
SWAGGER_VERSION = "5.9.0"
REDOC_VERSION = "2.1.3"

# 要下载的文件
swagger_files = [
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/swagger-ui.css",
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/swagger-ui-bundle.js",
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/swagger-ui-standalone-preset.js",
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/favicon-32x32.png",
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/favicon-16x16.png",
]

redoc_files = [
    f"https://cdn.jsdelivr.net/npm/redoc@{REDOC_VERSION}/bundles/redoc.standalone.js",
]

def download_file(url, dest_path):
    """下载文件到指定路径"""
    try:
        print(f"📥 下载: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 确保目录存在
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 保存到: {dest_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def main():
    # 项目根目录
    root_dir = Path(__file__).parent.parent
    static_dir = root_dir / "static"
    
    print("🚀 开始下载Swagger UI资源...")
    
    # 下载Swagger UI文件
    swagger_dir = static_dir / "swagger"
    for url in swagger_files:
        filename = url.split('/')[-1]
        dest = swagger_dir / filename
        download_file(url, dest)
    
    # 下载ReDoc文件
    print("\n🚀 开始下载ReDoc资源...")
    redoc_dir = static_dir / "redoc"
    for url in redoc_files:
        filename = url.split('/')[-1]
        dest = redoc_dir / filename
        download_file(url, dest)
    
    print("\n✅ 所有资源下载完成！")
    
    # 显示下载的文件
    print("\n📋 已下载的文件:")
    for file_path in swagger_dir.glob("*"):
        print(f"  - {file_path.relative_to(root_dir)}")
    for file_path in redoc_dir.glob("*"):
        print(f"  - {file_path.relative_to(root_dir)}")

if __name__ == "__main__":
    main()