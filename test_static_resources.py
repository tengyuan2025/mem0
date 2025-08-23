#!/usr/bin/env python
"""
测试静态资源是否正常工作
"""

import os
import requests
from pathlib import Path

def test_static_files():
    """测试静态文件是否存在和大小"""
    print("🔍 检查静态资源文件...")
    
    base_dir = Path(__file__).parent
    static_dir = base_dir / "static" / "swagger-ui"
    
    files_to_check = [
        ("swagger-ui.css", 150000),  # 大约150KB
        ("swagger-ui-bundle.js", 1400000)  # 大约1.4MB
    ]
    
    all_good = True
    
    for filename, min_size in files_to_check:
        filepath = static_dir / filename
        
        if not filepath.exists():
            print(f"❌ 文件不存在: {filepath}")
            all_good = False
            continue
        
        file_size = filepath.stat().st_size
        if file_size < min_size:
            print(f"⚠️  文件太小: {filename} ({file_size} bytes, 期望 > {min_size})")
            all_good = False
        else:
            print(f"✅ {filename}: {file_size:,} bytes")
    
    return all_good

def test_web_service_static():
    """测试 Web 服务的静态文件访问"""
    print("\n🌐 测试 Web 服务静态文件...")
    
    base_url = "http://localhost:9000"
    
    # 测试静态文件 URL
    urls_to_test = [
        "/static/swagger-ui/swagger-ui.css",
        "/static/swagger-ui/swagger-ui-bundle.js"
    ]
    
    for url in urls_to_test:
        try:
            response = requests.get(base_url + url, timeout=5)
            if response.status_code == 200:
                size = len(response.content)
                print(f"✅ {url}: {size:,} bytes")
            else:
                print(f"❌ {url}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  无法连接到 Web 服务: {base_url}")
            print("   请先启动服务: python deepseek_web_service.py")
            break
        except Exception as e:
            print(f"❌ {url}: {e}")

def main():
    print("🧪 静态资源测试")
    print("=" * 40)
    
    # 测试本地文件
    files_ok = test_static_files()
    
    if files_ok:
        print("\n✅ 本地文件检查通过")
        # 测试 Web 服务
        test_web_service_static()
    else:
        print("\n❌ 本地文件检查失败")
        print("\n🔧 修复建议:")
        print("   1. 重新下载文件:")
        print("      curl -L -o static/swagger-ui/swagger-ui.css https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css")
        print("      curl -L -o static/swagger-ui/swagger-ui-bundle.js https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js")
        print("   2. 检查网络连接")
        print("   3. 检查目录权限")

if __name__ == "__main__":
    main()