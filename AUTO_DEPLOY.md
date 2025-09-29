# Mem0 自动部署指南

## 🚀 一键自动部署流程

### 前期准备

1. **服务器准备**
   - 阿里云/腾讯云等云服务器
   - Ubuntu 20.04+ 或 CentOS 7+
   - 至少 2GB 内存，20GB 硬盘
   - **推荐**：购买时选择预装Docker和Python（阿里云支持）

2. **SSH密钥配置**
   ```bash
   # 在本地生成SSH密钥
   ssh-keygen -t ed25519 -f ~/.ssh/mem0_deploy -N ""
   
   # 复制公钥到服务器
   ssh-copy-id -i ~/.ssh/mem0_deploy.pub root@你的服务器IP
   
   # 测试连接
   ssh -i ~/.ssh/mem0_deploy root@你的服务器IP
   ```

3. **GitHub Secrets 配置**
   
   在 GitHub 仓库 → Settings → Secrets and variables → Actions 中添加：
   
   | Secret 名称 | 值 | 说明 |
   |------------|----|----|
   | `SSH_HOST` | 你的服务器IP | 必需 |
   | `SSH_USER` | root | 可选，默认root |
   | `SSH_PRIVATE_KEY` | SSH私钥内容 | 必需 |
   | `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 可选 |
   | `OPENAI_API_KEY` | OpenAI API密钥 | 可选 |

### 🔄 自动部署触发

推送到以下分支会自动触发部署：
- `main` - 生产环境
- `daily/*` - 测试环境  
- `v*` 标签 - 版本发布

```bash
# 提交代码自动部署
git add .
git commit -m "feat: 新功能"
git push origin daily/0.0.1  # 自动部署到服务器
```

### 📊 部署流程说明

1. **代码检查** - 语法检查、单元测试
2. **Docker镜像构建** - 在GitHub中构建
3. **服务器环境检查** - SSH连接、Docker安装
4. **自动部署** - 下载代码、构建、运行
5. **健康检查** - 验证服务是否正常

### 🔍 查看部署状态

1. **GitHub Actions 日志**
   - 仓库页面 → Actions → 最新workflow
   - 查看详细的部署日志

2. **服务器状态检查**
   ```bash
   # 使用检查脚本（本地执行）
   ./scripts/check-deployment.sh 你的服务器IP
   
   # 或直接SSH检查
   ssh root@你的服务器IP "docker ps | grep mem0"
   ```

3. **API访问测试**
   ```bash
   # 健康检查
   curl http://你的服务器IP:8000/health
   
   # API文档
   http://你的服务器IP:8000/docs
   ```

### 🛠️ 服务器环境选择

**选择1：阿里云预装（推荐）**
- 购买ECS时勾选"应用软件"中的Docker
- 系统会自动安装Docker CE和Python
- 无需手动配置，开箱即用

**选择2：手动初始化服务器**
```bash
# SSH登录服务器
ssh root@你的服务器IP

# 下载并运行初始化脚本
curl -fsSL https://raw.githubusercontent.com/你的用户名/mem0/daily/0.0.1/scripts/deployment/setup-server.sh | bash
```

### ❌ 故障排除

#### 部署失败常见原因：

1. **SSH连接失败**
   - 检查 `SSH_HOST` 是否正确
   - 检查 `SSH_PRIVATE_KEY` 是否正确
   - 确保服务器SSH端口开放

2. **Docker环境问题**
   - 确保购买时选择了预装Docker
   - 或手动安装：`curl -fsSL https://get.docker.com | bash`
   - 启动服务：`systemctl start docker && systemctl enable docker`

3. **网络连接问题（已解决）**
   - 使用tar+scp方式传输代码，无需rsync
   - 部署流程：GitHub Actions打包 → scp传输 → 服务器解压部署
   - 避免了所有网络依赖问题

4. **服务启动失败**
   - 查看 GitHub Actions 日志
   - SSH登录服务器查看: `docker logs mem0-api`

#### 快速修复：

```bash
# SSH登录服务器
ssh root@你的服务器IP

# 查看容器状态
docker ps -a

# 查看应用日志
docker logs mem0-api

# 重启服务
cd /opt/mem0
docker stop mem0-api
docker rm mem0-api
docker build -f Dockerfile.simple -t mem0:latest .
docker run -d --name mem0-api -p 8000:8000 --restart always mem0:latest

# 测试服务
curl http://localhost:8000/health
```

### 🔧 自定义配置

如需修改服务器配置，编辑 `.env.server` 文件：

```env
# API密钥会自动生成，或从GitHub Secrets获取
API_SECRET_KEY=auto-generated

# LLM配置
MEM0_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}

# 其他配置...
```

### 📈 监控和维护

部署完成后，系统会自动设置：
- 容器自动重启（`--restart always`）
- 日志轮转
- 健康检查

定期检查：
```bash
# 查看服务状态
./scripts/check-deployment.sh 你的服务器IP

# 查看资源使用
ssh root@你的服务器IP "docker stats mem0-api"
```

---

## 🎉 总结

现在你只需要：
1. **配置一次** GitHub Secrets
2. **推送代码** 到指定分支
3. **自动部署** 到服务器完成

完全自动化，无需手动操作！