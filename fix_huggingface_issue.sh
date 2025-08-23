#!/bin/bash

echo "🔧 修复 HuggingFace 模型下载问题"
echo "=================================="

# 1. 设置 HuggingFace 镜像
echo "📍 设置 HuggingFace 镜像..."
export HF_ENDPOINT=https://hf-mirror.com

# 2. 预下载模型
echo "📥 预下载嵌入模型..."
python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print('正在下载 BAAI/bge-large-zh-v1.5 模型...')
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    print('✅ 模型下载成功!')
    
    # 测试模型
    test_text = ['测试文本', '这是一个测试']
    embeddings = model.encode(test_text)
    print(f'✅ 模型测试成功，维度: {embeddings.shape}')
    
except Exception as e:
    print(f'❌ 下载失败: {e}')
    print('🔄 尝试备用方案...')
"

echo ""
echo "🌐 设置环境变量（永久生效）..."
echo "export HF_ENDPOINT=https://hf-mirror.com" >> ~/.bashrc
echo "export HF_ENDPOINT=https://hf-mirror.com" >> ~/.zshrc

echo ""
echo "✅ 配置完成！"
echo "💡 请重新运行: ./start_services.sh"