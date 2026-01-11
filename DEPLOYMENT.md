# OneSpace Backend 部署指南

## 🔐 安全配置 (重要!)

在部署之前，你需要在 **GitHub Secrets** 中配置以下敏感信息：

### GitHub Secrets 配置

进入你的 GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `DOCKER_USERNAME` | Docker Hub 用户名 | `yourusername` |
| `DOCKER_PASSWORD` | Docker Hub 密码或 Access Token | `dckr_pat_xxx...` |
| `SERVER_HOST` | 服务器 IP 或域名 | `123.45.67.89` |
| `SERVER_USER` | SSH 用户名 | `root` |
| `SSH_PRIVATE_KEY` | SSH 私钥 (完整内容) | `-----BEGIN RSA PRIVATE KEY-----...` |
| `DB_HOST` | 数据库主机 | `mysql` 或 `127.0.0.1` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_USER` | 数据库用户名 | `onespace` |
| `DB_PASSWORD` | 数据库密码 ⚠️ | 使用强密码! |
| `DB_NAME` | 数据库名 | `onespace` |
| `JWT_SECRET_KEY` | JWT 加密密钥 ⚠️ | 见下方生成方法 |
| `ADMIN_USERNAME` | 管理员用户名 | `admin` |
| `ADMIN_PASSWORD_HASH` | 管理员密码哈希 ⚠️ | 见下方生成方法 |
| `CORS_ORIGINS` | 允许的前端域名 | `["https://yourdomain.com"]` |

### 生成安全密钥

#### 1. 生成 JWT 密钥

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### 2. 生成管理员密码哈希

```bash
# 在项目目录下运行
python scripts/generate_password_hash.py YourStrongPassword123!
```

或者：

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("YourStrongPassword123!"))
```

---

## 🐳 Docker 部署

### 方式一: Docker Compose (推荐)

#### 本地开发

```bash
# 1. 复制环境变量配置
cp env.example .env

# 2. 编辑 .env 文件，填入真实的密码和密钥
nano .env

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f backend
```

#### 生产环境

```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 方式二: GitHub Actions 自动部署

1. 将代码推送到 GitHub 仓库
2. 配置好所有 GitHub Secrets
3. 推送到 `master` 或 `main` 分支将自动触发部署

```bash
git add .
git commit -m "Add Docker deployment"
git push origin master
```

---

## 🖥️ 服务器准备

### 首次部署前，在服务器上执行：

```bash
# 1. 创建 Docker 网络
docker network create onespace-network

# 2. 创建数据持久化目录
mkdir -p /opt/onespace/uploads
mkdir -p /opt/onespace/mysql
mkdir -p /opt/onespace/redis

# 3. 设置目录权限
chmod 755 /opt/onespace/uploads
```

### Docker 镜像加速 (国内服务器)

编辑 `/etc/docker/daemon.json`:

```json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com"
  ]
}
```

然后重启 Docker:

```bash
systemctl daemon-reload
systemctl restart docker
```

---

## 📡 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Backend API | 8000 | FastAPI 后端 |
| MySQL | 3306 | 数据库 (建议只内网访问) |
| Redis | 6379 | 缓存 (建议只内网访问) |

---

## 🔍 常用命令

```bash
# 查看容器状态
docker ps

# 查看后端日志
docker logs -f onespace-backend

# 进入容器
docker exec -it onespace-backend /bin/sh

# 重启服务
docker restart onespace-backend

# 停止所有服务
docker-compose down

# 清理未使用的镜像
docker image prune -a
```

---

## ⚠️ 安全提醒

1. **绝不要**将 `.env` 文件提交到 Git
2. **绝不要**在代码中硬编码密码
3. 定期更换 JWT 密钥和管理员密码
4. 使用强密码 (16位以上，包含大小写、数字、特殊字符)
5. 生产环境关闭 DEBUG 模式
6. 建议使用 HTTPS 反向代理
