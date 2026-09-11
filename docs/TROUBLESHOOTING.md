# 铁路障碍物检测系统 - 故障排查记录

## 1. scp 传输压缩包不完整

### 现象
```
gzip: stdin: unexpected end of file
tar: Error is not recoverable: exiting now
```

### 定位
使用 `scp` 传输 `railway-yolo.tar.gz` 时网络中断或传输未完成，导致压缩包损坏。

### 解决
```bash
# 校验压缩包完整性
gzip -t railway-yolo.tar.gz

# 若报错，重新上传后再校验
```

### 结论
大文件传输后必须用 `gzip -t` 校验完整性，确认无误后再解压。

---

## 2. 后端容器启动失败：OpenCV 缺少 libGL

### 现象
```
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

### 定位
OpenCV 依赖系统图形库 `libGL`，但 `python:3.10-slim` 基础镜像未预装。

### 解决
在 Dockerfile 中安装系统依赖：
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

### 结论
使用 slim 基础镜像时需手动补齐 OpenCV 的运行时依赖（libGL、libglib2.0-0）。

---

## 3. 检测结果视频浏览器无法播放

### 现象
视频检测完成后，前端无法播放结果视频。

### 定位
OpenCV 默认使用 `mp4v` 编码器输出视频，多数浏览器不支持该编码格式。

### 解决
在容器内安装系统 ffmpeg，检测完成后转码：
```bash
ffmpeg -i input.mp4 -c:v libx264 -pix_fmt yuv420p -movflags +faststart output.mp4
```

### 结论
- `libx264`：H.264 编码，浏览器通用支持
- `yuv420p`：像素格式，兼容性最好
- `faststart`：将 moov atom 移到文件头，支持边下边播

---

## 4. 实时检测摄像头无法调用

### 现象
浏览器打开实时检测页面，摄像头无法启动。

### 定位
浏览器安全策略：`getUserMedia` API 仅在安全上下文（HTTPS 或 localhost）下可用。HTTP 页面直接拒绝访问。

### 解决
配置 Nginx HTTPS（自签证书即可满足内网访问）：
```nginx
server {
    listen 443 ssl;
    ssl_certificate     /etc/nginx/certs/nginx.crt;
    ssl_certificate_key /etc/nginx/certs/nginx.key;
    # ...
}
```

### 结论
涉及摄像头/麦克风/地理位置等敏感 API 的 Web 应用，必须部署在 HTTPS 下。

---

## 5. 健康检查导致容器频繁重启

### 现象
容器启动后反复重启，日志显示健康检查失败。

### 定位
YOLO 模型加载预热约需 30~60 秒，但健康检查在容器启动后立即执行，误判服务不可用。

### 解决
设置 `start_period` 给足预热时间：
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "..."]
  interval: 15s
  timeout: 10s
  retries: 5
  start_period: 90s
```

### 结论
有启动预热过程的服务（AI 模型、数据库初始化等），必须配置 `start_period` 避免健康检查误杀。
