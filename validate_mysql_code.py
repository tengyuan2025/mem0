#!/usr/bin/env python3
"""
Simple validation script for MySQL integration code
This script only validates syntax and basic imports without external dependencies
"""

import ast
import sys
from pathlib import Path

def validate_python_file(file_path):
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        print(f"✓ {file_path.name}: Syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"✗ {file_path.name}: Syntax error at line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"✗ {file_path.name}: Error - {e}")
        return False

def main():
    """Validate all MySQL integration files"""
    print("Validating MySQL integration code...\n")
    
    # Files to validate
    files_to_check = [
        "mem0/memory/mysql_storage.py",
        "mem0/memory/mysql_memory.py", 
        "mem0/configs/mysql.py",
        "examples/mysql_integration_example.py",
    ]
    
    current_dir = Path(__file__).parent
    valid_files = 0
    total_files = len(files_to_check)
    
    for file_path in files_to_check:
        full_path = current_dir / file_path
        if full_path.exists():
            if validate_python_file(full_path):
                valid_files += 1
        else:
            print(f"✗ {file_path}: File not found")
    
    print(f"\nValidation Results: {valid_files}/{total_files} files are syntactically valid")
    
    if valid_files == total_files:
        print("\n🎉 All MySQL integration files have valid syntax!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install mysql-connector-python")
        print("2. Start MySQL server (xiaozhi-server docker-compose_all.yml)")
        print("3. Run: python examples/mysql_integration_example.py")
        return 0
    else:
        print("\n❌ Some files have syntax errors. Please check and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())