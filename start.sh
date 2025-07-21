#!/bin/bash
# mem0 应用启动脚本

cd "$(dirname "$0")"
source venv/bin/activate
python mem0/app.py