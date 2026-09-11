# 铁路障碍物检测系统

基于 YOLOv8 的铁路轨道障碍物检测平台，支持图片、视频、实时摄像头三种输入方式，可对前方人员、异物、动物等障碍物实时识别、定位并告警。

## 技术栈

- **前端**：Vue 3 + Vite
- **后端**：FastAPI + YOLOv8（ultralytics）
- **部署**：Docker + Docker Compose + Nginx
- **系统**：Rocky Linux（本地自建环境）

## 功能模块

| 模块 | 说明 |
|------|------|
| 图片检测 | 上传图片，识别并标注障碍物位置，支持点击/下拉选择目标查看坐标 |
| 视频检测 | 上传视频，逐帧检测并输出标注后的结果视频 |
| 实时检测 | 调用浏览器摄像头，通过 WebSocket 实时传输检测结果 |

## 架构

```
浏览器 ──HTTPS──> Nginx(前端静态资源 + 反代)
                      │
                      ├── /api/* ──> FastAPI 后端(YOLOv8 推理)
                      └── /ws/*  ──> WebSocket 实时推理
```

## 部署

### 1. 准备 SSL 证书（HTTPS 必需，否则浏览器无法调用摄像头）

```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/nginx.key \
  -out certs/nginx.crt \
  -subj "/CN=localhost"
```

### 2. 启动

```bash
docker compose up -d --build
```

首次构建约 10~15 分钟（含 PyTorch 下载），日常启动 1~2 分钟。

### 3. 访问

- 前端：`https://服务器IP`
- 后端健康检查：`http://localhost:8000/ping`

## 配置说明

### Nginx（nginx.conf）
- HTTP 80 强制 301 跳转 HTTPS 443
- `/api/` 反代到后端 `backend:8000`，读超时 600s（视频检测耗时较长）
- `/ws/` WebSocket 代理，配置 Upgrade 头与 3600s 长连接保活
- `client_max_body_size 200m`（视频上传体积较大）

### 后端（raliway-main/Dockerfile）
- 基础镜像 `python:3.10-slim`，安装 CPU 版 PyTorch 控制镜像体积
- 安装 `libgl1 libglib2.0-0`（OpenCV 运行时依赖）和 `ffmpeg`（视频转码）
- 使用清华 PyPI 源 + PyTorch CPU wheel 加速依赖下载

### 数据持久化
- `./data/outputs` 挂载到容器内，检测结果（图片/视频/JSON）持久化到宿主机

### 健康检查与自恢复
- `healthcheck`：start_period 90s（YOLO 模型预热需 30~60 秒）
- `restart: unless-stopped`：容器异常退出或主机重启后自动恢复
- `depends_on`：前端等待后端 healthy 后启动

## 踩坑记录

| 问题 | 定位 | 解决 |
|------|------|------|
| `gzip: unexpected end of file` 解压失败 | scp 传输压缩包不完整 | `gzip -t` 校验完整性后重新上传 |
| 后端容器启动失败 | OpenCV 依赖 libGL 系统库缺失 | Dockerfile 中 `apt-get install libgl1 libglib2.0-0` |
| 检测结果视频浏览器无法播放 | OpenCV 默认 mp4v 编码浏览器不兼容 | 容器内装系统 ffmpeg，转码为 H.264（yuv420p+faststart） |
| 实时检测摄像头打不开 | 浏览器安全策略，非 HTTPS 页面无法调用 getUserMedia | 配置 HTTPS 自签证书 |

## 目录结构

```
.
├── frontend-main/          # 前端（Vue3 + Vite）
│   ├── Dockerfile          # 多阶段构建：Node 编译 → Nginx 运行
│   ├── nginx.conf          # Nginx 配置（HTTPS + 反代 + WebSocket）
│   └── src/
├── raliway-main/           # 后端（FastAPI + YOLOv8）
│   ├── Dockerfile
│   └── backend/
│       ├── app.py          # FastAPI 应用入口
│       ├── yolo_service.py # YOLO 推理服务
│       └── requirements.txt
├── docker-compose.yml      # 一键编排前后端
├── certs/                  # SSL 证书（需自行生成）
└── data/outputs/           # 检测结果持久化目录
```

## 常用运维命令

```bash
docker compose ps                    # 查看状态
docker compose logs -f backend       # 查看后端日志
docker compose restart               # 重启所有服务
docker compose down                  # 停止并删除容器
docker compose up -d                 # 后台启动
```
