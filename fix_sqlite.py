#!/usr/bin/env python3
"""
SQLite3 版本修复脚本
用于解决ChromaDB要求的SQLite版本问题
"""

import sys
import os

def fix_sqlite():
    """修复SQLite版本问题"""
    try:
        # 检查当前SQLite版本
        import sqlite3
        current_version = sqlite3.sqlite_version
        print(f"当前SQLite版本: {current_version}")
        
        # ChromaDB需要的最低版本
        required_version = "3.35.0"
        
        if current_version < required_version:
            print(f"SQLite版本过低，需要 >= {required_version}")
            
            # 尝试使用pysqlite3-binary
            try:
                import pysqlite3.dbapi2 as sqlite3
                print(f"使用pysqlite3-binary，版本: {sqlite3.sqlite_version}")
                
                # 替换系统sqlite3模块
                sys.modules['sqlite3'] = sqlite3
                os.environ['SQLITE3_FORCE_PYSQLITE3'] = '1'
                
                print("✅ SQLite3已升级")
                return True
                
            except ImportError:
                print("❌ pysqlite3-binary未安装，请运行: pip install pysqlite3-binary")
                return False
        else:
            print("✅ SQLite版本满足要求")
            return True
            
    except Exception as e:
        print(f"❌ SQLite检查失败: {e}")
        return False

if __name__ == "__main__":
    fix_sqlite()