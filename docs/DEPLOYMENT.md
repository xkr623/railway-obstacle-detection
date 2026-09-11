# 铁路障碍物检测系统 - 部署手册

## 1. 系统架构

```
浏览器 ──HTTPS(443)──> Nginx ──┬── /api/* ──> FastAPI(8000) ──> YOLOv8 推理
                                └── /ws/*  ──> WebSocket 实时推理
```

| 组件 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| 前端 | Vue 3 + Vite + Nginx | 80/443 | 静态资源托管 + 反向代理 |
| 后端 | FastAPI + YOLOv8 | 8000 | HTTP 接口 + WebSocket 推理 |

## 2. 环境要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Rocky Linux 9 / CentOS 7+ / Ubuntu 20.04+ |
| Docker | 20.10+ |
| Docker Compose | v2.0+ |
| 内存 | 4GB+（YOLO 模型加载约需 1~2GB） |
| 磁盘 | 20GB+ |

## 3. 部署步骤

### 3.1 生成 SSL 证书（HTTPS 必需）

```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/nginx.key \
  -out certs/nginx.crt \
  -subj "/CN=服务器IP或域名"
```

> 浏览器调用摄像头（getUserMedia）需要安全上下文（HTTPS），自签证书可满足本地/内网访问。

### 3.2 启动服务

```bash
# 构建并后台启动
docker compose up -d --build

# 查看启动状态
docker compose ps
```

首次构建约 10~15 分钟（含 PyTorch 下载），后续启动 1~2 分钟。

### 3.3 验证服务

```bash
# 后端健康检查
curl http://localhost:8000/ping

# 前端访问
# 浏览器打开 https://服务器IP
```

## 4. 配置说明

### 4.1 Nginx 反向代理（frontend-main/nginx.conf）

| 配置项 | 值 | 说明 |
|--------|-----|------|
| HTTP 跳转 | `return 301 https://$host$request_uri` | 80 端口强制跳转 HTTPS |
| API 反代 | `proxy_pass http://backend:8000/` | /api/ 前缀转发到后端 |
| API 超时 | `proxy_read_timeout 600s` | 视频检测耗时较长，放宽读超时 |
| WebSocket | `Upgrade` + `Connection "upgrade"` | /ws/ 长连接代理 |
| WS 超时 | `proxy_read_timeout 3600s` | 实时检测长连接保活 |
| 上传限制 | `client_max_body_size 200m` | 视频文件较大 |

### 4.2 后端镜像（raliway-main/Dockerfile）

| 优化项 | 说明 |
|--------|------|
| 基础镜像 `python:3.10-slim` | 精简体积 |
| CPU 版 PyTorch | 通过 `PIP_EXTRA_INDEX_URL` 指定 CPU wheel 源 |
| 清华 PyPI 源 | 加速依赖下载 |
| `libgl1 libglib2.0-0` | OpenCV 运行时依赖 |
| `ffmpeg` | 将 OpenCV 输出的 mp4v 转码为浏览器兼容的 H.264 |

### 4.3 数据持久化

| 宿主机路径 | 容器路径 | 说明 |
|-----------|---------|------|
| `./data/outputs` | `/app/raliway-main/outputs` | 检测结果（图片/视频/JSON） |
| `./certs` | `/etc/nginx/certs` | SSL 证书（只读） |

### 4.4 健康检查与自恢复

| 配置 | 值 | 说明 |
|------|-----|------|
| `start_period` | 90s | YOLO 模型预热约 30~60 秒，避免误判 |
| `interval` | 15s | 健康检查间隔 |
| `retries` | 5 | 连续失败 5 次标记为 unhealthy |
| `restart` | `unless-stopped` | 容器异常退出或主机重启后自动恢复 |

## 5. 常用运维命令

```bash
docker compose ps                    # 查看服务状态
docker compose logs -f backend       # 实时查看后端日志
docker compose logs -f frontend      # 实时查看前端日志
docker compose restart               # 重启所有服务
docker compose down                  # 停止并删除容器
docker compose up -d                 # 后台启动
docker compose build --no-cache      # 无缓存重新构建
```

## 6. 故障排查

详见 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
