# Mem0 API Docker 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 升级 pip
RUN python -m pip install --upgrade pip

# 安装 Python 依赖
# 首先安装核心依赖
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    python-multipart>=0.0.6 \
    httpx>=0.25.0 \
    pydantic>=2.7.3

# 安装 mem0ai 核心依赖
RUN pip install --no-cache-dir \
    qdrant-client>=1.9.1 \
    openai>=1.33.0 \
    posthog>=3.5.0 \
    pytz>=2024.1 \
    sqlalchemy>=2.0.31

# 安装测试依赖
RUN pip install --no-cache-dir \
    pytest>=8.2.2 \
    pytest-asyncio>=0.23.7 \
    pytest-mock>=3.14.0 \
    pytest-cov>=4.1.0

# 安装可选依赖（向量存储）
RUN pip install --no-cache-dir \
    chromadb>=0.4.24 \
    weaviate-client>=4.4.0 \
    "pinecone<=7.3.0" \
    pinecone-text>=0.10.0 \
    faiss-cpu>=1.7.4

# 安装 LLM 依赖
RUN pip install --no-cache-dir \
    groq>=0.3.0 \
    together>=0.2.10 \
    litellm>=0.1.0 \
    ollama>=0.1.0 \
    "google-generativeai>=0.3.0"

# 安装其他有用的依赖
RUN pip install --no-cache-dir \
    boto3>=1.34.0 \
    sentence-transformers>=5.0.0

# 设置权限
RUN chmod +x *.py

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 设置启动命令
CMD ["python", "-m", "mem0.api.main"]